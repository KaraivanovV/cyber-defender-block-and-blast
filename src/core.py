from __future__ import annotations
import asyncio
import pygame as pg
import random
import datetime
from dataclasses import dataclass
from typing import Optional

from .constants import DEFAULT_RES, FPS_CAP, GAME_TITLE
from .save_system import load_save, save, SaveData
from .assets import load_fonts, make_palette

def create_game_rng(save_data, stage=1, wave=1):
    """
    Create a Random instance for game scenes.
    Uses daily challenge seed if enabled, otherwise creates unseeded RNG.
    
    Args:
        save_data: SaveData instance
        stage: Current stage number (for seed variation)
        wave: Current wave number (for seed variation)
    
    Returns:
        random.Random instance
    """
    if save_data.daily_challenge_on:
        today = datetime.date.today().toordinal()
        seed = (today * 10007) % 2_000_000_000
        save_data.daily_seed = seed
        return random.Random(seed + 1000 * stage + wave)
    else:
        return random.Random()

@dataclass
class App:
    screen: pg.Surface
    clock: pg.time.Clock
    running: bool
    save: SaveData
    colors: dict
    fonts: any
    scene: any

class Scene:
    def __init__(self, app: App):
        self.app = app
    def enter(self, **kwargs): ...
    def exit(self): ...
    def handle_event(self, ev: pg.event.Event): ...
    def update(self, dt: float): ...
    def draw(self, surf: pg.Surface): ...

def set_display(res, fullscreen: bool):
    import sys
    # pygbag/WebGL doesn't support SCALED flag with high DPI displays
    if sys.platform == "emscripten":
        # Running in browser - use minimal flags for WebGL compatibility
        flags = 0
        if fullscreen:
            flags |= pg.FULLSCREEN
    else:
        # Running locally - use SCALED for better display handling
        flags = pg.SCALED
        if fullscreen:
            flags |= pg.FULLSCREEN
    return pg.display.set_mode(res, flags)

def create_app() -> App:
    pg.init()
    try:
        pg.mixer.init()
    except Exception:
        pass
    pg.display.set_caption(GAME_TITLE)
    sd = load_save()
    res = tuple(sd.settings.resolution)
    screen = set_display(res, sd.settings.fullscreen)
    clock = pg.time.Clock()
    colors = make_palette()
    fonts = load_fonts(scale=max(1.0, res[1]/720))
    return App(screen=screen, clock=clock, running=True, save=sd, colors=colors, fonts=fonts, scene=None)

def change_scene(app: App, new_scene: Scene, **kwargs):
    if app.scene:
        app.scene.exit()
    app.scene = new_scene
    app.scene.enter(**kwargs)

def apply_settings(app: App):
    res = tuple(app.save.settings.resolution)
    app.screen = set_display(res, app.save.settings.fullscreen)
    app.fonts = load_fonts(scale=max(1.0, res[1]/720))
    save(app.save)

async def main_loop(app: App):
    while app.running:
        dt = app.clock.tick(FPS_CAP) / 1000.0
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                app.running = False
            else:
                if app.scene:
                    app.scene.handle_event(ev)
        if app.scene:
            app.scene.update(dt)
            app.scene.draw(app.screen)
        pg.display.flip()
        # Yield control to browser (required for pygbag)
        await asyncio.sleep(0)
    save(app.save)
    pg.quit()
