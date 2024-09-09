from dataclasses import asdict
from dataclasses import dataclass
from typing import List

from clashroyalebuildabot.namespaces.units import Unit
from clashroyalebuildabot.namespaces.units import Units


@dataclass(frozen=True)
class Card:
    name: str
    target_anywhere: bool
    cost: int
    units: List[Unit]
    id_: int

    def __hash__(self):
        return hash(self.name)


@dataclass(frozen=True)
class _CardsNamespace:
    ARCHER_QUEEN: Card = Card(
        "archer_queen", False, 5, [Units.ARCHER_QUEEN], 26000072
    )
    ARCHERS: Card = Card("archers", False, 3, [Units.ARCHER], 26000001)
    ARROWS: Card = Card("arrows", True, 3, [], 28000001)
    BABY_DRAGON: Card = Card(
        "baby_dragon", False, 4, [Units.BABY_DRAGON], 26000015
    )
    BALLOON: Card = Card("balloon", False, 5, [Units.BALLOON], 26000006)
    BANDIT: Card = Card("bandit", False, 3, [Units.BANDIT], 26000046)
    BARBARIAN_BARREL: Card = Card(
        "barbarian_barrel", True, 2, [Units.BARBARIAN], 28000015
    )
    BARBARIAN_HUT: Card = Card(
        "barbarian_hut",
        False,
        7,
        [Units.BARBARIAN_HUT, Units.BARBARIAN],
        27000005,
    )
    BARBARIANS: Card = Card(
        "barbarians", False, 5, [Units.BARBARIAN], 26000008
    )
    BATS: Card = Card("bats", False, 2, [Units.BAT], 26000049)
    BATTLE_HEALER: Card = Card(
        "battle_healer", False, 4, [Units.BATTLE_HEALER], 26000068
    )
    BATTLE_RAM: Card = Card(
        "battle_ram", False, 4, [Units.BATTLE_RAM], 26000036
    )
    BLANK: Card = Card("blank", False, 11, [], -1)
    BOMBER: Card = Card("bomber", False, 2, [Units.BOMBER], 26000013)
    BOMB_TOWER: Card = Card(
        "bomb_tower", False, 4, [Units.BOMB_TOWER], 27000004
    )
    BOWLER: Card = Card("bowler", False, 5, [Units.BOWLER], 26000034)
    CANNON: Card = Card("cannon", False, 3, [Units.CANNON], 27000000)
    CANNON_CART: Card = Card(
        "cannon_cart", False, 5, [Units.CANNON_CART], 26000054
    )
    CLONE: Card = Card("clone", True, 3, [], 28000013)
    DART_GOBLIN: Card = Card(
        "dart_goblin", False, 3, [Units.DART_GOBLIN], 26000027
    )
    DARK_PRINCE: Card = Card(
        "dark_prince", False, 4, [Units.DARK_PRINCE], 26000040
    )
    EARTHQUAKE: Card = Card("earthquake", True, 3, [], 28000014)
    ELECTRO_DRAGON: Card = Card(
        "electro_dragon", False, 5, [Units.ELECTRO_DRAGON], 26000063
    )
    ELECTRO_GIANT: Card = Card(
        "electro_giant", False, 7, [Units.ELECTRO_GIANT], 26000085
    )
    ELECTRO_SPIRIT: Card = Card(
        "electro_spirit", False, 1, [Units.ELECTRO_SPIRIT], 26000084
    )
    ELECTRO_WIZARD: Card = Card(
        "electro_wizard", False, 4, [Units.ELECTRO_WIZARD], 26000042
    )
    ELITE_BARBARIANS: Card = Card(
        "elite_barbarians", False, 6, [Units.ELITE_BARBARIAN], 26000043
    )
    ELIXIR_COLLECTOR: Card = Card(
        "elixir_collector", False, 6, [Units.ELIXIR_COLLECTOR], 27000007
    )
    ELIXIR_GOLEM: Card = Card(
        "elixir_golem",
        False,
        3,
        [
            Units.ELIXIR_GOLEM_LARGE,
            Units.ELIXIR_GOLEM_MEDIUM,
            Units.ELIXIR_GOLEM_SMALL,
        ],
        26000067,
    )
    EXECUTIONER: Card = Card(
        "executioner", False, 5, [Units.EXECUTIONER], 26000045
    )
    FIRE_SPIRIT: Card = Card(
        "fire_spirit", False, 1, [Units.FIRE_SPIRIT], 26000031
    )
    FIREBALL: Card = Card("fireball", True, 4, [], 28000000)
    FIRECRACKER: Card = Card(
        "firecracker", False, 3, [Units.FIRE_CRACKER], 26000064
    )
    FISHERMAN: Card = Card("fisherman", False, 3, [Units.FISHERMAN], 26000061)
    FLYING_MACHINE: Card = Card(
        "flying_machine", False, 4, [Units.FLYING_MACHINE], 26000057
    )
    FREEZE: Card = Card("freeze", True, 4, [], 28000005)
    FURNACE: Card = Card("furnace", False, 4, [Units.FURNACE], 27000010)
    GIANT: Card = Card("giant", False, 5, [Units.GIANT], 26000003)
    GIANT_SKELETON: Card = Card(
        "giant_skeleton", False, 6, [Units.GIANT_SKELETON], 26000020
    )
    GIANT_SNOWBALL: Card = Card("giant_snowball", True, 2, [], 28000017)
    GOBLINS: Card = Card("goblins", False, 2, [Units.GOBLIN], 26000002)
    GOBLIN_BARREL: Card = Card(
        "goblin_barrel", True, 3, [Units.GOBLIN], 28000004
    )
    GOBLIN_CAGE: Card = Card(
        "goblin_cage", False, 4, [Units.GOBLIN_CAGE, Units.BRAWLER], 27000012
    )
    GOBLIN_DRILL: Card = Card(
        "goblin_drill", True, 4, [Units.GOBLIN_DRILL, Units.GOBLIN], 27000013
    )
    GOBLIN_GANG: Card = Card(
        "goblin_gang", False, 3, [Units.GOBLIN, Units.SPEAR_GOBLIN], 26000041
    )
    GOBLIN_GIANT: Card = Card(
        "goblin_giant", False, 6, [Units.SPEAR_GOBLIN], 26000060
    )
    GOBLIN_HUT: Card = Card(
        "goblin_hut",
        False,
        5,
        [Units.GOBLIN_HUT, Units.SPEAR_GOBLIN],
        27000001,
    )
    GOLDEN_KNIGHT: Card = Card(
        "golden_knight", False, 4, [Units.GOLDEN_KNIGHT], 26000074
    )
    GOLEM: Card = Card(
        "golem", False, 8, [Units.GOLEM, Units.GOLEMITE], 26000009
    )
    GRAVEYARD: Card = Card("graveyard", True, 5, [Units.SKELETON], 28000010)
    GUARDS: Card = Card("guards", False, 3, [Units.GUARD], 26000025)
    HEAL_SPIRIT: Card = Card(
        "heal_spirit", False, 1, [Units.HEAL_SPIRIT], 28000016
    )
    HOG_RIDER: Card = Card("hog_rider", False, 4, [Units.HOG_RIDER], 26000021)
    HUNTER: Card = Card("hunter", False, 4, [Units.HUNTER], 26000044)
    ICE_GOLEM: Card = Card("ice_golem", False, 2, [Units.ICE_GOLEM], 26000038)
    ICE_SPIRIT: Card = Card(
        "ice_spirit", False, 1, [Units.ICE_SPIRIT], 26000030
    )
    ICE_WIZARD: Card = Card(
        "ice_wizard", False, 3, [Units.ICE_WIZARD], 26000023
    )
    INFERNO_DRAGON: Card = Card(
        "inferno_dragon", False, 4, [Units.INFERNO_DRAGON], 26000037
    )
    INFERNO_TOWER: Card = Card(
        "inferno_tower", False, 5, [Units.INFERNO_TOWER], 27000003
    )
    KNIGHT: Card = Card("knight", False, 3, [Units.KNIGHT], 26000000)
    LAVA_HOUND: Card = Card(
        "lava_hound", False, 7, [Units.LAVA_HOUND, Units.LAVA_PUP], 26000029
    )
    LIGHTNING: Card = Card("lightning", True, 6, [], 28000007)
    LITTLE_PRINCE: Card = Card(
        "little_prince",
        False,
        3,
        [Units.LITTLE_PRINCE, Units.ROYAL_GUARDIAN],
        26000093,
    )
    LUMBERJACK: Card = Card(
        "lumberjack", False, 4, [Units.LUMBERJACK], 26000035
    )
    MAGIC_ARCHER: Card = Card(
        "magic_archer", False, 4, [Units.MAGIC_ARCHER], 26000062
    )
    MEGA_KNIGHT: Card = Card(
        "mega_knight", False, 7, [Units.MEGA_KNIGHT], 26000055
    )
    MEGA_MINION: Card = Card(
        "mega_minion", False, 3, [Units.MEGA_MINION], 26000039
    )
    MIGHTY_MINER: Card = Card(
        "mighty_miner", False, 4, [Units.MIGHTY_MINER], 26000065
    )
    MINER: Card = Card("miner", False, 3, [Units.MINER], 26000032)
    MINIONS: Card = Card("minions", False, 3, [Units.MINION], 26000005)
    MINION_HORDE: Card = Card(
        "minion_horde", False, 5, [Units.MINION], 26000022
    )
    MINIPEKKA: Card = Card("minipekka", False, 4, [Units.MINIPEKKA], 26000018)
    MIRROR: Card = Card("mirror", True, -1, [], 28000006)
    MONK: Card = Card("monk", False, 5, [Units.MONK], 26000077)
    MORTAR: Card = Card("mortar", False, 4, [Units.MORTAR], 27000002)
    MOTHER_WITCH: Card = Card(
        "mother_witch", False, 4, [Units.MOTHER_WITCH, Units.HOG], 26000083
    )
    MUSKETEER: Card = Card("musketeer", False, 4, [Units.MUSKETEER], 26000014)
    NIGHT_WITCH: Card = Card(
        "night_witch", False, 4, [Units.NIGHT_WITCH, Units.BAT], 26000048
    )
    PEKKA: Card = Card("pekka", False, 7, [Units.PEKKA], 26000004)
    PHOENIX: Card = Card(
        "phoenix",
        False,
        4,
        [Units.PHOENIX_LARGE, Units.PHOENIX_EGG, Units.PHOENIX_SMALL],
        26000087,
    )
    POISON: Card = Card("poison", True, 4, [], 28000009)
    PRINCE: Card = Card("prince", False, 5, [Units.PRINCE], 26000016)
    PRINCESS: Card = Card("princess", False, 3, [Units.PRINCESS], 26000026)
    RAGE: Card = Card("rage", True, 2, [], 28000002)
    RAM_RIDER: Card = Card("ram_rider", False, 5, [Units.RAM_RIDER], 26000051)
    RASCALS: Card = Card(
        "rascals", False, 5, [Units.RASCAL_BOY, Units.RASCAL_GIRL], 26000053
    )
    ROCKET: Card = Card("rocket", True, 6, [], 28000003)
    ROYAL_DELIVERY: Card = Card(
        "royal_delivery", False, 3, [Units.ROYAL_RECRUIT], 28000018
    )
    ROYAL_GHOST: Card = Card(
        "royal_ghost", False, 3, [Units.ROYAL_GHOST], 26000050
    )
    ROYAL_GIANT: Card = Card(
        "royal_giant", False, 6, [Units.ROYAL_GIANT], 26000024
    )
    ROYAL_HOGS: Card = Card(
        "royal_hogs", False, 5, [Units.ROYAL_HOG], 26000059
    )
    ROYAL_RECRUITS: Card = Card(
        "royal_recruits", False, 7, [Units.ROYAL_RECRUIT], 26000047
    )
    SKELETONS: Card = Card("skeletons", False, 1, [Units.SKELETON], 26000010)
    SKELETON_ARMY: Card = Card(
        "skeleton_army", False, 3, [Units.SKELETON], 26000012
    )
    SKELETON_BARREL: Card = Card(
        "skeleton_barrel", False, 3, [Units.SKELETON], 26000056
    )
    SKELETON_DRAGONS: Card = Card(
        "skeleton_dragons", False, 4, [Units.SKELETON_DRAGON], 26000080
    )
    SKELETON_KING: Card = Card(
        "skeleton_king",
        False,
        4,
        [Units.SKELETON_KING, Units.SKELETON],
        26000069,
    )
    SPARKY: Card = Card("sparky", False, 6, [Units.SPARKY], 26000033)
    SPEAR_GOBLINS: Card = Card(
        "spear_goblins", False, 2, [Units.SPEAR_GOBLIN], 26000019
    )
    TESLA: Card = Card("tesla", False, 4, [Units.TESLA], 27000006)
    THE_LOG: Card = Card("the_log", True, 2, [], 28000011)
    THREE_MUSKETEERS: Card = Card(
        "three_musketeers", False, 9, [Units.MUSKETEER], 26000028
    )
    TOMBSTONE: Card = Card("tombstone", False, 3, [Units.TOMBSTONE], 27000009)
    TORNADO: Card = Card("tornado", True, 3, [], 28000012)
    VALKYRIE: Card = Card("valkyrie", False, 4, [Units.VALKYRIE], 26000011)
    WALL_BREAKERS: Card = Card(
        "wall_breakers", False, 2, [Units.WALL_BREAKER], 26000058
    )
    WITCH: Card = Card(
        "witch", False, 5, [Units.WITCH, Units.SKELETON], 26000007
    )
    WIZARD: Card = Card("wizard", False, 5, [Units.WIZARD], 26000017)
    X_BOW: Card = Card("x_bow", False, 6, [Units.X_BOW], 27000008)
    ZAP: Card = Card("zap", True, 2, [], 28000008)
    ZAPPIES: Card = Card("zappies", False, 4, [Units.ZAPPY], 26000052)


Cards = _CardsNamespace()
NAME2CARD = dict(asdict(Cards).items())
