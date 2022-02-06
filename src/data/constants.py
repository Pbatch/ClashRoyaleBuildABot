import os

from win32api import GetSystemMetrics

"""
Screen dimensions
"""
SCREEN_WIDTH = GetSystemMetrics(0)
SCREEN_HEIGHT = GetSystemMetrics(1)

"""
App dimensions
"""
APP_WIDTH = 400
APP_HEIGHT = 684
BORDER_SIZE = 32

"""
Bounding boxes for screen ID
"""
CHEST_SIZE = 62
CHEST_X = 0
CHEST_Y = 590
OK_X = 143
OK_Y = 558
OK_WIDTH = 82
OK_HEIGHT = 30
SCREEN_CONFIG = [
    ['lobby',
     (CHEST_X,
      CHEST_Y,
      CHEST_X + CHEST_SIZE,
      CHEST_Y + CHEST_SIZE),
     (110, 425)],
    ['end_of_game',
     (OK_X, OK_Y, OK_X + OK_WIDTH, OK_Y + OK_HEIGHT),
     (OK_X + OK_WIDTH / 2, OK_Y + OK_HEIGHT / 2)]
]

"""
Bounding boxes for numbers
"""
_W = 28
_H = 7
KING_HP_X = 188
LEFT_PRINCESS_HP_X = 74
RIGHT_PRINCESS_HP_X = 266
ALLY_PRINCESS_HP_Y = 401
ENEMY_PRINCESS_HP_Y = 93
ALLY_KING_LEVEL_Y = 487
ENEMY_KING_LEVEL_Y = 19
KING_LEVEL_X = 134
KING_LEVEL_2_X = KING_LEVEL_X + _W
ELIXIR_BOUNDING_BOX = (100, 628, 350, 643)
NUMBER_CONFIG = [
    ['enemy_king_level', (KING_LEVEL_X, ENEMY_KING_LEVEL_Y, KING_LEVEL_X + _W, ENEMY_KING_LEVEL_Y + _H)],
    ['enemy_king_level_2', (KING_LEVEL_2_X, ENEMY_KING_LEVEL_Y, KING_LEVEL_2_X + _W, ENEMY_KING_LEVEL_Y + _H)],
    ['ally_king_level', (KING_LEVEL_X, ALLY_KING_LEVEL_Y, KING_LEVEL_X + _W, ALLY_KING_LEVEL_Y + _H)],
    ['ally_king_level_2', (KING_LEVEL_2_X, ALLY_KING_LEVEL_Y, KING_LEVEL_2_X + _W, ALLY_KING_LEVEL_Y + _H)],
    ['enemy_king_hp', (KING_HP_X, 15, 188 + _W, 15 + _H)],
    ['ally_king_hp', (KING_HP_X, 495, 188 + _W, 495 + _H)],
    ['right_ally_princess_hp',
     (RIGHT_PRINCESS_HP_X, ALLY_PRINCESS_HP_Y, RIGHT_PRINCESS_HP_X + _W, ALLY_PRINCESS_HP_Y + _H)],
    ['left_ally_princess_hp',
     (LEFT_PRINCESS_HP_X, ALLY_PRINCESS_HP_Y, LEFT_PRINCESS_HP_X + _W, ALLY_PRINCESS_HP_Y + _H)],
    ['right_enemy_princess_hp',
     (RIGHT_PRINCESS_HP_X, ENEMY_PRINCESS_HP_Y, RIGHT_PRINCESS_HP_X + _W, ENEMY_PRINCESS_HP_Y + _H)],
    ['left_enemy_princess_hp',
     (LEFT_PRINCESS_HP_X, ENEMY_PRINCESS_HP_Y, LEFT_PRINCESS_HP_X + _W, ENEMY_PRINCESS_HP_Y + _H)],
]

"""
Bounding boxes for cards
"""
CARD_Y = 545
CARD_INIT_X = 87
CARD_WIDTH = 55
CARD_HEIGHT = 65
CARD_DELTA_X = 69
CARD_CONFIG = [
    (19, 605, 51, 645),
    (CARD_INIT_X, CARD_Y, CARD_INIT_X + CARD_WIDTH, CARD_Y + CARD_HEIGHT),
    (CARD_INIT_X + CARD_DELTA_X, CARD_Y, CARD_INIT_X + CARD_WIDTH + CARD_DELTA_X, CARD_Y + CARD_HEIGHT),
    (CARD_INIT_X + 2 * CARD_DELTA_X, CARD_Y, CARD_INIT_X + CARD_WIDTH + 2 * CARD_DELTA_X, CARD_Y + CARD_HEIGHT),
    (CARD_INIT_X + 3 * CARD_DELTA_X, CARD_Y, CARD_INIT_X + CARD_WIDTH + 3 * CARD_DELTA_X, CARD_Y + CARD_HEIGHT),
]

"""
King and Princess HP for levels 1 to 14
"""
KING_HP = [2400, 2568, 2736, 2904, 3096, 3312, 3528, 3768, 4008, 4392, 4824, 5304, 5832, 6408]
PRINCESS_HP = [1400, 1512, 1624, 1750, 1890, 2030, 2184, 2352, 2534, 2786, 3052, 3346, 3668, 4032]

"""
Playable tiles
"""
TILE_HEIGHT = 14
TILE_WIDTH = 17
N_HEIGHT_TILES = 15
N_WIDE_TILES = 18
LEFT_PAD = 30
LOWER_PAD = 152
ALLY_TILES = [[x, 0]
              for x in range(N_WIDE_TILES // 3, 2 * N_WIDE_TILES // 3)]
ALLY_TILES += [[x, y]
               for x in range(N_WIDE_TILES)
               for y in range(1, N_HEIGHT_TILES)]
LEFT_PRINCESS_TILES = [[3, N_HEIGHT_TILES], [3, N_HEIGHT_TILES + 1]]
LEFT_PRINCESS_TILES += [[x, y]
                        for x in range(N_WIDE_TILES // 2)
                        for y in range(N_HEIGHT_TILES + 2, N_HEIGHT_TILES + 6)]
RIGHT_PRINCESS_TILES = [[14, N_HEIGHT_TILES], [14, N_HEIGHT_TILES + 1]]
RIGHT_PRINCESS_TILES += [[x, y]
                         for x in range(N_WIDE_TILES // 2, N_WIDE_TILES)
                         for y in range(N_HEIGHT_TILES + 2, N_HEIGHT_TILES + 6)]

"""
Unit classes
"""
UNITS = [
    "ally_archer",
    "ally_brawler",
    "ally_giant",
    "ally_goblin_cage",
    "ally_hungry_dragon",
    "ally_knight",
    "ally_minion",
    "ally_minipekka",
    "ally_musketeer",
    "ally_prince",
    "ally_valkyrie",
    "enemy_archer",
    "enemy_brawler",
    "enemy_giant",
    "enemy_goblin",
    "enemy_goblin_cage",
    "enemy_hungry_dragon",
    "enemy_knight",
    "enemy_minion",
    "enemy_minipekka",
    "enemy_muskateer",
    "enemy_prince",
    "enemy_skeleton",
    "enemy_spear_goblin",
    "enemy_valkyrie"
]

"""
Directories
"""
SRC_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(SRC_DIR, 'data')
SCREENSHOTS_DIR = os.path.join(SRC_DIR, 'screenshots')

"""
Number detector
"""
NUMBER_HEIGHT = 16
NUMBER_WIDTH = 64
NUMBER_MIN_CONFIDENCE = 0.5

"""
Unit detector
"""
UNIT_SIZE = 416
UNIT_Y_START = 0.05
UNIT_Y_END = 0.80
