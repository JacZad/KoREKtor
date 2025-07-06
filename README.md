# KoREKtor - Analizator Ogłoszeń o Pracę

Aplikacja webowa oparta o Gradio i LangChain, która analizuje ogłoszenia o pracę pod kątem ich dostępności i inkluzywności dla osób z niepełnosprawnościami.

## Jak używać?

1.  Uruchom aplikację.
2.  Wklej tekst ogłoszenia w pole tekstowe lub prześlij plik w formacie `.docx` lub `.pdf`.
3.  Kliknij przycisk "Submit".
4.  Po chwili otrzymasz wyniki:
    *   **Wyniki analizy (JSON):** Surowe dane z analizy w formacie JSON, przeznaczone do dalszego, maszynowego przetwarzania.
    *   **Pełny raport Word:** Dokument `.docx` ze szczegółowymi wynikami.
    *   **Skrócony raport Word:** Uproszczona wersja raportu.

## Kluczowe funkcje i architektura

Aplikacja działa w kilku krokach, aby zapewnić dokładność i zoptymalizować koszty.

### 1. Wstępna weryfikacja treści (Funkcja `is_job_ad`)

Aby uniknąć niepotrzebnego przetwarzania i kosztów związanych z API, aplikacja najpierw sprawdza, czy przesłany tekst jest faktycznie ogłoszeniem o pracę.

*   **Ograniczenie kontekstu:** Analizie poddawany jest tylko **pierwsze 1500 znaków** dokumentu. Jest to wystarczające, aby zidentyfikować rodzaj treści, jednocześnie minimalizując zużycie tokenów.
*   **Zapytanie do AI:** Do modelu `gpt-4o-mini` wysyłane jest proste zapytanie z prośbą o klasyfikację tekstu (czy jest to ogłoszenie o pracę?).
*   **Obsługa błędu:** Jeśli tekst nie zostanie rozpoznany jako ogłoszenie, proces jest przerywany, a użytkownik otrzymuje stosowny komunikat.

### 2. Główna analiza (Funkcja `analyze_job_ad`)

Jeśli weryfikacja przebiegnie pomyślnie, rozpoczyna się właściwa analiza całego tekstu ogłoszenia.

*   **Przygotowanie pytań:** Pytania do analizy są dynamicznie tworzone na podstawie pliku `matryca.csv`.
*   **Wywołanie LLM:** Pełny tekst ogłoszenia wraz z pytaniami jest wysyłany do modelu `gpt-4o-mini` za pośrednictwem LangChain.
*   **Przetwarzanie odpowiedzi:** Odpowiedź modelu w formacie JSON jest parsowana i przekształcana w strukturę danych (DataFrame) w celu łatwiejszego generowania raportów.

### 3. Generowanie raportów (Funkcje `_generate_report`, `create_report`, `create_short_report`)

Na podstawie przetworzonych wyników generowane są dwa oddzielne dokumenty Word.

*   **Refaktoryzacja:** Logika tworzenia dokumentu `.docx` została wydzielona do jednej, prywatnej funkcji `_generate_report`, która jest wywoływana z różnymi parametrami w celu stworzenia raportu pełnego i skróconego.
*   **Pełny raport:** Zawiera wszystkie informacje z analizy, w tym dodatkowe wskazówki i kontekst z kolumny `more` w pliku `matryca.csv`.
*   **Skrócony raport:** Prezentuje tylko kluczowe wyniki (obszar, cytat, treść) bez dodatkowych informacji.

## Struktura projektu

*   `app.py`: Główny plik aplikacji zawierający logikę, definicję interfejsu Gradio i interakcję z API OpenAI.
*   `matryca.csv`: Plik konfiguracyjny zawierający kryteria analizy, pytania, treści do raportów i wskazówki.
*   `template.docx`: Szablon dokumentu Word używany do generowania raportów.
*   `requirements.txt`: Lista wymaganych bibliotek Python.
*   `logo-korektor.png`: Logo projektu.
*   `belka.png`: Grafika z logotypami.

## Model danych

Analiza wykorzystuje dwa główne modele Pydantic:
- `QuestionAnswer` - reprezentuje pojedyncze pytanie i odpowiedź
- `JobAdAnalysis` - zawiera pełną analizę ogłoszenia

## Wynik analizy (JSON)

Aplikacja zwraca wynik w formacie JSON, który jest listą obiektów. Każdy obiekt reprezentuje wynik analizy jednego kryterium z `matryca.csv` i zawiera następujące pola:

-   `area` (string): Nazwa obszaru analizy (np. "Język inkluzywny", "Elastyczność pracy").
-   `answer` (string): Odpowiedź "TAK" lub "NIE", wskazująca, czy kryterium zostało spełnione.
-   `citation` (string): Dokładny fragment tekstu z ogłoszenia, który był podstawą do odpowiedzi.
-   `content` (string): Rekomendacja lub komentarz wygenerowany na podstawie odpowiedzi.
-   `more` (string): Dodatkowe wskazówki i informacje kontekstowe (używane w pełnym raporcie).

Ten format jest przeznaczony do łatwej integracji z innymi systemami i narzędziami analitycznymi.

## Wersja online

Aplikacja jest również dostępna online na platformie [Deklaracja-dostepnosci.info](https://deklaracja-dostepnosci.info/korektor)


## Współpraca i rozwój

Zachęcamy do zgłaszania uwag i propozycji ulepszeń poprzez system Issues na GitHubie.

## Licencja

Ten projekt jest udostępniany na licencji [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

[Polityka prywatności](polityka.md)

## Mapa drogowa

- [x] Skrócony raport z analizy.
- [x] Filtrowanie tekstu przesyłanego do aplikacji.
- [ ] Generowanie poprawionego ogłoszenia.
- [ ] Wczytywanie z adresu URL.
Ten projekt jest udostępniany na licencji [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

[Polityka prywatności](polityka.md)

## Mapa drogowa

- [ ] Skrócony raport z analizy.
- [ ] Filtrowanie tekstu przesyłanego do aplikacji.
- [ ] Generowanie poprawionego ogłoszenia.
- [ ] Wczytywanie z adresu URL.
