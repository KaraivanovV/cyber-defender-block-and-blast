"""
Achievement system for Cyber Defender game.
Defines all achievements and provides tracking/unlocking functionality.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .save_system import SaveData


@dataclass
class Achievement:
    """Represents a single achievement"""
    id: str
    name_en: str
    name_mk: str
    desc_en: str
    desc_mk: str
    category: str
    requirement: int = 1  # How many times/points needed to unlock
    hidden: bool = False
    reward_coins: int = 0  # Coin reward when achievement is unlocked


# All 25 achievements
ACHIEVEMENTS = {
    # Story Progress (5)
    "first_steps": Achievement(
        id="first_steps",
        name_en="First Steps",
        name_mk="Први чекори",
        desc_en="Complete level 1",
        desc_mk="Заврши ниво 1",
        category="story",
        requirement=1,
        reward_coins=50
    ),
    "getting_started": Achievement(
        id="getting_started",
        name_en="Getting Started",
        name_mk="Добар почеток",
        desc_en="Complete level 5",
        desc_mk="Заврши ниво 5",
        category="story",
        requirement=5,
        reward_coins=150
    ),
    "halfway_there": Achievement(
        id="halfway_there",
        name_en="Halfway There",
        name_mk="Половина готово",
        desc_en="Complete level 10",
        desc_mk="Заврши ниво 10",
        category="story",
        requirement=10,
        reward_coins=300
    ),
    "almost_done": Achievement(
        id="almost_done",
        name_en="Almost Done",
        name_mk="Речиси готово",
        desc_en="Complete level 13",
        desc_mk="Заврши ниво 13",
        category="story",
        requirement=13,
        reward_coins=600
    ),
    "cyber_hero": Achievement(
        id="cyber_hero",
        name_en="Cyber Hero",
        name_mk="Кибер херој",
        desc_en="Complete all 15 levels",
        desc_mk="Заврши сите 15 нивоа",
        category="story",
        requirement=15,
        reward_coins=1000
    ),
    
    # Quiz Master (4)
    "bookworm": Achievement(
        id="bookworm",
        name_en="Bookworm",
        name_mk="Книголубец",
        desc_en="Answer 10 quiz questions correctly",
        desc_mk="Одговори точно на 10 квиз прашања",
        category="quiz",
        requirement=10,
        reward_coins=150
    ),
    "knowledge_seeker": Achievement(
        id="knowledge_seeker",
        name_en="Knowledge Seeker",
        name_mk="Барател на знаење",
        desc_en="Answer 25 quiz questions correctly",
        desc_mk="Одговори точно на 25 квиз прашања",
        category="quiz",
        requirement=25,
        reward_coins=300
    ),
    "quiz_expert": Achievement(
        id="quiz_expert",
        name_en="Quiz Expert",
        name_mk="Квиз експерт",
        desc_en="Answer 50 quiz questions correctly",
        desc_mk="Одговори точно на 50 квиз прашања",
        category="quiz",
        requirement=50,
        reward_coins=750
    ),
    "library_regular": Achievement(
        id="library_regular",
        name_en="Library Regular",
        name_mk="Редовен посетител",
        desc_en="Own all 3 books",
        desc_mk="Поседувај ги сите 3 книги",
        category="quiz",
        requirement=3,
        reward_coins=250
    ),
    
    # Shopping Spree (4)
    "first_purchase": Achievement(
        id="first_purchase",
        name_en="First Purchase",
        name_mk="Прва купувина",
        desc_en="Buy any item from the shop",
        desc_mk="Купи било што од продавницата",
        category="shop",
        requirement=1,
        reward_coins=50
    ),
    "wealthy": Achievement(
        id="wealthy",
        name_en="Wealthy",
        name_mk="Богат",
        desc_en="Accumulate 5,000 coins",
        desc_mk="Собери 5,000 coins",
        category="shop",
        requirement=5000,
        reward_coins=500
    ),
    "rich": Achievement(
        id="rich",
        name_en="Rich",
        name_mk="Многу богат",
        desc_en="Accumulate 10,000 coins",
        desc_mk="Собери 10,000 coins",
        category="shop",
        requirement=10000,
        reward_coins=1000
    ),
    "fully_upgraded": Achievement(
        id="fully_upgraded",
        name_en="Fully Upgraded",
        name_mk="Целосно надграден",
        desc_en="Max out all permanent upgrades",
        desc_mk="Надгради ги сите трајни надградби",
        category="shop",
        requirement=1,
        reward_coins=1000
    ),
    
    # Defense Master (4)
    "wall_builder": Achievement(
        id="wall_builder",
        name_en="Wall Builder",
        name_mk="Градител на ѕидови",
        desc_en="Place 100 walls total",
        desc_mk="Постави 100 ѕидови вкупно",
        category="defense",
        requirement=100,
        reward_coins=200
    ),
    "sharpshooter": Achievement(
        id="sharpshooter",
        name_en="Sharpshooter",
        name_mk="Остар стрелец",
        desc_en="Destroy 500 enemies",
        desc_mk="Уништи 500 непријатели",
        category="defense",
        requirement=500,
        reward_coins=350
    ),
    "perfect_defense": Achievement(
        id="perfect_defense",
        name_en="Perfect Defense",
        name_mk="Перфектна одбрана",
        desc_en="Complete a level without losing any hearts",
        desc_mk="Заврши ниво без да изгубиш срца",
        category="defense",
        requirement=1,
        reward_coins=75
    ),
    "untouchable": Achievement(
        id="untouchable",
        name_en="Untouchable",
        name_mk="Недопирлив",
        desc_en="Complete 5 levels without losing any hearts",
        desc_mk="Заврши 5 нивоа без да изгубиш срца",
        category="defense",
        requirement=5,
        reward_coins=400
    ),
    
    # Survival (4)
    "close_call": Achievement(
        id="close_call",
        name_en="Close Call",
        name_mk="Тесна победа",
        desc_en="Complete a level with only 1 heart remaining",
        desc_mk="Заврши ниво со само 1 срце",
        category="survival",
        requirement=1,
        reward_coins=75
    ),
    "comeback_king": Achievement(
        id="comeback_king",
        name_en="Comeback King",
        name_mk="Крал на враќањето",
        desc_en="Win after buying back a heart",
        desc_mk="Победи откако купи срце назад",
        category="survival",
        requirement=1,
        reward_coins=100
    ),
    "shield_master": Achievement(
        id="shield_master",
        name_en="Shield Master",
        name_mk="Мајстор на штит",
        desc_en="Use shields 20 times",
        desc_mk="Користи штит 20 пати",
        category="survival",
        requirement=20,
        reward_coins=200
    ),
    "no_damage": Achievement(
        id="no_damage",
        name_en="No Damage",
        name_mk="Без оштетување",
        desc_en="Complete a wave without taking damage",
        desc_mk="Заврши бран без да примиш оштетување",
        category="survival",
        requirement=1,
        reward_coins=75
    ),
    
    # Skill & Mastery (4)
    "speed_runner": Achievement(
        id="speed_runner",
        name_en="Speed Runner",
        name_mk="Брз играч",
        desc_en="Complete a level in under 2 minutes",
        desc_mk="Заврши ниво за помалку од 2 минути",
        category="skill",
        requirement=1,
        reward_coins=250
    ),
    "coin_collector": Achievement(
        id="coin_collector",
        name_en="Coin Collector",
        name_mk="Собирач на coins",
        desc_en="Earn 1,000 coins from Tetris",
        desc_mk="Заработи 1,000 coins од Tetris",
        category="skill",
        requirement=1000,
        reward_coins=450
    ),
    "tetris_pro": Achievement(
        id="tetris_pro",
        name_en="Tetris Pro",
        name_mk="Tetris професионалец",
        desc_en="Score 500+ points in a single Tetris session",
        desc_mk="Постигни 500+ поени во една Tetris сесија",
        category="skill",
        requirement=500,
        reward_coins=500
    ),
    "checkpoint_champion": Achievement(
        id="checkpoint_champion",
        name_en="Checkpoint Champion",
        name_mk="Шампион на checkpoint",
        desc_en="Reach all 5 checkpoint levels",
        desc_mk="Достигни ги сите 5 checkpoint нивоа",
        category="skill",
        requirement=5,
        reward_coins=500
    ),
}


def check_achievement(sd: SaveData, achievement_id: str, value: int = None) -> bool:
    """
    Check and potentially unlock an achievement.
    
    Args:
        sd: SaveData object
        achievement_id: ID of the achievement to check
        value: Current value to check (for non-incremental achievements) or amount to add (for incremental)
    
    Returns:
        True if achievement was newly unlocked, False otherwise
    """
    if achievement_id not in ACHIEVEMENTS:
        return False
    
    if achievement_id in sd.unlocked_achievements:
        return False  # Already unlocked
    
    achievement = ACHIEVEMENTS[achievement_id]
    
    # For incremental achievements, add to progress
    if value is None:
        value = 1
    
    # Some achievements check current state, others track cumulative progress
    if achievement_id in ["wealthy", "rich", "fully_upgraded", "library_regular"]:
        # These check current state, not cumulative
        current_value = value
    else:
        # These track cumulative progress
        current_value = sd.achievement_progress.get(achievement_id, 0) + value
        sd.achievement_progress[achievement_id] = current_value
    
    # Check if requirement met
    if current_value >= achievement.requirement:
        sd.unlocked_achievements.append(achievement_id)
        # Coins are NOT granted automatically - player must claim manually
        return True
    
    return False


def claim_achievement(sd: SaveData, achievement_id: str) -> int:
    """
    Claim an unlocked achievement and grant its reward.
    
    Args:
        sd: SaveData object
        achievement_id: ID of the achievement to claim
    
    Returns:
        Amount of coins granted (0 if already claimed or not unlocked)
    """
    if achievement_id not in ACHIEVEMENTS:
        return 0
    
    if achievement_id in sd.claimed_achievements:
        return 0  # Already claimed
    
    if achievement_id not in sd.unlocked_achievements:
        return 0  # Not unlocked yet
    
    achievement = ACHIEVEMENTS[achievement_id]
    sd.claimed_achievements.append(achievement_id)
    
    # Grant coin reward
    if achievement.reward_coins > 0:
        sd.wallet += achievement.reward_coins
    
    return achievement.reward_coins


def get_achievement_progress(sd: SaveData, achievement_id: str) -> tuple[int, int]:
    """Get current progress for an achievement (current, required)"""
    if achievement_id not in ACHIEVEMENTS:
        return (0, 1)
    
    achievement = ACHIEVEMENTS[achievement_id]
    current = sd.achievement_progress.get(achievement_id, 0)
    
    return (current, achievement.requirement)


def get_unlocked_count(sd: SaveData) -> int:
    """Get number of unlocked achievements"""
    return len(sd.unlocked_achievements)


def get_total_count() -> int:
    """Get total number of achievements"""
    return len(ACHIEVEMENTS)
