from collections.abc import Sequence

import numpy as np
from loguru import logger

from clashroyalebuildabot.detectors.card_detector import CardDetector
from clashroyalebuildabot.detectors.elixir_reader import ElixirReader
from clashroyalebuildabot.detectors.screen_detector import ScreenDetector
from clashroyalebuildabot.detectors.timer_reader import TimerReader
from clashroyalebuildabot.detectors.tower_hp_reader import TowerHPReader
from clashroyalebuildabot.detectors.unit_detector import UnitDetector
from clashroyalebuildabot.game import ScreenName, State
from clashroyalebuildabot.game.cards import DECK_SIZE, Card
from clashroyalebuildabot.utils.error_handling import WikifiedError

# Screens that only come between battles, so a battle has ended.
BETWEEN_BATTLES = {
    ScreenName.LOBBY,
    ScreenName.END_OF_GAME,
    ScreenName.BYPASS_END_OF_GAME,
}


class StateReader:
    def __init__(self, cards: Sequence[Card]) -> None:
        if len(cards) != DECK_SIZE:
            raise WikifiedError(
                "005",
                f"Your deck must have {DECK_SIZE} cards, "
                f"but {len(cards)} were given",
            )

        self.cards = cards

        self.card_detector = CardDetector(self.cards)
        self.elixir_reader = ElixirReader()
        self.unit_detector = UnitDetector(self.cards)
        self.screen_detector = ScreenDetector()
        self.tower_hp_reader = TowerHPReader()
        self.timer_reader = TimerReader()

        # Parts that remember the battle so far, which start afresh with
        # each battle: each has a reset().
        self._battle_memory = [
            self.tower_hp_reader,
            self.timer_reader,
            self.card_detector,
        ]

    def run(self, image: np.ndarray) -> State | None:
        """
        Detect the state of one screenshot. Returns None if detection fails,
        and the bot moves on to the next screenshot. Retrying the same image
        would fail the same way, since detection is deterministic.

        Cards, units, elixir, tower HP and the timer are only read in a
        battle. On other screens they would be meaningless, so the state has
        no units or cards and 0 elixir.

        Whether this is a battle comes from the frame itself (the
        ScreenDetector reads the timer and looks for the elixir bar), so the
        bot plays as soon as a battle starts, and stops as soon as it ends.
        """
        logger.debug("Setting state...")
        try:
            screen = self.screen_detector.run(image)
            if screen != ScreenName.IN_GAME:
                if screen in BETWEEN_BATTLES:
                    # Start the next battle with fresh readings.
                    for part in self._battle_memory:
                        part.reset()
                # Otherwise it's a screen the bot waits through, or the
                # elixir bar is hidden for a moment mid-battle: keep the
                # readings in case the battle goes on.
                return self._state_outside_battle(screen)

            cards, ready = self.card_detector.run(image)
            allies, enemies = self.unit_detector.run(image)
            elixir = self.elixir_reader.run(image)
            towers = self.tower_hp_reader.run(image)
            timer = self.timer_reader.run(image)
        except Exception:
            logger.exception("Detection failed, skipping this screenshot.")
            return None
        return State(
            allies=allies,
            enemies=enemies,
            elixir=elixir,
            towers=towers,
            timer=timer,
            cards=cards,
            ready=ready,
            screen=screen,
        )

    def _state_outside_battle(self, screen: ScreenName) -> State:
        return State(
            allies=[],
            enemies=[],
            elixir=0,
            towers=self.tower_hp_reader.latest(),
            timer=self.timer_reader.latest(),
            cards=[],
            ready=[],
            screen=screen,
        )

    def close(self) -> None:
        """Nothing to release: every part reads frames as they come, with no
        threads of its own. The bot calls this when it stops."""
