import os

"""
Miscellaneous
"""
# Directories
SRC_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(SRC_DIR, 'data')
SCREENSHOTS_DIR = os.path.join(SRC_DIR, 'screenshots')

"""
Click config
"""
# Display dimensions
DISPLAY_WIDTH = 720
DISPLAY_HEIGHT = 1280

# Screenshot dimensions
SCREENSHOT_WIDTH = 368
SCREENSHOT_HEIGHT = 652

# Screen ID
CHEST_SIZE = 62
CHEST_X = 0
CHEST_Y = 590
OK_X = 143
OK_Y = 558
OK_WIDTH = 82
OK_HEIGHT = 30
SCREEN_CONFIG = {
    'lobby': {'bbox': (CHEST_X,
                       CHEST_Y,
                       CHEST_X + CHEST_SIZE,
                       CHEST_Y + CHEST_SIZE),
              'click_coordinates': (220, 830)},
    'end_of_game': {'bbox': (OK_X,
                             OK_Y,
                             OK_X + OK_WIDTH,
                             OK_Y + OK_HEIGHT),
                    'click_coordinates': (360, 1125)}
}

# Playable tiles
TILE_HEIGHT = 27.6
TILE_WIDTH = 34
N_HEIGHT_TILES = 15
N_WIDE_TILES = 18
TILE_INIT_X = 52
TILE_INIT_Y = 296
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
DISPLAY_CARD_Y = 1067
DISPLAY_CARD_INIT_X = 164
DISPLAY_CARD_WIDTH = 117
DISPLAY_CARD_HEIGHT = 147
DISPLAY_CARD_DELTA_X = 136

"""
Detector config
"""
# Cards
HAND_SIZE = 5
DECK_SIZE = 8
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

# Numbers
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
NUMBER_HEIGHT = 16
NUMBER_WIDTH = 64
NUMBER_MIN_CONFIDENCE = 0.5

# HP
KING_HP = [2400, 2568, 2736, 2904, 3096, 3312, 3528, 3768, 4008, 4392, 4824, 5304, 5832, 6408]
PRINCESS_HP = [1400, 1512, 1624, 1750, 1890, 2030, 2184, 2352, 2534, 2786, 3052, 3346, 3668, 4032]

# Units
UNIT_SIZE = 416
UNIT_Y_START = 0.05
UNIT_Y_END = 0.80
UNITS = ['archer',
         'brawler',
         'giant',
         'goblin',
         'goblin_cage',
         'hungry_dragon',
         'knight',
         'minion',
         'minipekka',
         'musketeer',
         'prince',
         'skeleton',
         'spear_goblin',
         'valkyrie']

# Multihash coefficients
MULTI_HASH_SCALE = 0.355
MULTI_HASH_INTERCEPT = 163

# Cards to units
CARD_TO_UNITS = {'goblin_cage': ['brawler'],
                 'minions': ['minion'],
                 'skeletons': ['skeleton'],
                 'archers': ['archer'],
                 'spear_goblins': ['spear_goblin'],
                 'goblins': ['goblin']}

# Side
SIDE_SIZE = 16
