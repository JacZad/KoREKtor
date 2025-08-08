"""
Asystent HR dla pracodawców zatrudniających osoby z niepełnosprawnościami.
Wykorzystuje dokumenty PDF oraz treści ze stron internetowych jako bazę wiedzy 
z wektorową bazą danych w pamięci.
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
import pandas as pd

from web_loader import load_url_documents
from pdf_chunker import IntelligentPDFChunker
from vector_stats import VectorStoreAnalyzer, analyze_vector_store, print_vector_stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HRAssistant:
    """
    Asystent HR dla pracodawców zatrudniających osoby z niepełnosprawnościami.

    Wykorzystuje dokumenty PDF oraz treści ze stron internetowych jako bazę wiedzy, 
    przetwarza je na wektorową bazę danych (FAISS), a następnie umożliwia zadawanie 
    pytań w języku polskim z konwersacyjną pamięcią kontekstu.
    Odpowiedzi generowane są przez model OpenAI GPT na podstawie treści dokumentów.

    Parametry:
        openai_api_key (str): Klucz API do OpenAI.
        pdf_directory (str): Ścieżka do katalogu z plikami PDF.
        urls_file (str): Ścieżka do pliku z listą URLs do załadowania.
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
            "Twoja wiedza opiera się na oficjalnych dokumentach, poradnikach dla pracodawców oraz aktualnych informacjach ze stron PFRON.\n\n"
            "Kontekst z dokumentów:\n{context}\n\n"
            "Historia rozmowy:\n{chat_history}\n\n"
            "Pytanie: {question}\n\n"
            "Instrukcje:\n"
            "1. Odpowiadaj w języku polskim\n"
            "2. Bazuj wyłącznie na informacjach z dostarczonych dokumentów i stron internetowych\n"
            "3. Jeśli nie masz informacji w dokumentach, powiedz to wprost\n"
            "4. Podawaj konkretne, praktyczne porady\n"
            "5. Odwołuj się do konkretnych przepisów prawnych gdy to możliwe\n"
            "6. Bądź pomocny i profesjonalny\n"
            "7. Gdy to możliwe, podaj źródło informacji (nazwę dokumentu lub stronę internetową)\n"
            "8. Dla informacji ze stron internetowych podaj datę dostępu jeśli jest dostępna\n\n"
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
    
    def __init__(self, openai_api_key: str, pdf_directory: str = "pdfs", urls_file: str = "urls.txt"):
        self.openai_api_key = openai_api_key
        self.pdf_directory = Path(pdf_directory)
        self.urls_file = urls_file
        self._known_pdfs = set()
        self._pdf_mtimes = {}
        
        # Załaduj bibliografię z pliku CSV
        self.bibliography = self._load_bibliography()

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

    def _load_bibliography(self) -> Dict[str, str]:
        """
        Ładuje bibliografię z pliku bibliografia.csv.
        Zwraca słownik mapujący nazwę pliku na pełny opis bibliograficzny.
        """
        bibliography_path = Path("bibliografia.csv")
        if not bibliography_path.exists():
            logger.warning("Plik bibliografia.csv nie istnieje. Będą używane nazwy plików.")
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
        Ładuje i przetwarza dokumenty PDF oraz treści z URLs.
        """
        logger.info("Ładowanie dokumentów PDF i treści z URLs...")

        # Ładowanie PDF
        pdf_files = self._list_pdf_files()
        if not pdf_files:
            logger.warning(f"Nie znaleziono plików PDF w katalogu: {self.pdf_directory}")
        
        all_documents = []
        
        # Przetwarzanie plików PDF
        if pdf_files:
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
        
        # Ładowanie treści z URLs
        url_documents = load_url_documents(self.urls_file)
        all_documents.extend(url_documents)
        
        if not all_documents:
            raise ValueError("Nie znaleziono żadnych dokumentów do przetworzenia (ani PDF ani URLs)")
        
        logger.info(f"Łącznie dokumentów do przetworzenia: {len(all_documents)} (PDF: {len(all_documents) - len(url_documents)}, URLs: {len(url_documents)})")
        
        chunked_documents = self.chunker.chunk_documents(all_documents)
        logger.info(f"Utworzono {len(chunked_documents)} chunków")
        
        self.vectorstore = FAISS.from_documents(
            chunked_documents,
            self.embeddings
        )
        logger.info("Baza wektorowa została utworzona")
        
        # Wyświetl statystyki bazy wektorowej
        stats = analyze_vector_store(self.vectorstore)
        logger.info(f"Statystyki bazy: {stats['vectors_count']:,} wektorów, "
                   f"{stats['memory_size_mb']} MB, kategoria: {stats['size_category']}")
        
        # Wyświetl ostrzeżenia dla dużych baz
        if stats.get('memory_size_mb', 0) > 500:
            logger.warning("Duża baza wektorowa - rozważ optymalizację!")
            for rec in stats.get('recommendations', []):
                logger.info(f"Rekomendacja: {rec}")
        
        # Zaktualizuj zmienne śledzące pliki PDF po pomyślnym załadowaniu
        self._known_pdfs = set()
        self._pdf_mtimes = {}
        for pdf_file in pdf_files:
            self._known_pdfs.add(pdf_file.name)
            self._pdf_mtimes[pdf_file.name] = pdf_file.stat().st_mtime

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
        # Usunięte automatyczne sprawdzanie zmian - baza ładowana tylko przy starcie
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
                # Pobierz podstawowe metadane
                source_url = doc.metadata.get("source", "")
                title = doc.metadata.get("title", "")
                filename = doc.metadata.get("filename", "")
                
                # Formatowanie dla źródeł URL vs PDF
                if source_url.startswith("https://"):
                    # Dla URL - użyj tytułu jako nazwy wyświetlanej (skróć długie tytuły PFRON)
                    raw_title = title if title else source_url
                    # Usuń zbędną część tytułu PFRON
                    clean_title = raw_title.replace(" - Państwowy Fundusz Rehabilitacji Osób Niepełnosprawnych", "")
                    display_name = clean_title
                    
                    source_info = {
                        "type": "url",
                        "url": source_url,
                        "title": clean_title,
                        "display_name": display_name,
                        "filename": "",
                        "bibliography": doc.metadata.get("bibliography", f"{clean_title} - {source_url}"),
                        "page": "",
                        "section": doc.metadata.get("section", ""),
                        "snippet": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    }
                else:
                    # Dla PDF - standardowe formatowanie
                    source_info = {
                        "type": "pdf",
                        "url": "",
                        "title": title,
                        "display_name": filename,
                        "filename": filename,
                        "bibliography": doc.metadata.get("bibliography", filename),
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

    def reload_knowledge_base(self):
        """
        Ręcznie przeładowuje bazę wiedzy (sprawdza zmiany w plikach PDF).
        """
        logger.info("Ręczne przeładowanie bazy wiedzy...")
        if self._pdfs_changed():
            logger.info("Wykryto zmiany w plikach PDF. Przeładowuję bazę wiedzy...")
            self._load_and_process_documents()
            self._setup_qa_chain()
            return True
        else:
            logger.info("Brak zmian w plikach PDF.")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Zwraca statystyki asystenta.
        """
        # Policz URLs z pliku
        url_count = 0
        if os.path.exists(self.urls_file):
            try:
                with open(self.urls_file, 'r', encoding='utf-8') as f:
                    url_count = len([line.strip() for line in f if line.strip() and not line.startswith('#')])
            except:
                pass
        
        return {
            "total_documents": self.vectorstore.index.ntotal if self.vectorstore else 0,
            "pdf_files": len(self._list_pdf_files()),
            "url_sources": url_count,
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
    
    def get_vector_stats(self):
        """Zwraca statystyki bazy wektorowej."""
        if not self.vectorstore:
            return {"error": "Baza wektorowa nie została zainicjalizowana"}
        return analyze_vector_store(self.vectorstore)
    
    def print_vector_stats(self):
        """Wyświetla sformatowane statystyki bazy wektorowej."""
        if not self.vectorstore:
            print("❌ Baza wektorowa nie została zainicjalizowana")
            return
        print_vector_stats(self.vectorstore)
