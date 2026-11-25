import numpy as np

from clashroyalebuildabot.constants.screenshot import (
    BATTLE_CHECK_BOX,
    SCREENSHOT_HEIGHT,
    SCREENSHOT_WIDTH,
)
from clashroyalebuildabot.detectors.battle_check import (
    REFERENCE_PATH,
    BattleCheck,
)
from clashroyalebuildabot.utils.image import load, resize


def frame(fill=(0, 0, 0)):
    return np.full((SCREENSHOT_HEIGHT, SCREENSHOT_WIDTH, 3), fill, np.uint8)


def frame_with_elixir_drop():
    image = frame()
    left, top, right, bottom = BATTLE_CHECK_BOX
    image[top:bottom, left:right] = resize(
        load(REFERENCE_PATH), (right - left, bottom - top)
    )
    return image


def test_sees_the_elixir_drop():
    assert BattleCheck().run(frame_with_elixir_drop())


def test_rejects_a_frame_without_it():
    check = BattleCheck()
    assert not check.run(frame())
    assert not check.run(frame((255, 255, 255)))
    # The blue OK button of the results screen.
    assert not check.run(frame((60, 140, 230)))


def test_rejects_noise():
    rng = np.random.default_rng(0)
    pixels = rng.integers(
        0, 256, (SCREENSHOT_HEIGHT, SCREENSHOT_WIDTH, 3), dtype=np.uint8
    )
    assert not BattleCheck().run(pixels)
