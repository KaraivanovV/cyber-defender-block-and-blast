"""Brick collectible that falls from defeated enemies."""
from __future__ import annotations
import pygame as pg
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Brick:
    """A collectible brick that falls with gravity."""
    
    def __init__(self, x: float, y: float):
        """
        Initialize a brick at the given position.
        
        Args:
            x: Initial x position (center)
            y: Initial y position (top)
        """
        self.x = x
        self.y = y
        self.vy = 0.0  # Vertical velocity
        self.gravity = 600.0  # Pixels per second squared
        self.size = 12  # Brick size in pixels
        self.alive = True
        
    def update(self, dt: float, screen_bottom: float):
        """
        Update brick position with gravity.
        
        Args:
            dt: Delta time in seconds
            screen_bottom: Bottom edge of screen to check if brick fell off
        """
        # Apply gravity
        self.vy += self.gravity * dt
        self.y += self.vy * dt
        
        # Remove if fell off screen
        if self.y > screen_bottom + 50:
            self.alive = False
    
    def get_rect(self) -> pg.Rect:
        """Get collision rectangle for the brick."""
        return pg.Rect(
            self.x - self.size // 2,
            self.y,
            self.size,
            self.size
        )
    
    def draw(self, surf: pg.Surface, colors: dict):
        """
        Draw the brick.
        
        Args:
            surf: Surface to draw on
            colors: Color dictionary from app
        """
        rect = self.get_rect()
        
        # Draw brick with border
        pg.draw.rect(surf, colors.get("accent", (255, 100, 0)), rect, border_radius=2)
        pg.draw.rect(surf, colors.get("text", (255, 255, 255)), rect, width=1, border_radius=2)
