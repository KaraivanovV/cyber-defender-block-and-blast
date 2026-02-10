from __future__ import annotations

GAME_TITLE = "Cyber Defender: Block & Blast"
SAVE_PATH = "data/save.json"

DEFAULT_RES = (1280, 720)
FPS_CAP = 120

# Layout
BUILD_W_RATIO = 0.42  # left zone
PANEL_PAD = 14

# Tetris grid
GRID_W = 10
GRID_H = 20
CELL_PAD = 2

# Gameplay tuning (kid-friendly)
START_LIVES = 5
SHIP_SPEED = 420.0
BULLET_SPEED = 780.0

INVADER_ROWS = 5
INVADER_COLS = 10

# Wave pacing
CARD_PER_WAVE_MIN = 1
CARD_PER_WAVE_MAX = 2

# Progression
RANKS = [
    ("rookie", 0),
    ("helper", 250),
    ("protector", 700),
    ("cyber_hero", 1400),
]

MAX_SFX_VOL = 1.0
MAX_MUSIC_VOL = 1.0
