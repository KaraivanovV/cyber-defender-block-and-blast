"""
Book parser for reading quiz questions from book files.
"""
from __future__ import annotations
from typing import List, Dict, Optional
import re
from pathlib import Path


class Question:
    """Represents a single quiz question with bilingual support."""
    def __init__(self, number: int, text_mk: str, text_en: str, 
                 options_mk: Dict[str, str], options_en: Dict[str, str],
                 correct: str, hint_mk: str, hint_en: str):
        self.number = number
        self.text_mk = text_mk
        self.text_en = text_en
        self.options_mk = options_mk  # {"A": "...", "B": "...", "C": "..."}
        self.options_en = options_en  # {"A": "...", "B": "...", "C": "..."}
        self.correct = correct  # "A", "B", or "C"
        self.hint_mk = hint_mk
        self.hint_en = hint_en
    
    def get_text(self, lang: str) -> str:
        """Get question text in specified language."""
        return self.text_en if lang == "en" else self.text_mk
    
    def get_options(self, lang: str) -> Dict[str, str]:
        """Get options in specified language."""
        return self.options_en if lang == "en" else self.options_mk
    
    def get_hint(self, lang: str) -> str:
        """Get hint in specified language."""
        return self.hint_en if lang == "en" else self.hint_mk


class Book:
    """Represents a book with questions."""
    def __init__(self, book_id: int, title: str, questions: List[Question]):
        self.book_id = book_id
        self.title = title
        self.questions = questions
        self.level_range = self._get_level_range(book_id)
    
    def _get_level_range(self, book_id: int) -> tuple:
        """Get level range for book."""
        if book_id == 1:
            return (1, 5)
        elif book_id == 2:
            return (6, 10)
        elif book_id == 3:
            return (11, 15)
        return (1, 15)
    
    def get_question_for_level(self, level: int) -> Optional[Question]:
        """Get a random question appropriate for the level."""
        if not self.questions:
            return None
        # Use level as seed to get consistent question for same level
        index = (level - 1) % len(self.questions)
        return self.questions[index]


def parse_book_file(filepath: str) -> Optional[Book]:
    """Parse a book file and return Book object."""
    try:
        path = Path(filepath)
        if not path.exists():
            return None
        
        # Determine book ID from filename
        filename = path.name.lower()
        if "book1" in filename or "book_test" in filename:
            book_id = 1
        elif "book2" in filename:
            book_id = 2
        elif "book3" in filename:
            book_id = 3
        else:
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title from first line - handle both # and ## formats
        title_match = re.search(r'#+ (.+)', content.split('\n')[0])
        title = title_match.group(1).strip() if title_match else f"Book {book_id}"
        # Remove emoji if present
        title = re.sub(r'#\s*', '', title)
        
        # Parse questions
        questions = []
        
        # Split by ## to get question blocks
        question_blocks = re.split(r'\n##\s+', content)
        
        for block in question_blocks[1:]:  # Skip first block (header)
            try:
                lines = block.split('\n')
                if not lines:
                    continue
                
                # Extract question number and text from first line
                # Format: "1. Што е интернет? | What is the internet?"
                first_line = lines[0].strip()
                q_match = re.match(r'(\d+)\.\s*(.+)', first_line)
                if not q_match:
                    continue
                
                q_number = int(q_match.group(1))
                q_text_full = q_match.group(2).strip()
                
                # Split by | to get MK and EN versions
                if '|' in q_text_full:
                    parts = q_text_full.split('|')
                    q_text_mk = parts[0].strip()
                    q_text_en = parts[1].strip() if len(parts) > 1 else q_text_mk
                    
                    # Remove ## prefix from English text if present
                    q_text_en = re.sub(r'^##\s*\d+\.\s*', '', q_text_en)
                else:
                    # Fallback: if no pipe, use same text for both
                    q_text_mk = q_text_full
                    q_text_en = q_text_full
                
                # Extract options - look for **A)**, **B)**, **C)** pattern
                # Format: "**A)** Видео игра | **A)** Video game"
                options_mk = {}
                options_en = {}
                for line in lines:
                    option_match = re.match(r'\*\*([ABC])\)\*\*\s*(.+)', line.strip())
                    if option_match:
                        option_letter = option_match.group(1)
                        option_text_full = option_match.group(2).strip()
                        
                        # Split by | to get MK and EN versions
                        if '|' in option_text_full:
                            parts = option_text_full.split('|')
                            options_mk[option_letter] = parts[0].strip()
                            en_text = parts[1].strip() if len(parts) > 1 else parts[0].strip()
                            
                            # Remove duplicate **A)**, **B)**, **C)** from English text if present
                            en_text = re.sub(r'^\*\*[ABC]\)\*\*\s*', '', en_text)
                            options_en[option_letter] = en_text
                        else:
                            # Fallback: if no pipe, use same text for both
                            options_mk[option_letter] = option_text_full
                            options_en[option_letter] = option_text_full
                
                # Extract correct answer - look for **Точен одговор:** B
                correct = None
                for line in lines:
                    # Try Macedonian format
                    correct_match = re.search(r'\*\*Точен одговор:\*\*\s*([ABC])', line)
                    if not correct_match:
                        correct_match = re.search(r'\*\*Correct answer:\*\*\s*([ABC])', line)
                    if correct_match:
                        correct = correct_match.group(1)
                        break
                
                # Extract hints - look for both MK and EN versions
                # Format: "*Hint (MK):* текст" or "*Hint:* текст | text"
                hint_mk = ""
                hint_en = ""
                
                for line in lines:
                    # Try separate MK hint
                    hint_mk_match = re.search(r'\*Hint \(MK\):\*\s*(.+)', line)
                    if hint_mk_match:
                        hint_mk = hint_mk_match.group(1).strip()
                    
                    # Try separate EN hint
                    hint_en_match = re.search(r'\*Hint \(EN\):\*\s*(.+)', line)
                    if hint_en_match:
                        hint_en = hint_en_match.group(1).strip()
                    
                    # Try combined hint format
                    hint_combined_match = re.search(r'\*Hint:\*\s*(.+)', line)
                    if hint_combined_match and not hint_mk and not hint_en:
                        hint_full = hint_combined_match.group(1).strip()
                        if '|' in hint_full:
                            parts = hint_full.split('|')
                            hint_mk = parts[0].strip()
                            hint_en = parts[1].strip() if len(parts) > 1 else parts[0].strip()
                        else:
                            # Fallback: use same hint for both
                            hint_mk = hint_full
                            hint_en = hint_full
                
                # Create question if we have all required parts
                if len(options_mk) == 3 and len(options_en) == 3 and correct and correct in options_mk:
                    question = Question(q_number, q_text_mk, q_text_en, 
                                      options_mk, options_en, correct, hint_mk, hint_en)
                    questions.append(question)
            
            except Exception as e:
                # Skip malformed questions
                continue
        
        if questions:
            return Book(book_id, title, questions)
        
        return None
    
    except Exception:
        return None


def load_all_books(base_path: str = ".") -> Dict[int, Book]:
    """Load all three books from the base path."""
    books = {}
    
    for i in range(1, 4):
        filepath = Path(base_path) / f"book{i}.txt"
        book = parse_book_file(str(filepath))
        if book:
            books[i] = book
    
    return books


def get_book_for_level(level: int, books: Dict[int, Book]) -> Optional[Book]:
    """Get the appropriate book for a given level."""
    if 1 <= level <= 5:
        return books.get(1)
    elif 6 <= level <= 10:
        return books.get(2)
    elif 11 <= level <= 15:
        return books.get(3)
    return None
