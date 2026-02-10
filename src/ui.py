from __future__ import annotations
import pygame as pg
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

@dataclass
class Button:
    rect: pg.Rect
    text: str
    on_click: Callable[[], None]
    enabled: bool = True
    tooltip: Optional[str] = None

    def handle(self, ev: pg.event.Event):
        if not self.enabled:
            return
        if ev.type == pg.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                self.on_click()

    def draw(self, surf: pg.Surface, font: pg.font.Font, colors: dict, hover: bool=False):
        bg = colors["panel2"] if hover and self.enabled else colors["panel"]
        if not self.enabled:
            bg = (colors["panel"][0], colors["panel"][1], colors["panel"][2])
        pg.draw.rect(surf, bg, self.rect, border_radius=10)
        pg.draw.rect(surf, colors["line"], self.rect, width=2, border_radius=10)

        tcol = colors["text"] if self.enabled else colors["muted"]
        
        # Word wrap text to fit within button
        max_width = self.rect.width - 20  # 10px padding on each side
        words = self.text.split(" ")
        lines = []
        current_line = ""
        
        for word in words:
            test_line = (current_line + " " + word).strip()
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Render lines centered vertically and horizontally
        line_height = font.get_height()
        total_height = len(lines) * line_height
        start_y = self.rect.centery - total_height // 2
        
        for i, line in enumerate(lines):
            img = font.render(line, True, tcol)
            text_rect = img.get_rect(center=(self.rect.centerx, start_y + i * line_height + line_height // 2))
            surf.blit(img, text_rect)

def draw_panel(surf: pg.Surface, rect: pg.Rect, colors: dict, title: str|None=None,
               title_font: pg.font.Font|None=None):
    pg.draw.rect(surf, colors["panel"], rect, border_radius=14)
    pg.draw.rect(surf, colors["line"], rect, width=2, border_radius=14)
    if title and title_font:
        img = title_font.render(title, True, colors["text"])
        surf.blit(img, (rect.x+14, rect.y+10))

def draw_text(surf: pg.Surface, text: str, font: pg.font.Font, color: tuple, pos: Tuple[int,int], max_w: int|None=None, line_h: int|None=None):
    # Simple word wrap
    if not max_w:
        surf.blit(font.render(text, True, color), pos)
        return pos[1] + font.get_height()
    words = text.split(" ")
    x, y = pos
    lh = line_h or int(font.get_height()*1.2)
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if font.size(test)[0] <= max_w:
            line = test
        else:
            surf.blit(font.render(line, True, color), (x, y))
            y += lh
            line = w
    if line:
        surf.blit(font.render(line, True, color), (x, y))
        y += lh
    return y

def hover_state(rect: pg.Rect) -> bool:
    return rect.collidepoint(pg.mouse.get_pos())

