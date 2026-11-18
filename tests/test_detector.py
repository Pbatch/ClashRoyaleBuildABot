import time

import pytest
from loguru import logger

import clashroyalebuildabot.detectors.detector as detector_module
from clashroyalebuildabot.game import ScreenName, State
from clashroyalebuildabot.game.cards import Cards
from clashroyalebuildabot.game.numbers import Timer, Tower, Towers
from tests.conftest import default_config

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


READ_TOWERS = Towers(left_enemy_princess=Tower(hp=1918, level=8))


class FakeTowerHPReader(FakeSubDetector):
    def __init__(self, *args, **kwargs):
        super().__init__(result=READ_TOWERS)
        self.resets = 0

    def latest(self):
        return Towers()

    def reset(self):
        self.resets += 1


READ_TIMER = Timer(time_left=117)


class FakeTimerReader(FakeSubDetector):
    def __init__(self, *args, **kwargs):
        super().__init__(result=READ_TIMER)
        self.resets = 0

    def latest(self):
        return Timer()

    def reset(self):
        self.resets += 1


class FakeCardDetector(FakeSubDetector):
    def __init__(self, cards):
        super().__init__(result=(list(cards[:5]), [0, 1]))
        self.resets = 0

    def reset(self):
        self.resets += 1


@pytest.fixture
def detector(monkeypatch):
    monkeypatch.setattr(detector_module, "CardDetector", FakeCardDetector)
    monkeypatch.setattr(
        detector_module,
        "UnitDetector",
        lambda path, cards: FakeSubDetector(result=([], [])),
    )
    monkeypatch.setattr(
        detector_module,
        "NumberDetector",
        lambda: FakeSubDetector(result=7),
    )
    monkeypatch.setattr(
        detector_module, "BattleCheck", lambda: FakeSubDetector(result=True)
    )
    monkeypatch.setattr(detector_module, "make_client", lambda config: None)
    monkeypatch.setattr(
        detector_module.ScreenDetector,
        "from_config",
        classmethod(
            lambda cls, config, client: FakeSubDetector(
                result=ScreenName.LOBBY
            )
        ),
    )
    monkeypatch.setattr(detector_module, "TowerHPReader", FakeTowerHPReader)
    monkeypatch.setattr(detector_module, "TimerReader", FakeTimerReader)
    return detector_module.Detector(DECK, default_config().screen_detector)


def test_returns_state_in_game(detector):
    detector.screen_detector.result = ScreenName.IN_GAME
    state = detector.run(image=None)
    assert isinstance(state, State)
    assert state.screen == ScreenName.IN_GAME
    assert state.cards == DECK[:5]
    assert state.ready == [0, 1]


def battle_detectors(detector):
    return (
        detector.card_detector,
        detector.unit_detector,
        detector.number_detector,
    )


def test_skips_battle_detectors_outside_a_battle(detector):
    state = detector.run(image=None)  # lobby
    assert state.screen == ScreenName.LOBBY
    assert [d.calls for d in battle_detectors(detector)] == [0, 0, 0]
    assert detector.battle_check.calls == 0
    assert (state.allies, state.enemies) == ([], [])
    assert (state.cards, state.ready) == ([], [])
    assert state.numbers.elixir == 0


def test_stale_in_game_answer_is_not_trusted(detector):
    # The screen detector still says in game, but the frame has no elixir
    # bar: the battle has just ended.
    detector.screen_detector.result = ScreenName.IN_GAME
    detector.battle_check.result = False
    state = detector.run(image=None)
    assert state.screen == ScreenName.UNKNOWN
    assert state.ready == []
    assert [d.calls for d in battle_detectors(detector)] == [0, 0, 0]
    assert detector.tower_hp_reader.calls == 0
    assert detector.timer_reader.calls == 0
    # A flicker mid-battle mustn't lose the tower and timer readings, or
    # the remembered hand.
    assert detector.tower_hp_reader.resets == 0
    assert detector.timer_reader.resets == 0
    assert detector.card_detector.resets == 0


def test_forgets_the_hand_between_battles(detector):
    detector.run(image=None)  # lobby
    assert detector.card_detector.resets == 1


def test_reads_tower_hp_in_game(detector):
    detector.screen_detector.result = ScreenName.IN_GAME
    state = detector.run(image=None)
    assert state.numbers.towers.left_enemy_princess.hp == 1918
    assert state.numbers.towers.left_enemy_princess.level == 8
    assert state.numbers.elixir == 7
    assert detector.tower_hp_reader.calls == 1


def test_reads_timer_in_game(detector):
    detector.screen_detector.result = ScreenName.IN_GAME
    state = detector.run(image=None)
    assert state.numbers.timer.time_left == 117
    assert state.numbers.timer.overtime is False
    assert detector.timer_reader.calls == 1


def test_resets_timer_between_battles(detector):
    state = detector.run(image=None)  # lobby
    assert detector.timer_reader.calls == 0
    assert detector.timer_reader.resets == 1
    assert state.numbers.timer.time_left == float("inf")


def test_resets_tower_hp_between_battles(detector):
    state = detector.run(image=None)  # lobby
    assert detector.tower_hp_reader.calls == 0
    assert detector.tower_hp_reader.resets == 1
    assert state.numbers.towers.left_enemy_princess.hp == float("inf")
    assert state.numbers.towers.left_enemy_princess.level == 0


def test_failure_returns_none_after_one_attempt(detector):
    detector.screen_detector.result = ScreenName.IN_GAME
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
        detector_module.Detector(DECK[:7], default_config().screen_detector)
