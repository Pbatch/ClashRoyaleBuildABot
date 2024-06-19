from dataclasses import asdict
from dataclasses import dataclass
from typing import List, Optional

from clashroyalebuildabot.namespaces.units import Unit
from clashroyalebuildabot.namespaces.units import Units


@dataclass(frozen=True)
class Card:
    name: str
    target_anywhere: bool
    cost: int
    units: Optional[List[Unit]] = None

    def __hash__(self):
        return hash(self.name)


@dataclass(frozen=True)
class _CardsNamespace:
    ARCHER_QUEEN: Card = Card("archer_queen", False, 5)
    ARCHERS: Card = Card("archers", False, 3, [Units.ARCHER])
    ARROWS: Card = Card("arrows", True, 3)
    BALLOON: Card = Card("balloon", False, 5)
    BANDIT: Card = Card("bandit", False, 3)
    BARBARIAN_BARREL: Card = Card(
        "barbarian_barrel", True, 2, [Units.BARBARIAN]
    )
    BARBARIAN_HUT: Card = Card(
        "barbarian_hut", False, 7, [Units.BARBARIAN_HUT, Units.BARBARIAN]
    )
    BARBARIANS: Card = Card("barbarians", False, 5, [Units.BARBARIAN])
    BATS: Card = Card("bats", False, 2)
    BATTLE_HEALER: Card = Card("battle_healer", False, 4)
    BATTLE_RAM: Card = Card("battle_ram", False, 4)
    BLANK: Card = Card("blank", False, 11)
    BOMBER: Card = Card("bomber", False, 2, [Units.BOMBER])
    BOMB_TOWER: Card = Card("bomb_tower", False, 4, [Units.BOMB_TOWER])
    BOWLER: Card = Card("bowler", False, 5)
    CANNON: Card = Card("cannon", False, 3, [Units.CANNON])
    CANNON_CART: Card = Card("cannon_cart", False, 5)
    CLONE: Card = Card("clone", True, 3)
    DART_GOBLIN: Card = Card("dart_goblin", False, 3)
    DARK_PRINCE: Card = Card("dark_prince", False, 4, [Units.DARK_PRINCE])
    EARTHQUAKE: Card = Card("earthquake", True, 3)
    ELECTRO_DRAGON: Card = Card("electro_dragon", False, 5)
    ELECTRO_GIANT: Card = Card("electro_giant", False, 7)
    ELECTRO_SPIRIT: Card = Card("electro_spirit", False, 1)
    ELECTRO_WIZARD: Card = Card("electro_wizard", False, 4)
    ELITE_BARBARIANS: Card = Card("elite_barbarians", False, 6)
    ELIXIR_COLLECTOR: Card = Card(
        "elixir_collector", False, 6, [Units.ELIXIR_COLLECTOR]
    )
    ELIXIR_GOLEM: Card = Card("elixir_golem", False, 3)
    EXECUTIONER: Card = Card("executioner", False, 5)
    FIRE_SPIRIT: Card = Card("fire_spirit", False, 1)
    FIREBALL: Card = Card("fireball", True, 4)
    FIRECRACKER: Card = Card("firecracker", False, 3)
    FISHERMAN: Card = Card("fisherman", False, 3)
    FLYING_MACHINE: Card = Card("flying_machine", False, 4)
    FREEZE: Card = Card("freeze", True, 4)
    FURNACE: Card = Card("furnace", False, 4, [Units.FURNACE])
    GIANT: Card = Card("giant", False, 5, [Units.GIANT])
    GIANT_SKELETON: Card = Card("giant_skeleton", False, 6)
    GIANT_SNOWBALL: Card = Card("giant_snowball", True, 2)
    GOBLINS: Card = Card("goblins", False, 2, [Units.GOBLIN])
    GOBLIN_BARREL: Card = Card("goblin_barrel", True, 3, [Units.GOBLIN])
    GOBLIN_CAGE: Card = Card(
        "goblin_cage", False, 4, [Units.GOBLIN_CAGE, Units.BRAWLER]
    )
    GOBLIN_DRILL: Card = Card("goblin_drill", True, 4)
    GOBLIN_GANG: Card = Card(
        "goblin_gang", False, 3, [Units.GOBLIN, Units.SPEAR_GOBLIN]
    )
    GOBLIN_GIANT: Card = Card("goblin_giant", False, 6)
    GOBLIN_HUT: Card = Card(
        "goblin_hut", False, 5, [Units.GOBLIN_HUT, Units.SPEAR_GOBLIN]
    )
    GOLDEN_KNIGHT: Card = Card("golden_knight", False, 4)
    GOLEM: Card = Card("golem", False, 8)
    GRAVEYARD: Card = Card("graveyard", True, 5)
    GUARDS: Card = Card("guards", False, 3)
    HEAL_SPIRIT: Card = Card("heal_spirit", False, 1)
    HOG_RIDER: Card = Card("hog_rider", False, 4)
    HUNGRY_DRAGON: Card = Card(
        "hungry_dragon", False, 4, [Units.HUNGRY_DRAGON]
    )
    HUNTER: Card = Card("hunter", False, 4, [Units.HUNTER])
    ICE_GOLEM: Card = Card("ice_golem", False, 2, [Units.ICE_GOLEM])
    ICE_SPIRIT: Card = Card("ice_spirit", False, 1, [Units.ICE_SPIRIT])
    ICE_WIZARD: Card = Card("ice_wizard", False, 3)
    INFERNO_DRAGON: Card = Card("inferno_dragon", False, 4)
    INFERNO_TOWER: Card = Card(
        "inferno_tower", False, 5, [Units.INFERNO_TOWER]
    )
    KNIGHT: Card = Card("knight", False, 3, [Units.KNIGHT])
    LAVA_HOUND: Card = Card("lava_hound", False, 7)
    LIGHTNING: Card = Card("lightning", True, 6)
    LUMBERJACK: Card = Card("lumberjack", False, 4)
    MAGIC_ARCHER: Card = Card("magic_archer", False, 4)
    MEGA_KNIGHT: Card = Card("mega_knight", False, 7)
    MEGA_MINION: Card = Card("mega_minion", False, 3)
    MIGHTY_MINER: Card = Card("mighty_miner", False, 4)
    MINER: Card = Card("miner", False, 3)
    MINIONS: Card = Card("minions", False, 3, [Units.MINION])
    MINION_HORDE: Card = Card("minion_horde", False, 5, [Units.MINION])
    MINIPEKKA: Card = Card("minipekka", False, 4, [Units.MINIPEKKA])
    MIRROR: Card = Card("mirror", True, -1)
    MONK: Card = Card("monk", False, 5)
    MORTAR: Card = Card("mortar", False, 4, [Units.MORTAR])
    MOTHER_WITCH: Card = Card("mother_witch", False, 4)
    MUSKETEER: Card = Card("musketeer", False, 4, [Units.MUSKETEER])
    NIGHT_WITCH: Card = Card("night_witch", False, 4)
    PEKKA: Card = Card("pekka", False, 7)
    PHOENIX: Card = Card("phoenix", False, 4)
    POISON: Card = Card("poison", True, 4)
    PRINCE: Card = Card("prince", False, 5, [Units.PRINCE])
    PRINCESS: Card = Card("princess", False, 3)
    RAGE: Card = Card("rage", True, 2)
    RAM_RIDER: Card = Card("ram_rider", False, 5)
    RASCALS: Card = Card("rascals", False, 5)
    ROCKET: Card = Card("rocket", True, 6)
    ROYAL_DELIVERY: Card = Card("royal_delivery", False, 3)
    ROYAL_GHOST: Card = Card("royal_ghost", False, 3)
    ROYAL_GIANT: Card = Card("royal_giant", False, 6)
    ROYAL_HOGS: Card = Card("royal_hogs", False, 5, [Units.ROYAL_HOG])
    ROYAL_RECRUITS: Card = Card("royal_recruits", False, 7)
    SKELETONS: Card = Card("skeletons", False, 1, [Units.SKELETON])
    SKELETON_ARMY: Card = Card("skeleton_army", False, 3, [Units.SKELETON])
    SKELETON_BARREL: Card = Card("skeleton_barrel", False, 3)
    SKELETON_DRAGONS: Card = Card("skeleton_dragons", False, 4)
    SKELETON_KING: Card = Card("skeleton_king", False, 4)
    SPARKY: Card = Card("sparky", False, 6)
    SPEAR_GOBLINS: Card = Card("spear_goblins", False, 2, [Units.SPEAR_GOBLIN])
    TESLA: Card = Card("tesla", False, 4)
    THE_LOG: Card = Card("the_log", True, 2)
    THREE_MUSKETEERS: Card = Card(
        "three_musketeers", False, 9, [Units.MUSKETEER]
    )
    TOMBSTONE: Card = Card("tombstone", False, 3, [Units.TOMBSTONE])
    TORNADO: Card = Card("tornado", True, 3)
    VALKYRIE: Card = Card("valkyrie", False, 4, [Units.VALKYRIE])
    WALL_BREAKERS: Card = Card("wall_breakers", False, 2, [Units.WALL_BREAKER])
    WITCH: Card = Card("witch", False, 5)
    WIZARD: Card = Card("wizard", False, 5)
    X_BOW: Card = Card("x_bow", False, 6, [Units.X_BOW])
    ZAP: Card = Card("zap", True, 2)
    ZAPPIES: Card = Card("zappies", False, 4)


Cards = _CardsNamespace()
NAME2CARD = dict(asdict(Cards).items())
