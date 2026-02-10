from __future__ import annotations
import pygame as pg

from ..assets import SHIP_SKINS, TRAILS
from .base import BaseScene
from ..ui import draw_panel, Button, hover_state
from ..localization import TEXT
from ..core import change_scene, create_game_rng
from ..constants import PANEL_PAD, START_LIVES, SHIP_SPEED, BULLET_SPEED
from ..gameplay.invaders import InvaderField, Bullet
from ..gameplay.boss import BossField
from ..gameplay.level_config import get_level_config, is_boss_level, get_enemy_type_stats
from ..save_system import save, default_save

OB_W, OB_H = 10, 10


class FightScene(BaseScene):
    """
    Phase 1 (placement):
      - A/D select wall
      - Q/E move selected wall
      - ENTER to start fight

    Phase 2 (fight):
      - LEFT/RIGHT move ship
      - HOLD SPACE shoot
      - walls are FIXED
    """

    def __init__(self, app):
        super().__init__(app)
        self.score = 0
        self.lives = START_LIVES
        self.paused = False
        self.phase = "place"

        # unified pause menu (same as build/game)
        self.pause_btns: list[Button] = []

        # remember last enter args for restart
        self._last_enter_kwargs = {}
        
        # Brick collection system
        self.bricks = []  # List of falling bricks
        self.bricks_collected = 0  # Counter for collected bricks
        
        # Load boss sprites
        from ..assets import load_boss_sprites
        self.boss_sprites = load_boss_sprites()
        
        # Load enemy sprites
        self.enemy_sprites = {}
        try:
            from pathlib import Path
            assets_path = Path(__file__).parent.parent.parent / "assets"
            enemy_types = ["basic", "fast", "armored", "shooter", "elite", "berserker"]
            for enemy_type in enemy_types:
                sprite_path = assets_path / f"enemy_{enemy_type}.png"
                if sprite_path.exists():
                    self.enemy_sprites[enemy_type] = pg.image.load(str(sprite_path)).convert_alpha()
        except Exception as e:
            print(f"Could not load enemy sprites: {e}")

    # ---------------- Progress reset / navigation ----------------
    def _reset_progress(self):
        """Hard reset: wallets + upgrades + runtime hearts/shield."""
        sd = self.app.save

        sd.wallet = 0

        # upgrades -> defaults
        sd.upgrades = dict(default_save().upgrades)

        # runtime carry values
        self.app._run_hearts = START_LIVES
        self.app._wave_shield_hp = 0

        save(sd)

    def _go_main_menu(self):
        # lazy import to avoid circular imports
        from .menu import MenuScene
        change_scene(self.app, MenuScene(self.app))

    def _quit_game(self):
        # main loop will save + quit pygame
        self.app.running = False

    def _restart(self):
        kw = dict(self._last_enter_kwargs)
        self.enter(**kw)

    # ---------------- Pause helpers ----------------
    def _set_paused(self, v: bool):
        self.paused = bool(v)

    def _draw_pause(self, surf):
        app = self.app
        colors, fonts = app.colors, app.fonts
        t = TEXT[app.save.settings.lang]

        overlay = pg.Surface(surf.get_size(), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surf.blit(overlay, (0, 0))

        w, h = surf.get_size()
        panel = pg.Rect(w // 2 - 220, h // 2 - 170, 440, 340)
        draw_panel(surf, panel, colors, title=t.get("pause", "Pause"), title_font=fonts.ui_bold)

        self.pause_btns = []
        y = panel.y + 90

        def add(label, cb):
            nonlocal y
            r = pg.Rect(panel.x + 90, y, panel.w - 180, 46)
            self.pause_btns.append(Button(r, label, cb))
            y += 62

        add(t.get("resume", "Resume"), lambda: self._set_paused(False))

        def go_menu():
            from .menu import MenuScene  # lazy import avoids circular issues
            change_scene(app, MenuScene(app))

        add(t.get("to_menu", "Main Menu"), go_menu)
        add(t.get("quit", "Quit"), lambda: setattr(app, "running", False))

        for b in self.pause_btns:
            b.draw(surf, fonts.ui_bold, colors, hover_state(b.rect))

    # ---------------- Enter ----------------
    def enter(self, mode="story", stage=1, wave=1, obstruction=None, tetris_coins=0, **kwargs):
        self._last_enter_kwargs = dict(
            mode=mode, stage=stage, wave=wave,
            obstruction=obstruction, tetris_coins=tetris_coins, **kwargs
        )

        self.mode = mode
        self.stage = int(stage)
        self.wave = int(wave)

        self.score = 0
        self.paused = False
        self.phase = "place"
        self.shoot_held = False
        self.fire_cd = 0.0
        
        # Dash mechanic
        self.dash_cd = 0.0
        self.dash_cooldown = 2.0  # 2 seconds cooldown
        self.dashing = False
        self.dash_duration = 0.15  # 0.15 seconds dash
        self.dash_timer = 0.0
        
        # Level 0 unwinnable logic
        from ..gameplay.level_config import get_level_config
        level_config = get_level_config(self.stage)
        self.unwinnable = level_config.get("unwinnable", False)
        self.unwinnable_timer = 15.0 if self.unwinnable else 0.0  # Force loss after 15 seconds
        
        # Tutorial restrictions
        self.is_tutorial = level_config.get("tutorial", False)
        self.skip_placement = level_config.get("skip_build", False)  # Levels 0-1 skip wall placement
        self.dash_enabled = self.stage >= 8  # Dash unlocks at Level 8 (first boss)

        self.obstruction = obstruction or [[0] * OB_W for _ in range(OB_H)]
        self.tetris_coins = int(tetris_coins)

        # hearts carry through run
        self.lives = getattr(self.app, "_run_hearts", START_LIVES)

        sd = self.app.save
        up = getattr(sd, "upgrades", {})
        if not isinstance(up, dict):
            up = {}

        self.block_hp = int(up.get("block_hp", 1))
        self.fire_rate_lvl = int(up.get("fire_rate_lvl", 1))
        self.num_walls = int(up.get("obstacle_slots", 1))
        
        # If skipping placement, start in fight phase immediately
        if self.skip_placement:
            self.phase = "fight"

        # shield is wave-only
        self.shield_hp = getattr(self.app, "_wave_shield_hp", 0)

        # RNG
        self.rng = create_game_rng(sd, stage=self.stage, wave=self.wave)

        self._layout()

        self.WALL_SCALE = 1.10  # wall size multiplier

        # Load level configuration
        self.level_config = get_level_config(self.stage)
        
        # Brick dropping system (for tutorial levels)
        self.drop_bricks_enabled = self.level_config.get("drop_bricks", False)
        self.bricks_required = self.level_config.get("bricks_required", 0)  # How many bricks to collect
        self.bricks = []  # Reset bricks for new level
        self.bricks_collected = 0  # Reset counter
        
        self.is_boss = is_boss_level(self.stage)
        
        if self.is_boss:
            # Boss fight
            self.boss_field = BossField(self.rng, level_config, getattr(self, "inv_rect", self.play_rect), self.boss_sprites)
            self.inv = None
        else:
            # Regular wave with enemy types
            self.inv = InvaderField(self.rng)
            self.boss_field = None
            
            rows = level_config.get("rows", 5)
            cols = level_config.get("cols", 10)
            speed = level_config.get("speed", 1.0)
            enemy_type = level_config.get("enemy_type", "basic")
            mixed = level_config.get("mixed", False)
            
            field_rect = getattr(self, "inv_rect", self.play_rect)
            
            if mixed and isinstance(enemy_type, list):
                # Mixed enemy types
                self.inv.spawn_wave(field_rect, rows=rows, cols=cols, kind="enemy", hp=1, 
                                   speed_scale=speed, enemy_types=enemy_type)
            else:
                # Single enemy type
                self.inv.spawn_wave(field_rect, rows=rows, cols=cols, kind="enemy", hp=1,
                                   speed_scale=speed, enemy_types=enemy_type)

        # ship
        self.ship_x = self.play_rect.centerx
        self.ship_y = self.play_rect.bottom - (self.SHIP_H + int(self.U * 2))
        self.ship_vx = 0.0
        self.trail = []

        # walls
        self.selected_wall = 0
        self.wall_x = [self.play_rect.centerx for _ in range(self.num_walls)]

        # hp grids
        self.walls_hp = []
        for _ in range(self.num_walls):
            hp_grid = [[0] * OB_W for _ in range(OB_H)]
            for y in range(OB_H):
                for x in range(OB_W):
                    hp_grid[y][x] = self.block_hp if self.obstruction[y][x] else 0
            self.walls_hp.append(hp_grid)

    # ---------------- Layout ----------------
    def _layout(self):
        w, h = self.app.screen.get_size()
        self.def_rect = pg.Rect(PANEL_PAD, PANEL_PAD, w - 2 * PANEL_PAD, h - 2 * PANEL_PAD)

        M = 14
        RIGHT_W = 360
        HUD_H = 120
        GAP = 12
        HUD_Y_OFFSET = 18

        self.right_panel = pg.Rect(
            self.def_rect.right - RIGHT_W - M,
            self.def_rect.y + M,
            RIGHT_W,
            self.def_rect.h - 2 * M
        )

        left_w = self.def_rect.w - RIGHT_W - (M * 3)
        self.left_hud = pg.Rect(
            self.def_rect.x + M,
            self.def_rect.y + M + HUD_Y_OFFSET,
            left_w,
            HUD_H
        )

        self.play_rect = pg.Rect(
            self.def_rect.x + M,
            self.left_hud.bottom + GAP,
            left_w,
            self.def_rect.bottom - M - (self.left_hud.bottom + GAP)
        )

        # invader field rect (compact like Endless)
        INV_MAX_W = 640
        self.inv_rect = self.play_rect.copy()
        if self.inv_rect.w > INV_MAX_W:
            cx = self.inv_rect.centerx
            self.inv_rect.w = INV_MAX_W
            self.inv_rect.centerx = cx

        # unified sizing unit
        SCALE = 1.40
        base = int(min(self.def_rect.w, self.def_rect.h) / 60)
        self.U = max(12, min(18, int(base * SCALE)))

        # enemy size (increased for better visibility)
        self.ENEMY_W = int(self.U * 2.5)  # Increased from 1.8
        self.ENEMY_H = int(self.U * 1.8)  # Increased from 1.3

        # ship size
        self.SHIP_W = int(self.U * 2.8)
        self.SHIP_H = int(self.U * 0.9)
        self.SHIP_MAST_W = max(3, int(self.U * 0.35))
        self.SHIP_MAST_H = int(self.U * 0.7)

        # bullet size
        self.BULLET_W = max(3, int(self.U * 0.25))
        self.BULLET_H = int(self.U * 1.0)

    # ---------------- Input ----------------
    def handle_event(self, ev):
        if ev.type == pg.VIDEORESIZE:
            self._layout()

        # paused -> only pause UI
        if self.paused:
            if ev.type == pg.KEYDOWN and ev.key == pg.K_ESCAPE:
                self._set_paused(False)
                return
            for b in self.pause_btns:
                b.handle(ev)
            return

        if ev.type == pg.KEYDOWN:
            if ev.key == pg.K_ESCAPE:
                self._set_paused(True)
                return

            if self.phase == "place":
                if ev.key == pg.K_a:
                    self.selected_wall = (self.selected_wall - 1) % max(1, self.num_walls)
                if ev.key == pg.K_d:
                    self.selected_wall = (self.selected_wall + 1) % max(1, self.num_walls)

                if ev.key == pg.K_q:
                    self.wall_x[self.selected_wall] -= 24
                if ev.key == pg.K_e:
                    self.wall_x[self.selected_wall] += 24

                if ev.key == pg.K_RETURN:
                    self.phase = "fight"
                return

            # fight
            if ev.key == pg.K_LEFT:
                self.ship_vx = -1
            if ev.key == pg.K_RIGHT:
                self.ship_vx = 1
            if ev.key == pg.K_SPACE:
                self.shoot_held = True
                self._shoot()
            # Dash only if enabled (Level 2+)
            if ev.key in (pg.K_LSHIFT, pg.K_RSHIFT):
                if self.dash_enabled:
                    self._dash()

        if ev.type == pg.KEYUP:
            if self.phase == "fight":
                if ev.key == pg.K_LEFT and self.ship_vx < 0:
                    self.ship_vx = 0
                if ev.key == pg.K_RIGHT and self.ship_vx > 0:
                    self.ship_vx = 0
                if ev.key == pg.K_SPACE:
                    self.shoot_held = False

    def _shoot(self):
        if self.phase != "fight":
            return
        if self.fire_cd > 0:
            return
        cd = max(0.05, 0.25 - 0.04 * (self.fire_rate_lvl - 1))
        
        # Add bullet to appropriate field
        if self.is_boss and self.boss_field:
            self.boss_field.bullets.append(Bullet(self.ship_x, self.ship_y - 18, vy=-BULLET_SPEED, friendly=True, kind="normal"))
        elif self.inv:
            self.inv.bullets.append(Bullet(self.ship_x, self.ship_y - 18, vy=-BULLET_SPEED, friendly=True, kind="normal"))
        
        self.fire_cd = cd

    def _dash(self):
        """Execute a dash in the current movement direction."""
        if self.phase != "fight":
            return
        if self.dash_cd > 0:
            return
        if self.dashing:
            return
        
        # Start dash
        self.dashing = True
        self.dash_timer = self.dash_duration
        self.dash_cd = self.dash_cooldown

    # ---------------- Update ----------------
    def update(self, dt):
        if self.paused:
            return

        # clamp walls by actual wall band size (scaled)
        half = int((260 * self.WALL_SCALE) // 2)
        minx = self.play_rect.left + half
        maxx = self.play_rect.right - half
        for i in range(len(self.wall_x)):
            self.wall_x[i] = max(minx, min(maxx, self.wall_x[i]))

        if self.phase == "place":
            return
        
        # Unwinnable level logic (Level 0)
        if self.unwinnable and self.unwinnable_timer > 0:
            self.unwinnable_timer -= dt
            if self.unwinnable_timer <= 0:
                # Force game over but continue to next level with explanation
                from ..gameplay.level_config import get_level_config
                config = get_level_config(self.stage)
                
                # Show splash_after if it exists, then continue to next level
                if "splash_after" in config:
                    from .splash import SplashScene
                    from .build import BuildScene
                    from .fight import FightScene
                    sd = self.app.save
                    lang = sd.settings.lang
                    splash_text = config["splash_after"].get(lang, config["splash_after"].get("en", ""))
                    
                    # Check if there's a second splash screen
                    if "splash_after_2" in config:
                        # Chain to second splash, which then goes to next level
                        splash_text_2 = config["splash_after_2"].get(lang, config["splash_after_2"].get("en", ""))
                        
                        # Get next level config to determine final destination
                        next_config = get_level_config(self.stage + 1)
                        skip_next_build = next_config.get("skip_build", False)
                        
                        if skip_next_build:
                            final_scene_class = FightScene
                            final_args = {"mode": "story", "stage": self.stage + 1, "wave": 1, "obstruction": None, "tetris_coins": 0}
                        else:
                            final_scene_class = BuildScene
                            final_args = {"mode": "story", "stage": self.stage + 1, "wave": 1}
                        
                        # Create second splash that goes to next level
                        second_splash = SplashScene(self.app, splash_text_2,
                                                   next_scene_class=final_scene_class,
                                                   next_scene_args=final_args)
                        
                        # Create first splash that goes to second splash
                        first_splash = SplashScene(self.app, splash_text,
                                                  next_scene_class=SplashScene,
                                                  next_scene_args={"text": splash_text_2,
                                                                  "next_scene_class": final_scene_class,
                                                                  "next_scene_args": final_args})
                        change_scene(self.app, first_splash)
                    else:
                        # Single splash, then go to next level
                        next_config = get_level_config(self.stage + 1)
                        skip_next_build = next_config.get("skip_build", False)
                        
                        if skip_next_build:
                            next_scene_class = FightScene
                            next_args = {"mode": "story", "stage": self.stage + 1, "wave": 1, "obstruction": None, "tetris_coins": 0}
                        else:
                            next_scene_class = BuildScene
                            next_args = {"mode": "story", "stage": self.stage + 1, "wave": 1}
                        
                        splash_scene = SplashScene(self.app, splash_text,
                                                 next_scene_class=next_scene_class,
                                                 next_scene_args=next_args)
                        change_scene(self.app, splash_scene)
                else:
                    # No splash, go directly to next level
                    next_config = get_level_config(self.stage + 1)
                    skip_next_build = next_config.get("skip_build", False)
                    
                    if skip_next_build:
                        from .fight import FightScene
                        change_scene(self.app, FightScene(self.app), mode="story", stage=self.stage + 1, wave=1,
                                   obstruction=None, tetris_coins=0)
                    else:
                        from .build import BuildScene
                        change_scene(self.app, BuildScene(self.app), mode="story", stage=self.stage + 1, wave=1)
                return

        if self.fire_cd > 0:
            self.fire_cd -= dt
        if self.shoot_held:
            self._shoot()
        
        # Update dash timers
        if self.dash_cd > 0:
            self.dash_cd -= dt
        
        if self.dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.dashing = False
        
        # Apply movement with dash boost
        speed_mult = 3.0 if self.dashing else 1.0
        self.ship_x += (self.ship_vx * SHIP_SPEED * speed_mult) * dt
        self.ship_x = max(self.play_rect.left + 30, min(self.play_rect.right - 30, self.ship_x))

        self.trail.append((self.ship_x, self.ship_y, 0.22))
        self.trail = [(x, y, t - dt) for (x, y, t) in self.trail if t - dt > 0]

        # Update enemies (boss or regular)
        if self.is_boss and self.boss_field:
            self.boss_field.update(dt)
        elif self.inv:
            self.inv.update(dt, self.play_rect)
        
        # Update bricks (falling with gravity)
        if self.drop_bricks_enabled:
            screen_bottom = self.play_rect.bottom
            for brick in list(self.bricks):
                brick.update(dt, screen_bottom)
                
                # Check collision with player
                player_rect = pg.Rect(
                    self.ship_x - self.SHIP_W // 2,
                    self.ship_y - self.SHIP_H // 2,
                    self.SHIP_W,
                    self.SHIP_H
                )
                
                if player_rect.colliderect(brick.get_rect()):
                    self.bricks_collected += 1
                    brick.alive = False
            
            # Remove dead bricks
            self.bricks = [b for b in self.bricks if b.alive]
        
        self._handle_collisions()

        # Check victory/defeat
        if self.is_boss and self.boss_field:
            if self.boss_field.boss and not self.boss_field.boss.alive:
                self._end_wave(success=True)
        elif self.inv:
            # Check if this is a brick collection level
            if self.bricks_required > 0:
                # Victory condition: collect required bricks AND defeat all enemies
                if self.bricks_collected >= self.bricks_required and not self.inv.alive_invaders():
                    self._end_wave(success=True)
            else:
                # Normal victory condition: defeat all enemies
                if not self.inv.alive_invaders():
                    self._end_wave(success=True)
            
            # Defeat condition: enemies reach bottom
            if self.inv.any_reached_bottom(self.play_rect.bottom):
                self._end_wave(success=False)
        if self.lives <= 0:
            self._end_wave(success=False)

    def _end_wave(self, success: bool):
        self.app._run_hearts = self.lives
        self.app._wave_shield_hp = 0
        
        # Special handling for Level 0 (unwinnable tutorial)
        # If we lose Level 0, continue to Level 1 with splash screens
        if self.stage == 0 and not success:
            from ..gameplay.level_config import get_level_config
            config = get_level_config(self.stage)
            
            # Show splash_after if it exists, then continue to next level
            if "splash_after" in config:
                from .splash import SplashScene
                from .build import BuildScene
                from .fight import FightScene
                sd = self.app.save
                lang = sd.settings.lang
                splash_text = config["splash_after"].get(lang, config["splash_after"].get("en", ""))
                
                # Check if there's a second splash screen
                if "splash_after_2" in config:
                    # Chain to second splash, which then goes to next level
                    splash_text_2 = config["splash_after_2"].get(lang, config["splash_after_2"].get("en", ""))
                    
                    # Get next level config to determine final destination
                    next_config = get_level_config(self.stage + 1)
                    skip_next_build = next_config.get("skip_build", False)
                    
                    if skip_next_build:
                        final_scene_class = FightScene
                        final_args = {"mode": "story", "stage": self.stage + 1, "wave": 1, "obstruction": None, "tetris_coins": 0}
                    else:
                        final_scene_class = BuildScene
                        final_args = {"mode": "story", "stage": self.stage + 1, "wave": 1}
                    
                    # Create first splash that goes to second splash
                    first_splash = SplashScene(self.app, splash_text,
                                              next_scene_class=SplashScene,
                                              next_scene_args={"text": splash_text_2,
                                                              "next_scene_class": final_scene_class,
                                                              "next_scene_args": final_args})
                    change_scene(self.app, first_splash)
                else:
                    # Single splash, then go to next level
                    next_config = get_level_config(self.stage + 1)
                    skip_next_build = next_config.get("skip_build", False)
                    
                    if skip_next_build:
                        next_scene_class = FightScene
                        next_args = {"mode": "story", "stage": self.stage + 1, "wave": 1, "obstruction": None, "tetris_coins": 0}
                    else:
                        next_scene_class = BuildScene
                        next_args = {"mode": "story", "stage": self.stage + 1, "wave": 1}
                    
                    splash_scene = SplashScene(self.app, splash_text,
                                             next_scene_class=next_scene_class,
                                             next_scene_args=next_args)
                    change_scene(self.app, splash_scene)
                return
        
        # Check if we should show splash_after for successful completion
        if success:
            from ..gameplay.level_config import get_level_config
            config = get_level_config(self.stage)
            
            if "splash_after" in config:
                from .splash import SplashScene
                from .hub import WaveHubScene
                sd = self.app.save
                lang = sd.settings.lang
                splash_text = config["splash_after"].get(lang, config["splash_after"].get("en", ""))
                
                # Show splash, then go to hub
                splash_scene = SplashScene(self.app, splash_text,
                                         next_scene_class=WaveHubScene,
                                         next_scene_args={
                                             "mode": self.mode,
                                             "stage": self.stage,
                                             "wave": self.wave,
                                             "success": success,
                                             "score": self.score,
                                             "tetris_coins": self.tetris_coins
                                         })
                change_scene(self.app, splash_scene)
                return
        
        # Normal flow for all other levels (no splash or failure)
        from .hub import WaveHubScene
        change_scene(self.app, WaveHubScene(self.app),
                     mode=self.mode, stage=self.stage, wave=self.wave,
                     success=success, score=self.score, tetris_coins=self.tetris_coins)

    # ---------------- Collisions ----------------
    def _wall_band_rect(self, cx: int) -> pg.Rect:
        w = int(260 * self.WALL_SCALE)
        h = int(120 * self.WALL_SCALE)

        # higher so doesn't touch ship
        top = self.play_rect.bottom - int(self.U * 11.0) - (h // 2)

        band = pg.Rect(0, 0, w, h)
        band.centerx = int(cx)
        band.y = int(top)

        # clamp inside play rect
        if band.left < self.play_rect.left:
            band.left = self.play_rect.left
        if band.right > self.play_rect.right:
            band.right = self.play_rect.right
        return band

    def _obstacle_hit_any(self, bx, by) -> bool:
        for wi in range(self.num_walls):
            band = self._wall_band_rect(self.wall_x[wi])
            if not band.collidepoint(bx, by):
                continue

            lx = int((bx - band.x) / max(1, band.w) * OB_W)
            ly = int((by - band.y) / max(1, band.h) * OB_H)
            lx = max(0, min(OB_W - 1, lx))
            ly = max(0, min(OB_H - 1, ly))

            if self.walls_hp[wi][ly][lx] > 0:
                self.walls_hp[wi][ly][lx] -= 1
                return True
        return False

    def _check_enemy_wall_collisions(self):
        """Check if any enemies are touching walls and destroy wall blocks on contact."""
        if not self.inv:
            return
        
        for enemy in self.inv.alive_invaders():
            # Check collision with each wall
            for wi in range(self.num_walls):
                band = self._wall_band_rect(self.wall_x[wi])
                
                # Create enemy hitbox (slightly smaller than visual size)
                enemy_rect = pg.Rect(
                    int(enemy.x - self.ENEMY_W // 2 + 2),
                    int(enemy.y - self.ENEMY_H // 2 + 2),
                    self.ENEMY_W - 4,
                    self.ENEMY_H - 4
                )
                
                # Check if enemy overlaps with wall band
                if enemy_rect.colliderect(band):
                    # Find which wall blocks to destroy
                    # Check multiple points on the enemy for more accurate collision
                    points_to_check = [
                        (enemy.x, enemy.y),  # center
                        (enemy.x - self.ENEMY_W // 3, enemy.y),  # left
                        (enemy.x + self.ENEMY_W // 3, enemy.y),  # right
                        (enemy.x, enemy.y + self.ENEMY_H // 3),  # bottom
                    ]
                    
                    for px, py in points_to_check:
                        if band.collidepoint(px, py):
                            lx = int((px - band.x) / max(1, band.w) * OB_W)
                            ly = int((py - band.y) / max(1, band.h) * OB_H)
                            lx = max(0, min(OB_W - 1, lx))
                            ly = max(0, min(OB_H - 1, ly))
                            
                            # Destroy the wall block
                            if self.walls_hp[wi][ly][lx] > 0:
                                self.walls_hp[wi][ly][lx] = 0

    def _handle_collisions(self):
        # Check enemy-wall collisions (enemies destroy walls on contact)
        self._check_enemy_wall_collisions()
        
        # Get bullets from appropriate source
        bullets = self.boss_field.bullets if (self.is_boss and self.boss_field) else (self.inv.bullets if self.inv else [])
        
        for b in list(bullets):
            if b.friendly:
                # Player bullet hitting enemies
                if self.is_boss and self.boss_field:
                    # Hit boss
                    if self.boss_field.hit_boss(b.x, b.y):
                        b.alive = False
                        self.score += 10
                elif self.inv:
                    # Hit regular enemies
                    killed_positions = self.inv.hit_invaders_with_positions(b, radius=12)
                    if len(killed_positions) > 0:
                        self.score += 10 * len(killed_positions)
                        
                        # Spawn bricks at killed enemy positions
                        if self.drop_bricks_enabled:
                            from ..gameplay.brick import Brick
                            for pos in killed_positions:
                                brick = Brick(pos[0], pos[1])
                                self.bricks.append(brick)
            else:
                # Enemy bullet hitting player/walls
                if self._obstacle_hit_any(b.x, b.y):
                    b.alive = False
                    continue
                
                # Shield check
                if self.shield_hp > 0:
                    ship_r = pg.Rect(self.ship_x - self.SHIP_W//2, self.ship_y - self.SHIP_H//2, 
                                    self.SHIP_W, self.SHIP_H)
                    if ship_r.collidepoint(b.x, b.y):
                        self.shield_hp -= 1
                        self.app._wave_shield_hp = self.shield_hp
                        b.alive = False
                        continue
                
                # Player hit
                ship_r = pg.Rect(self.ship_x - self.SHIP_W//2, self.ship_y - self.SHIP_H//2, 
                                self.SHIP_W, self.SHIP_H)
                if ship_r.collidepoint(b.x, b.y):
                    self.lives -= 1
                    self.app._run_hearts = self.lives
                    b.alive = False
        
        # Remove dead bullets
        if self.is_boss and self.boss_field:
            self.boss_field.bullets = [b for b in self.boss_field.bullets if b.alive]
        elif self.inv:
            self.inv.bullets = [b for b in self.inv.bullets if b.alive]
    # ---------------- Draw ----------------
    def draw(self, surf):
        app = self.app
        colors, fonts = app.colors, app.fonts
        lang = app.save.settings.lang
        t = TEXT[lang]

        self.draw_background(surf, colors)
        draw_panel(surf, self.def_rect, colors,
                   title=("Defense" if lang == "en" else "Одбрана"),
                   title_font=fonts.ui_bold)

        draw_panel(surf, self.left_hud, colors, title="", title_font=fonts.ui_bold)
        draw_panel(surf, self.right_panel, colors,
                   title=("Upgrades" if lang == "en" else "Надградби"),
                   title_font=fonts.ui_bold)

        # left hud text
        hx, hy = self.left_hud.x + 16, self.left_hud.y + 14
        
        # Draw hearts as icons
        def draw_heart(surf, x, y, size=16):
            """Draw a pixel art heart icon"""
            # Heart color (bright red)
            heart_color = (255, 48, 48)
            outline_color = (0, 0, 0)
            highlight_color = (255, 255, 255)
            
            # Scale for heart shape (simplified pixel heart)
            s = size // 16
            
            # Draw filled heart (simpler approach with rectangles)
            # Top bumps
            pg.draw.rect(surf, heart_color, (x + 4*s, y + 4*s, 3*s, 2*s))
            pg.draw.rect(surf, heart_color, (x + 9*s, y + 4*s, 3*s, 2*s))
            # Middle section
            pg.draw.rect(surf, heart_color, (x + 3*s, y + 6*s, 10*s, 4*s))
            # Lower triangle approximation
            for i in range(4):
                w = 10*s - i*2*s
                pg.draw.rect(surf, heart_color, (x + 3*s + i*s, y + 10*s + i*s, w, s))
            
            # Add white highlight (small dot)
            pg.draw.rect(surf, highlight_color, (x + 10*s, y + 5*s, s, s))
            
        # Draw "Lives: " text followed by heart icons
        lives_label = "Lives: " if lang == "en" else "Срца: "
        lives_text_surf = fonts.ui_bold.render(lives_label, True, colors["text"])
        surf.blit(lives_text_surf, (hx, hy))
        
        # Draw hearts horizontally after the text
        heart_x = hx + lives_text_surf.get_width() + 8
        heart_size = 16
        heart_spacing = 20
        for i in range(max(0, self.lives)):
            draw_heart(surf, heart_x + i * heart_spacing, hy + 2, heart_size)
        surf.blit(fonts.ui.render(f"{t['hud_score']}: {self.score}", True, colors["text"]), (hx, hy + 24))
        surf.blit(fonts.ui.render(f"{t['hud_wave']}: {self.stage}/15", True, colors["muted"]), (hx, hy + 44))
        
        # Show brick counter if brick dropping is enabled
        if self.drop_bricks_enabled:
            brick_label = "Bricks" if lang == "en" else "Тули"
            if self.bricks_required > 0:
                # Show progress towards goal
                surf.blit(fonts.ui.render(f"{brick_label}: {self.bricks_collected}/{self.bricks_required}", True, colors["accent"]), (hx, hy + 64))
            else:
                # Just show count
                surf.blit(fonts.ui.render(f"{brick_label}: {self.bricks_collected}", True, colors["accent"]), (hx, hy + 64))
        
        # Dash cooldown bar (only show if dash is enabled)
        if self.dash_enabled:
            dash_label = "Dash" if lang == "en" else "Dash"
            surf.blit(fonts.ui.render(dash_label, True, colors["text"]), (hx, hy + 64))
            
            # Draw dash cooldown bar
            bar_x = hx
            bar_y = hy + 82
            bar_w = 140
            bar_h = 8
            
            # Background
            pg.draw.rect(surf, colors["panel2"], (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            
            # Fill based on cooldown
            if self.dash_cd <= 0:
                # Ready - full green bar
                pg.draw.rect(surf, colors["good"], (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            else:
                # Charging - show progress
                progress = 1.0 - (self.dash_cd / self.dash_cooldown)
                fill_w = int(bar_w * progress)
                if fill_w > 0:
                    pg.draw.rect(surf, colors["accent"], (bar_x, bar_y, fill_w, bar_h), border_radius=4)
            
            # Border
            pg.draw.rect(surf, colors["line"], (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=4)

        # right hud text
        rx, ry = self.right_panel.x + 16, self.right_panel.y + 60
        surf.blit(fonts.ui.render(f"{'Walls' if lang=='en' else 'Ѕидови'}: {self.num_walls}/5", True, colors["text"]), (rx, ry)); ry += 24
        surf.blit(fonts.ui.render(f"Block HP: {self.block_hp}/5", True, colors["text"]), (rx, ry)); ry += 24
        surf.blit(fonts.ui.render(f"Fire rate lvl: {self.fire_rate_lvl}", True, colors["text"]), (rx, ry)); ry += 24
        surf.blit(fonts.ui.render(f"{t['power_shield']}: {self.shield_hp}", True, colors["text"]), (rx, ry)); ry += 30
        
        # Controls in right panel
        if self.phase == "place":
            instr = ("A/D select"
                     if lang == "en" else "A/D избери")
            instr2 = ("Q/E move"
                      if lang == "en" else "Q/E помести")
            instr3 = ("ENTER continue"
                      if lang == "en" else "ENTER продолжи")
        else:
            instr = ("←/→ move"
                     if lang == "en" else "←/→ движи")
            if self.dash_enabled:
                instr2 = ("SHIFT dash"
                          if lang == "en" else "SHIFT dash")
            else:
                instr2 = None  # Don't show dash instruction before level 8
            instr3 = ("SPACE shoot"
                      if lang == "en" else "SPACE пука")
        
        surf.blit(fonts.ui.render(instr, True, colors["muted"]), (rx, ry)); ry += 20
        if instr2:  # Only render instr2 if it exists
            surf.blit(fonts.ui.render(instr2, True, colors["muted"]), (rx, ry)); ry += 20
        surf.blit(fonts.ui.render(instr3, True, colors["muted"]), (rx, ry))

        # clip to play rect
        old_clip = surf.get_clip()
        surf.set_clip(self.play_rect)

        # walls
        for wi in range(self.num_walls):
            band = self._wall_band_rect(self.wall_x[wi])
            cw, ch = band.w / OB_W, band.h / OB_H

            if self.phase == "place" and wi == self.selected_wall:
                pg.draw.rect(surf, colors["cyan"], band, width=3, border_radius=16)

            for y in range(OB_H):
                for x in range(OB_W):
                    hp = self.walls_hp[wi][y][x]
                    if hp > 0:
                        r = pg.Rect(band.x + x * cw + 1, band.y + y * ch + 1, cw - 2, ch - 2)
                        pg.draw.rect(surf, colors["accent"], r, border_radius=4)

        # Draw enemies or boss
        if self.is_boss and self.boss_field and self.boss_field.boss:
            # Draw boss
            boss = self.boss_field.boss
            if boss.alive:
                # Use custom boss size from level config if specified, otherwise default to 120
                boss_size = self.level_config.get("boss_size", 120)
                
                # Check if boss has a sprite
                if boss.sprite:
                    # Render animated sprite
                    frame = boss.sprite.get_current_frame()
                    # Scale sprite to boss size
                    scaled_frame = pg.transform.scale(frame, (boss_size, boss_size))
                    frame_rect = scaled_frame.get_rect(center=(int(boss.x), int(boss.y)))
                    surf.blit(scaled_frame, frame_rect)
                else:
                    # Fall back to default rectangle rendering
                    r = pg.Rect(int(boss.x - boss_size // 2), int(boss.y - boss_size // 2), boss_size, boss_size)
                    pg.draw.rect(surf, (255, 100, 100), r, border_radius=12)
                    # Boss eyes
                    eye_size = 8
                    pg.draw.rect(surf, colors["bg"],
                               pg.Rect(r.x + 12, r.y + 15, eye_size, eye_size), border_radius=2)
                    pg.draw.rect(surf, colors["bg"],
                               pg.Rect(r.right - 20, r.y + 15, eye_size, eye_size), border_radius=2)
        elif self.inv:
            # Draw regular invaders with sprites or fallback to colored rectangles
            for inv in self.inv.alive_invaders():
                # Calculate enemy rectangle (needed for HP bar regardless of sprite/no sprite)
                r = pg.Rect(int(inv.x - self.ENEMY_W // 2), int(inv.y - self.ENEMY_H // 2), self.ENEMY_W, self.ENEMY_H)
                
                # Try to use sprite if available
                if inv.enemy_type in self.enemy_sprites:
                    sprite = self.enemy_sprites[inv.enemy_type]
                    # Scale sprite to enemy size
                    scaled_sprite = pg.transform.scale(sprite, (self.ENEMY_W, self.ENEMY_H))
                    sprite_rect = scaled_sprite.get_rect(center=(int(inv.x), int(inv.y)))
                    surf.blit(scaled_sprite, sprite_rect)
                else:
                    # Fallback to colored rectangle rendering
                    enemy_stats = get_enemy_type_stats(inv.enemy_type)
                    enemy_color = enemy_stats.get("color", (255, 255, 100))
                    
                    pg.draw.rect(surf, enemy_color, r, border_radius=max(4, self.U // 2))
                    
                    # Eyes
                    eye = max(2, self.U // 5)
                    pg.draw.rect(surf, colors["bg"],
                               pg.Rect(r.x + int(self.ENEMY_W * 0.28), r.y + int(self.ENEMY_H * 0.30), eye, eye),
                               border_radius=2)
                    pg.draw.rect(surf, colors["bg"],
                               pg.Rect(r.right - int(self.ENEMY_W * 0.42), r.y + int(self.ENEMY_H * 0.30), eye, eye),
                               border_radius=2)
                
                # HP indicator for armored/elite enemies
                if inv.max_hp > 1:
                    hp_bar_w = self.ENEMY_W - 4
                    hp_bar_h = 3
                    hp_ratio = inv.hp / inv.max_hp
                    hp_fill = int(hp_bar_w * hp_ratio)
                    hp_bar_y = r.bottom + 2
                    pg.draw.rect(surf, (60, 60, 60), pg.Rect(r.x + 2, hp_bar_y, hp_bar_w, hp_bar_h))
                    if hp_fill > 0:
                        pg.draw.rect(surf, (100, 255, 100), pg.Rect(r.x + 2, hp_bar_y, hp_fill, hp_bar_h))
        
        # bullets
        bullets = self.boss_field.bullets if (self.is_boss and self.boss_field) else (self.inv.bullets if self.inv else [])
        for b in bullets:
            if b.friendly:
                r = pg.Rect(int(b.x - self.BULLET_W // 2), int(b.y - self.BULLET_H // 2), self.BULLET_W, self.BULLET_H)
                pg.draw.rect(surf, colors["cyan"], r, border_radius=2)
            else:
                r = pg.Rect(int(b.x - self.BULLET_W // 2), int(b.y - self.BULLET_H // 2), self.BULLET_W, self.BULLET_H)
                pg.draw.rect(surf, colors["bad"], r, border_radius=max(2, self.BULLET_W // 2))
        
        # Draw falling bricks
        if self.drop_bricks_enabled:
            for brick in self.bricks:
                brick.draw(surf, colors)

        # ship trail + ship skin (same as game.py)
        trail_id = self.app.save.cosmetics.get("trail", 0) if isinstance(self.app.save.cosmetics, dict) else 0
        try:
            trail_id = int(trail_id)
        except Exception:
            trail_id = 0
        trail_id = max(0, min(trail_id, len(TRAILS) - 1))
        trail_color = TRAILS[trail_id]["color"]

        life = 0.22  # must match update() trail lifetime
        for tx, ty, tleft in self.trail:
            a = int(180 * (tleft / life))
            s = pg.Surface((10, 10), pg.SRCALPHA)
            pg.draw.circle(s, (*trail_color, a), (5, 5), 4)
            surf.blit(s, (tx - 5, ty - 5))

        skin_id = self.app.save.cosmetics.get("ship_skin", 0) if isinstance(self.app.save.cosmetics, dict) else 0
        try:
            skin_id = int(skin_id)
        except Exception:
            skin_id = 0
        skin_id = max(0, min(skin_id, len(SHIP_SKINS) - 1))
        skin = SHIP_SKINS[skin_id]

        x, y = int(self.ship_x), int(self.ship_y)
        pg.draw.rect(surf, skin["shade"], pg.Rect(x - 12, y - 6, 24, 10), border_radius=4)
        pg.draw.rect(surf, skin["main"], pg.Rect(x - 18, y + 2, 36, 10), border_radius=4)
        pg.draw.rect(surf, self.app.colors["text"], pg.Rect(x - 2, y - 12, 4, 6), border_radius=2)

        # restore clip ALWAYS
        surf.set_clip(old_clip)
        
        # Boss health bar (drawn outside clip)
        if self.is_boss and self.boss_field and self.boss_field.boss and self.boss_field.boss.alive:
            self.boss_field.draw_health_bar(surf, fonts, colors)

        # unified pause overlay + menu
        if self.paused:
            self._draw_pause(surf)
