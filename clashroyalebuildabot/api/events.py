"""Hands events from the bot's threads to WebSocket clients on the server's
event loop."""

import asyncio
import contextlib
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from loguru import Message


class Channel:
    """Fans items out to subscribers, each with its own bounded queue.

    ``publish`` may be called from any thread. A subscriber that falls
    behind loses its oldest items rather than slowing the bot down.
    """

    def __init__(self, queue_size: int) -> None:
        self.queue_size = queue_size
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queues: set[asyncio.Queue[Any]] = set()

    def attach(self, loop: asyncio.AbstractEventLoop) -> None:
        """Deliver to subscribers on loop, the server's event loop."""
        self._loop = loop

    def detach(self) -> None:
        self._loop = None

    @property
    def has_subscribers(self) -> bool:
        return bool(self._queues)

    @contextlib.contextmanager
    def subscribe(self) -> Generator[asyncio.Queue[Any]]:
        """A queue receiving every item published while the block runs.
        Must be entered on the attached loop."""
        queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=self.queue_size)
        self._queues.add(queue)
        try:
            yield queue
        finally:
            self._queues.discard(queue)

    def publish(self, item: object) -> None:
        loop = self._loop
        if loop is None or not self._queues:
            return
        # The loop closes on shutdown, possibly while the bot still runs.
        with contextlib.suppress(RuntimeError):
            loop.call_soon_threadsafe(self._deliver, item)

    def _deliver(self, item: object) -> None:
        """Runs on the loop, so the queues aren't touched across threads."""
        for queue in list(self._queues):
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(item)


class EventHub:
    """The API's two streams: JSON events (status changes and log lines),
    and annotated frames as JPEG bytes."""

    def __init__(self) -> None:
        self.events = Channel(queue_size=1000)
        # Only the newest frame matters to a viewer.
        self.frames = Channel(queue_size=1)

    def attach(self, loop: asyncio.AbstractEventLoop) -> None:
        self.events.attach(loop)
        self.frames.attach(loop)

    def detach(self) -> None:
        self.events.detach()
        self.frames.detach()

    def log_sink(self, message: "Message") -> None:
        """A loguru sink. Mustn't log itself, or it would loop."""
        record = message.record
        self.events.publish(
            {
                "type": "log",
                "time": record["time"].isoformat(),
                "level": record["level"].name,
                "source": (
                    f"{record['module']}:{record['function']}:{record['line']}"
                ),
                "message": record["message"],
            }
        )
