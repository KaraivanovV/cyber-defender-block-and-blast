from __future__ import annotations
import pygame as pg
from pathlib import Path
from ..core import Scene

class BaseScene(Scene):
    _shared_background = None  # Class variable to cache background
    
    @classmethod
    def load_background(cls):
        """Load background image once and cache it"""
        if cls._shared_background is None:
            try:
                assets_path = Path(__file__).parent.parent.parent / "assets" / "background.png"
                if assets_path.exists():
                    cls._shared_background = pg.image.load(str(assets_path)).convert()
            except Exception as e:
                print(f"Could not load background.png: {e}")
        return cls._shared_background
    
    def draw_background(self, surf, colors):
        """Draw background image if available, otherwise fill with solid color"""
        bg = self.load_background()
        if bg:
            w, h = surf.get_size()
            scaled_bg = pg.transform.scale(bg, (w, h))
            surf.blit(scaled_bg, (0, 0))
        else:
            surf.fill(colors["bg"])

