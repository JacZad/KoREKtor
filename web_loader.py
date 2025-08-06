import logging
import re
from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def _extract_url_content(soup: BeautifulSoup) -> str:
    """
    Wyodrębnia główną treść ze strony internetowej.
    Próbuje różnych selektorów CSS aby znaleźć główną treść.
    """
    # Selektory specyficzne dla stron PFRON
    selectors = [
        '.csc-textpic-text.article-content',  # Główny selektor dla PFRON
        '.frame.default',
        '.csc-default',
        'article',
        'main',
        '.content',
        '#content',
        '.main-content',
        '.page-content'
    ]

    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            # Połącz tekst z wszystkich znalezionych elementów
            content_parts = []
            for element in elements:
                text = element.get_text(separator='\\n', strip=True)
                if text and len(text) > 20:  # Ignore very short content
                    content_parts.append(text)

            if content_parts:
                return '\\n\\n'.join(content_parts)

    # Fallback - pobierz tekst z body
    if soup.body:
        # Remove script and style elements
        for script in soup.body(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        return soup.body.get_text(separator='\\n', strip=True)

    return ""


def load_url_documents(urls_file: str) -> List[Document]:
    """
    Pobiera i przetwarza treści ze stron internetowych z pliku URLs.
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

    for url in urls:
        try:
            logger.info(f"Pobieranie: {url}")
            response = requests.get(
                url,
                timeout=15,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.find('title').get_text().strip() if soup.find('title') else 'Brak tytułu'
            content = _extract_url_content(soup)

            if content and len(content.strip()) > 50:  # Minimum content threshold
                metadata = {
                    'source': url,
                    'title': title,
                    'type': 'website',
                    'added_date': datetime.now().strftime("%Y-%m-%d"),
                    'bibliography': f"PFRON, {title}, dostęp: {datetime.now().strftime('%d.%m.%Y')}, {url}"
                }

                # Check if contains financial data
                if re.search(r'\\d+(?:[.,]\\d+)?\\s*(?:zł|PLN|złot)', content, re.IGNORECASE):
                    metadata["contains_financial_data"] = True

                url_documents.append(Document(
                    page_content=content,
                    metadata=metadata
                ))
                logger.info(f"Pobrano treść: {len(content)} znaków")
            else:
                logger.warning(f"Brak wystarczającej treści dla: {url}")

        except requests.RequestException as e:
            logger.error(f"Błąd podczas pobierania {url}: {e}")
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas przetwarzania {url}: {e}")

    logger.info(f"Pomyślnie pobrano {len(url_documents)} dokumentów z URLs")
    return url_documents
