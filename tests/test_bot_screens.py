from clashroyalebuildabot.game import ScreenName, Screens
from tests.conftest import make_state
from tests.test_bot_lifecycle import make_bot as make_test_bot
from tests.test_bot_lifecycle import make_config


class TapRecorder:
    def click(self, x, y):
        pass

    def close(self):
        pass


class Record:
    """What the bot did: cards played, waits, and taps."""

    def __init__(self):
        self.played = 0
        self.waits: list[str] = []
        self.taps: list[tuple[int, int]] = []


def make_bot(monkeypatch, auto_start=False):
    config = make_config()
    config.bot.auto_start_game = auto_start
    bot = make_test_bot(TapRecorder(), config)
    record = Record()

    def play(state):
        record.played += 1

    def wait(prefix, delay):
        record.waits.append(prefix)

    def tap(x, y):
        record.taps.append((x, y))

    monkeypatch.setattr(bot, "_handle_game_step", play)
    monkeypatch.setattr(bot, "_log_and_wait", wait)
    monkeypatch.setattr(bot.emulator, "click", tap)
    return bot, record


def show(bot, monkeypatch, screen):
    monkeypatch.setattr(
        bot, "compute_state", lambda: make_state(screen=screen)
    )
    return bot.step(None)


def test_plays_cards_in_battle(monkeypatch):
    bot, record = make_bot(monkeypatch)
    show(bot, monkeypatch, ScreenName.IN_GAME)
    assert record.played == 1


def test_waits_on_unknown_screens(monkeypatch):
    # Searching for an opponent, loading, popups and the like.
    bot, record = make_bot(monkeypatch)
    show(bot, monkeypatch, ScreenName.UNKNOWN)
    assert record.played == 0
    assert record.taps == []
    assert record.waits == ["Waiting on the unknown screen"]


def test_never_plays_cards_in_the_lobby(monkeypatch):
    bot, record = make_bot(monkeypatch, auto_start=False)
    show(bot, monkeypatch, ScreenName.LOBBY)
    assert record.played == 0
    assert record.taps == []


def test_starts_a_battle_from_the_lobby_when_asked(monkeypatch):
    bot, record = make_bot(monkeypatch, auto_start=True)
    show(bot, monkeypatch, ScreenName.LOBBY)
    assert record.taps == [Screens.get(ScreenName.LOBBY).click_xy]
    assert record.played == 0


def test_taps_ok_once_even_if_the_screen_flickers(monkeypatch):
    bot, record = make_bot(monkeypatch)
    for screen in (
        ScreenName.END_OF_GAME,
        ScreenName.UNKNOWN,
        ScreenName.END_OF_GAME,
    ):
        show(bot, monkeypatch, screen)
    assert record.taps == [Screens.get(ScreenName.END_OF_GAME).click_xy]
