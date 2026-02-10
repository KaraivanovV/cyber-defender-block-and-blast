from __future__ import annotations
import pygame as pg

from .base import BaseScene
from ..ui import Button, draw_panel, draw_text, hover_state
from ..localization import TEXT
from ..core import change_scene
from ..save_system import save
from ..achievements import check_achievement
from ..constants import START_LIVES


def price_obstacle_slots(next_val: int) -> int:
    table = {2: 80, 3: 180, 4: 360, 5: 600}
    return table.get(next_val, 9999)


def price_fire_rate(next_lvl: int) -> int:
    return 80 + (next_lvl - 2) * 120


def price_block_hp(next_val: int) -> int:
    table = {2: 100, 3: 220, 4: 450, 5: 750}
    return table.get(next_val, 9999)


def price_shield(add_one: int) -> int:
    return 40


def price_heart() -> int:
    return 120


def price_tetris_time(next_bonus: int) -> int:
    # bonus 1..10
    return 50 + (next_bonus - 1) * 40


class ShopScene(BaseScene):
    def enter(self, mode="story", stage=1, wave=1, **kwargs):
        self.mode = mode
        self.stage = int(stage)
        self.wave = int(wave)

        if not hasattr(self.app, "_run_hearts"):
            self.app._run_hearts = START_LIVES
        if not hasattr(self.app, "_wave_shield_hp"):
            self.app._wave_shield_hp = 0

        self.msg = ""
        self.btns = []
        self.tab_btns = []  # For tab button click handling
        
        # Tab system
        self.current_tab = "upgrades"  # upgrades, books, consumables
        
        self._layout()

    def _layout(self):
        w, h = self.app.screen.get_size()
        self.panel = pg.Rect(w // 2 - 520, h // 2 - 320, 1040, 640)

    def handle_event(self, ev):
        if ev.type == pg.VIDEORESIZE:
            self._layout()

        # Handle tab clicks manually
        if ev.type == pg.MOUSEBUTTONDOWN and ev.button == 1:
            if hasattr(self, 'tab_btns'):
                for tab_rect, tab_id in self.tab_btns:
                    if tab_rect.collidepoint(ev.pos):
                        self._switch_tab(tab_id)
                        return

        for b in self.btns:
            b.handle(ev)

    def update(self, dt):
        pass

    def _wallet(self) -> int:
        sd = self.app.save
        return sd.wallet

    def _set_wallet(self, v: int):
        sd = self.app.save
        sd.wallet = v

    def _buy(self, cost: int) -> bool:
        w = self._wallet()
        if w < cost:
            self.msg = "Not enough coins." if self.app.save.settings.lang == "en" else "Немаш доволно coins."
            return False
        self._set_wallet(w - cost)
        
        # Track first purchase achievement
        check_achievement(self.app.save, "first_purchase", 1)
        
        save(self.app.save)
        self.msg = "Purchased!" if self.app.save.settings.lang == "en" else "Купено!"
        return True

    def _back(self):
        from .hub import WaveHubScene
        change_scene(
            self.app, WaveHubScene(self.app),
            mode=self.mode, stage=self.stage, wave=self.wave,
            success=True, score=0, tetris_coins=0
        )

    def _switch_tab(self, tab: str):
        self.current_tab = tab
        self.msg = ""  # Clear message when switching tabs

    def draw(self, surf):
        app = self.app
        sd = app.save
        colors, fonts = app.colors, app.fonts
        t = TEXT[sd.settings.lang]
        lang = sd.settings.lang

        self.draw_background(surf, colors)
        title = "Shop" if lang == "en" else "Продавница"
        draw_panel(surf, self.panel, colors, title=title, title_font=fonts.ui_bold)

        self.btns = []

        # Wallet display (top right)
        wallet = self._wallet()
        
        # Check coin achievements
        check_achievement(sd, "wealthy", wallet)
        check_achievement(sd, "rich", wallet)
        
        # Check library regular (all 3 books owned)
        if len(sd.owned_books) >= 3:
            check_achievement(sd, "library_regular", len(sd.owned_books))
        
        # Check fully upgraded (all upgrades maxed)
        upgrades = sd.upgrades
        if (upgrades.get("obstacle_slots", 1) >= 5 and
            upgrades.get("fire_rate_lvl", 1) >= 5 and
            upgrades.get("block_hp", 1) >= 5 and
            upgrades.get("tetris_time_bonus", 0) >= 10):
            check_achievement(sd, "fully_upgraded", 1)
        
        wallet_text = f"{wallet} coins"
        wallet_surf = fonts.ui_bold.render(wallet_text, True, colors["accent"])
        wallet_x = self.panel.right - wallet_surf.get_width() - 40
        wallet_y = self.panel.y + 20
        surf.blit(wallet_surf, (wallet_x, wallet_y))

        # Status bar (hearts and shields)
        hearts = getattr(app, "_run_hearts", START_LIVES)
        shield_hp = getattr(app, "_wave_shield_hp", 0)
        
        status_x = self.panel.x + 40
        status_y = self.panel.y + 70
        
        hearts_text = f"Hearts: {hearts}/{START_LIVES}"
        shield_text = f"Shield: {shield_hp}/3"
        
        draw_text(surf, hearts_text, fonts.ui, colors["muted"], (status_x, status_y), max_w=200)
        draw_text(surf, shield_text, fonts.ui, colors["muted"], (status_x + 220, status_y), max_w=200)

        # Tab buttons
        tab_y = self.panel.y + 110
        tab_w = 150
        tab_h = 40
        tab_gap = 10
        tab_x = self.panel.x + 40

        tabs = [
            ("upgrades", "Upgrades" if lang == "en" else "Надградби"),
            ("books", "Books" if lang == "en" else "Книги"),
            ("consumables", "Consumables" if lang == "en" else "Потрошни")
        ]

        tab_btns = []
        for i, (tab_id, tab_name) in enumerate(tabs):
            tab_rect = pg.Rect(tab_x + i * (tab_w + tab_gap), tab_y, tab_w, tab_h)
            
            # Draw tab background
            if self.current_tab == tab_id:
                pg.draw.rect(surf, colors["panel2"], tab_rect, border_radius=8)
                pg.draw.rect(surf, colors["accent"], tab_rect, width=2, border_radius=8)
            else:
                pg.draw.rect(surf, colors["panel"], tab_rect, border_radius=8)
                pg.draw.rect(surf, colors["line"], tab_rect, width=2, border_radius=8)
            
            # Draw tab text
            tab_text = fonts.ui_bold.render(tab_name, True, colors["text"])
            text_rect = tab_text.get_rect(center=tab_rect.center)
            surf.blit(tab_text, text_rect)
            
            # Store tab button for click handling (we'll handle clicks manually)
            tab_btns.append((tab_rect, tab_id))

        # Content area
        content_y = tab_y + tab_h + 30
        content_h = self.panel.bottom - content_y - 140

        # Draw content based on current tab
        if self.current_tab == "upgrades":
            self._draw_upgrades_tab(surf, content_y, content_h, colors, fonts, lang, sd)
        elif self.current_tab == "books":
            self._draw_books_tab(surf, content_y, content_h, colors, fonts, lang, sd)
        elif self.current_tab == "consumables":
            self._draw_consumables_tab(surf, content_y, content_h, colors, fonts, lang, sd, app)

        # Message display
        if self.msg:
            msg_y = self.panel.bottom - 110
            draw_text(surf, self.msg, fonts.ui_bold, colors["accent"], (self.panel.x + 40, msg_y), max_w=self.panel.w - 80)

        # Back button
        back = pg.Rect(self.panel.x + 40, self.panel.bottom - 70, 180, 50)
        self.btns.append(Button(back, t.get("back", "Back"), self._back))

        # Draw all buttons
        for b in self.btns:
            b.draw(surf, fonts.ui_bold, colors, hover_state(b.rect))
        
        # Store tab buttons for click handling in handle_event
        self.tab_btns = tab_btns

    def _draw_card(self, surf, rect, title, description, price_text, status_text, on_buy, enabled, colors, fonts):
        """Draw a shop item card"""
        # Card background
        if enabled:
            bg_color = colors["panel"]
            border_color = colors["line"]
        else:
            bg_color = (colors["panel"][0] // 2, colors["panel"][1] // 2, colors["panel"][2] // 2)
            border_color = colors["muted"]
        
        # Hover effect
        mx, my = pg.mouse.get_pos()
        if rect.collidepoint(mx, my) and enabled:
            bg_color = colors["panel2"]
            border_color = colors["accent"]
        
        pg.draw.rect(surf, bg_color, rect, border_radius=12)
        pg.draw.rect(surf, border_color, rect, width=2, border_radius=12)
        
        # Content
        y = rect.y + 20
        x = rect.x + 20
        
        # Title
        title_color = colors["text"] if enabled else colors["muted"]
        y = draw_text(surf, title, fonts.ui_bold, title_color, (x, y), max_w=rect.w - 40)
        y += 10
        
        # Description
        desc_color = colors["muted"] if enabled else (colors["muted"][0] // 2, colors["muted"][1] // 2, colors["muted"][2] // 2)
        y = draw_text(surf, description, fonts.ui, desc_color, (x, y), max_w=rect.w - 40)
        y += 15
        
        # Status (if provided)
        if status_text:
            y = draw_text(surf, status_text, fonts.ui, colors["accent"], (x, y), max_w=rect.w - 40)
            y += 10
        
        # Price and buy button at bottom
        btn_w = 120
        btn_h = 40
        btn_x = rect.right - btn_w - 20
        btn_y = rect.bottom - btn_h - 15
        
        # Price text
        price_y = btn_y + (btn_h // 2) - (fonts.ui_bold.get_height() // 2)
        draw_text(surf, price_text, fonts.ui_bold, colors["text"] if enabled else colors["muted"], (x, price_y), max_w=rect.w - btn_w - 60)
        
        # Buy button
        if enabled and on_buy:
            btn_rect = pg.Rect(btn_x, btn_y, btn_w, btn_h)
            self.btns.append(Button(btn_rect, "Buy" if self.app.save.settings.lang == "en" else "Купи", on_buy))

    def _draw_upgrades_tab(self, surf, content_y, content_h, colors, fonts, lang, sd):
        """Draw upgrades tab content"""
        up = sd.upgrades if isinstance(sd.upgrades, dict) else {}
        slots = int(up.get("obstacle_slots", 1))
        fire = int(up.get("fire_rate_lvl", 1))
        bhp = int(up.get("block_hp", 1))
        tbonus = int(up.get("tetris_time_bonus", 0))
        tbonus = max(0, min(10, tbonus))
        
        # Card layout: 2 columns, 2 rows
        card_w = 460
        card_h = 160
        gap = 20
        start_x = self.panel.x + 50
        start_y = content_y
        
        cards = []
        
        # More walls
        def buy_slots():
            if slots >= 5:
                return
            c = price_obstacle_slots(slots + 1)
            if self._buy(c):
                sd.upgrades["obstacle_slots"] = slots + 1
                save(sd)
        
        next_slots = min(5, slots + 1)
        cost_slots = price_obstacle_slots(next_slots) if next_slots != slots else 0
        
        cards.append({
            "title": "More Walls" if lang == "en" else "Повеќе ѕидови",
            "desc": "Increase wall capacity for building phase" if lang == "en" else "Зголеми капацитет на ѕидови за фаза градење",
            "price": f"Cost: {cost_slots}" if lang == "en" else f"Цена: {cost_slots}",
            "status": f"Level: {slots}/5" if lang == "en" else f"Ниво: {slots}/5",
            "callback": buy_slots,
            "enabled": slots < 5
        })
        
        # Fire rate
        def buy_fire():
            c = price_fire_rate(fire + 1)
            if self._buy(c):
                sd.upgrades["fire_rate_lvl"] = fire + 1
                save(sd)
        
        cfire = price_fire_rate(fire + 1)
        
        cards.append({
            "title": "Faster Shooting" if lang == "en" else "Побрзо пукање",
            "desc": "Increase firing speed" if lang == "en" else "Зголеми брзина на пукање",
            "price": f"Cost: {cfire}" if lang == "en" else f"Цена: {cfire}",
            "status": f"Level: {fire}" if lang == "en" else f"Ниво: {fire}",
            "callback": buy_fire,
            "enabled": True
        })
        
        # Block HP
        def buy_bhp():
            if bhp >= 5:
                return
            c = price_block_hp(bhp + 1)
            if self._buy(c):
                sd.upgrades["block_hp"] = bhp + 1
                save(sd)
        
        next_bhp = min(5, bhp + 1)
        cbhp = price_block_hp(next_bhp) if next_bhp != bhp else 0
        
        cards.append({
            "title": "Wall HP" if lang == "en" else "HP на ѕид",
            "desc": "Increase wall hit points" if lang == "en" else "Зголеми HP на ѕидови",
            "price": f"Cost: {cbhp}" if lang == "en" else f"Цена: {cbhp}",
            "status": f"Level: {bhp}/5" if lang == "en" else f"Ниво: {bhp}/5",
            "callback": buy_bhp,
            "enabled": bhp < 5
        })
        
        # Tetris time bonus
        def buy_tetris_time():
            if tbonus >= 10:
                return
            c = price_tetris_time(tbonus + 1)
            if self._buy(c):
                sd.upgrades["tetris_time_bonus"] = tbonus + 1
                save(sd)
        
        next_tb = min(10, tbonus + 1)
        ctb = price_tetris_time(next_tb) if next_tb != tbonus else 0
        
        cards.append({
            "title": "Tetris Time Bonus" if lang == "en" else "Tetris време бонус",
            "desc": "Extra time for building phase" if lang == "en" else "Дополнително време за фаза градење",
            "price": f"Cost: {ctb}" if lang == "en" else f"Цена: {ctb}",
            "status": f"+{tbonus}s/10s",
            "callback": buy_tetris_time,
            "enabled": tbonus < 10
        })
        
        # Draw cards in grid
        for i, card in enumerate(cards):
            row = i // 2
            col = i % 2
            x = start_x + col * (card_w + gap)
            y = start_y + row * (card_h + gap)
            rect = pg.Rect(x, y, card_w, card_h)
            
            self._draw_card(
                surf, rect,
                card["title"],
                card["desc"],
                card["price"],
                card["status"],
                card["callback"],
                card["enabled"],
                colors, fonts
            )

    def _draw_books_tab(self, surf, content_y, content_h, colors, fonts, lang, sd):
        """Draw books tab content"""
        owned_books = getattr(sd, 'owned_books', [])
        
        def buy_book(book_id: int, cost: int):
            if book_id in owned_books:
                return
            if self._buy(cost):
                if not hasattr(sd, 'owned_books'):
                    sd.owned_books = []
                sd.owned_books.append(book_id)
                save(sd)
        
        # Card layout: 3 books in a row
        card_w = 310
        card_h = 200
        gap = 20
        start_x = self.panel.x + 50
        start_y = content_y
        
        books = [
            {
                "id": 1,
                "title": "Book 1 - Digital Explorer" if lang == "en" else "Книга 1 - Digital Explorer",
                "desc": "Hints for levels 1-5" if lang == "en" else "Hints за нивоа 1-5",
                "cost": 200
            },
            {
                "id": 2,
                "title": "Book 2 - Password Guardian" if lang == "en" else "Книга 2 - Password Guardian",
                "desc": "Hints for levels 6-10" if lang == "en" else "Hints за нивоа 6-10",
                "cost": 300
            },
            {
                "id": 3,
                "title": "Book 3 - Cyber Hero" if lang == "en" else "Книга 3 - Cyber Hero",
                "desc": "Hints for levels 11-15" if lang == "en" else "Hints за нивоа 11-15",
                "cost": 400
            }
        ]
        
        for i, book in enumerate(books):
            x = start_x + i * (card_w + gap)
            y = start_y
            rect = pg.Rect(x, y, card_w, card_h)
            
            book_owned = book["id"] in owned_books
            status = "OWNED" if book_owned else ""
            
            self._draw_card(
                surf, rect,
                book["title"],
                book["desc"],
                f"Cost: {book['cost']}" if lang == "en" else f"Цена: {book['cost']}",
                status,
                lambda bid=book["id"], cost=book["cost"]: buy_book(bid, cost),
                not book_owned,
                colors, fonts
            )

    def _draw_consumables_tab(self, surf, content_y, content_h, colors, fonts, lang, sd, app):
        """Draw consumables tab content"""
        hearts = getattr(app, "_run_hearts", START_LIVES)
        shield_hp = getattr(app, "_wave_shield_hp", 0)
        
        # Card layout: 2 large cards
        card_w = 460
        card_h = 200
        gap = 40
        start_x = self.panel.x + 50
        start_y = content_y
        
        # Heart buyback
        def buy_heart():
            if getattr(app, "_run_hearts", START_LIVES) >= START_LIVES:
                return
            if self._buy(price_heart()):
                app._run_hearts = min(START_LIVES, app._run_hearts + 1)
        
        heart_rect = pg.Rect(start_x, start_y, card_w, card_h)
        self._draw_card(
            surf, heart_rect,
            "Buy Back Heart" if lang == "en" else "Купи срце назад",
            "Restore one lost heart" if lang == "en" else "Врати едно изгубено срце",
            f"Cost: {price_heart()}" if lang == "en" else f"Цена: {price_heart()}",
            f"Current: {hearts}/{START_LIVES}",
            buy_heart,
            hearts < START_LIVES,
            colors, fonts
        )
        
        # Shield
        def buy_shield():
            if getattr(app, "_wave_shield_hp", 0) >= 3:
                return
            if self._buy(price_shield(1)):
                app._wave_shield_hp = min(3, app._wave_shield_hp + 1)
        
        shield_rect = pg.Rect(start_x + card_w + gap, start_y, card_w, card_h)
        self._draw_card(
            surf, shield_rect,
            "Shield" if lang == "en" else "Штит",
            "Temporary protection for this wave only" if lang == "en" else "Привремена заштита само за овој бран",
            f"Cost: {price_shield(1)}" if lang == "en" else f"Цена: {price_shield(1)}",
            f"Current: {shield_hp}/3  •  Max: 3",
            buy_shield,
            shield_hp < 3,
            colors, fonts
        )
