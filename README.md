# Cyber Defender: Block & Blast (Pygame)

A kid-friendly arcade game that mixes **Tetris-style firewall building** with **Space-Invaders-style defense**, teaching internet safety through quick scenario “cards” that affect gameplay.

---

## 🚀 Quick Launch (Windows EXE — No Python required)

A pre-built Windows executable is included in the `dist\CyberDefender\` folder.

1. Open the `dist\CyberDefender\` folder
2. Double-click **`CyberDefender.exe`** to start the game

> **Important:** Do **not** move `CyberDefender.exe` out of its folder.  
> It depends on the files inside `_internal\` to run correctly.  
> To share the game, zip the entire `dist\CyberDefender\` folder and send it as-is.

---

## 🎥 Included Video

The file **`Screen Recording 2026-02-10 130238.mp4`** in the project root is a gameplay recording that demonstrates the game in action — showing the main menu, Tetris/Space Invaders hybrid gameplay, the educational scenario cards, and a boss encounter. You can watch it to get a quick overview of how the game looks and plays before running it.

---

- **Story Mode:** 4 Worlds × 4 stages (3 stages + boss) ~15–20 minutes total
- **Endless Mode:** infinite waves with increasing difficulty
- **Progression:** XP ranks, coins, cosmetics, achievements
- **Save system:** JSON (coins, unlocks, highscores, achievements, settings)
- **Localization:** Македонски (default) + English (toggle in Settings)

---

## 1) Install

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## 2) Run

```bash
python main.py
```

---

## Controls (Gameplay)

**Ship / Defense Zone**
- **Left / Right:** move ship
- **Space:** shoot
- **Esc:** pause

**Build Zone (Firewall / Tetris)**
- **Down:** soft drop
- **Up / X:** rotate clockwise
- **Z:** rotate counter-clockwise
- **C:** hold piece

**Menus**
- Mouse only

---

## Educational “Cards”
Between waves you’ll get 1–2 quick scenario cards with **3 choices**:
- **Safe to Share**
- **Private**
- **Never Share**

Your choice immediately affects gameplay:
- Correct → better blocks/power-ups, more coins/XP
- Wrong → “junk blocks” or debuffs (lag, pop-up fog, fake reward trap)

---

## How to add assets later
The game currently draws **placeholder pixel sprites** in code.
You can swap them later by adding PNGs to:
- `assets/images/` and updating `src/assets.py`

---

## Project structure

```
cyber_defender_block_blast/
  main.py
  requirements.txt
  README.md
  data/
    save.json               (auto-created on first run)
  src/
    core.py
    assets.py
    localization.py
    save_system.py
    constants.py
    ui.py
    scenes/
      base.py
      menu.py
      settings.py
      achievements.py
      credits.py
      storymap.py
      game.py
    gameplay/
      tetris.py
      invaders.py
      scenarios.py
      progression.py
```

---

## Notes for teachers/parents
- The game avoids violence: enemies are “Scam Invaders” and shots are “security signals”.
- Boss stages are mission-based (clear lines + use correct security action).
- Kids learn: **privacy**, **password strength**, **DM safety**, **phishing/pop-ups** via consequences inside the game.
