"""What the API can do, written once and served twice: as REST routes under
/api and as MCP tools under /mcp. Each operation is a plain function. Its
name, arguments, return type and docstring become both the route's OpenAPI
entry and the tool's schema, so the two can't drift apart.

Operations raise ApiError rather than anything HTTP- or MCP-specific, and
return Jpeg for an image. Each front end turns those into its own form.
"""

import json
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from types import FunctionType
from typing import Any, Literal

import cv2
import numpy as np
from pydantic import BaseModel, ValidationError

from clashroyalebuildabot.api.schemas import (
    ActionsOut,
    CardStatsOut,
    MetaOut,
    PlayIn,
    PlayOut,
    RejectionOut,
    StateOut,
    UnitStatsOut,
    meta,
)
from clashroyalebuildabot.bot.controller import BotController, BotStatus
from clashroyalebuildabot.bot.plays import Play, PlayRejected, Reason
from clashroyalebuildabot.config import save_config as write_config
from clashroyalebuildabot.constants import paths
from clashroyalebuildabot.game import game_data
from clashroyalebuildabot.game.screens import ScreenName
from clashroyalebuildabot.utils.error_handling import WikifiedError

JPEG_QUALITY = 80


class ApiError(Exception):
    """An operation that couldn't be done, with the HTTP status it maps to.

    With a reason (one of plays.Reason), REST sends
    ``{"reason", "message"}``. Without one, it sends ``{"detail": detail}``,
    where detail defaults to the message. MCP sends the message, prefixed
    with the reason if there is one.
    """

    def __init__(
        self,
        status: int,
        message: str,
        *,
        reason: str | None = None,
        detail: Any = None,  # noqa: ANN401
    ) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.reason = reason
        self.detail = message if detail is None else detail

    def body(self) -> dict[str, Any]:
        if self.reason is not None:
            return {"reason": self.reason, "message": self.message}
        return {"detail": self.detail}

    def tool_message(self) -> str:
        if self.reason is not None:
            return f"{self.reason}: {self.message}"
        return self.message


@dataclass(frozen=True)
class Jpeg:
    """An image an operation returns: image/jpeg over REST, image content
    over MCP."""

    data: bytes


def encode_jpeg(frame: np.ndarray) -> bytes:
    """An RGB frame as JPEG bytes."""
    bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    ok, buffer = cv2.imencode(
        ".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
    )
    if not ok:
        raise ValueError("Couldn't encode the frame as JPEG.")
    return buffer.tobytes()


@dataclass(frozen=True)
class Operation:
    # A plain function, as both front ends read its signature and name.
    fn: FunctionType
    method: Literal["GET", "POST", "PATCH"]
    # Under /api.
    path: str
    # Doesn't change anything: MCP's readOnlyHint.
    read_only: bool = False
    # OpenAPI's description of the errors, by status.
    responses: dict[int | str, dict[str, Any]] = field(default_factory=dict)

    @property
    def name(self) -> str:
        """The tool's name and the route's operationId."""
        return self.fn.__name__


class StatusOut(BaseModel):
    status: BotStatus


class LatestFrame:
    """The newest annotated frame, kept for screenshot. Cleared when the bot
    stops, so an old battle isn't mistaken for the current one."""

    def __init__(self, controller: BotController) -> None:
        self._frame: np.ndarray | None = None
        self._lock = threading.Lock()
        controller.add_frame_listener(self._set)
        controller.add_status_listener(self._on_status)

    def _set(self, frame: np.ndarray | None) -> None:
        with self._lock:
            self._frame = frame

    def _on_status(self, status: BotStatus) -> None:
        if status == BotStatus.STOPPED:
            self._set(None)

    def get(self) -> np.ndarray | None:
        with self._lock:
            return self._frame


def _stats(get: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return get()
    except game_data.UnknownName as e:
        raise ApiError(404, str(e.args[0])) from e
    except game_data.BadLevel as e:
        raise ApiError(422, str(e)) from e


def _validation_message(error: ValidationError) -> str:
    problems = "; ".join(
        f"{'.'.join(str(part) for part in e['loc'])}: {e['msg']}"
        for e in error.errors()
    )
    return f"Invalid settings, so none were changed. {problems}"


def operations(controller: BotController) -> list[Operation]:
    """Everything the API can do with controller."""
    latest_frame = LatestFrame(controller)

    def changed_or_conflict(changed: bool, action: str) -> StatusOut:
        status = controller.status
        if not changed:
            raise ApiError(409, f"Can't {action} while the bot is {status}.")
        return StatusOut(status=status)

    def get_status() -> StatusOut:
        """The bot's status: stopped, running, paused or stopping."""
        return StatusOut(status=controller.status)

    def start() -> StatusOut:
        """Start the bot. It connects to the device, then plays battles
        until stopped: with its built-in policy, or with what clients send
        to play when bot.policy is external. Fails if it isn't stopped."""
        return changed_or_conflict(controller.start(), "start")

    def stop() -> StatusOut:
        """Stop the bot. It finishes its current step first, so the status
        is stopping for a moment before stopped."""
        return changed_or_conflict(controller.stop(), "stop")

    def pause() -> StatusOut:
        """Pause the bot. It stops playing but stays connected."""
        return changed_or_conflict(controller.pause(), "pause")

    def resume() -> StatusOut:
        """Resume a paused bot."""
        return changed_or_conflict(controller.resume(), "resume")

    def get_config() -> dict[str, Any]:
        """Every setting, in the sections of default_config.yaml."""
        return controller.config.model_dump()

    def update_config(changes: dict[str, Any]) -> dict[str, Any]:
        """Change some settings, e.g. {"bot": {"policy": "external"}}, and
        return them all. Only the settings sent change. A running bot keeps
        the settings it started with, apart from bot.log_level: stop and
        start it to use the rest. If any setting is invalid, none change.
        Changes aren't saved to config.yaml."""
        try:
            controller.update_config(changes)
        except ValidationError as e:
            raise ApiError(
                422,
                _validation_message(e),
                detail=json.loads(e.json(include_url=False)),
            ) from e
        return controller.config.model_dump()

    def save_config() -> dict[str, Any]:
        """Save the current settings to config.yaml, so the bot starts with
        them next time. Only settings that differ from the defaults are
        written. Returns every setting."""
        try:
            write_config(controller.config, paths.USER_CONFIG_PATH)
        except WikifiedError as e:
            raise ApiError(500, f"Couldn't save config.yaml: {e}") from e
        return controller.config.model_dump()

    def get_meta() -> MetaOut:
        """What doesn't change during a battle: the tile grid and where the
        towers stand, the bot's deck, every card and unit by name, the
        elixir timeline, tower stats and card levels. Read it once."""
        deck = [action.CARD for action in controller.actions]
        return meta(deck, controller.config.bot.policy)

    def get_unit(
        name: str, level: int = game_data.DEFAULT_LEVEL
    ) -> UnitStatsOut:
        """A unit's stats at a level (default 11): hitpoints, damage, speed,
        range and more. Units are named as in the state's detections."""
        return UnitStatsOut.model_validate(
            _stats(lambda: game_data.unit_stats(name, level))
        )

    def get_card(name: str, level: int | None = None) -> CardStatsOut:
        """A card's cost, rarity and type, what it deploys with each unit's
        stats, and a spell's damage. Without level: 11, or the card's
        lowest level if that's higher."""
        return CardStatsOut.model_validate(
            _stats(lambda: game_data.card_stats(name, level))
        )

    def get_state() -> StateOut:
        """The game as of the latest frame: the screen, and in a battle the
        elixir, timer, towers, hand and the units detected on each side.
        Detections are noisy, so don't react to one frame alone. Pass its
        frame to play. Fails until the bot has read a frame."""
        observation = controller.observation
        if observation is None:
            raise ApiError(
                404,
                "No state yet: the bot isn't running, or hasn't read a frame.",
            )
        return StateOut.of(observation)

    def get_actions() -> ActionsOut:
        """The cards that can be played now, each with every tile it can go
        on, or why nothing can be (blocked_by)."""
        observation = controller.observation
        if controller.status not in (BotStatus.RUNNING, BotStatus.PAUSED):
            return ActionsOut(
                frame=None, blocked_by=Reason.NOT_RUNNING, cards=[]
            )
        frame = observation.frame if observation else None
        if not controller.is_external:
            blocked: str | None = Reason.BUILTIN_POLICY
        elif controller.is_paused:
            blocked = Reason.PAUSED
        elif observation is None:
            blocked = Reason.NOT_RUNNING
        elif observation.state.screen != ScreenName.IN_GAME:
            blocked = Reason.NOT_IN_BATTLE
        else:
            cards = ActionsOut.legal_cards(observation.state)
            if observation.pending is not None:
                blocked = Reason.PLAY_PENDING
            elif not cards:
                blocked = "no_affordable_card"
            else:
                blocked = None
            return ActionsOut(frame=frame, blocked_by=blocked, cards=cards)
        return ActionsOut(frame=frame, blocked_by=blocked, cards=[])

    def play(request: PlayIn) -> PlayOut:
        """Play the card at hand_index (0-3, left to right) on a tile, and
        wait until the bot has tapped it. Needs bot.policy external. Pass
        the frame the decision was made on: the play is refused as stale if
        that frame is more than max_age seconds old (default 1) when the bot
        gets to it. A slow decider should raise max_age, or leave frame
        out. If it isn't played, the reason says why (not_enough_elixir,
        bad_tile, play_pending, ...)."""
        try:
            result = controller.submit_play(
                Play(request.hand_index, request.tile_x, request.tile_y),
                frame=request.frame,
                max_age=request.max_age,
            )
        except PlayRejected as e:
            raise ApiError(409, e.message, reason=e.reason) from e
        return PlayOut.of(result)

    def screenshot() -> Jpeg:
        """The latest annotated frame, as a JPEG: the screen with what the
        bot detected drawn on it. Needs visuals.show_images on."""
        frame = latest_frame.get()
        if frame is None:
            raise ApiError(
                404,
                "No frame yet: the bot isn't running, or visuals.show_images "
                "is off.",
            )
        return Jpeg(encode_jpeg(frame))

    rejection = {409: {"model": RejectionOut, "description": "Not played."}}
    return [
        Operation(get_status, "GET", "/status", read_only=True),
        Operation(start, "POST", "/start"),
        Operation(stop, "POST", "/stop"),
        Operation(pause, "POST", "/pause"),
        Operation(resume, "POST", "/resume"),
        Operation(get_config, "GET", "/config", read_only=True),
        Operation(update_config, "PATCH", "/config"),
        Operation(save_config, "POST", "/config/save"),
        Operation(get_meta, "GET", "/meta", read_only=True),
        Operation(
            get_unit,
            "GET",
            "/units/{name}",
            read_only=True,
            responses={404: {"description": "No such unit."}},
        ),
        Operation(
            get_card,
            "GET",
            "/cards/{name}",
            read_only=True,
            responses={404: {"description": "No such card."}},
        ),
        Operation(
            get_state,
            "GET",
            "/state",
            read_only=True,
            responses={404: {"description": "No frame read yet."}},
        ),
        Operation(get_actions, "GET", "/actions", read_only=True),
        Operation(play, "POST", "/play", responses=rejection),
        Operation(
            screenshot,
            "GET",
            "/screenshot.jpg",
            read_only=True,
            responses={
                200: {"content": {"image/jpeg": {}}},
                404: {"description": "No frame yet."},
            },
        ),
    ]
