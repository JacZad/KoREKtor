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

# Wczytanie matrycy danych
matryca_df = pd.read_csv('matryca.csv', header=None,
                         names=['area', 'prompt', 'true', 'false', 'more', 'hint'])

question_to_area_map = {}

def prepare_questions(df):
    global question_to_area_map
    question_to_area_map = {}
    questions_text = ""
    for index, row in df.iterrows():
        question_number = index + 1
        questions_text += f"{question_number} {row['prompt']}\n"
        question_to_area_map[question_number] = {
            'area': row['area'],
            'true': row['true'],
            'false': row['false'],
            'hint': row['hint'],
            'more': row['more']
        }
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

def create_report(result: pd.DataFrame) -> str:
    doc = Document('template.docx')
    doc.add_heading('Raport analizy ogłoszenia o pracę', 0)
    doc.add_paragraph(f'Data wygenerowania: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
    for _, row in result.iterrows():
        doc.add_heading(str(row['area']), 1)
        doc.add_paragraph(str(row['citation']), style='Intense Quote')
        for line in str(row['content']).split('\n'):
            if line.strip():
                doc.add_paragraph(line)
        if pd.notna(row['more']):
            for line in str(row['more']).split('\n'):
                if line.strip():
                    doc.add_paragraph(line)
    
    # Użycie prefix dla nazwy pliku zaczynającej się od "KoREKtor_"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"KoREKtor_{timestamp}_"
    
    with tempfile.NamedTemporaryFile(delete=False, prefix=prefix, suffix=".docx") as tmp:
        doc.save(tmp.name)
        return tmp.name  # Zwracamy ścieżkę do pliku tymczasowego

def analyze_job_ad(job_ad, file):
    if file:
        job_ad = doc_to_text(file)
        if job_ad == "error":
            return None, None
    questions = prepare_questions(matryca_df)
    prompt_template = PromptTemplate.from_template(
        """Przeanalizuj poniższe ogłoszenie o pracę pod kątem dostępności dla osób z niepełnosprawnościami.

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
    )

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

    word_file_path = create_report(output_df)
    json_output = output_df.to_dict(orient="records")
    return json_output, word_file_path

# Interfejs Gradio
demo = gr.Interface(
    fn=analyze_job_ad,
    inputs=[gr.TextArea(label="Ogłoszenie (opcjonalnie)"), gr.File(label="Plik PDF lub DOCX")],
    outputs=[gr.JSON(label="Wyniki analizy"), gr.File(label="Pobierz raport w formacie Word")],
    title="KoREKtor – analiza ogłoszenia",
).launch()