"""Positions on the device's screen, 720x1280 pixels, where the bot taps.

Boxes are (left, top, right, bottom).
"""

from clashroyalebuildabot.constants.screenshot import (
    CARD_BOXES,
    SCREENSHOT_HEIGHT,
    SCREENSHOT_WIDTH,
)
from clashroyalebuildabot.utils.image import Box

DISPLAY_WIDTH = 720
DISPLAY_HEIGHT = 1280

# The arena's grid of tiles. Tile (0, 0) is the bottom-left tile, and its
# bottom-left corner is TILE_INIT_X across and TILE_INIT_Y up from the
# bottom of the screen.
#
# Measured from the grass checkerboard, one square per tile, in battle
# screenshots (Nov 2026): 16.64 x 13.36 px tiles from x 33.5 to 333.1 and
# y 79.4 to 506.9 of the 368x652 screenshot, scaled up here. The game's own
# placement outline and the river sit on those tile edges.
TILE_HEIGHT = 26.23
TILE_WIDTH = 32.56
N_HEIGHT_TILES = 15
N_WIDE_TILES = 18
TILE_INIT_X = 65.5
TILE_INIT_Y = 284.9
# Where the bot can always play a card: our half of the arena.
ALLY_TILES = [[x, 0] for x in range(N_WIDE_TILES // 3, 2 * N_WIDE_TILES // 3)]
ALLY_TILES += [
    [x, y] for x in range(N_WIDE_TILES) for y in range(1, N_HEIGHT_TILES)
]
ALL_TILES = ALLY_TILES + [[x, 31 - y] for x, y in ALLY_TILES]


def tile_box(tile_x: int, tile_y: int) -> tuple[int, int, int, int]:
    """A tile in screenshot pixels, (left, top, right, bottom). Tiles count
    from the bottom left, as everywhere else in the bot."""
    sx = SCREENSHOT_WIDTH / DISPLAY_WIDTH
    sy = SCREENSHOT_HEIGHT / DISPLAY_HEIGHT
    left = (TILE_INIT_X + tile_x * TILE_WIDTH) * sx
    bottom = (DISPLAY_HEIGHT - TILE_INIT_Y - tile_y * TILE_HEIGHT) * sy
    return (
        round(left),
        round(bottom - TILE_HEIGHT * sy),
        round(left + TILE_WIDTH * sx),
        round(bottom),
    )


# Extra tiles we can play on once that enemy princess tower is destroyed.
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

# The tiles under each tower's base, as (x_min, y_min, x_max, y_max), both
# ends included, named as in Towers. Kings cover 4x4 tiles, princesses 3x3.
# From the towers' centres in the game's logic files (king (9, 3), princess
# (3.5, 6.5) and (14.5, 6.5) on our side, in tiles, mirrored for the
# enemy's), and checked against battle screenshots. The towers are drawn
# leaning up the screen, so their sprites reach above these tiles.
TOWER_TILES = {
    "left_enemy_princess": (2, 24, 4, 26),
    "right_enemy_princess": (13, 24, 15, 26),
    "left_ally_princess": (2, 5, 4, 7),
    "right_ally_princess": (13, 5, 15, 7),
    "enemy_king": (7, 27, 10, 30),
    "ally_king": (7, 1, 10, 4),
}


def _scale_to_display(box: Box) -> Box:

    sx = DISPLAY_WIDTH / SCREENSHOT_WIDTH
    sy = DISPLAY_HEIGHT / SCREENSHOT_HEIGHT
    left, top, right, bottom = box
    return (left * sx, top * sy, right * sx, bottom * sy)


# The four hand cards from left to right: the screenshot's boxes, scaled up.
HAND_CARD_BOXES = [_scale_to_display(box) for box in CARD_BOXES[1:]]
