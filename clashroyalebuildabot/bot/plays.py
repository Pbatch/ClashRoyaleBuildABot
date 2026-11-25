"""What the bot may play, and where: the rules the built-in policy and an
outside client's plays (through the API) are both held to. Also the
hand-off of a client's play from the API's thread to the bot's.
"""

import threading
from concurrent.futures import Future
from dataclasses import dataclass, field
from enum import StrEnum

from clashroyalebuildabot.constants.device_screen import (
    ALL_TILES,
    ALLY_TILES,
    LEFT_PRINCESS_TILES,
    RIGHT_PRINCESS_TILES,
    TOWER_TILES,
)
from clashroyalebuildabot.game.cards import Card
from clashroyalebuildabot.game.screens import ScreenName
from clashroyalebuildabot.game.state import State

HAND_SIZE = 4

# The tiles under our towers, where nothing can be placed. Left out even
# once a princess tower falls: its ruins may still block placement, and a
# missed tile costs less than a tap the game refuses.
ALLY_TOWER_TILES = frozenset(
    (x, y)
    for name in ("left_ally_princess", "right_ally_princess", "ally_king")
    for x0, y0, x1, y1 in [TOWER_TILES[name]]
    for x in range(x0, x1 + 1)
    for y in range(y0, y1 + 1)
)


@dataclass(frozen=True)
class Play:
    """Play the card at hand position ``hand_index`` (0-3, left to right)
    on tile (``tile_x``, ``tile_y``)."""

    hand_index: int
    tile_x: int
    tile_y: int


class Reason(StrEnum):
    """Why a play wasn't made. Stable: clients match on these."""

    NOT_RUNNING = "not_running"
    PAUSED = "paused"
    BUILTIN_POLICY = "builtin_policy"
    NOT_IN_BATTLE = "not_in_battle"
    PLAY_PENDING = "play_pending"
    BUSY = "busy"
    STALE = "stale"
    TIMEOUT = "timeout"
    BAD_HAND_INDEX = "bad_hand_index"
    NOT_READY = "not_ready"
    NOT_ENOUGH_ELIXIR = "not_enough_elixir"
    BAD_TILE = "bad_tile"


class PlayRejected(Exception):
    def __init__(self, reason: Reason, message: str) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message


def placeable_tiles(state: State) -> list[list[int]]:
    """Where a troop or building can go: our half, apart from the tiles
    under our towers, plus the enemy's half behind each princess tower that
    has fallen."""
    tiles = [
        tile for tile in ALLY_TILES if tuple(tile) not in ALLY_TOWER_TILES
    ]
    if state.towers.left_enemy_princess.hp == 0:
        tiles += LEFT_PRINCESS_TILES
    if state.towers.right_enemy_princess.hp == 0:
        tiles += RIGHT_PRINCESS_TILES
    return tiles


def tiles_for(card: Card, state: State) -> list[list[int]]:
    """Where card can be played. Spells, and anything else that targets
    anywhere, go on any tile."""
    return list(ALL_TILES) if card.target_anywhere else placeable_tiles(state)


def hand_card(state: State, hand_index: int) -> Card | None:
    """The card at a hand position, or None if the slot is empty or there's
    no such position."""
    position = hand_index + 1
    if 0 <= hand_index < HAND_SIZE and position < len(state.cards):
        return state.cards[position]
    return None


def affordable_hand(state: State) -> list[tuple[int, Card]]:
    """The hand positions that can be played now, ready and affordable,
    each with its card."""
    playable = []
    for i in state.ready:
        card = hand_card(state, i)
        if card is not None and state.elixir >= card.cost:
            playable.append((i, card))
    return playable


def check(state: State, play: Play) -> Card:
    """The card play would play. Raises PlayRejected if the rules don't
    allow it in state."""
    if state.screen != ScreenName.IN_GAME:
        raise PlayRejected(
            Reason.NOT_IN_BATTLE, f"Not in a battle: on {state.screen}."
        )
    card = hand_card(state, play.hand_index)
    if card is None:
        raise PlayRejected(
            Reason.BAD_HAND_INDEX,
            f"No card at hand position {play.hand_index}.",
        )
    if play.hand_index not in state.ready:
        raise PlayRejected(
            Reason.NOT_READY, f"{card.name} isn't ready to play."
        )
    if state.elixir < card.cost:
        raise PlayRejected(
            Reason.NOT_ENOUGH_ELIXIR,
            f"{card.name} costs {card.cost}, elixir is {state.elixir}.",
        )
    if [play.tile_x, play.tile_y] not in tiles_for(card, state):
        raise PlayRejected(
            Reason.BAD_TILE,
            f"{card.name} can't be played on ({play.tile_x}, {play.tile_y}).",
        )
    return card


@dataclass(frozen=True)
class PlayResult:
    """A play the bot has tapped. It shows on the screen a few frames
    later."""

    card: Card
    play: Play
    # The frame it was checked against and tapped on.
    frame: int


@dataclass
class PlayRequest:
    play: Play
    # The frame the client decided on, if it said, and the oldest that
    # frame may be when the bot gets to it, in seconds.
    frame: int | None = None
    max_age: float = 1.0
    future: Future[PlayResult] = field(default_factory=Future)

    def reject(self, reason: Reason, message: str) -> None:
        self.future.set_exception(PlayRejected(reason, message))


class PlayRequests:
    """Plays asked for on other threads, waiting for the bot's thread.

    One at a time: a play asked for while another waits is refused as
    BUSY, rather than queued behind a play it might conflict with.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._waiting: PlayRequest | None = None

    def submit(self, request: PlayRequest) -> Future[PlayResult]:
        with self._lock:
            waiting = self._waiting
            if waiting is not None and not waiting.future.done():
                raise PlayRejected(
                    Reason.BUSY, "Another play is waiting to be made."
                )
            self._waiting = request
        return request.future

    def take(self) -> PlayRequest | None:
        """The waiting request, now the caller's to answer. None if there's
        none, or the client gave up on it."""
        with self._lock:
            request, self._waiting = self._waiting, None
        if (
            request is None
            or not request.future.set_running_or_notify_cancel()
        ):
            return None
        return request

    def reject_waiting(self, reason: Reason, message: str) -> None:
        request = self.take()
        if request is not None:
            request.reject(reason, message)
