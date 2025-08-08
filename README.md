# KoREKtor: Analizator Dostępności Ogłoszeń i Asystent HR

**KoREKtor** to zaawansowane narzędzie zaprojektowane, aby wspierać pracodawców w tworzeniu bardziej inkluzywnych i dostępnych miejsc pracy dla osób z niepełnosprawnościami. Aplikacja składa się z dwóch głównych modułów dostarczanych w jednym, łatwym w obsłudze interfejsie webowym.

![Logo](logo-korektor.png)

---

## 🎯 Główne Funkcje

### 1. 📋 Analizator Ogłoszeń o Pracę

Moduł ten pozwala na automatyczną analizę ogłoszeń o pracę pod kątem ich dostępności i potencjalnych barier dla kandydatów z niepełnosprawnościami. Użytkownik może wkleić tekst ogłoszenia lub wgrać plik w formacie PDF/DOCX.

- **🧠 Inteligentna Analiza:** Wykorzystuje duży model językowy (LLM) do oceny treści na podstawie predefiniowanej matrycy kryteriów.
- **📄 Generowanie Raportów:** Tworzy dwa rodzaje raportów w formacie `.docx`:
  - **Raport Skrócony:** Zawiera kluczowe rekomendacje i podsumowanie.
  - **Raport Pełny:** Oferuje szczegółową analizę każdego punktu z matrycy, wraz z cytatami i sugestiami.
- **📊 Wyniki w Formacie JSON:** Udostępnia wyniki w formacie JSON do dalszej analizy lub integracji.

### 2. 🤖 Asystent HR

To interaktywny chatbot oparty na wiedzy z wbudowanej bazy dokumentów (poradników, raportów, dobrych praktyk) **oraz aktualnych informacji ze stron internetowych PFRON**. Asystent odpowiada na pytania związane z zatrudnianiem, rekrutacją i zarządzaniem pracownikami z niepełnosprawnościami w Polsce.

- **📚 Baza Wiedzy:** Opiera się na starannie wyselekcjonowanych plikach PDF z pełną bibliografią **oraz treściach ze stron PFRON**
- **🌐 Aktualne Informacje:** Automatycznie ładuje treści z 21 stron PFRON z pliku `urls.txt`
- **🎯 Precyzyjne Odpowiedzi:** Dzięki mechanizmowi RAG (Retrieval-Augmented Generation) odpowiedzi są kontekstowe i bazują na treści dokumentów oraz stron internetowych
- **📖 Cytowanie Źródeł:** Każda odpowiedź zawiera pełne opisy bibliograficzne dokumentów z numerami stron i sekcjami oraz linki do stron internetowych
- **⚡ Optymalizacja Wydajności:** Baza wiedzy jest ładowana tylko raz przy starcie, co zapewnia szybkie odpowiedzi

---

## 🚀 Najnowsze Funkcje (v2.0)

### ✨ Inteligentne Cytowanie Źródeł
- **📖 Pełne Opisy Bibliograficzne:** System automatycznie ładuje pełne cytowania z pliku `bibliografia.csv`
- **🔍 Precyzyjne Lokalizacje:** Każde źródło zawiera dokładny numer strony i sekcję dokumentu
- **🎯 Czytelne Formatowanie:** Źródła wyświetlane są w eleganckim formacie bez fragmentów tekstu
- **🔗 Klikalne Linki URL:** Źródła internetowe wyświetlane jako klikalne linki z czystymi tytułami

### ⚡ Optymalizacja Wydajności
- **🚫 Koniec Ponownego Ładowania:** Baza wiedzy jest tworzona tylko raz przy starcie aplikacji
- **🔄 Inteligentne Cache'owanie:** System pamięta przetworzony stan dokumentów PDF
- **📊 Monitoring Zmian:** Opcjonalne ręczne przeładowanie przy dodaniu nowych dokumentów
- **💾 Statystyki Bazy Wektorowej:** Monitoring rozmiaru i wydajności bazy (18.05 MB, kategoria: mała)

### 📚 Zarządzanie Bibliografią
- **📋 Centralna Baza Opisów:** Plik `bibliografia.csv` zawiera pełne opisy wszystkich dokumentów
- **🔧 Łatwa Aktualizacja:** Wystarczy edytować plik CSV aby zmienić cytowania
- **📖 Profesjonalne Standardy:** Zgodność z akademickimi standardami cytowania

### 🏗️ Refaktoryzacja Architektury (v2.1)
- **🔧 Modularna Struktura:** Kod podzielony na specjalizowane komponenty (DocumentManager, Config)
- **🧪 Łatwiejsze Testowanie:** 14 testów jednostkowych, możliwość mockowania komponentów
- **⚙️ Centralna Konfiguracja:** Wszystkie parametry w jednym miejscu z walidacją
- **🔄 Kompatybilność Wsteczna:** Zachowana pełna kompatybilność API z poprzednią wersją
- **🚀 Przygotowanie na Przyszłość:** Architektura gotowa na async processing i nowe funkcje

---

## ⚡ Jak Uruchomić

1. **Klonowanie Repozytorium:**
   
   ```bash
   git clone [URL_REPOZYTORIUM]
   cd korektor2
   ```

2. **Utworzenie i Aktywacja Środowiska Wirtualnego:**
   
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # lub
   venv\Scripts\activate  # Windows
   ```

3. **Instalacja Zależności:**
   
   ```bash
   pip install -r requirements.txt
   ```

4. **Ustawienie Klucza API OpenAI:**
   
   ```bash
   export OPENAI_API_KEY="twój_klucz_api_openai"
   ```

5. **Uruchomienie Aplikacji:**
   
   ```bash
   python app.py
   ```
   
6. **Otwórz Przeglądarkę:** Przejdź pod adres `http://localhost:7860`

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
├── app.py                    # Główny plik aplikacji Gradio
├── hr_assistant.py           # Logika asystenta HR (wersja oryginalna)
├── hr_assistant_v2.py        # Zrefaktoryzowana wersja asystenta HR
├── document_manager.py       # Zarządzanie dokumentami PDF i URL
├── config.py                 # Centralna konfiguracja aplikacji
├── vector_stats.py           # Statystyki i monitoring bazy wektorowej
├── vector_optimization.py    # Optymalizacja i cache'owanie wektorów
├── requirements.txt          # Lista zależności Python
├── matryca.csv              # Matryca kryteriów dla analizatora ogłoszeń
├── bibliografia.csv         # Dane bibliograficzne dla źródeł
├── urls.txt                 # Lista URL źródeł PFRON
├── template.docx            # Szablon dla generowanych raportów
├── pdfs/                    # Katalog z dokumentami bazy wiedzy
├── faiss_cache/             # Cache bazy wektorowej (auto-generated)
├── test_refactoring.py      # Testy jednostkowe nowej architektury
├── refactoring_examples.py  # Przykłady użycia nowej architektury
├── migrate_to_v2.py         # Skrypt migracji na nową architekturę
├── REFACTORING_PROPOSALS.md # Propozycje i analiza refaktoryzacji
└── README.md                # Ta dokumentacja
```

---

## 📁 Pliki Danych

- **`matryca.csv`**: Kluczowy plik dla analizatora ogłoszeń. Każdy wiersz definiuje jedno kryterium oceny, zawierając m.in. treść pytania do modelu LLM oraz szablony odpowiedzi.
- **`bibliografia.csv`**: **NOWE!** 📚 Plik mapujący nazwy plików PDF na pełne opisy bibliograficzne, używane w odpowiedziach Asystenta HR. Format: `opis;filename`
- **`template.docx`**: Szablon Microsoft Word używany do generowania raportów analizy ogłoszeń.
- **`pdfs/`**: Katalog zawierający dokumenty bazy wiedzy (poradniki, raporty, przepisy prawne).

### Przykład `bibliografia.csv`:
```csv
opis;filename
"Gruszczyńska A., Gruntowski M., Osoba z niepełnosprawnością w Twojej firmie, Fundacja Aktywizacja, Warszawa 2024";Niezbednik-pracodawcy-online.pdf
"Kotowska L.; Prawo pracy. Pracownik niepełnosprawny; Państwowa Inspekcja Pracy; wydanie 2/2024";Wydawnictwo PIP - Niepelnosprawny pracownik.pdf
```

---

## 🛠️ Zależności

Projekt korzysta z następujących głównych bibliotek (pełna lista w `requirements.txt`):

- **Interface i Backend:**
  - `gradio`: Do budowy interfejsu webowego
  - `pandas`: Do przetwarzania danych CSV

- **AI i NLP:**
  - `langchain` i `langchain-openai`: Framework do pracy z modelami językowymi
  - `faiss-cpu`: Wektorowa baza danych do przeszukiwania semantycznego
  - `tiktoken`: Tokenizacja tekstu dla OpenAI

- **Przetwarzanie Dokumentów:**
  - `python-docx`: Generowanie raportów Word
  - `pypdf` i `docx2txt`: Odczyt plików PDF/DOCX
  - `pymupdf`: Inteligentna ekstrakcja tekstu z PDF
  - `sentence-transformers`: Zaawansowane embeddingi tekstowe

---

## � Migracja na Nową Architekturę

KoREKtor oferuje zrefaktoryzowaną architekturę (v2.1) z lepszą modularyzacją i testowalnocią, zachowując pełną kompatybilność wsteczną.

### 🎯 Opcje Przełączenia

#### 1. Stopniowe Przejście (Zalecane)
```python
# W app.py - dodaj na górze:
USE_NEW_ARCHITECTURE = False  # Ustaw True gdy chcesz przełączyć

if USE_NEW_ARCHITECTURE:
    from hr_assistant_v2 import HRAssistantV2 as HRAssistant
    from config import KorektorConfig
    
    def initialize_hr_assistant():
        config = KorektorConfig.from_env()
        return HRAssistant(config)
else:
    from hr_assistant import HRAssistant
    
    def initialize_hr_assistant():
        return HRAssistant(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            pdf_directory="pdfs"
        )
```

#### 2. Przez Zmienną Środowiskową
```bash
export KOREKTOR_USE_V2=true
python app.py
```

#### 3. Testowanie Komponentów
```bash
# Testy nowej architektury
python test_refactoring.py

# Przykłady użycia
python refactoring_examples.py

# Skrypt migracji (tworzy pomocnicze pliki)
python migrate_to_v2.py
```

### ✨ Korzyści Nowej Architektury

- **🏗️ Modularna Struktura:** Oddzielne komponenty dla dokumentów, konfiguracji i logiki
- **🧪 Łatwiejsze Testowanie:** 14 testów jednostkowych, możliwość mockowania
- **⚙️ Centralna Konfiguracja:** Wszystkie parametry w `config.py` z walidacją
- **🔄 Kompatybilność Wsteczna:** Identyczne API - istniejący kod działa bez zmian
- **🚀 Przygotowanie na Przyszłość:** Async processing, event system, caching

### 📋 Pliki Związane z Refaktoryzacją

- `hr_assistant_v2.py` - Nowa implementacja asystenta
- `document_manager.py` - Zarządzanie dokumentami
- `config.py` - Centralna konfiguracja
- `test_refactoring.py` - Testy nowej architektury
- `refactoring_examples.py` - Przykłady użycia
- `migrate_to_v2.py` - Narzędzia migracji
- `REFACTORING_PROPOSALS.md` - Szczegółowa analiza zmian

---

## �🔧 Konfiguracja

### Zmienne Środowiskowe
```bash
export OPENAI_API_KEY="sk-..." # Klucz API OpenAI (wymagany)
```

### Struktura Katalogów
```
pdfs/           # Dokumenty bazy wiedzy (PDF)
├── dokument1.pdf
├── dokument2.pdf
└── ...
```

### Pliki Konfiguracyjne
## 📚 Dokumentacja

- **`README.md`** - Ten plik - główny przewodnik użytkownika
- **`CHANGELOG.md`** - Historia zmian i nowych funkcji
- **`DEVELOPER.md`** - Dokumentacja techniczna dla deweloperów
- **`project_description.md`** - Szczegółowy opis projektu i architektury

## 🤝 Wsparcie

W przypadku problemów lub pytań:
1. Sprawdź sekcję **Debugowanie** w `DEVELOPER.md`
2. Przejrzyj **Changelog** w `CHANGELOG.md`
3. Sprawdź logi aplikacji w konsoli

## 📄 Licencja

CC-BY-SA-4.0 - szczegóły w pliku LICENSE