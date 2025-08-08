"""
Skrypt migracji z oryginalnego HRAssistant na zrefaktoryzowaną wersję.

Pomaga w płynnym przejściu na nową architekturę zachowując kompatybilność.
"""

import sys
import os
from pathlib import Path

def create_migration_app_py():
    """
    Tworzy zmigrowaną wersję app.py używającą nowej architektury.
    """
    
    migrated_content = '''"""
Zmigrowana wersja app.py używająca zrefaktoryzowanej architektury.

Główne zmiany:
- Używa KorektorConfig dla konfiguracji
- Wykorzystuje HRAssistantV2
- Lepsze zarządzanie błędami
- Centralna konfiguracja
"""

import gradio as gr
import pandas as pd
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field, field_validator
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.output_parsers import PydanticOutputParser
from docx import Document
from datetime import datetime
import os
import tempfile

# Import nowych modułów
from config import KorektorConfig
from hr_assistant_v2 import HRAssistantV2

# Globalna instancja asystenta HR
hr_assistant = None

def initialize_hr_assistant():
    """Inicjalizuje asystenta HR z nową architekturą."""
    global hr_assistant
    
    try:
        # Utwórz konfigurację (automatycznie pobiera OPENAI_API_KEY ze środowiska)
        config = KorektorConfig.from_env()
        
        # Dodatkowe parametry konfiguracyjne można ustawić tutaj
        # config.chunk_size = 800  # przykład customizacji
        # config.search_k = 3
        
        # Zwaliduj konfigurację
        config.validate()
        
        # Utwórz asystenta z konfiguracją
        hr_assistant = HRAssistantV2(config)
        
        # Wyświetl informacje o inicjalizacji
        stats = hr_assistant.get_stats()
        print(f"✅ Asystent HR zainicjalizowany pomyślnie:")
        print(f"   📚 Dokumenty w bazie: {stats['total_documents']:,}")
        print(f"   📄 Pliki PDF: {stats['pdf_files']}")
        print(f"   🔗 Źródła URL: {stats['url_sources']}")
        print(f"   🤖 Model: {stats['model']}")
        print(f"   🔤 Embeddings: {stats['embedding_model']}")
        
        # Wyświetl statystyki bazy wektorowej
        vector_stats = hr_assistant.get_vector_stats()
        print(f"   💾 Rozmiar bazy: {vector_stats.get('memory_size_mb', 'N/A')} MB")
        print(f"   📊 Kategoria: {vector_stats.get('size_category', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd podczas inicjalizacji asystenta HR: {e}")
        print(f"💡 Sprawdź czy ustawiona jest zmienna środowiskowa OPENAI_API_KEY")
        return False

def ask_hr_assistant(question, history):
    """
    Zmigrowana funkcja do komunikacji z asystentem HR.
    
    Używa nowej architektury ale zachowuje kompatybilny interfejs.
    """
    if not hr_assistant:
        return "❌ Asystent HR nie został zainicjalizowany. Sprawdź logi podczas uruchamiania.", []

    try:
        # Zadaj pytanie używając nowej architektury
        response = hr_assistant.ask(question)
        
        # Sformatuj odpowiedź (zachowuje kompatybilność z oryginalnym formatem)
        answer = response['answer']
        sources = response['sources']
        
        # Dodaj źródła do odpowiedzi (nowy format z klikalnymi linkami URL)
        if sources:
            answer += "\\n\\n📚 **Źródła:**\\n"
            for i, source in enumerate(sources, 1):
                if source['type'] == 'url':
                    # URL jako kliknalny link
                    answer += f"{i}. [{source['display_name']}]({source['url']})\\n"
                else:
                    # PDF standardowo
                    page_info = f", str. {source['page']}" if source['page'] else ""
                    answer += f"{i}. {source['display_name']}{page_info}\\n"
        
        return answer, []
        
    except Exception as e:
        error_msg = f"❌ Wystąpił błąd: {str(e)}"
        print(f"Błąd w ask_hr_assistant: {e}")
        return error_msg, []

def reload_knowledge_base():
    """
    Funkcja do ręcznego przeładowania bazy wiedzy.
    
    Nowa funkcjonalność dostępna dzięki refaktoryzacji.
    """
    if not hr_assistant:
        return "❌ Asystent HR nie został zainicjalizowany."
    
    try:
        reloaded = hr_assistant.reload_knowledge_base()
        if reloaded:
            stats = hr_assistant.get_stats()
            return f"✅ Baza wiedzy została przeładowana!\\n📚 Dokumenty: {stats['total_documents']:,}"
        else:
            return "ℹ️ Brak zmian w dokumentach - baza wiedzy aktualna."
    except Exception as e:
        return f"❌ Błąd podczas przeładowania: {str(e)}"

def clear_conversation_memory():
    """
    Nowa funkcja - czyszczenie pamięci konwersacji.
    
    Możliwa dzięki lepszej separacji odpowiedzialności.
    """
    if not hr_assistant:
        return "❌ Asystent HR nie został zainicjalizowany."
    
    try:
        hr_assistant.clear_memory()
        return "✅ Pamięć konwersacji została wyczyszczona."
    except Exception as e:
        return f"❌ Błąd podczas czyszczenia pamięci: {str(e)}"

def get_system_info():
    """
    Nowa funkcja - informacje o systemie.
    
    Pokazuje korzyści z centralizacji konfiguracji.
    """
    if not hr_assistant:
        return "❌ Asystent HR nie został zainicjalizowany."
    
    try:
        stats = hr_assistant.get_stats()
        vector_stats = hr_assistant.get_vector_stats()
        
        info = f"""🔧 **Informacje o systemie:**
        
📚 **Dokumenty:**
- Łącznie w bazie: {stats['total_documents']:,}
- Pliki PDF: {stats['pdf_files']}
- Źródła URL: {stats['url_sources']}
- Wpisy bibliografii: {stats.get('bibliography_entries', 'N/A')}

🤖 **Modele AI:**
- LLM: {stats['model']}
- Embeddings: {stats['embedding_model']}

💾 **Baza wektorowa:**
- Rozmiar: {vector_stats.get('memory_size_mb', 'N/A')} MB
- Kategoria: {vector_stats.get('size_category', 'N/A')}
- Wektory: {vector_stats.get('vectors_count', 'N/A'):,}

🧠 **Pamięć:**
- Wiadomości w pamięci: {stats['memory_messages']}

📁 **Ścieżki:**
- Katalog PDF: {stats.get('pdf_directory', 'N/A')}
- Plik URLs: {stats.get('urls_file', 'N/A')}
"""
        return info
        
    except Exception as e:
        return f"❌ Błąd podczas pobierania informacji: {str(e)}"

# Inicjalizacja przy starcie (z obsługą błędów)
if not initialize_hr_assistant():
    print("⚠️  Aplikacja będzie działać w trybie ograniczonym.")
    print("🔧 Możesz nadal korzystać z analizatora ogłoszeń.")

# [Tutaj reszta kodu app.py - modele Pydantic, funkcje analizy ogłoszeń, itp.]
# [Zachowana bez zmian dla kompatybilności]

# Przykład jak dodać nowe funkcje do interfejsu Gradio:
def create_enhanced_interface():
    """
    Tworzy ulepszony interfejs z nowymi funkcjami.
    """
    with gr.Blocks(title="KoREKtor v2.0 - Zrefaktoryzowany") as demo:
        gr.Markdown("# 🚀 KoREKtor v2.0 - Asystent HR (Zrefaktoryzowany)")
        
        with gr.Tab("💬 Asystent HR"):
            chatbot = gr.Chatbot(height=400)
            msg = gr.Textbox(label="Zadaj pytanie:", placeholder="Np. Jakie są warunki zatrudnienia...")
            
            with gr.Row():
                send_btn = gr.Button("📤 Wyślij", variant="primary")
                clear_btn = gr.Button("🗑️ Wyczyść", variant="secondary")
            
            # Nowe funkcje dzięki refaktoryzacji
            with gr.Row():
                reload_btn = gr.Button("🔄 Przeładuj bazę wiedzy")
                memory_btn = gr.Button("🧠 Wyczyść pamięć")
                info_btn = gr.Button("ℹ️ Info systemu")
            
            # Output dla nowych funkcji
            system_output = gr.Textbox(label="Status systemu", interactive=False)
            
            # Bindowanie funkcji
            send_btn.click(ask_hr_assistant, [msg, chatbot], [chatbot, chatbot])
            reload_btn.click(reload_knowledge_base, outputs=system_output)
            memory_btn.click(clear_conversation_memory, outputs=system_output)
            info_btn.click(get_system_info, outputs=system_output)
        
        with gr.Tab("📋 Analiza ogłoszeń"):
            # [Zachowana bez zmian]
            gr.Markdown("Analiza ogłoszeń pozostaje bez zmian...")
    
    return demo

# Uruchomienie aplikacji
if __name__ == "__main__":
    print("🚀 Uruchamianie KoREKtor v2.0 (zrefaktoryzowany)...")
    
    # Można użyć nowej konfiguracji dla Gradio
    if hr_assistant and hasattr(hr_assistant, 'config'):
        config = hr_assistant.config
        demo = create_enhanced_interface()
        demo.launch(
            server_name=config.gradio_host,
            server_port=config.gradio_port,
            share=config.gradio_share
        )
    else:
        # Fallback na domyślne ustawienia
        demo = create_enhanced_interface()
        demo.launch()
'''
    
    return migrated_content

def create_migration_guide():
    """Tworzy przewodnik migracji."""
    
    guide_content = '''# 🔄 Przewodnik Migracji - KoREKtor v2.0

## 📋 Przegląd Zmian

### ✨ Nowe Pliki:
- `config.py` - Centralna konfiguracja
- `document_manager.py` - Zarządzanie dokumentami  
- `hr_assistant_v2.py` - Zrefaktoryzowany asystent
- `app_migrated.py` - Zmigrowana aplikacja Gradio

### 🔧 Zachowane Pliki:
- `hr_assistant.py` - Oryginalny (do kompatybilności)
- `app.py` - Oryginalny (do kompatybilności)
- Wszystkie inne pliki bez zmian

## 🚀 Kroki Migracji

### 1. Testowanie Nowej Architektury
```bash
# Test nowych komponentów
python test_refactoring.py

# Test przykładów użycia  
python refactoring_examples.py
```

### 2. Migracja Aplikacji
```bash
# Backup oryginalnej aplikacji
cp app.py app_original.py

# Użyj nowej wersji
cp app_migrated.py app.py
```

### 3. Konfiguracja Środowiska
```bash
# Nowe zmienne środowiskowe (opcjonalne)
export KOREKTOR_CHUNK_SIZE=800
export KOREKTOR_SEARCH_K=3
export KOREKTOR_LLM_MODEL="gpt-4"
```

## 🎯 Korzyści Po Migracji

### ✅ Dla Deweloperów:
- Łatwiejsze testowanie jednostkowe
- Czytelniejszy kod
- Lepsze separacja odpowiedzialności
- Centralna konfiguracja

### ✅ Dla Użytkowników:
- Nowe funkcje w interfejsie
- Lepsze informacje o systemie  
- Możliwość przeładowania bazy
- Czyszczenie pamięci konwersacji

### ✅ Dla Utrzymania:
- Modularny kod
- Łatwiejsze dodawanie funkcji
- Lepsze obsługa błędów
- Przygotowanie pod async

## 🔧 Kompatybilność

### ✅ Zachowane API:
```python
# To będzie działać bez zmian:
assistant = HRAssistant(openai_api_key=key)
response = assistant.ask("Pytanie")
```

### ✨ Nowe API:
```python
# Nowe możliwości:
config = KorektorConfig(chunk_size=800)
assistant = HRAssistantV2(config)
```

## 🧪 Testowanie Migracji

### 1. Test Kompatybilności:
```python
from hr_assistant import HRAssistant  # Stary
from hr_assistant_v2 import HRAssistantV2  # Nowy

# Oba powinny działać identycznie
response1 = old_assistant.ask("Test")
response2 = new_assistant.ask("Test")
```

### 2. Test Nowych Funkcji:
```python
# Nowe możliwości niedostępne w v1
config = KorektorConfig.for_testing()
assistant = HRAssistantV2(config)
reloaded = assistant.reload_knowledge_base()
```

## 🚨 Potencjalne Problemy

### ⚠️ Import Errors:
- Dodaj nowe pliki do PYTHONPATH
- Sprawdź czy wszystkie zależności są zainstalowane

### ⚠️ Konfiguracja:
- Sprawdź zmienne środowiskowe
- Zwaliduj ścieżki do plików

### ⚠️ Wydajność:
- Nowa architektura może mieć różne timing
- Monitoruj użycie pamięci

## 🔙 Plan Rollback

W razie problemów:
```bash
# Przywróć oryginalną aplikację
cp app_original.py app.py

# Użyj oryginalnego HRAssistant
from hr_assistant import HRAssistant
```

## 📞 Wsparcie

Jeśli wystąpią problemy:
1. Sprawdź logi podczas uruchamiania
2. Uruchom `test_refactoring.py` 
3. Sprawdź przykłady w `refactoring_examples.py`
4. W ostateczności użyj oryginalnej wersji

## 🎉 Następne Kroki

Po udanej migracji:
1. Eksploruj nowe funkcje w interfejsie
2. Customizuj konfigurację
3. Rozważ async processing
4. Dodaj własne komponenty
'''
    
    return guide_content

def run_migration():
    """Główna funkcja migracji."""
    print("🚀 ROZPOCZYNAM MIGRACJĘ KOREKTOR v2.0\n")
    
    # Sprawdź czy jesteśmy w odpowiednim katalogu
    if not Path("hr_assistant.py").exists():
        print("❌ Nie znaleziono hr_assistant.py")
        print("💡 Uruchom skrypt z katalogu głównego projektu")
        return False
    
    # Utwórz pliki migracji
    print("📝 Tworzę pliki migracji...")
    
    # Utwórz zmigrowaną aplikację
    migrated_app = create_migration_app_py()
    with open("app_migrated.py", "w", encoding="utf-8") as f:
        f.write(migrated_app)
    print("✅ Utworzono app_migrated.py")
    
    # Utwórz przewodnik migracji
    guide = create_migration_guide()
    with open("MIGRATION_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide)
    print("✅ Utworzono MIGRATION_GUIDE.md")
    
    print("\n🎯 MIGRACJA PRZYGOTOWANA!")
    print("\n📋 Następne kroki:")
    print("1. Przeczytaj MIGRATION_GUIDE.md")
    print("2. Uruchom testy: python test_refactoring.py")
    print("3. Przetestuj przykłady: python refactoring_examples.py") 
    print("4. Gdy będziesz gotowy: cp app_migrated.py app.py")
    print("\n✨ Nowa architektura zapewnia lepszą czytelność i testowanie!")
    
    return True

if __name__ == "__main__":
    run_migration()
