"""
Zaawansowany system cache'owania i optymalizacji dla dużych baz wektorowych.
"""
import os
import hashlib
import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from hr_assistant import HRAssistant
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class VectorStoreCache:
    """
    System cache'owania bazy wektorowej na dysku z automatyczną detekcją zmian.
    """
    
    def __init__(self, cache_dir: str = "faiss_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"
    
    def _calculate_content_hash(self, pdf_directory: str, urls_file: str) -> str:
        """Oblicza hash zawartości plików PDF i URLs."""
        hash_md5 = hashlib.md5()
        
        # Hash plików PDF
        pdf_path = Path(pdf_directory)
        if pdf_path.exists():
            pdf_files = sorted(pdf_path.glob("*.pdf"))
            for pdf_file in pdf_files:
                # Hash nazwy pliku i rozmiaru (szybsze niż cała zawartość)
                stat = pdf_file.stat()
                hash_md5.update(f"{pdf_file.name}:{stat.st_size}:{stat.st_mtime}".encode())
        
        # Hash pliku URLs
        if os.path.exists(urls_file):
            with open(urls_file, 'r', encoding='utf-8') as f:
                content = f.read()
                hash_md5.update(content.encode())
        
        return hash_md5.hexdigest()
    
    def _save_metadata(self, content_hash: str, stats: Dict[str, Any]):
        """Zapisuje metadane cache."""
        metadata = {
            "content_hash": content_hash,
            "created_at": datetime.now().isoformat(),
            "stats": stats
        }
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    def _load_metadata(self) -> Optional[Dict[str, Any]]:
        """Ładuje metadane cache."""
        if not self.metadata_file.exists():
            return None
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Błąd podczas ładowania metadanych cache: {e}")
            return None
    
    def is_cache_valid(self, pdf_directory: str, urls_file: str) -> bool:
        """Sprawdza czy cache jest aktualny."""
        metadata = self._load_metadata()
        if not metadata:
            return False
        
        current_hash = self._calculate_content_hash(pdf_directory, urls_file)
        return metadata.get("content_hash") == current_hash
    
    def save_vectorstore(self, vectorstore, pdf_directory: str, urls_file: str):
        """Zapisuje bazę wektorową do cache."""
        try:
            from vector_stats import analyze_vector_store
            
            # Zapisz indeks FAISS
            index_path = self.cache_dir / "faiss_index"
            vectorstore.save_local(str(index_path))
            
            # Zapisz metadane
            content_hash = self._calculate_content_hash(pdf_directory, urls_file)
            stats = analyze_vector_store(vectorstore)
            self._save_metadata(content_hash, stats)
            
            logger.info(f"Baza wektorowa zapisana w cache: {self.cache_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania do cache: {e}")
            return False
    
    def load_vectorstore(self, embeddings):
        """Ładuje bazę wektorową z cache."""
        try:
            from langchain_community.vectorstores import FAISS
            
            index_path = self.cache_dir / "faiss_index"
            if not index_path.exists():
                return None
            
            vectorstore = FAISS.load_local(str(index_path), embeddings, allow_dangerous_deserialization=True)
            
            metadata = self._load_metadata()
            if metadata:
                stats = metadata.get("stats", {})
                logger.info(f"Załadowano bazę z cache: {stats.get('vectors_count', 0):,} wektorów, "
                           f"{stats.get('memory_size_mb', 0)} MB")
            
            return vectorstore
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania z cache: {e}")
            return None
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Zwraca informacje o cache."""
        metadata = self._load_metadata()
        if not metadata:
            return {"exists": False}
        
        index_path = self.cache_dir / "faiss_index"
        
        return {
            "exists": True,
            "created_at": metadata.get("created_at"),
            "content_hash": metadata.get("content_hash"),
            "stats": metadata.get("stats", {}),
            "cache_size_mb": self._get_cache_size_mb(),
            "index_exists": index_path.exists()
        }
    
    def _get_cache_size_mb(self) -> float:
        """Oblicza rozmiar cache na dysku."""
        total_size = 0
        for file_path in self.cache_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)
    
    def clear_cache(self):
        """Czyści cache."""
        import shutil
        try:
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Cache wyczyszczony")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas czyszczenia cache: {e}")
            return False


class LazyVectorStore:
    """
    Lazy wrapper dla bazy wektorowej - ładuje tylko gdy potrzebne.
    """
    
    def __init__(self, hr_assistant_factory, cache_enabled: bool = True):
        self.hr_assistant_factory = hr_assistant_factory
        self.cache_enabled = cache_enabled
        self._vectorstore = None
        self._cache = VectorStoreCache() if cache_enabled else None
    
    @property
    def vectorstore(self):
        """Lazy loading bazy wektorowej."""
        if self._vectorstore is None:
            self._vectorstore = self._load_or_create_vectorstore()
        return self._vectorstore
    
    def _load_or_create_vectorstore(self):
        """Ładuje z cache lub tworzy nową bazę."""
        hr_assistant = self.hr_assistant_factory()
        
        # Próbuj załadować z cache
        if self.cache_enabled and self._cache:
            if self._cache.is_cache_valid(hr_assistant.pdf_directory, hr_assistant.urls_file):
                logger.info("Ładuję bazę wektorową z cache...")
                cached_vectorstore = self._cache.load_vectorstore(hr_assistant.embeddings)
                if cached_vectorstore:
                    return cached_vectorstore
                else:
                    logger.warning("Nie udało się załadować z cache, tworzę nową bazę")
            else:
                logger.info("Cache nieaktualny, tworzę nową bazę wektorową")
        
        # Stwórz nową bazę
        logger.info("Tworzę nową bazę wektorową...")
        vectorstore = self._create_fresh_vectorstore(hr_assistant)
        
        # Zapisz do cache
        if self.cache_enabled and self._cache and vectorstore:
            self._cache.save_vectorstore(vectorstore, hr_assistant.pdf_directory, hr_assistant.urls_file)
        
        return vectorstore
    
    def _create_fresh_vectorstore(self, hr_assistant):
        """Tworzy świeżą bazę wektorową."""
        # Użyj logiki z HRAssistant
        hr_assistant._load_and_process_documents()
        return hr_assistant.vectorstore
    
    def invalidate_cache(self):
        """Unieważnia cache."""
        if self._cache:
            self._cache.clear_cache()
        self._vectorstore = None
    
    def get_cache_info(self):
        """Zwraca informacje o cache."""
        if not self._cache:
            return {"cache_enabled": False}
        return self._cache.get_cache_info()


def create_optimized_hr_assistant(openai_api_key: str, pdf_directory: str = "pdfs", 
                                use_cache: bool = True) -> 'HRAssistant':
    """
    Tworzy zoptymalizowanego asystenta HR z cache'owaniem.
    """
    from hr_assistant import HRAssistant
    
    if use_cache:
        cache = VectorStoreCache()
        
        # Sprawdź czy można użyć cache
        if cache.is_cache_valid(pdf_directory, "urls.txt"):
            logger.info("🚀 Używam cache'owanej bazy wektorowej")
            
            # Stwórz asystenta normalnie, ale zastąp vectorstore
            hr = HRAssistant(openai_api_key, pdf_directory)
            
            # Załaduj z cache i zastąp vectorstore
            cached_vectorstore = cache.load_vectorstore(hr.embeddings)
            
            if cached_vectorstore:
                hr.vectorstore = cached_vectorstore
                hr._setup_qa_chain()  # Ustaw ponownie qa_chain z nowym vectorstore
                logger.info("✅ Asystent HR załadowany z cache")
                return hr
        
        logger.info("Cache nieaktualny, tworzę nową bazę...")
    
    # Fallback - stwórz normalnie
    hr = HRAssistant(openai_api_key, pdf_directory)
    
    # Zapisz do cache jeśli włączony
    if use_cache:
        cache = VectorStoreCache()
        cache.save_vectorstore(hr.vectorstore, pdf_directory, "urls.txt")
    
    return hr


if __name__ == "__main__":
    # Test cache'owania
    import os
    
    print("🧪 Test systemu cache'owania...")
    
    cache = VectorStoreCache()
    print(f"Cache info: {cache.get_cache_info()}")
    
    # Test zoptymalizowanego asystenta
    hr = create_optimized_hr_assistant(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        use_cache=True
    )
    
    hr.print_vector_stats()
