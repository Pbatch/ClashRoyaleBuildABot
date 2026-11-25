"""Web pages in the browser can't drive the bot: api/security.py."""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from clashroyalebuildabot.api import EventHub, create_app
from clashroyalebuildabot.api.security import refusal
from tests.test_api import LOCAL, LOCAL_WS
from tests.test_api import controller as controller

EVIL = "https://evil.example"


@pytest.mark.parametrize(
    "host",
    [
        "127.0.0.1:8000",
        "localhost:8000",
        "localhost",
        "[::1]:8000",
        "LOCALHOST",
    ],
)
def test_loopback_hosts_are_accepted(host):
    assert refusal({"host": host}, check_host=True) is None


@pytest.mark.parametrize(
    "host", ["evil.example", "evil.example:8000", "192.168.1.5:8000", ""]
)
def test_other_hosts_are_refused_on_loopback(host):
    assert refusal({"host": host}, check_host=True) is not None


def test_any_host_is_accepted_off_loopback():
    assert refusal({"host": "192.168.1.5:8000"}, check_host=False) is None


@pytest.mark.parametrize("check_host", [True, False])
@pytest.mark.parametrize(
    "origin",
    [
        EVIL,
        "http://127.0.0.1:9999",
        "https://127.0.0.1:8000.evil.example",
        "null",
    ],
)
def test_foreign_origins_are_refused(origin, check_host):
    headers = {"host": "127.0.0.1:8000", "origin": origin}
    reason = refusal(headers, check_host)
    assert reason is not None
    assert "aren't allowed" in reason


def test_the_servers_own_origin_is_accepted():
    headers = {"host": "127.0.0.1:8000", "origin": "http://127.0.0.1:8000"}
    assert refusal(headers, check_host=True) is None


@pytest.fixture
def local(controller):
    with TestClient(
        create_app(controller, EventHub()), base_url=LOCAL
    ) as client:
        yield client


def test_a_web_page_cant_start_the_bot(local, controller):
    response = local.post("/api/start", headers={"Origin": EVIL})
    assert response.status_code == 403
    assert "evil.example" in response.json()["detail"]
    assert not controller.is_running


def test_a_rebound_domain_is_refused(local):
    response = local.get("/api/status", headers={"Host": "evil.example:8000"})
    assert response.status_code == 403


def test_mcp_is_protected_too(local):
    response = local.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        headers={
            "Origin": EVIL,
            "Accept": "application/json, text/event-stream",
        },
    )
    assert response.status_code == 403


def test_a_web_page_cant_open_a_websocket(local):
    with (
        pytest.raises(WebSocketDisconnect) as refused,
        local.websocket_connect(
            LOCAL_WS + "/api/events", headers={"Origin": EVIL}
        ),
    ):
        pass
    assert refused.value.code == 1008


def test_same_origin_pages_and_programs_get_through(local):
    # The /docs page, and the bot's own web UI, send their own origin.
    assert (
        local.post("/api/pause", headers={"Origin": LOCAL}).status_code == 409
    )
    # Programs send no Origin.
    assert local.get("/api/status").status_code == 200
    with local.websocket_connect(LOCAL_WS + "/api/events") as ws:
        assert ws.receive_json()["type"] == "status"


def test_served_on_the_network_any_host_works(controller):
    app = create_app(controller, EventHub(), host="0.0.0.0")
    with TestClient(app, base_url="http://192.168.1.5:8000") as client:
        assert client.get("/api/status").status_code == 200
        assert (
            client.post("/api/start", headers={"Origin": EVIL}).status_code
            == 403
        )
