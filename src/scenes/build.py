from __future__ import annotations
import pygame as pg

from .base import BaseScene
from ..ui import draw_panel, draw_text, Button, hover_state
from ..localization import TEXT
from ..core import change_scene, create_game_rng
from ..gameplay.mini_tetris import MiniTetris, W, H


class BuildScene(BaseScene):
    def enter(self, mode="story", stage=1, wave=1, **kwargs):
        self.mode = mode
        self.stage = int(stage)
        self.wave = int(wave)

        self.paused = False
        self.pause_btns = []

        # Check if this is a building-only level (tutorial levels 2, 3, 4)
        from ..gameplay.level_config import get_level_config
        self.level_config = get_level_config(self.stage)
        self.building_only = self.level_config.get("building_only", False)

        # Base time + shop upgrade bonus
        sd = self.app.save
        tetris_bonus = sd.upgrades.get("tetris_time_bonus", 0)
        self.timer = 20.0 + tetris_bonus  # Base 20s + upgrade bonus (0-10s)

        self.rng = create_game_rng(sd, stage=self.stage, wave=self.wave)

        self.mt = MiniTetris(self.rng)
        self.coins_earned = 0

        self._layout()

    def _layout(self):
        w, h = self.app.screen.get_size()

        # main panel
        self.panel = pg.Rect(w // 2 - 560, h // 2 - 360, 1120, 720)

        pad = 28
        top_pad = 90

        # left area (grid holder) + right info panel
        right_w = 420
        gap = 22

        left_area = pg.Rect(
            self.panel.x + pad,
            self.panel.y + top_pad,
            self.panel.w - pad * 2 - right_w - gap,
            self.panel.h - top_pad - pad
        )

        self.right_rect = pg.Rect(
            left_area.right + gap,
            left_area.y,
            right_w,
            left_area.h
        )

        # --- Make grid border "tight": pick a cell size then make rect exactly fit (W x H cells) ---
        inner = left_area.inflate(-24, -24)

        cell = min(inner.w // W, inner.h // H)
        grid_w = cell * W + 2
        grid_h = cell * H + 2

        self.grid_rect = pg.Rect(0, 0, grid_w, grid_h)
        self.grid_rect.center = inner.center

        # Hold/Next boxes INSIDE right info panel
        box_gap = 18
        box_w = (self.right_rect.w - 16 * 2 - box_gap) // 2
        box_h = 150

        self.hold_rect = pg.Rect(self.right_rect.x + 16, self.right_rect.y + 70, box_w, box_h)
        self.next_rect = pg.Rect(self.hold_rect.right + box_gap, self.hold_rect.y, box_w, box_h)

    def handle_event(self, ev):
        if ev.type == pg.VIDEORESIZE:
            self._layout()

        # paused -> only pause UI
        if self.paused:
            if ev.type == pg.KEYDOWN and ev.key == pg.K_ESCAPE:
                self.paused = False
                return
            for b in self.pause_btns:
                b.handle(ev)
            return

        if ev.type == pg.KEYDOWN:
            if ev.key == pg.K_ESCAPE:
                self.paused = True
                return

            if ev.key == pg.K_LEFT:  self.mt.move(-1, 0)
            if ev.key == pg.K_RIGHT: self.mt.move(+1, 0)
            if ev.key == pg.K_DOWN:  self.mt.soft_drop()
            if ev.key == pg.K_SPACE: self.mt.hard_drop()
            if ev.key == pg.K_z:     self.mt.rotate(-1)
            if ev.key == pg.K_x:     self.mt.rotate(+1)
            if ev.key == pg.K_c:     self.mt.hold_piece()

    def update(self, dt):
        if self.paused:
            return

        self.timer -= dt
        self.mt.update(dt)

        # 1 line = 1 coin
        if self.mt.lines_cleared_last > 0:
            self.coins_earned += self.mt.lines_cleared_last

        if self.timer <= 0 or self.mt.game_over:
            # For building-only levels, skip fight and go straight to hub
            if self.building_only:
                from .hub import WaveHubScene
                change_scene(self.app, WaveHubScene(self.app),
                           mode=self.mode, stage=self.stage, wave=self.wave,
                           success=True, score=0, tetris_coins=self.coins_earned)
            else:
                # Check if there's a splash screen to show between build and fight
                if "splash_mid" in self.level_config:
                    from .splash import SplashScene
                    from .fight import FightScene
                    sd = self.app.save
                    lang = sd.settings.lang
                    splash_text = self.level_config["splash_mid"].get(lang, self.level_config["splash_mid"].get("en", ""))
                    
                    # Prepare the obstruction data for FightScene
                    obstruction = self.mt.export_obstruction()
                    
                    # Create splash that transitions to FightScene
                    splash_scene = SplashScene(self.app, splash_text,
                                             next_scene_class=FightScene,
                                             next_scene_args={
                                                 "mode": self.mode,
                                                 "stage": self.stage,
                                                 "wave": self.wave,
                                                 "obstruction": obstruction,
                                                 "tetris_coins": self.coins_earned
                                             })
                    change_scene(self.app, splash_scene)
                else:
                    # Normal levels: proceed directly to fight (no splash)
                    obstruction = self.mt.export_obstruction()
                    from .fight import FightScene
                    change_scene(self.app, FightScene(self.app),
                               mode=self.mode, stage=self.stage, wave=self.wave,
                               obstruction=obstruction, tetris_coins=self.coins_earned)

    def _draw_pause(self, surf):
        app = self.app
        colors, fonts = app.colors, app.fonts
        t = TEXT[app.save.settings.lang]

        overlay = pg.Surface(surf.get_size(), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surf.blit(overlay, (0, 0))

        w, h = surf.get_size()
        panel = pg.Rect(w // 2 - 220, h // 2 - 170, 440, 340)
        draw_panel(surf, panel, colors, title=t["pause"], title_font=fonts.ui_bold)

        self.pause_btns = []
        y = panel.y + 90

        def add(label, cb):
            nonlocal y
            r = pg.Rect(panel.x + 90, y, panel.w - 180, 46)
            self.pause_btns.append(Button(r, label, cb))
            y += 62

        add(t["resume"], lambda: setattr(self, "paused", False))

        def go_menu():
            from .menu import MenuScene  # lazy import avoids circular import
            change_scene(app, MenuScene(app))

        add(t["to_menu"], go_menu)
        add(t["quit"], lambda: setattr(app, "running", False))

        for b in self.pause_btns:
            b.draw(surf, fonts.ui_bold, colors, hover_state(b.rect))

    def draw(self, surf):
        app = self.app
        colors, fonts = app.colors, app.fonts
        lang = app.save.settings.lang
        t = TEXT[lang]

        self.draw_background(surf, colors)
        draw_panel(
            surf, self.panel, colors,
            title=("Build Firewall" if lang == "en" else "Гради ѕид"),
            title_font=fonts.ui_bold
        )

        # --- GRID PANEL (tight border) ---
        pg.draw.rect(surf, colors["panel2"], self.grid_rect, border_radius=16)
        pg.draw.rect(surf, colors["line"], self.grid_rect, width=2, border_radius=16)

        # compute exact cell and origin from tight rect
        cell = min((self.grid_rect.w - 2) // W, (self.grid_rect.h - 2) // H)
        ox = self.grid_rect.x + 1
        oy = self.grid_rect.y + 1

        # placed blocks
        for y in range(H):
            for x in range(W):
                if self.mt.grid[y][x]:
                    r = pg.Rect(ox + x * cell + 1, oy + y * cell + 1, cell - 2, cell - 2)
                    pg.draw.rect(surf, colors["accent"], r, border_radius=6)

        # current piece
        p = self.mt.current
        for cx, cy in p.cells():
            gx, gy = p.x + cx, p.y + cy
            if gy >= 0:
                r = pg.Rect(ox + gx * cell + 1, oy + gy * cell + 1, cell - 2, cell - 2)
                pg.draw.rect(surf, colors["cyan"], r, border_radius=6)

        # --- RIGHT INFO PANEL ---
        draw_panel(
            surf, self.right_rect, colors,
            title=("Info" if lang == "en" else "Инфо"),
            title_font=fonts.ui_bold
        )

        # HOLD / NEXT previews (inside right panel)
        draw_panel(surf, self.hold_rect, colors, title="Hold", title_font=fonts.ui_bold)
        draw_panel(surf, self.next_rect, colors, title=("Next" if lang == "en" else "Следно"), title_font=fonts.ui_bold)

        def draw_piece_preview(piece, rect, color):
            if not piece:
                return
            cellp = min((rect.w - 24) // 4, (rect.h - 42) // 4)
            oxp = rect.x + (rect.w - cellp * 4) // 2
            oyp = rect.y + 38
            for cx, cy in piece.cells():
                rr = pg.Rect(oxp + cx * cellp, oyp + cy * cellp, cellp - 2, cellp - 2)
                pg.draw.rect(surf, color, rr, border_radius=6)

        draw_piece_preview(getattr(self.mt, "hold", None), self.hold_rect, colors["accent"])
        draw_piece_preview(getattr(self.mt, "next_piece", None), self.next_rect, colors["cyan"])

        # info text
        rx = self.right_rect.x + 16
        ry = self.next_rect.bottom + 18

        surf.blit(fonts.ui_bold.render(
            (f"{'Time' if lang=='en' else 'Време'}: {max(0, self.timer):.1f}s"),
            True, colors["text"]), (rx, ry))
        ry += 30

        surf.blit(fonts.ui.render(
            (f"{'Lines' if lang=='en' else 'Линии'}: {self.mt.score_lines}"),
            True, colors["text"]), (rx, ry))
        ry += 24

        surf.blit(fonts.ui_bold.render(
            (f"{t['coins']}: {self.coins_earned}"),
            True, colors["text"]), (rx, ry))
        ry += 30

        # controls: display each instruction on a separate line
        if lang == "en":
            control_lines = [
                "←/→ move",
                "Z/X rotate",
                "C hold",
                "↓ soft drop",
                "SPACE hard drop"
            ]
        else:
            control_lines = [
                "←/→ движи",
                "Z/X ротирај",
                "C hold",
                "↓ спушти",
                "SPACE drop"
            ]
        
        for line in control_lines:
            surf.blit(fonts.ui.render(line, True, colors["muted"]), (rx, ry))
            ry += 20

        if self.paused:
            self._draw_pause(surf)
