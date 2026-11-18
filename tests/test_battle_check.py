import numpy as np
from PIL import Image

from clashroyalebuildabot.constants.screenshot import (
    BATTLE_CHECK_BOX,
    SCREENSHOT_HEIGHT,
    SCREENSHOT_WIDTH,
)
from clashroyalebuildabot.detectors.battle_check import (
    REFERENCE_PATH,
    BattleCheck,
)


def frame(fill=(0, 0, 0)):
    return Image.new("RGB", (SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT), fill)


def frame_with_elixir_drop():
    image = frame()
    left, top, right, bottom = BATTLE_CHECK_BOX
    drop = Image.open(REFERENCE_PATH).resize((right - left, bottom - top))
    image.paste(drop, (left, top))
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
    assert not BattleCheck().run(Image.fromarray(pixels))
