import threading

import pytest
import requests
from PIL import Image

from clashroyalebuildabot.detectors.screen_detector import (
    OK_CRITERIA,
    SCREEN_CRITERIA,
    OneJevClient,
    ScreenDetector,
)
from clashroyalebuildabot.namespaces import Screens
from clashroyalebuildabot.utils.error_handling import WikifiedError


def answers(screen, ok=None):
    return {"screen": screen, "ok_button": ok or {"right": 0.5, "centre": 0.5}}


class FakeClient:
    def __init__(self, reply=None, error=None):
        self.reply = reply or answers({"lobby": 0.9, "unknown": 0.1})
        self.error = error
        self.calls = 0
        self.release = threading.Event()
        self.release.set()

    def ask(self, image):
        self.calls += 1
        self.release.wait(5)
        if self.error:
            raise self.error
        return self.reply


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self.body


class FakeSession:
    def __init__(self, body=None, error=None):
        self.body = body
        self.error = error
        self.posts = []

    def get(self, url, timeout):
        if self.error:
            raise self.error
        return FakeResponse({})

    def post(self, url, json, timeout):
        self.posts.append((url, json))
        return FakeResponse(self.body)


def onejev(body=None, error=None):
    client = OneJevClient("http://flide:8000/")
    session = FakeSession(body, error)
    client.session = session  # ty: ignore[invalid-assignment]
    return client, session


def frame():
    return Image.new("RGB", (368, 652), (40, 40, 40))


def test_request_asks_both_questions():
    body = {
        "answers": {
            "screen": {"probabilities": {"lobby": 0.9, "in_game": 0.1}},
            "ok_button": {"probabilities": {"right": 0.3, "centre": 0.7}},
        }
    }
    client, session = onejev(body)
    assert client.ask(frame()) == {
        "screen": {"lobby": 0.9, "in_game": 0.1},
        "ok_button": {"right": 0.3, "centre": 0.7},
    }

    url, payload = session.posts[0]
    assert url == "http://flide:8000/v1/systemone"
    assert payload["state"]["screen"] == "<image:1>"
    assert payload["media"][0]["data"].startswith("data:image/png;base64,")
    questions = payload["questions"]
    assert questions["screen"]["criteria"] == SCREEN_CRITERIA
    assert questions["ok_button"]["criteria"] == OK_CRITERIA


def test_unreachable_server_raises_at_startup():
    client, _ = onejev(error=requests.ConnectionError("refused"))
    with pytest.raises(WikifiedError) as e:
        client.check()
    assert e.value.error_code == "010"


@pytest.mark.parametrize(
    "screen, expected",
    [
        ({"in_game": 0.8, "lobby": 0.1, "unknown": 0.1}, Screens.IN_GAME),
        ({"lobby": 0.92, "unknown": 0.08}, Screens.LOBBY),
        ({"unknown": 0.6, "lobby": 0.4}, Screens.UNKNOWN),
        ({"matchmaking": 0.8, "lobby": 0.2}, Screens.UNKNOWN),
        ({"loading": 0.7, "lobby": 0.3}, Screens.UNKNOWN),
        ({"vs": 0.9, "end_of_game": 0.1}, Screens.UNKNOWN),
        ({"match_over": 0.9, "end_of_game": 0.1}, Screens.UNKNOWN),
    ],
)
def test_most_likely_screen_wins(screen, expected):
    detector = ScreenDetector(FakeClient(answers(screen)))
    assert detector.classify(frame()) == expected


@pytest.mark.parametrize(
    "ok, expected",
    [
        ({"right": 0.8, "centre": 0.2}, Screens.END_OF_GAME),
        ({"right": 0.1, "centre": 0.9}, Screens.BYPASS_END_OF_GAME),
    ],
)
def test_ok_button_position_picks_end_of_game_layout(ok, expected):
    reply = answers({"end_of_game": 0.9, "unknown": 0.1}, ok)
    detector = ScreenDetector(FakeClient(reply))
    assert detector.classify(frame()) == expected


def test_low_confidence_is_unknown():
    reply = answers({"in_game": 0.4, "lobby": 0.35, "unknown": 0.25})
    detector = ScreenDetector(FakeClient(reply), min_confidence=0.5)
    assert detector.classify(frame()) == Screens.UNKNOWN


@pytest.mark.parametrize(
    "error", [requests.ConnectionError("refused"), KeyError("answers")]
)
def test_failed_request_is_unknown(error):
    detector = ScreenDetector(FakeClient(error=error))
    assert detector.classify(frame()) == Screens.UNKNOWN


def test_run_does_not_block_and_reports_result_later():
    client = FakeClient()
    client.release.clear()
    detector = ScreenDetector(client, interval=0)

    # The model is still thinking, so there is no answer yet.
    assert detector.run(frame()) == Screens.UNKNOWN
    # A frame arriving while a request is in flight doesn't queue another.
    detector.run(frame())
    assert client.calls == 1

    client.release.set()
    detector.wait(5)
    assert detector.run(frame()) == Screens.LOBBY
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
    assert detector.run(frame()) == Screens.UNKNOWN
    detector.close()


def test_from_config_checks_server(monkeypatch):
    monkeypatch.setattr(
        OneJevClient,
        "check",
        lambda self: (_ for _ in ()).throw(WikifiedError("010", "down")),
    )
    with pytest.raises(WikifiedError):
        ScreenDetector.from_config({"base_url": "http://nowhere:1"})
