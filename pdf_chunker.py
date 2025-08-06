import re
from typing import List, Tuple
import fitz  # PyMuPDF
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

class IntelligentPDFChunker:
    """
    Inteligentny chunker dla dokumentów PDF, który respektuje strukturę dokumentu.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def _detect_structure_markers(self, text: str) -> List[Tuple[int, str, int]]:
        """
        Wykrywa markery struktury w tekście (nagłówki, punkty, etc.)
        Zwraca listę tupli (pozycja, typ, poziom)
        """
        markers = []
        
        # Wzorce dla różnych typów struktury
        patterns = [
            (r'^#{1,6}\s+(.+)', 'header', lambda m: len(m.group(0).split()[0])),
            (r'^##\s+(.+)', 'header', 2),
            (r'^###\s+(.+)', 'header', 3),
            (r'^####\s+(.+)', 'header', 4),
            (r'^#####\s+(.+)', 'header', 5),
            (r'^######\s+(.+)', 'header', 6),
            (r'^\d+\.\s+(.+)', 'numbered_list', 1),
            (r'^•\s+(.+)', 'bullet_list', 1),
            (r'^-\s+(.+)', 'bullet_list', 1),
            (r'^\*\s+(.+)', 'bullet_list', 1),
            (r'^[A-ZĄĆĘŁŃÓŚŹŻ][A-ZĄĆĘŁŃÓŚŹŻ\s]+:$', 'section_title', 1),
            (r'^Krok\s+\d+', 'step', 1),
            (r'^Rozdział\s+\d+', 'chapter', 1),
            (r'^Część\s+\d+', 'part', 1),
        ]
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            for pattern, marker_type, level_func in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    level = level_func(match) if callable(level_func) else level_func
                    markers.append((i, marker_type, level))
                    break
        
        return markers
    
    def _extract_pdf_structure(self, pdf_path: str) -> List[Document]:
        """
        Ekstraktuje tekst z PDF z zachowaniem struktury dokumentu.
        """
        doc = fitz.open(pdf_path)
        documents = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Pobierz tekst z metadanymi o czcionce
            blocks = page.get_text("dict")["blocks"]
            
            page_text = ""
            current_section = ""
            
            for block in blocks:
                if block.get("type") == 0:  # text block
                    for line in block["lines"]:
                        line_text = ""
                        max_size = 0
                        
                        for span in line["spans"]:
                            text = span.get("text", "").strip()
                            if text:
                                line_text += text + " "
                                max_size = max(max_size, span.get("size", 0))
                        
                        if line_text.strip():
                            # Wykryj nagłówki na podstawie rozmiaru czcionki
                            if max_size > 12:  # Większa czcionka = prawdopodobnie nagłówek
                                if current_section:
                                    # Zapisz poprzednią sekcję
                                    documents.append(Document(
                                        page_content=page_text.strip(),
                                        metadata={
                                            "source": pdf_path,
                                            "page": page_num + 1,
                                            "section": current_section,
                                            "type": "section"
                                        }
                                    ))
                                    page_text = ""
                                
                                current_section = line_text.strip()
                                page_text += f"\n## {line_text.strip()}\n"
                            else:
                                page_text += line_text.strip() + " "
            
            # Dodaj ostatnią sekcję ze strony
            if page_text.strip():
                documents.append(Document(
                    page_content=page_text.strip(),
                    metadata={
                        "source": pdf_path,
                        "page": page_num + 1,
                        "section": current_section or f"Strona {page_num + 1}",
                        "type": "section"
                    }
                ))
        
        doc.close()
        return documents
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Dzieli dokumenty na chunki z zachowaniem struktury.
        """
        chunked_docs = []
        
        for doc in documents:
            # Jeśli dokument jest mały, zostaw go bez dzielenia
            if len(doc.page_content) <= self.chunk_size:
                chunked_docs.append(doc)
                continue
            
            # Użyj RecursiveCharacterTextSplitter z separatorami strukturalnymi
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=[
                    "\n## ",      # Nagłówki H2
                    "\n### ",     # Nagłówki H3
                    "\n#### ",    # Nagłówki H4
                    "\n\n",       # Podwójny enter
                    "\n",         # Pojedynczy enter
                    ". ",         # Koniec zdania
                    ", ",         # Przecinek
                    " ",          # Spacja
                    ""
                ]
            )
            
            texts = text_splitter.split_text(doc.page_content)
            
            for i, text in enumerate(texts):
                chunk_metadata = doc.metadata.copy()
                chunk_metadata["chunk_id"] = i
                chunk_metadata["total_chunks"] = len(texts)
                
                chunked_docs.append(Document(
                    page_content=text,
                    metadata=chunk_metadata
                ))
        
        return chunked_docs