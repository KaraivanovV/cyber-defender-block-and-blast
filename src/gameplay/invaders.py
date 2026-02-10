from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import random
import pygame as pg

@dataclass
class Bullet:
    x: float
    y: float
    vy: float
    friendly: bool
    kind: str = "normal"  # normal | piercing
    alive: bool = True

@dataclass
class Invader:
    x: float
    y: float
    kind: str
    hp: int = 1
    max_hp: int = 1
    alive: bool = True
    enemy_type: str = "basic"

@dataclass
class Debuff:
    kind: str  # "popup" | "lag"
    time_left: float

class InvaderField:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.invaders: List[Invader] = []
        self.bullets: List[Bullet] = []
        self.dir = 1
        self.step_timer = 0.0
        self.step_interval = 0.35  # Was 0.58 - moves 40% more frequently
        self.drop_amount = 32.0  # Was 18.0 - drops 78% faster
        self.shoot_timer = 0.0
        self.shoot_interval = 0.65  # Was 1.15 - shoots 43% more frequently
        self.speed_scale = 1.0
        self.slow_time = 0.0

        self.debuffs: List[Debuff] = []
        self.pop_fog = 0.0  # 0..1
        self.lag = 0.0      # 0..1

        self.columns = 10
        self.rows = 5

    def spawn_wave(self, rect: pg.Rect, rows: int, cols: int, kind: str, hp: int, speed_scale: float, enemy_types=None):
        """Spawn a wave of invaders. enemy_types can be a single type or list of types per row."""
        self.invaders.clear()
        self.bullets.clear()
        self.debuffs.clear()
        self.pop_fog = 0.0
        self.lag = 0.0
        self.rows, self.columns = rows, cols
        self.dir = 1
        self.speed_scale = speed_scale
        margin = 50
        spacing_x = (rect.w - 2*margin) / max(1, cols)
        spacing_y = 42
        
        for r in range(rows):
            # Determine enemy type for this row
            if enemy_types is None:
                enemy_type = "basic"
                row_hp = hp
            elif isinstance(enemy_types, list):
                enemy_type = enemy_types[r] if r < len(enemy_types) else "basic"
                # Get HP from enemy type
                from .level_config import get_enemy_type_stats
                stats = get_enemy_type_stats(enemy_type)
                row_hp = stats["hp"]
            else:
                enemy_type = enemy_types
                from .level_config import get_enemy_type_stats
                stats = get_enemy_type_stats(enemy_type)
                row_hp = stats["hp"]
            
            for c in range(cols):
                x = rect.x + margin + c*spacing_x
                y = rect.y + 40 + r*spacing_y
                self.invaders.append(Invader(x=x, y=y, kind=kind, hp=row_hp, max_hp=row_hp, enemy_type=enemy_type))
        
        # Adjust intervals based on speed scale - make them MUCH faster
        self.step_interval = max(0.12, 0.35 / speed_scale)  # Was max(0.22, 0.58 / speed_scale)
        self.shoot_interval = max(0.20, 0.65 / speed_scale)  # Was max(0.35, 1.15 / speed_scale)

    def alive_invaders(self) -> List[Invader]:
        return [i for i in self.invaders if i.alive]

    def any_reached_bottom(self, bottom_y: float) -> bool:
        for i in self.alive_invaders():
            if i.y >= bottom_y - 90:
                return True
        return False

    def add_debuff(self, kind: str, duration: float):
        self.debuffs.append(Debuff(kind, duration))

    def update_debuffs(self, dt: float):
        self.pop_fog = 0.0
        self.lag = 0.0
        for d in list(self.debuffs):
            d.time_left -= dt
            if d.time_left <= 0:
                self.debuffs.remove(d)
                continue
            if d.kind == "popup":
                self.pop_fog = min(1.0, self.pop_fog + 0.8)
            if d.kind == "lag":
                self.lag = min(1.0, self.lag + 0.9)

    def update(self, dt: float, field_rect: pg.Rect):
        if self.slow_time > 0:
            self.slow_time -= dt
        slow_mul = 0.55 if self.slow_time > 0 else 1.0

        self.update_debuffs(dt)

        # Move invaders in discrete steps for retro feel
        self.step_timer += dt * slow_mul
        if self.step_timer >= self.step_interval:
            self.step_timer = 0.0
            alive = self.alive_invaders()
            if alive:
                # find edges
                left = min(i.x for i in alive)
                right = max(i.x for i in alive)
                if right >= field_rect.right - 40 and self.dir == 1:
                    self.dir = -1
                    for i in alive: i.y += self.drop_amount
                elif left <= field_rect.left + 40 and self.dir == -1:
                    self.dir = 1
                    for i in alive: i.y += self.drop_amount
                else:
                    for i in alive:
                        i.x += 28 * self.dir  # Was 18 - moves 56% faster horizontally

        # Enemy shooting - apply enemy type shoot multiplier
        self.shoot_timer += dt * slow_mul
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0.0
            alive = self.alive_invaders()
            if alive:
                shooter = self.rng.choice(alive)
                # Shoot with speed multiplier
                self.bullets.append(Bullet(shooter.x, shooter.y+10, vy=+320*self.speed_scale, friendly=False, kind="normal"))  # Was 260

        # Bullets move
        for b in list(self.bullets):
            b.y += b.vy * dt
            if b.y < field_rect.top - 50 or b.y > field_rect.bottom + 80:
                self.bullets.remove(b)

    def apply_column_bomb(self, field_rect: pg.Rect, x: float) -> int:
        # Clears a column of invaders near x
        killed = 0
        for i in self.alive_invaders():
            if abs(i.x - x) <= 24:
                i.alive = False
                killed += 1
        return killed

    def hit_invaders(self, bullet: Bullet, radius: float = 10.0) -> int:
        killed = 0
        for i in self.alive_invaders():
            if abs(i.x - bullet.x) <= 18 and abs(i.y - bullet.y) <= 18:
                i.hp -= 1
                if i.hp <= 0:
                    i.alive = False
                    killed += 1
                if bullet.kind != "piercing":
                    bullet.alive = False
                break
        return killed
    
    def hit_invaders_with_positions(self, bullet: Bullet, radius: float = 10.0) -> List[Tuple[float, float]]:
        """Hit invaders and return positions of killed enemies."""
        killed_positions = []
        for i in self.alive_invaders():
            if abs(i.x - bullet.x) <= 18 and abs(i.y - bullet.y) <= 18:
                i.hp -= 1
                if i.hp <= 0:
                    i.alive = False
                    killed_positions.append((i.x, i.y))
                if bullet.kind != "piercing":
                    bullet.alive = False
                break
        return killed_positions
