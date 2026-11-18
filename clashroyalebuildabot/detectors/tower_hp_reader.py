"""Read every tower's health and level with a small vision model.

Each tower's health bar has its exact HP written on it, with the tower's
level on a badge to its left. A crop of each bar is sent to the same model
the screen detector uses, and its answer is constrained to a schema of two
whole numbers.

Princess and king towers are asked differently, because "no health bar"
means opposite things for them: a princess tower without one is rubble,
while a king tower without one is untouched (it shows only its badge until
it's first hit). If a king tower falls, the battle is over.

All six towers are read in parallel, in the background, at most once per
``interval`` seconds. Until a tower's first reading, its HP is
``UNKNOWN_HP``: treated as standing, never as destroyed.
"""

import dataclasses
from concurrent.futures import ThreadPoolExecutor

from loguru import logger
from PIL import Image
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass

from clashroyalebuildabot.constants.screenshot import (
    KING_TOWER_BOXES,
    PRINCESS_TOWER_BOXES,
)
from clashroyalebuildabot.detectors.background import LatestResult
from clashroyalebuildabot.detectors.vlm_client import VisionClient, VisionError
from clashroyalebuildabot.game.numbers import (
    UNKNOWN_HP,
    Tower,
    Towers,
)

# Crops are enlarged before they're sent, so the digits are easy to read.
CROP_SCALE = 4


class TowerReading(BaseModel):
    # Level comes first: asked the other way round, the model read rubble
    # as 100 HP.
    level: int = Field(
        ge=0,
        le=16,
        description="the tower's level: the number on the small yellow badge "
        "to the left of the health bar; 0 if the tower is rubble",
    )
    hp: int = Field(
        ge=0,
        le=9999,
        description="the number written on the tower's health bar; "
        "0 if the tower is rubble",
    )


class KingReading(BaseModel):
    level: int = Field(
        ge=1,
        le=16,
        description="the number on the king tower's small yellow crown badge",
    )
    hp: int = Field(
        ge=0,
        le=9999,
        description="the number written on the king tower's health bar; "
        "0 if there is no health bar",
    )


PRINCESS_PROMPT = (
    "This crop shows a tower's health bar from the game Clash Royale, or "
    "the rubble of a destroyed tower. Answer in JSON with `level`: the "
    "number on the small yellow level badge to the left of the bar, and "
    "`hp`: the number written on the health bar. Use 0 for both if the "
    "tower is rubble."
)
KING_PROMPT = (
    "This crop shows a king tower's level badge from the game Clash Royale, "
    "and its health bar if it has one. An undamaged king tower shows only "
    "its badge, with no health bar. Answer in JSON with `level`: the number "
    "on the small yellow crown badge, and `hp`: the number written on the "
    "health bar, or 0 if there is no health bar."
)


@dataclass(frozen=True)
class _TowerKind:
    schema: type[TowerReading] | type[KingReading]
    prompt: str
    # What an answer of 0 HP means for this kind of tower.
    zero_hp: float
    # Whether the badge (and so the level) is still there at 0 HP.
    level_at_zero_hp: bool


PRINCESS = _TowerKind(TowerReading, PRINCESS_PROMPT, 0, False)
KING = _TowerKind(KingReading, KING_PROMPT, UNKNOWN_HP, True)

TOWERS = [(name, box, PRINCESS) for name, box in PRINCESS_TOWER_BOXES.items()]
TOWERS += [(name, box, KING) for name, box in KING_TOWER_BOXES.items()]


class TowerHPReader:
    def __init__(self, client: VisionClient, interval=1.0):
        self.client = client
        self._pool = ThreadPoolExecutor(
            max_workers=len(TOWERS), thread_name_prefix="tower-hp"
        )
        # HP only changes during a battle, so the last reading stays valid
        # until reset() at the end of it.
        self._latest = LatestResult(
            self.read,
            default=Towers(),
            interval=interval,
            max_age=None,
            name="tower-hp-reader",
        )

    def _read_one(
        self, image: Image.Image, bbox, kind: _TowerKind
    ) -> TowerReading | KingReading | None:
        left, top, right, bottom = bbox
        crop = image.crop(bbox).resize(
            ((right - left) * CROP_SCALE, (bottom - top) * CROP_SCALE),
            Image.Resampling.LANCZOS,
        )
        try:
            return self.client.ask(crop, kind.prompt, kind.schema)
        except VisionError as e:
            logger.warning(f"Tower reading failed: {e}")
            return None

    def read(self, image: Image.Image) -> Towers:
        """Blocking reading of all six towers.

        A tower whose reading fails keeps its previous values. A destroyed
        princess tower keeps its last level: its badge is gone, and a level
        never changes during a battle.
        """
        previous = self._latest.latest()
        answers = self._pool.map(
            lambda tower: self._read_one(image, tower[1], tower[2]), TOWERS
        )
        changes = {}
        for (name, _, kind), answer in zip(TOWERS, answers, strict=True):
            if answer is None:
                continue
            hp = answer.hp if answer.hp > 0 else kind.zero_hp
            level = (
                answer.level
                if answer.hp > 0 or kind.level_at_zero_hp
                else getattr(previous, name).level
            )
            changes[name] = Tower(hp=hp, level=level)
        return dataclasses.replace(previous, **changes)

    def run(self, image: Image.Image) -> Towers:
        """Return the latest readings, refreshing them in the background."""
        return self._latest.run(image)

    def latest(self) -> Towers:
        """The latest readings, without asking for new ones."""
        return self._latest.latest()

    def reset(self):
        """Forget the readings, ready for the next battle."""
        self._latest.reset()

    def wait(self, timeout: float | None = None):
        self._latest.wait(timeout)

    def close(self):
        self._latest.close()
        self._pool.shutdown(wait=False, cancel_futures=True)
