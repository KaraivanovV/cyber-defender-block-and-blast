from __future__ import annotations
import pygame as pg
import random
import os

from .base import BaseScene
from ..ui import Button, draw_panel, draw_text, hover_state
from ..localization import TEXT
from ..core import change_scene
from ..save_system import save
from ..gameplay.book_parser import load_all_books, get_book_for_level


class QuizScene(BaseScene):
    def enter(self, mode="story", stage=1, wave=1, **kwargs):
        self.mode = mode
        self.stage = int(stage)
        self.wave = int(wave)

        # Load books from project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.books = load_all_books(project_root)
        
        # Get appropriate book for current level
        self.current_book = get_book_for_level(self.stage, self.books)
        
        # Check if player owns this book
        sd = self.app.save
        book_id = self._get_book_id_for_level(self.stage)
        self.owns_book = book_id in getattr(sd, 'owned_books', [])
        
        # Select 5 random questions from the book
        self.questions = []
        if self.current_book and self.current_book.questions:
            all_questions = list(self.current_book.questions)
            random.shuffle(all_questions)
            self.questions = all_questions[:min(5, len(all_questions))]
        
        self.idx = 0
        self.correct = 0
        self.done = False
        self.result_text = ""
        self.btns = []
        self._layout()

    def _get_book_id_for_level(self, level: int) -> int:
        """Get book ID for a given level."""
        if 1 <= level <= 5:
            return 1
        elif 6 <= level <= 10:
            return 2
        elif 11 <= level <= 15:
            return 3
        return 1

    def _layout(self):
        w, h = self.app.screen.get_size()
        self.panel = pg.Rect(w//2-500, h//2-300, 1000, 600)

    def handle_event(self, ev):
        if ev.type == pg.VIDEORESIZE:
            self._layout()
        for b in self.btns:
            b.handle(ev)

    def update(self, dt): ...

    def _answer(self, choice: str):
        if self.done or not self.questions:
            return

        q = self.questions[self.idx]
        lang = self.app.save.settings.lang
        
        if choice == q.correct:
            self.correct += 1
            self.result_text = " Correct!" if lang == "en" else " Точно!"
        else:
            self.result_text = f" Wrong! Correct: {q.correct}" if lang == "en" else f" Неточно! Точен: {q.correct}"

        self.idx += 1
        if self.idx >= len(self.questions):
            self.done = True

            gain = 10 * self.correct
            sd = self.app.save
            sd.wallet += gain
            save(sd)

            if not hasattr(self.app, "_quiz_done"):
                self.app._quiz_done = {}
            self.app._quiz_done[(self.mode, self.stage)] = True

    def _back_to_hub(self):
        from .hub import WaveHubScene
        change_scene(self.app, WaveHubScene(self.app),
                     mode=self.mode, stage=self.stage, wave=self.wave,
                     success=True, score=0, tetris_coins=0)

    def draw(self, surf):
        app = self.app
        sd = app.save
        colors, fonts = app.colors, app.fonts
        self.draw_background(surf, colors)
        t = TEXT[sd.settings.lang]
        lang = sd.settings.lang

        title = "Library Quiz" if lang == "en" else "Библиотека - Квиз"
        draw_panel(surf, self.panel, colors, title=title, title_font=fonts.ui_bold)

        self.btns = []
        x = self.panel.x + 40
        y = self.panel.y + 90

        if not self.questions:
            # No questions available
            msg = "No questions available for this level." if lang == "en" else "Нема прашања за ова ниво."
            y = draw_text(surf, msg, fonts.ui_bold, colors["text"], (x, y), max_w=self.panel.w-80)
            
            r = pg.Rect(self.panel.centerx-160, self.panel.bottom-110, 320, 56)
            self.btns.append(Button(r, ("Back" if lang == "en" else "Назад"), self._back_to_hub))
        
        elif not self.done:
            q = self.questions[self.idx]
            
            # Get text in current language
            text = q.get_text(lang)
            options = q.get_options(lang)
            hint = q.get_hint(lang)
            
            # Question text
            y = draw_text(surf, f"{self.idx+1}/5: {text}", fonts.ui_bold, colors["text"], (x, y), max_w=self.panel.w-80)
            y += 20

            # Show result from previous question
            if self.result_text:
                result_color = colors["text"] if "" in self.result_text else colors["bad"]
                y = draw_text(surf, self.result_text, fonts.ui, result_color, (x, y), max_w=self.panel.w-80)
                y += 15

            # Show hint if book is owned
            if self.owns_book and hint:
                y = draw_text(surf, hint, fonts.ui, (255, 215, 0), (x, y), max_w=self.panel.w-80)
                y += 10
            elif not self.owns_book:
                book_id = self._get_book_id_for_level(self.stage)
                no_hint = f" Buy Book {book_id} in shop to unlock hints" if lang == "en" else f" Купи Книга {book_id} во продавница за hints"
                y = draw_text(surf, no_hint, fonts.ui, colors["muted"], (x, y), max_w=self.panel.w-80)
                y += 10

            # Answer buttons
            btn_w = (self.panel.w - 140) // 3
            btn_y = self.panel.bottom - 120
            gap = 20

            for i, (letter, text) in enumerate(options.items()):
                r = pg.Rect(self.panel.x + 40 + i*(btn_w+gap), btn_y, btn_w, 70)
                label = f"{letter}) {text}"
                self.btns.append(Button(r, label, lambda c=letter: self._answer(c), enabled=True))

        else:
            # Quiz completed
            gain = 10 * self.correct
            msg = (f"You got {self.correct}/5   (+{gain} coins)" if lang == "en"
                   else f"Имаш {self.correct}/5   (+{gain} coins)")
            y = draw_text(surf, msg, fonts.big, colors["text"], (x, y), max_w=self.panel.w-80)
            y += 20

            tip = ("Quiz can be done only once per wave." if lang == "en"
                   else "Квизот може само еднаш по бран.")
            y = draw_text(surf, tip, fonts.ui, colors["muted"], (x, y), max_w=self.panel.w-80)

            r = pg.Rect(self.panel.centerx-160, self.panel.bottom-110, 320, 56)
            self.btns.append(Button(r, ("Back" if lang == "en" else "Назад"), self._back_to_hub))

        for b in self.btns:
            b.draw(surf, fonts.ui_bold, colors, hover_state(b.rect))
