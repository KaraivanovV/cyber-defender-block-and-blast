from __future__ import annotations
import pygame as pg

from .base import BaseScene
from ..ui import Button, draw_panel, hover_state
from ..localization import TEXT
from ..core import change_scene
from .storymap import StoryMapScene
from .settings import SettingsScene
from .achievements import AchievementsScene
from .credits import CreditsScene


class MenuScene(BaseScene):
    def enter(self, **kwargs):
        self.btns = []
        self.bg_scroll = 0.0

    def handle_event(self, ev):
        for b in self.btns:
            b.handle(ev)

    def update(self, dt):
        self.bg_scroll += dt * 20

    def draw(self, surf):
        app = self.app
        lang = app.save.settings.lang
        t = TEXT[lang]
        colors = app.colors
        fonts = app.fonts
        
        self.draw_background(surf, colors)

        w, h = surf.get_size()

        # --- buttons config ---
        labels = [
            (t["start_story"], lambda: change_scene(app, StoryMapScene(app), mode="story")),
            (t["settings"], lambda: change_scene(app, SettingsScene(app))),
            (t["achievements"], lambda: change_scene(app, AchievementsScene(app))),
            (t["credits"], lambda: change_scene(app, CreditsScene(app))),
            (t["quit"], lambda: setattr(app, "running", False)),
        ]

        btn_h = 46
        gap = 14
        top_pad = 120
        bottom_pad = 40

        # dynamic height so border always wraps everything
        panel_w = 540
        panel_h = top_pad + len(labels) * btn_h + (len(labels) - 1) * gap + bottom_pad
        panel = pg.Rect(0, 0, panel_w, panel_h)
        panel.center = (w // 2, h // 2)

        draw_panel(surf, panel, colors)

        # --- title fit into panel (auto-scale if too wide) ---
        title_text = t["menu_title"]
        max_w = panel.w - 80  # padding inside panel
        y = panel.y + 34

        s = fonts.big.render(title_text, True, colors["text"])

        if s.get_width() > max_w:
            scale = max_w / s.get_width()
            new_w = max_w
            new_h = max(1, int(s.get_height() * scale))
            s = pg.transform.smoothscale(s, (new_w, new_h))

        surf.blit(s, s.get_rect(midtop=(panel.centerx, y)))

        # build buttons
        self.btns = []
        y = panel.y + top_pad

        for label, cb in labels:
            r = pg.Rect(panel.x + 90, y, panel.w - 180, btn_h)
            self.btns.append(Button(r, label, cb, enabled=True))
            y += btn_h + gap

        for b in self.btns:
            b.draw(surf, fonts.ui_bold, colors, hover_state(b.rect))
