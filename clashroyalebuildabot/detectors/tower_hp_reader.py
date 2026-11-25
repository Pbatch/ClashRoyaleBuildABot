"""Read every tower's health.

Each tower's health bar has its exact HP written on it, in the game's own
font, which is matched digit by digit (see digit_reader). Tower levels
aren't read: they stay ``UNKNOWN_LEVEL``.

A number that can't be read doesn't mean much on its own: "Elixir!" and
other pop-ups often cover it for a moment. So:

- A king tower without a number keeps its last reading. Until it's first
  hit it shows only its badge, so it stays ``UNKNOWN_HP`` (standing); once
  hit, its bar never goes away. If a king tower falls, the battle is over.
- A princess tower without a number keeps its last reading while its health
  bar's colour is still there. With neither number nor bar for
  ``RUBBLE_READINGS`` readings in a row, it's rubble: 0 HP, for the rest of
  the battle.

All six towers are read in parallel, in the background, at most once per
``interval`` seconds. Until a tower's first reading, its HP is
``UNKNOWN_HP``: treated as standing, never as destroyed.
"""

import dataclasses
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

import numpy as np

from clashroyalebuildabot.constants.screenshot import (
    KING_TOWER_BOXES,
    PRINCESS_TOWER_BOXES,
)
from clashroyalebuildabot.detectors.background import BackgroundReader
from clashroyalebuildabot.detectors.digit_reader import read_number
from clashroyalebuildabot.game.numbers import Tower, Towers
from clashroyalebuildabot.utils.image import crop

TOWER_BOXES = {**PRINCESS_TOWER_BOXES, **KING_TOWER_BOXES}
# Readings in a row with no number and no bar before a princess tower
# counts as destroyed. Pop-ups that hide a bar are gone within this many.
RUBBLE_READINGS = 3
# The share of a princess tower's box in its bar's colour above which the
# bar is still there. Rubble is at or near 0; a bar is at 0.04 to 0.1, and
# the bars pop-ups cover are too. A bar under about 200 HP is barely
# coloured and falls below it, but then it only counts as rubble if its
# number is unreadable for RUBBLE_READINGS readings, and it's about to fall.
BAR_SHARE = 0.03


def bar_share(image: np.ndarray, enemy: bool) -> float:
    """The share of a crop in a health bar's fill colour: pink for the
    enemy's towers, blue for ours."""
    r, g, b = (image[..., i].astype(np.int16) for i in range(3))
    if enemy:
        bar = (r > 170) & (g < 110) & (b > 60) & (b < 170) & (r - b > 60)
    else:
        bar = (b > 190) & (r < 130) & (g > 110) & (b - r > 90)
    return float(bar.mean())


def _no_misses() -> dict[str, int]:
    return dict.fromkeys(PRINCESS_TOWER_BOXES, 0)


@dataclass(frozen=True)
class TowerReadings:
    towers: Towers = field(default_factory=Towers)
    # Per princess tower, readings in a row with no number and no bar.
    missing: Mapping[str, int] = field(default_factory=_no_misses)


def _read_one(image: np.ndarray, name: str) -> tuple[int | None, bool]:
    """(HP or None, whether the bar's colour shows)."""
    box = crop(image, TOWER_BOXES[name])
    hp = read_number(box)
    return hp, bar_share(box, "enemy" in name) >= BAR_SHARE


class TowerHPReader(BackgroundReader[TowerReadings, Towers]):
    def __init__(self, interval: float = 1.0) -> None:
        self._pool = ThreadPoolExecutor(
            max_workers=len(TOWER_BOXES), thread_name_prefix="tower-hp"
        )
        super().__init__(TowerReadings(), interval, name="tower-hp-reader")

    def read(
        self, image: np.ndarray, previous: TowerReadings
    ) -> TowerReadings:
        """All six towers, read in parallel."""
        names = list(TOWER_BOXES)
        readings = self._pool.map(lambda n: _read_one(image, n), names)
        changes = {}
        missing = dict(previous.missing)
        for name, (hp, bar) in zip(names, readings, strict=True):
            last = getattr(previous.towers, name)
            princess = name in missing
            if princess and last.hp == 0:
                continue  # rubble doesn't come back
            if hp is not None:
                changes[name] = Tower(hp=hp, level=last.level)
                if princess:
                    missing[name] = 0
            elif princess and not bar:
                missing[name] += 1
                if missing[name] >= RUBBLE_READINGS:
                    changes[name] = Tower(hp=0, level=last.level)
            elif princess:
                missing[name] = 0
        towers = dataclasses.replace(previous.towers, **changes)
        return TowerReadings(towers, missing)

    def output(self, state: TowerReadings) -> Towers:
        return state.towers

    def close(self) -> None:
        super().close()
        self._pool.shutdown(wait=False, cancel_futures=True)
