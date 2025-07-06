import gradio as gr
import pandas as pd
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field, field_validator
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.output_parsers import PydanticOutputParser
from docx import Document
from datetime import datetime
import os
import tempfile

# Model danych
class QuestionAnswer(BaseModel):
    question_number: int = Field(..., description="Numer pytania")
    answer: str = Field(..., description="Odpowiedź, tylko TAK lub NIE")
    citation: str = Field(..., description="Fragment cytatu")

    @field_validator("answer")
    def validate_answer(cls, v):
        if v not in {"TAK", "NIE"}:
            raise ValueError("Odpowiedź musi być TAK lub NIE")
        return v

class JobAdAnalysis(BaseModel):
    answers: list[QuestionAnswer]

parser = PydanticOutputParser(pydantic_object=JobAdAnalysis)

PROMPT_TEMPLATE_TEXT = """Przeanalizuj poniższe ogłoszenie o pracę pod kątem dostępności dla osób z niepełnosprawnościami.

Ogłoszenie:
{job_ad}

Odpowiedz na następujące pytania:
{questions}

Format odpowiedzi powinien być w następującej strukturze JSON:
{{
  "answers": [
    {{
      "question_number": 1,
      "answer": "TAK/NIE",
      "citation": "dokładny cytat z tekstu"
    }}
  ]
}}
"""

# Wczytanie matrycy danych
matryca_df = pd.read_csv('matryca.csv', header=None,
                         names=['area', 'prompt', 'true', 'false', 'more', 'hint'])

def prepare_questions(df):
    questions_text = ""
    for index, row in df.iterrows():
        question_number = index + 1
        questions_text += f"{question_number} {row['prompt']}\n"
    return questions_text

def doc_to_text(file):
    extension = os.path.splitext(file.name)[1].lower()
    if extension == ".docx":
        loader = Docx2txtLoader(file.name)
    elif extension == ".pdf":
        loader = PyPDFLoader(file.name)
    else:
        return "error"
    pages = loader.load()
    return "\n".join(page.page_content for page in pages)

def _generate_report(result: pd.DataFrame, title: str, prefix: str, include_more: bool) -> str:
    """Tworzy dokument Word na podstawie wyników analizy."""
    doc = Document('template.docx')
    doc.add_heading(title, 0)
    doc.add_paragraph(f'Data wygenerowania: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
    
    for _, row in result.iterrows():
        doc.add_heading(str(row['area']), 1)
        doc.add_paragraph(str(row['citation']), style='Intense Quote')
        for line in str(row['content']).split('\n'):
            if line.strip():
                doc.add_paragraph(line)
        
        if include_more and pd.notna(row['more']):
            for line in str(row['more']).split('\n'):
                if line.strip():
                    doc.add_paragraph(line)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_prefix = f"{prefix}{timestamp}_"
    
    with tempfile.NamedTemporaryFile(delete=False, prefix=filename_prefix, suffix=".docx") as tmp:
        doc.save(tmp.name)
        return tmp.name

def create_short_report(result: pd.DataFrame) -> str:
    return _generate_report(
        result,
        title='Raport analizy ogłoszenia o pracę (wersja skrócona)',
        prefix='KoREKtor_short_',
        include_more=False
    )

def create_report(result: pd.DataFrame) -> str:
    return _generate_report(
        result,
        title='Raport analizy ogłoszenia o pracę',
        prefix='KoREKtor_pelny_',
        include_more=True
    )

def analyze_job_ad(job_ad, file):
    try:
        print(f"DEBUG: file={file}, job_ad length={len(job_ad) if job_ad else 0}")
        
        if file:
            job_ad = doc_to_text(file)
            print(f"DEBUG: doc_to_text result={job_ad[:100] if job_ad != 'error' else 'ERROR'}")
            if job_ad == "error":
                return None, None, None
        
        if not job_ad or job_ad.strip() == "":
            print("DEBUG: Empty job_ad")
            return None, None, None
            
        questions = prepare_questions(matryca_df)
        prompt_template = PromptTemplate.from_template(PROMPT_TEMPLATE_TEXT)
    
        model = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        chain = prompt_template | model | parser
        response = chain.invoke({"job_ad": job_ad, "questions": questions})
    
        output_df = pd.DataFrame(columns=['area', 'answer', 'citation', 'content', 'more'])
        for i in range(16):
            if response.answers[i].answer in {"TAK", "NIE"}:
                # Dla indeksu 9 zamieniamy odpowiedź na przeciwną
                answer = response.answers[i].answer
                if i == 9:
                    answer = "NIE" if answer == "TAK" else "TAK"
                    
                new_row = {
                    'area': matryca_df.area[i],
                    'answer': answer,
                    'citation': response.answers[i].citation,
                    'content': matryca_df.true[i] if answer == 'TAK' else matryca_df.false[i],
                    'more': matryca_df.more[i]
                }
                output_df = pd.concat([output_df, pd.DataFrame([new_row])], ignore_index=True)
    
        short_word_file_path = create_short_report(output_df)
        word_file_path = create_report(output_df)
        json_output = output_df.to_dict(orient="records")
        
        print(f"DEBUG: Zwracam pliki - pełny: {word_file_path}, skrócony: {short_word_file_path}")
        print(f"DEBUG: Pliki istnieją - pełny: {os.path.exists(word_file_path)}, skrócony: {os.path.exists(short_word_file_path)}")
        print(f"DEBUG: Rozmiary plików - pełny: {os.path.getsize(word_file_path) if os.path.exists(word_file_path) else 'N/A'}")
        print(f"DEBUG: Rozmiary plików - skrócony: {os.path.getsize(short_word_file_path) if os.path.exists(short_word_file_path) else 'N/A'}")
        
        return json_output, word_file_path, short_word_file_path
    except Exception as e:
        print(f"ERROR w analyze_job_ad: {e}")
        return None, None, None

# Interfejs Gradio
demo = gr.Interface(
    fn=analyze_job_ad,
    inputs=[
        gr.TextArea(label="Ogłoszenie (opcjonalnie)", placeholder="Wklej tekst ogłoszenia tutaj..."), 
        gr.File(label="Lub wybierz plik PDF/DOCX", file_types=[".pdf", ".docx"])
    ],
    outputs=[
        gr.JSON(label="Wyniki analizy"), 
        gr.File(label="Pobierz pełny raport Word"), 
        gr.File(label="Pobierz skrócony raport Word")
    ],
    title="KoREKtor – analiza ogłoszenia",
    description="Przeanalizuj ogłoszenie o pracę pod kątem dostępności dla osób z niepełnosprawnościami"
).launch()