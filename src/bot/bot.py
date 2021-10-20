from src.screen import Screen
from src.state.detector import Detector
from src.data.constants import (
    ALLY_TILES,
    LEFT_PRINCESS_TILES,
    RIGHT_PRINCESS_TILES,
    LEFT_PAD,
    LOWER_PAD,
    APP_HEIGHT,
    BORDER_SIZE,
    TILE_HEIGHT,
    TILE_WIDTH,
    CARD_WIDTH,
    CARD_HEIGHT,
    CARD_Y,
    CARD_INIT_X,
    CARD_DELTA_X
)


class Bot:
    def __init__(self, card_names):
        self.card_names = card_names

        self.screen = Screen()
        self.detector = Detector(card_names)

    @staticmethod
    def _get_nearest_tile(x, y):
        """
        Get the nearest tile to (x, y)
        """
        tile_x = round(((x - LEFT_PAD) / TILE_WIDTH) - 0.5)
        tile_y = round(((APP_HEIGHT - BORDER_SIZE - LOWER_PAD - y) / TILE_HEIGHT) - 0.5)
        return tile_x, tile_y

    @staticmethod
    def _get_tile_centre(tile_x, tile_y):
        """
        Get the (x, y) coordinate of the centre of a tile
        """
        x = LEFT_PAD + (tile_x + 0.5) * TILE_WIDTH
        y = APP_HEIGHT - BORDER_SIZE - LOWER_PAD - (tile_y + 0.5) * TILE_HEIGHT
        return x, y

    @staticmethod
    def _get_card_centre(card_n):
        """
        Get the (x, y) coordinate of the centre of card_n
        """
        x = CARD_INIT_X + CARD_WIDTH / 2 + card_n * CARD_DELTA_X
        y = CARD_Y - BORDER_SIZE + CARD_HEIGHT / 2
        return x, y

    @staticmethod
    def _get_valid_tiles(state):
        """
        Calculate which tiles we are allowed to play on
        """
        tiles = ALLY_TILES
        if state['numbers']['left_enemy_princess']['number'] == 0:
            tiles += LEFT_PRINCESS_TILES
        if state['numbers']['right_enemy_princess']['number'] == 0:
            tiles += RIGHT_PRINCESS_TILES
        return tiles

    def get_actions(self, state):
        all_tiles = ALLY_TILES + LEFT_PRINCESS_TILES + RIGHT_PRINCESS_TILES
        valid_tiles = self._get_valid_tiles(state)

        # Compute the list of playable actions
        # An action is a tuple (card_index, tile_x, tile_y)
        actions = []
        for i in range(4):
            if int(state['numbers']['elixir']['number']) >= state['cards'][i+1]['cost']:
                if state['cards'][i+1]['type'] == 'spell':
                    actions.extend([[i, x, y] for (x, y) in all_tiles])
                else:
                    actions.extend([[i, x, y] for (x, y) in valid_tiles])

        return actions

    def get_state(self):
        screenshot = self.screen.take_screenshot()
        state = self.detector.run(screenshot)
        return state

    def play_action(self, action):
        card_centre = self._get_card_centre(action[0])
        tile_centre = self._get_tile_centre(action[1], action[2])
        self.screen.click(*card_centre)
        self.screen.click(*tile_centre)