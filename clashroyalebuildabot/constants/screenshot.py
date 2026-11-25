"""Positions in the screenshot the detectors read, 368x652 pixels.

Boxes are (left, top, right, bottom).
"""

SCREENSHOT_WIDTH = 368
SCREENSHOT_HEIGHT = 652

# Cards. Each box is the card's face (its art and thin dark border), the same
# framing as the card art the card embeddings are made from, without the
# frame around it. Measured by matching that art to battle frames.
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

# The elixir bar, from just right of the elixir drop: the elixir written at
# its left end, then the pink fill. Its middle rows, where the fill is
# solid.
ELIXIR_BOX = (100, 630, 360, 641)
# The elixir written beside the drop.
ELIXIR_NUMBER_BOX = (100, 618, 132, 646)

# Buttons the ScreenDetector recognises screens by, inside their edges: the
# word "Battle" on the lobby's Battle button, and the results screen's Play
# Again and OK buttons. The results screen has a second layout with only an
# OK button, in the centre.
LOBBY_BATTLE_BOX = (140, 490, 240, 518)
RESULTS_PLAY_AGAIN_BOX = (88, 578, 172, 615)
RESULTS_OK_BOX = (196, 578, 280, 615)
RESULTS_CENTRE_OK_BOX = (142, 578, 226, 615)

# Each tower's health bar, with the HP written on it and the level badge to
# its left. Named as in Towers. The bars sit a little higher in some arenas
# than others, so each box reaches 4 pixels above the bar, where the HP's
# digits would otherwise be cut off.
PRINCESS_TOWER_BOXES = {
    "left_enemy_princess": (65, 104, 130, 132),
    "right_enemy_princess": (245, 104, 310, 132),
    "left_ally_princess": (65, 400, 130, 430),
    "right_ally_princess": (245, 400, 310, 430),
}
# Until it's first hit, a king tower shows only its badge, in the middle of
# its box.
KING_TOWER_BOXES = {
    "enemy_king": (147, 37, 221, 64),
    "ally_king": (147, 488, 221, 515),
}

# The battle timer in the top-right corner: "Time left:" (or "Overtime:")
# above the minutes and seconds.
TIMER_BOX = (304, 31, 368, 68)
