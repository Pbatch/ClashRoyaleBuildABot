import time

from loguru import logger

from clashroyalebuildabot.bot.action import Action
from clashroyalebuildabot.constants import ALLY_TILES
from clashroyalebuildabot.constants import DISPLAY_CARD_DELTA_X
from clashroyalebuildabot.constants import DISPLAY_CARD_HEIGHT
from clashroyalebuildabot.constants import DISPLAY_CARD_INIT_X
from clashroyalebuildabot.constants import DISPLAY_CARD_WIDTH
from clashroyalebuildabot.constants import DISPLAY_CARD_Y
from clashroyalebuildabot.constants import DISPLAY_HEIGHT
from clashroyalebuildabot.constants import LEFT_PRINCESS_TILES
from clashroyalebuildabot.constants import RIGHT_PRINCESS_TILES
from clashroyalebuildabot.constants import TILE_HEIGHT
from clashroyalebuildabot.constants import TILE_INIT_X
from clashroyalebuildabot.constants import TILE_INIT_Y
from clashroyalebuildabot.constants import TILE_WIDTH
from clashroyalebuildabot.detectors.detector import Detector
from clashroyalebuildabot.emulator import Emulator
from clashroyalebuildabot.namespaces import Screens


class Bot:
    def __init__(
        self, cards, action_class=Action, auto_start=True, debug=False
    ):
        self.cards = cards
        self.action_class = action_class
        self.auto_start = auto_start
        self.debug = debug
        self.emulator = Emulator()
        self.detector = Detector(cards, debug=self.debug)
        self.state = None

    @staticmethod
    def _get_nearest_tile(x, y):
        tile_x = round(((x - TILE_INIT_X) / TILE_WIDTH) - 0.5)
        tile_y = round(
            ((DISPLAY_HEIGHT - TILE_INIT_Y - y) / TILE_HEIGHT) - 0.5
        )
        return tile_x, tile_y

    @staticmethod
    def _get_tile_centre(tile_x, tile_y):
        x = TILE_INIT_X + (tile_x + 0.5) * TILE_WIDTH
        y = DISPLAY_HEIGHT - TILE_INIT_Y - (tile_y + 0.5) * TILE_HEIGHT
        return x, y

    @staticmethod
    def _get_card_centre(card_n):
        x = (
            DISPLAY_CARD_INIT_X
            + DISPLAY_CARD_WIDTH / 2
            + card_n * DISPLAY_CARD_DELTA_X
        )
        y = DISPLAY_CARD_Y + DISPLAY_CARD_HEIGHT / 2
        return x, y

    def _get_valid_tiles(self):
        tiles = ALLY_TILES
        if self.state.numbers["left_enemy_princess_hp"]["number"] == 0:
            tiles += LEFT_PRINCESS_TILES
        if self.state.numbers["right_enemy_princess_hp"]["number"] == 0:
            tiles += RIGHT_PRINCESS_TILES
        return tiles

    def get_actions(self):
        if not self.state:
            return []
        all_tiles = ALLY_TILES + LEFT_PRINCESS_TILES + RIGHT_PRINCESS_TILES
        valid_tiles = self._get_valid_tiles()
        actions = []
        for i in self.state.ready:
            card = self.state.cards[i + 1]
            if int(self.state.numbers["elixir"]["number"]) < card.cost:
                continue

            tiles = all_tiles if card.target_anywhere else valid_tiles
            actions.extend(
                [self.action_class(i, x, y, card) for (x, y) in tiles]
            )

        return actions

    def set_state(self):
        try:
            screenshot = self.emulator.take_screenshot()
            self.state = self.detector.run(screenshot)
            if self.auto_start and self.state.screen != Screens.IN_GAME:
                self.emulator.click(*self.state.screen.click_xy)
                time.sleep(2)
        except Exception as e:
            logger.error(f"Error occurred while taking screenshot: {e}")

    def play_action(self, action):
        card_centre = self._get_card_centre(action.index)
        tile_centre = self._get_tile_centre(action.tile_x, action.tile_y)
        self.emulator.click(*card_centre)
        self.emulator.click(*tile_centre)
