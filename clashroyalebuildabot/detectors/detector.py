import os

from loguru import logger

from clashroyalebuildabot.config import ScreenDetectorConfig
from clashroyalebuildabot.constants.paths import MODELS_DIR
from clashroyalebuildabot.detectors.battle_check import BattleCheck
from clashroyalebuildabot.detectors.card_detector import CardDetector
from clashroyalebuildabot.detectors.number_detector import NumberDetector
from clashroyalebuildabot.detectors.screen_detector import ScreenDetector
from clashroyalebuildabot.detectors.timer_reader import TimerReader
from clashroyalebuildabot.detectors.tower_hp_reader import TowerHPReader
from clashroyalebuildabot.detectors.unit_detector import UnitDetector
from clashroyalebuildabot.detectors.vlm_client import make_client
from clashroyalebuildabot.game import ScreenName, State
from clashroyalebuildabot.game.cards import DECK_SIZE
from clashroyalebuildabot.game.numbers import Numbers
from clashroyalebuildabot.utils.error_handling import WikifiedError


class Detector:
    def __init__(self, cards, screen_config: ScreenDetectorConfig):
        if len(cards) != DECK_SIZE:
            raise WikifiedError(
                "005",
                f"Your deck must have {DECK_SIZE} cards, "
                f"but {len(cards)} were given",
            )

        self.cards = cards

        self.card_detector = CardDetector(self.cards)
        self.number_detector = NumberDetector()
        self.battle_check = BattleCheck()
        self.unit_detector = UnitDetector(
            os.path.join(MODELS_DIR, "units_M_480x352.onnx"), self.cards
        )
        # Screens, tower HP and the timer are read by the same vision model
        # server.
        client = make_client(screen_config)
        self.screen_detector = ScreenDetector.from_config(
            screen_config, client
        )
        interval = screen_config.interval
        self.tower_hp_reader = TowerHPReader(client, interval=interval)
        self.timer_reader = TimerReader(client, interval=interval)

    def run(self, image) -> State | None:
        """
        Detect the state of one screenshot. Returns None if detection fails,
        and the bot moves on to the next screenshot. Retrying the same image
        would fail the same way, since detection is deterministic.

        Cards, units, elixir, tower HP and the timer are only read in a
        battle. On other screens they would be meaningless, so the state has
        no units or cards and 0 elixir.
        """
        logger.debug("Setting state...")
        try:
            screen = self.screen_detector.run(image)
            if screen != ScreenName.IN_GAME:
                # Between battles: start the next one with fresh readings.
                self.tower_hp_reader.reset()
                self.timer_reader.reset()
                self.card_detector.reset()
                return self._state_outside_battle(screen)
            if not self.battle_check.run(image):
                # The screen detector's answer is older than this frame, and
                # the battle has ended or not yet begun. Keep the tower and
                # timer readings in case this is a brief flicker mid-battle.
                logger.debug(
                    "The screen detector says in game, but no "
                    "elixir bar is visible."
                )
                return self._state_outside_battle(ScreenName.UNKNOWN)

            cards, ready = self.card_detector.run(image)
            allies, enemies = self.unit_detector.run(image)
            elixir = self.number_detector.run(image)
            towers = self.tower_hp_reader.run(image)
            timer = self.timer_reader.run(image)
            numbers = Numbers(elixir=elixir, towers=towers, timer=timer)
        except Exception:
            logger.exception("Detection failed, skipping this screenshot.")
            return None
        return State(allies, enemies, numbers, cards, ready, screen)

    def _state_outside_battle(self, screen: ScreenName) -> State:
        numbers = Numbers(
            towers=self.tower_hp_reader.latest(),
            timer=self.timer_reader.latest(),
        )
        return State([], [], numbers, [], [], screen)

    def close(self):
        self.screen_detector.close()
        self.tower_hp_reader.close()
        self.timer_reader.close()
