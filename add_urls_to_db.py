import requests
from bs4 import BeautifulSoup
from datetime import datetime
import database
import os

def extract_main_content(soup: BeautifulSoup) -> str:
    """
    Próbuje wyodrębnić główną treść artykułu ze strony, testując kilka popularnych selektorów.
    """
    # Lista potencjalnych selektorów dla głównej treści, od najbardziej specyficznego do ogólnego
    selectors = [
        ".frame.default",                         # Sugestia użytkownika
        "article",
        "div[role='article']",
        "main",
        "div[role='main']",
        ".csc-textpic-text.article-content",      # Poprzedni selektor
        ".article-content",
        ".post-content",
        ".entry-content"
    ]
    
    best_content = ""
    
    # Przetestuj selektory i znajdź ten, który daje najwięcej tekstu
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            current_content = element.get_text(separator='\n', strip=True)
            if len(current_content) > len(best_content):
                best_content = current_content
                
    # Jeśli nic nie znaleziono, w ostateczności weź całe body
    if not best_content and soup.body:
        body_text = soup.body.get_text(separator='\n', strip=True)
        lines = body_text.split('\n')
        meaningful_lines = [line for line in lines if len(line.strip()) > 30]
        best_content = "\n".join(meaningful_lines)

    return best_content

def scrape_and_store_urls(file_path='urls.txt'):
    """
    Scrapes content from URLs listed in a file and stores them in the database.
    """
    print("--- Rozpoczęcie skryptu scrape_and_store_urls (wersja z selektorem .frame.default) ---")

    if not os.path.exists(file_path):
        print(f"BŁĄD KRYTYCZNY: Plik '{file_path}' nie został znaleziony.")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        print(f"Znaleziono {len(urls)} adresów URL w pliku '{file_path}'.")
    except Exception as e:
        print(f"BŁĄD KRYTYCZNY: Nie udało się odczytać pliku '{file_path}': {e}")
        return

    print("\n--- Inicjalizacja bazy danych ---")
    collection = database.get_collection()
    print("Pomyślnie połączono z bazą danych FAISS.")

    print("\n--- Rozpoczęcie przetwarzania adresów URL ---")
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Przetwarzanie: {url}")
        try:
            response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            print(f"  - Status odpowiedzi HTTP: {response.status_code} (OK)")

            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.find('title').get_text().strip() if soup.find('title') else 'Brak tytułu'
            
            content = extract_main_content(soup)
            
            if content:
                print(f"  - Znaleziono treść (rozmiar: {len(content)} znaków).")
            else:
                print(f"  - OSTRZEŻENIE: Nie udało się wyodrębnić treści ze strony {url}. Pomijanie.")
                continue

            current_date = datetime.now().strftime("%Y-%m-%d")
            metadata = {'source': url, 'title': title, 'added_date': current_date}
            
            print("  - Próba dodania do bazy danych...")
            collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[f"url_{url}"]
            )
            print("  - SUKCES: Pomyślnie dodano dokument i zapisano bazę danych.")

        except requests.RequestException as e:
            print(f"  - BŁĄD: Nie udało się pobrać strony {url}: {e}")
        except Exception as e:
            print(f"  - BŁĄD: Wystąpił nieoczekiwany błąd podczas przetwarzania {url}: {e}")

    print("\n--- Zakończono skrypt ---")

if __name__ == '__main__':
    scrape_and_store_urls()