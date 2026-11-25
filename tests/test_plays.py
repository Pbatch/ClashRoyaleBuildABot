import pytest

from clashroyalebuildabot.bot.plays import (
    Play,
    PlayRejected,
    PlayRequest,
    PlayRequests,
    Reason,
    affordable_hand,
    check,
)
from clashroyalebuildabot.constants.device_screen import ALL_TILES
from clashroyalebuildabot.game import ScreenName
from clashroyalebuildabot.game.cards import Cards
from tests.conftest import make_state

# The next card, then the hand: knight (3), arrows (3), witch (5), cannon (3).
HAND = [Cards.ARCHERS, Cards.KNIGHT, Cards.ARROWS, Cards.WITCH, Cards.CANNON]


def battle(elixir=4, ready=(0, 1, 2, 3), **kwargs):
    return make_state(cards=HAND, ready=list(ready), elixir=elixir, **kwargs)


def reason(state, play):
    with pytest.raises(PlayRejected) as error:
        check(state, play)
    return error.value.reason


def test_a_legal_play_returns_its_card():
    assert check(battle(), Play(0, 9, 5)) == Cards.KNIGHT


def test_affordable_hand_leaves_out_what_costs_too_much():
    assert affordable_hand(battle(elixir=4)) == [
        (0, Cards.KNIGHT),
        (1, Cards.ARROWS),
        (3, Cards.CANNON),
    ]
    assert affordable_hand(battle(elixir=4, ready=[2, 3])) == [
        (3, Cards.CANNON)
    ]


@pytest.mark.parametrize(
    ("state", "play", "expected"),
    [
        (
            battle(screen=ScreenName.LOBBY),
            Play(0, 9, 5),
            Reason.NOT_IN_BATTLE,
        ),
        (battle(ready=[1]), Play(0, 9, 5), Reason.NOT_READY),
        (battle(elixir=4), Play(2, 9, 5), Reason.NOT_ENOUGH_ELIXIR),
        # Troops stay on our half while the enemy's towers stand.
        (battle(), Play(0, 9, 25), Reason.BAD_TILE),
        (battle(), Play(0, 18, 5), Reason.BAD_TILE),
        (
            make_state(cards=HAND[:2], ready=[0, 1]),
            Play(3, 9, 5),
            Reason.BAD_HAND_INDEX,
        ),
    ],
)
def test_illegal_plays_say_why(state, play, expected):
    assert reason(state, play) == expected


def test_spells_go_anywhere():
    x, y = ALL_TILES[-1]
    assert y > 16
    assert check(battle(), Play(1, x, y)) == Cards.ARROWS


def test_a_fallen_tower_opens_its_side():
    play = Play(0, 2, 20)
    assert reason(battle(), play) == Reason.BAD_TILE
    assert check(battle(left_enemy_hp=0), play) == Cards.KNIGHT


def test_one_request_waits_at_a_time():
    requests = PlayRequests()
    first = requests.submit(PlayRequest(Play(0, 9, 5)))
    with pytest.raises(PlayRejected) as error:
        requests.submit(PlayRequest(Play(1, 9, 5)))
    assert error.value.reason == Reason.BUSY

    taken = requests.take()
    assert taken is not None
    assert taken.future is first
    assert requests.take() is None


def test_a_request_given_up_on_is_never_taken():
    requests = PlayRequests()
    future = requests.submit(PlayRequest(Play(0, 9, 5)))
    assert future.cancel()
    assert requests.take() is None


def test_rejecting_the_waiting_request():
    requests = PlayRequests()
    future = requests.submit(PlayRequest(Play(0, 9, 5)))
    requests.reject_waiting(Reason.NOT_IN_BATTLE, "on the lobby")
    with pytest.raises(PlayRejected) as error:
        future.result(timeout=1)
    assert error.value.reason == Reason.NOT_IN_BATTLE
