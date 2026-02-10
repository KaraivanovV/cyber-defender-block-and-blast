from __future__ import annotations
import pygame as pg
from typing import TYPE_CHECKING, Any, Dict

from .base import BaseScene
from ..core import change_scene
from ..ui import draw_panel

if TYPE_CHECKING:
    from ..app import App

class SplashScene(BaseScene):
    """Display a splash screen with text before/after levels."""
    
    def __init__(self, app: App, text: str, next_scene_class=None, next_scene_args: dict = None):
        """
        Args:
            app: Application instance
            text: Text to display (supports newlines)
            next_scene_class: Scene class to instantiate and transition to
            next_scene_args: Arguments to pass to next scene's enter() method
        """
        super().__init__(app)
        self.text = text
        self.next_scene_class = next_scene_class
        self.next_scene_args = next_scene_args or {}
        
        # Get language from settings
        self.lang = app.save.settings.lang
        
    def update(self, dt: float):
        """No auto-advance - player must manually skip."""
        pass
            
    def handle_event(self, event: pg.event.Event):
        """Handle manual skip."""
        if event.type == pg.KEYDOWN:
            if event.key in (pg.K_SPACE, pg.K_RETURN, pg.K_ESCAPE):
                self._advance()
        elif event.type == pg.MOUSEBUTTONDOWN:
            self._advance()
            
    def _advance(self):
        """Transition to next scene."""
        if self.next_scene_class:
            # Special handling for SplashScene which requires text parameter
            if self.next_scene_class == SplashScene:
                # Extract text and other args for splash scene
                text = self.next_scene_args.get("text", "")
                next_class = self.next_scene_args.get("next_scene_class")
                next_args = self.next_scene_args.get("next_scene_args", {})
                next_scene = SplashScene(self.app, text, next_scene_class=next_class, next_scene_args=next_args)
                change_scene(self.app, next_scene)
            else:
                # Normal scene instantiation
                next_scene = self.next_scene_class(self.app)
                change_scene(self.app, next_scene, **self.next_scene_args)
        
    def draw(self, surf: pg.Surface):
        """Draw splash screen with improved styling."""
        # Access fonts and colors through app instance
        fonts = self.app.fonts
        colors, fonts = self.app.colors, self.app.fonts
        self.draw_background(surf, colors)
        w, h = surf.get_size()
        
        # Create a large centered panel
        panel_w = min(900, w - 100)
        panel_h = min(600, h - 100)
        panel_rect = pg.Rect((w - panel_w) // 2, (h - panel_h) // 2, panel_w, panel_h)
        
        draw_panel(surf, panel_rect, colors)
        
        # Draw text with better formatting
        lines = self.text.split('\n')
        
        # Use larger, game-consistent fonts
        y = panel_rect.y + 60
        line_spacing = 45
        
        for line in lines:
            if line.strip():
                # Use accent color for title lines (all caps or ending with !)
                if line.isupper() or line.strip().endswith('!'):
                    # Title line - use bold font and accent color
                    text_surf = fonts.ui_bold.render(line, True, colors["accent"])
                else:
                    # Regular line
                    text_surf = fonts.ui.render(line, True, colors["text"])
                
                text_rect = text_surf.get_rect(centerx=panel_rect.centerx, y=y)
                surf.blit(text_surf, text_rect)
                y += line_spacing
        
        # Draw prominent "Press SPACE to continue" button-style hint
        hint_y = panel_rect.bottom - 80
        hint_text = "Press SPACE to continue" if self.lang == "en" else "Притисни SPACE за да продолжиш"
        
        # Draw a button-like background
        hint_surf = fonts.ui_bold.render(hint_text, True, colors["text"])
        hint_rect = hint_surf.get_rect(centerx=panel_rect.centerx, centery=hint_y)
        
        # Button background
        button_rect = hint_rect.inflate(40, 20)
        pg.draw.rect(surf, colors["panel2"], button_rect, border_radius=8)
        pg.draw.rect(surf, colors["accent"], button_rect, width=2, border_radius=8)
        
        # Draw text on top
        surf.blit(hint_surf, hint_rect)
