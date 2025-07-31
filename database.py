import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

# Sprawdzenie, czy klucz API jest ustawiony
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("Klucz OPENAI_API_KEY nie jest ustawiony w zmiennych środowiskowych. Ustaw go, aby kontynuować.")

# Model do tworzenia wektorów (embeddings) - ten sam, co w hr_assistant.py
EMBEDDINGS = OpenAIEmbeddings(model="text-embedding-3-small")

class FaissCollectionWrapper:
    """
    Klasa-adapter do pracy z bazą FAISS w pamięci.
    """
    def __init__(self, vector_store=None):
        if vector_store is None:
            # Utwórz pustą bazę FAISS z minimalną zawartością
            self._vector_store = FAISS.from_texts(["placeholder"], EMBEDDINGS)
        else:
            self._vector_store = vector_store

    def add(self, documents, metadatas, ids):
        """
        Dodaje dokumenty do bazy FAISS (tylko w pamięci, bez zapisu na dysk).
        """
        docs_to_add = []
        for i, content in enumerate(documents):
            docs_to_add.append(Document(page_content=content, metadata=metadatas[i]))

        if docs_to_add:
            new_docs_vectorstore = FAISS.from_documents(docs_to_add, EMBEDDINGS)
            self._vector_store.merge_from(new_docs_vectorstore)
            print(f"Dodano {len(docs_to_add)} dokumentów do bazy w pamięci.")

def get_collection():
    """
    Tworzy nową, pustą bazę FAISS w pamięci.
    """
    print("Tworzenie nowej bazy danych FAISS w pamięci...")
    # Tworzymy nowy wrapper, który automatycznie utworzy pustą bazę
    return FaissCollectionWrapper()

if __name__ == '__main__':
    print("Testowanie modułu database.py...")
    collection = get_collection()
    print("Pomyślnie zainicjalizowano bazę danych FAISS.")