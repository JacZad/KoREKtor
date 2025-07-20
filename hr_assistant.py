"""
Asystent HR dla pracodawców zatrudniających osoby z niepełnosprawnościami.
Wykorzystuje dokumenty PDF jako bazę wiedzy z wektorową bazą danych w pamięci.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re

# LangChain imports (aktualne na 2024-06)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate

# PDF processing
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


class HRAssistant:
    """
    Asystent HR dla pracodawców zatrudniających osoby z niepełnosprawnościami.

    Wykorzystuje dokumenty PDF jako bazę wiedzy, przetwarza je na wektorową bazę danych (FAISS),
    a następnie umożliwia zadawanie pytań w języku polskim z konwersacyjną pamięcią kontekstu.
    Odpowiedzi generowane są przez model OpenAI GPT na podstawie treści dokumentów.

    Parametry:
        openai_api_key (str): Klucz API do OpenAI.
        pdf_directory (str): Ścieżka do katalogu z plikami PDF.
    """

    def _setup_qa_chain(self):
        """
        Tworzy i konfiguruje łańcuch pytań i odpowiedzi (ConversationalRetrievalChain) dla asystenta HR.
        Łańcuch ten korzysta z modelu LLM, bazy wektorowej oraz pamięci konwersacyjnej.
        Prompt jest zoptymalizowany pod polskie realia HR i bazuje wyłącznie na wiedzy z dokumentów PDF.

        Raises:
            ValueError: Jeśli baza wektorowa nie została zainicjalizowana.
        """
        if not self.vectorstore:
            raise ValueError("Baza wektorowa nie została zainicjalizowana.")

        prompt_template = (
            "Jesteś ekspertem HR specjalizującym się w zatrudnianiu osób z niepełnosprawnościami w Polsce.\n"
            "Twoja wiedza opiera się na oficjalnych dokumentach i poradnikach dla pracodawców.\n\n"
            "Kontekst z dokumentów:\n{context}\n\n"
            "Historia rozmowy:\n{chat_history}\n\n"
            "Pytanie: {question}\n\n"
            "Instrukcje:\n"
            "1. Odpowiadaj w języku polskim\n"
            "2. Bazuj wyłącznie na informacjach z dostarczonych dokumentów\n"
            "3. Jeśli nie masz informacji w dokumentach, powiedz to wprost\n"
            "4. Podawaj konkretne, praktyczne porady\n"
            "5. Odwołuj się do konkretnych przepisów prawnych gdy to możliwe\n"
            "6. Bądź pomocny i profesjonalny\n"
            "7. Gdy to możliwe, podaj źródło informacji (nazwę dokumentu)\n\n"
            "Odpowiedź:"
        )
        custom_prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "chat_history", "question"]
        )
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            ),
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": custom_prompt},
            return_source_documents=True,
            output_key="answer"
        )
    """
    Asystent HR dla pracodawców zatrudniających osoby z niepełnosprawnościami.
    """
    
    def __init__(self, openai_api_key: str, pdf_directory: str = "pdfs"):
        self.openai_api_key = openai_api_key
        self.pdf_directory = Path(pdf_directory)
        self._known_pdfs = set()
        self._pdf_mtimes = {}

        # Inicjalizuj komponenty
        self.embeddings = OpenAIEmbeddings(
            api_key=openai_api_key,
            model="text-embedding-3-small"
        )
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4o-mini",
            temperature=0.3
        )
        self.chunker = IntelligentPDFChunker(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.vectorstore = None
        self.qa_chain = None
        self.memory = ConversationBufferWindowMemory(
            k=5,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer",
            input_key="question"
        )
        self._load_and_process_documents()
        self._setup_qa_chain()

    def _list_pdf_files(self):
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

    def _load_and_process_documents(self):
        """
        Ładuje i przetwarza dokumenty PDF.
        """
        logger.info("Ładowanie dokumentów PDF...")

        pdf_files = self._list_pdf_files()
        if not pdf_files:
            raise ValueError(f"Nie znaleziono plików PDF w katalogu: {self.pdf_directory}")

        logger.info(f"Znaleziono {len(pdf_files)} plików PDF")
        all_documents = []
        for pdf_file in pdf_files:
            logger.info(f"Przetwarzanie: {pdf_file.name}")
            documents = self.chunker._extract_pdf_structure(str(pdf_file))
            for doc in documents:
                doc.metadata["filename"] = pdf_file.name
                doc.metadata["file_stem"] = pdf_file.stem
            all_documents.extend(documents)
        logger.info(f"Wyekstraktowano {len(all_documents)} sekcji")
        chunked_documents = self.chunker.chunk_documents(all_documents)
        logger.info(f"Utworzono {len(chunked_documents)} chunków")
        self.vectorstore = FAISS.from_documents(
            chunked_documents,
            self.embeddings
        )
        logger.info("Baza wektorowa została utworzona")

    def _reload_if_pdfs_changed(self):
        """
        Przeładowuje embeddingi jeśli pojawiły się nowe/zmienione PDF-y.
        """
        if self._pdfs_changed():
            logger.info("Wykryto nowe lub zmienione pliki PDF. Przeładowuję bazę wiedzy...")
            self._load_and_process_documents()
            self._setup_qa_chain()

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Zadaje pytanie asystentowi.
        """
        logger.info(f"Otrzymano pytanie: {question}")
        self._reload_if_pdfs_changed()
        try:
            result = self.qa_chain.invoke({
                "question": question,
                "chat_history": self.memory.chat_memory.messages
            })
            response = {
                "answer": result["answer"],
                "sources": [],
                "confidence": "medium"
            }
            for doc in result.get("source_documents", []):
                source_info = {
                    "filename": doc.metadata.get("filename", ""),
                    "page": doc.metadata.get("page", ""),
                    "section": doc.metadata.get("section", ""),
                    "snippet": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                }
                response["sources"].append(source_info)
            return response
        except Exception as e:
            logger.error(f"Błąd podczas przetwarzania pytania: {e}")
            return {
                "answer": "Przepraszam, wystąpił błąd podczas przetwarzania Twojego pytania.",
                "sources": [],
                "confidence": "low",
                "error": str(e)
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Zwraca statystyki asystenta.
        """
        return {
            "total_documents": self.vectorstore.index.ntotal if self.vectorstore else 0,
            "pdf_files": len(self._list_pdf_files()),
            "memory_messages": len(self.memory.chat_memory.messages),
            "model": "gpt-4o-mini",
            "embedding_model": "text-embedding-3-small"
        }
    
    def clear_memory(self):
        """
        Czyści pamięć konwersacji.
        """
        self.memory.clear()
        logger.info("Pamięć konwersacji została wyczyszczona")


def print_unique_sources(sources: list):
    """
    Wypisuje unikalne źródła na podstawie filename, page, section.
    """
    unique_sources = []
    seen = set()
    for source in sources:
        key = (source['filename'], source['page'], source['section'])
        if key not in seen:
            seen.add(key)
            unique_sources.append(source)
    for i, source in enumerate(unique_sources, 1):
        print(f"{i}. {source['filename']} (str. {source['page']}) - {source['section']}")

def handle_command(command: str, assistant: HRAssistant) -> bool:
    """
    Obsługuje polecenia specjalne. Zwraca True jeśli należy kontynuować pętlę.
    """
    cmd = command.lower()
    if cmd in ['quit', 'exit', 'q']:
        return False
    if cmd == 'stats':
        print(f"Statystyki: {assistant.get_stats()}")
        return True
    if cmd == 'clear':
        assistant.clear_memory()
        print("Pamięć konwersacji została wyczyszczona")
        return True
    return None

def main():
    """
    Przykład użycia asystenta HR.
    """
    # Sprawdź czy ustawiono klucz API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Ustaw zmienną środowiskową OPENAI_API_KEY")
    
    # Utwórz asystenta
    assistant = HRAssistant(
        openai_api_key=api_key,
        pdf_directory="pdfs"
    )
    
    # Przykładowe pytania
    test_questions = [
        "Jakie są uprawnienia pracownika z niepełnosprawnością?",
        "Jak przeprowadzić rekrutację osoby z niepełnosprawnością?",
        "Jakie wsparcie może otrzymać pracodawca zatrudniający osoby z niepełnosprawnościami?",
        "Czy osoba z orzeczeniem o całkowitej niezdolności do pracy może być zatrudniona?"
    ]
    
    print("=== Asystent HR - Zatrudnianie osób z niepełnosprawnościami ===\n")
    print(f"Statystyki: {assistant.get_stats()}\n")
    
    # Interaktywny tryb
    while True:
        try:
            question = input("\nTwoje pytanie (lub 'quit' aby zakończyć): ")
            if not question.strip():
                continue

            cmd_result = handle_command(question, assistant)
            if cmd_result is False:
                break
            if cmd_result is True:
                continue

            # Uzyskaj odpowiedź
            response = assistant.ask(question)
            print(f"\n📝 Odpowiedź:")
            print(response["answer"])

            if "error" in response:
                print(f"\n⚠️  Błąd: {response['error']}")

        except KeyboardInterrupt:
            print("\n\nDo widzenia!")
            break
        except Exception as e:
            print(f"\n❌ Błąd: {e}")


if __name__ == "__main__":
    main()


# ===============================
# Instrukcja wdrożenia modułu HRAssistant
# ===============================
#
# 1. Ustaw zmienną środowiskową z kluczem OpenAI:
#    export OPENAI_API_KEY="twoj_klucz_openai"
#
# 2. Umieść pliki PDF w katalogu "pdfs" (lub wskaż inny katalog w parametrze pdf_directory).
#
# 3. Zainstaluj wymagane biblioteki:
#    pip install -r requirements.txt
#
# 4. Uruchom moduł:
#    python hr_assistant.py
#
# 5. Możesz zintegrować klasę HRAssistant w swoim projekcie:
#    from hr_assistant import HRAssistant
#    assistant = HRAssistant(openai_api_key="...", pdf_directory="pdfs")
#    odpowiedz = assistant.ask("Twoje pytanie")
#
# 6. Szczegóły i przykłady znajdziesz w README.md oraz EXAMPLES.md.
