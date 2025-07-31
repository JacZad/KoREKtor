# Dokumentacja Projektu: KorChat - Asystent HR

## 1. Wprowadzenie

**Nazwa projektu:** KorChat (KoREKtor)
**Autor:** Jacek (2024-2025)
**Licencja:** CC-BY-SA-4.0

Niniejszy dokument stanowi kompletną dokumentację techniczną i opisową dla projektu **KorChat**, inteligentnego asystenta HR stworzonego w celu wspierania pracodawców w procesie rekrutacji i zatrudniania osób z niepełnosprawnościami w Polsce.

## 2. Cel Projektu

Głównym celem projektu jest stworzenie zaawansowanego, ale łatwego w obsłudze narzędzia, które dostarcza rzetelnych, precyzyjnych i uźródłowionych informacji na temat prawnych, organizacyjnych i praktycznych aspektów zatrudniania osób z niepełnosprawnościami. Asystent ma za zadanie odpowiadać na pytania w języku naturalnym, eliminując potrzebę przeszukiwania wielu dokumentów i stron internetowych.

## 3. Główne Funkcjonalności

- **Konwersacyjny Interfejs:** Umożliwia prowadzenie rozmowy i zadawanie pytań w języku polskim.
- **Baza Wiedzy z Wielu Źródeł:** Integruje informacje z dokumentów PDF, stron internetowych oraz danych wprowadzonych na stałe.
- **Odpowiedzi Oparte na Kontekście:** Generuje odpowiedzi wyłącznie na podstawie zweryfikowanych danych z bazy wiedzy, co zapewnia ich wiarygodność.
- **Podawanie Źródeł:** Do każdej odpowiedzi dołączana jest lista źródeł (konkretny dokument, strona, sekcja lub URL), co umożliwia weryfikację informacji.
- **Pamięć Konwersacji:** Asystent pamięta kontekst rozmowy (ostatnie 5 interakcji), co pozwala na zadawanie pytań uzupełniających.
- **Inteligentne Przetwarzanie Dokumentów:** Kod dzieli dokumenty PDF na logiczne fragmenty (chun'y) z zachowaniem ich struktury (nagłówki, sekcje), co zwiększa precyzję odpowiedzi.
- **Dwa Interfejsy Użytkownika:**
    - **Interfejs webowy (Gradio):** Przejrzysta i łatwa w obsłudze aplikacja webowa.
    - **Interfejs konsolowy:** Dla zaawansowanych użytkowników, z dodatkowymi komendami (`stats`, `clear`, `exit`).
- **Logowanie Przebiegu Działania:** System zapisuje logi, co ułatwia diagnostykę i monitorowanie.

## 4. Architektura i Technologie

System zbudowany jest w oparciu o nowoczesne biblioteki do przetwarzania języka naturalnego i uczenia maszynowego.

### 4.1. Baza Wiedzy

Źródła danych są trojakiego rodzaju:
1.  **Dokumenty PDF:** Główne źródło merytoryczne, pliki znajdują się w katalogu `pdfs/`.
2.  **Strony Internetowe:** Treści z adresów URL zdefiniowanych w pliku `urls.txt` są automatycznie pobierane.
3.  **Dane "na sztywno" (Hardcoded):** Kluczowe, rzadko zmieniające się dane (np. kwoty dofinansowań PFRON) są wpisane bezpośrednio w kodzie (`hr_assistant.py`), aby zagwarantować ich dostępność i poprawność.

### 4.2. Przetwarzanie Języka Naturalnego (NLP)

- **Model Językowy (LLM):** Sercem systemu jest model **`gpt-4o-mini`** od OpenAI, który generuje odpowiedzi.
- **Framework:** Całość jest zintegrowana przy użyciu frameworka **LangChain**, który orkiestruje przepływ danych między komponentami.

### 4.3. Wektorowa Baza Danych

- **Model Einbeddingów:** Do konwersji tekstu na wektory (liczbowe reprezentacje) używany jest model **`text-embedding-3-small`** od OpenAI.
- **Baza Danych:** Wektory są przechowywane i przeszukiwane w pamięci operacyjnej przy użyciu silnika **FAISS (Facebook AI Similarity Search)**. Umożliwia to błyskawiczne odnajdywanie najbardziej relevantnych semantycznie fragmentów tekstu.

### 4.4. Interfejs Użytkownika

- **Aplikacja Webowa:** Zbudowana przy użyciu biblioteki **Gradio**.
- **Aplikacja Konsolowa:** Standardowy interfejs wejścia/wyjścia w Pythonie.

### 4.5. Przetwarzanie Danych

- **Web Scraping:** Biblioteki `requests` i `BeautifulSoup4` służą do pobierania i analizy treści stron WWW.
- **Przetwarzanie PDF:** Biblioteka `PyMuPDF` (fitz) jest używana do ekstrakcji tekstu i analizy struktury plików PDF.

## 5. Struktura Repozytorium

```
/Users/jacek/korchat/
├─── chatbot.py             # Kod interfejsu webowego Gradio
├─── hr_assistant.py        # Główny plik z logiką asystenta HR
├─── database.py            # Zarządzanie wektorową bazą danych FAISS
├─── add_urls_to_db.py      # Skrypt do pobierania danych z URLi
├─── requirements.txt       # Lista zależności Python
├─── bibliografia.csv       # Dane bibliograficzne do formatowania źródeł
├─── urls.txt               # Lista adresów URL do włączenia do bazy wiedzy
├─── README.md              # Skrócona instrukcja dla Hugging Face
├─── project_description.md # Niniejszy dokument
├─── pdfs/                  # Katalog z dokumentami PDF stanowiącymi bazę wiedzy
└─── ...                    # Inne pliki (grafiki, konfiguracja git)
```

## 6. Jak to Działa? Krok po Kroku

1.  **Inicjalizacja:** Po uruchomieniu, skrypt `hr_assistant.py` (lub `chatbot.py`) tworzy instancję klasy `HRAssistant`.
2.  **Ładowanie Danych:** System wczytuje wszystkie dokumenty PDF, pobiera treści z plików URL i dodaje dane "na sztywno".
3.  **Przetwarzanie (Chunking):** Cała zebrana treść jest dzielona na mniejsze, logiczne fragmenty (`chunky`) z zachowaniem struktury (nagłówki, akapity).
4.  **Tworzenie Wektorów (Embedding):** Każdy fragment tekstu jest przepuszczany przez model `text-embedding-3-small` i zamieniany na wektor numeryczny.
5.  **Budowa Bazy FAISS:** Wszystkie wektory są indeksowane i ładowane do bazy danych FAISS w pamięci RAM.
6.  **Zapytanie Użytkownika:** Pytanie zadane przez użytkownika również jest zamieniane na wektor.
7.  **Wyszukiwanie Semantyczne:** Baza FAISS jest przeszukiwana w celu znalezienia wektorów (czyli fragmentów tekstu) najbardziej podobnych do wektora zapytania.
8.  **Przygotowanie Kontekstu:** Najbardziej pasujące fragmenty tekstu, wraz z historią konwersacji, są formatowane w specjalnym szablonie (prompcie).
9.  **Generowanie Odpowiedzi:** Przygotowany kontekst jest wysyłany do modelu `gpt-4o-mini`, który generuje odpowiedź w języku polskim.
10. **Prezentacja Wyniku:** Użytkownik otrzymuje odpowiedź wraz z precyzyjnie sformatowaną listą źródeł.

## 7. Instalacja i Uruchomienie

**Wymagania:**
- Python 3.10+
- Klucz API OpenAI

**Kroki:**

1.  **Klonowanie Repozytorium:**
    ```bash
    git clone <adres-repozytorium>
    cd korchat
    ```

2.  **Instalacja Zależności:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Konfiguracja Klucza API:**
    Należy ustawić zmienną środowiskową `OPENAI_API_KEY`.
    - Na systemach Linux/macOS:
      ```bash
      export OPENAI_API_KEY='sk-...'
      ```
    - Na systemie Windows:
      ```bash
      set OPENAI_API_KEY=sk-...
      ```

4.  **Przygotowanie Danych:**
    - Umieść pliki PDF w katalogu `pdfs/`.
    - (Opcjonalnie) Zaktualizuj plik `urls.txt` o nowe adresy URL.

5.  **Uruchomienie:**
    - **Interfejs webowy (zalecane):**
      ```bash
      python chatbot.py
      ```
      Aplikacja będzie dostępna pod adresem `http://127.0.0.1:7860`.

    - **Interfejs konsolowy:**
      ```bash
      python hr_assistant.py
      ```

## 8. Użycie

### Interfejs Webowy

Po uruchomieniu `chatbot.py`, otwórz przeglądarkę i wejdź na wskazany adres. Wpisz pytanie w polu tekstowym i naciśnij "Wyślij".

### Interfejs Konsolowy

Po uruchomieniu `hr_assistant.py`, możesz wpisywać pytania bezpośrednio w terminalu. Dostępne są również komendy specjalne:
- `stats`: Wyświetla statystyki bazy wiedzy (liczba dokumentów, chunków itp.).
- `clear`: Resetuje pamięć konwersacji.
- `quit`, `exit`, `q`: Kończy działanie programu.
