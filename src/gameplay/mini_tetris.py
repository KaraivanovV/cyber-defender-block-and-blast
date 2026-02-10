from __future__ import annotations
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional

W, H = 10, 10

SHAPES = {
    "I": [(0,1),(1,1),(2,1),(3,1)],
    "O": [(1,0),(2,0),(1,1),(2,1)],
    "T": [(1,0),(0,1),(1,1),(2,1)],
    "L": [(0,0),(0,1),(0,2),(1,2)],
    "J": [(1,0),(1,1),(1,2),(0,2)],
    "S": [(1,0),(2,0),(0,1),(1,1)],
    "Z": [(0,0),(1,0),(1,1),(2,1)],
}

def rotate_cells(cells: List[Tuple[int,int]], dir: int) -> List[Tuple[int,int]]:
    out=[]
    for x,y in cells:
        if dir > 0:
            out.append((y, 3-x))
        else:
            out.append((3-y, x))
    minx=min(c[0] for c in out)
    miny=min(c[1] for c in out)
    return [(x-minx, y-miny) for x,y in out]

@dataclass
class Piece:
    kind: str
    cells0: List[Tuple[int,int]]
    rot: int = 0
    x: int = 3
    y: int = -2

    def cells(self) -> List[Tuple[int,int]]:
        c = self.cells0
        r = self.rot % 4
        for _ in range(r):
            c = rotate_cells(c, +1)
        return c

class MiniTetris:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.grid = [[0]*W for _ in range(H)]
        self.game_over = False

        # lines
        self.lines_cleared_last = 0
        self.score_lines = 0

        # hold/next
        self.hold: Optional[Piece] = None
        self.hold_used = False
        self.next_piece = self._new_piece()
        self.current = self._spawn()

        # timing
        self.drop_timer = 0.0
        self.drop_interval = 0.45

    def _new_piece(self) -> Piece:
        k = self.rng.choice(list(SHAPES.keys()))
        return Piece(k, SHAPES[k])

    def _spawn(self) -> Piece:
        p = self.next_piece
        self.next_piece = self._new_piece()
        p.x, p.y, p.rot = 3, -2, 0
        self.hold_used = False
        if not self._fits(p, p.x, p.y, p.rot):
            self.game_over = True
        return p

    def _fits(self, p: Piece, x: int, y: int, rot: int) -> bool:
        old = p.rot
        p.rot = rot
        for cx, cy in p.cells():
            gx, gy = x+cx, y+cy
            if gx < 0 or gx >= W:
                p.rot = old; return False
            if gy >= H:
                p.rot = old; return False
            if gy >= 0 and self.grid[gy][gx]:
                p.rot = old; return False
        p.rot = old
        return True

    def move(self, dx: int, dy: int) -> None:
        if self.game_over: return
        nx, ny = self.current.x + dx, self.current.y + dy
        if self._fits(self.current, nx, ny, self.current.rot):
            self.current.x, self.current.y = nx, ny
        elif dy == 1:
            self._lock()

    def rotate(self, dir: int) -> None:
        if self.game_over: return
        nr = (self.current.rot + (1 if dir>0 else -1)) % 4
        for kx in (0, -1, 1, -2, 2):
            if self._fits(self.current, self.current.x+kx, self.current.y, nr):
                self.current.x += kx
                self.current.rot = nr
                return

    def soft_drop(self) -> None:
        self.move(0, 1)

    def hard_drop(self) -> None:
        while not self.game_over and self._fits(self.current, self.current.x, self.current.y+1, self.current.rot):
            self.current.y += 1
        self._lock()

    def hold_piece(self) -> None:
        if self.game_over or self.hold_used:
            return
        self.hold_used = True

        if self.hold is None:
            self.hold = Piece(self.current.kind, self.current.cells0)
            self.current = self._spawn()
        else:
            tmp = self.hold
            self.hold = Piece(self.current.kind, self.current.cells0)
            self.current = Piece(tmp.kind, tmp.cells0)
            self.current.x, self.current.y, self.current.rot = 3, -2, 0
            if not self._fits(self.current, self.current.x, self.current.y, self.current.rot):
                self.game_over = True

    def update(self, dt: float) -> None:
        if self.game_over:
            return

        # IMPORTANT: reset ONCE per frame
        self.lines_cleared_last = 0

        self.drop_timer += dt
        while self.drop_timer >= self.drop_interval:
            self.drop_timer -= self.drop_interval
            self.move(0, 1)

    def _lock(self) -> None:
        for cx, cy in self.current.cells():
            gx, gy = self.current.x+cx, self.current.y+cy
            if gy < 0:
                self.game_over = True
                return
            self.grid[gy][gx] = 1

        cleared = 0
        new = []
        for row in self.grid:
            if all(row):
                cleared += 1
            else:
                new.append(row)

        while len(new) < H:
            new.insert(0, [0]*W)

        self.grid = new

        self.lines_cleared_last = cleared
        self.score_lines += cleared

        self.current = self._spawn()

    def export_obstruction(self) -> List[List[int]]:
        return [row[:] for row in self.grid]
