# 🛠️ Dokumentacja Deweloperska - KoREKtor

## 🏗️ Architektura Systemu

### Komponenty Główne

```
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

## 📂 Struktura Kodu

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
```
Start → Ładowanie bibliografia.csv → Skanowanie PDFs → 
Ekstrakcja tekstu → Chunking → Embeddings → 
Tworzenie FAISS → Ready
```

### 2. Zapytanie do Asystenta
```
Pytanie → Embedding → Similarity Search → 
Retrieval → LLM (GPT-4o-mini) → 
Format Answer + Sources → Response
```

### 3. Analiza Ogłoszenia
```
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
   ```
   ValueError: Brak klucza OPENAI_API_KEY
   ```
   Rozwiązanie: `export OPENAI_API_KEY="sk-..."`

2. **Brak pliku bibliografia.csv**
   ```
   WARNING: Plik bibliografia.csv nie istnieje
   ```
   System będzie używał nazw plików jako fallback.

3. **Błąd ładowania PDF**
   ```
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
- Cache'owanie przetworzonch dokumentów
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
# Development:
python app.py

# Production:
gunicorn app:demo -w 4 -b 0.0.0.0:7860
```

### Docker (przygotowanie)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 7860
CMD ["python", "app.py"]
```

### Zmienne Środowiskowe
```bash
OPENAI_API_KEY=sk-...          # Wymagane
GRADIO_SERVER_NAME=0.0.0.0     # Opcjonalne
GRADIO_SERVER_PORT=7860        # Opcjonalne
```
