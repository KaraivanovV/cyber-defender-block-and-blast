from __future__ import annotations
import pygame as pg

from .base import BaseScene
from ..ui import Button, draw_panel, hover_state
from ..localization import TEXT
from ..core import change_scene
from ..constants import START_LIVES
from .build import BuildScene

LEVEL_COUNT = 20  # Updated from 15 to 20 (tutorial 0-5 + main game 6-20)


class StoryMapScene(BaseScene):
    def enter(self, mode="story", **kwargs):
        self.mode = mode
        self.btns: list[Button] = []
        self.scroll = 0
        self.max_scroll = 0
        self._layout()

    def _layout(self):
        w, h = self.app.screen.get_size()
        self.panel = pg.Rect(w // 2 - 460, h // 2 - 300, 920, 600)

        # scrollable list area INSIDE panel
        self.list_rect = pg.Rect(self.panel.x + 26, self.panel.y + 70, self.panel.w - 52, self.panel.h - 150)

        # fixed back button at bottom
        self.back_rect = pg.Rect(self.panel.x + 26, self.panel.bottom - 60, 180, 44)

    def handle_event(self, ev):
        if ev.type == pg.VIDEORESIZE:
            self._layout()

        # mouse wheel scroll (pygame2)
        if ev.type == pg.MOUSEWHEEL:
            if self.list_rect.collidepoint(pg.mouse.get_pos()):
                self.scroll -= ev.y * 40
                self.scroll = max(0, min(self.scroll, self.max_scroll))

        # old pygame wheel fallback
        if ev.type == pg.MOUSEBUTTONDOWN:
            if ev.button == 4:  # wheel up
                if self.list_rect.collidepoint(ev.pos):
                    self.scroll = max(0, self.scroll - 40)
            if ev.button == 5:  # wheel down
                if self.list_rect.collidepoint(ev.pos):
                    self.scroll = min(self.max_scroll, self.scroll + 40)

        for b in self.btns:
            b.handle(ev)

    def update(self, dt):
        ...

    def draw(self, surf):
        app = self.app
        sd = app.save
        lang = sd.settings.lang
        t = TEXT[lang]
        surf, colors, fonts = app.screen, app.colors, app.fonts
        self.draw_background(surf, colors)

        draw_panel(surf, self.panel, colors, title=t.get("story_map", "Story"), title_font=fonts.ui_bold)

        # unlocked logic
        unlocked_max = int(getattr(sd, "story_max_unlocked", 1))

        # row layout
        row_h = 62
        inner_pad = 0

        content_h = LEVEL_COUNT * row_h
        self.max_scroll = max(0, content_h - self.list_rect.h)

        # keep scroll valid if resize happened
        self.scroll = max(0, min(self.scroll, self.max_scroll))

        # build buttons fresh
        self.btns = []

        # --- clip to list_rect so items don't draw outside ---
        old_clip = surf.get_clip()
        surf.set_clip(self.list_rect)

        # label word (no new localization keys)
        level_word = "Ниво" if lang == "mk" else "Level"
        checkpoint_word = "Checkpoint" if lang == "en" else "Чекпоинт"
        tutorial_word = "Tutorial" if lang == "en" else "Туторијал"
        
        # Checkpoint levels - level 6 + boss levels
        CHECKPOINT_LEVELS = [6, 8, 11, 14, 17, 20]
        
        # Tutorial levels
        TUTORIAL_LEVELS = [0, 1, 2, 3, 4, 5]

        for i in range(LEVEL_COUNT + 1):  # 0 to 20 inclusive
            y = self.list_rect.y + i * row_h - self.scroll + inner_pad
            r = pg.Rect(self.list_rect.x, y, self.list_rect.w, 50)

            locked = i > unlocked_max
            enabled = not locked  # unlocked = can replay too
            is_checkpoint = i in CHECKPOINT_LEVELS
            is_tutorial = i in TUTORIAL_LEVELS

            # draw row background - special color for checkpoints and tutorials
            if is_checkpoint and not locked:
                bg_col = (60, 80, 100)  # Darker blue for unlocked checkpoints
            elif is_checkpoint and locked:
                bg_col = (40, 50, 60)  # Even darker for locked checkpoints
            elif is_tutorial and not locked:
                bg_col = (80, 60, 100)  # Purple tint for tutorial levels
            elif is_tutorial and locked:
                bg_col = (50, 40, 60)  # Darker purple for locked tutorial
            else:
                bg_col = colors["panel"] if locked else colors["panel2"]
            
            pg.draw.rect(surf, bg_col, r, border_radius=12)
            
            # Special border for checkpoints and tutorials
            if is_checkpoint and not locked:
                border_col = (100, 200, 255)
                border_width = 3
            elif is_tutorial and not locked:
                border_col = (180, 120, 255)
                border_width = 2
            else:
                border_col = colors["line"]
                border_width = 2
            pg.draw.rect(surf, border_col, r, width=border_width, border_radius=12)

            # text colors
            txt_col = colors["muted"] if locked else colors["text"]

            # All levels display with +1 offset (internal 0-20 → display Level 1-21)
            label = f"{level_word} {i + 1}"
            surf.blit(fonts.ui_bold.render(label, True, txt_col), (r.x + 16, r.y + 12))
            
            # Add checkpoint label for checkpoint levels
            if is_checkpoint:
                checkpoint_label = f"{checkpoint_word}"
                checkpoint_color = (255, 215, 0) if not locked else (100, 100, 80)
                surf.blit(fonts.ui.render(checkpoint_label, True, checkpoint_color), (r.x + 740, r.y + 14))

            icon = "" if locked else ""
            surf.blit(fonts.ui.render(icon, True, colors["muted"]), (r.right - 40, r.y + 14))

            def make_cb(level=i):
                # story uses Build -> then placement -> fight
                def start_level():
                    # Always reset hearts to full when starting from story map
                    app._run_hearts = START_LIVES
                    from .build import BuildScene
                    from .fight import FightScene
                    from .splash import SplashScene
                    from ..gameplay.level_config import get_level_config
                    
                    # Get level config to check for splash screens and special flags
                    config = get_level_config(level)
                    
                    # Determine next scene based on level config
                    skip_build = config.get("skip_build", False)
                    
                    # If level has a "splash_before", show it first
                    if "splash_before" in config:
                        splash_text = config["splash_before"].get(lang, config["splash_before"].get("en", ""))
                        
                        # Determine final destination scene
                        if skip_build:
                            final_scene_class = FightScene
                            final_args = {"mode": "story", "stage": level, "wave": 1, "obstruction": None, "tetris_coins": 0}
                        else:
                            final_scene_class = BuildScene
                            final_args = {"mode": "story", "stage": level, "wave": 1}
                        
                        # Check if there are multiple splash screens to chain
                        if "splash_before_3" in config:
                            # Three splash screens: splash_before → splash_before_2 → splash_before_3 → final scene
                            splash_text_2 = config["splash_before_2"].get(lang, config["splash_before_2"].get("en", ""))
                            splash_text_3 = config["splash_before_3"].get(lang, config["splash_before_3"].get("en", ""))
                            
                            # Create first splash that chains to second
                            splash_scene = SplashScene(app, splash_text,
                                                      next_scene_class=SplashScene,
                                                      next_scene_args={"text": splash_text_2,
                                                                      "next_scene_class": SplashScene,
                                                                      "next_scene_args": {"text": splash_text_3,
                                                                                         "next_scene_class": final_scene_class,
                                                                                         "next_scene_args": final_args}})
                            change_scene(app, splash_scene)
                        elif "splash_before_2" in config:
                            # Two splash screens: splash_before → splash_before_2 → final scene
                            splash_text_2 = config["splash_before_2"].get(lang, config["splash_before_2"].get("en", ""))
                            
                            splash_scene = SplashScene(app, splash_text,
                                                      next_scene_class=SplashScene,
                                                      next_scene_args={"text": splash_text_2,
                                                                      "next_scene_class": final_scene_class,
                                                                      "next_scene_args": final_args})
                            change_scene(app, splash_scene)
                        else:
                            # Single splash screen → final scene
                            splash_scene = SplashScene(app, splash_text,
                                                       next_scene_class=final_scene_class, 
                                                       next_scene_args=final_args)
                            change_scene(app, splash_scene)
                    else:
                        # No splash - check if we skip build
                        if skip_build:
                            # Go directly to fight
                            change_scene(app, FightScene(app), mode="story", stage=level, wave=1, 
                                       obstruction=None, tetris_coins=0)
                        else:
                            # Normal flow: build then fight
                            change_scene(app, BuildScene(app), mode="story", stage=level, wave=1)
                return start_level

            # invisible button over the row
            self.btns.append(Button(r, "", make_cb(i), enabled=enabled))

            # hover outline for enabled rows
            if enabled and hover_state(r):
                if is_checkpoint:
                    hover_col = (150, 220, 255)
                elif is_tutorial:
                    hover_col = (200, 150, 255)
                else:
                    hover_col = colors["accent"]
                pg.draw.rect(surf, hover_col, r, width=3, border_radius=12)

        surf.set_clip(old_clip)

        # back button (fixed, not scrolling)
        self.btns.append(Button(self.back_rect, t.get("back", "Back"), lambda: _go_menu(app)))

        # draw back button normally
        for b in self.btns:
            if b.rect == self.back_rect:
                b.draw(surf, fonts.ui_bold, colors, hover_state(b.rect))

        # optional: small scroll hint (only if scrollable)
        if self.max_scroll > 0:
            hint = "" if lang == "en" else ""
            surf.blit(fonts.ui.render(hint, True, colors["muted"]), (self.panel.right - 190, self.panel.y + 40))


def _go_menu(app):
    from .menu import MenuScene
    from ..core import change_scene
    change_scene(app, MenuScene(app))
