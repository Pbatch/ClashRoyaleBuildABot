"""Read every tower's health, on every frame.

Each tower's health bar has its exact HP written on it, in the game's own
font, which a small CNN reads (see digit_model): all six towers in one
batch, in a few milliseconds.

Levels come from the HP, not the badges: a side's three towers share a
level, and a princess tower's first reading is its full HP, which only one
level has (game_data.tower_level). Both princess towers must agree, as a
tower already hit when the bot starts could happen to show another level's
full HP. Once a side's level is known, so is its untouched king tower's HP:
full, for that level. Until then, levels stay ``UNKNOWN_LEVEL``.

A number that can't be read doesn't mean much on its own: "Elixir!" and
other pop-ups often cover it for a moment. So:

- A king tower without a number keeps its last reading. Until it's first
  hit it shows only its badge, so it's at full HP, or ``UNKNOWN_HP``
  (standing) while its level isn't known; once hit, its bar never goes
  away. If a king tower falls, the battle is over.
  A number is only taken while its bar's colour is there: before then, the
  badge's level, or a troop's level badge or a damage number passing over
  it, would otherwise read as its HP.
- A princess tower without a number keeps its last reading while its health
  bar's colour is still there. With neither number nor bar for
  ``RUBBLE_SECONDS``, it's rubble: 0 HP, for the rest of the battle. That's
  measured in seconds, not frames, so a pop-up over the bar for a few
  frames doesn't topple a tower, however fast frames come.

Until a tower's first reading, its HP is ``UNKNOWN_HP``: treated as
standing, never as destroyed.
"""

import dataclasses
import os
import time
from collections.abc import Callable

import numpy as np

from clashroyalebuildabot.constants.paths import MODELS_DIR
from clashroyalebuildabot.constants.screenshot import (
    KING_TOWER_BOXES,
    PRINCESS_TOWER_BOXES,
)
from clashroyalebuildabot.detectors import digit_model
from clashroyalebuildabot.game import game_data
from clashroyalebuildabot.game.towers import (
    UNKNOWN_HP,
    UNKNOWN_LEVEL,
    Tower,
    Towers,
)
from clashroyalebuildabot.utils.image import crop

TOWER_BOXES = {**PRINCESS_TOWER_BOXES, **KING_TOWER_BOXES}
MODEL_PATH = os.path.join(MODELS_DIR, "tower_hp_digits.onnx")
# Seconds with no number and no bar before a princess tower counts as
# destroyed. Pop-ups that hide a bar are gone within this.
RUBBLE_SECONDS = 2.0
# The share of a princess tower's box in its bar's colour above which the
# bar is still there. Rubble is at or near 0; a bar is at 0.04 to 0.1, and
# the bars pop-ups cover are too. A bar under about 200 HP is barely
# coloured and falls below it, but then it only counts as rubble if its
# number is unreadable for RUBBLE_SECONDS too, and it's about to fall.
BAR_SHARE = 0.03
# Each side's towers, king last.
SIDES = [
    (f"left_{side}_princess", f"right_{side}_princess", f"{side}_king")
    for side in ("enemy", "ally")
]


def bar_share(image: np.ndarray, enemy: bool) -> float:
    """The share of a crop in a health bar's fill colour: pink for the
    enemy's towers, blue for ours."""
    r, g, b = (image[..., i].astype(np.int16) for i in range(3))
    if enemy:
        bar = (r > 170) & (g < 110) & (b > 60) & (b < 170) & (r - b > 60)
    else:
        bar = (b > 190) & (r < 130) & (g > 110) & (b - r > 90)
    return float(bar.mean())


class TowerHPReader:
    def __init__(
        self,
        model_path: str = MODEL_PATH,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._model = digit_model.load(model_path)
        self._clock = clock
        self.reset()

    def latest(self) -> Towers:
        """The latest readings, without reading a frame."""
        return self._towers

    def reset(self) -> None:
        """Forget the readings, ready for the next battle."""
        self._towers = Towers()
        # Per princess tower, since when it has shown neither number nor
        # bar, or None while it shows either.
        self._unseen_since: dict[str, float | None] = dict.fromkeys(
            PRINCESS_TOWER_BOXES
        )
        # Per princess tower, its first reading: full HP, unless the bot
        # started once it was already hit.
        self._first_hp: dict[str, float] = {}

    def run(self, image: np.ndarray) -> Towers:
        """Read all six towers in this frame, in one batch, and return
        every tower's HP."""
        now = self._clock()
        crops = {name: crop(image, box) for name, box in TOWER_BOXES.items()}
        hps = self._model.read(list(crops.values()))
        changes = {}
        for (name, tower), hp in zip(crops.items(), hps, strict=True):
            last = getattr(self._towers, name)
            princess = name in self._unseen_since
            if princess and last.hp == 0:
                continue  # rubble doesn't come back
            bar = bar_share(tower, "enemy" in name) >= BAR_SHARE
            if not princess:
                if hp is not None and bar:
                    changes[name] = Tower(hp=hp, level=last.level)
                continue
            if hp is not None:
                changes[name] = Tower(hp=hp, level=last.level)
                self._first_hp.setdefault(name, hp)
            if hp is not None or bar:
                self._unseen_since[name] = None
                continue
            since = self._unseen_since[name]
            if since is None:
                self._unseen_since[name] = since = now
            if now - since >= RUBBLE_SECONDS:
                changes[name] = Tower(hp=0, level=last.level)
        self._towers = self._with_levels(
            dataclasses.replace(self._towers, **changes)
        )
        return self._towers

    def _with_levels(self, towers: Towers) -> Towers:
        """Give each side whose level isn't known yet the level both its
        princess towers' first readings show, and its untouched king tower
        full HP for it."""
        changes = {}
        for *princesses, king in SIDES:
            if getattr(towers, king).level != UNKNOWN_LEVEL:
                continue
            levels = {
                game_data.tower_level(self._first_hp.get(name, UNKNOWN_HP))
                for name in princesses
            }
            if len(levels) != 1 or None in levels:
                continue
            (level,) = levels
            for name in (*princesses, king):
                changes[name] = Tower(hp=getattr(towers, name).hp, level=level)
            full = game_data.king_hitpoints(level)
            if getattr(towers, king).hp == UNKNOWN_HP and full is not None:
                changes[king] = Tower(hp=full, level=level)
        return dataclasses.replace(towers, **changes)
