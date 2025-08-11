# 🛠️ Dokumentacja Deweloperska - KoREKtor

## 🏗️ Architektura Systemu

### Komponenty Główne

```plaintext
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │    Backend      │    │   Baza Wiedzy   │
│   (Gradio UI)   │◄──►│   (app.py)      │◄──►│     (PDFs)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   HR Assistant  │
                       │(hr_assistant.py)│
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Vector Store   │
                       │     (FAISS)     │
                       └─────────────────┘
```

### Architektura v2.1 (Zrefaktoryzowana)

```plaintext
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │    Backend      │    │   Config        │
│   (Gradio UI)   │◄──►│   (app.py)      │◄──►│  (config.py)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ HRAssistantV2   │
                       │(hr_assistant_v2)│
                       └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
            ┌──────────────┐ ┌─────────┐ ┌──────────────┐
            │DocumentMgr   │ │VectorDB │ │Conversation  │
            │(docs+URLs)   │ │(FAISS)  │ │Memory        │
            └──────────────┘ └─────────┘ └──────────────┘
```plaintext

## 📂 Struktura Kodu - Migracja

### 🚀 Przewodnik Migracji v1 → v2.1

### Korzyści Nowej Architektury

#### 📈 Metryki Poprawy

- **Redukcja złożoności**: Główna klasa z 377 → 250 linii (-34%)
- **Testowalność**: Z 0 → 14 testów jednostkowych
- **Separacja odpowiedzialności**: 1 monolityczna klasa → 3 specjalizowane komponenty
- **Konfiguracja**: Rozproszona → scentralizowana w jednym miejscu

#### 🎯 Zalety Funkcjonalne

- **Łatwiejsze debugowanie**: Wyizolowane komponenty
- **Szybsze rozwój**: Modułowa architektura
- **Lepsze testowanie**: Każdy komponent osobno
- **Elastyczna konfiguracja**: Zmienne środowiskowe

### Opcje Migracji

#### 🔄 Opcja 1: Stopniowa Migracja (Zalecana)

```python
# Krok 1: Użyj v2 równolegle
from hr_assistant import HRAssistant as HRAssistantV1
from hr_assistant_v2 import HRAssistantV2
from config import KorektorConfig

# Krok 2: Porównaj wyniki
config = KorektorConfig()
assistant_v1 = HRAssistantV1()
assistant_v2 = HRAssistantV2(config)

# Krok 3: Testuj identyczność odpowiedzi
question = "Jakie są najlepsze praktyki zatrudniania?"
answer_v1 = assistant_v1.ask(question)
answer_v2 = assistant_v2.ask(question)

# Krok 4: Gdy zadowolony, przełącz import
# from hr_assistant_v2 import HRAssistantV2 as HRAssistant
```plaintext

#### ⚡ Opcja 2: Szybka Migracja

```python
# W app.py zastąp:
# from hr_assistant import HRAssistant
# hr_assistant = HRAssistant()

# Na:
from hr_assistant_v2 import HRAssistantV2
from config import KorektorConfig

config = KorektorConfig.from_env()
hr_assistant = HRAssistantV2(config)
```plaintext

#### 🧪 Opcja 3: A/B Testing

```python
# Użyj zmiennej środowiskowej
import os
if os.getenv("USE_HR_V2", "false").lower() == "true":
    from hr_assistant_v2 import HRAssistantV2
    from config import KorektorConfig
    config = KorektorConfig.from_env()
    hr_assistant = HRAssistantV2(config)
else:
    from hr_assistant import HRAssistant
    hr_assistant = HRAssistant()
   ```bash

### Konfiguracja przez Zmienne Środowiskowe

```bash
# .env file (zmienne środowiskowe)
OPENAI_API_KEY=twój_klucz_api_openai            # Klucz API OpenAI
KOREKTOR_PDF_DIRECTORY=./custom_pdfs
KOREKTOR_CHUNK_SIZE=1500
KOREKTOR_LLM_MODEL=gpt-4
KOREKTOR_EMBEDDING_MODEL=text-embedding-3-large
KOREKTOR_MAX_CHUNKS=8
KOREKTOR_TEMPERATURE=0.2
KOREKTOR_MAX_TOKENS=1000
```

```python
# Automatyczne załadowanie konfiguracji
config = KorektorConfig.from_env()
assistant = HRAssistantV2(config)
```

### Testowanie Migracji

#### Uruchomienie Testów

```bash
# Testy jednostkowe nowej architektury
python -m pytest test_refactoring.py -v

# Przykłady użycia
python refactoring_examples.py

# Automatyczna migracja (opcjonalnie)
python migrate_to_v2.py
```

#### Weryfikacja Kompatybilności

```python
# Test identyczności API
from test_refactoring import TestIntegration
test = TestIntegration()
test.test_v2_maintains_v1_compatibility()  # Sprawdza kompatybilność API
```

---

## 📂 Struktura Kodu - Szczegóły

### `app.py` - Główna Aplikacja

```python
# Główne funkcje:
- initialize_hr_assistant()      # Inicjalizacja przy starcie
- analyze_job_ad()              # Analiza ogłoszeń
- ask_hr_assistant()            # Interface do HR Assistant
- _generate_report()            # Generowanie raportów Word
```

### `hr_assistant.py` - Silnik AI

```python
class HRAssistant:
    # Główne metody:
    - __init__()                    # Inicjalizacja z bibliografią
    - _load_bibliography()          # Ładowanie bibliografia.csv
    - _load_and_process_documents() # Przetwarzanie PDFs
    - ask()                        # Główna metoda odpowiedzi
    - reload_knowledge_base()      # Ręczne przeładowanie
```

### `IntelligentPDFChunker` - Przetwarzanie PDF

```python
class IntelligentPDFChunker:
    - _extract_pdf_structure()     # Ekstrakcja z zachowaniem struktury
    - chunk_documents()            # Inteligentne dzielenie na fragmenty
    - _detect_structure_markers()  # Wykrywanie nagłówków
```

### `config.py` - Centralna Konfiguracja

```python
@dataclass
class KorektorConfig:
    # Parametry konfiguracyjne:
    - pdf_directory: str = "pdfs"
    - chunk_size: int = 1000
    - llm_model: str = "gpt-4o-mini"
    - embedding_model: str = "text-embedding-3-small"
    
    # Metody:
    - from_env()                   # Konfiguracja ze zmiennych środowiskowych
    - for_testing()               # Konfiguracja dla testów
    - validate()                  # Walidacja parametrów
```

### `document_manager.py` - Zarządzanie Dokumentami

```python
class DocumentManager:
    # Odpowiedzialności:
    - load_pdf_documents()        # Ładowanie i przetwarzanie PDF
    - load_url_documents()        # Ładowanie treści z URLs
    - load_all_documents()        # Kombinacja PDF + URLs z chunkowaniem
    - has_changes()               # Wykrywanie zmian w plikach
    - _load_bibliography()        # Zarządzanie opisami bibliograficznymi
```

### `hr_assistant_v2.py` - Zrefaktoryzowany Asystent

```python
class HRAssistantV2:
    # Ulepszona architektura:
    - __init__(config)            # Inicjalizacja z konfiguracją
    - _initialize_knowledge_base() # Delegacja do DocumentManager
    - _format_sources()           # Wydzielone formatowanie źródeł
    - ask()                       # Główna metoda (kompatybilna z v1)
    - reload_knowledge_base()     # Wykorzystuje DocumentManager
```

### `test_refactoring.py` - Testy Jednostkowe

```python
# Klasy testowe:
class TestKorektorConfig:         # Testy konfiguracji
class TestDocumentManager:       # Testy zarządzania dokumentami  
class TestIntegration:           # Testy integracyjne

# 14 testów obejmujących:
- Walidację konfiguracji
- Zarządzanie dokumentami
- Wykrywanie zmian w plikach
- Integrację komponentów
```

## 🔧 Kluczowe Mechanizmy

### 1. Ładowanie Bibliografii

```python
def _load_bibliography(self) -> Dict[str, str]:
    """
    Ładuje bibliografia.csv i mapuje nazwy plików na opisy.
    Format: opis;filename
    """
    df = pd.read_csv("bibliografia.csv", delimiter=';')
    return dict(zip(df['filename'], df['opis']))
```

### 2. Cache'owanie Dokumentów

```python
# Zmienne śledzące stan plików PDF:
self._known_pdfs = set()      # Nazwy znanych plików
self._pdf_mtimes = {}         # Czasy modyfikacji plików

def _pdfs_changed(self) -> bool:
    """Sprawdza czy pliki PDF się zmieniły"""
    # Porównuje current_mtimes z self._pdf_mtimes
```

### 3. Metadane Dokumentów

```python
doc.metadata = {
    "filename": "dokument.pdf",
    "bibliography": "Autor, Tytuł, Wydawca, 2024",  # NOWE!
    "page": 15,
    "section": "Rozdział 3",
    "chunk_id": 0
}
```

### 4. Formatowanie Źródeł

```python
def ask_hr_assistant(question):
    # Nowy format źródeł:
    source_text = f"{i}. {bibliography}"
    if page: source_text += f", str. {page}"
    if section: source_text += f" - _{section}_"
    # Usunięto fragmenty tekstu (snippet)
```

## 📊 Przepływ Danych

### 1. Inicjalizacja Systemu

```text
Start → Ładowanie bibliografia.csv → Skanowanie PDFs → 
Ekstrakcja tekstu → Chunking → Embeddings → 
Tworzenie FAISS → Ready
```

### 2. Zapytanie do Asystenta

```text
Pytanie → Embedding → Similarity Search → 
Retrieval → LLM (GPT-4o-mini) → 
Format Answer + Sources → Response
```

### 3. Analiza Ogłoszenia

```text
Tekst/Plik → Ekstrakcja → Walidacja → 
Analiza LLM → Przetwarzanie → 
Generowanie Raportów → JSON Output
```

## 🐛 Debugowanie

### Logi Systemu

```bash
# Włączenie logów debug:
export PYTHONPATH=$PYTHONPATH:.
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
python app.py
```

### Typowe Problemy

1. **Brak OPENAI_API_KEY**

   ```text
   ValueError: Brak klucza OPENAI_API_KEY
   ```

   Rozwiązanie: `export OPENAI_API_KEY="sk-..."`

2. **Brak pliku bibliografia.csv**

   ```text
   WARNING: Plik bibliografia.csv nie istnieje
   ```

   System będzie używał nazw plików jako fallback.

3. **Błąd ładowania PDF**

   ```text
   ERROR: Błąd podczas przetwarzania PDF
   ```

   Sprawdź format i uszkodzenia pliku PDF.

### Narzędzia Diagnostyczne

```python
# W hr_assistant.py dostępne komendy:
assistant.get_stats()          # Statystyki systemu
assistant.clear_memory()       # Wyczyść pamięć rozmów
assistant.reload_knowledge_base()  # Ręczne przeładowanie
```

## 🧪 Testowanie

### Unit Testy

```bash
# Uruchomienie testów:
python -m pytest tests/

# Test konkretnej funkcji:
python -c "
from hr_assistant import HRAssistant
assistant = HRAssistant(api_key='test', pdf_directory='pdfs')
print(assistant.get_stats())
"
```

### Testy Integracyjne

```python
# Test pełnego pipeline'u:
response = assistant.ask('Test pytanie')
assert 'answer' in response
assert 'sources' in response
assert len(response['sources']) > 0
```

## 🔒 Bezpieczeństwo

### Klucze API

- Nigdy nie commituj kluczy do repozytorium
- Używaj zmiennych środowiskowych
- Rotuj klucze regularnie

### Walidacja Danych

```python
# Sprawdzanie typu pliku:
ALLOWED_EXTENSIONS = ['.pdf', '.docx']
if file_extension not in ALLOWED_EXTENSIONS:
    return error_response
```

## 📈 Optymalizacja

### Wydajność

- Baza wiedzy ładowana raz przy starcie
- Cache'owanie przetworzonych dokumentów
- Efektywne chunking z zachowaniem kontekstu

### Pamięć

- FAISS przechowuje embeddingi w RAM
- Chunki mają ograniczony rozmiar (1000 znaków)
- Automatyczne zarządzanie pamięcią konwersacji (ostatnie 5 wiadomości)

### Monitoring

```python
# Sprawdzanie zużycia zasobów:
stats = assistant.get_stats()
print(f"Dokumenty: {stats['total_documents']}")
print(f"Pliki PDF: {stats['pdf_files']}")
print(f"Pamięć rozmów: {stats['memory_messages']}")
```

## 🚀 Deployment

### Lokalne Uruchomienie

```bash
python app.py
```

Aplikacja jest uruchamiana w domyślnym interfejsie Gradio. Jest w pełni funkcjonalny, poza tym że raport jest wyświetlany w formacie JSON, który może nie być czytelny dla człowieka. Zalecamy wykorzystać endpointy Gradio do przygotowania własnego interfejsu.

### Zmienne Środowiskowe

```bash
OPENAI_API_KEY=sk-...          # Wymagane
GRADIO_SERVER_NAME=0.0.0.0     # Opcjonalne
GRADIO_SERVER_PORT=7860        # Opcjonalne
```
