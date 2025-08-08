import logging
from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


def get_full_content(soup: BeautifulSoup) -> str:
    """
    Pobiera pełną treść tekstową ze strony PFRON używając klasy 'article-content'.
    
    Args:
        soup: Obiekt BeautifulSoup reprezentujący sparsowaną stronę HTML.
        
    Returns:
        Ciąg znaków z pełną treścią strony lub pusty ciąg, jeśli treść nie zostanie znaleziona.
    """
    # Szukaj elementów z klasą 'article-content' (główna treść PFRON)
    elements = soup.select('.article-content')
    
    if not elements:
        # Fallback - próbuj inne selektory
        selectors = [
            '.frame.default',
            '.csc-textpic-text',
            '.csc-default',
            'article',
            'main',
            '.content',
            '#content'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                logger.info(f"Znaleziono treść za pomocą selektora: {selector}")
                break
    else:
        logger.info(f"Znaleziono {len(elements)} elementów z klasą 'article-content'")
    
    if not elements:
        logger.warning("Nie znaleziono żadnych elementów treści. Próba z body.")
        if soup.body:
            return soup.body.get_text(strip=True, separator=' ')
        return ""
    
    # Wyciągnij tekst ze wszystkich znalezionych elementów
    all_text = []
    for element in elements:
        text = element.get_text(strip=True, separator=' ')
        if text:
            all_text.append(text)
    
    return '\n\n'.join(all_text)


def load_url_documents(urls_file: str, enable_chunking: bool = False, chunk_size: int = 3000) -> List[Document]:
    """
    Pobiera i przetwarza pełne treści ze stron internetowych z pliku URLs.
    
    Args:
        urls_file: Ścieżka do pliku z adresami URL.
        enable_chunking: Czy włączyć wstępne chunkowanie długich stron.
        chunk_size: Maksymalny rozmiar chunka (tylko jeśli enable_chunking=True).
    """
    try:
        with open(urls_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        logger.warning(f"Plik '{urls_file}' nie został znaleziony. Pomijam ładowanie URLs.")
        return []
    except Exception as e:
        logger.error(f"Błąd podczas odczytu pliku {urls_file}: {e}")
        return []

    if not urls:
        logger.info("Brak URLs do przetworzenia.")
        return []

    logger.info(f"Znaleziono {len(urls)} adresów URL do przetworzenia.")
    url_documents = []
    total_chars = 0

    for url in urls:
        try:
            logger.info(f"Pobieranie: {url}")
            response = requests.get(
                url,
                timeout=15,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            response.raise_for_status()
            
            # Ustaw kodowanie na podstawie nagłówków odpowiedzi
            response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title').get_text().strip() if soup.find('title') else 'Brak tytułu'
            full_content = get_full_content(soup)

            if not full_content:
                logger.warning(f"Brak treści do zindeksowania dla: {url}")
                print(f"INFO: Pominięto stronę (brak treści): {url}")
                continue

            content_len = len(full_content)
            total_chars += content_len
            print(f"INFO: Pobrano {content_len} znaków z: {title} ({url})")

            # Zabezpieczenie przed przetwarzaniem zbyt dużych stron
            max_content_length = 1000000
            if content_len > max_content_length:
                logger.warning(f"Treść z {url} jest bardzo duża ({content_len} znaków), ograniczanie do {max_content_length}")
                full_content = full_content[:max_content_length]

            if len(full_content) > 50:  # Minimum content threshold
                metadata = {
                    'source': url,
                    'title': title,
                    'type': 'website',
                    'added_date': datetime.now().strftime("%Y-%m-%d"),
                    'bibliography': f"PFRON, {title}, dostęp: {datetime.now().strftime('%d.%m.%Y')}, {url}"
                }

                # Opcjonalne wstępne chunkowanie dla bardzo długich stron
                if enable_chunking and len(full_content) > chunk_size:
                    logger.info(f"Chunkowanie strony {url} ({len(full_content)} znaków) na części ~{chunk_size} znaków")
                    
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=chunk_size,
                        chunk_overlap=200,
                        separators=[
                            "\n\nKrok ",      # Kroki procedur PFRON
                            "\n\nPunkt ",     # Punkty list
                            "\n\nUwaga:",     # Uwagi
                            "\n\n",           # Podwójny enter
                            "\n",             # Pojedynczy enter
                            ". ",             # Koniec zdania
                            " ",              # Spacja
                            ""
                        ]
                    )
                    
                    chunks = text_splitter.split_text(full_content)
                    
                    for i, chunk in enumerate(chunks):
                        chunk_metadata = metadata.copy()
                        chunk_metadata.update({
                            'chunk_id': i,
                            'total_chunks': len(chunks),
                            'chunk_type': 'pre_chunked'
                        })
                        
                        url_documents.append(Document(
                            page_content=chunk,
                            metadata=chunk_metadata
                        ))
                else:
                    url_documents.append(Document(
                        page_content=full_content,
                        metadata=metadata
                    ))
            else:
                logger.info(f"Pominięto treść ({len(full_content)} znaków) z {url} z powodu zbyt małej długości.")

        except requests.RequestException as e:
            logger.error(f"Błąd podczas pobierania {url}: {e}")
            print(f"ERROR: Błąd sieci dla {url}: {e}")
        except Exception as e:
            logger.error(f"Błąd podczas przetwarzania {url}: {e}")
            print(f"ERROR: Błąd przetwarzania dla {url}: {e}")

    print(f"\n--- PODSUMOWANIE ---")
    print(f"Pobrano treść z {len(url_documents)} z {len(urls)} stron.")
    print(f"Łączna liczba pobranych znaków: {total_chars}")
    print(f"Średnio {total_chars // max(len(url_documents), 1)} znaków na stronę.")
    print(f"--------------------")
    
    return url_documents
