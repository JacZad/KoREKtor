"""
Przykład użycia zrefaktoryzowanej architektury HRAssistant.

Pokazuje korzyści z nowego podejścia:
- Łatwiejsza konfiguracja
- Lepsze testowanie
- Czytelniejszy kod
- Separacja odpowiedzialności
"""

from config import KorektorConfig
from hr_assistant_v2 import HRAssistantV2
from document_manager import DocumentManager


def example_basic_usage():
    """Podstawowe użycie z domyślną konfiguracją."""
    print("🔥 PRZYKŁAD 1: Podstawowe użycie")
    
    # Prosta inicjalizacja - używa domyślnej konfiguracji
    assistant = HRAssistantV2()
    
    # Zadaj pytanie
    response = assistant.ask("Jakie są warunki ubiegania się o dofinansowanie?")
    print(f"Odpowiedź: {response['answer'][:100]}...")
    print(f"Liczba źródeł: {len(response['sources'])}")


def example_custom_config():
    """Użycie z niestandardową konfiguracją."""
    print("\n🔧 PRZYKŁAD 2: Niestandardowa konfiguracja")
    
    # Utwórz niestandardową konfigurację
    config = KorektorConfig(
        chunk_size=800,  # Mniejsze chunki
        search_k=3,     # Mniej wyników wyszukiwania
        memory_k=3,     # Krótsza pamięć konwersacji
        llm_temperature=0.1  # Bardziej deterministyczne odpowiedzi
    )
    
    assistant = HRAssistantV2(config)
    
    # Pokaż statystyki
    stats = assistant.get_stats()
    print(f"Model: {stats['model']}")
    print(f"Dokumenty w bazie: {stats['total_documents']}")
    print(f"Pliki PDF: {stats['pdf_files']}")


def example_environment_config():
    """Użycie z konfiguracją ze zmiennych środowiskowych."""
    print("\n🌍 PRZYKŁAD 3: Konfiguracja ze środowiska")
    
    # Konfiguracja pobierana automatycznie ze zmiennych środowiskowych
    config = KorektorConfig.from_env()
    print(f"Model LLM: {config.llm_model}")
    print(f"Katalog PDF: {config.pdf_directory}")
    print(f"Rozmiar chunka: {config.chunk_size}")


def example_testing_config():
    """Konfiguracja dla testów."""
    print("\n🧪 PRZYKŁAD 4: Konfiguracja testowa")
    
    # Specjalna konfiguracja dla testów
    test_config = KorektorConfig.for_testing()
    print(f"Katalog testowy: {test_config.pdf_directory}")
    print(f"Rozmiar chunka dla testów: {test_config.chunk_size}")
    
    # W testach używalibyśmy mock dla OpenAI API
    # assistant = HRAssistantV2(test_config)


def example_document_manager_standalone():
    """Użycie DocumentManager jako samostatnego komponentu."""
    print("\n📚 PRZYKŁAD 5: Standalone DocumentManager")
    
    # DocumentManager można używać niezależnie
    doc_manager = DocumentManager(
        pdf_directory="pdfs",
        chunk_size=500,
        chunk_overlap=100
    )
    
    # Sprawdź statystyki dokumentów
    stats = doc_manager.get_stats()
    print(f"Pliki PDF: {stats['pdf_files']}")
    print(f"URL sources: {stats['url_sources']}")
    print(f"Bibliografia: {stats['bibliography_entries']}")
    
    # Sprawdź czy są zmiany w plikach
    has_changes = doc_manager.has_changes()
    print(f"Wykryto zmiany w plikach: {has_changes}")


def example_error_handling():
    """Przykład obsługi błędów."""
    print("\n❌ PRZYKŁAD 6: Obsługa błędów")
    
    try:
        # Próba utworzenia konfiguracji z błędnymi parametrami
        bad_config = KorektorConfig(
            chunk_size=0,  # Błędny parametr
            chunk_overlap=-1  # Błędny parametr
        )
        bad_config.validate()
    except ValueError as e:
        print(f"Wykryto błąd konfiguracji: {e}")
    
    try:
        # Konfiguracja bez klucza API
        no_api_config = KorektorConfig(openai_api_key="")
    except ValueError as e:
        print(f"Brak klucza API: {e}")


def example_migration_from_v1():
    """Jak migrować z oryginalnego HRAssistant."""
    print("\n🔄 PRZYKŁAD 7: Migracja z wersji 1")
    
    # STARY SPOSÓB (v1):
    # from hr_assistant import HRAssistant
    # assistant_v1 = HRAssistant(
    #     openai_api_key=api_key,
    #     pdf_directory="pdfs",
    #     urls_file="urls.txt"
    # )
    
    # NOWY SPOSÓB (v2):
    config = KorektorConfig(
        pdf_directory="pdfs",
        urls_file="urls.txt"
        # openai_api_key pobierane automatycznie ze środowiska
    )
    assistant_v2 = HRAssistantV2(config)
    
    # API pozostaje takie samo!
    # response = assistant_v2.ask("Pytanie")
    
    print("✅ Migracja zachowuje kompatybilność API")


if __name__ == "__main__":
    print("🚀 DEMONSTRACJA ZREFAKTORYZOWANEJ ARCHITEKTURY\n")
    
    # Uruchom wszystkie przykłady
    example_basic_usage()
    example_custom_config() 
    example_environment_config()
    example_testing_config()
    example_document_manager_standalone()
    example_error_handling()
    example_migration_from_v1()
    
    print("\n✨ KORZYŚCI Z REFAKTORYZACJI:")
    print("✅ Centralna konfiguracja")
    print("✅ Łatwiejsze testowanie") 
    print("✅ Lepsza separacja odpowiedzialności")
    print("✅ Czytelniejszy kod")
    print("✅ Kompatybilność wsteczna")
    print("✅ Możliwość używania komponentów niezależnie")
