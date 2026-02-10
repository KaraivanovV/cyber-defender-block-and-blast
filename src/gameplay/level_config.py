from __future__ import annotations
from typing import Dict, Any, List, Tuple

# Enemy type definitions with stats
ENEMY_TYPES = {
    "basic": {
        "hp": 1,
        "speed_mult": 1.6,
        "shoot_mult": 0.6,
        "color": (100, 255, 100),  # Green
        "icon": "●"
    },
    "fast": {
        "hp": 1,
        "speed_mult": 2.2,
        "shoot_mult": 0.5,
        "color": (255, 255, 100),  # Yellow
        "icon": "*"
    },
    "armored": {
        "hp": 2,
        "speed_mult": 1.4,
        "shoot_mult": 0.5,
        "color": (100, 150, 255),  # Blue
        "icon": "#"
    },
    "shooter": {
        "hp": 1,
        "speed_mult": 1.5,
        "shoot_mult": 0.25,
        "color": (255, 80, 80),  # Red
        "icon": ">"
    },
    "elite": {
        "hp": 3,
        "speed_mult": 1.8,
        "shoot_mult": 0.3,
        "color": (200, 100, 255),  # Purple
        "icon": "@"
    },
    "berserker": {
        "hp": 2,
        "speed_mult": 2.5,
        "shoot_mult": 0.2,
        "color": (255, 140, 0),  # Orange
        "icon": "!"
    }
}

# Boss levels (shifted from 3,6,9,12,15 to 8,11,14,17,20)
BOSS_LEVELS = [8, 11, 14, 17, 20]

# Tutorial levels (0-5)
TUTORIAL_LEVELS = [0, 1, 2, 3, 4, 5]

# Level configurations
LEVEL_CONFIGS = {
    # ============ TUTORIAL LEVELS (0-5) ============
    
    0: {  # Tutorial: Unwinnable attack
        "tutorial": True,
        "unwinnable": True,
        "skip_build": True,  # No firewall yet
        "rows": 6,  # Increased to 6 rows
        "cols": 10,  # Increased to 10 columns for overwhelming attack
        "enemy_type": ["basic", "fast", "armored", "shooter"],  # Mixed enemy types
        "speed": 3.0,  # Very fast
        "mixed": True,  # Enable mixed enemy types
        "splash_before": {
            "en": "OH NO! WE'RE UNDER ATTACK!\n\nCyber enemies are invading our town!\nDefend yourself!\n\n[Press SPACE to shoot]\n[Use ← → to move]",
            "mk": "ОХ НЕ! НИ НАПАДААТ!\n\nКибер непријатели го нападаат нашиот град!\nБрани се!\n\n[Притисни SPACE за пукање]\n[Користи ← → за движење]"
        },
        "splash_after": {
            "en": "THE TOWN HAS BEEN DESTROYED!\n\nThe enemies destroyed:\n- The Firewall (our protection)\n- The Shop (where we get stronger)\n- The Library (where we learn)\n\nWe need to rebuild everything!",
            "mk": "ГРАДОТ Е УНИШТЕН!\n\nНепријателите уништија:\n- Firewall (наша заштита)\n- Продавница (каде станувам посилен)\n- Библиотека (каде учиме)\n\nТреба да го обновиме се!"
        },
        "splash_after_2": {  # NEW: Second splash explaining bricks
            "en": "HOW TO REBUILD\n\nTo rebuild our defense system,\nwe need to collect BRICKS!\n\nDefeat enemies to make them drop bricks.\nCollect the bricks by moving over them.\n\nLet's start collecting!",
            "mk": "КАКО ДА ОБНОВИМЕ\n\nЗа да го обновиме нашиот систем,\nтреба да собереме ТУЛИ!\n\nПорази ги непријателите за да пуштаат тули.\nСобери ги тулите со движење преку нив.\n\nАјде да собираме!"
        }
    },
    
    1: {  # Tutorial: Collect bricks (combat only, no firewall yet)
        "tutorial": True,
        "skip_build": True,  # No firewall yet - it's destroyed
        "rows": 2,
        "cols": 5,
        "enemy_type": "basic",
        "speed": 1.2,
        "mixed": False,
        "drop_bricks": True,
        "splash_before": {
            "en": "COLLECT THE BRICKS!\n\nDefeat enemies and they will drop bricks!\nMove over the bricks to collect them.\n\nWe need bricks to rebuild our defenses!\n\n[SPACE to shoot] [← → to move]",
            "mk": "СОБЕРИ ГИ ТУЛИТЕ!\n\nПорази ги непријателите и ќе пуштаат тули!\nДвижи се преку тулите за да ги собереш.\n\nНи требаат тули за да го обновиме одбраната!\n\n[SPACE за пукање] [← → за движење]"
        },
        "splash_after": {
            "en": "BRICKS COLLECTED!\n\nGreat job! You collected the bricks!\n\nNow we can use them to rebuild\nour defense system with Tetris blocks!\n\nNext: Learn about the Firewall!",
            "mk": "ТУЛИТЕ СЕ СОБРАНИ!\n\nОдлична работа! Ги собра тулите!\n\nСега можеме да ги користиме за да го\nобновиме нашиот систем со Tetris блокови!\n\nСледно: Научи за Firewall!"
        }
    },
    
    2: {  # Tutorial: Build firewall then fight
        "tutorial": True,
        "rows": 2,
        "cols": 5,
        "enemy_type": "basic",
        "speed": 1.3,
        "mixed": False,
        "firewall_explanation": {  # NEW: Show before building
            "en": "ABOUT THE FIREWALL\n\nThe Firewall is your main defense!\nIt blocks enemy attacks.\n\nYou'll build it using Tetris blocks.\nFill rows to make it stronger!\n\nControls:\n[← →] Move pieces\n[Q E] Rotate\n[↓] Drop faster",
            "mk": "ЗА FIREWALL\n\nFirewall е твојата главна одбрана!\nГи блокира нападите.\n\nЌе го изградиш со Tetris блокови.\nПополни редови за да биде посилен!\n\nКонтроли:\n[← →] Движење\n[Q E] Ротација\n[↓] Побрзо паѓање"
        },
        "splash_before": {
            "en": "BUILD THE FIREWALL!\n\nNow it's time to build!\nUse the Tetris blocks to create your wall.\n\nThen defend against enemies!",
            "mk": "ИЗГРАДИ ГО FIREWALL!\n\nСега е време да градиме!\nКористи ги Tetris блоковите за да го направиш ѕидот.\n\nПотоа брани се од непријатели!"
        },
        "splash_mid": {  # NEW: Show after build, before fight
            "en": "WALL PLACEMENT!\n\nYou can move your firewall left/right\nto position it strategically!\n\nControls:\n[Q / E] Move wall left/right\n[ENTER] Start battle",
            "mk": "ПОСТАВУВАЊЕ НА ЅИДОТ!\n\nМожеш да го поместиш твојот firewall лево/десно\nза да го позиционираш стратешки!\n\nКонтроли:\n[Q / E] Помести ѕид лево/десно\n[ENTER] Почни битка"
        },
        "splash_after": {
            "en": "FIREWALL WORKS!\n\nGreat! You built the wall and\ndefended against the attack!\n\nNext: Rebuild the Shop!",
            "mk": "FIREWALL РАБОТИ!\n\nОдлично! Го изгради ѕидот и\nсе одбрани од нападот!\n\nСледно: Обнови ја Продавницата!"
        }
    },
    
    3: {  # Tutorial: Build shop then fight and collect bricks
        "tutorial": True,
        "rows": 3,
        "cols": 6,
        "enemy_type": "basic",
        "speed": 1.4,
        "mixed": False,
        "drop_bricks": True,
        "bricks_required": 5,  # Need 5 bricks to rebuild the shop
        "splash_before": {
            "en": "BUILD THE SHOP!\n\nThe Shop lets you buy upgrades!\n\nBuild your firewall, then collect\n5 BRICKS to rebuild the shop!",
            "mk": "ИЗГРАДИ ЈА ПРОДАВНИЦАТА!\n\nПродавницата ти дозволува да купуваш надградби!\n\nИзгради го firewall, па собери\n5 ТУЛИ за да ја обновиш продавницата!"
        },
        "splash_after": {
            "en": "SHOP REBUILT!\n\nGreat! You collected the bricks\nand rebuilt the shop!\n\nNow you can buy upgrades!\n\nNext: Rebuild the Library!",
            "mk": "ПРОДАВНИЦАТА Е ОБНОВЕНА!\n\nОдлично! Ги собра тулите\nи ја обнови продавницата!\n\nСега можеш да купуваш надградби!\n\nСледно: Обнови ја Библиотеката!"
        }
    },
    
    4: {  # Tutorial: Build library then fight and collect bricks
        "tutorial": True,
        "rows": 4,
        "cols": 7,
        "enemy_type": "basic",
        "speed": 1.5,
        "mixed": False,
        "drop_bricks": True,
        "bricks_required": 7,  # Need 7 bricks to rebuild the library
        "splash_before": {
            "en": "BUILD THE LIBRARY!\n\nThe Library holds all our knowledge!\n\nBuild your firewall, then collect\n7 BRICKS to rebuild the library!",
            "mk": "ИЗГРАДИ ЈА БИБЛИОТЕКАТА!\n\nБиблиотеката го чува нашето знаење!\n\nИзгради го firewall, па собери\n7 ТУЛИ за да ја обновиш библиотеката!"
        },
        "splash_after": {
            "en": "LIBRARY REBUILT!\n\nExcellent! You collected the bricks\nand rebuilt the library!\n\nYou can now access it from the hub\nto answer quiz questions and earn rewards!",
            "mk": "БИБЛИОТЕКАТА Е ОБНОВЕНА!\n\nОдлично! Ги собра тулите\nи ја обнови библиотеката!\n\nСега можеш да пристапиш до неа од хаб\nза да одговараш на прашања и да заработиш награди!"
        }
    },
    
    5: {  # Tutorial: Final tutorial level
        "tutorial": True,
        "tutorial_final": True,
        "rows": 3,
        "cols": 7,
        "enemy_type": "basic",
        "speed": 1.5,
        "mixed": False,
        "splash_before": {
            "en": "FINAL TUTORIAL LEVEL!\n\nAll systems are online!\nUse everything you've learned!\n\nFirewall protects you\nShop makes you stronger\nLibrary gives rewards\n\nWin this to unlock the main game!",
            "mk": "ПОСЛЕДНО НИВО НА ТУТОРИЈАЛ!\n\nСите системи се активни!\nКористи го сето што научи!\n\nFirewall те штити\nПродавницата те прави посилен\nБиблиотеката дава награди\n\nПобеди за да го отклучиш главниот дел!"
        },
        "splash_after": {
            "en": "TUTORIAL COMPLETE!\n\nYou are now a Cyber Defender!\n\nProgress saved - you won't need\nto replay the tutorial!\n\nThe real adventure begins!\n\nGood luck, Defender!",
            "mk": "ТУТОРИЈАЛОТ Е ЗАВРШЕН!\n\nСега си Кибер Бранител!\n\nПрогресот е зачуван - нема да треба\nда го повториш туторијалот!\n\nВистинската авантура почнува!\n\nСреќно, Бранителе!"
        }
    },
    
    # ============ MAIN GAME LEVELS (6-20) ============
    # Original levels 1-15 shifted to 6-20
    
    6: {  # Was Level 1
        "rows": 4,
        "cols": 8,
        "enemy_type": "basic",
        "speed": 1.8,
        "mixed": False
    },
    7: {  # Was Level 2
        "rows": 4,
        "cols": 9,
        "enemy_type": "basic",
        "speed": 2.0,
        "mixed": False
    },
    8: {  # BOSS: The Fake Prize Ship (was Level 3)
        "boss": True,
        "boss_name": "boss_fake_prize",
        "boss_hp": 60,
        "boss_pattern": "sweep",
        "boss_sprite": "boss_first",
        "minion_type": "basic",
        "minion_interval": 5.0,
        "splash_before": {
            "en": "THE LIBRARIAN\n\n\"Defender! I've been researching\nour ancient archives...\n\nI found something that might help\nyou against the upcoming boss!\n\nLet me show you...\"",
            "mk": "БИБЛИОТЕКАРОТ\n\n\"Бранителе! Ги истражував\nнашите стари архиви...\n\nНајдов нешто што може да ти помогне\nпротив надоаѓачкиот бос!\n\nДозволи да ти покажам...\""
        },
        "splash_before_2": {
            "en": "THE LIBRARIAN\n\n\"This technique is called DASH!\n\nPress SHIFT to dash!\n\nYou'll move quickly to dodge attacks!\nBut it requires energy to recharge.\n\nUse it wisely in battle!\"",
            "mk": "БИБЛИОТЕКАРОТ\n\n\"Оваа техника се вика DASH!\n\nПритисни SHIFT за dash!\n\nБрзо ќе се движиш за да избегаш напади!\nНо потребна е енергија за полнење.\n\nКористи ја мудро во битка!\""
        },
        "splash_before_3": {
            "en": "THE LIBRARIAN\n\n\"The boss ahead is powerful...\n\nCombine your firewall, shooting,\nand this new dash ability!\n\nBOSS FIGHT!\n\nGood luck, Defender!\nI believe in you!\"",
            "mk": "БИБЛИОТЕКАРОТ\n\n\"Босот што следува е моќен...\n\nКомбинирај го твојот firewall, пукање,\nи оваа нова dash способност!\n\nБОС БИТКА!\n\nСреќно, Бранителе!\nВерувам во тебе!\""
        }
    },
    
    9: {  # Was Level 4
        "rows": 5,
        "cols": 9,
        "enemy_type": "fast",
        "speed": 2.1,
        "mixed": False
    },
    10: {  # Was Level 5
        "rows": 5,
        "cols": 10,
        "enemy_type": "armored",
        "speed": 2.3,
        "mixed": False
    },
    11: {  # BOSS: The Phishing Mothership (was Level 6)
        "boss": True,
        "boss_name": "boss_phishing",
        "boss_hp": 100,
        "boss_pattern": "orbital",
        "boss_sprite": "boss_2",  # Second boss sprite
        "boss_size": 150,  # Larger than default (120)
        "minion_type": "armored",
        "minion_interval": 6.0
    },
    
    12: {  # Was Level 7
        "rows": 5,
        "cols": 11,
        "enemy_type": ["fast", "fast", "armored", "armored", "shooter"],
        "speed": 2.4,
        "mixed": True
    },
    13: {  # Was Level 8
        "rows": 6,
        "cols": 10,
        "enemy_type": "shooter",
        "speed": 2.5,
        "mixed": False
    },
    14: {  # BOSS: The DM Magnet (was Level 9)
        "boss": True,
        "boss_name": "boss_chat",
        "boss_hp": 140,
        "boss_pattern": "zigzag",
        "boss_sprite": "boss_3",  # Third boss sprite
        "minion_type": ["fast", "armored", "shooter"],
        "minion_interval": 5.0
    },
    
    15: {  # Was Level 10
        "rows": 6,
        "cols": 11,
        "enemy_type": "elite",
        "speed": 2.6,
        "mixed": False
    },
    16: {  # Was Level 11
        "rows": 6,
        "cols": 11,
        "enemy_type": ["shooter", "shooter", "elite", "elite", "berserker", "berserker"],
        "speed": 2.7,
        "mixed": True
    },
    17: {  # BOSS: The Profile Snatcher (was Level 12)
        "boss": True,
        "boss_name": "boss_privacy",
        "boss_hp": 170,
        "boss_pattern": "teleport",
        "boss_sprite": "boss_4",  # Fourth boss sprite
        "minion_type": ["elite", "shooter"],
        "minion_interval": 7.0
    },
    
    18: {  # Was Level 13
        "rows": 6,
        "cols": 12,
        "enemy_type": "berserker",
        "speed": 2.8,
        "mixed": False
    },
    19: {  # Was Level 14
        "rows": 7,
        "cols": 11,
        "enemy_type": ["fast", "shooter", "elite", "elite", "berserker", "berserker", "berserker"],
        "speed": 2.9,
        "mixed": True
    },
    20: {  # BOSS: The Cyber Overlord - FINAL BOSS (was Level 15)
        "boss": True,
        "boss_name": "boss_cyber_overlord",
        "boss_hp": 300,
        "boss_pattern": "multi_phase",
        "boss_sprite": "final_boss",  # Final boss sprite
        "boss_size": 180,  # Larger than all other bosses for epic final battle
        "minion_type": ["fast", "armored", "shooter", "elite", "berserker"],
        "minion_interval": 4.0,
        "phases": 3
    }
}

def get_level_config(stage: int) -> Dict[str, Any]:
    """Get configuration for a specific level."""
    return LEVEL_CONFIGS.get(stage, LEVEL_CONFIGS[6])  # Default to level 6 (first main game level)

def is_boss_level(stage: int) -> bool:
    """Check if a stage is a boss level."""
    return stage in BOSS_LEVELS

def is_tutorial_level(stage: int) -> bool:
    """Check if a stage is a tutorial level."""
    return stage in TUTORIAL_LEVELS

def get_enemy_type_stats(enemy_type: str) -> Dict[str, Any]:
    """Get stats for a specific enemy type."""
    return ENEMY_TYPES.get(enemy_type, ENEMY_TYPES["basic"])
