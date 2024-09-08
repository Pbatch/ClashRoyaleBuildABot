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
    ARCHER_QUEEN: Card = Card("archer_queen", False, 5, [Units.ARCHER_QUEEN])
    ARCHERS: Card = Card("archers", False, 3, [Units.ARCHER])
    ARROWS: Card = Card("arrows", True, 3)
    BABY_DRAGON: Card = Card("baby_dragon", False, 4, [Units.BABY_DRAGON])
    BALLOON: Card = Card("balloon", False, 5, [Units.BALLOON])
    BANDIT: Card = Card("bandit", False, 3, [Units.BANDIT])
    BARBARIAN_BARREL: Card = Card(
        "barbarian_barrel", True, 2, [Units.BARBARIAN]
    )
    BARBARIAN_HUT: Card = Card(
        "barbarian_hut", False, 7, [Units.BARBARIAN_HUT, Units.BARBARIAN]
    )
    BARBARIANS: Card = Card("barbarians", False, 5, [Units.BARBARIAN])
    BATS: Card = Card("bats", False, 2, [Units.BAT])
    BATTLE_HEALER: Card = Card(
        "battle_healer", False, 4, [Units.BATTLE_HEALER]
    )
    BATTLE_RAM: Card = Card("battle_ram", False, 4, [Units.BATTLE_RAM])
    BLANK: Card = Card("blank", False, 11)
    BOMBER: Card = Card("bomber", False, 2, [Units.BOMBER])
    BOMB_TOWER: Card = Card("bomb_tower", False, 4, [Units.BOMB_TOWER])
    BOWLER: Card = Card("bowler", False, 5, [Units.BOWLER])
    CANNON: Card = Card("cannon", False, 3, [Units.CANNON])
    CANNON_CART: Card = Card("cannon_cart", False, 5, [Units.CANNON_CART])
    CLONE: Card = Card("clone", True, 3)
    DART_GOBLIN: Card = Card("dart_goblin", False, 3, [Units.DART_GOBLIN])
    DARK_PRINCE: Card = Card("dark_prince", False, 4, [Units.DARK_PRINCE])
    EARTHQUAKE: Card = Card("earthquake", True, 3)
    ELECTRO_DRAGON: Card = Card(
        "electro_dragon", False, 5, [Units.ELECTRO_DRAGON]
    )
    ELECTRO_GIANT: Card = Card(
        "electro_giant", False, 7, [Units.ELECTRO_GIANT]
    )
    ELECTRO_SPIRIT: Card = Card(
        "electro_spirit", False, 1, [Units.ELECTRO_SPIRIT]
    )
    ELECTRO_WIZARD: Card = Card(
        "electro_wizard", False, 4, [Units.ELECTRO_WIZARD]
    )
    ELITE_BARBARIANS: Card = Card(
        "elite_barbarians", False, 6, [Units.ELITE_BARBARIAN]
    )
    ELIXIR_COLLECTOR: Card = Card(
        "elixir_collector", False, 6, [Units.ELIXIR_COLLECTOR]
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
    )
    EXECUTIONER: Card = Card("executioner", False, 5, [Units.EXECUTIONER])
    FIRE_SPIRIT: Card = Card("fire_spirit", False, 1, [Units.FIRE_SPIRIT])
    FIREBALL: Card = Card("fireball", True, 4)
    FIRECRACKER: Card = Card("firecracker", False, 3, [Units.FIRE_CRACKER])
    FISHERMAN: Card = Card("fisherman", False, 3, [Units.FISHERMAN])
    FLYING_MACHINE: Card = Card(
        "flying_machine", False, 4, [Units.FLYING_MACHINE]
    )
    FREEZE: Card = Card("freeze", True, 4)
    FURNACE: Card = Card("furnace", False, 4, [Units.FURNACE])
    GIANT: Card = Card("giant", False, 5, [Units.GIANT])
    GIANT_SKELETON: Card = Card(
        "giant_skeleton", False, 6, [Units.GIANT_SKELETON]
    )
    GIANT_SNOWBALL: Card = Card("giant_snowball", True, 2)
    GOBLINS: Card = Card("goblins", False, 2, [Units.GOBLIN])
    GOBLIN_BARREL: Card = Card("goblin_barrel", True, 3, [Units.GOBLIN])
    GOBLIN_CAGE: Card = Card(
        "goblin_cage", False, 4, [Units.GOBLIN_CAGE, Units.BRAWLER]
    )
    GOBLIN_DRILL: Card = Card(
        "goblin_drill", True, 4, [Units.GOBLIN_DRILL, Units.GOBLIN]
    )
    GOBLIN_GANG: Card = Card(
        "goblin_gang", False, 3, [Units.GOBLIN, Units.SPEAR_GOBLIN]
    )
    GOBLIN_GIANT: Card = Card("goblin_giant", False, 6, [Units.SPEAR_GOBLIN])
    GOBLIN_HUT: Card = Card(
        "goblin_hut", False, 5, [Units.GOBLIN_HUT, Units.SPEAR_GOBLIN]
    )
    GOLDEN_KNIGHT: Card = Card(
        "golden_knight", False, 4, [Units.GOLDEN_KNIGHT]
    )
    GOLEM: Card = Card("golem", False, 8, [Units.GOLEM, Units.GOLEMITE])
    GRAVEYARD: Card = Card("graveyard", True, 5, [Units.SKELETON])
    GUARDS: Card = Card("guards", False, 3, [Units.GUARD])
    HEAL_SPIRIT: Card = Card("heal_spirit", False, 1, [Units.HEAL_SPIRIT])
    HOG_RIDER: Card = Card("hog_rider", False, 4, [Units.HOG_RIDER])
    HUNTER: Card = Card("hunter", False, 4, [Units.HUNTER])
    ICE_GOLEM: Card = Card("ice_golem", False, 2, [Units.ICE_GOLEM])
    ICE_SPIRIT: Card = Card("ice_spirit", False, 1, [Units.ICE_SPIRIT])
    ICE_WIZARD: Card = Card("ice_wizard", False, 3, [Units.ICE_WIZARD])
    INFERNO_DRAGON: Card = Card(
        "inferno_dragon", False, 4, [Units.INFERNO_DRAGON]
    )
    INFERNO_TOWER: Card = Card(
        "inferno_tower", False, 5, [Units.INFERNO_TOWER]
    )
    KNIGHT: Card = Card("knight", False, 3, [Units.KNIGHT])
    LAVA_HOUND: Card = Card(
        "lava_hound", False, 7, [Units.LAVA_HOUND, Units.LAVA_PUP]
    )
    LIGHTNING: Card = Card("lightning", True, 6)
    LITTLE_PRINCE: Card = Card(
        "little_prince", False, 3, [Units.LITTLE_PRINCE, Units.ROYAL_GUARDIAN]
    )
    LUMBERJACK: Card = Card("lumberjack", False, 4, [Units.LUMBERJACK])
    MAGIC_ARCHER: Card = Card("magic_archer", False, 4, [Units.MAGIC_ARCHER])
    MEGA_KNIGHT: Card = Card("mega_knight", False, 7, [Units.MEGA_KNIGHT])
    MEGA_MINION: Card = Card("mega_minion", False, 3, [Units.MEGA_MINION])
    MIGHTY_MINER: Card = Card("mighty_miner", False, 4, [Units.MIGHTY_MINER])
    MINER: Card = Card("miner", False, 3, [Units.MINER])
    MINIONS: Card = Card("minions", False, 3, [Units.MINION])
    MINION_HORDE: Card = Card("minion_horde", False, 5, [Units.MINION])
    MINIPEKKA: Card = Card("minipekka", False, 4, [Units.MINIPEKKA])
    MIRROR: Card = Card("mirror", True, -1)
    MONK: Card = Card("monk", False, 5, [Units.MONK])
    MORTAR: Card = Card("mortar", False, 4, [Units.MORTAR])
    MOTHER_WITCH: Card = Card(
        "mother_witch", False, 4, [Units.MOTHER_WITCH, Units.HOG]
    )
    MUSKETEER: Card = Card("musketeer", False, 4, [Units.MUSKETEER])
    NIGHT_WITCH: Card = Card(
        "night_witch", False, 4, [Units.NIGHT_WITCH, Units.BAT]
    )
    PEKKA: Card = Card("pekka", False, 7, [Units.PEKKA])
    PHOENIX: Card = Card(
        "phoenix",
        False,
        4,
        [Units.PHOENIX_LARGE, Units.PHOENIX_EGG, Units.PHOENIX_SMALL],
    )
    POISON: Card = Card("poison", True, 4)
    PRINCE: Card = Card("prince", False, 5, [Units.PRINCE])
    PRINCESS: Card = Card("princess", False, 3, [Units.PRINCESS])
    RAGE: Card = Card("rage", True, 2)
    RAM_RIDER: Card = Card("ram_rider", False, 5, [Units.RAM_RIDER])
    RASCALS: Card = Card(
        "rascals", False, 5, [Units.RASCAL_BOY, Units.RASCAL_GIRL]
    )
    ROCKET: Card = Card("rocket", True, 6)
    ROYAL_DELIVERY: Card = Card(
        "royal_delivery", False, 3, [Units.ROYAL_RECRUIT]
    )
    ROYAL_GHOST: Card = Card("royal_ghost", False, 3, [Units.ROYAL_GHOST])
    ROYAL_GIANT: Card = Card("royal_giant", False, 6, [Units.ROYAL_GIANT])
    ROYAL_HOGS: Card = Card("royal_hogs", False, 5, [Units.ROYAL_HOG])
    ROYAL_RECRUITS: Card = Card(
        "royal_recruits", False, 7, [Units.ROYAL_RECRUIT]
    )
    SKELETONS: Card = Card("skeletons", False, 1, [Units.SKELETON])
    SKELETON_ARMY: Card = Card("skeleton_army", False, 3, [Units.SKELETON])
    SKELETON_BARREL: Card = Card("skeleton_barrel", False, 3, [Units.SKELETON])
    SKELETON_DRAGONS: Card = Card(
        "skeleton_dragons", False, 4, [Units.SKELETON_DRAGON]
    )
    SKELETON_KING: Card = Card(
        "skeleton_king", False, 4, [Units.SKELETON_KING, Units.SKELETON]
    )
    SPARKY: Card = Card("sparky", False, 6, [Units.SPARKY])
    SPEAR_GOBLINS: Card = Card("spear_goblins", False, 2, [Units.SPEAR_GOBLIN])
    TESLA: Card = Card("tesla", False, 4, [Units.TESLA])
    THE_LOG: Card = Card("the_log", True, 2)
    THREE_MUSKETEERS: Card = Card(
        "three_musketeers", False, 9, [Units.MUSKETEER]
    )
    TOMBSTONE: Card = Card("tombstone", False, 3, [Units.TOMBSTONE])
    TORNADO: Card = Card("tornado", True, 3)
    VALKYRIE: Card = Card("valkyrie", False, 4, [Units.VALKYRIE])
    WALL_BREAKERS: Card = Card("wall_breakers", False, 2, [Units.WALL_BREAKER])
    WITCH: Card = Card("witch", False, 5, [Units.WITCH, Units.SKELETON])
    WIZARD: Card = Card("wizard", False, 5, [Units.WIZARD])
    X_BOW: Card = Card("x_bow", False, 6, [Units.X_BOW])
    ZAP: Card = Card("zap", True, 2)
    ZAPPIES: Card = Card("zappies", False, 4, [Units.ZAPPY])


Cards = _CardsNamespace()
NAME2CARD = dict(asdict(Cards).items())
