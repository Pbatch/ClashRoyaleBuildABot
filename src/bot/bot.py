from src.bot.action import Action
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
    CARD_DELTA_X,
    SCREEN_CONFIG
)
from src.screen import Screen
from src.state.detector import Detector


class Bot:
    def __init__(self, card_names, action_class=Action, auto_start=True):
        self.card_names = card_names
        self.action_class = action_class
        self.auto_start = auto_start

        self.screen = Screen()
        self.detector = Detector(card_names)
        self.state = None

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

    def _get_valid_tiles(self):
        """
        Calculate which tiles we are allowed to play on
        """
        tiles = ALLY_TILES
        if self.state['numbers']['left_enemy_princess_hp']['number'] == 0:
            tiles += LEFT_PRINCESS_TILES
        if self.state['numbers']['right_enemy_princess_hp']['number'] == 0:
            tiles += RIGHT_PRINCESS_TILES
        return tiles

    def get_actions(self):
        if len(self.state) == 0:
            return []
        all_tiles = ALLY_TILES + LEFT_PRINCESS_TILES + RIGHT_PRINCESS_TILES
        valid_tiles = self._get_valid_tiles()

        # Compute the list of playable actions
        # An action is a tuple (card_index, tile_x, tile_y)
        actions = []
        for i in range(4):
            if int(self.state['numbers']['elixir']['number']) >= self.state['cards'][i + 1]['cost']:
                if self.state['cards'][i + 1]['type'] == 'spell':
                    tiles = all_tiles
                else:
                    tiles = valid_tiles
                actions.extend([self.action_class(i, x, y, *self.state['cards'][i + 1].values())
                                for (x, y) in tiles])

        return actions

    def set_state(self):
        screenshot = self.screen.take_screenshot()
        self.state = self.detector.run(screenshot)

        # Try to click a button to get closer to starting a game
        if self.auto_start:
            for name, bounding_box, click_coordinates in SCREEN_CONFIG:
                if self.state['screen'][name] and 'name' != 'in_game':
                    self.screen.click(*click_coordinates)

    def play_action(self, action):
        card_centre = self._get_card_centre(action.index)
        tile_centre = self._get_tile_centre(action.tile_x, action.tile_y)
        self.screen.click(*card_centre)
        self.screen.click(*tile_centre)
