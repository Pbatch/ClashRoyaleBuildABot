import time

import pytest
from loguru import logger

import clashroyalebuildabot.detectors.state_reader as state_reader_module
from clashroyalebuildabot.game import ScreenName, State
from clashroyalebuildabot.game.cards import Cards
from clashroyalebuildabot.game.timer import Timer
from clashroyalebuildabot.game.towers import Tower, Towers

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


class FakePart:
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


class FakeTowerHPReader(FakePart):
    def __init__(self, *args, **kwargs):
        super().__init__(result=READ_TOWERS)
        self.resets = 0

    def latest(self):
        return Towers()

    def reset(self):
        self.resets += 1


READ_TIMER = Timer(time_left=117)


class FakeTimerReader(FakePart):
    def __init__(self, *args, **kwargs):
        super().__init__(result=READ_TIMER)
        self.resets = 0

    def latest(self):
        return Timer()

    def reset(self):
        self.resets += 1


class FakeCardDetector(FakePart):
    def __init__(self, cards):
        super().__init__(result=(list(cards[:5]), [0, 1]))
        self.resets = 0

    def reset(self):
        self.resets += 1


@pytest.fixture
def reader(monkeypatch):
    monkeypatch.setattr(state_reader_module, "CardDetector", FakeCardDetector)
    monkeypatch.setattr(
        state_reader_module,
        "UnitDetector",
        lambda cards: FakePart(result=([], [])),
    )
    monkeypatch.setattr(
        state_reader_module,
        "ElixirReader",
        lambda: FakePart(result=7),
    )
    monkeypatch.setattr(
        state_reader_module,
        "ScreenDetector",
        lambda: FakePart(result=ScreenName.LOBBY),
    )
    monkeypatch.setattr(
        state_reader_module, "TowerHPReader", FakeTowerHPReader
    )
    monkeypatch.setattr(state_reader_module, "TimerReader", FakeTimerReader)
    return state_reader_module.StateReader(DECK)


def in_battle(reader):
    """The frame shows a battle."""
    reader.screen_detector.result = ScreenName.IN_GAME


def test_returns_state_in_game(reader):
    in_battle(reader)
    state = reader.run(image=None)
    assert isinstance(state, State)
    assert state.screen == ScreenName.IN_GAME
    assert state.cards == DECK[:5]
    assert state.ready == [0, 1]


def battle_detectors(reader):
    return (
        reader.card_detector,
        reader.unit_detector,
        reader.elixir_reader,
    )


def test_skips_battle_detectors_outside_a_battle(reader):
    state = reader.run(image=None)  # lobby
    assert state.screen == ScreenName.LOBBY
    assert [d.calls for d in battle_detectors(reader)] == [0, 0, 0]
    assert (state.allies, state.enemies) == ([], [])
    assert (state.cards, state.ready) == ([], [])
    assert state.elixir == 0


def test_unknown_screen_keeps_the_readings(reader):
    # No elixir bar and no known screen: a screen the bot waits through, or
    # the elixir bar hidden for a moment mid-battle.
    reader.screen_detector.result = ScreenName.UNKNOWN
    state = reader.run(image=None)
    assert state.screen == ScreenName.UNKNOWN
    assert state.ready == []
    assert [d.calls for d in battle_detectors(reader)] == [0, 0, 0]
    assert reader.tower_hp_reader.calls == 0
    assert reader.timer_reader.calls == 0
    # A flicker mid-battle mustn't lose the tower and timer readings, or
    # the remembered hand.
    assert reader.tower_hp_reader.resets == 0
    assert reader.timer_reader.resets == 0
    assert reader.card_detector.resets == 0


@pytest.mark.parametrize(
    "screen",
    [
        ScreenName.LOBBY,
        ScreenName.END_OF_GAME,
        ScreenName.BYPASS_END_OF_GAME,
    ],
)
def test_readings_reset_on_screens_between_battles(reader, screen):
    reader.screen_detector.result = screen
    assert reader.run(image=None).screen == screen
    assert reader.tower_hp_reader.resets == 1
    assert reader.timer_reader.resets == 1
    assert reader.card_detector.resets == 1


def test_forgets_the_hand_between_battles(reader):
    reader.run(image=None)  # lobby
    assert reader.card_detector.resets == 1


def test_reads_tower_hp_in_game(reader):
    in_battle(reader)
    state = reader.run(image=None)
    assert state.towers.left_enemy_princess.hp == 1918
    assert state.towers.left_enemy_princess.level == 8
    assert state.elixir == 7
    assert reader.tower_hp_reader.calls == 1


def test_reads_timer_in_game(reader):
    in_battle(reader)
    state = reader.run(image=None)
    assert state.timer.time_left == 117
    assert state.timer.overtime is False
    assert reader.timer_reader.calls == 1


def test_resets_timer_between_battles(reader):
    state = reader.run(image=None)  # lobby
    assert reader.timer_reader.calls == 0
    assert reader.timer_reader.resets == 1
    assert state.timer.time_left == float("inf")


def test_resets_tower_hp_between_battles(reader):
    state = reader.run(image=None)  # lobby
    assert reader.tower_hp_reader.calls == 0
    assert reader.tower_hp_reader.resets == 1
    assert state.towers.left_enemy_princess.hp == float("inf")
    assert state.towers.left_enemy_princess.level == 0


def test_failure_returns_none_after_one_attempt(reader):
    in_battle(reader)
    reader.unit_detector.error = RuntimeError("model failed")
    messages = []
    sink = logger.add(lambda m: messages.append(m.record["message"]))
    try:
        start = time.monotonic()
        assert reader.run(image=None) is None
        elapsed = time.monotonic() - start
    finally:
        logger.remove(sink)

    assert reader.unit_detector.calls == 1  # no retries
    assert elapsed < 0.5  # no sleeping between attempts
    assert any("Detection failed" in m for m in messages)


def test_keeps_the_given_cards_without_copying(reader):
    assert reader.cards is DECK


def test_rejects_wrong_deck_size(monkeypatch):
    with pytest.raises(
        state_reader_module.WikifiedError, match="must have 8 cards, but 7"
    ):
        state_reader_module.StateReader(DECK[:7])
