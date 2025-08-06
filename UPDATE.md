# 🔄 Instrukcja Aktualizacji - KoREKtor

## Aktualizacja do wersji 2.0

### 1. 📋 Lista Zmian
- ✅ Optymalizacja wydajności - brak ponownego ładowania bazy przy każdym pytaniu
- ✅ Inteligentne cytowanie źródeł z pliku `bibliografia.csv`
- ✅ Czytelniejsze wyświetlanie źródeł bez fragmentów tekstu
- ✅ Nowe narzędzia diagnostyczne i dokumentacja

### 2. 📁 Wymagane Pliki

**NOWY PLIK:** `bibliografia.csv`
```csv
opis;filename
"Autor, Tytuł, Wydawnictwo, Rok";nazwa_pliku.pdf
```

**Przykład:**
```csv
opis;filename
"Gruszczyńska A., Gruntowski M., Osoba z niepełnosprawnością w Twojej firmie, Fundacja Aktywizacja, Warszawa 2024";Niezbednik-pracodawcy-online.pdf
"Kotowska L.; Prawo pracy. Pracownik niepełnosprawny; Państwowa Inspekcja Pracy; wydanie 2/2024";Wydawnictwo PIP - Niepelnosprawny pracownik.pdf
```

### 3. 🚀 Kroki Aktualizacji

1. **Zatrzymaj aplikację**
   ```bash
   # Ctrl+C jeśli uruchomiona w konsoli
   # lub kill -TERM <PID>
   ```

2. **Zaktualizuj kod**
   ```bash
   git pull origin main
   # lub pobierz nowe pliki
   ```

3. **Utwórz plik bibliografia.csv**
   ```bash
   # Skopiuj bibliografia.csv do głównego katalogu
   cp bibliografia.csv /ścieżka/do/projektu/
   ```

4. **Uruchom ponownie**
   ```bash
   python app.py
   ```

### 4. ✅ Weryfikacja

Po uruchomieniu sprawdź logi:
```
INFO:hr_assistant:Załadowano bibliografię dla X dokumentów
INFO:hr_assistant:Baza wektorowa została utworzona
```

Zadaj przykładowe pytanie i sprawdź czy źródła wyświetlają się w nowym formacie:
```
📚 Źródła:
1. Gruszczyńska A., Gruntowski M., Osoba z niepełnosprawnością w Twojej firmie, Fundacja Aktywizacja, Warszawa 2024, str. 15 - Rekrutacja
```

### 5. 🛠️ Rozwiązywanie Problemów

**Problem:** `WARNING: Plik bibliografia.csv nie istnieje`
**Rozwiązanie:** Utwórz plik lub system będzie używał nazw plików

**Problem:** Błąd ładowania bibliografii
**Rozwiązanie:** Sprawdź format CSV - separator `;`, kodowanie UTF-8

**Problem:** Źródła nie wyświetlają się poprawnie
**Rozwiązanie:** Sprawdź czy nazwy plików w CSV dokładnie odpowiadają plikom w `pdfs/`

### 6. 🔄 Rollback (powrót do poprzedniej wersji)

Jeśli wystąpią problemy:
1. Przywróć poprzednią wersję kodu
2. Usuń plik `bibliografia.csv`
3. Uruchom ponownie

### 7. 📊 Nowe Funkcje dla Administratorów

**Statystyki systemu:**
```python
from hr_assistant import HRAssistant
assistant = HRAssistant(api_key="...", pdf_directory="pdfs")
print(assistant.get_stats())
```

**Ręczne przeładowanie bazy wiedzy:**
```python
# Po dodaniu nowych plików PDF:
success = assistant.reload_knowledge_base()
print(f"Przeładowanie: {'sukces' if success else 'brak zmian'}")
```

**Czyszczenie pamięci rozmów:**
```python
assistant.clear_memory()
```

---

## 📞 Kontakt w Sprawie Problemów

W przypadku problemów z aktualizacją:
1. Sprawdź logi w konsoli
2. Zobacz `DEVELOPER.md` - sekcja Debugowanie
3. Sprawdź `CHANGELOG.md` - lista wszystkich zmian
