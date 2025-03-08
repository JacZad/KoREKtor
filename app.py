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
    "model_name": "gpt-3.5-turbo",
    "temperature": 0.0,
    "max_tokens": 1000
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
        "Na podstawie poniższych pytań udziel odpowiedzi, używając formatu JSON, gdzie dla każdego obszaru podajesz:\n"
        "- \"opis\": odpowiedź TAK lub NIE,\n"
        "- \"komentarz\": krótki komentarz wyjaśniający.\n\n"
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
        '  "Nazwa obszaru": {{\n'
        '      "opis": "TAK" lub "NIE",\n'
        '      "komentarz": "krótki komentarz"\n'
        "  }},\n"
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

  # Lewa kolumna z polem tekstowym
with left_col:
      job_ad = st.text_area("Wklej treść ogłoszenia o pracę", height=500)
      analyze_button = st.button("Analizuj ogłoszenie", help="Kliknij, aby przeanalizować treść ogłoszenia")
      clear_button = st.button("Wyczyść", help="Kliknij, aby wyczyścić pole tekstowe")

  # Prawa kolumna z tabelą wyników
with right_col:
      if analyze_button and job_ad:
          st.markdown("""
          | Obszar | Status | Komentarz |
          |--------|--------|-----------|
          | Otwartość na zatrudnianie | ✅ | Firma zachęca do aplikowania |
          | Dostępność | ❌ | Brak informacji o dostępności |
          | Benefity | ✅ | Wymienione świadczenia |
          | Polityka różnorodności | ✅ | Wspomniana polityka D&I |
          """)