"""Playing through the API: a real Bot and BotController, with a fake
device and a fake state reader whose state each test sets."""

import dataclasses
import functools
import json
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient

import clashroyalebuildabot.bot.controller as controller_module
from clashroyalebuildabot.api import EventHub, create_app
from clashroyalebuildabot.bot.bot import Bot
from clashroyalebuildabot.bot.controller import BotController
from clashroyalebuildabot.game import ScreenName
from clashroyalebuildabot.game.cards import Cards
from clashroyalebuildabot.game.timer import Timer
from tests.conftest import make_state
from tests.test_api import wait_until
from tests.test_bot_lifecycle import ACTIONS, FakeVisualizer, make_config

# The next card, then the hand: knight (3), archers (3), witch (5), cannon (3).
HAND = [
    Cards.MUSKETEER,
    Cards.KNIGHT,
    Cards.ARCHERS,
    Cards.WITCH,
    Cards.CANNON,
]


class Device:
    def __init__(self):
        self.taps = []

    def take_screenshot(self):
        time.sleep(0.005)
        return np.zeros((4, 4, 3), np.uint8)

    def tap_sequence(self, points):
        self.taps.append(list(points))

    def click(self, x, y):
        pass

    def load_deck(self, cards):
        pass

    def close(self):
        pass


class StateReader:
    def __init__(self):
        self.state = make_state(cards=HAND, ready=[0, 1, 2, 3], elixir=4)

    def run(self, image):
        return self.state

    def close(self):
        pass


@pytest.fixture
def device():
    return Device()


@pytest.fixture
def reader():
    return StateReader()


@pytest.fixture
def make_client(monkeypatch, device, reader):
    def make(policy="external"):
        monkeypatch.setattr(
            controller_module,
            "Bot",
            functools.partial(
                Bot,
                device=device,
                state_reader=reader,
                visualizer=FakeVisualizer(),
            ),
        )
        config = make_config()
        config.bot.policy = policy
        controller = BotController(config, ACTIONS)
        return TestClient(create_app(controller, EventHub()))

    return make


def start(client):
    assert client.post("/api/start").status_code == 200
    wait_until(lambda: client.get("/api/state").status_code == 200)


def test_meta_describes_the_grid_deck_and_cards(make_client):
    with make_client() as client:
        meta = client.get("/api/meta").json()
    assert (meta["grid"]["width"], meta["grid"]["height"]) == (18, 32)
    assert meta["grid"]["river_rows"] == [15, 16]
    towers = meta["grid"]["towers"]
    assert towers["ally_king"]["centre"] == [9, 3]
    assert towers["left_ally_princess"]["centre"] == [3.5, 6.5]
    # The enemy's towers mirror ours across the river.
    for side in ("left_", "right_", ""):
        ally = towers[f"{side}ally_{'king' if not side else 'princess'}"]
        enemy = towers[f"{side}enemy_{'king' if not side else 'princess'}"]
        assert (enemy["x_min"], enemy["x_max"]) == (
            ally["x_min"],
            ally["x_max"],
        )
        assert enemy["y_min"] == 31 - ally["y_max"]
        assert enemy["y_max"] == 31 - ally["y_min"]
    assert {card["name"] for card in meta["deck"]} == {
        action.CARD.name for action in ACTIONS
    }
    names = {card["name"] for card in meta["cards"]}
    assert "baby_dragon" in names
    assert "blank" not in names
    knight = next(unit for unit in meta["units"] if unit["name"] == "knight")
    assert knight == {
        "name": "knight",
        "category": "troop",
        "target": "ground",
        "transport": "ground",
    }
    assert meta["policy"] == "external"


def test_no_state_until_the_bot_reads_a_frame(make_client):
    with make_client() as client:
        assert client.get("/api/state").status_code == 404


def test_state_is_plain_json(make_client, reader, unit_factory):
    reader.state = make_state(
        cards=HAND,
        ready=[0, 2],
        elixir=4,
        enemies=[unit_factory(9, 20)],
        left_enemy_hp=0,
    )
    with make_client() as client:
        start(client)
        response = client.get("/api/state")
    # Infinity would be invalid JSON; unknown values are null.
    state = json.loads(response.text)
    assert state["screen"] == "in_game"
    battle = state["battle"]
    assert battle["elixir"] == 4
    assert battle["timer"] == {"time_left": None, "overtime": False}
    assert battle["towers"]["enemy_king"] == {
        "destroyed": False,
        "hp": None,
        "level": None,
    }
    assert battle["towers"]["left_enemy_princess"]["destroyed"] is True
    assert battle["towers"]["left_enemy_princess"]["hp"] == 0
    assert battle["next_card"] == "musketeer"
    assert battle["hand"][0] == {
        "hand_index": 0,
        "card": "knight",
        "cost": 3,
        "playable": True,
    }
    assert battle["hand"][1]["playable"] is False  # not ready
    assert battle["hand"][2]["playable"] is False  # the witch costs 5
    assert battle["enemies"][0]["unit"] == "knight"
    assert (
        battle["enemies"][0]["tile_x"],
        battle["enemies"][0]["tile_y"],
    ) == (
        9,
        20,
    )
    assert state["pending_play"] is None


@pytest.mark.parametrize(
    ("screen", "shown"),
    [
        (ScreenName.LOBBY, "lobby"),
        (ScreenName.END_OF_GAME, "end_of_game"),
        (ScreenName.BYPASS_END_OF_GAME, "end_of_game"),
        (ScreenName.UNKNOWN, "unknown"),
    ],
)
def test_no_battle_outside_a_battle(make_client, reader, screen, shown):
    reader.state = make_state(screen=screen)
    with make_client() as client:
        start(client)
        state = client.get("/api/state").json()
    assert state["screen"] == shown
    assert state["battle"] is None


def test_actions_list_where_each_card_can_go(make_client):
    with make_client() as client:
        start(client)
        actions = client.get("/api/actions").json()
    assert actions["blocked_by"] is None
    cards = {card["card"]: card for card in actions["cards"]}
    assert set(cards) == {"knight", "archers", "cannon"}
    assert [9, 5] in cards["knight"]["tiles"]
    assert [9, 25] not in cards["knight"]["tiles"]


def test_a_play_is_tapped_and_then_pending(make_client, device):
    with make_client() as client:
        start(client)
        response = client.post(
            "/api/play", json={"hand_index": 0, "tile_x": 9, "tile_y": 5}
        )
        assert response.status_code == 200
        assert response.json()["card"] == "knight"
        assert len(device.taps) == 1

        # The fake screen never shows the knight played.
        wait_until(
            lambda: client.get("/api/state").json()["pending_play"] is not None
        )
        assert client.get("/api/actions").json()["blocked_by"] == (
            "play_pending"
        )
        again = client.post(
            "/api/play", json={"hand_index": 1, "tile_x": 9, "tile_y": 5}
        )
    assert again.status_code == 409
    assert again.json()["reason"] == "play_pending"
    assert len(device.taps) == 1


@pytest.mark.parametrize(
    ("play", "reason"),
    [
        ({"hand_index": 0, "tile_x": 9, "tile_y": 25}, "bad_tile"),
        ({"hand_index": 2, "tile_x": 9, "tile_y": 5}, "not_enough_elixir"),
        (
            {"hand_index": 0, "tile_x": 9, "tile_y": 5, "frame": 10**9},
            "stale",
        ),
    ],
)
def test_illegal_plays_are_refused_with_a_reason(
    make_client, device, play, reason
):
    with make_client() as client:
        start(client)
        response = client.post("/api/play", json=play)
    assert response.status_code == 409
    assert response.json()["reason"] == reason
    assert device.taps == []


def test_a_play_on_an_old_frame_is_stale(make_client, device):
    with make_client() as client:
        start(client)
        frame = client.get("/api/state").json()["frame"]
        time.sleep(0.05)
        response = client.post(
            "/api/play",
            json={
                "hand_index": 0,
                "tile_x": 9,
                "tile_y": 5,
                "frame": frame,
                "max_age": 0.01,
            },
        )
    assert response.json()["reason"] == "stale"
    assert device.taps == []


def test_out_of_range_plays_are_invalid(make_client):
    with make_client() as client:
        response = client.post(
            "/api/play", json={"hand_index": 4, "tile_x": 0, "tile_y": 0}
        )
    assert response.status_code == 422


def test_no_plays_outside_a_battle(make_client, reader, device):
    reader.state = make_state(screen=ScreenName.LOBBY)
    with make_client() as client:
        start(client)
        assert client.get("/api/actions").json()["blocked_by"] == (
            "not_in_battle"
        )
        response = client.post(
            "/api/play", json={"hand_index": 0, "tile_x": 9, "tile_y": 5}
        )
    assert response.json()["reason"] == "not_in_battle"
    assert device.taps == []


def test_no_plays_while_stopped_or_paused(make_client):
    play = {"hand_index": 0, "tile_x": 9, "tile_y": 5}
    with make_client() as client:
        assert client.post("/api/play", json=play).json()["reason"] == (
            "not_running"
        )
        assert client.get("/api/actions").json()["blocked_by"] == (
            "not_running"
        )
        start(client)
        client.post("/api/pause")
        assert client.post("/api/play", json=play).json()["reason"] == (
            "paused"
        )


def test_the_builtin_policy_refuses_client_plays(make_client):
    with make_client(policy="builtin") as client:
        start(client)
        assert client.get("/api/actions").json()["blocked_by"] == (
            "builtin_policy"
        )
        response = client.post(
            "/api/play", json={"hand_index": 0, "tile_x": 9, "tile_y": 5}
        )
    assert response.json()["reason"] == "builtin_policy"


def test_states_stream(make_client):
    with make_client() as client:
        start(client)
        with client.websocket_connect("/api/states") as ws:
            first = ws.receive_json()
            second = ws.receive_json()
    assert first["screen"] == "in_game"
    assert second["frame"] > first["frame"]


def test_unit_stats_at_a_level(make_client):
    with make_client() as client:
        knight = client.get("/api/units/knight", params={"level": 11}).json()
        assert (knight["hitpoints"], knight["damage"]) == (1766, 202)
        default = client.get("/api/units/knight").json()
        assert default["level"] == 11
        assert client.get("/api/units/nobody").status_code == 404
        response = client.get("/api/units/knight", params={"level": 0})
        assert response.status_code == 422


def test_card_stats_with_their_units(make_client):
    with make_client() as client:
        card = client.get("/api/cards/witch", params={"level": 11}).json()
        assert card["summons"][0]["stats"]["spawns"]["unit"] == "skeleton"
        fireball = client.get("/api/cards/fireball").json()
        assert fireball["spell"]["damage"] > 0
        assert client.get("/api/cards/nothing").status_code == 404
        response = client.get("/api/cards/witch", params={"level": 3})
        assert response.status_code == 422


def test_meta_has_elixir_and_tower_stats(make_client):
    with make_client() as client:
        meta = client.get("/api/meta").json()
    assert meta["elixir"]["phases"][0] == {
        "from": 0,
        "to": 120,
        "seconds_per_elixir": 2.8,
    }
    assert meta["tower_stats"]["princess"]["range"] == 7.5
    assert meta["default_level"] == 11


def test_state_has_the_elixir_rate(make_client, reader):
    reader.state = make_state(cards=HAND, ready=[0], elixir=4)
    reader.state = dataclasses.replace(
        reader.state, timer=Timer(time_left=30, overtime=True)
    )
    with make_client() as client:
        start(client)
        rate = client.get("/api/state").json()["battle"]["elixir_rate"]
    assert rate == {"seconds_per_elixir": 0.93, "multiplier": 3}
