"""Starts, pauses and stops the bot on its own thread. No GUI code: the Qt
window and any future API both drive the bot through this."""

import threading
from collections.abc import Callable, Sequence
from enum import StrEnum

import numpy as np
from loguru import logger

from clashroyalebuildabot.actions.generic.action import Action
from clashroyalebuildabot.bot.bot import Bot
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
        self, config: Config, actions: Sequence[type[Action]]
    ) -> None:
        self.config = config
        self.actions = actions
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
        # Serialises config changes, which may come from the GUI and the
        # API at once, and the snapshot each new bot takes.
        self._config_lock = threading.RLock()

    def add_frame_listener(
        self, listener: Callable[[np.ndarray], None]
    ) -> None:
        """Called with each annotated frame while show_images is on."""
        self._frame_listeners.append(listener)

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

    def _run(self, config: Config) -> None:
        """Runs on the bot's thread, with the config it started with."""
        try:
            bot = Bot(
                actions=self.actions,
                config=config,
                on_frame=self._emit_frame,
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
                self._stop_requested = False
            logger.info("Bot stopped")
            self._emit_status()
