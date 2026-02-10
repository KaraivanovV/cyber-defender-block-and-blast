from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
import random

@dataclass
class Scenario:
    id: str
    world: int
    prompt_mk: str
    prompt_en: str
    correct: str  # "safe" | "private" | "never"
    tip_mk: str
    tip_en: str

def build_scenarios() -> List[Scenario]:
    s = []
    # World 1 (privacy basics)
    s += [
        Scenario("w1_name",1,
            "Ново другарче прашува: „Како ти е целото име?“",
            "A new friend asks: “What is your full name?”",
            "private",
            "Може да кажеш само прекар. Целото име е приватно.",
            "A nickname is fine. Your full name is private."
        ),
        Scenario("w1_address",1,
            "Некоj онлајн прашува: „Каде живееш? Кажи адреса.“",
            "Someone online asks: “Where do you live? Tell your address.”",
            "never",
            "Адресата никогаш не ја споделувај онлајн.",
            "Never share your home address online."
        ),
        Scenario("w1_school",1,
            "Во игра те прашуваат: „Во кое училиште одиш?“",
            "A game asks: “Which school do you go to?”",
            "never",
            "Училиштето може да те открие. Подобро не.",
            "School info can identify you. Better not."
        ),
    ]
    # World 2 (passwords)
    s += [
        Scenario("w2_pw1",2,
            "Правиш лозинка. Која е подобра?",
            "You're making a password. Which is better?",
            "private",
            "Лозинки се приватни. И нека бидат долги и мешани!",
            "Passwords are private. Make them long and mixed!"
        ),
        Scenario("w2_pw2",2,
            "Лозинка: 'miki2017'. Добра ли е?",
            "Password: 'miki2017'. Is it good?",
            "never",
            "Не користи име/година. Додај знаци и повеќе букви.",
            "Don't use names/years. Add symbols and more letters."
        ),
        Scenario("w2_pw3",2,
            "Другарче ти бара лозинка „само да проба игра“.",
            "A friend asks for your password “just to try a game.”",
            "never",
            "Лозинката е само твоја (и за родител/старател ако треба).",
            "Your password is only yours (and a parent/guardian if needed)."
        ),
    ]
    # World 3 (DM safety)
    s += [
        Scenario("w3_dm1",3,
            "Непознат праќа DM: „Прати ми слика и ќе ти дадам skin.“",
            "A stranger DM: “Send a pic and I'll give you a skin.”",
            "never",
            "Странци + награди = трик. Блокирај и пријави.",
            "Strangers + prizes = a trick. Block and report."
        ),
        Scenario("w3_dm2",3,
            "Некој вели: „Не кажувај на никого, тоа е тајна!“",
            "Someone says: “Don’t tell anyone, it’s a secret!”",
            "never",
            "Безбедни тајни не бараат да молчиш. Кажи на доверлив возрасен.",
            "Safe secrets don't demand silence. Tell a trusted adult."
        ),
        Scenario("w3_dm3",3,
            "Другарче прашува: „Кој ти е број?“",
            "A friend asks: “What’s your phone number?”",
            "never",
            "Бројот е личен. Сподели само со родител/доверливи луѓе офлајн.",
            "Phone numbers are personal. Share only with trusted adults offline."
        ),
    ]
    # World 4 (scams/phishing)
    s += [
        Scenario("w4_popup",4,
            "Поп-ап: „Честитки! Освои телефон! Кликни веднаш!“",
            "Pop-up: “Congrats! You won a phone! Click now!”",
            "never",
            "Премногу добро за да е вистина. Затвори го поп-апот.",
            "Too good to be true. Close the pop-up."
        ),
        Scenario("w4_link",4,
            "Линк изгледа чудно: 'g00gle-prize.com'. Што правиш?",
            "A link looks weird: 'g00gle-prize.com'. What do you do?",
            "never",
            "Чудни линкови = опасност. Не кликнувај, прашај возрасен.",
            "Weird links = danger. Don't click; ask an adult."
        ),
        Scenario("w4_info",4,
            "Сајт бара име + адреса за „бесплатна награда“.",
            "A site asks for name + address for a “free prize.”",
            "never",
            "Никогаш не давај лични податоци за награди.",
            "Never give personal info for prizes."
        ),
    ]
    return s

def pick_scenarios(pool: List[Scenario], world: int, k: int, rng: random.Random) -> List[Scenario]:
    choices = [x for x in pool if x.world == world]
    if not choices:
        choices = pool[:]
    rng.shuffle(choices)
    return choices[:k]
