# 📝 Changelog - KoREKtor

Wszystkie istotne zmiany w projekcie KoREKtor są dokumentowane w tym pliku.

## [2.0.0] - 2025-08-06

### ✨ Nowe Funkcje

#### 📚 Inteligentne Zarządzanie Bibliografią
- **Dodano plik `bibliografia.csv`** z pełnymi opisami bibliograficznymi dokumentów
- **Automatyczne ładowanie opisów** - system mapuje nazwy plików na pełne cytowania
- **Profesjonalne formatowanie źródeł** - zgodne z akademickimi standardami

#### ⚡ Optymalizacja Wydajności
- **Usunięto ponowne ładowanie bazy wiedzy** przy każdym pytaniu do asystenta HR
- **Dodano inteligentne cache'owanie** - baza wiedzy tworzona tylko raz przy starcie
- **Wprowadzono śledzenie zmian plików PDF** - opcjonalne ręczne przeładowanie
- **Dodano metodę `reload_knowledge_base()`** dla ręcznego odświeżania

#### 🎯 Ulepszenia UX
- **Usunięto fragmenty tekstu** z listy źródeł - czystsze wyświetlanie
- **Poprawiono formatowanie cytowań** - nazwa dokumentu, strona, sekcja
- **Dodano fallback dla brakujących opisów** bibliograficznych

### 🔧 Zmiany Techniczne

#### Klasa `HRAssistant`
- Dodano metodę `_load_bibliography()` do ładowania opisów z CSV
- Rozszerzono metadane dokumentów o pole `bibliography`
- Usunięto `self._reload_if_pdfs_changed()` z metody `ask()`
- Dodano poprawne ustawianie zmiennych śledzących pliki PDF

#### Funkcja `ask_hr_assistant()` w `app.py`
- Zmieniono wyświetlanie źródeł na pełne opisy bibliograficzne
- Usunięto wyświetlanie fragmentów tekstu (`snippet`)
- Dodano obsługę sekcji i numerów stron

### 📁 Nowe Pliki
- `bibliografia.csv` - Baza opisów bibliograficznych
- `CHANGELOG.md` - Ten plik z historią zmian

### 🛠️ Poprawki Błędów
- Naprawiono problem z wielokrotnym tworzeniem bazy wiedzy
- Poprawiono wydajność odpowiedzi asystenta HR
- Ustabilizowano ładowanie metadanych dokumentów

---

## [1.0.0] - 2024

### 🎉 Pierwsza Wersja
- **Analizator ogłoszeń o pracę** z matrycą kryteriów
- **Asystent HR** oparty na bazie dokumentów PDF
- **Interfejs Gradio** z dwoma zakładkami
- **Generowanie raportów Word** (pełny i skrócony)
- **Mechanizm RAG** z wektorową bazą danych FAISS
- **Inteligentny chunking** dokumentów PDF
- **Pamięć konwersacji** dla asystenta HR

---

## 🔮 Planowane Funkcje

### W Przygotowaniu
- [ ] Ładowanie dokumentów z URLs (reaktywacja funkcji)
- [ ] Cache'owanie wektorowej bazy danych na dysku
- [ ] API endpoints dla integracji zewnętrznych
- [ ] Wielojęzyczność interfejsu
- [ ] Rozszerzona analityka użytkowania

### Rozważane
- [ ] Obsługa innych formatów dokumentów (TXT, MD)
- [ ] Integracja z bazami danych
- [ ] Eksport wyników do różnych formatów
- [ ] System powiadomień o aktualizacjach dokumentów
