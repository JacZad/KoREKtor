import streamlit as st
import pandas as pd
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import Optional, Union
import json
from pathlib import Path
import logging
from functools import lru_cache

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log'
)

# Konfiguracja modelu
MODEL_CONFIG = {
    "model_name": "gpt-4o",
    "temperature": 0.0,
    "max_tokens": 4000
}

# Inicjalizacja modelu OpenAI
openai_model = ChatOpenAI(
    model_name=MODEL_CONFIG["model_name"], 
    temperature=MODEL_CONFIG["temperature"],
    api_key=os.getenv("OPENAI_API_KEY")
)

# Definicja szablonu promptu
matrix_prompt = PromptTemplate(
    input_variables=["job_ad"],
    template=(
        "Przeanalizuj poniższe ogłoszenie o pracę pod kątem dostępności dla osób z niepełnosprawnościami. "
        "Na podstawie poniższych pytań udziel odpowiedzi, używając formatu JSON, gdzie dla każdego obszaru podajesz odpowiedzi na pytania cząstkowe.\n\n"
        "Pytania:\n\n"
        "1. Wymagane kwalifikacje/doświadczenie:\n"
        "   a) Czy szczegółowo opisano wymagane kwalifikacje i doświadczenie?\n"
        "   b) Czy opis umożliwia ocenę, które wymagania są niezbędne, a które dodatkowym atutem?\n\n"
        "2. Zadania na stanowisku pracy:\n"
        "   a) Czy szczegółowo opisano zadania na stanowisku pracy?\n\n"
        "3. Wynagrodzenie:\n"
        "   a) Czy wskazano możliwą wysokość wynagrodzenia lub widełki?\n\n"
        "4. Proces aplikowania - szczególne potrzeby:\n"
        "   a) Czy zawarto informację o możliwości zgłoszenia szczególnych potrzeb na etapie rekrutacji?\n"
        "   b) Czy uwzględniono możliwość rekrutacji online?\n\n"
        "5. Onboarding/wdrażanie:\n"
        "   a) Czy opisano sposób wdrożenia nowego pracownika do zespołu?\n\n"
        "6. Rozwój - podnoszenie kwalifikacji:\n"
        "   a) Czy umieszczono informację o możliwościach podnoszenia kwalifikacji (np. szkolenia, kursy)?\n\n"
        "7. Rozwój - ścieżka awansu:\n"
        "   a) Czy wskazano możliwą ścieżkę awansu lub informację o braku takiej możliwości?\n\n"
        "8. Otwartość na zatrudnianie osób z niepełnosprawnościami:\n"
        "   a) Czy zawarto informację, że firma zatrudnia już osoby z niepełnosprawnościami?\n"
        "   b) Czy zachęcono osoby z niepełnosprawnościami do aplikowania?\n"
        "   c) Czy nie stawiano wymogu posiadania orzeczenia?\n\n"
        "9. Dostępność:\n"
        "   a) Czy podano informacje o dostępności miejsca pracy (budynku i otoczenia)?\n"
        "   b) Czy opisano dostępność stanowiska pracy?\n\n"
        "10. Benefity:\n"
        "    a) Czy zawarto informacje o benefitach oferowanych przez pracodawcę?\n\n"
        "11. Polityka/strategia różnorodności:\n"
        "    a) Czy uwzględniono informacje o polityce lub strategii różnorodności?\n\n"
        "Treść ogłoszenia:\n{job_ad}\n\n"
        "Proszę odpowiedz w poniższym formacie (każdy klucz to nazwa obszaru):\n"
        "{{\n"
        '  "Wymagane kwalifikacje/doświadczenie": {{\n'
        '      "a": {{\n'
        '          "odpowiedz": "TAK" lub "NIE",\n'
        '          "komentarz": "krótki komentarz"\n'
        '      }},\n'
        '      "b": {{\n'
        '          "odpowiedz": "TAK" lub "NIE",\n'
        '          "komentarz": "krótki komentarz"\n'
        '      }}\n'
        '  }},\n'
        "  ...\n"
        "}}"    )
)

# Inicjalizacja parsera JSON i łańcucha przetwarzania
json_parser = JsonOutputParser()
chain = {
    "job_ad": RunnablePassthrough()
} | matrix_prompt | openai_model | json_parser

def validate_input(content: str) -> bool:
    """Sprawdza poprawność wprowadzonych danych"""
    return bool(content and len(content.strip()) > 10)

@lru_cache(maxsize=100)
def analyze_job_ad(text: str) -> str:
    """Analizuje ogłoszenie o pracę i zwraca wyniki w formacie JSON"""
    content = text.strip() if text else ""
    
    # Walidacja zawartości
    if not content:
        return "⚠️ Nie podano treści ogłoszenia do analizy."
    
    if not validate_input(content):
        return "⚠️ Wprowadzona treść jest zbyt krótka."
    
    # Analiza treści
    try:
        result = chain.invoke({"job_ad": content})
        return result
    except Exception as e:
        logging.error(f"Błąd analizy: {e}")
        return f"Wystąpił błąd podczas analizy: {str(e)}"

st.title("KoREKtor - narzędzie dostępnej rekrutacji")

# Tworzenie dwóch kolumn
left_col, right_col = st.columns([1, 1])
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
import os

def read_document(file, file_type):
    # Zapisujemy plik tymczasowo
    with open(f"temp.{file_type}", "wb") as f:
        f.write(file.getvalue())
    
    # Używamy odpowiedniego loadera
    if file_type == "pdf":
        loader = PyPDFLoader(f"temp.{file_type}")
    else:
        loader = Docx2txtLoader(f"temp.{file_type}")
    
    # Wczytujemy dokumenty i łączymy tekst
    documents = loader.load()
    text_content = "\n".join([doc.page_content for doc in documents])
    
    # Usuwamy plik tymczasowy
    os.remove(f"temp.{file_type}")
    
    return text_content

# Lewa kolumna z polem tekstowym
with left_col:
    uploaded_file = st.file_uploader("Wczytaj plik (DOCX lub PDF)", type=['docx', 'pdf'])
    
    if uploaded_file:
        file_type = "pdf" if uploaded_file.type == "application/pdf" else "docx"
        text_content = read_document(uploaded_file, file_type)
        job_ad = st.text_area("Wklej treść ogłoszenia o pracę", value=text_content, height=500)
    else:
        job_ad = st.text_area("Wklej treść ogłoszenia o pracę", height=500)
        
    analyze_button = st.button("Analizuj ogłoszenie", help="Kliknij, aby przeanalizować treść ogłoszenia")
    clear_button = st.button("Wyczyść", help="Kliknij, aby wyczyścić pole tekstowe")

from docx import Document
from docx.shared import Pt, RGBColor
from io import BytesIO
from datetime import datetime

def create_report(analysis_results: dict) -> BytesIO:
    doc = Document()
    
    # Tytuł raportu
    doc.add_heading('Raport analizy ogłoszenia o pracę', 0)
    
    # Data wygenerowania
    doc.add_paragraph(f'Data wygenerowania: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    doc.add_paragraph('\n')
    
    # Dodanie wyników analizy
    for area, questions in analysis_results.items():
        # Dodaj nagłówek sekcji
        heading = doc.add_heading(level=1)
        heading_run = heading.add_run(area)
        heading_run.font.size = Pt(14)
        
        # Dodaj szczegóły dla każdego pytania cząstkowego
        for question_key, details in questions.items():
            status = "✓" if details["odpowiedz"] == "TAK" else "✗"
            p = doc.add_paragraph()
            p.add_run(f'{question_key}) {status} ').bold = True
            p.add_run(details["komentarz"])
        
        # Dodaj odstęp
        doc.add_paragraph('\n')
    
    # Zapisz do BytesIO
    doc_io = BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

# Prawa kolumna z wynikami
with right_col:
    if analyze_button and job_ad:
        result = analyze_job_ad(job_ad)
        if isinstance(result, dict):
            for area, questions in result.items():
                st.header(area)
                for question_key, details in questions.items():
                    status = "✅" if details["odpowiedz"] == "TAK" else "❌"
                    st.write(f"{question_key}) {status} {details['komentarz']}")
                st.divider()
            
            # Przycisk do pobrania raportu
            report_doc = create_report(result)
            st.download_button(
                label="Pobierz raport DOCX",
                data=report_doc,
                file_name="raport_analizy.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )