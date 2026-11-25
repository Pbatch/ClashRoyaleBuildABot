"""The MCP tools at /mcp: the same operations as the REST routes, through
FastMCP's in-memory client."""

import asyncio

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from fastmcp import Client
from fastmcp.exceptions import ToolError
from mcp.types import ImageContent

from clashroyalebuildabot.api import EventHub, create_app
from tests.test_api import FakeBot, send_frame, started, wait_until

# The fixtures these tests share with the REST tests.
from tests.test_api import client as client
from tests.test_api import controller as controller
from tests.test_api import hub as hub
from tests.test_api_play import device as device
from tests.test_api_play import make_client as make_client
from tests.test_api_play import reader as reader
from tests.test_api_play import start


def call(app, tool, arguments=None):
    """The tool's result, through an MCP client of app's server."""

    async def run():
        async with Client(app.state.mcp) as mcp:
            return await mcp.call_tool(tool, arguments or {})

    return asyncio.run(run())


def test_every_route_is_a_tool_with_the_same_name(client):
    async def tools():
        async with Client(client.app.state.mcp) as mcp:
            return await mcp.list_tools()

    tools = {tool.name: tool for tool in asyncio.run(tools())}
    routes = {
        operation["operationId"]
        for methods in client.get("/openapi.json").json()["paths"].values()
        for operation in methods.values()
    }
    assert set(tools) == routes
    assert tools["get_state"].annotations.read_only_hint is True
    assert tools["play"].annotations.read_only_hint is False
    # The docstring is the description.
    assert "hand_index" in tools["play"].description


def test_lifecycle_through_tools(client, controller):
    assert call(client.app, "get_status").data.status == "stopped"
    assert call(client.app, "start").data.status == "running"
    wait_until(lambda: controller._bot is not None)
    assert client.get("/api/status").json() == {"status": "running"}
    assert call(client.app, "pause").data.status == "paused"


def test_errors_carry_the_message(client):
    with pytest.raises(
        ToolError, match="Can't pause while the bot is stopped"
    ):
        call(client.app, "pause")
    with pytest.raises(ToolError, match="No state yet"):
        call(client.app, "get_state")


def test_invalid_config_names_the_setting(client, controller):
    before = controller.config.model_dump()
    with pytest.raises(ToolError, match=r"ingame\.play_action"):
        call(
            client.app,
            "update_config",
            {"changes": {"ingame": {"play_action": -1}}},
        )
    assert controller.config.model_dump() == before


def test_screenshot_is_an_image(client, controller):
    with pytest.raises(ToolError, match="No frame yet"):
        call(client.app, "screenshot")
    started(client, controller)
    frame = np.zeros((40, 30, 3), np.uint8)
    frame[..., 0] = 255
    send_frame(frame)

    (content,) = call(client.app, "screenshot").content
    assert isinstance(content, ImageContent)
    assert content.mime_type == "image/jpeg"
    # The same frame over REST.
    response = client.get("/api/screenshot.jpg")
    assert response.headers["content-type"] == "image/jpeg"
    decoded = cv2.imdecode(
        np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR
    )
    assert decoded.shape == frame.shape


def test_the_screenshot_is_cleared_when_the_bot_stops(client, controller):
    started(client, controller)
    send_frame(np.zeros((4, 4, 3), np.uint8))
    assert client.get("/api/screenshot.jpg").status_code == 200
    FakeBot.instances[0].stop()
    wait_until(lambda: not controller.is_running)
    assert client.get("/api/screenshot.jpg").status_code == 404


def test_a_play_through_a_tool(make_client, device):
    with make_client() as client:
        start(client)
        result = call(
            client.app,
            "play",
            {"request": {"hand_index": 0, "tile_x": 9, "tile_y": 5}},
        )
        assert result.data.card == "knight"
        assert len(device.taps) == 1
        with pytest.raises(ToolError, match=r"^play_pending: "):
            call(
                client.app,
                "play",
                {"request": {"hand_index": 1, "tile_x": 9, "tile_y": 25}},
            )


def test_mcp_is_served_over_http(controller):
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "0"},
        },
    }
    app = create_app(controller, EventHub())
    with TestClient(app, base_url="http://127.0.0.1:8000") as http:
        response = http.post(
            "/mcp",
            json=initialize,
            headers={"Accept": "application/json, text/event-stream"},
        )
        assert response.status_code == 200
        assert "Clash Royale Build-A-Bot" in response.text
        # The REST routes and docs still win over the mount.
        assert http.get("/api/status").json() == {"status": "stopped"}
        assert http.get("/docs").status_code == 200
