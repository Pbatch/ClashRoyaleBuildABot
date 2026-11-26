"""Follow the units the detector finds from one frame to the next.

The detector reads each frame on its own, so a unit it misses for a frame
leaves the state, and one it names wrongly for a frame changes name. The
tracker matches each frame's detections to the units it already follows,
and reports those instead: a unit stays through a short dropout (moved on
at its speed), keeps the name it has been seen as most, and is reported
once it's been seen twice, or at once if the detector is sure of it.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import linear_sum_assignment

from clashroyalebuildabot.game.units import (
    Position,
    Unit,
    UnitCategory,
    UnitDetection,
)

COLS, ROWS = 18, 32


@dataclass
class Track:
    """One unit followed over frames, in tile coordinates (the bot's: x from
    the left, y up from the bottom)."""

    id: int
    x: float
    y: float
    seen: float  # when it was last detected
    conf: float  # the detector's confidence, averaged over frames
    # The confidence summed per name it was detected as, fading so a name
    # it keeps being seen as takes over.
    votes: dict[Unit, float] = field(default_factory=dict)
    vx: float = 0.0  # tiles per second
    vy: float = 0.0
    hits: int = 1
    confirmed: bool = False

    @property
    def unit(self) -> Unit:
        return max(self.votes, key=self.votes.__getitem__)

    def detection(self) -> UnitDetection:
        position = Position(
            self.conf,
            min(max(round(self.x), 0), COLS - 1),
            min(max(round(self.y), 0), ROWS - 1),
        )
        return UnitDetection(self.unit, position)


class SideTracker:
    """Tracks the units of one side (ours or the opponent's)."""

    # Furthest a detection can be from where a unit is expected, in tiles.
    # The fastest units walk about 2 tiles a second.
    GATE = 2.5
    # The extra cost, in tiles, of matching a detection to a unit seen as
    # another one: a wrong name for a frame stays the same unit.
    RENAME_COST = 1.0
    # Reported at once if detected this sure (the detector's MIN_CONF), and
    # otherwise after this many detections.
    INSTANT_CONF = 0.7
    CONFIRM_HITS = 2
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
    # How much of each name's votes is kept at each detection.
    VOTE_FADE = 0.8

    def __init__(self) -> None:
        self.tracks: list[Track] = []
        self._next_id = 0
        self._last: float | None = None

    def reset(self) -> None:
        self.tracks = []
        self._last = None

    def update(
        self, detections: Sequence[UnitDetection], now: float
    ) -> list[UnitDetection]:
        """The units followed after this frame's detections, at time now
        (seconds)."""
        dt = 0.0 if self._last is None else max(now - self._last, 0.0)
        self._last = now
        for track in self.tracks:
            track.x += track.vx * dt
            track.y += track.vy * dt

        matched_tracks: set[int] = set()
        matched_dets: set[int] = set()
        if self.tracks and detections:
            cost = self._costs(detections)
            for t, d in zip(*linear_sum_assignment(cost), strict=True):
                if cost[t, d] < self.GATE + self.RENAME_COST:
                    self._match(self.tracks[t], detections[d], now, dt)
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
        return [track.detection() for track in self.tracks if track.confirmed]

    def _costs(self, detections: Sequence[UnitDetection]) -> np.ndarray:
        """Each unit's cost of each detection: how far it is from where the
        unit is expected, more if named another unit; an impossible match
        (out of reach) costs a lot."""
        impossible = 1e6
        cost = np.full((len(self.tracks), len(detections)), impossible)
        for t, track in enumerate(self.tracks):
            for d, det in enumerate(detections):
                distance = math.hypot(
                    det.position.tile_x - track.x,
                    det.position.tile_y - track.y,
                )
                if distance > self.GATE:
                    continue
                cost[t, d] = distance + (
                    self.RENAME_COST * (det.unit != track.unit)
                )
        return cost

    def _match(
        self, track: Track, det: UnitDetection, now: float, dt: float
    ) -> None:
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
        for unit in track.votes:
            track.votes[unit] *= self.VOTE_FADE
        conf = det.position.conf
        track.votes[det.unit] = track.votes.get(det.unit, 0.0) + conf
        if track.unit.category == UnitCategory.BUILDING:
            track.vx = track.vy = 0.0
        track.conf += self.CONF_WEIGHT * (conf - track.conf)
        track.seen = now
        track.hits += 1
        track.confirmed |= (
            track.hits >= self.CONFIRM_HITS or conf >= self.INSTANT_CONF
        )

    def _clamp(self, speed: float) -> float:
        return min(max(speed, -self.MAX_SPEED), self.MAX_SPEED)

    def _new_track(self, det: UnitDetection, now: float) -> Track:
        self._next_id += 1
        conf = det.position.conf
        return Track(
            id=self._next_id,
            x=det.position.tile_x,
            y=det.position.tile_y,
            seen=now,
            conf=conf,
            votes={det.unit: conf},
            confirmed=conf >= self.INSTANT_CONF,
        )


class UnitTracker:
    """Tracks our units and the opponent's, each side on its own. Call
    ``reset`` between battles."""

    def __init__(self) -> None:
        self.allies = SideTracker()
        self.enemies = SideTracker()

    def reset(self) -> None:
        self.allies.reset()
        self.enemies.reset()

    def update(
        self,
        allies: Sequence[UnitDetection],
        enemies: Sequence[UnitDetection],
        now: float,
    ) -> tuple[list[UnitDetection], list[UnitDetection]]:
        """(allies, enemies) followed after this frame's detections."""
        return (
            self.allies.update(allies, now),
            self.enemies.update(enemies, now),
        )
