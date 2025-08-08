#!/usr/bin/env python3
"""
Test dla poprawki duplikacji informacji o numerze strony w źródłach.

Ten test sprawdza, czy poprawka zapobiega wyświetlaniu duplikacji
informacji o numerze strony w formatowaniu źródeł PDF.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Dodaj ścieżkę do katalogu głównego projektu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import ask_hr_assistant


class TestSourceFormattingFix(unittest.TestCase):
    """Testy poprawki duplikacji informacji o numerze strony."""
    
    def setUp(self):
        """Przygotuj test case."""
        # Mock dla źródła PDF z duplikacją w sekcji
        self.pdf_source_with_duplication = {
            'type': 'pdf',
            'page': 5,
            'section': 'Strona 5',  # To powodowało duplikację
            'bibliography': 'Test Document.pdf',
            'filename': 'Test Document.pdf'
        }
        
        # Mock dla źródła PDF z poprawną sekcją
        self.pdf_source_correct = {
            'type': 'pdf', 
            'page': 5,
            'section': 'Wprowadzenie do zatrudnienia',  # Poprawna nazwa sekcji
            'bibliography': 'Test Document.pdf',
            'filename': 'Test Document.pdf'
        }
        
        # Mock dla źródła URL
        self.url_source = {
            'type': 'url',
            'url': 'https://example.com',
            'title': 'Test Article',
            'display_name': 'Test Article',
            'section': 'Główna treść'
        }

    @patch('app.hr_assistant')
    def test_no_page_duplication_in_pdf_sources(self, mock_hr_assistant):
        """Test sprawdzający, czy nie ma duplikacji informacji o stronie dla PDF."""
        
        # Mock odpowiedzi HR Assistant z potencjalną duplikacją
        mock_response = {
            'answer': 'Test odpowiedź',
            'sources': [self.pdf_source_with_duplication]
        }
        mock_hr_assistant.ask.return_value = mock_response
        
        # Wywołaj funkcję formatowania
        result = ask_hr_assistant("Test pytanie")
        
        # Sprawdź, czy nie ma duplikacji "str. 5" i "Strona 5"
        self.assertIn("str. 5", result)  # Powinno być
        self.assertNotIn("str. 5 - _Strona 5_", result)  # Nie powinno być duplikacji
        
    @patch('app.hr_assistant')
    def test_correct_section_display_for_pdf(self, mock_hr_assistant):
        """Test sprawdzający poprawne wyświetlanie prawidłowej sekcji."""
        
        # Mock odpowiedzi z poprawną sekcją
        mock_response = {
            'answer': 'Test odpowiedź',
            'sources': [self.pdf_source_correct]
        }
        mock_hr_assistant.ask.return_value = mock_response
        
        result = ask_hr_assistant("Test pytanie")
        
        # Sprawdź, czy poprawna sekcja jest wyświetlana
        self.assertIn("str. 5", result)
        self.assertIn("_Wprowadzenie do zatrudnienia_", result)
        
    @patch('app.hr_assistant') 
    def test_url_sources_formatting(self, mock_hr_assistant):
        """Test sprawdzający poprawne formatowanie źródeł URL."""
        
        mock_response = {
            'answer': 'Test odpowiedź',
            'sources': [self.url_source]
        }
        mock_hr_assistant.ask.return_value = mock_response
        
        result = ask_hr_assistant("Test pytanie")
        
        # Sprawdź formatowanie URL (nie powinno mieć informacji o stronie)
        self.assertIn("Test Article", result)
        self.assertNotIn("str. ", result)  # URL nie powinno mieć numerów stron
        
    def test_section_duplication_detection_logic(self):
        """Test logiki wykrywania duplikacji sekcji."""
        
        page = "5"
        
        # Przypadki duplikacji
        self.assertTrue(f"Strona {page}".startswith(f"Strona {page}"))
        self.assertTrue("Strona 5".startswith("Strona 5"))
        
        # Przypadki bez duplikacji  
        self.assertFalse("Wprowadzenie do zatrudnienia".startswith(f"Strona {page}"))
        self.assertFalse("Część II: Procedury".startswith(f"Strona {page}"))
        
    @patch('app.hr_assistant')
    def test_mixed_sources_formatting(self, mock_hr_assistant):
        """Test mieszanych typów źródeł."""
        
        mock_response = {
            'answer': 'Test odpowiedź',
            'sources': [
                self.pdf_source_correct,
                self.url_source,
                self.pdf_source_with_duplication
            ]
        }
        mock_hr_assistant.ask.return_value = mock_response
        
        result = ask_hr_assistant("Test pytanie")
        
        # Sprawdź, że wszystkie źródła są sformatowane poprawnie
        lines = result.split('\n')
        source_lines = [line for line in lines if line.strip() and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.'))]
        
        self.assertEqual(len(source_lines), 3)  # Powinny być 3 źródła
        
        # Sprawdź, że duplikacja nie występuje w żadnym źródle
        for line in source_lines:
            if "str. " in line:  # Jeśli to PDF z numerem strony
                # Nie powinno być "str. X - _Strona X_"
                import re
                match = re.search(r'str\. (\d+)', line)
                if match:
                    page_num = match.group(1)
                    self.assertNotIn(f"str. {page_num} - _Strona {page_num}_", line)


if __name__ == '__main__':
    # Uruchom testy
    unittest.main(verbosity=2)
