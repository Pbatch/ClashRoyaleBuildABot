"""Follow the units the detector finds from one frame to the next.

The detector reads each frame on its own, so a unit it misses for a frame
leaves the state, one it names wrongly for a frame changes name, and one it
puts on the wrong side for a frame changes sides. The tracker matches each
frame's detections, ours and the opponent's together, to the units it
already follows, and reports those instead: a unit stays through a short
dropout (moved on at its speed), and is reported once it's been seen twice,
or at once if the detector is sure of it.

Each track sums the model's scores for every unit, on both sides, on its
tile over the frames it was detected. Its side and name come from those
sums (Track.best_side and Track.best_unit), not from what one frame said.
"""

import math
from collections.abc import Collection, Iterable, Sequence
from dataclasses import InitVar, dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from scipy.optimize import linear_sum_assignment

from clashroyalebuildabot.game.units import (
    Position,
    Unit,
    UnitCategory,
    UnitDetection,
)

if TYPE_CHECKING:
    from clashroyalebuildabot.detectors.opponent_deck import OpponentDeck

COLS, ROWS = 18, 32
ALLY, ENEMY = 0, 1  # the rows of ScoredDetection.scores


@dataclass(frozen=True, eq=False)
class ScoredDetection(UnitDetection):
    """A detection with the model's scores for every unit, on both sides, on
    its tile, before it was named (UnitDetector.decode), so a track can
    weigh every unit it might be, not only the one each frame named."""

    scores: np.ndarray  # [2, len(units)]: ALLY and ENEMY rows, each 0 to 1
    units: Sequence[Unit]  # the unit each score is for


@dataclass
class Track:
    """One unit followed over frames, in tile coordinates (the bot's: x from
    the left, y up from the bottom)."""

    id: int
    x: float
    y: float
    seen: float  # when it was last detected
    conf: float  # the detector's confidence, averaged over frames
    det: InitVar[ScoredDetection]  # its first detection
    # How sure the model was of each side, [ALLY, ENEMY], summed over every
    # frame without fading: a unit never changes sides.
    side_votes: list[float] = field(default_factory=lambda: [0.0, 0.0])
    vx: float = 0.0  # tiles per second
    vy: float = 0.0
    hits: int = 1
    born: float = 0.0  # when it was first detected
    # The model's [2, units] scores for every unit on both sides on the
    # track's tile (ScoredDetection), summed over the frames it was
    # detected: with each older frame counting SCORE_FADE times the one
    # after it, and in full.
    scores: np.ndarray = field(init=False)
    total_scores: np.ndarray = field(init=False)
    units: Sequence[Unit] = field(init=False)  # the unit each score is for

    # How much each older frame's scores count against the frame after it,
    # when newer frames count more.
    SCORE_FADE = 0.9

    def __post_init__(self, det: ScoredDetection) -> None:
        self.units = det.units
        self.scores = det.scores.astype(np.float64)
        self.total_scores = det.scores.astype(np.float64)
        self._count_sides(det.scores)

    @property
    def unit(self) -> Unit:
        """The unit it most likely is, lately, with no unit favoured."""
        return self.best_unit()

    @property
    def ally(self) -> bool:
        """Whether it's ours, as best_side says."""
        return self.best_side() == ALLY

    def record(self, det: ScoredDetection) -> None:
        """Count one more frame's detection in its scores."""
        self.scores = self.SCORE_FADE * self.scores + det.scores
        self.total_scores += det.scores
        self._count_sides(det.scores)

    def _count_sides(self, scores: np.ndarray) -> None:
        # Both sides' evidence, not only the side this frame chose.
        self.side_votes[ALLY] += float(scores[ALLY].max())
        self.side_votes[ENEMY] += float(scores[ENEMY].max())

    def best_side(self) -> int:
        """ALLY or ENEMY: the side the model has rated it on most, over
        every frame, counting how sure it was of each side in each."""
        if self.side_votes[ALLY] >= self.side_votes[ENEMY]:
            return ALLY
        return ENEMY

    def best_unit(
        self,
        side: int | None = None,
        favoured: Collection[Unit] = (),
        others: float = 1.0,
        recent: bool = True,
    ) -> Unit:
        """The unit it most likely is, from the model's scores for side
        (best_side if None) over every frame it was detected: newer frames
        counting more if recent, else all alike.

        favoured units count in full, and the rest at others times their
        score (0: never chosen), as UnitDetector does for one frame.
        Without favoured units, or when nothing it could be has any
        score, every unit counts in full."""
        summed = self.scores if recent else self.total_scores
        if side is None:
            side = self.best_side()
        rated = summed[side]
        if favoured:
            weight = np.array(
                [1.0 if u in favoured else others for u in self.units]
            )
            if (weight * rated).any():
                rated = rated * weight
        return self.units[int(np.argmax(rated))]

    def detection(self, unit: Unit) -> UnitDetection:
        """It as a detection, as unit."""
        position = Position(
            self.conf,
            min(max(round(self.x), 0), COLS - 1),
            min(max(round(self.y), 0), ROWS - 1),
        )
        return UnitDetection(unit, position)


class Tracker:
    """Tracks units across frames, ours and the opponent's together."""

    # Furthest a detection can be from where a unit is expected, in tiles.
    # The fastest units walk about 2 tiles a second.
    GATE = 2.5
    # The extra cost, in tiles, of matching a detection to a unit seen as
    # another one: a wrong name for a frame stays the same unit.
    RENAME_COST = 1.0
    # The extra cost of matching a detection to a unit seen on the other
    # side: a wrong side for a frame stays the same unit, but only when
    # it's close, so two units fighting each other aren't swapped.
    SIDE_COST = 2.0
    # How long a unit is kept, moved on at its speed, once it's no longer
    # detected, in seconds. Short, as a unit that died must not stay.
    MAX_COAST = 0.6
    # How much of the newest frame goes into the position, speed and
    # confidence (the rest is what came before).
    POSITION_WEIGHT = 0.7
    SPEED_WEIGHT = 0.4
    CONF_WEIGHT = 0.5
    # No unit is faster than this, in tiles per second.
    MAX_SPEED = 3.0

    def __init__(self) -> None:
        self.tracks: list[Track] = []
        self._next_id = 0
        self._last: float | None = None

    def reset(self) -> None:
        self.tracks = []
        self._last = None

    def step(
        self,
        detections: Sequence[ScoredDetection],
        sides: Sequence[int],
        now: float,
    ) -> None:
        """Follow this frame's detections, each on the side (ALLY or
        ENEMY) at its index in sides, at time now (seconds)."""
        dt = 0.0 if self._last is None else max(now - self._last, 0.0)
        self._last = now
        if dt > self.MAX_COAST:
            # No frames for longer than a unit is kept for (a pause): what
            # comes up where a unit was is a new one.
            self.tracks = []
        for track in self.tracks:
            track.x += track.vx * dt
            track.y += track.vy * dt

        matched_tracks: set[int] = set()
        matched_dets: set[int] = set()
        if self.tracks and detections:
            cost = self._costs(detections, sides)
            for t, d in zip(*linear_sum_assignment(cost), strict=True):
                if cost[t, d] < self.GATE + self.RENAME_COST:
                    self._match(self.tracks[t], detections[d], now)
                    matched_tracks.add(t)
                    matched_dets.add(d)

        self.tracks = [
            track
            for i, track in enumerate(self.tracks)
            if i in matched_tracks or now - track.seen <= self.MAX_COAST
        ]
        for i, det in enumerate(detections):
            if i not in matched_dets:
                self.tracks.append(self._new_track(det, now))

    def _costs(
        self, detections: Sequence[ScoredDetection], sides: Sequence[int]
    ) -> np.ndarray:
        """Each unit's cost of each detection: how far it is from where the
        unit is expected, more if named another unit or on the other side;
        an impossible match (out of reach) costs a lot."""
        impossible = 1e6
        cost = np.full((len(self.tracks), len(detections)), impossible)
        for t, track in enumerate(self.tracks):
            unit, side = track.unit, track.best_side()
            for d, det in enumerate(detections):
                distance = math.hypot(
                    det.position.tile_x - track.x,
                    det.position.tile_y - track.y,
                )
                if distance > self.GATE:
                    continue
                cost[t, d] = (
                    distance
                    + self.RENAME_COST * (det.unit != unit)
                    + self.SIDE_COST * (sides[d] != side)
                )
        return cost

    def _match(self, track: Track, det: ScoredDetection, now: float) -> None:
        x, y = det.position.tile_x, det.position.tile_y
        old_x, old_y = track.x, track.y
        track.x += self.POSITION_WEIGHT * (x - track.x)
        track.y += self.POSITION_WEIGHT * (y - track.y)
        since_seen = now - track.seen
        if since_seen > 0:
            # The speed from where it was expected to where it's seen,
            # added to the speed it was moving at.
            track.vx = self._clamp(
                track.vx + self.SPEED_WEIGHT * (x - old_x) / since_seen
            )
            track.vy = self._clamp(
                track.vy + self.SPEED_WEIGHT * (y - old_y) / since_seen
            )
        track.record(det)
        if track.unit.category == UnitCategory.BUILDING:
            track.vx = track.vy = 0.0
        track.conf += self.CONF_WEIGHT * (det.position.conf - track.conf)
        track.seen = now
        track.hits += 1

    def _clamp(self, speed: float) -> float:
        return min(max(speed, -self.MAX_SPEED), self.MAX_SPEED)

    def _new_track(self, det: ScoredDetection, now: float) -> Track:
        self._next_id += 1
        return Track(
            id=self._next_id,
            x=det.position.tile_x,
            y=det.position.tile_y,
            seen=now,
            born=now,
            conf=det.position.conf,
            det=det,
        )


class UnitTracker:
    """Tracks our units and the opponent's, and names them. Call ``reset``
    between battles.

    A unit is reported on the side it's been rated on most, and
    named from its scores over its frames (Track.best_unit): ours only from
    our deck's units, the opponent's in favour of their known cards'
    units (OpponentDeck.favour)."""

    # A unit is reported once it's been detected this many times, or at
    # once if detected this sure (the detector's MIN_CONF).
    CONFIRM_HITS = 2
    INSTANT_CONF = 0.7

    def __init__(self, ally_units: Iterable[Unit]) -> None:
        self.ally_units = frozenset(ally_units)
        self.tracker = Tracker()

    @property
    def tracks(self) -> list[Track]:
        return self.tracker.tracks

    def reset(self) -> None:
        self.tracker.reset()

    def update(
        self,
        allies: Sequence[ScoredDetection],
        enemies: Sequence[ScoredDetection],
        now: float,
        opponent: "OpponentDeck",
    ) -> tuple[list[UnitDetection], list[UnitDetection]]:
        """(allies, enemies) followed after this frame's detections at time
        now (seconds), the opponent's named in favour of their cards seen
        so far."""
        self.tracker.step(
            [*allies, *enemies],
            [ALLY] * len(allies) + [ENEMY] * len(enemies),
            now,
        )
        favoured, others = opponent.favour()
        out_allies: list[UnitDetection] = []
        out_enemies: list[UnitDetection] = []
        for track in self.tracks:
            if not self._reported(track):
                continue
            if track.ally:
                unit = track.best_unit(ALLY, self.ally_units, 0.0)
                out_allies.append(track.detection(unit))
            else:
                unit = track.best_unit(ENEMY, favoured, others)
                out_enemies.append(track.detection(unit))
        return out_allies, out_enemies

    def _reported(self, track: Track) -> bool:
        # Until it's matched, a track's conf is its first detection's.
        return (
            track.hits >= self.CONFIRM_HITS or track.conf >= self.INSTANT_CONF
        )
