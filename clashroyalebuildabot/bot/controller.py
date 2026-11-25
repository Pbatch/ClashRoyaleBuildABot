"""Starts, pauses and stops the bot on its own thread. No GUI code: the Qt
window and any future API both drive the bot through this."""

import threading
from collections.abc import Callable, Sequence
from concurrent.futures import TimeoutError as FutureTimeout
from enum import StrEnum

import numpy as np
from loguru import logger

from clashroyalebuildabot.actions.generic.action import Action
from clashroyalebuildabot.bot.bot import Bot, Observation
from clashroyalebuildabot.bot.plays import (
    Play,
    PlayRejected,
    PlayRequest,
    PlayResult,
    Reason,
)
from clashroyalebuildabot.bot.policy import Policy
from clashroyalebuildabot.config import Config, apply_changes
from clashroyalebuildabot.utils.error_handling import WikifiedError


class BotStatus(StrEnum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"


class BotController:
    """Owns at most one bot and the thread it runs on.

    Frame listeners are called on the bot's thread. Status listeners are
    called on whichever thread changed the status: the caller's for start,
    stop and pause, the bot's when it finishes. A GUI must move the work to
    its own thread before touching widgets.
    """

    def __init__(
        self,
        config: Config,
        actions: Sequence[type[Action]],
        policy: Policy | None = None,
    ) -> None:
        """Each bot plays with policy if given, otherwise as
        ``bot.policy`` in the config says."""
        self.config = config
        self.actions = actions
        self.policy = policy
        self._bot: Bot | None = None
        self._thread: threading.Thread | None = None
        self._stop_requested = False
        # Guards _bot, _thread and _stop_requested, which the bot's thread
        # and the caller's thread both change.
        self._lock = threading.Lock()
        # Serialises status emissions. Each reads the status while holding
        # it, so the last one listeners get always matches the current
        # status, even when the bot's thread and the caller's race.
        self._emit_lock = threading.RLock()
        self._frame_listeners: list[Callable[[np.ndarray], None]] = []
        self._status_listeners: list[Callable[[BotStatus], None]] = []
        self._config_listeners: list[Callable[[Config], None]] = []
        self._observation_listeners: list[Callable[[Observation], None]] = []
        self._observation: Observation | None = None
        # Serialises config changes, which may come from the GUI and the
        # API at once, and the snapshot each new bot takes.
        self._config_lock = threading.RLock()

    def add_frame_listener(
        self, listener: Callable[[np.ndarray], None]
    ) -> None:
        """Called with each annotated frame while show_images is on."""
        self._frame_listeners.append(listener)

    def add_observation_listener(
        self, listener: Callable[[Observation], None]
    ) -> None:
        """Called with every frame's Observation, on the bot's thread."""
        self._observation_listeners.append(listener)

    @property
    def observation(self) -> Observation | None:
        """The running bot's latest Observation. None until it has read a
        frame, and once it stops."""
        return self._observation

    @property
    def is_external(self) -> bool:
        """Whether the running bot plays what clients ask for."""
        bot = self._bot
        return bot is not None and bot.is_external

    def submit_play(
        self,
        play: Play,
        *,
        frame: int | None = None,
        max_age: float = 1.0,
        timeout: float = 2.0,
    ) -> PlayResult:
        """Ask the running bot to make play, on its next battle frame, and
        wait until it has. Raises PlayRejected with the reason it wasn't
        made, including TIMEOUT if the bot didn't get to it in timeout
        seconds (it then never will)."""
        bot = self._bot
        if bot is None or self._stop_requested:
            raise PlayRejected(Reason.NOT_RUNNING, "The bot isn't running.")
        if not bot.is_external:
            raise PlayRejected(
                Reason.BUILTIN_POLICY,
                "The bot is playing with its built-in policy. Set "
                "bot.policy to external, then restart it.",
            )
        if bot.is_paused:
            raise PlayRejected(Reason.PAUSED, "The bot is paused.")
        request = PlayRequest(play=play, frame=frame, max_age=max_age)
        future = bot.requests.submit(request)
        try:
            return future.result(timeout=timeout)
        except FutureTimeout:
            if future.cancel():
                raise PlayRejected(
                    Reason.TIMEOUT,
                    f"The bot didn't get to the play in {timeout} seconds.",
                ) from None
            # The bot took it just in time.
            return future.result()

    def add_config_listener(self, listener: Callable[[Config], None]) -> None:
        """Called with the config after every update_config(), on the
        thread that made the change."""
        self._config_listeners.append(listener)

    def update_config(self, changes: dict) -> None:
        """Apply some settings, e.g. ``{"bot": {"load_deck": True}}``. A
        running bot keeps the settings it started with. Raises pydantic's
        ValidationError, changing nothing, if any setting is invalid."""
        with self._config_lock:
            apply_changes(self.config, changes)
            for listener in self._config_listeners:
                listener(self.config)

    def add_status_listener(
        self, listener: Callable[[BotStatus], None]
    ) -> None:
        """Called with the new status after every change, including when
        the bot shuts down on its own after a crash."""
        self._status_listeners.append(listener)

    @property
    def is_running(self) -> bool:
        """True from start() until the bot has fully shut down."""
        return self._thread is not None

    @property
    def is_paused(self) -> bool:
        bot = self._bot
        return bot is not None and bot.is_paused

    @property
    def status(self) -> BotStatus:
        if not self.is_running:
            return BotStatus.STOPPED
        if self._stop_requested:
            return BotStatus.STOPPING
        if self.is_paused:
            return BotStatus.PAUSED
        return BotStatus.RUNNING

    def start(self) -> bool:
        """Start a bot with the current config. False if one is already
        running or still shutting down, so two never run at once."""
        with self._lock:
            if self._thread is not None:
                return False
            self._stop_requested = False
            # A copy, so changes made while it runs can't reach it halfway.
            with self._config_lock:
                config = self.config.model_copy(deep=True)
            self._thread = threading.Thread(
                target=self._run, args=(config,), daemon=True
            )
            self._thread.start()
        logger.info("Starting bot")
        self._emit_status()
        return True

    def stop(self) -> bool:
        """Ask the bot to stop. Returns at once, with the status STOPPING
        until it has. False if there was nothing to stop."""
        with self._lock:
            if self._thread is None or self._stop_requested:
                return False
            self._stop_requested = True
            bot = self._bot
        # If the bot is still being created, _run sees _stop_requested.
        if bot is not None:
            bot.stop()
        logger.info("Stopping bot")
        self._emit_status()
        return True

    def pause(self) -> bool:
        """False if there's no running bot to pause, or it's paused."""
        bot = self._bot
        if bot is None or self._stop_requested or bot.is_paused:
            return False
        bot.pause()
        self._emit_status()
        return True

    def resume(self) -> bool:
        """False if there's no paused bot to resume."""
        bot = self._bot
        if bot is None or self._stop_requested or not bot.is_paused:
            return False
        bot.resume()
        self._emit_status()
        return True

    def toggle_pause(self) -> bool:
        """Pause or resume. Returns whether the bot is now paused."""
        if not self.pause():
            self.resume()
        return self.is_paused

    def close(self, timeout: float = 10) -> None:
        """Stop the bot and wait for it. For app shutdown, so the screen
        recording doesn't outlive the app."""
        thread = self._thread
        self.stop()
        if thread is not None:
            thread.join(timeout=timeout)

    def _emit_status(self) -> None:
        with self._emit_lock:
            status = self.status
            for listener in self._status_listeners:
                listener(status)

    def _emit_frame(self, frame: np.ndarray) -> None:
        for listener in self._frame_listeners:
            listener(frame)

    def _emit_observation(self, observation: Observation) -> None:
        self._observation = observation
        for listener in self._observation_listeners:
            listener(observation)

    def _run(self, config: Config) -> None:
        """Runs on the bot's thread, with the config it started with."""
        try:
            bot = Bot(
                actions=self.actions,
                config=config,
                on_frame=self._emit_frame,
                on_observation=self._emit_observation,
                policy=self.policy,
            )
            with self._lock:
                self._bot = bot
                stop_now = self._stop_requested
            if stop_now:
                bot.stop()
            bot.run()
        except Exception as e:
            # Raising here would only reach the console, so log instead:
            # that reaches the console, the log file and the GUI.
            if not isinstance(e, WikifiedError):
                crash = WikifiedError("003", "Bot crashed.")
                crash.__cause__ = e
                e = crash
            logger.opt(exception=e).error(str(e).strip())
        finally:
            # Bot.run has closed the emulator by now, so a new bot can start.
            with self._lock:
                self._bot = None
                self._thread = None
                self._observation = None
                self._stop_requested = False
            logger.info("Bot stopped")
            self._emit_status()
