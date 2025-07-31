# KoREKtor: Analizator Dostępności Ogłoszeń i Asystent HR

**KoREKtor** to zaawansowane narzędzie zaprojektowane, aby wspierać pracodawców w tworzeniu bardziej inkluzywnych i dostępnych miejsc pracy dla osób z niepełnosprawnościami. Aplikacja składa się z dwóch głównych modułów dostarczanych w jednym, łatwym w obsłudze interfejsie webowym.

![Logo](logo-korektor.png)

---

## Główne Funkcje

### 1. Analizator Ogłoszeń o Pracę

Moduł ten pozwala na automatyczną analizę ogłoszeń o pracę pod kątem ich dostępności i potencjalnych barier dla kandydatów z niepełnosprawnościami. Użytkownik może wkleić tekst ogłoszenia lub wgrać plik w formacie PDF/DOCX.

- **Inteligentna Analiza:** Wykorzystuje duży model językowy (LLM) do oceny treści na podstawie predefiniowanej matrycy kryteriów.
- **Generowanie Raportów:** Tworzy dwa rodzaje raportów w formacie `.docx`:
  - **Raport Skrócony:** Zawiera kluczowe rekomendacje i podsumowanie.
  - **Raport Pełny:** Oferuje szczegółową analizę każdego punktu z matrycy, wraz z cytatami i sugestiami.
- **Wyniki w Formacie JSON:** Udostępnia wyniki w formacie JSON do dalszej analizy lub integracji.

### 2. Asystent HR

To interaktywny chatbot oparty na wiedzy z wbudowanej bazy dokumentów (poradników, raportów, dobrych praktyk). Asystent odpowiada na pytania związane z zatrudnianiem, rekrutacją i zarządzaniem pracownikami z niepełnosprawnościami w Polsce.

- **Baza Wiedzy:** Opiera się na starannie wyselekcjonowanych plikach PDF.
- **Precyzyjne Odpowiedzi:** Dzięki mechanizmowi RAG (Retrieval-Augmented Generation) odpowiedzi są kontekstowe i bazują na treści dokumentów.
- **Cytowanie Źródeł:** Każda odpowiedź zawiera odwołania do konkretnych dokumentów i numerów stron, co zapewnia wiarygodność.

---

## Instalacja i Uruchomienie

1.  **Klonowanie Repozytorium:**
    ```bash
    git clone <adres-repozytorium>
    cd korektor2
    ```

2.  **Utworzenie i Aktywacja Środowiska Wirtualnego:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instalacja Zależności:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ustawienie Klucza API OpenAI:**
    ```bash
    export OPENAI_API_KEY="<Twój-klucz-API>"
    ```

5.  **Uruchomienie Aplikacji:**
    ```bash
    python3 app.py
    ```
    Aplikacja będzie dostępna pod adresem: `http://127.0.0.1:7860`.

---

## Użycie

### Interfejs Webowy

Po uruchomieniu aplikacji w przeglądarce pojawią się dwa główne narzędzia:

-   **Analizator Ogłoszeń:**
    1.  Wklej tekst ogłoszenia w pole tekstowe lub przeciągnij plik PDF/DOCX.
    2.  Kliknij przycisk **"Analizuj"**.
    3.  Wyniki pojawią się w formacie JSON, a poniżej będą dostępne linki do pobrania raportów.

-   **Asystent HR:**
    1.  Wpisz swoje pytanie w polu tekstowym.
    2.  Kliknij **"Wyślij"**.
    3.  Odpowiedź wraz ze źródłami pojawi się poniżej.

### Dostęp przez API (Gradio)

Aplikacja Gradio automatycznie udostępnia API, które pozwala na zdalne wywoływanie funkcji. Poniżej znajdują się przykłady, jak z niego korzystać.

#### 1. API Analizatora Ogłoszeń

Funkcja `analyze_job_ad` przyjmuje dwa argumenty: tekst ogłoszenia i opcjonalnie plik. Zwraca trzy wartości: JSON z wynikami, plik z pełnym raportem i plik ze skróconym raportem.

**Przykład użycia `curl` (wysyłanie tekstu):**
```bash
curl -X POST http://127.0.0.1:7860/run/predict \
-H "Content-Type: application/json" \
-d '{
  "data": [
    "Treść przykładowego ogłoszenia o pracę...",
    null
  ]
}'
```

**Przykład użycia w Pythonie (`requests`):**
```python
import requests
import json

response = requests.post(
    "http://127.0.0.1:7860/run/predict",
    json={
        "data": [
            "Wymagania: 5 lat doświadczenia w branży.", # Tekst ogłoszenia
            None  # Brak pliku
        ]
    }
)

if response.status_code == 200:
    result = response.json()
    # Wyniki są w kluczu 'data'
    json_output = result['data'][0]
    full_report_path = result['data'][1]['name']
    short_report_path = result['data'][2]['name']
    
    print("Wyniki JSON:", json.dumps(json_output, indent=2))
    print("Ścieżka do pełnego raportu:", full_report_path)
    print("Ścieżka do skróconego raportu:", short_report_path)
else:
    print("Błąd:", response.text)
```

#### 2. API Asystenta HR

Funkcja `ask_hr_assistant` przyjmuje jeden argument: pytanie w formie tekstowej. Zwraca odpowiedź w formacie Markdown.

**Przykład użycia `curl`:**
```bash
curl -X POST http://127.0.0.1:7860/run/predict \
-H "Content-Type: application/json" \
-d '{
  "data": [
    "Jakie są obowiązki pracodawcy wobec pracownika z niepełnosprawnością?"
  ]
}'
```

**Przykład użycia w Pythonie (`requests`):**
```python
import requests

response = requests.post(
    "http://127.0.0.1:7860/run/predict",
    json={
        "data": [
            "Jakie są uprawnienia pracownika z orzeczeniem o niepełnosprawności?"
        ]
    }
)

if response.status_code == 200:
    result = response.json()
    answer = result['data'][0]
    print("Odpowiedź Asystenta:", answer)
else:
    print("Błąd:", response.text)
```

---

## Struktura Projektu

```
/Users/jacek/korektor2/
├── app.py                # Główny plik aplikacji Gradio
├── hr_assistant.py       # Logika asystenta HR i obsługi bazy wiedzy
├── requirements.txt      # Lista zależności Python
├── matryca.csv           # Matryca kryteriów dla analizatora ogłoszeń
├── bibliografia.csv      # Dane bibliograficzne dla źródeł
├── template.docx         # Szablon dla generowanych raportów
├── pdfs/                 # Katalog z dokumentami bazy wiedzy
└── README.md             # Ta dokumentacja
```

---

## Pliki Danych

-   **`matryca.csv`**: Kluczowy plik dla analizatora ogłoszeń. Każdy wiersz definiuje jedno kryterium oceny, zawierając m.in. treść pytania do modelu LLM oraz szablony odpowiedzi.
-   **`bibliografia.csv`**: Plik mapujący nazwy plików PDF na pełne opisy bibliograficzne, używane w odpowiedziach Asystenta HR.

---

## Zależności

Projekt korzysta z następujących głównych bibliotek (pełna lista w `requirements.txt`):

-   `gradio`: Do budowy interfejsu webowego.
-   `langchain` i `langchain-openai`: Do interakcji z modelami językowymi.
-   `pandas`: Do wczytywania i przetwarzania danych z plików CSV.
-   `python-docx`: Do generowania raportów w formacie DOCX.
-   `pypdf` i `docx2txt`: Do odczytu treści z plików.
-   `faiss-cpu`: Do tworzenia wektorowej bazy danych.
-   `tiktoken`: Do tokenizacji tekstu.
-   `pymupdf` i `sentence-transformers`: Do inteligentnego dzielenia dokumentów PDF na fragmenty.