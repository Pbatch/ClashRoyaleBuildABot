"""Positions in the screenshot the detectors read, 368x652 pixels.

Boxes are (left, top, right, bottom).
"""

SCREENSHOT_WIDTH = 368
SCREENSHOT_HEIGHT = 652

# Cards. Each box is the card's face (its art and thin dark border), the same
# framing as the card art card_hashes.py is made from, without the frame
# around it. Measured by matching that art to battle frames.
NEXT_CARD_BOX = (27, 610, 55, 645)
_CARD_Y = 546
_CARD_INIT_X = 87
_CARD_WIDTH = 61
_CARD_HEIGHT = 76
_CARD_DELTA_X = 66
# The next card, then the four hand cards from left to right.
CARD_BOXES = [
    NEXT_CARD_BOX,
    *(
        (
            _CARD_INIT_X + i * _CARD_DELTA_X,
            _CARD_Y,
            _CARD_INIT_X + i * _CARD_DELTA_X + _CARD_WIDTH,
            _CARD_Y + _CARD_HEIGHT,
        )
        for i in range(4)
    ),
]

ELIXIR_BOX = (100, 628, 350, 643)
# The elixir drop at the left end of the elixir bar, which only a battle
# shows. BattleCheck compares it with images/screen/in_game.jpg.
BATTLE_CHECK_BOX = (80, 624, 99, 649)

# Each tower's health bar, with the HP written on it and the level badge to
# its left. Named as in Towers.
PRINCESS_TOWER_BOXES = {
    "left_enemy_princess": (65, 108, 130, 132),
    "right_enemy_princess": (245, 108, 310, 132),
    "left_ally_princess": (65, 404, 130, 430),
    "right_ally_princess": (245, 404, 310, 430),
}
# Until it's first hit, a king tower shows only its badge, in the middle of
# its box.
KING_TOWER_BOXES = {
    "enemy_king": (147, 41, 221, 64),
    "ally_king": (147, 492, 221, 515),
}

# The battle timer in the top-right corner: "Time left:" (or "Overtime:")
# above the minutes and seconds.
TIMER_BOX = (304, 31, 368, 68)
