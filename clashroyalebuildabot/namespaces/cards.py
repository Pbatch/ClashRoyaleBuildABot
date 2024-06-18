from dataclasses import dataclass, asdict
from typing import List, Optional

from clashroyalebuildabot.namespaces.units import Unit, Units


@dataclass
class Card:
    name: str
    cost: int
    units: Optional[List[Unit]]


@dataclass(frozen=True)
class _CardsNamespace:
    ARCHER_QUEEN: Card = Card("archer_queen", 5)
    ARCHERS: Card = Card("archers", 3, [Units.ARCHER])
    ARROWS: Card = Card("arrows", 3)
    BALLOON: Card = Card("balloon", 5)
    BANDIT: Card = Card("bandit", 3)
    BARBARIAN_BARREL: Card = Card("barbarian_barrel", 2, [Units.BARBARIAN])
    BARBARIAN_HUT: Card = Card(
        "barbarian_hut", 7, [Units.BARBARIAN_HUT, Units.BARBARIAN]
    )
    BARBARIANS: Card = Card("barbarians", 5, [Units.BARBARIAN])
    BATS: Card = Card("bats", 2)
    BATTLE_HEALER: Card = Card("battle_healer", 4)
    BATTLE_RAM: Card = Card("battle_ram", 4)
    BLANK: Card = Card("blank", 11, [])
    BOMBER: Card = Card("bomber", 2, [Units.BOMBER])
    BOMB_TOWER: Card = Card("bomb_tower", 4, [Units.BOMB_TOWER])
    BOWLER: Card = Card("bowler", 5)
    CANNON: Card = Card("cannon", 3, [Units.CANNON])
    CANNON_CART: Card = Card("cannon_cart", 5)
    CLONE: Card = Card("clone", 3)
    DART_GOBLIN: Card = Card("dart_goblin", 3)
    DARK_PRINCE: Card = Card("dark_prince", 4, [Units.DARK_PRINCE])
    EARTHQUAKE: Card = Card("earthquake", 3)
    ELECTRO_DRAGON: Card = Card("electro_dragon", 5)
    ELECTRO_GIANT: Card = Card("electro_giant", 7)
    ELECTRO_SPIRIT: Card = Card("electro_spirit", 1)
    ELECTRO_WIZARD: Card = Card("electro_wizard", 4)
    ELITE_BARBARIANS: Card = Card("elite_barbarians", 6)
    ELIXIR_COLLECTOR: Card = Card(
        "elixir_collector", 6, [Units.ELIXIR_COLLECTOR]
    )
    ELIXIR_GOLEM: Card = Card("elixir_golem", 3)
    EXECUTIONER: Card = Card("executioner", 5)
    FIRE_SPIRIT: Card = Card("fire_spirit", 1)
    FIREBALL: Card = Card("fireball", 4)
    FIRECRACKER: Card = Card("firecracker", 3)
    FISHERMAN: Card = Card("fisherman", 3)
    FLYING_MACHINE: Card = Card("flying_machine", 4)
    FREEZE: Card = Card("freeze", 4)
    FURNACE: Card = Card("furnace", 4, [Units.FURNACE])
    GIANT: Card = Card("giant", 5, [Units.GIANT])
    GIANT_SKELETON: Card = Card("giant_skeleton", 6)
    GIANT_SNOWBALL: Card = Card("giant_snowball", 2)
    GOBLINS: Card = Card("goblins", 2, [Units.GOBLIN])
    GOBLIN_BARREL: Card = Card("goblin_barrel", 3, [Units.GOBLIN])
    GOBLIN_CAGE: Card = Card(
        "goblin_cage", 4, [Units.GOBLIN_CAGE, Units.BRAWLER]
    )
    GOBLIN_DRILL: Card = Card("goblin_drill", 4)
    GOBLIN_GANG: Card = Card(
        "goblin_gang", 3, [Units.GOBLIN, Units.SPEAR_GOBLIN]
    )
    GOBLIN_GIANT: Card = Card("goblin_giant", 6)
    GOBLIN_HUT: Card = Card(
        "goblin_hut", 5, [Units.GOBLIN_HUT, Units.SPEAR_GOBLIN]
    )
    GOLDEN_KNIGHT: Card = Card("golden_knight", 4)
    GOLEM: Card = Card("golem", 8)
    GRAVEYARD: Card = Card("graveyard", 5)
    GUARDS: Card = Card("guards", 3)
    HEAL_SPIRIT: Card = Card("heal_spirit", 1)
    HOG_RIDER: Card = Card("hog_rider", 4)
    HUNGRY_DRAGON: Card = Card("hungry_dragon", 4, [Units.HUNGRY_DRAGON])
    HUNTER: Card = Card("hunter", 4, [Units.HUNTER])
    ICE_GOLEM: Card = Card("ice_golem", 2, [Units.ICE_GOLEM])
    ICE_SPIRIT: Card = Card("ice_spirit", 1, [Units.ICE_SPIRIT])
    ICE_WIZARD: Card = Card("ice_wizard", 3)
    INFERNO_DRAGON: Card = Card("inferno_dragon", 4)
    INFERNO_TOWER: Card = Card("inferno_tower", 5, [Units.INFERNO_TOWER])
    KNIGHT: Card = Card("knight", 3, [Units.KNIGHT])
    LAVA_HOUND: Card = Card("lava_hound", 7)
    LIGHTNING: Card = Card("lightning", 6)
    LUMBERJACK: Card = Card("lumberjack", 4)
    MAGIC_ARCHER: Card = Card("magic_archer", 4)
    MEGA_KNIGHT: Card = Card("mega_knight", 7)
    MEGA_MINION: Card = Card("mega_minion", 3)
    MIGHTY_MINER: Card = Card("mighty_miner", 4)
    MINER: Card = Card("miner", 3)
    MINIONS: Card = Card("minions", 3, [Units.MINION])
    MINION_HORDE: Card = Card("minion_horde", 5, [Units.MINION])
    MINIPEKKA: Card = Card("minipekka", 4, [Units.MINIPEKKA])
    MIRROR: Card = Card("mirror", -1)
    MONK: Card = Card("monk", 5)
    MORTAR: Card = Card("mortar", 4, [Units.MORTAR])
    MOTHER_WITCH: Card = Card("mother_witch", 4)
    MUSKETEER: Card = Card("musketeer", 4, [Units.MUSKETEER])
    NIGHT_WITCH: Card = Card("night_witch", 4)
    PEKKA: Card = Card("pekka", 7)
    PHOENIX: Card = Card("phoenix", 4)
    POISON: Card = Card("poison", 4)
    PRINCE: Card = Card("prince", 5, [Units.PRINCE])
    PRINCESS: Card = Card("princess", 3)
    RAGE: Card = Card("rage", 2)
    RAM_RIDER: Card = Card("ram_rider", 5)
    RASCALS: Card = Card("rascals", 5)
    ROCKET: Card = Card("rocket", 6)
    ROYAL_DELIVERY: Card = Card("royal_delivery", 3)
    ROYAL_GHOST: Card = Card("royal_ghost", 3)
    ROYAL_GIANT: Card = Card("royal_giant", 6)
    ROYAL_HOGS: Card = Card("royal_hogs", 5, [Units.ROYAL_HOG])
    ROYAL_RECRUITS: Card = Card("royal_recruits", 7)
    SKELETONS: Card = Card("skeletons", 1, [Units.SKELETON])
    SKELETON_ARMY: Card = Card("skeleton_army", 3, [Units.SKELETON])
    SKELETON_BARREL: Card = Card("skeleton_barrel", 3)
    SKELETON_DRAGONS: Card = Card("skeleton_dragons", 4)
    SKELETON_KING: Card = Card("skeleton_king", 4)
    SPARKY: Card = Card("sparky", 6)
    SPEAR_GOBLINS: Card = Card("spear_goblins", 2, [Units.SPEAR_GOBLIN])
    TESLA: Card = Card("tesla", 4)
    THE_LOG: Card = Card("the_log", 2)
    THREE_MUSKETEERS: Card = Card("three_musketeers", 9, [Units.MUSKETEER])
    TOMBSTONE: Card = Card("tombstone", 3, [Units.TOMBSTONE])
    TORNADO: Card = Card("tornado", 3)
    VALKYRIE: Card = Card("valkyrie", 4, [Units.VALKYRIE])
    WALL_BREAKERS: Card = Card("wall_breakers", 2, [Units.WALL_BREAKER])
    WITCH: Card = Card("witch", 5)
    WIZARD: Card = Card("wizard", 5)
    X_BOW: Card = Card("x_bow", 6, [Units.X_BOW])
    ZAP: Card = Card("zap", 2)
    ZAPPIES: Card = Card("zappies", 4)

    def dict(self):
        return {k: v for k, v in asdict(self).items()}


Cards = _CardsNamespace()
