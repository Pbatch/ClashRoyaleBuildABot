from pydantic.dataclasses import dataclass

from clashroyalebuildabot.game.units import Unit, Units

# Cards in a Clash Royale deck
DECK_SIZE = 8


@dataclass(frozen=True)
class Card:
    name: str
    cost: int
    id_: int
    target_anywhere: bool = False
    units: tuple[Unit, ...] = ()


@dataclass(frozen=True)
class _CardsNamespace:
    ARCHER_QUEEN: Card = Card(
        "archer_queen", cost=5, id_=26000072, units=(Units.ARCHER_QUEEN,)
    )
    ARCHERS: Card = Card(
        "archers", cost=3, id_=26000001, units=(Units.ARCHER,)
    )
    ARROWS: Card = Card("arrows", cost=3, id_=28000001, target_anywhere=True)
    BABY_DRAGON: Card = Card(
        "baby_dragon", cost=4, id_=26000015, units=(Units.BABY_DRAGON,)
    )
    BALLOON: Card = Card(
        "balloon", cost=5, id_=26000006, units=(Units.BALLOON,)
    )
    BANDIT: Card = Card("bandit", cost=3, id_=26000046, units=(Units.BANDIT,))
    BARBARIAN_BARREL: Card = Card(
        "barbarian_barrel",
        cost=2,
        id_=28000015,
        target_anywhere=True,
        units=(Units.BARBARIAN,),
    )
    BARBARIAN_HUT: Card = Card(
        "barbarian_hut",
        cost=6,
        id_=27000005,
        units=(Units.BARBARIAN_HUT, Units.BARBARIAN),
    )
    BARBARIANS: Card = Card(
        "barbarians", cost=5, id_=26000008, units=(Units.BARBARIAN,)
    )
    BATS: Card = Card("bats", cost=2, id_=26000049, units=(Units.BAT,))
    BATTLE_HEALER: Card = Card(
        "battle_healer", cost=4, id_=26000068, units=(Units.BATTLE_HEALER,)
    )
    BATTLE_RAM: Card = Card(
        "battle_ram", cost=4, id_=26000036, units=(Units.BATTLE_RAM,)
    )
    BERSERKER: Card = Card(
        "berserker", cost=2, id_=26000102, units=(Units.BERSERKER,)
    )
    BLANK: Card = Card("blank", cost=11, id_=-1)
    BOMBER: Card = Card("bomber", cost=2, id_=26000013, units=(Units.BOMBER,))
    BOMB_TOWER: Card = Card(
        "bomb_tower", cost=4, id_=27000004, units=(Units.BOMB_TOWER,)
    )
    BOSS_BANDIT: Card = Card(
        "boss_bandit", cost=6, id_=26000103, units=(Units.BOSS_BANDIT,)
    )
    BOWLER: Card = Card("bowler", cost=5, id_=26000034, units=(Units.BOWLER,))
    CANNON: Card = Card("cannon", cost=3, id_=27000000, units=(Units.CANNON,))
    CANNON_CART: Card = Card(
        "cannon_cart", cost=5, id_=26000054, units=(Units.CANNON_CART,)
    )
    CLONE: Card = Card("clone", cost=3, id_=28000013, target_anywhere=True)
    DART_GOBLIN: Card = Card(
        "dart_goblin", cost=3, id_=26000040, units=(Units.DART_GOBLIN,)
    )
    DARK_PRINCE: Card = Card(
        "dark_prince", cost=4, id_=26000027, units=(Units.DARK_PRINCE,)
    )
    EARTHQUAKE: Card = Card(
        "earthquake", cost=3, id_=28000014, target_anywhere=True
    )
    ELECTRO_DRAGON: Card = Card(
        "electro_dragon", cost=5, id_=26000063, units=(Units.ELECTRO_DRAGON,)
    )
    ELECTRO_GIANT: Card = Card(
        "electro_giant", cost=7, id_=26000085, units=(Units.ELECTRO_GIANT,)
    )
    ELECTRO_SPIRIT: Card = Card(
        "electro_spirit", cost=1, id_=26000084, units=(Units.ELECTRO_SPIRIT,)
    )
    ELECTRO_WIZARD: Card = Card(
        "electro_wizard", cost=4, id_=26000042, units=(Units.ELECTRO_WIZARD,)
    )
    ELITE_BARBARIANS: Card = Card(
        "elite_barbarians",
        cost=6,
        id_=26000043,
        units=(Units.ELITE_BARBARIAN,),
    )
    ELIXIR_COLLECTOR: Card = Card(
        "elixir_collector",
        cost=6,
        id_=27000007,
        units=(Units.ELIXIR_COLLECTOR,),
    )
    ELIXIR_GOLEM: Card = Card(
        "elixir_golem",
        cost=3,
        id_=26000067,
        units=(
            Units.ELIXIR_GOLEM_LARGE,
            Units.ELIXIR_GOLEM_MEDIUM,
            Units.ELIXIR_GOLEM_SMALL,
        ),
    )
    EXECUTIONER: Card = Card(
        "executioner", cost=5, id_=26000045, units=(Units.EXECUTIONER,)
    )
    FIRE_SPIRIT: Card = Card(
        "fire_spirit", cost=1, id_=26000031, units=(Units.FIRE_SPIRIT,)
    )
    FIREBALL: Card = Card(
        "fireball", cost=4, id_=28000000, target_anywhere=True
    )
    FIRECRACKER: Card = Card(
        "firecracker", cost=3, id_=26000064, units=(Units.FIRE_CRACKER,)
    )
    FISHERMAN: Card = Card(
        "fisherman", cost=3, id_=26000061, units=(Units.FISHERMAN,)
    )
    FLYING_MACHINE: Card = Card(
        "flying_machine", cost=4, id_=26000057, units=(Units.FLYING_MACHINE,)
    )
    FREEZE: Card = Card("freeze", cost=4, id_=28000005, target_anywhere=True)
    FURNACE: Card = Card(
        "furnace", cost=4, id_=27000010, units=(Units.FURNACE,)
    )
    GIANT: Card = Card("giant", cost=5, id_=26000003, units=(Units.GIANT,))
    GIANT_SKELETON: Card = Card(
        "giant_skeleton", cost=6, id_=26000020, units=(Units.GIANT_SKELETON,)
    )
    GIANT_SNOWBALL: Card = Card(
        "giant_snowball", cost=2, id_=28000017, target_anywhere=True
    )
    GOBLIN_CURSE: Card = Card(
        "goblin_curse", cost=2, id_=28000024, target_anywhere=True
    )
    GOBLIN_DEMOLISHER: Card = Card(
        "goblin_demolisher",
        cost=4,
        id_=26000095,
        units=(Units.GOBLIN_DEMOLISHER,),
    )
    GOBLIN_MACHINE: Card = Card(
        "goblin_machine", cost=5, id_=26000096, units=(Units.GOBLIN_MACHINE,)
    )
    GOBLINS: Card = Card(
        "goblins", cost=2, id_=26000002, units=(Units.GOBLIN,)
    )
    GOBLIN_BARREL: Card = Card(
        "goblin_barrel",
        cost=3,
        id_=28000004,
        target_anywhere=True,
        units=(Units.GOBLIN,),
    )
    GOBLIN_CAGE: Card = Card(
        "goblin_cage",
        cost=4,
        id_=27000012,
        units=(Units.GOBLIN_CAGE, Units.BRAWLER),
    )
    GOBLIN_DRILL: Card = Card(
        "goblin_drill",
        cost=4,
        id_=27000013,
        target_anywhere=True,
        units=(Units.GOBLIN_DRILL, Units.GOBLIN),
    )
    GOBLIN_GANG: Card = Card(
        "goblin_gang",
        cost=3,
        id_=26000041,
        units=(Units.GOBLIN, Units.SPEAR_GOBLIN),
    )
    GOBLIN_GIANT: Card = Card(
        "goblin_giant", cost=6, id_=26000060, units=(Units.SPEAR_GOBLIN,)
    )
    GOBLIN_HUT: Card = Card(
        "goblin_hut",
        cost=4,
        id_=27000001,
        units=(Units.GOBLIN_HUT, Units.SPEAR_GOBLIN),
    )
    GOBLINSTEIN: Card = Card(
        "goblinstein",
        cost=5,
        id_=26000099,
        units=(Units.GOBLINSTEIN, Units.GOBLINSTEIN_DOCTOR),
    )
    GOLDEN_KNIGHT: Card = Card(
        "golden_knight", cost=4, id_=26000074, units=(Units.GOLDEN_KNIGHT,)
    )
    GOLEM: Card = Card(
        "golem", cost=8, id_=26000009, units=(Units.GOLEM, Units.GOLEMITE)
    )
    GRAVEYARD: Card = Card(
        "graveyard",
        cost=5,
        id_=28000010,
        target_anywhere=True,
        units=(Units.SKELETON,),
    )
    GUARDS: Card = Card("guards", cost=3, id_=26000025, units=(Units.GUARD,))
    HEAL_SPIRIT: Card = Card(
        "heal_spirit", cost=1, id_=28000016, units=(Units.HEAL_SPIRIT,)
    )
    HOG_RIDER: Card = Card(
        "hog_rider", cost=4, id_=26000021, units=(Units.HOG_RIDER,)
    )
    HUNTER: Card = Card("hunter", cost=4, id_=26000044, units=(Units.HUNTER,))
    ICE_GOLEM: Card = Card(
        "ice_golem", cost=2, id_=26000038, units=(Units.ICE_GOLEM,)
    )
    ICE_SPIRIT: Card = Card(
        "ice_spirit", cost=1, id_=26000030, units=(Units.ICE_SPIRIT,)
    )
    ICE_WIZARD: Card = Card(
        "ice_wizard", cost=3, id_=26000023, units=(Units.ICE_WIZARD,)
    )
    INFERNO_DRAGON: Card = Card(
        "inferno_dragon", cost=4, id_=26000037, units=(Units.INFERNO_DRAGON,)
    )
    INFERNO_TOWER: Card = Card(
        "inferno_tower", cost=5, id_=27000003, units=(Units.INFERNO_TOWER,)
    )
    KNIGHT: Card = Card("knight", cost=3, id_=26000000, units=(Units.KNIGHT,))
    LAVA_HOUND: Card = Card(
        "lava_hound",
        cost=7,
        id_=26000029,
        units=(Units.LAVA_HOUND, Units.LAVA_PUP),
    )
    LIGHTNING: Card = Card(
        "lightning", cost=6, id_=28000007, target_anywhere=True
    )
    LITTLE_PRINCE: Card = Card(
        "little_prince",
        cost=3,
        id_=26000093,
        units=(Units.LITTLE_PRINCE, Units.ROYAL_GUARDIAN),
    )
    LUMBERJACK: Card = Card(
        "lumberjack", cost=4, id_=26000035, units=(Units.LUMBERJACK,)
    )
    MAGIC_ARCHER: Card = Card(
        "magic_archer", cost=4, id_=26000062, units=(Units.MAGIC_ARCHER,)
    )
    MEGA_KNIGHT: Card = Card(
        "mega_knight", cost=7, id_=26000055, units=(Units.MEGA_KNIGHT,)
    )
    MEGA_MINION: Card = Card(
        "mega_minion", cost=3, id_=26000039, units=(Units.MEGA_MINION,)
    )
    MIGHTY_MINER: Card = Card(
        "mighty_miner", cost=4, id_=26000065, units=(Units.MIGHTY_MINER,)
    )
    MINER: Card = Card("miner", cost=3, id_=26000032, units=(Units.MINER,))
    MINIONS: Card = Card(
        "minions", cost=3, id_=26000005, units=(Units.MINION,)
    )
    MINION_HORDE: Card = Card(
        "minion_horde", cost=5, id_=26000022, units=(Units.MINION,)
    )
    MINIPEKKA: Card = Card(
        "minipekka", cost=4, id_=26000018, units=(Units.MINIPEKKA,)
    )
    MIRROR: Card = Card("mirror", cost=-1, id_=28000006, target_anywhere=True)
    MONK: Card = Card("monk", cost=5, id_=26000077, units=(Units.MONK,))
    MORTAR: Card = Card("mortar", cost=4, id_=27000002, units=(Units.MORTAR,))
    MOTHER_WITCH: Card = Card(
        "mother_witch",
        cost=4,
        id_=26000083,
        units=(Units.MOTHER_WITCH, Units.HOG),
    )
    MUSKETEER: Card = Card(
        "musketeer", cost=4, id_=26000014, units=(Units.MUSKETEER,)
    )
    NIGHT_WITCH: Card = Card(
        "night_witch",
        cost=4,
        id_=26000048,
        units=(Units.NIGHT_WITCH, Units.BAT),
    )
    PEKKA: Card = Card("pekka", cost=7, id_=26000004, units=(Units.PEKKA,))
    PHOENIX: Card = Card(
        "phoenix",
        cost=4,
        id_=26000087,
        units=(Units.PHOENIX_LARGE, Units.PHOENIX_EGG, Units.PHOENIX_SMALL),
    )
    POISON: Card = Card("poison", cost=4, id_=28000009, target_anywhere=True)
    PRINCE: Card = Card("prince", cost=5, id_=26000016, units=(Units.PRINCE,))
    PRINCESS: Card = Card(
        "princess", cost=3, id_=26000026, units=(Units.PRINCESS,)
    )
    RAGE: Card = Card("rage", cost=2, id_=28000002, target_anywhere=True)
    RAM_RIDER: Card = Card(
        "ram_rider", cost=5, id_=26000051, units=(Units.RAM_RIDER,)
    )
    RASCALS: Card = Card(
        "rascals",
        cost=5,
        id_=26000053,
        units=(Units.RASCAL_BOY, Units.RASCAL_GIRL),
    )
    ROCKET: Card = Card("rocket", cost=6, id_=28000003, target_anywhere=True)
    ROYAL_DELIVERY: Card = Card(
        "royal_delivery", cost=3, id_=28000018, units=(Units.ROYAL_RECRUIT,)
    )
    ROYAL_GHOST: Card = Card(
        "royal_ghost", cost=3, id_=26000050, units=(Units.ROYAL_GHOST,)
    )
    ROYAL_GIANT: Card = Card(
        "royal_giant", cost=6, id_=26000024, units=(Units.ROYAL_GIANT,)
    )
    ROYAL_HOGS: Card = Card(
        "royal_hogs", cost=5, id_=26000059, units=(Units.ROYAL_HOG,)
    )
    ROYAL_RECRUITS: Card = Card(
        "royal_recruits", cost=7, id_=26000047, units=(Units.ROYAL_RECRUIT,)
    )
    RUNE_GIANT: Card = Card(
        "rune_giant", cost=4, id_=26000101, units=(Units.RUNE_GIANT,)
    )
    SKELETONS: Card = Card(
        "skeletons", cost=1, id_=26000010, units=(Units.SKELETON,)
    )
    SKELETON_ARMY: Card = Card(
        "skeleton_army", cost=3, id_=26000012, units=(Units.SKELETON,)
    )
    SKELETON_BARREL: Card = Card(
        "skeleton_barrel", cost=3, id_=26000056, units=(Units.SKELETON,)
    )
    SKELETON_DRAGONS: Card = Card(
        "skeleton_dragons",
        cost=4,
        id_=26000080,
        units=(Units.SKELETON_DRAGON,),
    )
    SKELETON_KING: Card = Card(
        "skeleton_king",
        cost=4,
        id_=26000069,
        units=(Units.SKELETON_KING, Units.SKELETON),
    )
    SPARKY: Card = Card("sparky", cost=6, id_=26000033, units=(Units.SPARKY,))
    SPEAR_GOBLINS: Card = Card(
        "spear_goblins", cost=2, id_=26000019, units=(Units.SPEAR_GOBLIN,)
    )
    SPIRIT_EMPRESS: Card = Card(
        "spirit_empress",
        cost=6,
        id_=28000025,
        units=(Units.SPIRIT_EMPRESS, Units.SPIRIT_EMPRESS_MOUNTED),
    )
    SUSPICIOUS_BUSH: Card = Card(
        "suspicious_bush", cost=2, id_=26000097, units=(Units.SUSPICIOUS_BUSH,)
    )
    TESLA: Card = Card("tesla", cost=4, id_=27000006, units=(Units.TESLA,))
    THE_LOG: Card = Card("the_log", cost=2, id_=28000011, target_anywhere=True)
    THREE_MUSKETEERS: Card = Card(
        "three_musketeers", cost=9, id_=26000028, units=(Units.MUSKETEER,)
    )
    TOMBSTONE: Card = Card(
        "tombstone", cost=3, id_=27000009, units=(Units.TOMBSTONE,)
    )
    TORNADO: Card = Card("tornado", cost=3, id_=28000012, target_anywhere=True)
    VALKYRIE: Card = Card(
        "valkyrie", cost=4, id_=26000011, units=(Units.VALKYRIE,)
    )
    VINES: Card = Card("vines", cost=3, id_=28000026, target_anywhere=True)
    VOID: Card = Card("void", cost=5, id_=28000023, target_anywhere=True)
    WALL_BREAKERS: Card = Card(
        "wall_breakers", cost=2, id_=26000058, units=(Units.WALL_BREAKER,)
    )
    WITCH: Card = Card(
        "witch", cost=5, id_=26000007, units=(Units.WITCH, Units.SKELETON)
    )
    WIZARD: Card = Card("wizard", cost=5, id_=26000017, units=(Units.WIZARD,))
    X_BOW: Card = Card("x_bow", cost=6, id_=27000008, units=(Units.X_BOW,))
    ZAP: Card = Card("zap", cost=2, id_=28000008, target_anywhere=True)
    ZAPPIES: Card = Card("zappies", cost=4, id_=26000052, units=(Units.ZAPPY,))


Cards = _CardsNamespace()
