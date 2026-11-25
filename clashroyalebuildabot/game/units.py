from dataclasses import fields
from enum import StrEnum, auto

from pydantic.dataclasses import dataclass


class UnitCategory(StrEnum):
    TROOP = auto()
    BUILDING = auto()


class Target(StrEnum):
    AIR = auto()
    GROUND = auto()
    BUILDINGS = auto()
    ALL = auto()


class Transport(StrEnum):
    AIR = auto()
    GROUND = auto()


@dataclass(frozen=True)
class Unit:
    name: str
    category: UnitCategory
    target: Target | None = None
    transport: Transport | None = None


@dataclass(frozen=True)
class Position:
    bbox: tuple[int, int, int, int]
    conf: float
    tile_x: int
    tile_y: int


@dataclass(frozen=True)
class UnitDetection:
    unit: Unit
    position: Position


@dataclass(frozen=True)
class _UnitsNamespace:
    ARCHER: Unit = Unit(
        "archer",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    ARCHER_QUEEN: Unit = Unit(
        "archer_queen",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    BABY_DRAGON: Unit = Unit(
        "baby_dragon",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.AIR,
    )
    BALLOON: Unit = Unit(
        "balloon",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.AIR,
    )
    BANDIT: Unit = Unit(
        "bandit",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    BARBARIAN: Unit = Unit(
        "barbarian",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    BARBARIAN_HUT: Unit = Unit("barbarian_hut", category=UnitCategory.BUILDING)
    BAT: Unit = Unit(
        "bat",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.AIR,
    )
    BATTLE_HEALER: Unit = Unit(
        "battle_healer",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    BATTLE_RAM: Unit = Unit(
        "battle_ram",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    BERSERKER: Unit = Unit(
        "berserker",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    BOMB_TOWER: Unit = Unit(
        "bomb_tower",
        category=UnitCategory.BUILDING,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    BOMBER: Unit = Unit(
        "bomber",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    BOSS_BANDIT: Unit = Unit(
        "boss_bandit",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    BOWLER: Unit = Unit(
        "bowler",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    BRAWLER: Unit = Unit(
        "brawler",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    CANNON: Unit = Unit(
        "cannon",
        category=UnitCategory.BUILDING,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    CANNON_CART: Unit = Unit(
        "cannon_cart",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    DARK_PRINCE: Unit = Unit(
        "dark_prince",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    DART_GOBLIN: Unit = Unit(
        "dart_goblin",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    ELECTRO_DRAGON: Unit = Unit(
        "electro_dragon",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.AIR,
    )
    ELECTRO_GIANT: Unit = Unit(
        "electro_giant",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    ELECTRO_SPIRIT: Unit = Unit(
        "electro_spirit",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    ELECTRO_WIZARD: Unit = Unit(
        "electro_wizard",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    ELITE_BARBARIAN: Unit = Unit(
        "elite_barbarian",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    ELIXIR_COLLECTOR: Unit = Unit(
        "elixir_collector", category=UnitCategory.BUILDING
    )
    ELIXIR_GOLEM_LARGE: Unit = Unit(
        "elixir_golem_large",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    ELIXIR_GOLEM_MEDIUM: Unit = Unit(
        "elixir_golem_medium",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    ELIXIR_GOLEM_SMALL: Unit = Unit(
        "elixir_golem_small",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    EXECUTIONER: Unit = Unit(
        "executioner",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    FIRE_SPIRIT: Unit = Unit(
        "fire_spirit",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    FIRE_CRACKER: Unit = Unit(
        "firecracker",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    FISHERMAN: Unit = Unit(
        "fisherman",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    FLYING_MACHINE: Unit = Unit(
        "flying_machine",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.AIR,
    )
    FURNACE: Unit = Unit("furnace", category=UnitCategory.BUILDING)
    GIANT: Unit = Unit(
        "giant",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    GIANT_SKELETON: Unit = Unit(
        "giant_skeleton",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    GIANT_SNOWBALL: Unit = Unit("giant_snowball", category=UnitCategory.TROOP)
    GOBLIN: Unit = Unit(
        "goblin",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    GOBLIN_CAGE: Unit = Unit("goblin_cage", category=UnitCategory.BUILDING)
    GOBLIN_DEMOLISHER: Unit = Unit(
        "goblin_demolisher",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    GOBLIN_DRILL: Unit = Unit(
        "goblin_drill", category=UnitCategory.BUILDING, target=Target.GROUND
    )
    GOBLIN_HUT: Unit = Unit("goblin_hut", category=UnitCategory.BUILDING)
    GOBLIN_MACHINE: Unit = Unit(
        "goblin_machine",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    GOBLINSTEIN: Unit = Unit(
        "goblinstein",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    GOBLINSTEIN_DOCTOR: Unit = Unit(
        "goblinstein_doctor",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    GOLDEN_KNIGHT: Unit = Unit(
        "golden_knight",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    GOLEM: Unit = Unit(
        "golem",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    GOLEMITE: Unit = Unit(
        "golemite",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    GUARD: Unit = Unit(
        "guard",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    HEAL_SPIRIT: Unit = Unit(
        "heal_spirit",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    HOG: Unit = Unit(
        "hog",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    HOG_RIDER: Unit = Unit(
        "hog_rider",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    HUNTER: Unit = Unit(
        "hunter",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    ICE_GOLEM: Unit = Unit(
        "ice_golem",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    ICE_SPIRIT: Unit = Unit(
        "ice_spirit",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    ICE_WIZARD: Unit = Unit(
        "ice_wizard",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    INFERNO_DRAGON: Unit = Unit(
        "inferno_dragon",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.AIR,
    )
    INFERNO_TOWER: Unit = Unit("inferno_tower", category=UnitCategory.BUILDING)
    KNIGHT: Unit = Unit(
        "knight",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    LAVA_HOUND: Unit = Unit(
        "lava_hound",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.AIR,
    )
    LAVA_PUP: Unit = Unit(
        "lava_pup",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.AIR,
    )
    LITTLE_PRINCE: Unit = Unit(
        "little_prince",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    LUMBERJACK: Unit = Unit(
        "lumberjack",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    MAGIC_ARCHER: Unit = Unit(
        "magic_archer",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    MEGA_KNIGHT: Unit = Unit(
        "mega_knight",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    MEGA_MINION: Unit = Unit(
        "mega_minion",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.AIR,
    )
    MIGHTY_MINER: Unit = Unit(
        "mighty_miner",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    MINER: Unit = Unit(
        "miner",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    MINION: Unit = Unit(
        "minion",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.AIR,
    )
    MINIPEKKA: Unit = Unit(
        "minipekka",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    MONK: Unit = Unit(
        "monk",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    MORTAR: Unit = Unit(
        "mortar",
        category=UnitCategory.BUILDING,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    MOTHER_WITCH: Unit = Unit(
        "mother_witch",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    MUSKETEER: Unit = Unit(
        "musketeer",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    NIGHT_WITCH: Unit = Unit(
        "night_witch",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    PEKKA: Unit = Unit(
        "pekka",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    PHOENIX_EGG: Unit = Unit(
        "phoenix_egg", category=UnitCategory.TROOP, transport=Transport.GROUND
    )
    PHOENIX_LARGE: Unit = Unit(
        "phoenix_large",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.AIR,
    )
    PHOENIX_SMALL: Unit = Unit(
        "phoenix_small",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.AIR,
    )
    PRINCE: Unit = Unit(
        "prince",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    PRINCESS: Unit = Unit(
        "princess",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    RAM_RIDER: Unit = Unit(
        "ram_rider",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    RASCAL_BOY: Unit = Unit(
        "rascal_boy",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    RASCAL_GIRL: Unit = Unit(
        "rascal_girl",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    ROYAL_GHOST: Unit = Unit(
        "royal_ghost",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    ROYAL_GIANT: Unit = Unit(
        "royal_giant",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    ROYAL_GUARDIAN: Unit = Unit(
        "royal_guardian",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    ROYAL_HOG: Unit = Unit(
        "royal_hog",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    ROYAL_RECRUIT: Unit = Unit(
        "royal_recruit",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    RUNE_GIANT: Unit = Unit(
        "rune_giant",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    SKELETON: Unit = Unit(
        "skeleton",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    SKELETON_DRAGON: Unit = Unit(
        "skeleton_dragon",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.AIR,
    )
    SKELETON_KING: Unit = Unit(
        "skeleton_king",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    SPARKY: Unit = Unit(
        "sparky",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    SPEAR_GOBLIN: Unit = Unit(
        "spear_goblin",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    SPIRIT_EMPRESS: Unit = Unit(
        "spirit_empress",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    SPIRIT_EMPRESS_MOUNTED: Unit = Unit(
        "spirit_empress_mounted",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.AIR,
    )
    SUSPICIOUS_BUSH: Unit = Unit(
        "suspicious_bush",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    TESLA: Unit = Unit(
        "tesla",
        category=UnitCategory.BUILDING,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    TOMBSTONE: Unit = Unit("tombstone", category=UnitCategory.BUILDING)
    VALKYRIE: Unit = Unit(
        "valkyrie",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    WALL_BREAKER: Unit = Unit(
        "wall_breaker",
        category=UnitCategory.TROOP,
        target=Target.BUILDINGS,
        transport=Transport.GROUND,
    )
    WITCH: Unit = Unit(
        "witch",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    WIZARD: Unit = Unit(
        "wizard",
        category=UnitCategory.TROOP,
        target=Target.ALL,
        transport=Transport.GROUND,
    )
    X_BOW: Unit = Unit(
        "x_bow",
        category=UnitCategory.BUILDING,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )
    ZAPPY: Unit = Unit(
        "zappy",
        category=UnitCategory.TROOP,
        target=Target.GROUND,
        transport=Transport.GROUND,
    )

    def all(self) -> tuple[Unit, ...]:
        """Every unit, in the order they're listed above."""
        return tuple(getattr(self, field.name) for field in fields(self))


Units = _UnitsNamespace()
