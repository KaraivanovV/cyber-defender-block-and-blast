from __future__ import annotations
import json, os
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List

from .constants import SAVE_PATH, DEFAULT_RES

def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))

def _safe_int(x, default=0) -> int:
    try:
        return int(x)
    except Exception:
        return default

@dataclass
class Settings:
    lang: str = "mk"
    resolution: List[int] = field(default_factory=lambda: [DEFAULT_RES[0], DEFAULT_RES[1]])
    fullscreen: bool = False
    music_vol: float = 0.6
    sfx_vol: float = 0.8

    def normalize(self):
        if self.lang not in ("mk", "en"):
            self.lang = "mk"
        if not (isinstance(self.resolution, list) and len(self.resolution) == 2):
            self.resolution = [DEFAULT_RES[0], DEFAULT_RES[1]]
        self.resolution[0] = int(self.resolution[0])
        self.resolution[1] = int(self.resolution[1])
        self.music_vol = _clamp01(self.music_vol)
        self.sfx_vol = _clamp01(self.sfx_vol)

@dataclass
class SaveData:
    version: int = 2
    coins: int = 0
    xp: int = 0
    unlocked_world: int = 1

    cosmetics: Dict[str, Any] = field(default_factory=lambda: {
        "ship_skin": 0,
        "trail": 0,
        "firewall_palette": 0,
        "unlocked": {"ship_skin": [0], "trail": [0], "firewall_palette": [0]},
    })

    highscores: Dict[str, int] = field(default_factory=lambda: {"story": 0})
    achievements: Dict[str, bool] = field(default_factory=dict)
    settings: Settings = field(default_factory=Settings)

    daily_challenge_on: bool = False
    daily_seed: int = 0

    story_max_unlocked: int = 1
    story_best: int = 0

    wallet: int = 0
    
    # Tutorial system
    tutorial_completed: bool = False  # Set to True after completing Level 5
    completed_tutorials: List[int] = field(default_factory=list)  # List of completed tutorial level IDs

    upgrades: Dict[str, int] = field(default_factory=lambda: {
        "obstacle_slots": 1,
        "fire_rate_lvl": 1,
        "block_hp": 1,
        "tetris_time_bonus": 0,   # NEW: +seconds (0..10)
    })

    checkpoint_hearts: Dict[int, int] = field(default_factory=dict)  # Checkpoint level -> hearts saved
    owned_books: List[int] = field(default_factory=list)  # List of owned book IDs [1, 2, 3]
    
    # Achievement system
    achievement_progress: Dict[str, int] = field(default_factory=dict)  # achievement_id -> progress count
    unlocked_achievements: List[str] = field(default_factory=list)  # List of unlocked achievement IDs
    claimed_achievements: List[str] = field(default_factory=list)  # List of claimed achievement IDs (for rewards)

def default_save() -> SaveData:
    return SaveData()

def _migrate_raw(raw: Dict[str, Any]) -> Dict[str, Any]:
    raw = dict(raw) if isinstance(raw, dict) else {}

    raw["version"] = _safe_int(raw.get("version", 1), 1)

    if "settings" not in raw or not isinstance(raw["settings"], dict):
        raw["settings"] = {}

    if "cosmetics" not in raw or not isinstance(raw["cosmetics"], dict):
        raw["cosmetics"] = default_save().cosmetics

    if "highscores" not in raw or not isinstance(raw["highscores"], dict):
        raw["highscores"] = default_save().highscores

    if "achievements" not in raw or not isinstance(raw["achievements"], dict):
        raw["achievements"] = {}

    if "story_max_unlocked" not in raw:
        uw = _safe_int(raw.get("unlocked_world", 1), 1)
        raw["story_max_unlocked"] = 1 if uw <= 1 else min(10, 1 + (uw - 1) * 3)

    if "story_best" not in raw:
        raw["story_best"] = _safe_int(raw.get("highscores", {}).get("story", 0), 0)
    if "endless_best" not in raw:
        raw["endless_best"] = _safe_int(raw.get("highscores", {}).get("endless", 0), 0)

    # Migrate old wallet fields to new consolidated wallet
    if "wallet" not in raw:
        wallet_story = _safe_int(raw.get("wallet_story", 0), 0)
        wallet_endless = _safe_int(raw.get("wallet_endless", 0), 0)
        # Combine both wallets (user keeps all their coins)
        raw["wallet"] = wallet_story + wallet_endless

    if "upgrades" not in raw or not isinstance(raw["upgrades"], dict):
        raw["upgrades"] = default_save().upgrades
    else:
        for k, v in default_save().upgrades.items():
            if k not in raw["upgrades"]:
                raw["upgrades"][k] = v

    raw["upgrades"]["obstacle_slots"] = max(1, min(5, _safe_int(raw["upgrades"].get("obstacle_slots", 1), 1)))
    raw["upgrades"]["block_hp"] = max(1, min(5, _safe_int(raw["upgrades"].get("block_hp", 1), 1)))
    raw["upgrades"]["fire_rate_lvl"] = max(1, _safe_int(raw["upgrades"].get("fire_rate_lvl", 1), 1))
    raw["upgrades"]["tetris_time_bonus"] = max(0, min(10, _safe_int(raw["upgrades"].get("tetris_time_bonus", 0), 0)))

    if "checkpoint_hearts" not in raw or not isinstance(raw["checkpoint_hearts"], dict):
        raw["checkpoint_hearts"] = {}
    
    if "owned_books" not in raw or not isinstance(raw["owned_books"], list):
        raw["owned_books"] = []
    
    # Achievement system
    if "achievement_progress" not in raw or not isinstance(raw["achievement_progress"], dict):
        raw["achievement_progress"] = {}
    
    if "unlocked_achievements" not in raw or not isinstance(raw["unlocked_achievements"], list):
        raw["unlocked_achievements"] = []
    
    if "claimed_achievements" not in raw or not isinstance(raw["claimed_achievements"], list):
        raw["claimed_achievements"] = []
    
    # Tutorial completion flag
    if "tutorial_completed" not in raw:
        raw["tutorial_completed"] = False
    
    # Completed tutorials tracking
    if "completed_tutorials" not in raw or not isinstance(raw["completed_tutorials"], list):
        raw["completed_tutorials"] = []

    raw["story_max_unlocked"] = max(1, min(20, _safe_int(raw.get("story_max_unlocked", 1), 1)))
    return raw

def load_save() -> SaveData:
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

    if not os.path.exists(SAVE_PATH):
        sd = default_save()
        save(sd)
        return sd

    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)

        raw = _migrate_raw(raw)

        sd = SaveData(
            version=_safe_int(raw.get("version", 2), 2),
            coins=_safe_int(raw.get("coins", 0), 0),
            xp=_safe_int(raw.get("xp", 0), 0),
            unlocked_world=_safe_int(raw.get("unlocked_world", 1), 1),

            cosmetics=raw.get("cosmetics", default_save().cosmetics),
            highscores=raw.get("highscores", default_save().highscores),
            achievements=raw.get("achievements", {}),

            settings=Settings(**raw.get("settings", {})),
            daily_challenge_on=bool(raw.get("daily_challenge_on", False)),
            daily_seed=_safe_int(raw.get("daily_seed", 0), 0),

            story_max_unlocked=_safe_int(raw.get("story_max_unlocked", 1), 1),
            story_best=_safe_int(raw.get("story_best", 0), 0),

            wallet=_safe_int(raw.get("wallet", 0), 0),
            
            tutorial_completed=bool(raw.get("tutorial_completed", False)),
            completed_tutorials=raw.get("completed_tutorials", []),

            upgrades=raw.get("upgrades", default_save().upgrades),
            
            checkpoint_hearts=raw.get("checkpoint_hearts", {}),
            owned_books=raw.get("owned_books", []),
            
            achievement_progress=raw.get("achievement_progress", {}),
            unlocked_achievements=raw.get("unlocked_achievements", []),
            claimed_achievements=raw.get("claimed_achievements", []),
        )

        sd.settings.normalize()

        sd.highscores["story"] = max(sd.highscores.get("story", 0), sd.story_best)

        return sd

    except Exception:
        sd = default_save()
        save(sd)
        return sd

def save(sd: SaveData) -> None:
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

    sd.highscores["story"] = max(sd.highscores.get("story", 0), sd.story_best)

    d = asdict(sd)
    d["settings"] = asdict(sd.settings)

    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
