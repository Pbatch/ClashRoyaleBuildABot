"""An HTTP and WebSocket API over the BotController.

REST, under /api:
    GET   /status   {"status": "stopped" | "running" | "paused" | "stopping"}
    POST  /start, /stop, /pause, /resume
                    The new status, or 409 if that isn't possible now.
    GET   /config   All settings.
    PATCH /config   Some settings, e.g. {"bot": {"load_deck": true}}. A bot
                    already running keeps its settings; they apply from the
                    next start. 422, and nothing changed, if any is invalid.
    POST  /config/save   Save the settings to config.yaml.

    For clients that play the game themselves (bot.policy: external):
    GET   /meta     The grid, the deck, every card and unit, the elixir
                    timeline and tower stats.
    GET   /units/{name}?level=   A unit's stats at a level (default 11).
    GET   /cards/{name}?level=   A card's stats, with its units'.
    GET   /state    The latest frame's state. 404 until the bot reads one.
    GET   /actions  What can be played now, and where, or why nothing can.
    POST  /play     {"hand_index", "tile_x", "tile_y", "frame"?, "max_age"?}
                    Waits until the bot has tapped it: 200 with the play,
                    or 409 with {"reason", "message"} if it wasn't made.
    GET   /screenshot.jpg   The latest annotated frame, while
                    visuals.show_images is on. 404 until there is one.

The same operations are MCP tools, for AI agents, at /mcp (streamable
HTTP). Both are built from api/operations.py, so they always match.

WebSockets, under /api:
    /events   JSON: the current status on connect, then
              {"type": "status", "status": ...} on each change,
              {"type": "config", "config": ...} after each settings change
              and {"type": "log", "time", "level", "source", "message"}.
    /states   JSON: each frame's state, as GET /state returns it. Slow
              clients skip to the newest.
    /frames   Binary: each annotated frame as a JPEG, while
              visuals.show_images is on. Slow clients skip frames.

The web UI, clashroyalebuildabot/web/index.html, is served at /.

There's no authentication: anyone who can reach the server can drive the
device, so serve it on localhost unless the network is trusted.
"""

import asyncio
import contextlib
import functools
import inspect
import os
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any

import anyio
import numpy as np
from fastapi import APIRouter, FastAPI, Request, WebSocket
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.websockets import WebSocketDisconnect
from fastmcp.utilities.lifespan import combine_lifespans

from clashroyalebuildabot.api.events import EventHub
from clashroyalebuildabot.api.mcp import create_mcp
from clashroyalebuildabot.api.operations import (
    ApiError,
    Jpeg,
    Operation,
    encode_jpeg,
    operations,
)
from clashroyalebuildabot.api.schemas import StateOut
from clashroyalebuildabot.bot.bot import Observation
from clashroyalebuildabot.bot.controller import BotController
from clashroyalebuildabot.constants.paths import LOGO_PATH, WEB_UI_PATH


async def _pump(
    websocket: WebSocket,
    queue: asyncio.Queue[Any],
    send: Callable[[Any], Awaitable[None]],
) -> None:
    """Send everything from queue until the client disconnects.

    An anyio task group, not bare asyncio tasks, so a cancellation from the
    server (on shutdown, say) unwinds through it cleanly."""
    async with anyio.create_task_group() as group:

        async def forward() -> None:
            try:
                while True:
                    await send(await queue.get())
            except WebSocketDisconnect:
                group.cancel_scope.cancel()

        group.start_soon(forward)
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
        group.cancel_scope.cancel()


def _add_route(router: APIRouter, operation: Operation) -> None:
    """operation as a route. FastAPI runs it in its threadpool, as it's
    sync, and takes its schema from its signature and docstring."""
    fn = operation.fn
    endpoint: Callable[..., Any] = fn
    extra: dict[str, Any] = {}
    if inspect.signature(fn).return_annotation is Jpeg:

        @functools.wraps(fn)
        def endpoint(*args: Any, **kwargs: Any) -> Response:  # noqa: ANN401
            return Response(fn(*args, **kwargs).data, media_type="image/jpeg")

        extra = {"response_model": None, "response_class": Response}
    router.add_api_route(
        operation.path,
        endpoint,
        methods=[operation.method],
        name=operation.name,
        operation_id=operation.name,
        responses=operation.responses,
        **extra,
    )


def create_app(
    controller: BotController, hub: EventHub | None = None
) -> FastAPI:
    """The API for controller: REST and WebSockets under /api, and MCP at
    /mcp. Pass the hub whose log_sink is attached to the logger, so log
    lines reach /api/events.

    Shutting the app down stops the bot.
    """
    hub = hub or EventHub()

    controller.add_status_listener(
        lambda status: hub.events.publish(
            {"type": "status", "status": status.value}
        )
    )

    controller.add_config_listener(
        lambda config: hub.events.publish(
            {"type": "config", "config": config.model_dump()}
        )
    )

    def publish_frame(frame: np.ndarray) -> None:
        # Encoded on the bot's thread, so only when someone is watching.
        if hub.frames.has_subscribers:
            hub.frames.publish(encode_jpeg(frame))

    controller.add_frame_listener(publish_frame)

    def publish_state(observation: Observation) -> None:
        # Converted on the bot's thread, so only when someone is watching.
        if hub.states.has_subscribers:
            hub.states.publish(
                StateOut.of(observation).model_dump(mode="json")
            )

    controller.add_observation_listener(publish_state)

    ops = operations(controller)
    mcp = create_mcp(ops)
    mcp_app = mcp.http_app(path="/mcp")

    @contextlib.asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        hub.attach(asyncio.get_running_loop())
        try:
            yield
        finally:
            hub.detach()
            # Waits for the bot to close the emulator, off the event loop.
            await asyncio.to_thread(controller.close)

    app = FastAPI(
        title="Clash Royale Build-A-Bot",
        # Entered first, so it exits last: the bot stops after MCP's
        # sessions have closed.
        lifespan=combine_lifespans(lifespan, mcp_app.lifespan),
    )
    app.state.mcp = mcp

    @app.exception_handler(ApiError)
    def api_error(_request: Request, error: ApiError) -> JSONResponse:
        return JSONResponse(error.body(), status_code=error.status)

    router = APIRouter(prefix="/api")
    for operation in ops:
        _add_route(router, operation)

    @router.websocket("/states")
    async def states(websocket: WebSocket) -> None:
        await websocket.accept()
        with hub.states.subscribe() as queue:
            await _pump(websocket, queue, websocket.send_json)

    @router.websocket("/events")
    async def events(websocket: WebSocket) -> None:
        await websocket.accept()
        with hub.events.subscribe() as queue:
            await websocket.send_json(
                {"type": "status", "status": controller.status.value}
            )
            await _pump(websocket, queue, websocket.send_json)

    @router.websocket("/frames")
    async def frames(websocket: WebSocket) -> None:
        await websocket.accept()
        with hub.frames.subscribe() as queue:
            await _pump(websocket, queue, websocket.send_bytes)

    app.include_router(router)

    @app.get("/", include_in_schema=False)
    def web_ui() -> FileResponse:
        return FileResponse(WEB_UI_PATH, media_type="text/html")

    @app.get("/logo.png", include_in_schema=False)
    def logo() -> Response:
        # In the project folder, not the package, so an installed bot may
        # not have it. The page hides the image then.
        if not os.path.exists(LOGO_PATH):
            return Response(status_code=404)
        return FileResponse(LOGO_PATH, media_type="image/png")

    # Last, so it only gets what no route above matched. It serves /mcp.
    app.mount("/", mcp_app)
    return app
