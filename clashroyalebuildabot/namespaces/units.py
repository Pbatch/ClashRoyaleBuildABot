from dataclasses import asdict
from dataclasses import dataclass
from typing import Literal, Optional, Tuple


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
    category: Literal["troop", "spell", "building"]
    target: Optional[
        Literal[Target.AIR, Target.GROUND, Target.BUILDINGS, Target.ALL]
    ]
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
    ARCHER: Unit = Unit("archer", "troop", "both", "ground")
    BARBARIAN: Unit = Unit("barbarian", "troop", "ground", "ground")
    BARBARIAN_HUT: Unit = Unit("barbarian_hut", "building", None, None)
    BOMBER: Unit = Unit("bomber", "troop", "ground", "ground")
    BOMB_TOWER: Unit = Unit("bomb_tower", "building", "ground", "ground")
    BRAWLER: Unit = Unit("brawler", "troop", "ground", "ground")
    CANNON: Unit = Unit("cannon", "building", "ground", "ground")
    DARK_PRINCE: Unit = Unit("dark_prince", "troop", "ground", "ground")
    ELIXIR_COLLECTOR: Unit = Unit("elixir_collector", "building", None, None)
    FURNACE: Unit = Unit("furnace", "building", None, None)
    GIANT: Unit = Unit("giant", "troop", "ground", "ground")
    GOBLIN: Unit = Unit("goblin", "troop", "ground", "ground")
    GOBLIN_CAGE: Unit = Unit("goblin_cage", "building", None, None)
    GOBLIN_HUT: Unit = Unit("goblin_hut", "building", None, None)
    HUNGRY_DRAGON: Unit = Unit("hungry_dragon", "troop", "all", "air")
    HUNTER: Unit = Unit("hunter", "troop", "all", "ground")
    ICE_GOLEM: Unit = Unit("ice_golem", "troop", "buildings", "ground")
    ICE_SPIRIT: Unit = Unit("ice_spirit", "troop", "all", "ground")
    INFERNO_TOWER: Unit = Unit("inferno_tower", "building", None, None)
    KNIGHT: Unit = Unit("knight", "troop", "ground", "ground")
    MINION: Unit = Unit("minion", "troop", "both", "air")
    MINIPEKKA: Unit = Unit("minipekka", "troop", "ground", "ground")
    MORTAR: Unit = Unit("mortar", "building", "ground", "ground")
    MUSKETEER: Unit = Unit("musketeer", "troop", "both", "ground")
    PRINCE: Unit = Unit("prince", "troop", "ground", "ground")
    ROYAL_HOG: Unit = Unit("royal_hog", "troop", "buildings", "ground")
    SKELETON: Unit = Unit("skeleton", "troop", "ground", "ground")
    SPEAR_GOBLIN: Unit = Unit("spear_goblin", "troop", "both", "ground")
    TESLA: Unit = Unit("tesla", "building", "both", "ground")
    TOMBSTONE: Unit = Unit("tombstone", "building", None, None)
    VALKYRIE: Unit = Unit("valkyrie", "troop", "ground", "ground")
    WALL_BREAKER: Unit = Unit("wall_breaker", "troop", "buildings", "ground")
    X_BOW: Unit = Unit("x_bow", "building", "ground", "ground")


Units = _UnitsNamespace()
NAME2UNIT = dict(asdict(Units).items())
