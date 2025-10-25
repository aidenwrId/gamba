from __future__ import annotations

import json
import math
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

from .config import settings


@dataclass
class SlotSymbol:
    name: str
    weight: int
    payout: int


SLOT_REELS: List[List[SlotSymbol]] = [
    [
        SlotSymbol("galaxy", 20, 5),
        SlotSymbol("comet", 18, 8),
        SlotSymbol("quasar", 12, 20),
        SlotSymbol("nova", 8, 40),
        SlotSymbol("supernova", 2, 120),
    ],
    [
        SlotSymbol("galaxy", 20, 5),
        SlotSymbol("comet", 18, 8),
        SlotSymbol("quasar", 12, 20),
        SlotSymbol("nova", 8, 40),
        SlotSymbol("supernova", 2, 120),
    ],
    [
        SlotSymbol("galaxy", 20, 5),
        SlotSymbol("comet", 18, 8),
        SlotSymbol("quasar", 12, 20),
        SlotSymbol("nova", 8, 40),
        SlotSymbol("supernova", 2, 120),
    ],
]


def weighted_choice(symbols: List[SlotSymbol]) -> SlotSymbol:
    total = sum(symbol.weight for symbol in symbols)
    roll = secrets.randbelow(total) + 1
    upto = 0
    for symbol in symbols:
        upto += symbol.weight
        if roll <= upto:
            return symbol
    return symbols[-1]  # pragma: no cover - theoretical fallback


def spin_slots(bet: int) -> Tuple[List[str], int, str]:
    results = [weighted_choice(reel).name for reel in SLOT_REELS]
    payout_multiplier = 0
    message = ""
    if len(set(results)) == 1:
        symbol = results[0]
        payout_table = {s.name: s.payout for s in SLOT_REELS[0]}
        payout_multiplier = payout_table[symbol]
        message = f"Triple {symbol.title()}!"
    elif results.count(results[0]) == 2 or results.count(results[1]) == 2:
        payout_multiplier = 3
        message = "Twin constellation bonus"
    net = bet * payout_multiplier - bet
    return results, net + bet if net > 0 else 0, message or "Better luck next spin"


CARD_VALUES: Dict[str, int] = {
    "A": 11,
    "K": 10,
    "Q": 10,
    "J": 10,
    "10": 10,
    "9": 9,
    "8": 8,
    "7": 7,
    "6": 6,
    "5": 5,
    "4": 4,
    "3": 3,
    "2": 2,
}
SUITS = ["♠", "♥", "♦", "♣"]


def draw_deck() -> List[str]:
    deck = [f"{rank}{suit}" for rank in CARD_VALUES for suit in SUITS]
    secrets.SystemRandom().shuffle(deck)
    return deck


def hand_value(hand: List[str]) -> int:
    value = sum(CARD_VALUES[card[:-1]] for card in hand)
    aces = sum(1 for card in hand if card.startswith("A"))
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value


def simulate_blackjack(bet: int) -> Tuple[List[str], List[str], int, str]:
    deck = draw_deck()
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]

    while hand_value(player) < 17:
        player.append(deck.pop())
    while hand_value(dealer) < 17:
        dealer.append(deck.pop())

    player_score = hand_value(player)
    dealer_score = hand_value(dealer)

    if player_score > 21:
        outcome = "bust"
        net = -bet
    elif dealer_score > 21 or player_score > dealer_score:
        net = bet
        outcome = "win"
    elif player_score == dealer_score:
        net = 0
        outcome = "push"
    else:
        net = -bet
        outcome = "lose"
    return player, dealer, net, outcome


VIRTUAL_ODDS = {"aurora": 1.8, "nebula": 2.2}


def virtual_sport_event(selection: str, bet: int) -> Tuple[str, int, float]:
    odds = VIRTUAL_ODDS[selection]
    total_weight = sum(int(odds * 100) for odds in VIRTUAL_ODDS.values())
    roll = secrets.randbelow(total_weight)
    cumulative = 0
    for team, team_odds in VIRTUAL_ODDS.items():
        weight = int(team_odds * 100)
        if cumulative <= roll < cumulative + weight:
            winner = team
            break
        cumulative += weight
    else:  # pragma: no cover - fallback
        winner = selection
    if winner == selection:
        payout = math.floor(bet * odds)
        net = payout - bet
    else:
        payout = 0
        net = -bet
    return winner, net, odds


def render_session_details(data: Dict) -> str:
    return json.dumps({k: v for k, v in data.items()}, default=_json_default)


def _json_default(obj):  # pragma: no cover - JSON helper
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")
