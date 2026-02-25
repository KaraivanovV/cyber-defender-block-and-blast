# Cyber Defender: Block & Blast (Pygame)

A kid-friendly arcade game that mixes **Tetris-style firewall building** with **Space-Invaders-style defense**, teaching internet safety through quick scenario "cards" that affect gameplay.

Игра прилагодена за деца која комбинира **градење заштитен ѕид во Tetris стил** со **одбрана во Space Invaders стил**, учејќи ги децата за интернет безбедност преку сценарио „картички" кои влијаат на играта.

---

## Play Online / Играј Онлајн

**No install needed — runs directly in your browser.**

**Без инсталација — работи директно во прелистувачот.**

> **Link / Линк:** [https://karaivanovv.github.io/cyber-defender-block-and-blast/](https://karaivanovv.github.io/cyber-defender-block-and-blast/)

### How to play online / Како да играш онлајн

**English**
1. Click the link above
2. Wait **30–60 seconds** for the game to load (Python runtime downloads in background — this only happens once per browser)
3. When the game canvas appears, click on it once to focus it, then use keyboard controls to play
4. Recommended browsers: **Chrome** or **Firefox**
5. Note: progress is **not saved** in the browser version — each session starts fresh

**Македонски**
1. Кликни на линкот горе
2. Почекај **30–60 секунди** додека играта се вчитува (Python рантајмот се симнува во позадина — ова се случува само еднаш по прелистувач)
3. Кога ќе се појави платното на играта, кликни еднаш на него за фокус, а потоа користи ги контролите на тастатурата
4. Препорачани прелистувачи: **Chrome** или **Firefox**
5. Напомена: напредокот **не се зачувува** во веб верзијата — секоја сесија почнува одново

---



## 🚀 Quick Launch (Windows EXE — No Python required) / Брзо Стартување (Windows EXE — без Python)

**🇬🇧 English**

A pre-built Windows executable is included in the `dist\CyberDefender\` folder.

1. Open the `dist\CyberDefender\` folder
2. Double-click **`CyberDefender.exe`** to start the game

> **Important:** Do **not** move `CyberDefender.exe` out of its folder.  
> It depends on the files inside `_internal\` to run correctly.  
> To share the game, zip the entire `dist\CyberDefender\` folder and send it as-is.

**🇲🇰 Македонски**

Готова Windows апликација е вклучена во папката `dist\CyberDefender\`.

1. Отвори ја папката `dist\CyberDefender\`
2. Двојно кликни на **`CyberDefender.exe`** за да ја стартуваш играта

> **Важно:** НЕ местувај го `CyberDefender.exe` надвор од неговата папка.  
> Тој зависи од датотеките во `_internal\` за да работи правилно.  
> За да ја споделиш играта, архивирај ја целата папка `dist\CyberDefender\` и испрати ја таква.

---

## 🎥 Included Video / Вклучено Видео

**🇬🇧 English**

The file **`Screen Recording 2026-02-10 130238.mp4`** in the project root is a gameplay recording that demonstrates the game in action — showing the main menu, Tetris/Space Invaders hybrid gameplay, the educational scenario cards, and a boss encounter. You can watch it to get a quick overview of how the game looks and plays before running it.

**🇲🇰 Македонски**

Датотеката **`Screen Recording 2026-02-10 130238.mp4`** во главната папка е снимка од игра која го прикажува играњето — главното мени, хибридниот Tetris/Space Invaders режим, едукативните сценарио картички и средба со шеф. Можете да ја гледате за брз преглед на тоа како изгледа и се игра пред да ја стартувате.

---

## Game Features / Карактеристики на играта

- **Story Mode / Приказна:** 4 светови × 4 нивоа (3 нивоа + шеф) ~15–20 минути
- **Endless Mode / Бесконечен режим:** бесконечни бранови со зголемена тежина
- **Progression / Прогрес:** XP рангови, монети, козметика, достигнувања
- **Save system / Систем за зачувување:** JSON (монети, отклучувања, рекорди, достигнувања, поставки)
- **Localization / Јазик:** Македонски (стандардно) + English (промени во Поставки)

---

## 1) Install / Инсталација

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## 2) Run / Стартување

```bash
python main.py
```

---

## Controls (Gameplay) / Контроли (Играње)

**Ship / Defense Zone — Брод / Одбранбена зона**
- **Left / Right — Лево / Десно:** move ship / движење на бродот
- **Space — Спејс:** shoot / пукање
- **Esc:** pause / пауза

**Build Zone (Firewall / Tetris) — Зона за градење (Заштитен ѕид / Tetris)**
- **Down — Долу:** soft drop / бавно спуштање
- **Up / X — Горе / X:** rotate clockwise / ротација по часовникот
- **Z:** rotate counter-clockwise / ротација против часовникот
- **C:** hold piece / задржување парче

**Menus / Менија**
- Mouse only / Само глушец

---

## Educational "Cards" / Едукативни „Картички"

**🇬🇧 English**

Between waves you'll get 1–2 quick scenario cards with **3 choices**:
- **Safe to Share**
- **Private**
- **Never Share**

Your choice immediately affects gameplay:
- Correct → better blocks/power-ups, more coins/XP
- Wrong → "junk blocks" or debuffs (lag, pop-up fog, fake reward trap)

**🇲🇰 Македонски**

Помеѓу бранови ќе добиеш 1–2 брзи сценарио картички со **3 избори**:
- **Безбедно за споделување**
- **Приватно**
- **Никогаш не споделувај**

Твојот избор веднаш влијае на играта:
- Точно → подобри блокови/моќ, повеќе монети/XP
- Погрешно → „ѓубре блокови" или дебафови (задоцнување, маглa од реклами, лажна награда)

---

## Notes for Teachers / Parents — Белешки за наставници / родители

**🇬🇧 English**
- The game avoids violence: enemies are "Scam Invaders" and shots are "security signals".
- Boss stages are mission-based (clear lines + use correct security action).
- Kids learn: **privacy**, **password strength**, **DM safety**, **phishing/pop-ups** via consequences inside the game.

**🇲🇰 Македонски**
- Играта избегнува насилство: непријателите се „Измами" а куршумите се „сигнали за безбедност".
- Нивоата со шефови се мисиски (исчисти линии + користи точна акција за безбедност).
- Децата учат: **приватност**, **јачина на лозинка**, **безбедност во пораки**, **фишинг/реклами** преку последиции во играта.
