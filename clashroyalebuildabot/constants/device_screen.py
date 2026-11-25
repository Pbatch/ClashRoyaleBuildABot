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


def _scale_to_display(box: Box) -> Box:

    sx = DISPLAY_WIDTH / SCREENSHOT_WIDTH
    sy = DISPLAY_HEIGHT / SCREENSHOT_HEIGHT
    left, top, right, bottom = box
    return (left * sx, top * sy, right * sx, bottom * sy)


# The four hand cards from left to right: the screenshot's boxes, scaled up.
HAND_CARD_BOXES = [_scale_to_display(box) for box in CARD_BOXES[1:]]
