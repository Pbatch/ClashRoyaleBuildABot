import threading
import time
from typing import ClassVar

import cv2
import numpy as np
import pytest
import yaml
from fastapi.testclient import TestClient
from loguru import logger

import clashroyalebuildabot.bot.controller as controller_module
import clashroyalebuildabot.utils.logger as logger_module
from clashroyalebuildabot.api import EventHub, create_app
from clashroyalebuildabot.bot.controller import BotController
from clashroyalebuildabot.constants import paths
from tests.conftest import default_config

# Where a client on the same machine reaches the API. TestClient's default,
# testserver, isn't a loopback name, so the API would refuse it.
LOCAL = "http://127.0.0.1:8000"
# TestClient connects WebSockets to ws://testserver unless given a full URL.
LOCAL_WS = "ws://127.0.0.1:8000"


class FakeBot:
    """Runs until stopped. When `hold` is set, it keeps running after
    stop() until the test releases it."""

    instances: ClassVar[list["FakeBot"]] = []
    hold: ClassVar[threading.Event | None] = None

    is_external = False

    def __init__(
        self, actions, config, on_frame=None, on_observation=None, policy=None
    ):
        self.on_frame = on_frame
        self.on_observation = on_observation
        self.config = config.model_copy(deep=True)
        self.stopped = threading.Event()
        self.is_paused = False
        FakeBot.instances.append(self)

    def run(self):
        self.stopped.wait(timeout=5)
        if FakeBot.hold is not None:
            FakeBot.hold.wait(timeout=5)

    def stop(self):
        self.stopped.set()

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False


def wait_until(condition, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(0.01)
    raise AssertionError("condition not met in time")


@pytest.fixture
def controller(monkeypatch):
    FakeBot.instances = []
    FakeBot.hold = None
    monkeypatch.setattr(controller_module, "Bot", FakeBot)
    return BotController(default_config(), [])


@pytest.fixture
def hub():
    return EventHub()


@pytest.fixture
def client(controller, hub):
    with TestClient(
        create_app(controller, hub), base_url=LOCAL
    ) as test_client:
        yield test_client


def send_frame(frame):
    """Hand a frame to the API as the bot's visualizer would."""
    on_frame = FakeBot.instances[0].on_frame
    assert on_frame is not None
    on_frame(frame)


def started(client, controller):
    assert client.post("/api/start").json() == {"status": "running"}
    wait_until(lambda: controller._bot is not None)


def test_start_pause_resume_stop(client, controller):
    assert client.get("/api/status").json() == {"status": "stopped"}
    started(client, controller)

    assert client.post("/api/pause").json() == {"status": "paused"}
    assert client.post("/api/resume").json() == {"status": "running"}

    FakeBot.hold = threading.Event()
    assert client.post("/api/stop").json() == {"status": "stopping"}
    FakeBot.hold.set()
    wait_until(
        lambda: client.get("/api/status").json() == {"status": "stopped"}
    )


@pytest.mark.parametrize("action", ["stop", "pause", "resume"])
def test_actions_that_cant_happen_now_conflict(client, action):
    response = client.post(f"/api/{action}")
    assert response.status_code == 409
    assert "stopped" in response.json()["detail"]


def test_starting_twice_conflicts(client, controller):
    started(client, controller)
    assert client.post("/api/start").status_code == 409


def test_config_round_trip(client, controller):
    config = client.get("/api/config").json()
    assert config["bot"]["load_deck"] == controller.config.bot.load_deck

    response = client.patch(
        "/api/config",
        json={"bot": {"load_deck": True}, "ingame": {"play_action": 2.5}},
    )
    assert response.status_code == 200
    assert response.json()["ingame"]["play_action"] == 2.5
    # Changed in place, so everything holding the config sees it.
    assert controller.config.bot.load_deck is True
    assert controller.config.ingame.play_action == 2.5


def test_the_next_bot_gets_the_new_config(client, controller):
    client.patch("/api/config", json={"adb": {"device_serial": "abc"}})
    started(client, controller)
    assert FakeBot.instances[0].config.adb.device_serial == "abc"


@pytest.mark.parametrize(
    "changes",
    [
        {"ingame": {"play_action": -1}},
        {"bot": {"no_such_setting": True}},
        {"no_such_section": {}},
        # One bad value means none of the others apply either.
        {"bot": {"load_deck": True}, "ingame": {"play_action": 0}},
    ],
)
def test_invalid_config_changes_nothing(client, controller, changes):
    before = controller.config.model_dump()
    response = client.patch("/api/config", json=changes)
    assert response.status_code == 422
    assert controller.config.model_dump() == before


def test_log_level_change_reconfigures_logging(
    client, controller, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        logger_module, "setup_logger", lambda config, sinks: calls.append(1)
    )
    logger_module.follow_log_level(controller)
    assert calls == [1]  # set up straight away

    client.patch("/api/config", json={"bot": {"load_deck": True}})
    assert calls == [1]
    client.patch("/api/config", json={"bot": {"log_level": "error"}})
    assert calls == [1, 1]


def test_events_stream_status_changes(client, controller):
    with client.websocket_connect(LOCAL_WS + "/api/events") as ws:
        assert ws.receive_json() == {"type": "status", "status": "stopped"}
        started(client, controller)
        assert ws.receive_json() == {"type": "status", "status": "running"}
        client.post("/api/pause")
        assert ws.receive_json() == {"type": "status", "status": "paused"}


def test_events_stream_logs(client, hub):
    sink_id = logger.add(hub.log_sink)
    try:
        with client.websocket_connect(LOCAL_WS + "/api/events") as ws:
            ws.receive_json()  # the current status
            # Logged from another thread, as the bot does.
            thread = threading.Thread(target=lambda: logger.info("hello"))
            thread.start()
            thread.join()
            event = ws.receive_json()
    finally:
        logger.remove(sink_id)
    assert event["type"] == "log"
    assert event["level"] == "INFO"
    assert event["message"] == "hello"


def test_frames_stream_as_jpeg(client, controller, hub):
    started(client, controller)
    frame = np.zeros((40, 30, 3), np.uint8)
    frame[..., 0] = 255  # red, in RGB
    with client.websocket_connect(LOCAL_WS + "/api/frames") as ws:
        wait_until(lambda: hub.frames.has_subscribers)
        send_frame(frame)
        data = ws.receive_bytes()

    decoded = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    assert decoded is not None
    assert decoded.shape == frame.shape
    # OpenCV decodes as BGR, so red is the last channel.
    assert decoded[..., 2].mean() > 200
    assert decoded[..., 0].mean() < 50


def test_frames_arent_encoded_without_viewers(client, controller, monkeypatch):
    encoded = []
    monkeypatch.setattr(
        "clashroyalebuildabot.api.app.encode_jpeg", encoded.append
    )
    started(client, controller)
    send_frame(np.zeros((4, 4, 3), np.uint8))
    assert encoded == []


def test_disconnected_viewers_are_unsubscribed(client, hub):
    with client.websocket_connect(LOCAL_WS + "/api/frames"):
        wait_until(lambda: hub.frames.has_subscribers)
    wait_until(lambda: not hub.frames.has_subscribers)


def test_shutting_down_stops_the_bot(controller, hub):
    with TestClient(
        create_app(controller, hub), base_url=LOCAL
    ) as test_client:
        started(test_client, controller)
        bot = FakeBot.instances[0]
    assert bot.stopped.is_set()
    assert not controller.is_running


def test_events_stream_config_changes(client):
    with client.websocket_connect(LOCAL_WS + "/api/events") as ws:
        ws.receive_json()  # the current status
        client.patch("/api/config", json={"bot": {"load_deck": True}})
        event = ws.receive_json()
    assert event["type"] == "config"
    assert event["config"]["bot"]["load_deck"] is True


def test_save_config_writes_only_changed_settings(
    client, monkeypatch, tmp_path
):
    user_config = tmp_path / "config.yaml"
    monkeypatch.setattr(paths, "USER_CONFIG_PATH", str(user_config))
    client.patch("/api/config", json={"ingame": {"play_action": 2.5}})

    response = client.post("/api/config/save")

    assert response.status_code == 200
    saved = yaml.safe_load(user_config.read_text(encoding="utf-8"))
    assert saved == {"ingame": {"play_action": 2.5}}


def test_web_ui_is_served_at_the_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<title>Build-A-Bot</title>" in response.text
