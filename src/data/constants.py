"""
App dimensions
"""
APP_WIDTH = 400
APP_HEIGHT = 684
BORDER_SIZE = 32

"""
Princess position and size
"""
PRINCESS_WIDTH = 28
PRINCESS_HEIGHT = 10
LEFT_PRINCESS_X = 75
RIGHT_PRINCESS_X = 267
ENEMY_PRINCESS_Y = 92
ALLY_PRINCESS_Y = 399

"""
King level position and size
"""
KING_LEVEL_X = 148
KING_LEVEL_WIDTH = 14
KING_LEVEL_HEIGHT = 10

"""
King position and size
"""
KING_HP_X = 188
KING_HP_WIDTH = PRINCESS_WIDTH
KING_HP_HEIGHT = PRINCESS_HEIGHT

"""
Card position and size
"""
CARD_ELIXIR_SIZE = 15
CARD_ELIXIR_Y = 603
CARD_ELIXIR_INIT_X = 106
CARD_Y = 545
CARD_INIT_X = 87
CARD_WIDTH = 55
CARD_HEIGHT = 65
CARD_DELTA_X = 69

"""
Crown position and size
"""
CROWN_SIZE = 20
CROWN_X = 339

"""
Bounding boxes for numbers
"""
NUMBER_CONFIG = [
    ['left_enemy_princess',
     (LEFT_PRINCESS_X, ENEMY_PRINCESS_Y, LEFT_PRINCESS_X + PRINCESS_WIDTH, ENEMY_PRINCESS_Y + PRINCESS_HEIGHT), 170],
    ['right_enemy_princess',
     (RIGHT_PRINCESS_X, ENEMY_PRINCESS_Y, RIGHT_PRINCESS_X + PRINCESS_WIDTH, ENEMY_PRINCESS_Y + PRINCESS_HEIGHT), 170],
    ['left_ally_princess',
     (LEFT_PRINCESS_X, ALLY_PRINCESS_Y, LEFT_PRINCESS_X + PRINCESS_WIDTH, ALLY_PRINCESS_Y + PRINCESS_HEIGHT), 170],
    ['right_ally_princess',
     (RIGHT_PRINCESS_X, ALLY_PRINCESS_Y, RIGHT_PRINCESS_X + PRINCESS_WIDTH, ALLY_PRINCESS_Y + PRINCESS_HEIGHT), 170],
    ['enemy_level', (KING_LEVEL_X, 18, KING_LEVEL_X + KING_LEVEL_WIDTH, 18 + KING_LEVEL_HEIGHT), 180],
    ['ally_level', (KING_LEVEL_X, 486, KING_LEVEL_X + KING_LEVEL_WIDTH, 486 + KING_LEVEL_HEIGHT), 180],
    ['elixir', (96, 621, 123, 638), 190],
    ['timer', (311, 16, 362, 34), 180],
    ['ally_crowns', (CROWN_X, 332, CROWN_X + CROWN_SIZE, 332 + CROWN_SIZE), 100],
    ['enemy_crowns', (CROWN_X, 200, CROWN_X + CROWN_SIZE, 200 + CROWN_SIZE), 100],
    ['ally_hp', (KING_HP_X, 493, KING_HP_X + KING_HP_WIDTH, 493 + KING_HP_HEIGHT), 180],
    ['enemy_hp', (KING_HP_X, 14, KING_HP_X + KING_HP_WIDTH, 14 + KING_HP_HEIGHT), 195],
]

"""
Bounding boxes for cards
"""
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
