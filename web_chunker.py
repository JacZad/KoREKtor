"""
Dedykowany chunker dla dokumentów internetowych z lepszym rozpoznawaniem struktury HTML.
"""
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re


class WebContentChunker:
    """
    Chunker specjalnie zaprojektowany dla treści internetowych z PFRON.
    """
    
    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def _detect_web_structure(self, text: str) -> List[str]:
        """
        Wykrywa strukturę typową dla stron PFRON i dzieli tekst na logiczne sekcje.
        """
        # Wzorce typowe dla stron PFRON
        section_patterns = [
            r'\n(?=Krok \d+)',  # Kroki procedur
            r'\n(?=Punkt \d+)',  # Punkty list
            r'\n(?=§ \d+)',      # Paragrafy prawne
            r'\n(?=Art\. \d+)',  # Artykuły prawne
            r'\n(?=Rozdział \d+)', # Rozdziały
            r'\n(?=\d+\.\d+\.)',  # Numeracja wielopoziomowa (1.1., 1.2.)
            r'\n(?=\d+\.)',       # Numeracja (1., 2., 3.)
            r'\n(?=•)',           # Wypunktowania
            r'\n(?=Uwaga:)',      # Uwagi
            r'\n(?=Ważne:)',      # Ważne informacje
            r'\n(?=Przykład:)',   # Przykłady
        ]
        
        # Próbuj podzielić według wzorców
        sections = [text]
        for pattern in section_patterns:
            new_sections = []
            for section in sections:
                parts = re.split(pattern, section)
                new_sections.extend(parts)
            sections = [s.strip() for s in new_sections if s.strip()]
        
        return sections
    
    def chunk_web_documents(self, documents: List[Document]) -> List[Document]:
        """
        Dzieli dokumenty webowe na chunki z uwzględnieniem struktury PFRON.
        """
        chunked_docs = []
        
        for doc in documents:
            # Sprawdź czy to dokument z URL
            if not doc.metadata.get('source', '').startswith('https://'):
                # Dla dokumentów nie-URL użyj standardowego chunkowania
                chunked_docs.append(doc)
                continue
            
            # Jeśli dokument jest mały, zostaw bez dzielenia
            if len(doc.page_content) <= self.chunk_size:
                chunked_docs.append(doc)
                continue
            
            # Wykryj strukturę PFRON
            sections = self._detect_web_structure(doc.page_content)
            
            # Jeśli nie znaleziono sekcji, użyj standardowego chunkowania
            if len(sections) == 1:
                sections = self._standard_chunk(doc.page_content)
            
            # Utwórz chunki z sekcji
            for i, section in enumerate(sections):
                if len(section.strip()) < 50:  # Pomiń bardzo krótkie sekcje
                    continue
                
                # Jeśli sekcja jest nadal za duża, podziel dalej
                if len(section) > self.chunk_size:
                    subsections = self._standard_chunk(section)
                    for j, subsection in enumerate(subsections):
                        chunk_metadata = doc.metadata.copy()
                        chunk_metadata.update({
                            "chunk_id": f"{i}.{j}",
                            "total_chunks": len(sections),
                            "chunk_type": "subsection"
                        })
                        
                        chunked_docs.append(Document(
                            page_content=subsection,
                            metadata=chunk_metadata
                        ))
                else:
                    chunk_metadata = doc.metadata.copy()
                    chunk_metadata.update({
                        "chunk_id": i,
                        "total_chunks": len(sections),
                        "chunk_type": "section"
                    })
                    
                    chunked_docs.append(Document(
                        page_content=section,
                        metadata=chunk_metadata
                    ))
        
        return chunked_docs
    
    def _standard_chunk(self, text: str) -> List[str]:
        """
        Standardowe chunkowanie z separatorami dostosowanymi do treści PFRON.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[
                "\n\nKrok ",      # Kroki procedur
                "\n\nPunkt ",     # Punkty
                "\n\nUwaga:",     # Uwagi
                "\n\nWażne:",     # Ważne informacje
                "\n\n",           # Podwójny enter
                "\n",             # Pojedynczy enter
                ". ",             # Koniec zdania
                ", ",             # Przecinek
                " ",              # Spacja
                ""
            ]
        )
        
        return text_splitter.split_text(text)


def upgrade_web_chunking():
    """
    Funkcja pomocnicza do testowania nowego chunkera.
    """
    from web_loader import load_url_documents
    
    # Załaduj dokumenty URL
    url_docs = load_url_documents("urls.txt")
    
    # Przetestuj nowy chunker
    web_chunker = WebContentChunker(chunk_size=1200, chunk_overlap=200)
    chunked_docs = web_chunker.chunk_web_documents(url_docs)
    
    print(f"Oryginalnych dokumentów URL: {len(url_docs)}")
    print(f"Chunków po podziale: {len(chunked_docs)}")
    
    # Pokaż statystyki
    chunk_sizes = [len(doc.page_content) for doc in chunked_docs]
    if chunk_sizes:
        print(f"Średni rozmiar chunka: {sum(chunk_sizes) // len(chunk_sizes)} znaków")
        print(f"Min: {min(chunk_sizes)}, Max: {max(chunk_sizes)} znaków")
        print(f"Chunki > 1500 znaków: {len([x for x in chunk_sizes if x > 1500])}")
    
    return chunked_docs


if __name__ == "__main__":
    upgrade_web_chunking()
