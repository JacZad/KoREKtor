"""
Test formatowania źródeł URL jako linków w odpowiedziach asystenta HR.
"""
from hr_assistant import HRAssistant
import os


def test_source_formatting():
    """Testuje nowe formatowanie źródeł URL jako linków."""
    
    print("🔍 Test formatowania źródeł URL jako linków...")
    
    hr = HRAssistant(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        pdf_directory='pdfs'
    )
    
    # Pytania testowe, które powinny zwrócić różne typy źródeł
    test_questions = [
        "Jakie są warunki ubiegania się o dofinansowanie do wynagrodzeń?",
        "Jak obliczyć wysokość wpłat na PFRON?",
        "Jakie dokumenty są potrzebne do rejestracji pracodawcy?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"PYTANIE {i}: {question}")
        print('='*60)
        
        response = hr.ask(question)
        
        # Wyświetl odpowiedź
        print(f"\n📝 ODPOWIEDŹ:")
        print(response['answer'][:300] + "..." if len(response['answer']) > 300 else response['answer'])
        
        # Wyświetl źródła w nowym formacie
        if response.get('sources'):
            print(f"\n📚 ŹRÓDŁA:")
            for j, source in enumerate(response['sources'][:3], 1):
                if source.get('type') == 'url' and source.get('url'):
                    # Format URL jako link
                    title = source.get('title', 'Strona internetowa')
                    url = source.get('url')
                    source_text = f"{j}. [{title}]({url})"
                    
                    # Dodaj sekcję jeśli istnieje
                    section = source.get('section', '')
                    if section and section != title:
                        source_text += f" - _{section}_"
                        
                    print(source_text)
                    
                else:
                    # Format PDF
                    bibliography = source.get('bibliography', source.get('filename', ''))
                    page = source.get('page', '?')
                    section = source.get('section', '')
                    
                    source_text = f"{j}. {bibliography}"
                    if page and page != '?':
                        source_text += f", str. {page}"
                    if section and section != bibliography and section:
                        source_text += f" - _{section}_"
                    
                    print(source_text)
        else:
            print("\n📚 ŹRÓDŁA: Brak")
    
    print(f"\n{'='*60}")
    print("✅ Test zakończony! Sprawdź formatowanie linków powyżej.")
    print("💡 Linki URL są w formacie Markdown: [Tytuł](URL)")


def simulate_gradio_formatting():
    """Symuluje jak będą wyglądać odpowiedzi w interfejsie Gradio."""
    
    print("\n🖥️  Symulacja formatowania w interfejsie Gradio...")
    
    hr = HRAssistant(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        pdf_directory='pdfs'
    )
    
    question = "Jakie są warunki dofinansowania wynagrodzeń?"
    response = hr.ask(question)
    
    # Symuluj formatowanie z app.py
    answer = f"**Asystent HR:**\n\n{response['answer']}"
    
    if response.get('sources'):
        answer += f"\n\n📚 **Źródła:**\n"
        for i, source in enumerate(response['sources'][:3], 1):
            if source.get('type') == 'url' and source.get('url'):
                # Dla URL - stwórz link z tytułem
                title = source.get('title', 'Strona internetowa')
                url = source.get('url')
                source_text = f"{i}. [{title}]({url})"
                
                # Dodaj sekcję jeśli istnieje
                section = source.get('section', '')
                if section and section != title:
                    source_text += f" - _{section}_"
                    
            else:
                # Dla PDF - standardowe formatowanie
                bibliography = source.get('bibliography', source.get('filename', ''))
                page = source.get('page', '?')
                section = source.get('section', '')
                
                source_text = f"{i}. {bibliography}"
                if page and page != '?':
                    source_text += f", str. {page}"
                if section and section != bibliography and section:
                    source_text += f" - _{section}_"
            
            answer += source_text + "\n"
    
    print("\n" + "="*80)
    print("PRZYKŁAD ODPOWIEDZI W GRADIO:")
    print("="*80)
    print(answer)
    print("="*80)
    print("\n💡 W interfejsie Gradio linki będą klikalne!")


if __name__ == "__main__":
    test_source_formatting()
    simulate_gradio_formatting()
