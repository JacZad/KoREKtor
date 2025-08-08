"""
DocumentManager - Zarządzanie dokumentami PDF i URL.

Wydzielona klasa odpowiedzialna za:
- Ładowanie plików PDF
- Ładowanie treści z URLs  
- Śledzenie zmian w plikach
- Zarządzanie bibliografią
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd

from langchain_core.documents import Document
from pdf_chunker import IntelligentPDFChunker
from web_loader import load_url_documents

logger = logging.getLogger(__name__)


class DocumentManager:
    """
    Zarządza ładowaniem i przetwarzaniem dokumentów PDF oraz URL.
    
    Odpowiedzialności:
    - Ładowanie i parsowanie plików PDF
    - Ładowanie treści z URLs
    - Śledzenie zmian w plikach PDF  
    - Zarządzanie metadanymi i bibliografią
    """
    
    def __init__(self, 
                 pdf_directory: str = "pdfs", 
                 urls_file: str = "urls.txt",
                 bibliography_file: str = "bibliografia.csv",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        self.pdf_directory = Path(pdf_directory)
        self.urls_file = urls_file
        self.bibliography_file = bibliography_file
        
        # Śledzenie zmian w plikach PDF
        self._known_pdfs = set()
        self._pdf_mtimes = {}
        
        # Komponenty
        self.chunker = IntelligentPDFChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Załaduj bibliografię
        self.bibliography = self._load_bibliography()
    
    def _load_bibliography(self) -> Dict[str, str]:
        """
        Ładuje bibliografię z pliku CSV.
        Zwraca słownik mapujący nazwę pliku na pełny opis bibliograficzny.
        """
        bibliography_path = Path(self.bibliography_file)
        if not bibliography_path.exists():
            logger.warning(f"Plik {self.bibliography_file} nie istnieje. Będą używane nazwy plików.")
            return {}
        
        try:
            df = pd.read_csv(bibliography_path, delimiter=';')
            bibliography = {}
            for _, row in df.iterrows():
                filename = row['filename']
                opis = row['opis']
                bibliography[filename] = opis
            logger.info(f"Załadowano bibliografię dla {len(bibliography)} dokumentów")
            return bibliography
        except Exception as e:
            logger.error(f"Błąd podczas ładowania bibliografii: {e}")
            return {}
    
    def _list_pdf_files(self) -> List[Path]:
        """Zwraca listę plików PDF w katalogu."""
        return list(self.pdf_directory.glob("*.pdf"))
    
    def _pdfs_changed(self) -> bool:
        """
        Sprawdza, czy pojawiły się nowe pliki PDF lub zmieniły się istniejące.
        """
        changed = False
        current_pdfs = set()
        current_mtimes = {}
        
        for pdf in self._list_pdf_files():
            current_pdfs.add(pdf.name)
            mtime = pdf.stat().st_mtime
            current_mtimes[pdf.name] = mtime
            
            if (pdf.name not in self._pdf_mtimes) or (self._pdf_mtimes.get(pdf.name) != mtime):
                changed = True
        
        if self._known_pdfs != current_pdfs:
            changed = True
            
        if changed:
            self._known_pdfs = current_pdfs
            self._pdf_mtimes = current_mtimes
            
        return changed
    
    def load_pdf_documents(self) -> List[Document]:
        """
        Ładuje i przetwarza wszystkie dokumenty PDF.
        Dodaje metadane bibliograficzne.
        """
        pdf_files = self._list_pdf_files()
        if not pdf_files:
            logger.warning(f"Nie znaleziono plików PDF w katalogu: {self.pdf_directory}")
            return []
        
        all_documents = []
        logger.info(f"Znaleziono {len(pdf_files)} plików PDF")
        
        for pdf_file in pdf_files:
            logger.info(f"Przetwarzanie PDF: {pdf_file.name}")
            documents = self.chunker._extract_pdf_structure(str(pdf_file))
            
            for doc in documents:
                doc.metadata["filename"] = pdf_file.name
                doc.metadata["file_stem"] = pdf_file.stem
                
                # Dodaj pełny opis bibliograficzny jeśli dostępny
                if pdf_file.name in self.bibliography:
                    doc.metadata["bibliography"] = self.bibliography[pdf_file.name]
                else:
                    doc.metadata["bibliography"] = pdf_file.stem  # fallback na nazwę pliku
            
            all_documents.extend(documents)
        
        logger.info(f"Wyekstraktowano {len(all_documents)} sekcji z PDF")
        return all_documents
    
    def load_url_documents(self) -> List[Document]:
        """Ładuje dokumenty z URLs."""
        return load_url_documents(self.urls_file)
    
    def load_all_documents(self) -> List[Document]:
        """
        Ładuje wszystkie dokumenty (PDF + URLs) i zwraca po chunkowaniu.
        """
        logger.info("Ładowanie dokumentów PDF i treści z URLs...")
        
        # Ładowanie PDF
        pdf_documents = self.load_pdf_documents()
        
        # Ładowanie treści z URLs
        url_documents = self.load_url_documents()
        
        # Połącz wszystkie dokumenty
        all_documents = pdf_documents + url_documents
        
        if not all_documents:
            raise ValueError("Nie znaleziono żadnych dokumentów do przetworzenia (ani PDF ani URLs)")
        
        logger.info(f"Łącznie dokumentów do przetworzenia: {len(all_documents)} "
                   f"(PDF: {len(pdf_documents)}, URLs: {len(url_documents)})")
        
        # Chunkowanie
        chunked_documents = self.chunker.chunk_documents(all_documents)
        logger.info(f"Utworzono {len(chunked_documents)} chunków")
        
        # Aktualizuj śledzenie plików PDF po pomyślnym załadowaniu
        self._update_pdf_tracking()
        
        return chunked_documents
    
    def _update_pdf_tracking(self):
        """Aktualizuje zmienne śledzące pliki PDF po pomyślnym załadowaniu."""
        self._known_pdfs = set()
        self._pdf_mtimes = {}
        for pdf_file in self._list_pdf_files():
            self._known_pdfs.add(pdf_file.name)
            self._pdf_mtimes[pdf_file.name] = pdf_file.stat().st_mtime
    
    def has_changes(self) -> bool:
        """
        Sprawdza czy są zmiany w dokumentach (głównie PDF).
        """
        return self._pdfs_changed()
    
    def get_stats(self) -> Dict[str, Any]:
        """Zwraca statystyki dokumentów."""
        # Policz URLs z pliku
        url_count = 0
        if os.path.exists(self.urls_file):
            try:
                with open(self.urls_file, 'r', encoding='utf-8') as f:
                    url_count = len([line.strip() for line in f 
                                   if line.strip() and not line.startswith('#')])
            except:
                pass
        
        return {
            "pdf_files": len(self._list_pdf_files()),
            "url_sources": url_count,
            "bibliography_entries": len(self.bibliography),
            "pdf_directory": str(self.pdf_directory),
            "urls_file": self.urls_file
        }
