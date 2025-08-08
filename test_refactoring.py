"""
Testy jednostkowe dla zrefaktoryzowanych komponentów.

Pokazuje jak nowa architektura ułatwia testowanie.
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from config import KorektorConfig
from document_manager import DocumentManager


class TestKorektorConfig(unittest.TestCase):
    """Testy dla klasy KorektorConfig."""
    
    def test_default_config_creation(self):
        """Test tworzenia domyślnej konfiguracji."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            config = KorektorConfig()
            self.assertEqual(config.pdf_directory, "pdfs")
            self.assertEqual(config.chunk_size, 1000)
            self.assertEqual(config.embedding_model, "text-embedding-3-small")
    
    def test_config_validation_chunk_size(self):
        """Test walidacji rozmiaru chunka."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            config = KorektorConfig(chunk_size=0)
            with self.assertRaises(ValueError):
                config.validate()
    
    def test_config_validation_chunk_overlap(self):
        """Test walidacji overlapping chunków."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            config = KorektorConfig(chunk_size=100, chunk_overlap=200)
            with self.assertRaises(ValueError):
                config.validate()
    
    def test_config_from_env(self):
        """Test tworzenia konfiguracji ze zmiennych środowiskowych."""
        env_vars = {
            'OPENAI_API_KEY': 'test-key',
            'KOREKTOR_PDF_DIR': 'custom_pdfs',
            'KOREKTOR_CHUNK_SIZE': '800',
            'KOREKTOR_LLM_MODEL': 'gpt-4'
        }
        
        with patch.dict(os.environ, env_vars):
            config = KorektorConfig.from_env()
            self.assertEqual(config.pdf_directory, 'custom_pdfs')
            self.assertEqual(config.chunk_size, 800)
            self.assertEqual(config.llm_model, 'gpt-4')
    
    def test_config_for_testing(self):
        """Test konfiguracji testowej."""
        config = KorektorConfig.for_testing()
        self.assertEqual(config.openai_api_key, "test-key")
        self.assertEqual(config.pdf_directory, "test_pdfs")
        self.assertEqual(config.chunk_size, 500)
    
    def test_config_missing_api_key(self):
        """Test braku klucza API."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                KorektorConfig()
    
    def test_config_repr_hides_api_key(self):
        """Test czy reprezentacja ukrywa klucz API."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-1234567890abcdef'}):
            config = KorektorConfig()
            repr_str = repr(config)
            self.assertIn("sk-...cdef", repr_str)
            self.assertNotIn("sk-1234567890abcdef", repr_str)


class TestDocumentManager(unittest.TestCase):
    """Testy dla klasy DocumentManager."""
    
    def setUp(self):
        """Przygotowanie środowiska testowego."""
        self.temp_dir = tempfile.mkdtemp()
        self.pdf_dir = Path(self.temp_dir) / "pdfs"
        self.pdf_dir.mkdir()
        
        # Utwórz fikcyjny plik CSV z bibliografią
        self.bib_file = Path(self.temp_dir) / "test_bibliografia.csv"
        with open(self.bib_file, 'w', encoding='utf-8') as f:
            f.write("filename;opis\n")
            f.write("test.pdf;Test Document Description\n")
        
        # Utwórz fikcyjny plik URLs
        self.urls_file = Path(self.temp_dir) / "test_urls.txt"
        with open(self.urls_file, 'w', encoding='utf-8') as f:
            f.write("https://example.com/page1\n")
            f.write("https://example.com/page2\n")
    
    def tearDown(self):
        """Sprzątanie po testach."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_document_manager_creation(self):
        """Test tworzenia DocumentManager."""
        doc_manager = DocumentManager(
            pdf_directory=str(self.pdf_dir),
            urls_file=str(self.urls_file),
            bibliography_file=str(self.bib_file)
        )
        
        self.assertEqual(doc_manager.pdf_directory, self.pdf_dir)
        self.assertEqual(doc_manager.urls_file, str(self.urls_file))
        self.assertIn("test.pdf", doc_manager.bibliography)
    
    def test_load_bibliography_missing_file(self):
        """Test ładowania bibliografii gdy plik nie istnieje."""
        doc_manager = DocumentManager(
            pdf_directory=str(self.pdf_dir),
            bibliography_file="nonexistent.csv"
        )
        
        self.assertEqual(len(doc_manager.bibliography), 0)
    
    def test_list_pdf_files_empty_directory(self):
        """Test listowania PDF gdy katalog jest pusty."""
        doc_manager = DocumentManager(pdf_directory=str(self.pdf_dir))
        
        pdf_files = doc_manager._list_pdf_files()
        self.assertEqual(len(pdf_files), 0)
    
    def test_pdf_changes_detection(self):
        """Test wykrywania zmian w plikach PDF."""
        doc_manager = DocumentManager(pdf_directory=str(self.pdf_dir))
        
        # Początkowo brak zmian (brak plików)
        self.assertFalse(doc_manager._pdfs_changed())
        
        # Dodaj plik PDF (fikcyjny)
        test_pdf = self.pdf_dir / "test.pdf"
        test_pdf.touch()
        
        # Teraz powinny być zmiany
        self.assertTrue(doc_manager._pdfs_changed())
        
        # Po drugim sprawdzeniu nie powinno być zmian
        self.assertFalse(doc_manager._pdfs_changed())
    
    def test_get_stats(self):
        """Test statystyk DocumentManager."""
        doc_manager = DocumentManager(
            pdf_directory=str(self.pdf_dir),
            urls_file=str(self.urls_file),
            bibliography_file=str(self.bib_file)
        )
        
        stats = doc_manager.get_stats()
        
        self.assertEqual(stats['pdf_files'], 0)  # Pusty katalog
        self.assertEqual(stats['url_sources'], 2)  # 2 URLs w pliku
        self.assertEqual(stats['bibliography_entries'], 1)  # 1 wpis w bibliografii
        self.assertEqual(stats['pdf_directory'], str(self.pdf_dir))
    
    @patch('document_manager.load_url_documents')
    @patch('document_manager.IntelligentPDFChunker')
    def test_load_all_documents_empty_sources(self, mock_chunker, mock_load_urls):
        """Test gdy nie ma żadnych dokumentów do załadowania."""
        # Mock'uj brak dokumentów
        mock_load_urls.return_value = []
        mock_chunker_instance = MagicMock()
        mock_chunker_instance.chunk_documents.return_value = []
        mock_chunker.return_value = mock_chunker_instance
        
        doc_manager = DocumentManager(
            pdf_directory=str(self.pdf_dir),
            urls_file=str(self.urls_file)
        )
        
        with self.assertRaises(ValueError):
            doc_manager.load_all_documents()


class TestIntegration(unittest.TestCase):
    """Testy integracyjne pokazujące współpracę komponentów."""
    
    def test_config_and_document_manager_integration(self):
        """Test integracji Config z DocumentManager."""
        config = KorektorConfig.for_testing()
        
        # DocumentManager powinien używać parametrów z konfiguracji
        doc_manager = DocumentManager(
            pdf_directory=config.pdf_directory,
            urls_file=config.urls_file,
            bibliography_file=config.bibliography_file,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
        
        self.assertEqual(doc_manager.pdf_directory, Path(config.pdf_directory))
        self.assertEqual(doc_manager.urls_file, config.urls_file)
        self.assertEqual(doc_manager.chunker.chunk_size, config.chunk_size)


if __name__ == '__main__':
    # Uruchom testy
    unittest.main(verbosity=2)
