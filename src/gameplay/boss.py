from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import random
import math
import pygame as pg

@dataclass
class Boss:
    """Boss enemy with health, phases, and special attacks."""
    x: float
    y: float
    hp: int
    max_hp: int
    name: str
    pattern: str  # sweep, orbital, zigzag, teleport, multi_phase
    phase: int = 0
    alive: bool = True
    
    # Sprite support
    sprite_name: str = ""  # Name of sprite to use (empty = use default rendering)
    sprite: object = None  # AnimatedSprite object (set at runtime)
    
    # Movement state
    direction: int = 1
    angle: float = 0.0
    direction_x: float = 1.0
    direction_y: float = 1.0
    
    # Attack state
    shoot_timer: float = 0.0
    shoot_interval: float = 0.4  # Was 0.8 - shoots 50% faster
    minion_timer: float = 0.0
    minion_interval: float = 10.0
    
    # Special state
    teleport_timer: float = 4.0  # Was 8.0 - teleports 50% faster
    invulnerable: bool = False
    charging: bool = False
    charge_duration: float = 0.0

class BossField:
    """Manages boss fights with minions and special mechanics."""
    
    def __init__(self, rng: random.Random, boss_config: dict, field_rect: pg.Rect, boss_sprites: dict = None):
        self.rng = rng
        self.boss: Optional[Boss] = None
        self.minions: List = []  # Will use Invader from invaders.py
        self.bullets: List = []
        self.field_rect = field_rect
        
        # Create boss
        center_x = field_rect.centerx
        center_y = field_rect.top + 100
        
        sprite_name = boss_config.get("boss_sprite", "")
        
        self.boss = Boss(
            x=center_x,
            y=center_y,
            hp=boss_config.get("boss_hp", 50),
            max_hp=boss_config.get("boss_hp", 50),
            name=boss_config.get("boss_name", "boss"),
            pattern=boss_config.get("boss_pattern", "sweep"),
            sprite_name=sprite_name
        )
        
        # Assign sprite if available
        if boss_sprites and sprite_name and sprite_name in boss_sprites:
            self.boss.sprite = boss_sprites[sprite_name]
        
        self.minion_type = boss_config.get("minion_type", "basic")
        self.boss.minion_interval = boss_config.get("minion_interval", 10.0)
        
    def update(self, dt: float):
        """Update boss movement, attacks, and minions."""
        if not self.boss or not self.boss.alive:
            return
        
        # Update sprite animation
        if self.boss.sprite:
            self.boss.sprite.update(dt)
        
        # Update movement pattern
        self._update_movement(dt)
        
        # Update attacks
        self._update_attacks(dt)
        
        # Update minion spawning
        self._update_minions(dt)
        
        # Update bullets
        for b in list(self.bullets):
            b.y += b.vy * dt
            if b.y < self.field_rect.top - 50 or b.y > self.field_rect.bottom + 80:
                self.bullets.remove(b)
        
        # Check phase transitions
        self._check_phase_transition()
    
    def _update_movement(self, dt: float):
        """Update boss movement based on pattern."""
        if self.boss.invulnerable or self.boss.charging:
            return
        
        pattern = self.boss.pattern
        
        if pattern == "sweep":
            # Horizontal sweep - MUCH faster
            self.boss.x += self.boss.direction * 200 * dt  # Was 120 - 67% faster
            if self.boss.x >= self.field_rect.right - 100:
                self.boss.direction = -1
            elif self.boss.x <= self.field_rect.left + 100:
                self.boss.direction = 1
        
        elif pattern == "orbital":
            # Circular movement - MUCH faster and tighter
            radius = 120  # Was 150 - tighter circle
            center_x = self.field_rect.centerx
            center_y = self.field_rect.top + 150
            self.boss.angle += 2.2 * dt  # Was 1.2 - 83% faster rotation
            self.boss.x = center_x + math.cos(self.boss.angle) * radius
            self.boss.y = center_y + math.sin(self.boss.angle) * radius
        
        elif pattern == "zigzag":
            # Diagonal zigzag - MUCH faster
            self.boss.x += self.boss.direction_x * 180 * dt  # Was 100 - 80% faster
            self.boss.y += self.boss.direction_y * 120 * dt  # Was 60 - 100% faster
            
            if self.boss.x >= self.field_rect.right - 100 or self.boss.x <= self.field_rect.left + 100:
                self.boss.direction_x *= -1
            if self.boss.y >= self.field_rect.top + 250 or self.boss.y <= self.field_rect.top + 80:
                self.boss.direction_y *= -1
        
        elif pattern == "teleport":
            # Teleport pattern - MUCH faster
            self.boss.teleport_timer -= dt
            if self.boss.teleport_timer <= 0:
                # Teleport to random position - wider range
                self.boss.invulnerable = True
                self.boss.x = self.rng.randint(self.field_rect.left + 100, self.field_rect.right - 100)
                self.boss.y = self.rng.randint(self.field_rect.top + 80, self.field_rect.top + 300)  # Expanded from 200 to 300
                self.boss.teleport_timer = 4.0  # Was 8.0 - teleports 50% faster
                # Brief invulnerability
                self.boss.invulnerable = False
        
        elif pattern == "multi_phase":
            # Changes based on phase - all MUCH faster
            if self.boss.phase == 0:
                # Phase 1: Orbital - faster
                radius = 120  # Was 140 - tighter
                center_x = self.field_rect.centerx
                center_y = self.field_rect.top + 140
                self.boss.angle += 1.5 * dt  # Was 0.8 - 88% faster
                self.boss.x = center_x + math.cos(self.boss.angle) * radius
                self.boss.y = center_y + math.sin(self.boss.angle) * radius
            elif self.boss.phase == 1:
                # Phase 2: Zigzag (MUCH faster)
                self.boss.x += self.boss.direction_x * 220 * dt  # Was 140 - 57% faster
                self.boss.y += self.boss.direction_y * 140 * dt  # Was 80 - 75% faster
                if self.boss.x >= self.field_rect.right - 100 or self.boss.x <= self.field_rect.left + 100:
                    self.boss.direction_x *= -1
                if self.boss.y >= self.field_rect.top + 250 or self.boss.y <= self.field_rect.top + 80:
                    self.boss.direction_y *= -1
            else:
                # Phase 3: Erratic teleport - MUCH faster and wider range
                self.boss.teleport_timer -= dt
                if self.boss.teleport_timer <= 0:
                    self.boss.x = self.rng.randint(self.field_rect.left + 100, self.field_rect.right - 100)
                    self.boss.y = self.rng.randint(self.field_rect.top + 80, self.field_rect.top + 350)  # Expanded from 200 to 350
                    self.boss.teleport_timer = 2.5  # Was 5.0 - teleports 50% faster
    
    def _update_attacks(self, dt: float):
        """Update boss shooting patterns - MUCH more aggressive."""
        from .invaders import Bullet
        
        self.boss.shoot_timer -= dt
        if self.boss.shoot_timer <= 0:
            # Shoot based on phase - MORE BULLETS
            if self.boss.pattern == "multi_phase":
                if self.boss.phase == 0:
                    # Phase 1: Spread shot (12 bullets - was 9)
                    for i in range(12):
                        angle = -math.pi/3 + (i * math.pi/16)
                        vx = math.sin(angle) * 220
                        vy = math.cos(angle) * 220
                        self.bullets.append(Bullet(self.boss.x + vx*0.1, self.boss.y, vy=vy, friendly=False))
                    self.boss.shoot_timer = 0.4  # Was 0.8 - shoots 50% faster
                elif self.boss.phase == 1:
                    # Phase 2: Rapid fire (18 bullets in spiral - was 12)
                    for i in range(18):
                        angle = (i * math.pi / 9) + self.boss.angle
                        vx = math.sin(angle) * 200
                        vy = math.cos(angle) * 200 + 120
                        self.bullets.append(Bullet(self.boss.x, self.boss.y, vy=vy, friendly=False))
                    self.boss.shoot_timer = 0.35  # Was 0.7 - shoots 50% faster
                else:
                    # Phase 3: Bullet hell (24 bullets in circle - was 15)
                    for i in range(24):
                        angle = (i * 2 * math.pi / 24)
                        vx = math.sin(angle) * 170
                        vy = math.cos(angle) * 170 + 140
                        self.bullets.append(Bullet(self.boss.x, self.boss.y, vy=vy, friendly=False))
                    self.boss.shoot_timer = 0.3  # Was 0.6 - shoots 50% faster
            else:
                # Standard spread shot - MORE BULLETS
                num_bullets = 5 if self.boss.phase == 0 else 8  # Was 3 or 5
                for i in range(num_bullets):
                    offset = (i - num_bullets//2) * 25
                    self.bullets.append(Bullet(self.boss.x + offset, self.boss.y + 20, vy=+300, friendly=False))  # Was 250
                self.boss.shoot_timer = self.boss.shoot_interval
    
    def _update_minions(self, dt: float):
        """Spawn minions periodically."""
        self.boss.minion_timer -= dt
        if self.boss.minion_timer <= 0:
            # Spawn minions (handled in fight.py)
            self.boss.minion_timer = self.boss.minion_interval
    
    def _check_phase_transition(self):
        """Check if boss should transition to next phase."""
        if self.boss.pattern != "multi_phase":
            return
        
        hp_ratio = self.boss.hp / self.boss.max_hp
        
        if hp_ratio <= 0.33 and self.boss.phase < 2:
            self.boss.phase = 2
            self.boss.shoot_interval = 0.3  # Was 0.6 - shoots 50% faster
        elif hp_ratio <= 0.66 and self.boss.phase < 1:
            self.boss.phase = 1
            self.boss.shoot_interval = 0.35  # Was 0.7 - shoots 50% faster
    
    def hit_boss(self, bullet_x: float, bullet_y: float) -> bool:
        """Check if bullet hits boss."""
        if not self.boss or not self.boss.alive or self.boss.invulnerable:
            return False
        
        # Simple circle collision (boss is larger)
        dist = math.sqrt((self.boss.x - bullet_x)**2 + (self.boss.y - bullet_y)**2)
        if dist <= 40:  # Boss hitbox radius
            self.boss.hp -= 1
            
            # Check if boss is dead
            if self.boss.hp <= 0:
                self.boss.alive = False
            
            return True
        return False
    
    def draw_health_bar(self, surf: pg.Surface, fonts, colors):
        """Draw boss health bar at top of screen."""
        if not self.boss or not self.boss.alive:
            return
        
        # Position at top center
        bar_w = 400
        bar_h = 24
        x = surf.get_width() // 2 - bar_w // 2
        y = 20
        
        # Background
        bg_rect = pg.Rect(x, y, bar_w, bar_h)
        pg.draw.rect(surf, (40, 40, 40), bg_rect, border_radius=12)
        
        # Health fill
        hp_ratio = max(0, self.boss.hp / self.boss.max_hp)
        fill_w = int(bar_w * hp_ratio)
        
        # Color based on HP
        if hp_ratio > 0.66:
            color = (100, 255, 100)
        elif hp_ratio > 0.33:
            color = (255, 255, 100)
        else:
            color = (255, 100, 100)
        
        if fill_w > 0:
            fill_rect = pg.Rect(x, y, fill_w, bar_h)
            pg.draw.rect(surf, color, fill_rect, border_radius=12)
        
        # Border
        pg.draw.rect(surf, (255, 255, 255), bg_rect, width=3, border_radius=12)
        
        # HP text
        hp_text = f"{self.boss.hp} / {self.boss.max_hp}"
        text_surf = fonts.ui_bold.render(hp_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(x + bar_w//2, y + bar_h//2))
        surf.blit(text_surf, text_rect)
