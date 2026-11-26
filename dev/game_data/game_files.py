"""Reading the game's data files, as extracted from the APK by
dev/synthetic/apk_assets.py: the logic CSVs and TOMLs (Supercell-LZMA
compressed), the characters and buildings in them, and which game entities
each of the bot's unit labels is.

Standard library only, so dev/game_data/export_game_data.py runs in the
bot's own environment. apk_assets.py imports these too.
"""

import csv
import io
import lzma
import tomllib
from collections import defaultdict
from pathlib import Path

# Bot label -> game entities ("CHARACTER.X" / "BUILDING.X" names). The
# tuple's second item limits which animations count: phoenix_small is the
# Phoenix's rebirth, phoenix_large everything else.
LABELS = {
    "archer": ["Archer"],
    "archer_queen": ["ArcherQueen"],
    "baby_dragon": ["BabyDragon"],
    "balloon": ["Balloon"],
    "bandit": ["Assassin"],
    "barbarian": ["Barbarian"],
    "barbarian_hut": ["BarbarianHut"],
    "bat": ["Bat"],
    "berserker": ["Berserker"],
    "battle_healer": ["BattleHealer"],
    "battle_ram": ["BattleRam"],
    "bomb_tower": ["BombTower"],
    # BalloonBomb and BombTowerBomb share GiantSkeletonBomb's art.
    "bomb": ["GiantSkeletonBomb", "MightyMinerBomb"],
    "bomber": ["Bomber"],
    "boss_bandit": ["BossBandit"],
    "bowler": ["Bowler"],
    "brawler": ["GoblinBrawler"],
    "cannon": ["Cannon"],
    "cannon_cart": ["MovingCannon", "BrokenCannon"],
    "dark_prince": ["DarkPrince"],
    "dart_goblin": ["BlowdartGoblin"],
    "electro_dragon": ["ElectroDragon"],
    "electro_giant": ["ElectroGiant"],
    "electro_spirit": ["ElectroSpirit"],
    "electro_wizard": ["ElectroWizard"],
    "elite_barbarian": ["AngryBarbarian"],
    "elixir_collector": ["ElixirCollector"],
    "elixir_golem_large": ["ElixirGolem1"],
    "elixir_golem_medium": ["ElixirGolem2"],
    "elixir_golem_small": ["ElixirGolem4"],
    "executioner": ["AxeMan"],
    "fire_spirit": ["FireSpirits"],
    "firecracker": ["Firecracker"],
    "fisherman": ["Fisherman"],
    "flying_machine": ["DartBarrell"],
    "furnace": ["Furnace_rework"],
    "giant": ["Giant"],
    "giant_skeleton": ["GiantSkeleton"],
    # Goblin_Stab (the Goblins card), BarrelGoblin and the like share
    # Goblin's art; the Suspicious Bush's goblins have their own.
    "goblin": ["Goblin", "BushGoblin"],
    "goblin_cage": ["GoblinCage"],
    "goblin_demolisher": ["GoblinDemolisher"],
    "goblin_drill": ["GoblinDrill"],
    # Its spear goblins ride in the bag on its back.
    "goblin_giant": [("GoblinGiant", "with SpearGoblinGiant")],
    "goblin_hut": ["GoblinHut_Rework"],
    "goblin_machine": ["GoblinMachine"],
    "goblinstein": ["goblinstein"],
    "goblinstein_doctor": ["goblinstein_doctor"],
    "golden_knight": ["GoldenKnight"],
    "golem": ["Golem"],
    "golemite": ["Golemite"],
    "guard": ["SkeletonWarrior"],
    "heal_spirit": ["HealSpirit"],
    "hog": ["VoodooHog"],
    "hog_rider": ["HogRider"],
    "hunter": ["Hunter"],
    "ice_golem": ["IceGolemite"],
    "ice_spirit": ["IceSpirits"],
    "ice_wizard": ["IceWizard"],
    "inferno_dragon": ["InfernoDragon"],
    "inferno_tower": ["InfernoTower"],
    "knight": ["Knight"],
    "lava_hound": ["LavaHound"],
    "lava_pup": ["LavaPups"],
    "little_prince": ["LittlePrince"],
    "lumberjack": ["RageBarbarian"],
    "magic_archer": ["EliteArcher"],
    "mega_knight": ["MegaKnight"],
    "mega_minion": ["MegaMinion"],
    "mighty_miner": ["MightyMiner"],
    "miner": ["Miner"],
    "minion": ["Minion"],
    "minipekka": ["MiniPekka"],
    "monk": ["Monk"],
    "mortar": ["Mortar"],
    "mother_witch": ["WitchMother"],
    "musketeer": ["Musketeer"],
    "night_witch": ["DarkWitch"],
    "pekka": ["Pekka"],
    "phoenix_egg": ["PhoenixEgg"],
    "phoenix_large": [("Phoenix", "not reborn")],
    "phoenix_small": [("Phoenix", "reborn")],
    "prince": ["Prince"],
    "princess": ["Princess"],
    "ram_rider": [("Ram", "with RamRider")],
    "rascal_boy": ["RascalBoy"],
    "rascal_girl": ["RascalGirl"],
    "royal_ghost": ["Ghost"],
    "royal_giant": ["RoyalGiant"],
    "royal_hog": ["RoyalHog"],
    "royal_recruit": ["Recruit"],
    "rune_giant": ["GiantBuffer"],
    "skeleton": ["Skeleton"],
    "skeleton_barrel": ["SkeletonBalloon"],
    "skeleton_dragon": ["SkeletonDragon"],
    "skeleton_king": ["SkeletonKing"],
    "sparky": ["ZapMachine"],
    "spear_goblin": ["SpearGoblin"],
    "spirit_empress": ["MergeMaiden_Normal"],
    "spirit_empress_mounted": ["MergeMaiden_Mounted"],
    "suspicious_bush": ["SuspiciousBush"],
    "tesla": ["Tesla"],
    "tombstone": ["Tombstone"],
    "valkyrie": ["Valkyrie"],
    "wall_breaker": ["Wallbreaker"],
    "witch": ["Witch"],
    "wizard": ["Wizard"],
    "x_bow": ["Xbow"],
    "zappy": ["MiniZapMachine"],
}


def supercell_lzma(data: bytes) -> bytes:
    """Supercell stores LZMA with a 4-byte size where .lzma has 8."""
    data = data[:9] + b"\x00" * 4 + data[9:]
    return lzma.LZMADecompressor(lzma.FORMAT_ALONE).decompress(data)


def read_text(path: str | Path) -> str:
    data = Path(path).read_bytes()
    return (supercell_lzma(data) if data[:1] == b"]" else data).decode()


def read_csv(path: str | Path) -> list[list[str]]:
    return list(csv.reader(io.StringIO(read_text(path))))


def load_entities(
    logic: Path,
) -> tuple[dict[str, dict], dict[str, list[tuple[str, dict]]]]:
    """Every CHARACTER, BUILDING and EXT entry, with EXT bases resolved."""
    entries = {}
    for f in sorted(logic.rglob("*.toml")):
        try:
            data = tomllib.loads(read_text(f))
        except (tomllib.TOMLDecodeError, lzma.LZMAError, UnicodeDecodeError):
            continue  # a few buff tables repeat keys; none draws a unit
        for kind in ("CHARACTER", "BUILDING", "EXT"):
            for name, v in data.get(kind, {}).items():
                if isinstance(v, dict):
                    entries[(kind, name)] = v

    def resolved(key: tuple[str, str], depth: int = 0) -> dict:
        v = dict(entries[key])
        base = v.get("Base")
        if key[0] == "EXT" and base and depth < 5:
            kind, _, name = base.partition(".")
            if (kind, name) in entries:
                parent = resolved((kind, name), depth + 1)
                scale = v.get("Scale")
                if isinstance(scale, list):  # ["%", 120]: relative
                    v["Scale"] = parent.get("Scale", 100) * scale[1] / 100
                v = {**parent, **v}
        return v

    by_name = {}
    evolutions = defaultdict(list)
    for key in entries:
        v = resolved(key)
        if key[0] == "EXT":
            base = entries[key].get("Base", "").partition(".")[2]
            if entries[key].get("BlueExportName") and entries[key].get(
                "FileName"
            ):
                evolutions[base].append((key[1], v))
        else:
            by_name[key[1]] = v
    return by_name, evolutions
