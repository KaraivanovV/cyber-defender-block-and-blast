from __future__ import annotations
import pygame as pg

from .base import BaseScene
from ..ui import Button, draw_panel, draw_text, hover_state
from ..achievements import ACHIEVEMENTS, get_unlocked_count, get_total_count, get_achievement_progress, claim_achievement
from ..core import change_scene


class AchievementsScene(BaseScene):
    def enter(self, **kwargs):
        self.btns = []
        self.scroll = 0.0
        self.scroll_target = 0.0
        self.scroll_max = 0
        self._layout()

    def _layout(self):
        w, h = self.app.screen.get_size()
        self.panel = pg.Rect(w // 2 - 560, h // 2 - 340, 1120, 680)

    def handle_event(self, ev):
        if ev.type == pg.VIDEORESIZE:
            self._layout()
        
        # Mouse wheel scrolling
        if ev.type == pg.MOUSEWHEEL:
            mx, my = pg.mouse.get_pos()
            if self.panel.collidepoint(mx, my):
                self.scroll_target -= ev.y * 50
                self.scroll_target = max(0.0, min(self.scroll_target, self.scroll_max))
        
        for b in self.btns:
            b.handle(ev)

    def update(self, dt):
        # Smooth scrolling
        self.scroll += (self.scroll_target - self.scroll) * min(1.0, dt * 12.0)
        if abs(self.scroll - self.scroll_target) < 0.5:
            self.scroll = self.scroll_target

    def draw(self, surf):
        app = self.app
        sd = app.save
        lang = sd.settings.lang
        colors, fonts = app.colors, app.fonts
        self.draw_background(surf, colors)
        
        title = "Achievements" if lang == "en" else "Достигнувања"
        draw_panel(surf, self.panel, colors, title=title, title_font=fonts.ui_bold)

        self.btns = []

        # Progress header with better styling
        unlocked = get_unlocked_count(sd)
        total = get_total_count()
        progress_pct = int((unlocked / total) * 100) if total > 0 else 0
        
        header_y = self.panel.y + 75
        
        # Progress text
        progress_text = f"{unlocked}/{total} Unlocked ({progress_pct}%)" if lang == "en" else f"{unlocked}/{total} Отклучени ({progress_pct}%)"
        draw_text(surf, progress_text, fonts.ui_bold, colors["accent"], (self.panel.x + 40, header_y), max_w=self.panel.w - 80)
        
        # Overall progress bar
        bar_x = self.panel.x + 40
        bar_y = header_y + 30
        bar_w = self.panel.w - 80
        bar_h = 16
        
        pg.draw.rect(surf, colors["line"], (bar_x, bar_y, bar_w, bar_h), border_radius=8)
        if total > 0:
            fill_w = int((unlocked / total) * bar_w)
            if fill_w > 0:
                pg.draw.rect(surf, colors["accent"], (bar_x, bar_y, fill_w, bar_h), border_radius=8)

        # Scrollable area for achievements
        view = pg.Rect(self.panel.x + 40, self.panel.y + 130, self.panel.w - 80, self.panel.h - 220)

        # Clip to viewport
        old_clip = surf.get_clip()
        surf.set_clip(view)

        # Achievement grid: 4 columns for better spacing
        cols = 4
        card_w = 240
        card_h = 160
        gap_x = 18
        gap_y = 20
        
        # Calculate total grid width to center it
        total_grid_w = cols * card_w + (cols - 1) * gap_x
        start_x = view.x + (view.w - total_grid_w) // 2
        start_y = view.y - int(self.scroll)

        # Calculate total content height for scrolling
        rows = (len(ACHIEVEMENTS) + cols - 1) // cols
        content_height = rows * (card_h + gap_y) - gap_y
        self.scroll_max = max(0, content_height - view.h)

        # Draw achievement cards
        achievement_list = list(ACHIEVEMENTS.values())
        for i, achievement in enumerate(achievement_list):
            row = i // cols
            col = i % cols
            
            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)
            
            card_rect = pg.Rect(x, y, card_w, card_h)
            
            # Only draw if visible
            if card_rect.bottom < view.y - 20 or card_rect.top > view.bottom + 20:
                continue
            
            # Check if unlocked
            is_unlocked = achievement.id in sd.unlocked_achievements
            
            # Hover effect
            mx, my = pg.mouse.get_pos()
            is_hovered = card_rect.collidepoint(mx, my)
            
            # Card background with hover
            if is_unlocked:
                if is_hovered:
                    bg_color = colors["panel2"]
                    border_color = colors["accent"]
                else:
                    bg_color = colors["panel"]
                    border_color = colors["accent"]
                text_color = colors["text"]
            else:
                bg_color = (colors["panel"][0] // 2, colors["panel"][1] // 2, colors["panel"][2] // 2)
                border_color = colors["line"]
                text_color = colors["muted"]
            
            pg.draw.rect(surf, bg_color, card_rect, border_radius=12)
            pg.draw.rect(surf, border_color, card_rect, width=2, border_radius=12)
            
            # Achievement name
            name = achievement.name_en if lang == "en" else achievement.name_mk
            name_y = card_rect.y + 16
            draw_text(surf, name, fonts.ui_bold, text_color, (card_rect.x + 16, name_y), max_w=card_w - 32)
            
            # Achievement description + reward
            desc = achievement.desc_en if lang == "en" else achievement.desc_mk
            # Add reward info to description
            if achievement.reward_coins > 0:
                reward_text = f"Reward: {achievement.reward_coins} coins" if lang == "en" else f"Награда: {achievement.reward_coins} coins"
                desc = f"{desc}\n{reward_text}"
            desc_y = card_rect.y + 45
            draw_text(surf, desc, fonts.ui, text_color, (card_rect.x + 16, desc_y), max_w=card_w - 32)
            
            # Check if claimed
            is_claimed = achievement.id in sd.claimed_achievements
            
            # Bottom section: progress bar, claim button, or claimed status
            if not is_unlocked:
                # NOT UNLOCKED - Show progress bar for incremental achievements
                if achievement.requirement > 1:
                    current, required = get_achievement_progress(sd, achievement.id)
                    
                    # Progress text
                    progress_text = f"{current}/{required}"
                    prog_y = card_rect.bottom - 45
                    draw_text(surf, progress_text, fonts.ui, text_color, (card_rect.x + 16, prog_y), max_w=card_w - 32)
                    
                    # Progress bar
                    bar_x = card_rect.x + 16
                    bar_y = card_rect.bottom - 22
                    bar_w = card_w - 32
                    bar_h = 10
                    
                    # Background
                    pg.draw.rect(surf, colors["line"], (bar_x, bar_y, bar_w, bar_h), border_radius=5)
                    
                    # Fill
                    if required > 0:
                        fill_w = int((current / required) * bar_w)
                        if fill_w > 0:
                            pg.draw.rect(surf, colors["accent"], (bar_x, bar_y, fill_w, bar_h), border_radius=5)
            
            elif not is_claimed:
                # UNLOCKED BUT NOT CLAIMED - Show claim button
                claim_btn_rect = pg.Rect(card_rect.x + 16, card_rect.bottom - 40, card_w - 32, 30)
                claim_text = f"CLAIM +{achievement.reward_coins}" if lang == "en" else f"ЗЕМИ +{achievement.reward_coins}"
                
                def make_claim_callback(ach_id):
                    def claim_callback():
                        coins_earned = claim_achievement(sd, ach_id)
                        if coins_earned > 0:
                            from ..save_system import save
                            save(sd)
                    return claim_callback
                
                self.btns.append(Button(claim_btn_rect, claim_text, make_claim_callback(achievement.id)))
            
            else:
                # CLAIMED - Show checkmark and claimed status
                status_text = "CLAIMED" if lang == "en" else "ЗЕМЕНО"
                status_y = card_rect.bottom - 28
                draw_text(surf, status_text, fonts.ui_bold, colors["good"], (card_rect.x + 16, status_y), max_w=card_w - 32)

        # Restore clip
        surf.set_clip(old_clip)

        # Scroll bar (if needed)
        if self.scroll_max > 0:
            track_x = view.right - 10
            track = pg.Rect(track_x, view.y, 8, view.h)
            pg.draw.rect(surf, colors["line"], track, border_radius=4)
            
            knob_h = max(40, int(view.h * (view.h / (view.h + self.scroll_max))))
            knob_y = int(view.y + (view.h - knob_h) * (self.scroll / self.scroll_max))
            knob = pg.Rect(track_x, knob_y, 8, knob_h)
            pg.draw.rect(surf, colors["accent"], knob, border_radius=4)

        # Back button
        back = pg.Rect(self.panel.x + 40, self.panel.bottom - 70, 200, 50)
        back_text = "Back" if lang == "en" else "Назад"
        self.btns.append(Button(back, back_text, lambda: change_scene(app, __import__('src.scenes.menu', fromlist=['MenuScene']).MenuScene(app))))

        # Draw buttons
        for b in self.btns:
            b.draw(surf, fonts.ui_bold, colors, hover_state(b.rect))
