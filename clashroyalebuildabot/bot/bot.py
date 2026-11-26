import itertools
import threading
import time
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol, cast

import numpy as np
from loguru import logger

from clashroyalebuildabot.actions.generic.action import Action
from clashroyalebuildabot.bot.plays import (
    Play,
    PlayRejected,
    PlayRequest,
    PlayRequests,
    PlayResult,
    Reason,
    check,
)
from clashroyalebuildabot.bot.policy import Policy, ScoringPolicy
from clashroyalebuildabot.bot.visualizer import FrameCallback, Visualizer
from clashroyalebuildabot.config import Config
from clashroyalebuildabot.constants.device_screen import (
    DISPLAY_HEIGHT,
    HAND_CARD_BOXES,
    TILE_HEIGHT,
    TILE_INIT_X,
    TILE_INIT_Y,
    TILE_WIDTH,
)
from clashroyalebuildabot.detectors.state_reader import StateReader
from clashroyalebuildabot.emulator import Emulator
from clashroyalebuildabot.game import ScreenName, Screens
from clashroyalebuildabot.game.cards import Card
from clashroyalebuildabot.game.state import State

# Screens the bot just waits through.
WAITING_SCREENS = {ScreenName.UNKNOWN}
# Seconds between looks at a screen outside a battle. Nothing there needs
# an answer faster.
SCREEN_POLL_DELAY = 0.5
# How many recent frames' times the bot remembers, to tell how old the
# frame a client decided on is.
FRAME_HISTORY = 256

# Frame numbers, unique for the life of the process, so a frame number from
# one run of the bot can't be mistaken for one from the next.
_frame_numbers = itertools.count(1)


class Device(Protocol):
    """The phone, or an emulator: frames from it, and taps on it."""

    def take_screenshot(self) -> np.ndarray | None: ...
    def click(self, x: float, y: float) -> None: ...
    def tap_sequence(self, points: Sequence[tuple[float, float]]) -> None: ...
    def load_deck(self, cards: Sequence[Card]) -> None: ...
    def close(self) -> None: ...


class StateSource(Protocol):
    """Reads the game's state from a frame."""

    def run(self, image: np.ndarray) -> State | None: ...
    def close(self) -> None: ...


class FrameViewer(Protocol):
    """Shows or saves each frame with what was read from it."""

    def run(self, image: np.ndarray, state: State) -> None: ...


@dataclass(frozen=True)
class PendingPlay:
    """A card the bot has tapped, which the frames don't yet show played."""

    card: Card
    # Hand position, 0-3.
    index: int
    # Elixir just before the play.
    elixir: int
    started: float
    deadline: float

    def landed(self, state: State) -> bool:
        """Whether the frame shows the card played: it has left its place
        in the hand, or elixir has been spent."""
        position = self.index + 1
        if len(state.cards) > position and state.cards[position] != self.card:
            return True
        return state.elixir < self.elixir


@dataclass(frozen=True)
class Observation:
    """One frame's State, as the bot read it."""

    frame: int
    # When it was read: time.time(), for clients, and time.monotonic(), for
    # telling its age.
    time: float
    monotonic: float
    state: State
    # The card the bot last played, while the frames don't yet show it
    # played. The bot won't play again until they do.
    pending: PendingPlay | None


type ObservationCallback = Callable[[Observation], None]


class Bot:
    def __init__(
        self,
        actions: Sequence[type[Action]],
        config: Config,
        on_frame: FrameCallback | None = None,
        *,
        on_observation: ObservationCallback | None = None,
        policy: Policy | None = None,
        device: Device | None = None,
        state_reader: StateSource | None = None,
        visualizer: FrameViewer | None = None,
    ) -> None:
        """Without ``device``, ``state_reader`` or ``visualizer``, the bot makes
        its own from ``config``. Either way it owns them, and closes the
        device and the state reader when it stops.

        Without ``policy``, ``config.bot.policy`` decides: the built-in
        ScoringPolicy, or none (external), so the bot plays what's sent to
        ``requests``. ``on_observation`` is called with every frame read.
        """
        self.actions = actions
        self.auto_start = config.bot.auto_start_game
        self.end_of_game_clicked = False
        self.bypass_end_of_game_clicked = False
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()

        # The StateReader checks the deck size, before the emulator is created.
        cards = [action.CARD for action in actions]
        if policy is None and config.bot.policy == "builtin":
            policy = ScoringPolicy(actions)
        # None: external. Plays come from requests.
        self.policy = policy
        self.requests = PlayRequests()
        self.on_observation = on_observation
        self.observation: Observation | None = None
        self._frame_times: deque[tuple[int, float]] = deque(
            maxlen=FRAME_HISTORY
        )

        # The longest the bot waits for a card it played to show as played.
        self.play_action_delay = config.ingame.play_action
        self.pending_play: PendingPlay | None = None
        if visualizer is None:
            visualizer = Visualizer(
                **config.visuals.model_dump(), on_frame=on_frame
            )
        self.visualizer = visualizer
        if state_reader is None:
            state_reader = StateReader(cards=cards)
        self.state_reader = state_reader

        # The emulator owns a screen-recording process and a frame thread,
        # so it is created last and closed again if anything after it fails.
        if device is None:
            device = Emulator(device_serial=config.adb.device_serial)
        self.emulator = device
        try:
            if config.bot.load_deck:
                self.emulator.load_deck(cards)
        except BaseException:
            self.emulator.close()
            raise

    def _log_and_wait(self, prefix: str, delay: float) -> None:
        suffix = ""
        if delay > 1:
            suffix = "s"
        message = f"{prefix}. Waiting for {delay} second{suffix}."
        logger.info(message)
        # Returns early if stop() is called, so stopping is never delayed.
        self._stop_event.wait(delay)

    @property
    def is_paused(self) -> bool:
        return self._pause_event.is_set()

    def pause(self) -> None:
        if not self.is_paused:
            self._pause_event.set()
            logger.info("Bot paused.")

    def resume(self) -> None:
        if self.is_paused:
            self._pause_event.clear()
            logger.info("Bot resumed.")

    def toggle_pause(self) -> None:
        if self.is_paused:
            self.resume()
        else:
            self.pause()

    @staticmethod
    def _get_tile_centre(tile_x: int, tile_y: int) -> tuple[float, float]:
        x = TILE_INIT_X + (tile_x + 0.5) * TILE_WIDTH
        y = DISPLAY_HEIGHT - TILE_INIT_Y - (tile_y + 0.5) * TILE_HEIGHT
        return x, y

    @staticmethod
    def _get_card_centre(card_n: int) -> tuple[float, float]:
        left, top, right, bottom = HAND_CARD_BOXES[card_n]
        return (left + right) / 2, (top + bottom) / 2

    @property
    def is_external(self) -> bool:
        """Whether the bot plays what clients ask for, not its own policy."""
        return self.policy is None

    def compute_state(self) -> State | None:
        screenshot = self.emulator.take_screenshot()
        if screenshot is None:
            return None
        state = self.state_reader.run(screenshot)
        if state is not None:
            self.visualizer.run(screenshot, state)
        return state

    def play(self, play: Play) -> None:
        """Tap the card, then the tile."""
        card_centre = self._get_card_centre(play.hand_index)
        tile_centre = self._get_tile_centre(play.tile_x, play.tile_y)
        self.emulator.tap_sequence([card_centre, tile_centre])

    def _observe(self, state: State) -> None:
        if state.screen == ScreenName.IN_GAME:
            # Clears the pending play if this frame shows it landed, so the
            # observation says whether the bot can play now.
            self._waiting_for_play(state)
        else:
            self.pending_play = None
        frame = next(_frame_numbers)
        now = time.monotonic()
        self._frame_times.append((frame, now))
        self.observation = Observation(
            frame=frame,
            time=time.time(),
            monotonic=now,
            state=state,
            pending=self.pending_play,
        )
        if self.on_observation is not None:
            self.on_observation(self.observation)

    def _frame_time(self, frame: int) -> float | None:
        for number, read_at in reversed(self._frame_times):
            if number == frame:
                return read_at
        return None

    def step(self, state: State | None) -> State | None:

        old_screen = state.screen if state else None
        state = self.compute_state()
        if state is None:
            return state
        self._observe(state)

        new_screen = state.screen
        if new_screen != old_screen:
            logger.info(f"New screen state: {new_screen}")
        if new_screen != ScreenName.IN_GAME:
            self.requests.reject_waiting(
                Reason.NOT_IN_BATTLE, f"Not in a battle: on {new_screen}."
            )

        # Wait here, before the end-of-game flags below are cleared, so a
        # flicker through one of these screens can't cause a second tap.
        if new_screen in WAITING_SCREENS:
            self._log_and_wait(
                f"Waiting on the {new_screen} screen", SCREEN_POLL_DELAY
            )
            return state

        if new_screen == ScreenName.END_OF_GAME:
            if not self.end_of_game_clicked:
                self.emulator.click(
                    *cast(
                        "tuple[int, int]",
                        Screens.get(ScreenName.END_OF_GAME).click_xy,
                    )
                )
                self.end_of_game_clicked = True
                self._log_and_wait("Clicked END_OF_GAME screen", 2)
            return state
        self.end_of_game_clicked = False

        if new_screen == ScreenName.BYPASS_END_OF_GAME:
            if not self.bypass_end_of_game_clicked:
                self.emulator.click(
                    *cast(
                        "tuple[int, int]",
                        Screens.get(ScreenName.BYPASS_END_OF_GAME).click_xy,
                    )
                )
                self.bypass_end_of_game_clicked = True
                self._log_and_wait("Clicked BYPASS_END_OF_GAME screen", 2)
            return state
        self.bypass_end_of_game_clicked = False

        if self.auto_start and new_screen == ScreenName.LOBBY:
            self.emulator.click(
                *cast(
                    "tuple[int, int]", Screens.get(ScreenName.LOBBY).click_xy
                )
            )
            self._log_and_wait("Starting game", 2)
            return state

        # Only play cards in a battle, never in the lobby.
        if new_screen != ScreenName.IN_GAME:
            self._log_and_wait(
                f"Waiting on the {new_screen} screen", SCREEN_POLL_DELAY
            )
            return state

        self._handle_game_step(state)
        return state

    def _waiting_for_play(self, state: State) -> bool:
        """Whether a card the bot played hasn't yet shown as played. Until
        it does, the frames still show it in hand with the elixir unspent,
        and the bot would play it again."""
        pending = self.pending_play
        if pending is None:
            return False
        now = time.monotonic()
        if pending.landed(state):
            logger.debug(
                f"{pending.card.name} played after "
                f"{now - pending.started:.2f} seconds."
            )
        elif now < pending.deadline:
            return True
        else:
            logger.debug(
                f"{pending.card.name} not seen played after "
                f"{self.play_action_delay} seconds, moving on."
            )
        self.pending_play = None
        return False

    def _handle_game_step(self, state: State) -> None:
        # The bot never sleeps in a battle: it looks again at the next
        # frame, so it plays as soon as a card is affordable or worth
        # playing, and as soon as the last card it played has landed.
        if self.policy is None:
            self._serve_request(state)
            return
        if self._waiting_for_play(state):
            return
        play = self.policy.choose(state)
        if play is None:
            return
        try:
            card = check(state, play)
        except PlayRejected as e:
            logger.warning(f"The policy chose a play it can't make: {e}")
            return
        self._make(play, card, state)

    def _serve_request(self, state: State) -> None:
        """Make the play a client asked for, if it's still allowed."""
        request = self.requests.take()
        if request is None:
            return
        try:
            card = self._check_request(request, state)
        except PlayRejected as e:
            logger.debug(f"Refused {request.play}: {e}")
            request.future.set_exception(e)
            return
        logger.info(
            f"Playing {card.name} at "
            f"({request.play.tile_x}, {request.play.tile_y}) for a client"
        )
        self._make(request.play, card, state)
        frame = self.observation.frame if self.observation else 0
        request.future.set_result(
            PlayResult(card=card, play=request.play, frame=frame)
        )

    def _check_request(self, request: PlayRequest, state: State) -> Card:
        if request.frame is not None:
            read_at = self._frame_time(request.frame)
            if read_at is None:
                raise PlayRejected(
                    Reason.STALE, f"Frame {request.frame} is unknown or old."
                )
            age = time.monotonic() - read_at
            if age > request.max_age:
                raise PlayRejected(
                    Reason.STALE,
                    f"Frame {request.frame} is {age:.2f} seconds old, "
                    f"older than max_age ({request.max_age}).",
                )
        if self._waiting_for_play(state):
            raise PlayRejected(
                Reason.PLAY_PENDING,
                "The last card played hasn't shown as played yet.",
            )
        return check(state, request.play)

    def _make(self, play: Play, card: Card, state: State) -> None:
        self.play(play)
        now = time.monotonic()
        self.pending_play = PendingPlay(
            card=card,
            index=play.hand_index,
            elixir=state.elixir,
            started=now,
            deadline=now + self.play_action_delay,
        )

    def run(self) -> None:
        """Play until stop() is called. Always closes the emulator on exit."""
        state = None
        try:
            while not self._stop_event.is_set():
                if self.is_paused:
                    self._stop_event.wait(0.1)
                    continue

                state = self.step(state)
        except KeyboardInterrupt:
            pass
        finally:
            self.requests.reject_waiting(
                Reason.NOT_RUNNING, "The bot has stopped."
            )
            self.state_reader.close()
            self.emulator.close()
        logger.info("Thanks for using CRBAB, see you next time!")

    def stop(self) -> None:
        """Ask run() to return. Safe to call from any thread."""
        self._stop_event.set()
