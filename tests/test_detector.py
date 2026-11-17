import time

import pytest
from loguru import logger

import clashroyalebuildabot.detectors.detector as detector_module
from clashroyalebuildabot.namespaces import Screens, State
from clashroyalebuildabot.namespaces.cards import Cards

DECK = [
    Cards.ARCHERS,
    Cards.BABY_DRAGON,
    Cards.CANNON,
    Cards.GOBLIN_BARREL,
    Cards.KNIGHT,
    Cards.MINIPEKKA,
    Cards.MUSKETEER,
    Cards.WITCH,
]


class FakeSubDetector:
    def __init__(self, *args, result=None, **kwargs):
        self.result = result
        self.calls = 0
        self.error = None

    def run(self, image):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.result

    def close(self):
        pass


@pytest.fixture
def detector(monkeypatch):
    monkeypatch.setattr(
        detector_module,
        "CardDetector",
        lambda cards: FakeSubDetector(result=(list(cards[:5]), [0, 1])),
    )
    monkeypatch.setattr(
        detector_module,
        "UnitDetector",
        lambda path, cards: FakeSubDetector(result=([], [])),
    )
    monkeypatch.setattr(
        detector_module,
        "NumberDetector",
        lambda: FakeSubDetector(result="numbers"),
    )
    monkeypatch.setattr(
        detector_module.ScreenDetector,
        "from_config",
        classmethod(lambda cls, config: FakeSubDetector(result=Screens.LOBBY)),
    )
    return detector_module.Detector(DECK)


def test_returns_state(detector):
    state = detector.run(image=None)
    assert isinstance(state, State)
    assert state.screen == Screens.LOBBY
    assert state.ready == [0, 1]


def test_failure_returns_none_after_one_attempt(detector):
    detector.unit_detector.error = RuntimeError("model failed")
    messages = []
    sink = logger.add(lambda m: messages.append(m.record["message"]))
    try:
        start = time.monotonic()
        assert detector.run(image=None) is None
        elapsed = time.monotonic() - start
    finally:
        logger.remove(sink)

    assert detector.unit_detector.calls == 1  # no retries
    assert elapsed < 0.5  # no sleeping between attempts
    assert any("Detection failed" in m for m in messages)


def test_keeps_the_given_cards_without_copying(detector):
    assert detector.cards is DECK


def test_rejects_wrong_deck_size(monkeypatch):
    with pytest.raises(
        detector_module.WikifiedError, match="must have 8 cards, but 7"
    ):
        detector_module.Detector(DECK[:7])
