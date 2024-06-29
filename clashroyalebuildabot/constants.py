import os

from clashroyalebuildabot.namespaces import Units

# Directories
SRC_DIR = os.path.dirname(__file__)
DEBUG_DIR = os.path.join(SRC_DIR, "debug")
MODELS_DIR = os.path.join(SRC_DIR, "models")
IMAGES_DIR = os.path.join(SRC_DIR, "images")
EMULATOR_DIR = os.path.join(SRC_DIR, "emulator")
SCREENSHOTS_DIR = os.path.join(DEBUG_DIR, "screenshots")
LABELS_DIR = os.path.join(DEBUG_DIR, "labels")

# Display dimensions
DISPLAY_WIDTH = 720
DISPLAY_HEIGHT = 1280

# Screenshot dimensions
SCREENSHOT_WIDTH = 368
SCREENSHOT_HEIGHT = 652

# Playable tiles
TILE_HEIGHT = 27.6
TILE_WIDTH = 34
N_HEIGHT_TILES = 15
N_WIDE_TILES = 18
TILE_INIT_X = 52
TILE_INIT_Y = 296
ALLY_TILES = [[x, 0] for x in range(N_WIDE_TILES // 3, 2 * N_WIDE_TILES // 3)]
ALLY_TILES += [
    [x, y] for x in range(N_WIDE_TILES) for y in range(1, N_HEIGHT_TILES)
]
LEFT_PRINCESS_TILES = [[3, N_HEIGHT_TILES], [3, N_HEIGHT_TILES + 1]]
LEFT_PRINCESS_TILES += [
    [x, y]
    for x in range(N_WIDE_TILES // 2)
    for y in range(N_HEIGHT_TILES + 2, N_HEIGHT_TILES + 6)
]
RIGHT_PRINCESS_TILES = [[14, N_HEIGHT_TILES], [14, N_HEIGHT_TILES + 1]]
RIGHT_PRINCESS_TILES += [
    [x, y]
    for x in range(N_WIDE_TILES // 2, N_WIDE_TILES)
    for y in range(N_HEIGHT_TILES + 2, N_HEIGHT_TILES + 6)
]
DISPLAY_CARD_Y = 1067
DISPLAY_CARD_INIT_X = 164
DISPLAY_CARD_WIDTH = 117
DISPLAY_CARD_HEIGHT = 147
DISPLAY_CARD_DELTA_X = 136

# Cards
CARD_Y = 543
CARD_INIT_X = 84
CARD_WIDTH = 61
CARD_HEIGHT = 73
CARD_DELTA_X = 69
CARD_CONFIG = [
    (21, 609, 47, 642),
    (CARD_INIT_X, CARD_Y, CARD_INIT_X + CARD_WIDTH, CARD_Y + CARD_HEIGHT),
    (
        CARD_INIT_X + CARD_DELTA_X,
        CARD_Y,
        CARD_INIT_X + CARD_WIDTH + CARD_DELTA_X,
        CARD_Y + CARD_HEIGHT,
    ),
    (
        CARD_INIT_X + 2 * CARD_DELTA_X,
        CARD_Y,
        CARD_INIT_X + CARD_WIDTH + 2 * CARD_DELTA_X,
        CARD_Y + CARD_HEIGHT,
    ),
    (
        CARD_INIT_X + 3 * CARD_DELTA_X,
        CARD_Y,
        CARD_INIT_X + CARD_WIDTH + 3 * CARD_DELTA_X,
        CARD_Y + CARD_HEIGHT,
    ),
]

# Numbers
NUMBER_WIDTH = 32
NUMBER_HEIGHT = 8
KING_HP_X = 188
LEFT_PRINCESS_HP_X = 74
RIGHT_PRINCESS_HP_X = 266
ALLY_PRINCESS_HP_Y = 403
ENEMY_PRINCESS_HP_Y = 95
ALLY_KING_LEVEL_Y = 487
ENEMY_KING_LEVEL_Y = 19
KING_LEVEL_X = 134
KING_LEVEL_2_X = KING_LEVEL_X + NUMBER_WIDTH
ELIXIR_BOUNDING_BOX = (100, 628, 350, 643)
NUMBER_CONFIG = [
    [
        "enemy_king_level",
        KING_LEVEL_X,
        ENEMY_KING_LEVEL_Y,
    ],
    [
        "enemy_king_level_2",
        KING_LEVEL_2_X,
        ENEMY_KING_LEVEL_Y,
    ],
    [
        "ally_king_level",
        KING_LEVEL_X,
        ALLY_KING_LEVEL_Y,
    ],
    [
        "ally_king_level_2",
        KING_LEVEL_2_X,
        ALLY_KING_LEVEL_Y,
    ],
    ["enemy_king_hp", KING_HP_X, 15],
    ["ally_king_hp", KING_HP_X, 495],
    [
        "right_ally_princess_hp",
        RIGHT_PRINCESS_HP_X,
        ALLY_PRINCESS_HP_Y,
    ],
    [
        "left_ally_princess_hp",
        LEFT_PRINCESS_HP_X,
        ALLY_PRINCESS_HP_Y,
    ],
    [
        "right_enemy_princess_hp",
        RIGHT_PRINCESS_HP_X,
        ENEMY_PRINCESS_HP_Y,
    ],
    [
        "left_enemy_princess_hp",
        LEFT_PRINCESS_HP_X,
        ENEMY_PRINCESS_HP_Y,
    ],
]

# HP
KING_HP = [
    2400,
    2568,
    2736,
    2904,
    3096,
    3312,
    3528,
    3768,
    4008,
    4392,
    4824,
    5304,
    5832,
    6408,
]
PRINCESS_HP = [
    1400,
    1512,
    1624,
    1750,
    1890,
    2030,
    2184,
    2352,
    2534,
    2786,
    3052,
    3346,
    3668,
    4032,
]

# Units
DETECTOR_UNITS = [
    Units.ARCHER,
    Units.BARBARIAN,
    Units.BARBARIAN_HUT,
    Units.BOMB_TOWER,
    Units.BOMBER,
    Units.BRAWLER,
    Units.CANNON,
    Units.DARK_PRINCE,
    Units.ELIXIR_COLLECTOR,
    Units.FURNACE,
    Units.GIANT,
    Units.GOBLIN,
    Units.GOBLIN_CAGE,
    Units.GOBLIN_HUT,
    Units.HUNGRY_DRAGON,
    Units.HUNTER,
    Units.ICE_GOLEM,
    Units.ICE_SPIRIT,
    Units.INFERNO_TOWER,
    Units.KNIGHT,
    Units.MINION,
    Units.MINIPEKKA,
    Units.MORTAR,
    Units.MUSKETEER,
    Units.PRINCE,
    Units.ROYAL_HOG,
    Units.SKELETON,
    Units.SPEAR_GOBLIN,
    Units.TESLA,
    Units.TOMBSTONE,
    Units.VALKYRIE,
    Units.WALL_BREAKER,
    Units.X_BOW,
]
