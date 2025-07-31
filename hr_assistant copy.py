Główny moduł Asystenta HR - KorChat.

Ten plik zawiera logikę biznesową aplikacji, w tym:
- Klasę `HRAssistant`, która zarządza całym procesem Q&A.
- Klasy pomocnicze do ładowania i przetwarzania danych (`DataLoader`, `IntelligentPDFChunker`).
- Funkcje do formatowania odpowiedzi i obsługi interfejsu konsolowego.

Autor: Jacek (2024-2025)


import os
import logging
import csv
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# LangChain imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.documents import Document
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate

# Web scraping and PDF processing
import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF

# --- Konfiguracja logowania ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Funkcje pomocnicze do obsługi źródeł ---

def load_bibliography(file_path: str = "bibliografia.csv") -> Dict[str, str]:
    """
    Wczytuje dane bibliograficzne z pliku CSV i zwraca słownik mapujący
    nazwę pliku (bez rozszerzenia) na jego opis.
    """
    bibliography = {}
    if not os.path.exists(file_path):
        logger.warning(f"Plik bibliografii '{file_path}' nie został znaleziony.")
        return bibliography
        
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            next(reader, None)  # Pomiń nagłówek
            for row in reader:
                if len(row) >= 2:
                    description, filename = row[0].strip('"'), row[1].strip()
                    file_stem = Path(filename).stem
                    bibliography[file_stem] = description
    except Exception as e:
        logger.error(f"Błąd podczas wczytywania pliku bibliografii '{file_path}': {e}")
        
    return bibliography

bibliography_data = load_bibliography()

def format_unique_sources(sources: list, print_mode: bool = True) -> str:
    """
    Formatuje unikalne źródła jako string w formacie Markdown.
    Obsługuje zarówno obiekty Document, jak i słowniki.
    """
    unique_sources_meta = []
    seen = set()
    
    for source in sources:
        metadata = source.metadata if hasattr(source, 'metadata') else source
        
        filename = metadata.get('source') or metadata.get('filename', '')
        page = metadata.get('page', '')
        section = metadata.get('section', '')
        title = metadata.get('title', '')
        
        # Poprawiony klucz do sprawdzania unikalności
        key = (filename, page, section, title)
        if key not in seen:
            seen.add(key)
            unique_sources_meta.append(metadata)

    if not unique_sources_meta:
        return ""

    output_lines = ["\n\n---", "**Źródła:**"]
    for i, meta in enumerate(unique_sources_meta, 1):
        filename = meta.get('source') or meta.get('filename', '')
        page = meta.get('page', '')
        section = meta.get('section', '')
        title = meta.get('title', '')
        
        is_url = filename.startswith('http')

        if is_url:
            display_title = title or filename
            output_lines.append(f"{i}. [{display_title}]({filename})")
        else:
            file_stem = Path(filename).stem if filename else ''
            opis = bibliography_data.get(Path(filename).name) or bibliography_data.get(file_stem) or Path(filename).name
            
            source_str = f"{i}. **{opis}**"
            if page:
                source_str += f" (str. {page})"
            if section:
                source_str += f" - *{section}*"
            output_lines.append(source_str)

    formatted_string = "\n".join(output_lines)
    if print_mode:
        print(formatted_string)
        
    return formatted_string

# --- Klasy przetwarzające dane ---

class IntelligentPDFChunker:
    """
    Inteligentny chunker dla dokumentów PDF, który respektuje strukturę dokumentu,
    taką jak nagłówki, sekcje i strony.
    """
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", ". ", ", ", " "]
        )

    def extract_pdf_structure(self, pdf_path: str) -> List[Document]:
        """Ekstraktuje tekst z PDF, zachowując strukturę opartą na stronach i nagłówkach."""
        documents = []
        try:
            doc = fitz.open(pdf_path)
            for page_num, page in enumerate(doc):
                blocks = page.get_text("dict")["blocks"]
                page_text = ""
                current_section = ""
                for block in filter(lambda b: b.get("type") == 0, blocks):
                    for line in block["lines"]:
                        line_text = "".join(span.get("text", "").strip() + " " for span in line["spans"] if span.get("text", "").strip())
                        max_size = max((span.get("size", 0) for span in line["spans"]), default=0)
                        
                        if line_text:
                            if max_size > 12:  # Większa czcionka = nagłówek
                                if page_text: # Zapisz poprzednią sekcję
                                    documents.append(Document(page_content=page_text.strip(), metadata={"source": pdf_path, "page": page_num + 1, "section": current_section}))
                                    page_text = ""
                                current_section = line_text.strip()
                                page_text += f"\n## {current_section}\n"
                            else:
                                page_text += line_text
                
                if page_text: # Dodaj ostatnią sekcję ze strony
                    documents.append(Document(page_content=page_text.strip(), metadata={"source": pdf_path, "page": page_num + 1, "section": current_section or f"Strona {page_num + 1}"}))
            doc.close()
        except Exception as e:
            logger.error(f"Błąd podczas ekstrakcji struktury z pliku PDF {pdf_path}: {e}")
        return documents

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Dzieli dokumenty na mniejsze fragmenty (chunki)."""
        chunked_docs = []
        for doc in documents:
            if len(doc.page_content) <= self.chunk_size:
                chunked_docs.append(doc)
                continue
            
            texts = self.text_splitter.split_text(doc.page_content)
            for i, text in enumerate(texts):
                chunk_metadata = doc.metadata.copy()
                chunk_metadata.update({"chunk_id": i, "total_chunks": len(texts)})
                chunked_docs.append(Document(page_content=text, metadata=chunk_metadata))
        return chunked_docs

class DataLoader:
    """
    Klasa odpowiedzialna za ładowanie i przygotowywanie dokumentów
    z różnych źródeł (PDF, URL, hardcoded).
    """
    def __init__(self, pdf_directory: str = "pdfs", urls_file: str = 'urls.txt'):
        self.pdf_directory = Path(pdf_directory)
        self.urls_file = urls_file
        self.chunker = IntelligentPDFChunker()

    def load_all_documents(self) -> List[Document]:
        """Ładuje, przetwarza i chunk'uje dokumenty ze wszystkich źródeł."""
        logger.info("Rozpoczynam ładowanie dokumentów ze wszystkich źródeł...")
        all_docs = self._load_pdf_documents()
        all_docs.extend(self._load_url_documents())
        
        
        if not all_docs:
            logger.error("Nie załadowano żadnych dokumentów. Baza wiedzy będzie pusta.")
            return []
            
        logger.info(f"Łącznie załadowano {len(all_docs)} dokumentów/sekcji przed chunkowaniem.")
        chunked_documents = self.chunker.chunk_documents(all_docs)
        logger.info(f"Utworzono {len(chunked_documents)} chunków po przetworzeniu.")
        return chunked_documents

    def _load_pdf_documents(self) -> List[Document]:
        """Ładuje i przetwarza pliki PDF."""
        pdf_files = list(self.pdf_directory.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"Nie znaleziono plików PDF w katalogu: {self.pdf_directory}.")
            return []
        
        logger.info(f"Znaleziono {len(pdf_files)} plików PDF. Rozpoczynam przetwarzanie...")
        all_pdf_docs = []
        for pdf_file in pdf_files:
            try:
                docs = self.chunker.extract_pdf_structure(str(pdf_file))
                for doc in docs:
                    doc.metadata["filename"] = pdf_file.name
                    doc.metadata["file_stem"] = pdf_file.stem
                all_pdf_docs.extend(docs)
            except Exception as e:
                logger.error(f"Nie udało się przetworzyć pliku PDF {pdf_file.name}: {e}")
        return all_pdf_docs

    def _load_url_documents(self) -> List[Document]:
        """Pobiera i przetwarzać treści z plików URL."""
        if not os.path.exists(self.urls_file):
            logger.warning(f"Plik '{self.urls_file}' nie został znaleziony.")
            return []
        
        with open(self.urls_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        if not urls:
            return []

        logger.info(f"Znaleziono {len(urls)} adresów URL do przetworzenia.")
        url_documents = []
        for url in urls:
            try:
                response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find('title').get_text().strip() if soup.find('title') else 'Brak tytułu'
                content = self._extract_url_content(soup)
                
                if content:
                    metadata = {'source': url, 'title': title, 'added_date': datetime.now().strftime("%Y-%m-%d")}
                    if re.search(r'\d+(?:[.,]\d+)?\s*(?:zł|PLN|złot)', content, re.IGNORECASE):
                        metadata["contains_financial_data"] = True
                    url_documents.append(Document(page_content=content, metadata=metadata))
            except requests.RequestException as e:
                logger.error(f"Błąd podczas pobierania {url}: {e}")
        return url_documents

    def _extract_url_content(self, soup: BeautifulSoup) -> str:
        """Wyodrębnia główną treść ze strony internetowej."""
        selectors = ['.frame.default', '.csc-default', 'article', 'main', '.content', '#content']
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(separator='\n', strip=True)
        return soup.body.get_text(separator='\n', strip=True) if soup.body else ""

    

# --- Główna klasa Asystenta HR ---

class HRAssistant:
    """
    Główna klasa Asystenta HR. Zarządza bazą wiedzy, łańcuchem Q&A i pamięcią konwersacji.
    """
    def __init__(self, openai_api_key: str, pdf_directory: str = "pdfs"):
        self.api_key = openai_api_key
        self.pdf_dir = pdf_directory
        self.vectorstore = None
        self.qa_chain = None
        
        self.embeddings = OpenAIEmbeddings(api_key=self.api_key, model="text-embedding-3-small")
        self.llm = ChatOpenAI(api_key=self.api_key, model="gpt-4o-mini", temperature=0.3)
        self.memory = ConversationBufferWindowMemory(
            k=5, memory_key="chat_history", return_messages=True, output_key="answer"
        )
        
        self._initialize_vectorstore()
        self._setup_qa_chain()

    def _initialize_vectorstore(self):
        """Inicjalizuje bazę wektorową na podstawie załadowanych dokumentów."""
        data_loader = DataLoader(pdf_directory=self.pdf_dir)
        documents = data_loader.load_all_documents()
        if documents:
            logger.info("Tworzenie bazy wektorowej FAISS...")
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
            logger.info("Baza wektorowa została pomyślnie utworzona.")
        else:
            logger.error("Nie udało się utworzyć bazy wektorowej - brak dokumentów.")
            raise ValueError("Brak dokumentów do utworzenia bazy wiedzy.")

    def _setup_qa_chain(self):
        """Konfiguruje łańcuch konwersacyjny."""
        if not self.vectorstore:
            raise ValueError("Baza wektorowa nie jest zainicjalizowana.")

        prompt_template = (
            "Jesteś ekspertem HR w Polsce. Twoja wiedza opiera się wyłącznie na dostarczonym kontekście.\n"
            "Kontekst:\n{context}\n\n"
            "Historia rozmowy:\n{chat_history}\n\n"
            "Pytanie: {question}\n\n"
            "Instrukcje:\n"
            "1. Odpowiadaj po polsku, bazując tylko na kontekście.\n"
            "2. Jeśli odpowiedź nie znajduje się w kontekście, napisz: 'Niestety, nie posiadam informacji na ten temat w mojej bazie wiedzy.'.\n"
            "3. Bądź precyzyjny i profesjonalny.\n\n"
            "Odpowiedź:"
        )
        custom_prompt = PromptTemplate.from_template(prompt_template)
        
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": 8, "score_threshold": 0.5}
            ),
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": custom_prompt},
            return_source_documents=True,
            output_key="answer"
        )

    def ask(self, question: str) -> Dict[str, Any]:
        """Zadaje pytanie asystentowi i zwraca odpowiedź oraz źródła."""
        logger.info(f"Otrzymano pytanie: {question}")
        try:
            response = self.qa_chain.invoke({"question": question})
            return {
                "answer": response.get("answer", "Wystąpił błąd."),
                "sources": response.get("source_documents", [])
            }
        except Exception as e:
            logger.error(f"Błąd podczas przetwarzania pytania: {e}", exc_info=True)
            return {"answer": "Przepraszam, wystąpił błąd techniczny.", "sources": []}

    def get_formatted_response(self, question: str) -> str:
        """Zwraca pełną, sformatowaną odpowiedź tekstową ze źródłami."""
        response = self.ask(question)
        answer = response.get("answer")
        sources = response.get("sources")
        if sources:
            return f"{answer}{format_unique_sources(sources, print_mode=False)}"
        return answer

    def get_stats(self) -> Dict[str, Any]:
        """Zwraca statystyki asystenta."""
        return {
            "total_chunks": self.vectorstore.index.ntotal if self.vectorstore else 0,
            "pdf_files_in_dir": len(list(Path(self.pdf_dir).glob("*.pdf"))),
            "memory_size": len(self.memory.chat_memory.messages),
            "llm_model": "gpt-4o-mini",
            "embedding_model": "text-embedding-3-small"
        }

    def clear_memory(self):
        """Czyści pamięć konwersacji."""
        self.memory.clear()
        logger.info("Pamięć konwersacji została wyczyszczona.")

# --- Funkcje obsługi trybu konsolowego ---

def handle_command(command: str, assistant: HRAssistant) -> Optional[bool]:
    """Obsługuje komendy specjalne. Zwraca False, aby zakończyć pętlę."""
    cmd = command.lower().strip()
    if cmd in ['quit', 'exit', 'q']:
        return False
    if cmd == 'stats':
        print(f"Statystyki: {assistant.get_stats()}")
        return True
    if cmd == 'clear':
        assistant.clear_memory()
        return True
    return None

def main():
    """Główna funkcja uruchamiająca tryb konsolowy asystenta."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.critical("Zmienna środowiskowa OPENAI_API_KEY nie jest ustawiona!")
        return

    try:
        assistant = HRAssistant(openai_api_key=api_key)
        print("\n=== Asystent HR - Witamy! ===")
        print("Zadaj pytanie lub wpisz komendę (stats, clear, quit).\n")
        
        while True:
            question = input("Twoje pytanie: ")
            if not question.strip():
                continue

            cmd_result = handle_command(question, assistant)
            if cmd_result is False:
                break
            if cmd_result is True:
                continue

            formatted_response = assistant.get_formatted_response(question)
            print(f"\n📝 Odpowiedź:{formatted_response}\n")

    except Exception as e:
        logger.critical(f"Wystąpił krytyczny błąd podczas inicjalizacji lub działania asystenta: {e}", exc_info=True)
    finally:
        print("\nDo widzenia!")

if __name__ == "__main__":
    main()