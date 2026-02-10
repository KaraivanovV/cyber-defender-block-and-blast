from __future__ import annotations
import pygame as pg
from dataclasses import dataclass
from typing import List, Optional
import os
from pathlib import Path

@dataclass
class Fonts:
    ui: pg.font.Font
    ui_bold: pg.font.Font
    big: pg.font.Font

@dataclass
class AnimatedSprite:
    """Manages animated sprite frames and timing."""
    frames: List[pg.Surface]
    frame_duration: float = 0.1  # seconds per frame
    current_frame: int = 0
    timer: float = 0.0
    
    def update(self, dt: float):
        """Update animation timer and advance frames."""
        self.timer += dt
        if self.timer >= self.frame_duration:
            self.timer = 0.0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
    
    def get_current_frame(self) -> pg.Surface:
        """Get the current frame surface."""
        return self.frames[self.current_frame]

def load_fonts(scale: float = 1.0) -> Fonts:
    # Use default font for portability.
    ui = pg.font.SysFont("consolas,dejavusansmono,arial", int(18*scale))
    ui_b = pg.font.SysFont("consolas,dejavusansmono,arial", int(18*scale), bold=True)
    big = pg.font.SysFont("consolas,dejavusansmono,arial", int(34*scale), bold=True)
    return Fonts(ui=ui, ui_bold=ui_b, big=big)

def beep_sound(freq=440, ms=60, vol=0.25):
    # Lightweight procedural sound (optional). If mixer not available, ignore.
    try:
        import numpy as np
        sample_rate = 22050
        t = np.linspace(0, ms/1000.0, int(sample_rate*ms/1000.0), endpoint=False)
        wave = (np.sin(2*np.pi*freq*t)*32767*vol).astype(np.int16)
        snd = pg.sndarray.make_sound(wave)
        return snd
    except Exception:
        return None

def make_palette():
    # Soft pixel-friendly palette
    return {
        "bg": (14, 16, 28),
        "panel": (26, 30, 52),
        "panel2": (34, 40, 66),
        "line": (70, 80, 120),
        "text": (230, 234, 255),
        "muted": (170, 180, 210),
        "good": (120, 220, 150),
        "bad": (240, 120, 120),
        "accent": (120, 170, 255),
        "yellow": (250, 220, 120),
        "cyan": (110, 240, 235),
        "purple": (200, 140, 255),
    }

FIREWALL_PALETTES = [
    [(90, 110, 200), (110, 140, 255), (70, 90, 170)],  # blue
    [(90, 190, 160), (120, 230, 190), (70, 150, 120)], # mint
    [(200, 130, 100), (255, 170, 130), (170, 100, 70)],# warm
]

SHIP_SKINS = [
    {"main": (120, 170, 255), "shade": (60, 90, 170)},
    {"main": (120, 230, 190), "shade": (70, 150, 120)},
    {"main": (255, 170, 130), "shade": (170, 100, 70)},
]

TRAILS = [
    {"color": (120, 170, 255)},
    {"color": (120, 230, 190)},
    {"color": (255, 170, 130)},
]

def load_gif(filepath: str, target_size: tuple = (80, 80)) -> Optional[AnimatedSprite]:
    """Load an animated GIF and return an AnimatedSprite.
    
    Args:
        filepath: Path to the GIF file
        target_size: Tuple of (width, height) to scale frames to
        
    Returns:
        AnimatedSprite with all frames, or None if loading fails
    """
    try:
        from PIL import Image
        
        # Load GIF with PIL
        img = Image.open(filepath)
        frames = []
        
        # Extract all frames
        try:
            while True:
                # Convert frame to RGBA to preserve transparency
                frame = img.convert('RGBA')
                
                # Convert PIL image to pygame surface with proper alpha handling
                mode = frame.mode
                size = frame.size
                data = frame.tobytes()
                
                # Create pygame surface with per-pixel alpha
                py_image = pg.image.fromstring(data, size, mode)
                py_image = py_image.convert_alpha()  # Enable per-pixel alpha
                
                # Scale to target size (use smoothscale for better quality)
                py_image = pg.transform.smoothscale(py_image, target_size)
                frames.append(py_image)
                
                # Move to next frame
                img.seek(img.tell() + 1)
        except EOFError:
            pass  # End of frames
        
        if frames:
            # Try to get frame duration from GIF
            frame_duration = img.info.get('duration', 100) / 1000.0  # Convert ms to seconds
            return AnimatedSprite(frames=frames, frame_duration=frame_duration)
        
    except ImportError:
        print("PIL/Pillow not installed. Falling back to static image loading.")
        # Try loading as static image
        try:
            img = pg.image.load(filepath).convert_alpha()
            img = pg.transform.smoothscale(img, target_size)
            return AnimatedSprite(frames=[img], frame_duration=0.1)
        except Exception as e:
            print(f"Failed to load image {filepath}: {e}")
            return None
    except Exception as e:
        print(f"Failed to load GIF {filepath}: {e}")
        return None

def load_static_image(filepath: str, target_size: tuple = (80, 80)) -> Optional[AnimatedSprite]:
    """Load a static image (PNG, JPG, etc.) as a single-frame AnimatedSprite.
    
    Args:
        filepath: Path to the image file
        target_size: Tuple of (width, height) to scale to
        
    Returns:
        AnimatedSprite with single frame, or None if loading fails
    """
    try:
        img = pg.image.load(filepath).convert_alpha()  # Enable transparency
        img = pg.transform.smoothscale(img, target_size)  # Better quality scaling
        return AnimatedSprite(frames=[img], frame_duration=0.1)
    except Exception as e:
        print(f"Failed to load image {filepath}: {e}")
        return None

def load_boss_sprites(assets_dir: str = "assets") -> dict:
    """Load all boss sprites from the assets directory.
    
    Returns:
        Dictionary mapping sprite names to AnimatedSprite objects
    """
    sprites = {}
    
    # Get the project root directory (parent of src/)
    try:
        # Try to find assets directory relative to this file
        current_file = Path(__file__).parent.parent
        assets_path = current_file / assets_dir
        
        if not assets_path.exists():
            print(f"Assets directory not found at {assets_path}")
            return sprites
        
        # Load all image files
        for ext in ['*.gif', '*.png', '*.jpg', '*.jpeg']:
            for filepath in assets_path.glob(ext):
                sprite_name = filepath.stem  # filename without extension
                
                # Load based on extension
                if filepath.suffix.lower() == '.gif':
                    sprite = load_gif(str(filepath))
                else:
                    sprite = load_static_image(str(filepath))
                
                if sprite:
                    sprites[sprite_name] = sprite
                    print(f"Loaded boss sprite: {sprite_name} ({len(sprite.frames)} frames)")
        
    except Exception as e:
        print(f"Error loading boss sprites: {e}")
    
    return sprites
