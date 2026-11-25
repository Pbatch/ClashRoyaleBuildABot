import os

import numpy as np
import pytest

from clashroyalebuildabot.constants.screen_hashes import (
    BATTLE_DROP_HASH,
    BUTTON_HASHES,
)
from clashroyalebuildabot.constants.screenshot import (
    BATTLE_CHECK_BOX,
    LOBBY_BATTLE_BOX,
    RESULTS_CENTRE_OK_BOX,
    RESULTS_OK_BOX,
    RESULTS_PLAY_AGAIN_BOX,
)
from clashroyalebuildabot.detectors.screen_detector import (
    DROP_THUMBNAIL_SIZE,
    THUMBNAIL_SIZE,
    ScreenDetector,
)
from clashroyalebuildabot.game import ScreenName
from clashroyalebuildabot.utils.image import load, resize

DATA = os.path.join(os.path.dirname(__file__), "data", "screens")


def frame(*crops: tuple[str, tuple[int, int, int, int]]) -> np.ndarray:
    """A dark frame, with real crops of buttons pasted into boxes."""
    image = np.full((652, 368, 3), 30, np.uint8)
    for name, (left, top, right, bottom) in crops:
        image[top:bottom, left:right] = load(os.path.join(DATA, f"{name}.png"))
    return image


def with_elixir_drop(image: np.ndarray) -> np.ndarray:
    """The frame with the reference elixir drop, blown back up to the size
    of its box, pasted in."""
    width, height = DROP_THUMBNAIL_SIZE
    drop = np.frombuffer(bytes.fromhex(BATTLE_DROP_HASH), np.uint8)
    left, top, right, bottom = BATTLE_CHECK_BOX
    image[top:bottom, left:right] = resize(
        drop.reshape(height, width, 3), (right - left, bottom - top)
    )
    return image


@pytest.fixture
def detector():
    return ScreenDetector()


def test_battle(detector):
    assert detector.run(with_elixir_drop(frame())) == ScreenName.IN_GAME


def test_the_elixir_drop_wins_over_buttons(detector):
    # A battle is a battle, whatever else the frame looks like.
    image = with_elixir_drop(frame(("battle_button", LOBBY_BATTLE_BOX)))
    assert detector.run(image) == ScreenName.IN_GAME


@pytest.mark.parametrize("fill", [(0, 0, 0), (255, 255, 255), (60, 140, 230)])
def test_plain_frames_arent_a_battle(detector, fill):
    # The last is the blue of the results screen's OK button.
    image = np.full((652, 368, 3), fill, np.uint8)
    assert not detector.in_battle(image)


def test_noise_isnt_a_battle(detector):
    rng = np.random.default_rng(0)
    image = rng.integers(0, 256, (652, 368, 3), dtype=np.uint8)
    assert not detector.in_battle(image)


def test_lobby(detector):
    image = frame(("battle_button", LOBBY_BATTLE_BOX))
    assert detector.run(image) == ScreenName.LOBBY


def test_results_with_play_again_and_ok(detector):
    image = frame(
        ("play_again_button", RESULTS_PLAY_AGAIN_BOX),
        ("ok_button", RESULTS_OK_BOX),
    )
    assert detector.run(image) == ScreenName.END_OF_GAME


def test_results_with_only_an_ok_button_in_the_centre(detector):
    image = frame(("ok_button", RESULTS_CENTRE_OK_BOX))
    assert detector.run(image) == ScreenName.BYPASS_END_OF_GAME


def test_results_need_both_buttons(detector):
    # While the results appear, the buttons come in one at a time; tapping
    # before both are there would miss.
    image = frame(("ok_button", RESULTS_OK_BOX))
    assert detector.run(image) == ScreenName.UNKNOWN


def test_anything_else_is_unknown(detector):
    assert detector.run(frame()) == ScreenName.UNKNOWN


def test_a_blue_background_isnt_an_ok_button(detector):
    # The searching screen is blue where the OK button would be.
    image = frame(
        ("searching_ok_area", RESULTS_OK_BOX),
        ("play_again_button", RESULTS_PLAY_AGAIN_BOX),
    )
    assert detector.run(image) == ScreenName.UNKNOWN


def test_every_hash_is_a_whole_thumbnail():
    width, height = THUMBNAIL_SIZE
    for value in BUTTON_HASHES.values():
        assert len(bytes.fromhex(value)) == width * height * 3
    width, height = DROP_THUMBNAIL_SIZE
    assert len(bytes.fromhex(BATTLE_DROP_HASH)) == width * height * 3
