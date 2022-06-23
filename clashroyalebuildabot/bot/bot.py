import time

from clashroyalebuildabot.bot.action import Action
from clashroyalebuildabot.data.constants import (
    ALLY_TILES,
    LEFT_PRINCESS_TILES,
    RIGHT_PRINCESS_TILES,
    TILE_HEIGHT,
    TILE_WIDTH,
    DISPLAY_CARD_WIDTH,
    DISPLAY_CARD_HEIGHT,
    DISPLAY_CARD_Y,
    DISPLAY_CARD_INIT_X,
    DISPLAY_CARD_DELTA_X,
    SCREEN_CONFIG,
    TILE_INIT_X,
    TILE_INIT_Y,
    DISPLAY_HEIGHT
)
from clashroyalebuildabot.screen import Screen
from clashroyalebuildabot.state.detector import Detector


class Bot:
    def __init__(self, card_names,
                 action_class=Action,
                 auto_start=True,
                 debug=False):
        self.card_names = card_names
        self.action_class = action_class
        self.auto_start = auto_start
        self.debug = debug

        self.screen = Screen()
        self.detector = Detector(card_names, debug=self.debug)
        self.state = None

    @staticmethod
    def _get_nearest_tile(x, y):
        """
        Get the nearest tile to (x, y)
        """
        tile_x = round(((x - TILE_INIT_X) / TILE_WIDTH) - 0.5)
        tile_y = round(((DISPLAY_HEIGHT - TILE_INIT_Y - y) / TILE_HEIGHT) - 0.5)
        return tile_x, tile_y

    @staticmethod
    def _get_tile_centre(tile_x, tile_y):
        """
        Get the (x, y) coordinate of the centre of a tile
        """
        x = TILE_INIT_X + (tile_x + 0.5) * TILE_WIDTH
        y = DISPLAY_HEIGHT - TILE_INIT_Y - (tile_y + 0.5) * TILE_HEIGHT
        return x, y

    @staticmethod
    def _get_card_centre(card_n):
        """
        Get the (x, y) coordinate of the centre of card_n
        """
        x = DISPLAY_CARD_INIT_X + DISPLAY_CARD_WIDTH / 2 + card_n * DISPLAY_CARD_DELTA_X
        y = DISPLAY_CARD_Y + DISPLAY_CARD_HEIGHT / 2
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
            card = self.state['cards'][i + 1]
            enough_elixir = int(self.state['numbers']['elixir']['number']) >= card['cost']
            ready = card['ready']
            not_blank = card['name'] != 'blank'
            if enough_elixir and ready and not_blank:
                if card['type'] == 'spell':
                    tiles = all_tiles
                else:
                    tiles = valid_tiles
                actions.extend([self.action_class(i, x, y, *card.values())
                                for (x, y) in tiles])

        return actions

    def set_state(self):
        screenshot = self.screen.take_screenshot()
        self.state = self.detector.run(screenshot)

        # Try to click a button to get closer to starting a game
        if self.auto_start:
            if self.state['screen'] != 'in_game':
                self.screen.click(*SCREEN_CONFIG[self.state['screen']]['click_coordinates'])
                time.sleep(2)

    def play_action(self, action):
        card_centre = self._get_card_centre(action.index)
        tile_centre = self._get_tile_centre(action.tile_x, action.tile_y)
        self.screen.click(*card_centre)
        self.screen.click(*tile_centre)
