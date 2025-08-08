"""
Zrefaktoryzowany HRAssistant wykorzystujący DocumentManager i Config.

Główne zmiany:
- Wydzielono zarządzanie dokumentami do DocumentManager
- Centralna konfiguracja w Config
- Czytelniejsza struktura kodu
- Lepsze separation of concerns
"""

import logging
from typing import Dict, Any

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores.faiss import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate

from config import KorektorConfig
from document_manager import DocumentManager
from vector_stats import analyze_vector_store

logger = logging.getLogger(__name__)


class HRAssistantV2:
    """
    Zrefaktoryzowany Asystent HR z lepszą separacją odpowiedzialności.
    
    Wykorzystuje:
    - DocumentManager do zarządzania dokumentami
    - KorektorConfig do konfiguracji
    - Czytelniejszą strukturę z mniejszymi metodami
    """
    
    def __init__(self, config: KorektorConfig = None):
        """
        Inicjalizuje asystenta HR z podaną konfiguracją.
        
        Args:
            config: Konfiguracja aplikacji. Jeśli None, użyje domyślnej.
        """
        self.config = config or KorektorConfig.from_env()
        self.config.validate()
        
        # Inicjalizuj komponenty
        self.document_manager = DocumentManager(
            pdf_directory=self.config.pdf_directory,
            urls_file=self.config.urls_file,
            bibliography_file=self.config.bibliography_file,
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
        
        self.embeddings = OpenAIEmbeddings(
            api_key=self.config.openai_api_key,
            model=self.config.embedding_model
        )
        
        self.llm = ChatOpenAI(
            api_key=self.config.openai_api_key,
            model=self.config.llm_model,
            temperature=self.config.llm_temperature
        )
        
        self.memory = ConversationBufferWindowMemory(
            k=self.config.memory_k,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer",
            input_key="question"
        )
        
        # Załaduj dokumenty i utworz bazę wektorową
        self.vectorstore = None
        self.qa_chain = None
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Inicjalizuje bazę wiedzy (ładuje dokumenty i tworzy vectorstore)."""
        logger.info("Inicjalizowanie bazy wiedzy...")
        
        # Załaduj wszystkie dokumenty
        documents = self.document_manager.load_all_documents()
        
        # Utwórz bazę wektorową
        self.vectorstore = FAISS.from_documents(documents, self.embeddings)
        logger.info("Baza wektorowa została utworzona")
        
        # Wyświetl statystyki
        stats = analyze_vector_store(self.vectorstore)
        logger.info(f"Statystyki bazy: {stats['vectors_count']:,} wektorów, "
                   f"{stats['memory_size_mb']} MB, kategoria: {stats['size_category']}")
        
        # Wyświetl ostrzeżenia dla dużych baz
        if stats.get('memory_size_mb', 0) > 500:
            logger.warning("Duża baza wektorowa - rozważ optymalizację!")
            for rec in stats.get('recommendations', []):
                logger.info(f"Rekomendacja: {rec}")
        
        # Utwórz chain QA
        self._setup_qa_chain()
    
    def _setup_qa_chain(self):
        """Tworzy i konfiguruje łańcuch pytań i odpowiedzi."""
        if not self.vectorstore:
            raise ValueError("Baza wektorowa nie została zainicjalizowana.")
        
        prompt_template = self._get_prompt_template()
        
        custom_prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "chat_history", "question"]
        )
        
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(
                search_type=self.config.search_type,
                search_kwargs={"k": self.config.search_k}
            ),
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": custom_prompt},
            return_source_documents=True,
            output_key="answer"
        )
    
    def _get_prompt_template(self) -> str:
        """Zwraca szablon promptu dla asystenta HR."""
        return (
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
    
    def ask(self, question: str) -> Dict[str, Any]:
        """
        Zadaje pytanie asystentowi.
        
        Args:
            question: Pytanie do asystenta
            
        Returns:
            Dict zawierający odpowiedź, źródła i metadane
        """
        logger.info(f"Otrzymano pytanie: {question}")
        
        try:
            result = self.qa_chain.invoke({
                "question": question,
                "chat_history": self.memory.chat_memory.messages
            })
            
            response = {
                "answer": result["answer"],
                "sources": self._format_sources(result.get("source_documents", [])),
                "confidence": "medium"
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Błąd podczas przetwarzania pytania: {e}")
            return {
                "answer": "Przepraszam, wystąpił błąd podczas przetwarzania Twojego pytania.",
                "sources": [],
                "confidence": "low",
                "error": str(e)
            }
    
    def _format_sources(self, source_documents) -> list:
        """
        Formatuje źródła dokumentów do struktury odpowiedzi.
        
        Args:
            source_documents: Lista dokumentów źródłowych
            
        Returns:
            Lista sformatowanych źródeł
        """
        sources = []
        
        for doc in source_documents:
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
                
                source_info = {
                    "type": "url",
                    "url": source_url,
                    "title": clean_title,
                    "display_name": clean_title,
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
            
            sources.append(source_info)
        
        return sources
    
    def reload_knowledge_base(self) -> bool:
        """
        Ręcznie przeładowuje bazę wiedzy jeśli wykryto zmiany w dokumentach.
        
        Returns:
            bool: True jeśli przeładowano, False jeśli nie było zmian
        """
        logger.info("Ręczne przeładowanie bazy wiedzy...")
        
        if self.document_manager.has_changes():
            logger.info("Wykryto zmiany w dokumentach. Przeładowuję bazę wiedzy...")
            self._initialize_knowledge_base()
            return True
        else:
            logger.info("Brak zmian w dokumentach.")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Zwraca statystyki asystenta."""
        doc_stats = self.document_manager.get_stats()
        
        base_stats = {
            "total_documents": self.vectorstore.index.ntotal if self.vectorstore else 0,
            "memory_messages": len(self.memory.chat_memory.messages),
            "model": self.config.llm_model,
            "embedding_model": self.config.embedding_model
        }
        
        return {**base_stats, **doc_stats}
    
    def clear_memory(self):
        """Czyści pamięć konwersacji."""
        self.memory.clear()
        logger.info("Pamięć konwersacji została wyczyszczona")
    
    def get_vector_stats(self):
        """Zwraca statystyki bazy wektorowej."""
        if not self.vectorstore:
            return {"error": "Baza wektorowa nie została zainicjalizowana"}
        return analyze_vector_store(self.vectorstore)


# Alias dla zachowania kompatybilności
HRAssistant = HRAssistantV2
