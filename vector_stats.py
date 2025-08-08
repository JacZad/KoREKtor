"""
Narzędzia do analizy i optymalizacji bazy wektorowej FAISS.
"""
import os
import pickle
import psutil
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VectorStoreAnalyzer:
    """
    Analizator wydajności i rozmiaru bazy wektorowej FAISS.
    """
    
    def __init__(self, vectorstore=None):
        self.vectorstore = vectorstore
        
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """
        Zwraca kompletne statystyki bazy wektorowej.
        """
        if not self.vectorstore:
            return {"error": "Brak bazy wektorowej do analizy"}
        
        stats = {}
        
        try:
            # Podstawowe statystyki FAISS
            num_vectors = self.vectorstore.index.ntotal
            vector_dim = self.vectorstore.index.d
            
            # Rozmiar w pamięci (float32 = 4 bajty)
            memory_size_bytes = num_vectors * vector_dim * 4
            memory_size_mb = memory_size_bytes / (1024 * 1024)
            memory_size_gb = memory_size_mb / 1024
            
            stats.update({
                'vectors_count': num_vectors,
                'vector_dimensions': vector_dim,
                'memory_size_bytes': memory_size_bytes,
                'memory_size_mb': round(memory_size_mb, 2),
                'memory_size_gb': round(memory_size_gb, 3),
            })
            
            # Statystyki dokumentów
            if hasattr(self.vectorstore, 'docstore') and hasattr(self.vectorstore.docstore, '_dict'):
                docs = self.vectorstore.docstore._dict
                
                # Analiza źródeł
                pdf_docs = sum(1 for doc in docs.values() 
                              if hasattr(doc, 'metadata') and 
                              not doc.metadata.get('source', '').startswith('https://'))
                url_docs = sum(1 for doc in docs.values() 
                              if hasattr(doc, 'metadata') and 
                              doc.metadata.get('source', '').startswith('https://'))
                
                # Analiza rozmiarów chunków
                chunk_sizes = []
                for doc in docs.values():
                    if hasattr(doc, 'page_content'):
                        chunk_sizes.append(len(doc.page_content))
                
                if chunk_sizes:
                    stats.update({
                        'pdf_chunks': pdf_docs,
                        'url_chunks': url_docs,
                        'total_chunks': len(chunk_sizes),
                        'avg_chunk_size': round(sum(chunk_sizes) / len(chunk_sizes)),
                        'min_chunk_size': min(chunk_sizes),
                        'max_chunk_size': max(chunk_sizes),
                        'large_chunks_count': len([x for x in chunk_sizes if x > 2000]),
                    })
            
            # Użycie pamięci procesu
            process = psutil.Process(os.getpid())
            process_memory_mb = process.memory_info().rss / (1024 * 1024)
            stats['process_memory_mb'] = round(process_memory_mb, 2)
            
            # Typ modelu embeddings
            if hasattr(self.vectorstore, '_embedding_function'):
                embedding_func = self.vectorstore._embedding_function
                stats['embedding_model'] = getattr(embedding_func, 'model', 'unknown')
                stats['embedding_type'] = type(embedding_func).__name__
            
            # Klasyfikacja rozmiaru
            stats['size_category'] = self._classify_size(memory_size_mb)
            stats['recommendations'] = self._get_recommendations(memory_size_mb, num_vectors)
            
        except Exception as e:
            stats['error'] = f"Błąd podczas analizy: {e}"
            logger.error(f"Błąd w get_comprehensive_stats: {e}")
        
        return stats
    
    def _classify_size(self, memory_mb: float) -> str:
        """Klasyfikuje rozmiar bazy."""
        if memory_mb < 50:
            return "mała"
        elif memory_mb < 200:
            return "średnia"
        elif memory_mb < 1000:
            return "duża"
        else:
            return "bardzo_duża"
    
    def _get_recommendations(self, memory_mb: float, num_vectors: int) -> list:
        """Zwraca rekomendacje na podstawie rozmiaru bazy."""
        recommendations = []
        
        if memory_mb > 2000:  # > 2GB
            recommendations.extend([
                "Rozważ zapisanie bazy na dysk z opcją lazy loading",
                "Użyj kompresji wektorów (quantization)",
                "Podziel bazę na mniejsze segmenty",
                "Rozważ użycie zewnętrznej bazy wektorowej (Pinecone, Weaviate)"
            ])
        elif memory_mb > 500:  # > 500MB
            recommendations.extend([
                "Monitoruj użycie pamięci",
                "Rozważ cache'owanie na dysku dla rzadko używanych wektorów",
                "Optymalizuj rozmiar chunków"
            ])
        elif num_vectors > 10000:
            recommendations.append("Duża liczba wektorów - monitoruj wydajność wyszukiwania")
        
        if not recommendations:
            recommendations.append("Baza ma optymalny rozmiar")
        
        return recommendations
    
    def print_stats(self):
        """Wyświetla sformatowane statystyki."""
        stats = self.get_comprehensive_stats()
        
        if 'error' in stats:
            print(f"❌ {stats['error']}")
            return
        
        print("=" * 50)
        print("📊 STATYSTYKI BAZY WEKTOROWEJ FAISS")
        print("=" * 50)
        
        print(f"🔢 Liczba wektorów: {stats['vectors_count']:,}")
        print(f"📐 Wymiary wektora: {stats['vector_dimensions']}")
        print(f"💾 Rozmiar w pamięci: {stats['memory_size_mb']} MB ({stats['memory_size_gb']} GB)")
        print(f"📱 Pamięć procesu: {stats['process_memory_mb']} MB")
        
        if 'total_chunks' in stats:
            print(f"\n📄 Analiza dokumentów:")
            print(f"   • PDF chunków: {stats['pdf_chunks']:,}")
            print(f"   • URL chunków: {stats['url_chunks']:,}")
            print(f"   • Łącznie chunków: {stats['total_chunks']:,}")
            print(f"   • Średni rozmiar chunka: {stats['avg_chunk_size']} znaków")
            print(f"   • Zakres: {stats['min_chunk_size']} - {stats['max_chunk_size']} znaków")
            if stats['large_chunks_count'] > 0:
                print(f"   • Dużych chunków (>2000): {stats['large_chunks_count']}")
        
        if 'embedding_model' in stats:
            print(f"\n🤖 Model embeddings: {stats['embedding_model']}")
            print(f"🔧 Typ: {stats['embedding_type']}")
        
        print(f"\n📊 Kategoria rozmiaru: {stats['size_category']}")
        
        print(f"\n💡 Rekomendacje:")
        for rec in stats['recommendations']:
            print(f"   • {rec}")
        
        print("=" * 50)


class VectorStoreOptimizer:
    """
    Optymalizator bazy wektorowej dla dużych zbiorów danych.
    """
    
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        
    def save_to_disk(self, save_path: str):
        """Zapisz bazę FAISS na dysk."""
        try:
            save_path = Path(save_path)
            save_path.mkdir(parents=True, exist_ok=True)
            
            # Zapisz indeks FAISS
            index_path = save_path / "faiss_index"
            self.vectorstore.save_local(str(index_path))
            
            logger.info(f"Baza zapisana w: {index_path}")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania bazy: {e}")
            return False
    
    def load_from_disk(self, load_path: str, embeddings):
        """Załaduj bazę FAISS z dysku."""
        try:
            from langchain_community.vectorstores import FAISS
            
            load_path = Path(load_path) / "faiss_index"
            vectorstore = FAISS.load_local(str(load_path), embeddings)
            
            logger.info(f"Baza załadowana z: {load_path}")
            return vectorstore
        except Exception as e:
            logger.error(f"Błąd podczas ładowania bazy: {e}")
            return None
    
    def create_compressed_index(self, compression_factor: int = 4):
        """
        Tworzy skompresowaną wersję indeksu (wymaga faiss-gpu lub zaawansowanych funkcji).
        """
        try:
            import faiss
            
            # To jest zaawansowana funkcja - wymaga odpowiedniej wersji FAISS
            original_index = self.vectorstore.index
            
            # Utwórz kompresowany indeks PQ (Product Quantization)
            d = original_index.d
            m = d // compression_factor  # Liczba segmentów
            
            pq = faiss.IndexPQ(d, m, 8)  # 8 bitów na segment
            pq.train(original_index.reconstruct_n(0, original_index.ntotal))
            pq.add(original_index.reconstruct_n(0, original_index.ntotal))
            
            # Zastąp oryginalny indeks
            self.vectorstore.index = pq
            
            logger.info(f"Utworzono skompresowany indeks z kompresją {compression_factor}x")
            return True
            
        except ImportError:
            logger.warning("Kompresja wymaga zaawansowanej wersji FAISS")
            return False
        except Exception as e:
            logger.error(f"Błąd podczas kompresji: {e}")
            return False


# Funkcje pomocnicze do integracji z istniejącym kodem
def analyze_vector_store(vectorstore):
    """Szybka analiza bazy wektorowej."""
    analyzer = VectorStoreAnalyzer(vectorstore)
    return analyzer.get_comprehensive_stats()

def print_vector_stats(vectorstore):
    """Wyświetl statystyki bazy wektorowej."""
    analyzer = VectorStoreAnalyzer(vectorstore)
    analyzer.print_stats()

def optimize_large_vectorstore(vectorstore, save_path: str = "faiss_cache"):
    """Optymalizuj dużą bazę wektorową."""
    optimizer = VectorStoreOptimizer(vectorstore)
    
    # Zapisz na dysk
    success = optimizer.save_to_disk(save_path)
    if success:
        print(f"✅ Baza zapisana w {save_path}")
        print("💡 Możesz teraz ładować bazę z dysku zamiast tworzyć ją od nowa")
    
    return success


if __name__ == "__main__":
    # Test z istniejącą bazą
    from hr_assistant import HRAssistant
    import os
    
    print("🔍 Analizuję bazę wektorową...")
    
    hr = HRAssistant(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        pdf_directory='pdfs'
    )
    
    # Wyświetl pełne statystyki
    print_vector_stats(hr.vectorstore)
    
    # Sprawdź czy warto zapisać na dysk
    stats = analyze_vector_store(hr.vectorstore)
    if stats.get('memory_size_mb', 0) > 100:
        print("\n💾 Zapisuję bazę na dysk dla przyszłego użytku...")
        optimize_large_vectorstore(hr.vectorstore)
