from __future__ import annotations
from typing import Tuple, Dict, Any
from ..constants import RANKS

ACHIEVEMENTS = [
  {"id":"first_clear","name_mk":"Прво Firewall чистење","name_en":"First Firewall Clear",
   "desc_mk":"Исчисти една линија.", "desc_en":"Clear one line."},
  {"id":"tetris_4","name_mk":"Cyber Hero Комбо","name_en":"Cyber Hero Combo",
   "desc_mk":"Исчисти 4 линии одеднаш.", "desc_en":"Clear 4 lines at once."},
  {"id":"pop_up_dodger","name_mk":"Избегнувач на поп-ап","name_en":"Pop-up Dodger",
   "desc_mk":"Преживеј поп-ап магла без да изгубиш срце.", "desc_en":"Survive pop-up fog without losing a heart."},
  {"id":"privacy_pro","name_mk":"Privacy Pro","name_en":"Privacy Pro",
   "desc_mk":"Направи 5 точни приватност избори во една сесија.", "desc_en":"Make 5 correct privacy choices in one session."},
  {"id":"dm_shield","name_mk":"DM Shield","name_en":"DM Shield",
   "desc_mk":"Користи 'Пријави' 10 пати.", "desc_en":"Use 'Report' 10 times."},
  {"id":"boss_down","name_mk":"Победа над бос","name_en":"Boss Victory",
   "desc_mk":"Победи еден бос.", "desc_en":"Defeat a boss."},
  {"id":"strong_password","name_mk":"Strong Password Builder","name_en":"Strong Password Builder",
   "desc_mk":"Наполни Password Energy на максимум.", "desc_en":"Fill Password Energy to max."},
  {"id":"coin_hoarder","name_mk":"Собирач на монети","name_en":"Coin Hoarder",
   "desc_mk":"Собери 300 монети вкупно.", "desc_en":"Collect 300 coins total."},
  {"id":"perfect_wave","name_mk":"Чист бран","name_en":"Clean Wave",
   "desc_mk":"Заврши бран без да изгубиш срце.", "desc_en":"Finish a wave without losing a heart."},
  {"id":"combo_6","name_mk":"Комбо 6","name_en":"Combo 6",
   "desc_mk":"Направи комбо од 6 чистења.", "desc_en":"Reach a 6-clear combo."},
  {"id":"collector","name_mk":"Козметички колекционер","name_en":"Cosmetic Collector",
   "desc_mk":"Отклучи 3 козметики.", "desc_en":"Unlock 3 cosmetics."},
]

def rank_from_xp(xp: int) -> str:
    r = "rookie"
    for name, req in RANKS:
        if xp >= req:
            r = name
    return r

def next_rank_progress(xp: int) -> Tuple[str, int, int]:
    # returns (current_rank, cur_req, next_req)
    cur = ("rookie", 0)
    nxt = None
    for i,(name, req) in enumerate(RANKS):
        if xp >= req:
            cur = (name, req)
            if i+1 < len(RANKS):
                nxt = RANKS[i+1]
        else:
            break
    if not nxt:
        return cur[0], cur[1], cur[1]
    return cur[0], cur[1], nxt[1]
