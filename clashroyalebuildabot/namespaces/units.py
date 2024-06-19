from dataclasses import asdict
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class Unit:
    name: str
    category: Literal["troop", "spell", "building"]
    target: Optional[Literal["air", "ground", "buildings", "all"]]
    transport: Optional[Literal["air", "ground"]]


@dataclass(frozen=True)
class _UnitsNamespace:
    ARCHER: Unit = ("archer", "troop", "both", "ground")
    BARBARIAN: Unit = ("barbarian", "troop", "ground", "ground")
    BARBARIAN_HUT: Unit = ("barbarian_hut", "building", None, None)
    BOMBER: Unit = ("bomber", "troop", "ground", "ground")
    BOMB_TOWER: Unit = ("bomb_tower", "building", "ground", "ground")
    BRAWLER: Unit = ("brawler", "troop", "ground", "ground")
    CANNON: Unit = ("cannon", "building", "ground", "ground")
    DARK_PRINCE: Unit = ("dark_prince", "troop", "ground", "ground")
    ELIXIR_COLLECTOR: Unit = ("elixir_collector", "building")
    FURNACE: Unit = ("furnace", "building", None, None)
    GIANT: Unit = ("giant", "troop", "ground", "ground")
    GOBLIN: Unit = ("goblin", "troop", "ground", "ground")
    GOBLIN_CAGE: Unit = ("goblin_cage", "building", None, None)
    GOBLIN_HUT: Unit = ("goblin_hut", "building", None, None)
    HUNGRY_DRAGON: Unit = ("hungry_dragon", "troop", "all", "air")
    HUNTER: Unit = ("hunter", "troop", "all", "ground")
    ICE_GOLEM: Unit = ("ice_golem", "troop", "buildings", "ground")
    ICE_SPIRIT: Unit = ("ice_spirit", "troop", "all", "ground")
    INFERNO_TOWER: Unit = ("inferno_tower", "building")
    KNIGHT: Unit = ("knight", "troop", "ground", "ground")
    MINION: Unit = ("minion", "troop", "both", "air")
    MINIPEKKA: Unit = ("minipekka", "troop", "ground", "ground")
    MORTAR: Unit = ("mortar", "building", "ground", "ground")
    MUSKETEER: Unit = ("musketeer", "troop", "both", "ground")
    PRINCE: Unit = ("prince", "troop", "ground", "ground")
    ROYAL_HOG: Unit = ("royal_hog", "troop", "buildings", "ground")
    SKELETON: Unit = ("skeleton", "troop", "ground", "ground")
    SPEAR_GOBLIN: Unit = ("spear_goblin", "troop", "both", "ground")
    TESLA: Unit = ("tesla", "building", "both", "ground")
    TOMBSTONE: Unit = ("tombstone", "building", None, None)
    VALKYRIE: Unit = ("valkyrie", "troop", "ground", "ground")
    WALL_BREAKER: Unit = ("wall_breaker", "troop", "buildings", "ground")
    X_BOW: Unit = ("x_bow", "building", "ground", "ground")


Units = _UnitsNamespace()
NAME2UNIT = dict(asdict(Units).items())
