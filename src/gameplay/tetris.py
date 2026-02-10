from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import random

from ..constants import GRID_W, GRID_H

# Tetromino shapes as 4x4 matrices in rotation states
# 1 = filled, 0 = empty
TETROMINOES = {
    "I": [
        ["....",
         "####",
         "....",
         "...."],
        ["..#.",
         "..#.",
         "..#.",
         "..#."],
    ],
    "O": [
        [".##.",
         ".##.",
         "....",
         "...."],
    ],
    "T": [
        [".#..",
         "###.",
         "....",
         "...."],
        [".#..",
         ".##.",
         ".#..",
         "...."],
        ["....",
         "###.",
         ".#..",
         "...."],
        [".#..",
         "##..",
         ".#..",
         "...."],
    ],
    "S": [
        [".##.",
         "##..",
         "....",
         "...."],
        ["#...",
         "##..",
         ".#..",
         "...."],
    ],
    "Z": [
        ["##..",
         ".##.",
         "....",
         "...."],
        [".#..",
         "##..",
         "#...",
         "...."],
    ],
    "J": [
        ["#...",
         "###.",
         "....",
         "...."],
        [".##.",
         ".#..",
         ".#..",
         "...."],
        ["....",
         "###.",
         "..#.",
         "...."],
        [".#..",
         ".#..",
         "##..",
         "...."],
    ],
    "L": [
        ["..#.",
         "###.",
         "....",
         "...."],
        [".#..",
         ".#..",
         ".##.",
         "...."],
        ["....",
         "###.",
         "#...",
         "...."],
        ["##..",
         ".#..",
         ".#..",
         "...."],
    ],
}

# "Junk blocks" are awkward 3-block shapes (harder to fit)
JUNK = {
    "P": [
        ["##..",
         "#...",
         "....",
         "...."],
        ["#...",
         "##..",
         "....",
         "...."],
    ],
    "U": [
        ["#.#.",
         "###.",
         "....",
         "...."],
        ["##..",
         "#...",
         "##..",
         "...."],
    ],
}

# Special Security block (unlocked later): VPN block (like 2x3 with a hole) and has place-effect
VPN = {
    "V": [
        ["###.",
         "#.#.",
         "....",
         "...."],
        [".##.",
         ".#..",
         ".##.",
         "...."],
    ]
}

def shape_cells(shape: List[str]) -> List[Tuple[int,int]]:
    cells = []
    for y,row in enumerate(shape):
        for x,ch in enumerate(row):
            if ch == "#":
                cells.append((x,y))
    return cells

@dataclass
class Piece:
    kind: str
    rot: int
    x: int
    y: int
    special: str = ""  # "", "vpn", "junk"
    def cells(self) -> List[Tuple[int,int]]:
        mats = TETROMINOES.get(self.kind) or JUNK.get(self.kind) or VPN.get(self.kind)
        mat = mats[self.rot % len(mats)]
        return shape_cells(mat)

class Bag:
    def __init__(self, rng: random.Random, allow_junk=False, allow_vpn=False):
        self.rng = rng
        self.allow_junk = allow_junk
        self.allow_vpn = allow_vpn
        self.bag = []

    def _refill(self):
        kinds = list(TETROMINOES.keys())
        self.rng.shuffle(kinds)
        self.bag = kinds

    def next_piece(self, bias_good: float, junk_chance: float) -> Piece:
        # bias_good: increases chance to give easier pieces (I, O, T) by resampling
        if self.allow_vpn and self.rng.random() < max(0.0, min(0.22, 0.08 + bias_good*0.12)):
            return Piece("V", 0, GRID_W//2-2, 0, special="vpn")
        if self.allow_junk and self.rng.random() < junk_chance:
            k = self.rng.choice(list(JUNK.keys()))
            return Piece(k, 0, GRID_W//2-2, 0, special="junk")

        if not self.bag:
            self._refill()
        k = self.bag.pop()
        # resample for good bias
        if self.rng.random() < bias_good:
            k = self.rng.choice(["I","O","T",k])
        return Piece(k, 0, GRID_W//2-2, 0)

class TetrisBoard:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.grid = [[0 for _ in range(GRID_W)] for _ in range(GRID_H)]
        self.colors = [[0 for _ in range(GRID_W)] for _ in range(GRID_H)]
        self.drop_timer = 0.0
        self.drop_interval = 0.85
        self.lock_delay = 0.0
        self.lock_max = 0.25
        self.combo = 0
        self.hold: Optional[Piece] = None
        self.can_hold = True
        self.allow_junk = False
        self.allow_vpn = False
        self.bag = Bag(rng, allow_junk=False, allow_vpn=False)
        self.current = self.bag.next_piece(bias_good=0.0, junk_chance=0.0)
        self.next = self.bag.next_piece(bias_good=0.0, junk_chance=0.0)
        self.game_over = False
        self.last_clear = 0  # lines cleared in last lock

    def set_rules(self, drop_interval: float, allow_junk: bool, allow_vpn: bool):
        self.drop_interval = max(0.28, drop_interval)
        self.allow_junk = allow_junk
        self.allow_vpn = allow_vpn
        self.bag.allow_junk = allow_junk
        self.bag.allow_vpn = allow_vpn

    def spawn(self, bias_good: float, junk_chance: float):
        self.current = self.next
        self.current.x, self.current.y = GRID_W//2-2, 0
        self.next = self.bag.next_piece(bias_good=bias_good, junk_chance=junk_chance)
        self.can_hold = True
        if self.collides(self.current, 0, 0):
            self.game_over = True

    def hold_piece(self):
        if not self.can_hold:
            return
        self.can_hold = False
        if self.hold is None:
            self.hold = Piece(self.current.kind, 0, GRID_W//2-2, 0, special=self.current.special)
            self.current = self.next
            self.next = self.bag.next_piece(bias_good=0.0, junk_chance=0.0)
        else:
            self.hold, self.current = Piece(self.current.kind, 0, GRID_W//2-2, 0, special=self.current.special), self.hold
            self.current.x, self.current.y = GRID_W//2-2, 0

    def collides(self, p: Piece, dx: int, dy: int) -> bool:
        for cx, cy in p.cells():
            x = p.x + cx + dx
            y = p.y + cy + dy
            if x < 0 or x >= GRID_W or y < 0 or y >= GRID_H:
                return True
            if self.grid[y][x]:
                return True
        return False

    def rotate(self, dir: int):
        p = self.current
        old_rot = p.rot
        p.rot = (p.rot + dir) % 4
        # wall kicks simple
        for kick in [(0,0),(-1,0),(1,0),(-2,0),(2,0)]:
            if not self.collides(p, kick[0], kick[1]):
                p.x += kick[0]; p.y += kick[1]
                return
        p.rot = old_rot

    def move(self, dx: int):
        if not self.collides(self.current, dx, 0):
            self.current.x += dx

    def soft_drop(self):
        if not self.collides(self.current, 0, 1):
            self.current.y += 1
            self.drop_timer = 0.0
        else:
            self.lock_delay += 0.06

    def hard_drop(self):
        while not self.collides(self.current, 0, 1):
            self.current.y += 1
        self.lock_piece()

    def lock_piece(self):
        p = self.current
        # place
        color_id = 2 if p.special=="vpn" else (3 if p.special=="junk" else 1)
        for cx, cy in p.cells():
            x, y = p.x + cx, p.y + cy
            if 0 <= x < GRID_W and 0 <= y < GRID_H:
                self.grid[y][x] = 1
                self.colors[y][x] = color_id

        # VPN effect: clears a small 3x3 area around its center when placed (kid-friendly power)
        if p.special == "vpn":
            # approximate center
            cells = p.cells()
            mx = int(sum([c[0] for c in cells]) / len(cells)) + p.x
            my = int(sum([c[1] for c in cells]) / len(cells)) + p.y
            for yy in range(my-1, my+2):
                for xx in range(mx-1, mx+2):
                    if 0 <= xx < GRID_W and 0 <= yy < GRID_H:
                        self.grid[yy][xx] = 0
                        self.colors[yy][xx] = 0

        self.last_clear = self.clear_lines()
        if self.last_clear > 0:
            self.combo += 1
        else:
            self.combo = 0

        self.lock_delay = 0.0

    def clear_lines(self) -> int:
        cleared = 0
        new_grid = []
        new_colors = []
        for y in range(GRID_H):
            if all(self.grid[y][x] for x in range(GRID_W)):
                cleared += 1
            else:
                new_grid.append(self.grid[y])
                new_colors.append(self.colors[y])
        while len(new_grid) < GRID_H:
            new_grid.insert(0, [0]*GRID_W)
            new_colors.insert(0, [0]*GRID_W)
        self.grid, self.colors = new_grid, new_colors
        return cleared

    def update(self, dt: float, bias_good: float, junk_chance: float):
        if self.game_over:
            return
        self.drop_timer += dt
        if self.drop_timer >= self.drop_interval:
            self.drop_timer = 0.0
            if not self.collides(self.current, 0, 1):
                self.current.y += 1
            else:
                self.lock_delay += dt
                if self.lock_delay >= self.lock_max:
                    self.lock_piece()
                    self.spawn(bias_good=bias_good, junk_chance=junk_chance)

