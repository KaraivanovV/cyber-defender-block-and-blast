from __future__ import annotations
import pygame as pg

from .base import BaseScene
from ..ui import Button, draw_panel, draw_text, hover_state
from ..localization import TEXT
from ..core import change_scene, apply_settings
from ..save_system import save, default_save
from ..constants import START_LIVES

RES_OPTIONS = [(1280,720),(1366,768),(1600,900),(1920,1080)]


class SettingsScene(BaseScene):
    def enter(self, **kwargs):
        self.btns = []
        self.page = "main"   # "main" or "confirm_reset"

    def handle_event(self, ev):
        for b in self.btns:
            b.handle(ev)

    def update(self, dt): ...

    # ---------- RESET LOGIC ----------
    def _confirm_reset(self):
        self.page = "confirm_reset"

    def _cancel_reset(self):
        self.page = "main"

    def _do_reset(self):
        app = self.app
        sd = default_save()
        sd.settings = app.save.settings  # keep settings
        app.save = sd
        save(sd)
        
        # Reset runtime state
        if hasattr(app, "_run_hearts"):
            app._run_hearts = START_LIVES
        if hasattr(app, "_wave_shield_hp"):
            app._wave_shield_hp = 0
        if hasattr(app, "_quiz_done"):
            app._quiz_done = {}
        
        from .menu import MenuScene
        change_scene(app, MenuScene(app))

    # ---------- SETTINGS CHANGES ----------
    def _cycle_lang(self):
        app = self.app
        sd = app.save
        sd.settings.lang = "mk" if sd.settings.lang == "en" else "en"
        save(sd)

    def _cycle_res(self):
        app = self.app
        sd = app.save
        cur = tuple(sd.settings.resolution)
        try:
            idx = RES_OPTIONS.index(cur)
        except ValueError:
            idx = -1
        idx = (idx + 1) % len(RES_OPTIONS)
        w, h = RES_OPTIONS[idx]
        sd.settings.resolution = [w, h]
        apply_settings(app, sd.settings)
        save(sd)

    def _toggle_fullscreen(self):
        app = self.app
        sd = app.save
        sd.settings.fullscreen = not sd.settings.fullscreen
        apply_settings(app, sd.settings)
        save(sd)

    def _adjust_music(self, delta: int):
        app = self.app
        sd = app.save
        # music_vol is 0.0-1.0, delta is -10 or +10
        sd.settings.music_vol = max(0.0, min(1.0, sd.settings.music_vol + delta / 100.0))
        save(sd)

    def _adjust_sfx(self, delta: int):
        app = self.app
        sd = app.save
        # sfx_vol is 0.0-1.0, delta is -10 or +10
        sd.settings.sfx_vol = max(0.0, min(1.0, sd.settings.sfx_vol + delta / 100.0))
        save(sd)

    # ========== DEBUG MODE - REMOVE BEFORE FINAL RELEASE ==========
    def _toggle_debug_mode(self):
        """DEBUG ONLY: Toggle debug mode - unlock all levels and give 20000 coins for testing.
        
        WARNING: REMOVE THIS FUNCTION AND ITS BUTTON BEFORE FINAL RELEASE!
        """
        app = self.app
        sd = app.save
        
        # Check if debug mode is currently enabled
        debug_enabled = getattr(sd, 'debug_mode_enabled', False)
        
        if not debug_enabled:
            # Enable debug mode
            sd.story_max_unlocked = 20  # Unlock all levels (0-20)
            sd.wallet = 20000
            sd.debug_mode_enabled = True
        else:
            # Disable debug mode (reset to normal)
            sd.story_max_unlocked = 1
            sd.wallet = 0
            sd.debug_mode_enabled = False
        
        save(sd)
    # ========== END DEBUG MODE ==========

    def _set_page(self, page: str):
        self.page = page

    # ---------- DRAW ----------
    def draw(self, surf):
        app = self.app
        sd = app.save
        lang = sd.settings.lang
        t = TEXT[lang]
        colors, fonts = app.colors, app.fonts
        self.draw_background(surf, colors)
        w, h = surf.get_size()

        panel = pg.Rect(w//2-420, h//2-300, 840, 600)
        draw_panel(surf, panel, colors, title=t["settings"], title_font=fonts.ui_bold)

        self.btns = []

        # ---------------- CONFIRM RESET PAGE ----------------
        if self.page == "confirm_reset":
            msg = "This will reset ALL progress. Wallets and upgrades will be erased.\nAre you sure?" if lang == "en" else "Ова ќе го ресетира ЦЕЛИОТ напредок. Паричници и надградби ќе бидат избришани.\nДали си сигурен?"
            
            y = panel.y + 120
            for line in msg.split('\n'):
                y = draw_text(surf, line, fonts.ui_bold, colors["text"], (panel.x + 40, y), max_w=panel.w - 80)
                y += 10
            
            btn_w = 200
            btn_h = 50
            gap = 30
            
            yes_rect = pg.Rect(panel.centerx - btn_w - gap//2, panel.centery + 60, btn_w, btn_h)
            no_rect = pg.Rect(panel.centerx + gap//2, panel.centery + 60, btn_w, btn_h)
            
            self.btns.append(Button(yes_rect, "Yes" if lang == "en" else "Да", self._do_reset))
            self.btns.append(Button(no_rect, "No" if lang == "en" else "Не", self._cancel_reset))
            
            for b in self.btns:
                b.draw(surf, fonts.ui_bold, colors, hover_state(b.rect))
            return

        # ---------------- MAIN SETTINGS PAGE ----------------
        x0 = panel.x + 40
        y0 = panel.y + 80

        # Language
        lang_label = "Language" if lang == "en" else "Јазик"
        draw_text(surf, lang_label, fonts.ui_bold, colors["text"], (x0, y0), max_w=400)
        
        lang_btn = pg.Rect(panel.x + 500, y0 - 6, 300, 42)
        lang_text = "Македонски" if lang == "mk" else "English"
        self.btns.append(Button(lang_btn, lang_text, self._cycle_lang))
        y0 += 64

        # Resolution
        res_label = "Resolution" if lang == "en" else "Резолуција"
        draw_text(surf, res_label, fonts.ui_bold, colors["text"], (x0, y0), max_w=400)
        
        res_btn = pg.Rect(panel.x + 500, y0 - 6, 300, 42)
        res_text = f"{sd.settings.resolution[0]}x{sd.settings.resolution[1]}"
        self.btns.append(Button(res_btn, res_text, self._cycle_res))
        y0 += 64

        # Fullscreen
        fs_label = "Fullscreen" if lang == "en" else "Цел екран"
        draw_text(surf, fs_label, fonts.ui_bold, colors["text"], (x0, y0), max_w=400)
        
        fs_btn = pg.Rect(panel.x + 500, y0 - 6, 300, 42)
        fs_text = "ON" if sd.settings.fullscreen else "OFF"
        self.btns.append(Button(fs_btn, fs_text, self._toggle_fullscreen))
        y0 += 64

        # Music Volume
        music_pct = int(sd.settings.music_vol * 100)
        music_label = f"Music: {music_pct}%" if lang == "en" else f"Музика: {music_pct}%"
        draw_text(surf, music_label, fonts.ui_bold, colors["text"], (x0, y0), max_w=400)
        
        music_minus = pg.Rect(panel.x + 500, y0 - 6, 145, 42)
        music_plus = pg.Rect(panel.x + 655, y0 - 6, 145, 42)
        self.btns.append(Button(music_minus, "-10", lambda: self._adjust_music(-10)))
        self.btns.append(Button(music_plus, "+10", lambda: self._adjust_music(10)))
        y0 += 64

        # SFX Volume
        sfx_pct = int(sd.settings.sfx_vol * 100)
        sfx_label = f"SFX: {sfx_pct}%" if lang == "en" else f"SFX: {sfx_pct}%"
        draw_text(surf, sfx_label, fonts.ui_bold, colors["text"], (x0, y0), max_w=400)
        
        sfx_minus = pg.Rect(panel.x + 500, y0 - 6, 145, 42)
        sfx_plus = pg.Rect(panel.x + 655, y0 - 6, 145, 42)
        self.btns.append(Button(sfx_minus, "-10", lambda: self._adjust_sfx(-10)))
        self.btns.append(Button(sfx_plus, "+10", lambda: self._adjust_sfx(10)))
        y0 += 64

        # ========== DEBUG MODE BUTTON - REMOVE BEFORE FINAL RELEASE ==========
        debug_lbl = ("DEBUG: Unlock All + 20k Coins" if lang == "en" else "DEBUG: Отклучи сè + 20k Coins")
        draw_text(surf, debug_lbl, fonts.ui_bold, colors["accent"], (x0, y0), max_w=500)
        debug_btn = pg.Rect(panel.x + 500, y0 - 6, 300, 42)
        debug_enabled = getattr(sd, 'debug_mode_enabled', False)
        debug_btn_text = "ON" if debug_enabled else "OFF"
        self.btns.append(Button(debug_btn, debug_btn_text, lambda: self._toggle_debug_mode()))
        y0 += 64
        # ========== END DEBUG MODE BUTTON ==========

        # Reset Progress
        reset_label = "Reset Progress" if lang == "en" else "Ресетирај напредок"
        draw_text(surf, reset_label, fonts.ui_bold, colors["text"], (x0, y0), max_w=400)
        
        reset_btn = pg.Rect(panel.x + 500, y0 - 6, 300, 42)
        self.btns.append(Button(reset_btn, "Reset" if lang == "en" else "Ресетирај", self._confirm_reset))
        y0 += 64

        # Back button
        back = pg.Rect(panel.x + 40, panel.bottom - 70, 180, 50)
        self.btns.append(Button(back, t.get("back", "Back"), lambda: change_scene(app, __import__('src.scenes.menu', fromlist=['MenuScene']).MenuScene(app))))

        # Draw all buttons
        for b in self.btns:
            b.draw(surf, fonts.ui_bold, colors, hover_state(b.rect))
