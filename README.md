---
title: KoREKtor
emoji: 👀
colorFrom: yellow
colorTo: green
sdk: gradio
sdk_version: 5.24.0
app_file: app.py
pinned: false
---

# KoREKtor - Analizator Ogłoszeń o Pracę

![Logo KoREKtora](logo-korektor.png)

KoREKtor to narzędzie wykorzystujące sztuczną inteligencję do analizy ogłoszeń o pracę pod kątem dostępności dla osób z niepełnosprawnościami.

## Do autorstwa przyznają się:

- [Agata Gawska](https://www.linkedin.com/in/agata-gawska-b74506205/) - ogólna koncepcja, opracowanie matrycy, schematu działania i przeprowadzenie testów.
- [Jacek Zadrożny](https://linkedin.com/in/jaczad) - programowanie, dobór technologii, wdrażanie, dokumentacja.

![Belka z logotypami](belka.png)

## Funkcjonalności

- Analiza tekstu ogłoszenia o pracę pod kątem dostępności
- Automatyczna ocena 16 różnych obszarów dostępności
- Generowanie szczegółowych rekomendacji dla rekruterów
- Wskazywanie cytatów z ogłoszenia uzasadniających ocenę
- Obsługa różnych formatów plików (TXT, DOCX, PDF)
- Interfejs użytkownika oparty na Gradio

## Jak to działa?

KoREKtor wykorzystuje modele językowe OpenAI do analizy treści ogłoszeń o pracę. Aplikacja sprawdza, czy ogłoszenie spełnia kryteria dostępności dla osób z niepełnosprawnościami zgodnie z opracowaną matrycą oceny. Dla każdego kryterium system generuje:

1. Ocenę (TAK/NIE)
2. Cytat z ogłoszenia uzasadniający ocenę
3. Konkretne rekomendacje poprawy
4. Dodatkowe informacje i wskazówki

## Wymagania

- Python 3.8+
- Zainstalowane zależności z pliku requirements.txt
- Klucz API OpenAI

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/jaczad/korektor.git
cd korektor
```

2. Zainstaluj wymagane zależności:
```bash
pip install -r requirements.txt
```

3. Ustaw zmienną środowiskową z kluczem API OpenAI:
```bash
export OPENAI_API_KEY='twój-klucz-api'
```

## Użycie

1. Uruchom aplikację:
```bash
python app.py
```

2. Otwórz przeglądarkę i przejdź pod wskazany adres (domyślnie http://127.0.0.1:7860)
3. Wklej tekst ogłoszenia o pracę do pola tekstowego lub prześlij plik
4. Kliknij "Submit" aby otrzymać analizę

## Struktura projektu

- `app.py` - główny plik aplikacji z interfejsem Gradio
- `matryca.csv` - plik zawierający matrycę pytań i kryteriów oceny
- `requirements.txt` - lista wymaganych bibliotek
- `logo-korektor.png` - logo projektu
- `belka.png` - grafika z logotypami

## Model danych

Analiza wykorzystuje dwa główne modele Pydantic:
- `QuestionAnswer` - reprezentuje pojedyncze pytanie i odpowiedź
- `JobAdAnalysis` - zawiera pełną analizę ogłoszenia

## Wynik analizy

Wynik zwracany jest w formacie JSON zawierającym:
- Obszar analizy
- Odpowiedź (TAK/NIE)
- Cytat z tekstu
- Rekomendacje
- Dodatkowe informacje

## Wersja online

<!-- Aplikacja jest również dostępna online na platformie [Deklaracja-dostepnosci.info](https://deklaracja-dostepnosci.info/korektor)


## Współpraca i rozwój

Zachęcamy do zgłaszania uwag i propozycji ulepszeń poprzez system Issues na GitHubie.

## Licencja

Ten projekt jest udostępniany na licencji [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

[Polityka prywatności](polityka.md)