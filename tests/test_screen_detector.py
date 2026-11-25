import os

import numpy as np
import pytest

from clashroyalebuildabot.constants.screen_hashes import BUTTON_HASHES
from clashroyalebuildabot.constants.screenshot import (
    LOBBY_BATTLE_BOX,
    RESULTS_CENTRE_OK_BOX,
    RESULTS_OK_BOX,
    RESULTS_PLAY_AGAIN_BOX,
    TIMER_BOX,
)
from clashroyalebuildabot.detectors.screen_detector import (
    THUMBNAIL_SIZE,
    ScreenDetector,
)
from clashroyalebuildabot.game import ScreenName
from clashroyalebuildabot.utils.image import load

TESTS = os.path.dirname(__file__)
DATA = os.path.join(TESTS, "data", "screens")
TIMER = os.path.join(TESTS, "data", "numbers", "timer_2_29.png")
# A real crop of the elixir number and bar, and where it goes.
ELIXIR = os.path.join(TESTS, "data", "elixir", "elixir_7.png")
ELIXIR_CROP_BOX = (100, 618, 360, 646)


def frame(*crops: tuple[str, tuple[int, int, int, int]]) -> np.ndarray:
    """A dark frame, with real crops of buttons pasted into boxes."""
    image = np.full((652, 368, 3), 30, np.uint8)
    for name, (left, top, right, bottom) in crops:
        image[top:bottom, left:right] = load(os.path.join(DATA, f"{name}.png"))
    return image


def paste(image: np.ndarray, path: str, box) -> np.ndarray:
    left, top, right, bottom = box
    image[top:bottom, left:right] = load(path)
    return image


def with_timer(image: np.ndarray) -> np.ndarray:
    return paste(image, TIMER, TIMER_BOX)


def with_elixir_bar(image: np.ndarray) -> np.ndarray:
    return paste(image, ELIXIR, ELIXIR_CROP_BOX)


def battle(image: np.ndarray) -> np.ndarray:
    """The frame with a battle's HUD: a timer and the elixir bar."""
    return with_elixir_bar(with_timer(image))


@pytest.fixture
def detector():
    return ScreenDetector()


def test_battle(detector):
    assert detector.run(battle(frame())) == ScreenName.IN_GAME


def test_a_battle_wins_over_buttons(detector):
    # A battle is a battle, whatever else the frame looks like.
    image = battle(frame(("battle_button", LOBBY_BATTLE_BOX)))
    assert detector.run(image) == ScreenName.IN_GAME


def test_a_frozen_timer_alone_isnt_a_battle(detector):
    # When a battle ends, the timer stays on screen through the crowns and
    # onto the results, but the card and elixir bars are gone.
    assert not detector.in_battle(with_timer(frame()))


def test_an_elixir_bar_alone_isnt_a_battle(detector):
    # Menus have pink of their own.
    assert not detector.in_battle(with_elixir_bar(frame()))


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
