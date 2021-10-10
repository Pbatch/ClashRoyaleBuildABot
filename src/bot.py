from src.screen import Screen
from src.ocr import OCR
from src.constants import (
    ALLY_TILES,
    LEFT_PRINCESS_TILES,
    RIGHT_PRINCESS_TILES,
    LEFT_PAD,
    LOWER_PAD,
    APP_HEIGHT,
    BORDER_SIZE,
    TILE_HEIGHT,
    TILE_WIDTH,
    CARD_SIZE,
    CARD_Y,
    CARD_INIT_X,
    CARD_DELTA_X
)


class Bot:
    def __init__(self):
        self.screen = Screen()
        self.ocr = OCR()

    @staticmethod
    def get_tile_centre(tile_x, tile_y):
        x = LEFT_PAD + (tile_x + 0.5) * TILE_WIDTH
        y = APP_HEIGHT - BORDER_SIZE - LOWER_PAD - (tile_y + 0.5) * TILE_HEIGHT
        return x, y

    @staticmethod
    def get_card_centre(card_n):
        x = CARD_INIT_X + CARD_SIZE/2 + card_n * CARD_DELTA_X
        y = CARD_Y - BORDER_SIZE + CARD_SIZE/2
        return x, y

    def get_actions(self, state):
        # Calculate which tiles we can play on
        tiles = ALLY_TILES
        if state['left_enemy_princess'] == 0:
            tiles += LEFT_PRINCESS_TILES
        elif state['right_enemy_princess'] == 0:
            tiles += RIGHT_PRINCESS_TILES

        # Add actions for all playable cards on each playable tile
        actions = []
        for i in range(4):
            if state['elixir'] >= state[f'card_{i}'] != -1:
                actions.extend([[i, x, y] for (x, y) in tiles])

        return actions

    def get_state(self):
        screenshot = self.screen.take_screenshot()
        state = self.ocr.run(screenshot)
        return state

    def play_action(self, action):
        card_centre = self.get_card_centre(action[0])
        tile_centre = self.get_tile_centre(action[1], action[2])
        self.screen.click(*card_centre)
        self.screen.click(*tile_centre)