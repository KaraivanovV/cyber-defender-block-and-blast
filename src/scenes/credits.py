from __future__ import annotations
import pygame as pg

from .base import BaseScene
from ..ui import Button, draw_panel, draw_text, hover_state
from ..localization import TEXT
from ..core import change_scene
class CreditsScene(BaseScene):
    def enter(self, **kwargs):
        self.btns = []

    def handle_event(self, ev):
        for b in self.btns:
            b.handle(ev)

    def update(self, dt): ...

    def draw(self, surf):
        app = self.app
        t = TEXT[app.save.settings.lang]
        colors, fonts = self.app.colors, self.app.fonts
        self.draw_background(surf, colors)

        w, h = surf.get_size()
        panel = pg.Rect(w//2-360, h//2-220, 720, 440)
        draw_panel(surf, panel, colors, title=t["credits"], title_font=fonts.ui_bold)

        x, y = panel.x+26, panel.y+80
        y = draw_text(surf, "Game Design (Pygame Template)", fonts.ui_bold, colors["text"], (x, y), max_w=panel.w-52)
        y = draw_text(surf, "Art: Procedural pixel placeholders ", fonts.ui, colors["muted"], (x, y+8), max_w=panel.w-52)
        y = draw_text(surf, "Music/SFX: Optional procedural beeps ", fonts.ui, colors["muted"], (x, y+8), max_w=panel.w-52)
        y = draw_text(surf, "Educational focus: privacy, passwords, DMs, scams", fonts.ui, colors["text"], (x, y+18), max_w=panel.w-52)

        back = pg.Rect(panel.x+26, panel.bottom-60, 160, 44)
        self.btns = [Button(back, t["back"], lambda: _go_menu(app))]
        for b in self.btns:
            b.draw(surf, fonts.ui_bold, colors, hover_state(b.rect))



def _go_menu(app):
    from .menu import MenuScene
    from ..core import change_scene
    change_scene(app, MenuScene(app))
