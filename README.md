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


- Analiza tekstu ogłoszenia o pracę
- Automatyczna ocena 16 różnych obszarów dostępności
- Generowanie szczegółowych rekomendacji
- Wskazywanie cytatów uzasadniających ocenę

## Wymagania

- Python 3.8+
- Zainstalowane zależności z pliku requirements.txt
- Klucz API OpenAI

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://huggingface.co/spaces/jaczad/Rekruter
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

2. Otwórz przeglądarkę i przejdź pod wskazany adres
3. Wklej tekst ogłoszenia o pracę do pola tekstowego
4. Kliknij "Submit" aby otrzymać analizę

## Struktura projektu

- `app.py` - główny plik aplikacji
- `matryca.csv` - plik zawierający matrycę pytań i kryteriów oceny
- `requirements.txt` - lista wymaganych bibliotek

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

[Polityka prywatności](polityka.md)