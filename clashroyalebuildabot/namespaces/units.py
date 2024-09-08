from dataclasses import asdict
from dataclasses import dataclass
from typing import Literal, Optional, Tuple


@dataclass(frozen=True)
class UnitCategory:
    TROOP: str = "troop"
    BUILDING: str = "building"


@dataclass(frozen=True)
class Target:
    AIR: str = "air"
    GROUND: str = "ground"
    BUILDINGS: str = "buildings"
    ALL: str = "all"


@dataclass(frozen=True)
class Transport:
    AIR: str = "air"
    GROUND: str = "ground"


@dataclass(frozen=True)
class Unit:
    name: str
    category: Literal[UnitCategory.TROOP, UnitCategory.BUILDING]
    target: Optional[Literal[Target.GROUND, Target.BUILDINGS, Target.ALL]]
    transport: Optional[Literal[Transport.AIR, Transport.GROUND]]


@dataclass(frozen=True)
class Position:
    bbox: Tuple[int, int, int, int]
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
        "archer", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    ARCHER_QUEEN: Unit = Unit(
        "archer_queen", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    BABY_DRAGON: Unit = Unit(
        "baby_dragon", UnitCategory.TROOP, Target.ALL, Transport.AIR
    )
    BALLOON: Unit = Unit(
        "balloon", UnitCategory.TROOP, Target.BUILDINGS, Transport.AIR
    )
    BANDIT: Unit = Unit(
        "bandit", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    BARBARIAN: Unit = Unit(
        "barbarian", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    BARBARIAN_HUT: Unit = Unit(
        "barbarian_hut", UnitCategory.BUILDING, None, None
    )
    BAT: Unit = Unit("bat", UnitCategory.TROOP, Target.ALL, Transport.AIR)
    BATTLE_HEALER: Unit = Unit(
        "battle_healer", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    BATTLE_RAM: Unit = Unit(
        "battle_ram",
        UnitCategory.TROOP,
        UnitCategory.BUILDING,
        Transport.GROUND,
    )
    BOMB_TOWER: Unit = Unit(
        "bomb_tower", UnitCategory.BUILDING, Target.GROUND, Transport.GROUND
    )
    BOMBER: Unit = Unit(
        "bomber", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    BOWLER: Unit = Unit(
        "bowler", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    BRAWLER: Unit = Unit(
        "brawler", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    CANNON: Unit = Unit(
        "cannon", UnitCategory.BUILDING, Target.GROUND, Transport.GROUND
    )
    CANNON_CART: Unit = Unit(
        "cannon_cart", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    DARK_PRINCE: Unit = Unit(
        "dark_prince", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    DART_GOBLIN: Unit = Unit(
        "dart_goblin", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    ELECTRO_DRAGON: Unit = Unit(
        "electro_dragon", UnitCategory.TROOP, Target.ALL, Transport.AIR
    )
    ELECTRO_GIANT: Unit = Unit(
        "electro_giant", UnitCategory.TROOP, Target.BUILDINGS, Transport.GROUND
    )
    ELECTRO_SPIRIT: Unit = Unit(
        "electro_spirit", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    ELECTRO_WIZARD: Unit = Unit(
        "electro_wizard", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    ELITE_BARBARIAN: Unit = Unit(
        "elite_barbarian", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    ELIXIR_COLLECTOR: Unit = Unit(
        "elixir_collector", UnitCategory.BUILDING, None, None
    )
    ELIXIR_GOLEM_LARGE: Unit = Unit(
        "elixir_golem_large",
        UnitCategory.TROOP,
        Target.BUILDINGS,
        Transport.GROUND,
    )
    ELIXIR_GOLEM_MEDIUM: Unit = Unit(
        "elixir_golem_medium",
        UnitCategory.TROOP,
        Target.BUILDINGS,
        Transport.GROUND,
    )
    ELIXIR_GOLEM_SMALL: Unit = Unit(
        "elixir_golem_small",
        UnitCategory.TROOP,
        Target.BUILDINGS,
        Transport.GROUND,
    )
    EXECUTIONER: Unit = Unit(
        "executioner", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    FIRE_SPIRIT: Unit = Unit(
        "fire_spirit", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    FIRE_CRACKER: Unit = Unit(
        "firecracker", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    FISHERMAN: Unit = Unit(
        "fisherman", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    FLYING_MACHINE: Unit = Unit(
        "flying_machine", UnitCategory.TROOP, Target.ALL, Transport.AIR
    )
    FURNACE: Unit = Unit("furnace", UnitCategory.BUILDING, None, None)
    GIANT: Unit = Unit(
        "giant", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    GIANT_SKELETON: Unit = Unit(
        "giant_skeleton", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    # This is mistake, remove the snowball next time we train the object detector
    GIANT_SNOWBALL: Unit = Unit(
        "giant_snowball", UnitCategory.TROOP, None, None
    )
    GOBLIN: Unit = Unit(
        "goblin", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    GOBLIN_CAGE: Unit = Unit("goblin_cage", UnitCategory.BUILDING, None, None)
    GOBLIN_DRILL: Unit = Unit(
        "goblin_drill", UnitCategory.BUILDING, Target.GROUND, None
    )
    GOBLIN_HUT: Unit = Unit("goblin_hut", UnitCategory.BUILDING, None, None)
    GOLDEN_KNIGHT: Unit = Unit(
        "golden_knight", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    GOLEM: Unit = Unit(
        "golem", UnitCategory.TROOP, Target.BUILDINGS, Transport.GROUND
    )
    GOLEMITE: Unit = Unit(
        "golemite", UnitCategory.TROOP, Target.BUILDINGS, Transport.GROUND
    )
    GUARD: Unit = Unit(
        "guard", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    HEAL_SPIRIT: Unit = Unit(
        "heal_spirit", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    HOG: Unit = Unit(
        "hog", UnitCategory.TROOP, Target.BUILDINGS, Transport.GROUND
    )
    HOG_RIDER: Unit = Unit(
        "hog_rider", UnitCategory.TROOP, Target.BUILDINGS, Transport.GROUND
    )
    HUNTER: Unit = Unit(
        "hunter", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    ICE_GOLEM: Unit = Unit(
        "ice_golem", UnitCategory.TROOP, Target.BUILDINGS, Transport.GROUND
    )
    ICE_SPIRIT: Unit = Unit(
        "ice_spirit", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    ICE_WIZARD: Unit = Unit(
        "ice_wizard", UnitCategory.TROOP, Target.ALL, Transport.AIR
    )
    INFERNO_DRAGON: Unit = Unit(
        "inferno_dragon", UnitCategory.TROOP, Target.ALL, Transport.AIR
    )
    INFERNO_TOWER: Unit = Unit(
        "inferno_tower", UnitCategory.BUILDING, None, None
    )
    KNIGHT: Unit = Unit(
        "knight", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    LAVA_HOUND: Unit = Unit(
        "lava_hound", UnitCategory.TROOP, Target.BUILDINGS, Transport.AIR
    )
    LAVA_PUP: Unit = Unit(
        "lava_pup", UnitCategory.TROOP, Target.BUILDINGS, Transport.AIR
    )
    LITTLE_PRINCE: Unit = Unit(
        "little_prince", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    LUMBERJACK: Unit = Unit(
        "lumberjack", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    MAGIC_ARCHER: Unit = Unit(
        "magic_archer", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    MEGA_KNIGHT: Unit = Unit(
        "mega_knight", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    MEGA_MINION: Unit = Unit(
        "mega_minion", UnitCategory.TROOP, Target.ALL, Transport.AIR
    )
    MIGHTY_MINER: Unit = Unit(
        "mighty_miner", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    MINER: Unit = Unit(
        "miner", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    MINION: Unit = Unit(
        "minion", UnitCategory.TROOP, Target.ALL, Transport.AIR
    )
    MINIPEKKA: Unit = Unit(
        "minipekka", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    MONK: Unit = Unit(
        "monk", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    MORTAR: Unit = Unit(
        "mortar", UnitCategory.BUILDING, Target.GROUND, Transport.GROUND
    )
    MOTHER_WITCH: Unit = Unit(
        "mother_witch", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    MUSKETEER: Unit = Unit(
        "musketeer", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    NIGHT_WITCH: Unit = Unit(
        "night_witch", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    PEKKA: Unit = Unit(
        "pekka", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    PHOENIX_EGG: Unit = Unit(
        "phoenix_egg", UnitCategory.TROOP, None, Transport.GROUND
    )
    PHOENIX_LARGE: Unit = Unit(
        "phoenix_large", UnitCategory.TROOP, Target.ALL, Transport.AIR
    )
    PHOENIX_SMALL: Unit = Unit(
        "phoenix_small", UnitCategory.TROOP, Target.ALL, Transport.AIR
    )
    PRINCE: Unit = Unit(
        "prince", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    PRINCESS: Unit = Unit(
        "princess", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    RAM_RIDER: Unit = Unit(
        "ram_rider", UnitCategory.TROOP, Target.BUILDINGS, Transport.GROUND
    )
    RASCAL_BOY: Unit = Unit(
        "rascal_boy", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    RASCAL_GIRL: Unit = Unit(
        "rascal_girl", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    ROYAL_GHOST: Unit = Unit(
        "royal_ghost", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    ROYAL_GIANT: Unit = Unit(
        "royal_giant", UnitCategory.TROOP, Target.BUILDINGS, Transport.GROUND
    )
    ROYAL_GUARDIAN: Unit = Unit(
        "royal_guardian", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    ROYAL_HOG: Unit = Unit(
        "royal_hog", UnitCategory.TROOP, Target.BUILDINGS, Transport.GROUND
    )
    ROYAL_RECRUIT: Unit = Unit(
        "royal_recruit", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    SKELETON: Unit = Unit(
        "skeleton", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    SKELETON_DRAGON: Unit = Unit(
        "skeleton_dragon", UnitCategory.TROOP, Target.ALL, Transport.AIR
    )
    SKELETON_KING: Unit = Unit(
        "skeleton_king", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    SPARKY: Unit = Unit(
        "sparky", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    SPEAR_GOBLIN: Unit = Unit(
        "spear_goblin", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    TESLA: Unit = Unit(
        "tesla", UnitCategory.BUILDING, Target.ALL, Transport.GROUND
    )
    TOMBSTONE: Unit = Unit("tombstone", UnitCategory.BUILDING, None, None)
    VALKYRIE: Unit = Unit(
        "valkyrie", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )
    WALL_BREAKER: Unit = Unit(
        "wall_breaker", UnitCategory.TROOP, Target.BUILDINGS, Transport.GROUND
    )
    WITCH: Unit = Unit(
        "witch", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    WIZARD: Unit = Unit(
        "wizard", UnitCategory.TROOP, Target.ALL, Transport.GROUND
    )
    X_BOW: Unit = Unit(
        "x_bow", UnitCategory.BUILDING, Target.GROUND, Transport.GROUND
    )
    ZAPPY: Unit = Unit(
        "zappy", UnitCategory.TROOP, Target.GROUND, Transport.GROUND
    )


Units = _UnitsNamespace()
NAME2UNIT = dict(asdict(Units).items())
