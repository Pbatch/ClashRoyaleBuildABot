"""Export the game numbers the bot's API serves to
clashroyalebuildabot/data/game_data.json: unit and card stats, how they
grow with level, tower stats and the elixir timeline.

Reads the logic files dev/synthetic/apk_assets.py extracts from the APK.
Only the derived numbers are written, never the game's files themselves.
Re-run after a game update, or when a card is added to
clashroyalebuildabot/game. It needs nothing beyond the bot's own
environment, so from the project folder:

    uv run python dev/game_data/export_game_data.py

Level scaling (stored level-1 value x multiplier / 100, rounded down) was
checked against RoyaleAPI's cr-api-data (Oct 2023): all 4,945 per-level
values there follow it. That data predates later balance changes, so it
can't check the current base values themselves.
"""

import argparse
import json
import re
import sys
import tomllib
from collections import defaultdict
from dataclasses import fields
from pathlib import Path

from clashroyalebuildabot.game.cards import Card, Cards
from clashroyalebuildabot.game.units import Units
from game_files import LABELS, load_entities, read_csv, read_text

HERE = Path(__file__).parent
# Where dev/synthetic/apk_assets.py extracts the APK's logic files.
DEFAULT_LOGIC = HERE.parent / "synthetic/assets/apk/extracted/assets/csv_logic"
LOGIC = DEFAULT_LOGIC
OUT = HERE.parent.parent / "clashroyalebuildabot/data/game_data.json"

# The card tables, and the kind of card in each.
CARD_TABLES = {
    26: ("spells_characters.csv", "troop"),
    27: ("spells_buildings.csv", "building"),
    28: ("spells_other.csv", "spell"),
}
TILE = 1000  # logic units per tile
MS = 1000

# {kind: {name: section}}, e.g. sections["PROJECTILE"]["FireballSpell"].
type Sections = dict[str, dict[str, dict]]


def tables() -> Sections:
    """Every [KIND.Name] section in the logic TOML files, by kind, plus the
    top-level sections of the spells_*.toml overrides."""
    sections = defaultdict(dict)
    for path in sorted(LOGIC.rglob("*.toml")):
        try:
            data = tomllib.loads(read_text(path))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError, ValueError):
            continue
        for kind, entries in data.items():
            if not isinstance(entries, dict):
                continue
            if path.name.startswith("spells_") and not kind.isupper():
                # spells_characters.toml etc.: [Name] overrides the CSV row.
                sections["SPELL_OVERRIDE"][kind] = entries
                continue
            for name, value in entries.items():
                if isinstance(value, dict):
                    sections[kind][name] = value
    return sections


def rarities() -> dict[str, dict]:
    rows = read_csv(LOGIC / "rarities.csv")
    header = rows[0]
    name_i = header.index("Name")
    relative_i = header.index("RelativeLevel")
    mult_i = header.index("PowerLevelMultiplier")
    # A rarity's first row names it; the rows after it, unnamed, are its
    # further levels.
    min_levels: dict[str, int] = {}
    multipliers: dict[str, list[int]] = {}
    current = ""
    for row in rows[2:]:
        if row[name_i]:
            current = row[name_i]
            min_levels[current] = int(row[relative_i] or 0) + 1
            multipliers[current] = [100]
        multipliers[current].append(int(row[mult_i]))
    return {
        name: {"min_level": min_levels[name], "multipliers": multipliers[name]}
        for name in min_levels
    }


# Bot card names whose game name isn't the same name without underscores
# (ignoring a trailing s).
CARD_ALIASES = {
    "bandit": "Assassin",
    "barbarian_barrel": "BarbLog",
    "dart_goblin": "BlowdartGoblin",
    "furnace": "FirespiritHut",
    "giant_snowball": "Snowball",
    "royal_ghost": "Ghost",
    "rune_giant": "GiantBuffer",
    "sparky": "ZapMachine",
    "spirit_empress": "MergeMaiden",
    "the_log": "Log",
    "void": "DarkMagic",
    "zappies": "MiniSparkys",
    "goblin_barrel": "GoblinBarrel",
    "skeleton_dragons": "SkeletonDragons",
    "royal_recruits": "RoyalRecruits",
    "elixir_golem": "ElixirGolem",
    "cannon_cart": "MovingCannon",
    "elite_barbarians": "AngryBarbarians",
    "executioner": "AxeMan",
    "flying_machine": "DartBarrell",
    "guards": "SkeletonWarriors",
    "heal_spirit": "Heal",
    "ice_golem": "IceGolemite",
    "lumberjack": "RageBarbarian",
    "magic_archer": "EliteArcher",
    "mother_witch": "WitchMother",
    "night_witch": "DarkWitch",
    "skeleton_barrel": "SkeletonBalloon",
}


# Game entities a card summons that the label map has no entry for.
EXTRA_UNITS = {"Goblin_Stab": "goblin", "GoblinDrillDig": "goblin_drill"}


def _simple(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def card_rows() -> dict[str, dict]:
    """{simplified game name: CSV row as a dict}, from all three card
    tables."""
    out = {}
    for file, kind in CARD_TABLES.values():
        rows = read_csv(LOGIC / file)
        header = rows[0]
        for row in rows[2:]:
            entry = {k: v for k, v in zip(header, row, strict=False) if v}
            if "Name" not in entry or "ManaCost" not in entry:
                continue
            entry["_kind"] = kind
            out.setdefault(_simple(entry["Name"]), entry)
    return out


def find_row(card: Card, rows: dict[str, dict]) -> dict | None:
    alias = CARD_ALIASES.get(card.name)
    if alias:
        return rows.get(_simple(alias))
    simple = _simple(card.name)
    for candidate in (simple, simple + "s", simple.removesuffix("s")):
        if candidate in rows:
            return rows[candidate]
    return None


def tiles(value: float | None) -> float | None:
    return None if value is None else value / TILE


def seconds(value: float | None) -> float | None:
    return None if value is None else value / MS


def damage_of(
    entry: dict, sections: Sections, depth: int = 0
) -> tuple[int | None, float | None, int | None]:
    """(damage, area radius in tiles, crown tower damage percent) of a
    character, building, projectile or area effect. Follows a projectile
    that spawns another, as the Log's does."""
    damage = entry.get("Damage")
    radius = entry.get("AreaDamageRadius") or entry.get("Radius")
    radius = tiles(radius) if radius else None
    crown = entry.get("CrownTowerDamagePercent")
    if isinstance(damage, dict):  # AEO: {BaseDamage, TowerDamage}
        base, tower = damage.get("BaseDamage"), damage.get("TowerDamage")
        if base and tower is not None:
            crown = round(100 * tower / base) - 100
        damage = base
    next_name = None
    if damage is None:
        next_name = entry.get("Projectile") or entry.get("SpawnProjectile")
    if next_name and depth < 3:
        projectile = sections["PROJECTILE"].get(next_name, {})
        damage, p_radius, p_crown = damage_of(projectile, sections, depth + 1)
        if not entry.get("AreaDamageRadius"):
            radius = radius or p_radius
        crown = crown if crown is not None else p_crown
    return damage, radius, crown


def spawned_by(
    entry: dict, sections: Sections, depth: int = 0
) -> tuple[str, int] | None:
    """(game name, count) of the units a spell's projectile drops, as the
    Goblin Barrel's does."""
    if entry.get("SpawnCharacter"):
        return entry["SpawnCharacter"], entry.get("SpawnCharacterCount", 1)
    name = entry.get("Projectile") or entry.get("SpawnProjectile")
    if name and depth < 3:
        return spawned_by(
            sections["PROJECTILE"].get(name, {}), sections, depth + 1
        )
    return None


def unit_stats(
    entry: dict, sections: Sections, game_to_bot: dict[str, str]
) -> dict:
    damage, area, _ = damage_of(entry, sections)
    building = bool(entry.get("IsBuilding")) or "LifeTime" in entry
    stats = {
        "game_name": entry.get("Name"),
        "hitpoints": entry.get("Hitpoints"),
        "shield_hitpoints": entry.get("ShieldHitpoints"),
        "damage": damage,
        "area_damage_radius": area,
        "hit_speed": seconds(entry.get("HitSpeed")),
        "first_hit": seconds(entry.get("LoadTime")),
        "range": tiles(entry.get("Range")),
        "sight_range": tiles(entry.get("SightRange")),
        "speed": entry.get("Speed"),
        "deploy_time": seconds(entry.get("DeployTime")),
        "collision_radius": tiles(entry.get("CollisionRadius")),
        "mass": entry.get("Mass"),
        "flying": bool(entry.get("FlyingHeight")),
        "building": building,
        "lifetime": seconds(entry.get("LifeTime")),
        "attacks_air": bool(entry.get("AttacksAir")),
        "attacks_ground": bool(entry.get("AttacksGround")),
        "targets_only_buildings": bool(entry.get("TargetOnlyBuildings")),
        "death_damage": entry.get("DeathDamage"),
    }
    if entry.get("SpawnCharacter"):
        stats["spawns"] = {
            "unit": game_to_bot.get(entry["SpawnCharacter"]),
            "game_name": entry["SpawnCharacter"],
            "count": entry.get("SpawnNumber", 1),
            "interval": seconds(entry.get("SpawnPauseTime")),
        }
    if entry.get("DeathSpawnCharacter"):
        stats["death_spawns"] = {
            "unit": game_to_bot.get(entry["DeathSpawnCharacter"]),
            "game_name": entry["DeathSpawnCharacter"],
            "count": entry.get("DeathSpawnCount", 1),
        }
    return stats


def card_stats(
    card: Card, row: dict, sections: Sections, game_to_bot: dict[str, str]
) -> dict:
    name = row["Name"]
    override = sections["SPELL_OVERRIDE"].get(name, {})
    for kind in ("SPELL_CHARACTER", "SPELL_BUILDING", "SPELL_OTHER"):
        override = {**override, **sections[kind].get(name, {})}
    data = {**row, **override}
    out = {
        "game_name": name,
        "type": row["_kind"],
        "rarity": data["Rarity"].lower(),
        "cost": int(data["ManaCost"]),
        "summons": [],
    }
    summoned = data.get("SummonCharactersList")
    if summoned:
        for game_name in summoned:
            out["summons"].append(
                {"unit": game_to_bot.get(game_name), "game_name": game_name,
                 "count": 1}
            )  # fmt: skip
    elif data.get("SummonCharacter"):
        game_name = data["SummonCharacter"]
        out["summons"].append(
            {"unit": game_to_bot.get(game_name), "game_name": game_name,
             "count": int(data.get("SummonNumber", 1))}
        )  # fmt: skip
    if row["_kind"] == "spell":
        spawned = spawned_by(data, sections)
        if spawned and not out["summons"]:
            game_name, count = spawned
            out["summons"].append(
                {"unit": game_to_bot.get(game_name), "game_name": game_name,
                 "count": count}
            )  # fmt: skip
        source = None
        if data.get("Projectile"):
            source = sections["PROJECTILE"].get(data["Projectile"])
        elif data.get("AreaEffectObject"):
            source = sections["AEO"].get(data["AreaEffectObject"])
        damage, radius, crown = (None, None, None)
        if source:
            damage, radius, crown = damage_of(source, sections)
        waves = int(data.get("ProjectileWaves", 1))
        out["spell"] = {
            "damage": damage,
            "waves": waves,
            "radius": tiles(int(data["Radius"]))
            if data.get("Radius")
            else radius,
            "crown_tower_damage_percent": (
                None if crown is None else 100 + crown
            ),
        }
    # A summon the label map doesn't know, like each of the Three
    # Musketeers, is the card's own unit when the card has just one.
    if len(card.units) == 1:
        for summon in out["summons"]:
            if summon["unit"] is None:
                summon["unit"] = card.units[0].name
    return out


def elixir_timeline() -> dict:
    rows = read_csv(LOGIC / "battle_timelines.csv")
    header = rows[0]
    timeline, sections, current = [], [], None
    for row in rows[2:]:
        entry = dict(zip(header, row, strict=False))
        if entry["Name"]:
            current = entry["Name"]
        if current == "Default" and entry["ElixirRateLength"]:
            timeline.append(
                (int(entry["ElixirRateLength"]), int(entry["ElixirFullBarMS"]))
            )
        if current == "Default" and entry["StartingElixir"]:
            starting = int(entry["StartingElixir"])
        if current == "Default" and entry["SectionLength"]:
            sections.append(
                {
                    "type": entry["SectionType"].lower(),
                    "length": int(entry["SectionLength"]),
                }
            )
    max_elixir = next(
        int(r[1])
        for r in read_csv(LOGIC / "globals.csv")
        if r[0] == "MAX_MANA"
    )
    phases, start = [], 0
    for length, full_bar in timeline:
        phases.append(
            {
                "from": start,
                "to": start + length,
                # The bar fills from 0 to 10 in full_bar milliseconds.
                "seconds_per_elixir": round(full_bar / 10 / MS, 3),
            }
        )
        start += length
    # Battle sections in order: regulation ("normal"), then overtime, in
    # seconds. Phases count seconds from the start of the battle.
    return {
        "starting": starting,
        "max": max_elixir,
        "sections": sections,
        "phases": phases,
    }


def main() -> None:
    global LOGIC
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--logic",
        type=Path,
        default=DEFAULT_LOGIC,
        help="the APK's extracted assets/csv_logic folder "
        "(default: %(default)s)",
    )
    LOGIC = parser.parse_args().logic
    sections = tables()
    entities, _ = load_entities(LOGIC)
    for kind in ("PROJECTILE", "AEO"):
        sections[kind] = {**sections.get(kind, {})}
    # A label's entities are names, or (name, which animations) where one
    # entity is drawn as two units; the stats are the entity's either way.
    labels = {
        label: [item[0] if isinstance(item, tuple) else item for item in items]
        for label, items in LABELS.items()
    }
    game_to_bot = dict(EXTRA_UNITS)
    for label, names in labels.items():
        for name in names:
            game_to_bot.setdefault(name, label)
    # Variants (EXT entries, like each of the Three Musketeers) count as
    # the unit they're based on.
    for name in sections["EXT"]:
        base, seen = name, set()
        while base not in game_to_bot and base not in seen:
            seen.add(base)
            parent = sections["EXT"].get(base, {}).get("Base", "")
            if not parent:
                break
            base = parent.partition(".")[2]
        if base in game_to_bot:
            game_to_bot.setdefault(name, game_to_bot[base])

    units, missing = {}, []
    for unit in Units.all():
        names = labels.get(unit.name, [])
        entry = next((entities[n] for n in names if n in entities), None)
        if entry is None:
            missing.append(unit.name)
            continue
        units[unit.name] = unit_stats(entry, sections, game_to_bot)

    rows = card_rows()
    cards = {}
    for f in fields(Cards):
        card = getattr(Cards, f.name)
        row = find_row(card, rows)
        if row is None:
            missing.append(f"card {card.name}")
            continue
        if card.cost != int(row["ManaCost"]):
            print(f"{card.name}: cost {card.cost} here, {row['ManaCost']} "
                  f"in the game ({row['Name']})", file=sys.stderr)  # fmt: skip
        cards[card.name] = card_stats(card, row, sections, game_to_bot)

    towers = {}
    for name, game_name in (
        ("princess", "PrincessTower"),
        ("king", "KingTower"),
    ):
        entry = entities[game_name]
        damage, _, _ = damage_of(entry, sections)
        # Towers grow with level by their own table (their projectiles'
        # DamageScalingMode), which isn't in these files: only level 1.
        towers[name] = {
            "game_name": game_name,
            "hitpoints_level_1": entry["Hitpoints"],
            "damage_level_1": damage,
            "hit_speed": seconds(entry.get("HitSpeed")),
            "range": tiles(entry.get("Range")),
        }

    data = {
        "source": "Clash Royale's logic files, exported by "
        "dev/game_data/export_game_data.py",
        "level_scaling": "A stat at level L is the level-1 value times "
        "multipliers[L - 1] / 100, rounded down.",
        "multipliers": rarities()["Common"]["multipliers"],
        "rarities": {
            name.lower(): {"min_level": r["min_level"]}
            for name, r in rarities().items()
        },
        "units": units,
        "cards": cards,
        "towers": towers,
        "elixir": elixir_timeline(),
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    print(f"{len(units)} units, {len(cards)} cards -> {OUT}")
    if missing:
        print(f"Not in the game data: {', '.join(missing)}", file=sys.stderr)


if __name__ == "__main__":
    main()
