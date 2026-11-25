"""An HTTP and WebSocket API over the BotController.

REST, under /api:
    GET   /status   {"status": "stopped" | "running" | "paused" | "stopping"}
    POST  /start, /stop, /pause, /resume
                    The new status, or 409 if that isn't possible now.
    GET   /config   All settings.
    PATCH /config   Some settings, e.g. {"bot": {"load_deck": true}}. A bot
                    already running keeps its settings; they apply from the
                    next start. 422, and nothing changed, if any is invalid.

WebSockets, under /api:
    /events   JSON: the current status on connect, then
              {"type": "status", "status": ...} on each change and
              {"type": "log", "time", "level", "source", "message"}.
    /frames   Binary: each annotated frame as a JPEG, while
              visuals.show_images is on. Slow clients skip frames.

There's no authentication: anyone who can reach the server can drive the
device, so serve it on localhost unless the network is trusted.
"""

import asyncio
import contextlib
import json
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any

import anyio
import cv2
import numpy as np
from fastapi import APIRouter, Body, FastAPI, HTTPException, WebSocket
from fastapi.websockets import WebSocketDisconnect
from pydantic import BaseModel, ValidationError

from clashroyalebuildabot.api.events import EventHub
from clashroyalebuildabot.bot.controller import BotController, BotStatus

JPEG_QUALITY = 80


class StatusResponse(BaseModel):
    status: BotStatus


def encode_jpeg(frame: np.ndarray) -> bytes:
    """An RGB frame as JPEG bytes."""
    bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    ok, buffer = cv2.imencode(
        ".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
    )
    if not ok:
        raise ValueError("Couldn't encode the frame as JPEG.")
    return buffer.tobytes()


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


def create_app(
    controller: BotController, hub: EventHub | None = None
) -> FastAPI:
    """The API for controller. Pass the hub whose log_sink is attached to
    the logger, so log lines reach /events.

    Shutting the app down stops the bot.
    """
    hub = hub or EventHub()

    controller.add_status_listener(
        lambda status: hub.events.publish(
            {"type": "status", "status": status.value}
        )
    )

    def publish_frame(frame: np.ndarray) -> None:
        # Encoded on the bot's thread, so only when someone is watching.
        if hub.frames.has_subscribers:
            hub.frames.publish(encode_jpeg(frame))

    controller.add_frame_listener(publish_frame)

    @contextlib.asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        hub.attach(asyncio.get_running_loop())
        try:
            yield
        finally:
            hub.detach()
            # Waits for the bot to close the emulator, off the event loop.
            await asyncio.to_thread(controller.close)

    app = FastAPI(title="Clash Royale Build-A-Bot", lifespan=lifespan)
    router = APIRouter(prefix="/api")

    def status_or_conflict(changed: bool, action: str) -> StatusResponse:
        status = controller.status
        if not changed:
            raise HTTPException(
                409, f"Can't {action} while the bot is {status}."
            )
        return StatusResponse(status=status)

    @router.get("/status")
    def get_status() -> StatusResponse:
        return StatusResponse(status=controller.status)

    @router.post("/start")
    def start() -> StatusResponse:
        return status_or_conflict(controller.start(), "start")

    @router.post("/stop")
    def stop() -> StatusResponse:
        return status_or_conflict(controller.stop(), "stop")

    @router.post("/pause")
    def pause() -> StatusResponse:
        return status_or_conflict(controller.pause(), "pause")

    @router.post("/resume")
    def resume() -> StatusResponse:
        return status_or_conflict(controller.resume(), "resume")

    @router.get("/config")
    def get_config() -> dict[str, Any]:
        return controller.config.model_dump()

    @router.patch("/config")
    def patch_config(
        changes: dict[str, Any] = Body(...),  # noqa: B008
    ) -> dict[str, Any]:
        try:
            controller.update_config(changes)
        except ValidationError as e:
            raise HTTPException(
                422, json.loads(e.json(include_url=False))
            ) from e
        return controller.config.model_dump()

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
    return app
