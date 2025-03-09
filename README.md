# KoREKtor - narzędzie dostępnej rekrutacji

KoREKtor to aplikacja webowa stworzona w Streamlit, która pomaga analizować ogłoszenia o pracę pod kątem dostępności dla osób z niepełnosprawnościami.

[Demo aplikacji](https://ko-rektor.streamlit.app/)

## Funkcjonalności

- Analiza treści ogłoszeń o pracę z wykorzystaniem AI (GPT-3.5)
- Ocena 11 kluczowych obszarów dostępności
- Generowanie szczegółowych raportów z komentarzami
- Intuicyjny interfejs z podziałem na dwie kolumny

## Analizowane obszary

1. Wymagane kwalifikacje/doświadczenie
2. Zadania na stanowisku pracy 
3. Wynagrodzenie
4. Proces aplikowania
5. Onboarding/wdrażanie
6. Rozwój - podnoszenie kwalifikacji
7. Rozwój - ścieżka awansu
8. Otwartość na zatrudnianie osób z niepełnosprawnościami
9. Dostępność miejsca i stanowiska pracy
10. Benefity
11. Polityka/strategia różnorodności

## Technologie

- Python 3.x
- Streamlit - framework do tworzenia aplikacji webowych
- LangChain - integracja z modelami językowymi (langchain-openai, langchain-core, langchain-community)
- OpenAI GPT-4 - model językowy do analizy treści
- Pandas - obsługa danych
- python-docx - obsługa plików DOCX
- Obsługa plików PDF

## Funkcjonalności

- Analiza treści ogłoszeń o pracę z wykorzystaniem AI (GPT-4)
- Możliwość wczytywania plików DOCX i PDF
- Generowanie raportów w formacie DOCX
- Ocena 11 kluczowych obszarów dostępności
- Generowanie szczegółowych raportów z komentarzami
- Intuicyjny interfejs z podziałem na dwie kolumny

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/JacZad/KoREKtor.git
```

Aby zainstalować zaktualizowane zależności, należy wykonać:

```bash
pip install -r requirements.txt
```
2. Zainstaluj wymagane zależności:
```bash
pip install -r requirements.txt
```

3. Ustaw zmienną środowiskową z kluczem API OpenAI:
```bash
export OPENAI_API_KEY='twój-klucz-api'
```

4. Uruchom aplikację:
```bash
streamlit run app.py
```

## Użycie

1. Wklej treść ogłoszenia o pracę w pole tekstowe po lewej stronie
2. Kliknij przycisk "Analizuj ogłoszenie"
3. Zobacz wyniki analizy w formie tabeli po prawej stronie

## Logowanie

Aplikacja zapisuje logi do pliku app.log, co pomaga w monitorowaniu działania i debugowaniu.

## Licencja

MIT License

## Autorzy

- Agata Gawska
- Jacek Zadrożny

## Kontakt

[Link do profilu GitHub](https://github.com/JacZad)