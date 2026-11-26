"""Unit, card, tower and elixir numbers from the game's own files.

They're exported to data/game_data.json by
dev/game_data/export_game_data.py; see there for where each comes from.
Stats are stored at level 1. A stat at level L is the level-1 value times
the game's multiplier for L, over 100, rounded down. Levels are the game's
unified 1-15 scale, where each rarity starts higher: rare cards at 3, epic
at 6, legendary at 9, champions at 11.
"""

import functools
import json
import math
from typing import Any

from clashroyalebuildabot.constants.paths import GAME_DATA_PATH
from clashroyalebuildabot.game.timer import Timer

# What to assume when the level isn't known: tournament standard.
DEFAULT_LEVEL = 11

# The stats that grow with level. The rest (speed, range and so on) don't.
_UNIT_SCALED = ("hitpoints", "shield_hitpoints", "damage", "death_damage")


class UnknownName(KeyError):
    pass


class BadLevel(ValueError):
    pass


@functools.cache
def data() -> dict[str, Any]:
    with open(GAME_DATA_PATH, encoding="utf-8") as file:
        return json.load(file)


def max_level() -> int:
    return len(data()["multipliers"])


def scale(value: int | None, level: int) -> int | None:
    """A level-1 stat at level."""
    if value is None:
        return None
    return value * data()["multipliers"][level - 1] // 100


def min_level(rarity: str) -> int:
    return data()["rarities"][rarity]["min_level"]


def _check_level(level: int, lowest: int) -> None:
    if not lowest <= level <= max_level():
        raise BadLevel(f"Level must be from {lowest} to {max_level()}.")


def unit_names() -> list[str]:
    return sorted(data()["units"])


def card_names() -> list[str]:
    return sorted(data()["cards"])


def unit_stats(name: str, level: int = DEFAULT_LEVEL) -> dict[str, Any]:
    """A unit's stats at level. Raises UnknownName or BadLevel."""
    if name not in data()["units"]:
        raise UnknownName(f"No unit called {name!r}.")
    _check_level(level, 1)
    stats = dict(data()["units"][name])
    for key in _UNIT_SCALED:
        stats[key] = scale(stats[key], level)
    hit_speed = stats["hit_speed"]
    stats["dps"] = (
        round(stats["damage"] / hit_speed, 1)
        if stats["damage"] and hit_speed
        else None
    )
    stats["level"] = level
    stats["name"] = name
    return stats


def card_stats(name: str, level: int | None = None) -> dict[str, Any]:
    """A card's stats at level, with the stats of the units it deploys at
    the same level. Without a level, DEFAULT_LEVEL, or the card's rarity's
    lowest level if that's higher. Raises UnknownName or BadLevel."""
    if name not in data()["cards"]:
        raise UnknownName(f"No card called {name!r}.")
    card = dict(data()["cards"][name])
    lowest = min_level(card["rarity"])
    if level is None:
        level = max(DEFAULT_LEVEL, lowest)
    _check_level(level, lowest)
    card["summons"] = [
        {
            **summon,
            "stats": (
                unit_stats(summon["unit"], level)
                if summon["unit"] in data()["units"]
                else None
            ),
        }
        for summon in card["summons"]
    ]
    spell = card.get("spell")
    if spell is not None:
        damage = scale(spell["damage"], level)
        percent = spell["crown_tower_damage_percent"]
        card["spell"] = {
            **spell,
            "damage": damage,
            "crown_tower_damage": (
                damage * percent // 100
                if damage is not None and percent is not None
                else None
            ),
        }
    card["min_level"] = lowest
    card["level"] = level
    card["name"] = name
    return card


def towers() -> dict[str, Any]:
    """Princess and king tower stats, at level 1 only: towers grow with
    level by a table the game's files don't include."""
    return data()["towers"]


# Full HP by tower level, from 1. Towers scale by their own table, which the
# game's files leave out (see towers()), so it's written out here. Level 1
# matches the files' 2400 and 1400; real battles showed level 9 and 11
# princess towers at 2534 and 3052. Levels past 14 aren't known yet.
TOWER_HITPOINTS = {
    "princess": (1400, 1512, 1624, 1750, 1890, 2030, 2184,
                 2352, 2534, 2786, 3052, 3346, 3668, 4032),
    "king": (2400, 2568, 2736, 2904, 3096, 3312, 3528,
             3768, 4008, 4392, 4824, 5304, 5832, 6408),
}  # fmt: skip


def tower_level(princess_hp: float) -> int | None:
    """The level of a princess tower at full health, and so of its side's
    king tower too. None if no level has that HP."""
    try:
        return TOWER_HITPOINTS["princess"].index(princess_hp) + 1
    except ValueError:
        return None


def king_hitpoints(level: int) -> int | None:
    """A king tower's full HP at a level. None if it isn't known."""
    table = TOWER_HITPOINTS["king"]
    return table[level - 1] if 1 <= level <= len(table) else None


def elixir() -> dict[str, Any]:
    return data()["elixir"]


def seconds_since_start(timer: Timer) -> float | None:
    """How long the battle has run, from the timer. None until read."""
    if math.isinf(timer.time_left):
        return None
    sections = elixir()["sections"]
    regulation = sections[0]["length"]
    if not timer.overtime:
        return regulation - timer.time_left
    overtime = sections[1]["length"] if len(sections) > 1 else 0
    return regulation + overtime - timer.time_left


def seconds_per_elixir(timer: Timer) -> float | None:
    """How long one elixir takes to come in now. None until the timer has
    been read."""
    elapsed = seconds_since_start(timer)
    if elapsed is None:
        return None
    phases = elixir()["phases"]
    for phase in phases:
        if elapsed < phase["to"]:
            return phase["seconds_per_elixir"]
    return phases[-1]["seconds_per_elixir"]
