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
CARD_SIZE = 15
CARD_Y = 603
CARD_INIT_X = 106
CARD_DELTA_X = 69

"""
Crown position and size
"""
CROWN_SIZE = 20
CROWN_X = 339

"""
Bounding boxes for OCR
"""
OCR_CONFIG = [
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
    ['card_0', (CARD_INIT_X, CARD_Y, CARD_INIT_X + CARD_SIZE, CARD_Y + CARD_SIZE), 200],
    ['card_1', (CARD_INIT_X + CARD_DELTA_X, CARD_Y, CARD_INIT_X + CARD_DELTA_X + CARD_SIZE, CARD_Y + CARD_SIZE),
     200],
    ['card_2',
     (CARD_INIT_X + 2 * CARD_DELTA_X, CARD_Y, CARD_INIT_X + 2 * CARD_DELTA_X + CARD_SIZE, CARD_Y + CARD_SIZE), 200],
    ['card_3',
     (CARD_INIT_X + 3 * CARD_DELTA_X, CARD_Y, CARD_INIT_X + 3 * CARD_DELTA_X + CARD_SIZE, CARD_Y + CARD_SIZE), 200],
    ['elixir', (96, 621, 123, 638), 190],
    ['timer', (311, 16, 362, 34), 180],
    ['ally_crowns', (CROWN_X, 332, CROWN_X + CROWN_SIZE, 332 + CROWN_SIZE), 100],
    ['enemy_crowns', (CROWN_X, 200, CROWN_X + CROWN_SIZE, 200 + CROWN_SIZE), 100],
    ['ally_hp', (KING_HP_X, 493, KING_HP_X + KING_HP_WIDTH, 493 + KING_HP_HEIGHT), 180],
    ['enemy_hp', (KING_HP_X, 14, KING_HP_X + KING_HP_WIDTH, 14 + KING_HP_HEIGHT), 195],
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
# ALLY_TILES = [[LEFT_PAD + (i + 0.5) * TILE_WIDTH,
#                APP_HEIGHT - LOWER_PAD + (2 * N_HEIGHT_TILES + 1.5) * TILE_HEIGHT]
#               for i in range(N_WIDE_TILES // 3, 2 * N_WIDE_TILES // 3)]
# ALLY_TILES += [[LEFT_PAD + (i + 0.5) * TILE_WIDTH,
#                 APP_HEIGHT - LOWER_PAD + (N_HEIGHT_TILES + 1.5 + j) * TILE_HEIGHT]
#                for i in range(N_WIDE_TILES)
#                for j in range(1, N_HEIGHT_TILES)]
# LEFT_PRINCESS_TILES = [[LEFT_PAD + (3.5 * TILE_WIDTH), TOP_PAD + j * TILE_HEIGHT]
#                        for j in [15.5, 16.5]]
# LEFT_PRINCESS_TILES += [[LEFT_PAD + (i + 0.5) * TILE_WIDTH,
#                          TOP_PAD + (j + 0.5) * TILE_HEIGHT]
#                         for i in range(N_WIDE_TILES // 2)
#                         for j in range(N_HEIGHT_TILES - 4, N_HEIGHT_TILES)]
# RIGHT_PRINCESS_TILES = [[LEFT_PAD + 14.5 * TILE_WIDTH, TOP_PAD + j * TILE_HEIGHT]
#                         for j in [15.5, 16.5]]
# RIGHT_PRINCESS_TILES += [[LEFT_PAD + (i + 0.5) * TILE_WIDTH,
#                           TOP_PAD + (j + 0.5) * TILE_HEIGHT]
#                          for i in range(N_WIDE_TILES // 2, N_WIDE_TILES)
#                          for j in range(N_HEIGHT_TILES - 4, N_HEIGHT_TILES)]
