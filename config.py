"""
Centralna konfiguracja dla KoREKtor.

Zawiera wszystkie parametry konfiguracyjne w jednym miejscu.
"""

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class KorektorConfig:
    """
    Centralna konfiguracja aplikacji KoREKtor.
    
    Grupuje wszystkie parametry konfiguracyjne w jednym miejscu,
    ułatwiając zarządzanie i testowanie.
    """
    
    # Ścieżki do plików i katalogów
    pdf_directory: str = "pdfs"
    urls_file: str = "urls.txt"
    bibliography_file: str = "bibliografia.csv"
    matryca_file: str = "matryca.csv"
    template_file: str = "template.docx"
    
    # Parametry modeli AI
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    
    # Parametry chunkowania
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Parametry wyszukiwania
    search_k: int = 5
    search_type: str = "similarity"
    
    # Parametry pamięci konwersacji
    memory_k: int = 5
    
    # Klucze API
    openai_api_key: Optional[str] = None
    
    # Parametry interfejsu Gradio
    gradio_host: str = "127.0.0.1"
    gradio_port: int = 7860
    gradio_share: bool = False
    
    # Parametry debugowania i logowania
    log_level: str = "INFO"
    enable_debug: bool = False
    
    def __post_init__(self):
        """
        Walidacja konfiguracji po inicjalizacji.
        Automatycznie pobiera klucz API z zmiennej środowiskowej jeśli nie podano.
        """
        if self.openai_api_key is None:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError(
                "Brak klucza OPENAI_API_KEY. "
                "Ustaw zmienną środowiskową lub przekaż w konfiguracji."
            )
    
    @classmethod
    def from_env(cls) -> 'KorektorConfig':
        """
        Tworzy konfigurację z zmiennych środowiskowych.
        
        Zmienne środowiskowe:
        - OPENAI_API_KEY: Klucz API OpenAI
        - KOREKTOR_PDF_DIR: Katalog z plikami PDF
        - KOREKTOR_URLS_FILE: Plik z listą URLs
        - KOREKTOR_LLM_MODEL: Model LLM do użycia
        - KOREKTOR_EMBEDDING_MODEL: Model embeddingów
        - KOREKTOR_CHUNK_SIZE: Rozmiar chunka
        - KOREKTOR_HOST: Host interfejsu Gradio
        - KOREKTOR_PORT: Port interfejsu Gradio
        """
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            pdf_directory=os.getenv("KOREKTOR_PDF_DIR", "pdfs"),
            urls_file=os.getenv("KOREKTOR_URLS_FILE", "urls.txt"),
            llm_model=os.getenv("KOREKTOR_LLM_MODEL", "gpt-4o-mini"),
            embedding_model=os.getenv("KOREKTOR_EMBEDDING_MODEL", "text-embedding-3-small"),
            chunk_size=int(os.getenv("KOREKTOR_CHUNK_SIZE", "1000")),
            gradio_host=os.getenv("KOREKTOR_HOST", "127.0.0.1"),
            gradio_port=int(os.getenv("KOREKTOR_PORT", "7860")),
            gradio_share=os.getenv("KOREKTOR_SHARE", "false").lower() == "true",
            log_level=os.getenv("KOREKTOR_LOG_LEVEL", "INFO"),
            enable_debug=os.getenv("KOREKTOR_DEBUG", "false").lower() == "true"
        )
    
    @classmethod
    def for_testing(cls) -> 'KorektorConfig':
        """
        Tworzy konfigurację dla testów jednostkowych.
        """
        return cls(
            openai_api_key="test-key",
            pdf_directory="test_pdfs",
            urls_file="test_urls.txt",
            bibliography_file="test_bibliografia.csv",
            chunk_size=500,  # Mniejsze chunki dla szybszych testów
            memory_k=2,      # Mniej pamięci dla testów
            log_level="DEBUG"
        )
    
    def validate(self) -> bool:
        """
        Sprawdza poprawność konfiguracji.
        
        Returns:
            bool: True jeśli konfiguracja jest poprawna
            
        Raises:
            ValueError: Jeśli konfiguracja zawiera błędy
        """
        if self.chunk_size <= 0:
            raise ValueError("chunk_size musi być większy od 0")
        
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap nie może być ujemny")
        
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap musi być mniejszy od chunk_size")
        
        if self.memory_k <= 0:
            raise ValueError("memory_k musi być większy od 0")
        
        if self.search_k <= 0:
            raise ValueError("search_k musi być większy od 0")
        
        if self.llm_temperature < 0 or self.llm_temperature > 2:
            raise ValueError("llm_temperature musi być między 0 a 2")
        
        return True
    
    def __repr__(self) -> str:
        """Bezpieczna reprezentacja (ukrywa klucze API)."""
        safe_config = self.__dict__.copy()
        if safe_config.get('openai_api_key'):
            safe_config['openai_api_key'] = f"sk-...{safe_config['openai_api_key'][-4:]}"
        return f"KorektorConfig({safe_config})"


# Domyślna instancja konfiguracji
DEFAULT_CONFIG = KorektorConfig.from_env()
