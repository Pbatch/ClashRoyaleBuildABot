"""
App dimensions
"""
APP_WIDTH = 400
APP_HEIGHT = 684
BORDER_SIZE = 32

"""
Bounding boxes for numbers
"""
KING_LEVEL_X = 148
KING_LEVEL_WIDTH = 14
KING_LEVEL_HEIGHT = 10
NUMBER_CONFIG = {
    'elixir': [(96, 621, 123, 638), 190],
    'timer': [(311, 16, 362, 34), 180],
    'enemy_king_level': [(KING_LEVEL_X, 18, KING_LEVEL_X + KING_LEVEL_WIDTH, 18 + KING_LEVEL_HEIGHT),
                         (177, 18, 177 + 13, 18 + KING_LEVEL_HEIGHT),
                         180],
    'ally_king_level': [(KING_LEVEL_X, 486, KING_LEVEL_X + KING_LEVEL_WIDTH, 486 + KING_LEVEL_HEIGHT),
                        (177, 486, 177 + 13, 486 + KING_LEVEL_HEIGHT),
                        180],
}

"""
Bounding boxes for HP
"""
HP_WIDTH = 28
HP_HEIGHT = 7
KING_HP_X = 188
LEFT_PRINCESS_HP_X = 74
RIGHT_PRINCESS_HP_X = 266
ALLY_PRINCESS_HP_Y = 405
ENEMY_PRINCESS_HP_Y = 97
HP_CONFIG = [
    ['enemy_king', (KING_HP_X, 15, 188 + HP_WIDTH, 15 + HP_HEIGHT)],
    ['ally_king', (KING_HP_X, 495, 188 + HP_WIDTH, 495 + HP_HEIGHT)],
    ['right_ally_princess', (RIGHT_PRINCESS_HP_X, ALLY_PRINCESS_HP_Y, RIGHT_PRINCESS_HP_X + HP_WIDTH, ALLY_PRINCESS_HP_Y + HP_HEIGHT)],
    ['left_ally_princess', (LEFT_PRINCESS_HP_X, ALLY_PRINCESS_HP_Y, LEFT_PRINCESS_HP_X + HP_WIDTH, ALLY_PRINCESS_HP_Y + HP_HEIGHT)],
    ['right_enemy_princess', (RIGHT_PRINCESS_HP_X, ENEMY_PRINCESS_HP_Y, RIGHT_PRINCESS_HP_X + HP_WIDTH, ENEMY_PRINCESS_HP_Y + HP_HEIGHT)],
    ['left_enemy_princess', (LEFT_PRINCESS_HP_X, ENEMY_PRINCESS_HP_Y, LEFT_PRINCESS_HP_X + HP_WIDTH, ENEMY_PRINCESS_HP_Y + HP_HEIGHT)],
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
King and Princess HP for levels 1 to 13
"""
KING_HP = [2400, 2568, 2736, 2904, 3096, 3312, 3528, 3768, 4008, 4392, 4824, 5304, 5832]
PRINCESS_HP = [1400, 1512, 1624, 1750, 1890, 2030, 2184, 2352, 2534, 2786, 3052, 3346, 3668]

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
    'ally_archer',
    'ally_giant',
    'ally_knight',
    'ally_minion',
    'ally_minipekka',
    'ally_musketeer',
    'enemy_archer',
    'enemy_brawler',
    'enemy_giant',
    'enemy_goblin',
    'enemy_goblin_cage',
    'enemy_knight',
    'enemy_minion',
    'enemy_minipekka',
    'enemy_muskateer',
    'enemy_prince',
    'enemy_skeleton',
    'enemy_spear_goblin'
]
