from __future__ import annotations
import pygame as pg

from .base import BaseScene
from ..ui import Button, draw_panel, draw_text, hover_state
from ..localization import TEXT
from ..core import change_scene
from ..save_system import save
from ..constants import START_LIVES
from ..achievements import check_achievement


class WaveHubScene(BaseScene):
    def enter(self, mode="story", stage=1, wave=1, success=False, score=0, tetris_coins=0, **kwargs):
        self.mode = mode
        self.stage = int(stage)
        self.wave = int(wave)
        self.success = bool(success)
        self.score = int(score)
        self.tetris_coins = int(tetris_coins)

        sd = self.app.save

        # --- ensure fields exist (backwards compatible) ---
        if not hasattr(sd, "wallet"): sd.wallet = 0
        if not hasattr(sd, "story_best"): sd.story_best = 0
        if not hasattr(sd, "story_max_unlocked"): sd.story_max_unlocked = 1
        if not hasattr(sd, "completed_tutorials"): sd.completed_tutorials = []
        
        # Check if this is a tutorial replay
        from ..gameplay.level_config import TUTORIAL_LEVELS
        is_tutorial = self.stage in TUTORIAL_LEVELS
        self.is_tutorial_replay = is_tutorial and self.stage in sd.completed_tutorials

        # Calculate combat coin rewards (only if not a tutorial replay)
        combat_coins = 0
        
        if self.success and not self.is_tutorial_replay:
            # Score to coins conversion (1 coin per 20 points)
            combat_coins += self.score // 20
            
            # Level completion bonus (scales with level difficulty)
            level_bonus = 10 + (self.stage - 1) * 3  # 10 coins at level 1, up to 52 at level 15
            combat_coins += level_bonus
            
            # Perfect defense bonus (no hearts lost)
            current_hearts = getattr(self.app, "_run_hearts", START_LIVES)
            if current_hearts == START_LIVES:
                combat_coins += 20
        
        # Mark tutorial as completed if first time
        if self.success and is_tutorial and self.stage not in sd.completed_tutorials:
            sd.completed_tutorials.append(self.stage)
        
        # Add all coins to wallet (will be 0 for tutorial replays)
        total_coins = self.tetris_coins + combat_coins
        sd.wallet += total_coins
        sd.story_best = max(sd.story_best, self.score)
        
        # Store for display
        self.combat_coins = combat_coins

        # quiz used tracker
        if not hasattr(self.app, "_quiz_done"):
            self.app._quiz_done = {}
        key = (self.mode, self.stage)
        if key not in self.app._quiz_done:
            self.app._quiz_done[key] = False

        self.game_over = not self.success

        save(sd)
        self._layout()
        self.btns = []

    def _layout(self):
        w, h = self.app.screen.get_size()
        self.panel = pg.Rect(w // 2 - 420, h // 2 - 280, 840, 560)

    def handle_event(self, ev):
        if ev.type == pg.VIDEORESIZE:
            self._layout()
        for b in self.btns:
            b.handle(ev)

    def update(self, dt): ...

    def draw(self, surf):
        app = self.app
        sd = app.save
        colors, fonts = app.colors, app.fonts
        t = TEXT[sd.settings.lang]

        self.draw_background(surf, colors)
        title = "Wave Complete" if sd.settings.lang == "en" else "Бран завршен"
        if self.game_over:
            title = "Game Over" if sd.settings.lang == "en" else "Крај на играта"

        draw_panel(surf, self.panel, colors, title=title, title_font=fonts.ui_bold)

        x = self.panel.x + 36
        y = self.panel.y + 90

        # Result text
        if self.success:
            result_text = "Victory!" if sd.settings.lang == "en" else "Победа!"
            result_color = colors["good"]
        else:
            result_text = "Defeat" if sd.settings.lang == "en" else "Пораз"
            result_color = colors["bad"]

        lines = [
            (result_text, result_color),
            (f"Score: {self.score}", colors["text"]),
            (f"{'Tetris coins' if sd.settings.lang == 'en' else 'Тетрис coins'}: +{self.tetris_coins}", colors["accent"]),
            (f"{'Combat coins' if sd.settings.lang == 'en' else 'Борба coins'}: +{self.combat_coins}", colors["accent"]),
            (f"{'Total coins earned' if sd.settings.lang == 'en' else 'Вкупно coins'}: +{self.tetris_coins + self.combat_coins}", colors["cyan"]),
        ]
        
        for text, color in lines:
            y = draw_text(surf, text, fonts.ui, color, (x, y), max_w=self.panel.w - 72)
            y += 6
        
        y += 10 # Add a bit more space before wallet

        wallet = sd.wallet
        y = draw_text(
            surf,
            (f"Wallet: {wallet}" if sd.settings.lang == "en" else f"Паричник: {wallet}"),
            fonts.ui_bold, colors["text"], (x, y), max_w=self.panel.w - 72
        )
        y += 20
        
        # Show tutorial replay message if applicable
        if self.is_tutorial_replay and self.success:
            replay_msg = "Tutorial Replay - No Coins Earned" if sd.settings.lang == "en" else "Туторијал повторување - Без coins"
            y = draw_text(
                surf,
                replay_msg,
                fonts.ui_bold,
                colors["muted"],
                (x, y),
                max_w=self.panel.w - 72
            )
            y += 20

        self.btns = []

        # --- buttons layout (Library left, Shop right, Continue centered bigger) ---
        btn_h = 64
        gap = 26

        btn_w_small = 320
        btn_w_big = 520

        row_y = self.panel.bottom - 240

        total_w = btn_w_small * 2 + gap
        left_x = self.panel.centerx - total_w // 2

        key = (self.mode, self.stage)
        quiz_done = self.app._quiz_done.get(key, False)

        # Checkpoint levels - level 6 + boss levels
        CHECKPOINT_LEVELS = [6, 8, 11, 14, 17, 20]

        def on_continue():
            if self.game_over:
                # Find last checkpoint the player has crossed
                if hasattr(sd, 'checkpoint_hearts') and sd.checkpoint_hearts:
                    # Get all checkpoints player has reached that are before or at current level
                    # Convert keys to int because JSON stores dict keys as strings
                    reached_checkpoints = [int(lvl) for lvl in sorted(sd.checkpoint_hearts.keys()) if int(lvl) <= self.stage]
                    
                    if reached_checkpoints:
                        # Respawn at last checkpoint
                        last_checkpoint = max(reached_checkpoints)
                        # Access dictionary with string key because JSON stores int keys as strings
                        restored_hearts = sd.checkpoint_hearts[str(last_checkpoint)]
                        
                        # Set hearts for next run
                        app._run_hearts = restored_hearts
                        
                        # Restart from checkpoint
                        from .build import BuildScene
                        from .fight import FightScene
                        from ..gameplay.level_config import get_level_config
                        
                        checkpoint_config = get_level_config(last_checkpoint)
                        if checkpoint_config.get("skip_build", False):
                            change_scene(app, FightScene(app), mode="story", stage=last_checkpoint, wave=1,
                                       obstruction=None, tetris_coins=0)
                        else:
                            change_scene(app, BuildScene(app), mode="story", stage=last_checkpoint, wave=1)
                        return
                
                # No checkpoint reached yet - game over
                from .menu import MenuScene
                change_scene(app, MenuScene(app))
                return

            # Save checkpoint if current level is a checkpoint and we succeeded
            if self.success and self.stage in CHECKPOINT_LEVELS:
                current_hearts = getattr(app, "_run_hearts", START_LIVES)
                if not hasattr(sd, "checkpoint_hearts"):
                    sd.checkpoint_hearts = {}
                sd.checkpoint_hearts[self.stage] = current_hearts
                
                # Track checkpoint achievement
                check_achievement(sd, "checkpoint_champion", 1)
            
            # Tutorial completion checkpoint (Level 5)
            if self.success and self.stage == 5:
                sd.tutorial_completed = True
            
            # Track level completion achievements
            if self.success:
                # Check hearts for perfect defense / close call
                current_hearts = getattr(app, "_run_hearts", START_LIVES)
                
                # Perfect defense (no hearts lost)
                if current_hearts == START_LIVES:
                    check_achievement(sd, "perfect_defense", 1)
                    check_achievement(sd, "untouchable", 1)
                
                # Close call (only 1 heart left)
                if current_hearts == 1:
                    check_achievement(sd, "close_call", 1)
                
                # Story progress achievements based on level (updated for 20 levels)
                if self.stage >= 1:
                    check_achievement(sd, "first_steps", self.stage)
                if self.stage >= 5:
                    check_achievement(sd, "getting_started", self.stage)
                if self.stage >= 10:
                    check_achievement(sd, "halfway_there", self.stage)
                if self.stage >= 15:
                    check_achievement(sd, "almost_done", self.stage)
                if self.stage >= 20:
                    check_achievement(sd, "cyber_hero", self.stage)

            sd.story_max_unlocked = max(sd.story_max_unlocked, min(20, self.stage + 1))
            save(sd)

            # Check for game completion
            from ..gameplay.level_config import get_level_config
            
            if self.stage >= 20:
                # Game complete!
                from .menu import MenuScene
                change_scene(app, MenuScene(app))
                return
            
            # Get next level config to check if it skips build or has firewall explanation
            next_config = get_level_config(self.stage + 1)
            skip_next_build = next_config.get("skip_build", False)
            lang = sd.settings.lang
            
            # Check if next level has firewall_explanation splash to show
            if "firewall_explanation" in next_config:
                from .splash import SplashScene
                from .build import BuildScene
                from .fight import FightScene
                
                explanation_text = next_config["firewall_explanation"].get(lang, next_config["firewall_explanation"].get("en", ""))
                
                # Determine final scene after explanation
                if skip_next_build:
                    final_scene_class = FightScene
                    final_args = {"mode": "story", "stage": self.stage + 1, "wave": 1, "obstruction": None, "tetris_coins": 0}
                else:
                    final_scene_class = BuildScene
                    final_args = {"mode": "story", "stage": self.stage + 1, "wave": 1}
                
                # Show explanation splash then go to next level
                splash_scene = SplashScene(app, explanation_text,
                                         next_scene_class=final_scene_class,
                                         next_scene_args=final_args)
                change_scene(app, splash_scene)
            else:
                # No explanation - go directly to next level
                if skip_next_build:
                    from .fight import FightScene
                    change_scene(app, FightScene(app), mode="story", stage=self.stage + 1, wave=1,
                               obstruction=None, tetris_coins=0)
                else:
                    # Normal flow: continue to next level's build phase
                    from .build import BuildScene
                    change_scene(app, BuildScene(app), mode="story", stage=self.stage + 1, wave=1)

        def on_library():
            if quiz_done or self.game_over:
                return
            
            # Tutorial restriction: Library only available after Level 4
            if self.stage < 4 and not sd.tutorial_completed:
                return
            
            # Check if this is the first time accessing the library
            if not hasattr(sd, 'library_first_visit'):
                sd.library_first_visit = True
                save(sd)
                
                # Show library explanation splash before opening library
                from .splash import SplashScene
                from .quiz import QuizScene
                lang = sd.settings.lang
                
                explanation_text = {
                    "en": "LIBRARY UNLOCKED!\n\nThe Library will ask you questions\nabout staying safe online!\n\nAnswer correctly to earn rewards!\n\nALL SYSTEMS REBUILT!\nNow you're ready for real battles!",
                    "mk": "БИБЛИОТЕКАТА Е ОТКЛУЧЕНА!\n\nБиблиотеката ќе ти поставува прашања\nза безбедност на интернет!\n\nОдговарај точно за награди!\n\nСИТЕ СИСТЕМИ СЕ ОБНОВЕНИ!\nСега си подготвен за вистински битки!"
                }
                
                splash_text = explanation_text.get(lang, explanation_text.get("en", ""))
                splash_scene = SplashScene(app, splash_text,
                                         next_scene_class=QuizScene,
                                         next_scene_args={"mode": self.mode, "stage": self.stage, "wave": self.wave})
                change_scene(app, splash_scene)
            else:
                # Normal library access
                from .quiz import QuizScene
                change_scene(app, QuizScene(app), mode=self.mode, stage=self.stage, wave=self.wave)

        def on_shop():
            if self.game_over:
                return
            from .shop import ShopScene
            change_scene(app, ShopScene(app), mode=self.mode, stage=self.stage, wave=self.wave)
        
        # Tutorial restrictions:
        # Library unlocks after Level 4 (when library is rebuilt)
        # Shop unlocks after Level 3 (when shop is rebuilt)
        library_unlocked = self.stage >= 4
        shop_unlocked = self.stage >= 3

        cont_label = "Continue" if sd.settings.lang == "en" else "Продолжи"
        lib_label = "Library" if sd.settings.lang == "en" else "Библиотека"
        shop_label = "Shop" if sd.settings.lang == "en" else "Продавница"

        r_lib = pg.Rect(left_x, row_y, btn_w_small, btn_h)
        r_shop = pg.Rect(left_x + btn_w_small + gap, row_y, btn_w_small, btn_h)
        r_cont = pg.Rect(self.panel.centerx - btn_w_big // 2, row_y + btn_h + gap, btn_w_big, btn_h)

        # message (make it clearly visible and not hidden behind buttons)
        if quiz_done and not self.game_over:
            msg = "Library already used this wave." if sd.settings.lang == "en" else "Квизот веќе е решен за овој бран."
            draw_text(
                surf,
                msg,
                fonts.ui_bold,
                colors["text"],
                (self.panel.x + 36, row_y - 46),
                max_w=self.panel.w - 72
            )

        self.btns.append(Button(r_cont, cont_label, on_continue, enabled=True))
        self.btns.append(Button(r_lib, lib_label, on_library, enabled=(library_unlocked and not quiz_done and not self.game_over)))
        self.btns.append(Button(r_shop, shop_label, on_shop, enabled=(shop_unlocked and not self.game_over)))

        for b in self.btns:
            b.draw(surf, fonts.ui_bold, colors, hover_state(b.rect))
