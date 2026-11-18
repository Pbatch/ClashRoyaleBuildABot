import threading

import pytest
from PIL import Image
from pydantic import ValidationError

from clashroyalebuildabot.detectors.screen_detector import (
    OFFERED_SCREENS,
    ScreenAnswer,
    ScreenDetector,
)
from clashroyalebuildabot.detectors.vlm_client import VisionError, VLMClient
from clashroyalebuildabot.game import ScreenName, Screens
from clashroyalebuildabot.utils.error_handling import WikifiedError
from tests.conftest import default_config


class FakeClient:
    def __init__(self, screen="lobby", ok_button="none", error=None):
        self.answer = ScreenAnswer(screen=screen, ok_button=ok_button)
        self.error = error
        self.calls = 0
        self.release = threading.Event()
        self.release.set()

    def ask(self, image, prompt, schema):
        self.calls += 1
        self.release.wait(5)
        if self.error:
            raise self.error
        assert schema is ScreenAnswer
        return self.answer


def frame():
    return Image.new("RGB", (368, 652), (40, 40, 40))


def test_schema_offers_every_described_screen():
    schema = ScreenAnswer.model_json_schema()
    names = [screen.name for screen in OFFERED_SCREENS]
    assert schema["properties"]["screen"]["enum"] == names
    # The two results layouts are told apart by the OK button instead.
    assert ScreenName.BYPASS_END_OF_GAME not in names


def test_schema_rejects_an_unknown_screen():
    with pytest.raises(ValidationError):
        ScreenAnswer(screen="shop", ok_button="none")


@pytest.mark.parametrize(
    "screen",
    [
        ScreenName.IN_GAME,
        ScreenName.LOBBY,
        ScreenName.SEARCHING_FOR_OPPONENT,
        ScreenName.LOADING,
        ScreenName.VS,
        ScreenName.MATCH_OVER,
        ScreenName.UNKNOWN,
    ],
)
def test_answer_is_the_named_screen(screen):
    detector = ScreenDetector(FakeClient(screen))
    assert detector.classify(frame()) == screen


@pytest.mark.parametrize(
    "ok_button, expected",
    [
        ("right", ScreenName.END_OF_GAME),
        ("centre", ScreenName.BYPASS_END_OF_GAME),
        # Results still appearing: wait rather than tap blind.
        ("none", ScreenName.UNKNOWN),
    ],
)
def test_ok_button_position_picks_end_of_game_layout(ok_button, expected):
    detector = ScreenDetector(FakeClient("end_of_game", ok_button))
    assert detector.classify(frame()) == expected


def test_failed_request_is_unknown():
    detector = ScreenDetector(FakeClient(error=VisionError("refused")))
    assert detector.classify(frame()) == ScreenName.UNKNOWN


def test_run_does_not_block_and_reports_result_later():
    client = FakeClient()
    client.release.clear()
    detector = ScreenDetector(client, interval=0)

    # The model is still thinking, so there is no answer yet.
    assert detector.run(frame()) == ScreenName.UNKNOWN
    # A frame arriving while a request is in flight doesn't queue another.
    detector.run(frame())
    assert client.calls == 1

    client.release.set()
    detector.wait(5)
    assert detector.run(frame()) == ScreenName.LOBBY
    detector.close()


def test_run_respects_interval():
    client = FakeClient()
    detector = ScreenDetector(client, interval=60)
    detector.run(frame())
    detector.wait(5)
    detector.run(frame())
    assert client.calls == 1
    detector.close()


def test_stale_answer_becomes_unknown():
    detector = ScreenDetector(FakeClient(), interval=60, max_age=0)
    detector.run(frame())
    detector.wait(5)
    assert detector.run(frame()) == ScreenName.UNKNOWN
    detector.close()


def test_from_config_checks_server(monkeypatch):
    def down(self):
        raise WikifiedError("010", "down")

    monkeypatch.setattr(VLMClient, "check", down)
    with pytest.raises(WikifiedError):
        ScreenDetector.from_config(
            default_config().screen_detector.model_copy(
                update={"base_url": "http://nowhere:1"}
            )
        )


def test_prompt_lists_each_screen_by_name():
    from clashroyalebuildabot.detectors.screen_detector import PROMPT

    for screen in OFFERED_SCREENS:
        assert f"- {screen.name}: " in PROMPT
    assert "Screen(" not in PROMPT


def test_every_screen_name_has_details():
    assert {screen.name for screen in Screens.all()} == set(ScreenName)
