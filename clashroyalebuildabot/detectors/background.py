"""Run a slow detector in the background and keep its latest result."""

import threading
import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from typing import TypeVar

import numpy as np

T = TypeVar("T")


class LatestResult[T]:
    """Compute a value from frames in the background, at most every
    ``interval`` seconds, and hand back the most recent one.

    ``run`` never blocks, so the bot keeps its frame rate while a slow model
    thinks. Each answer describes a frame from a moment ago, not the current
    one. After ``max_age`` seconds without a fresh answer, ``run`` returns
    ``default`` instead; with ``max_age=None`` the last answer never expires.
    """

    def __init__(
        self,
        compute: Callable[[np.ndarray], T],
        default: T,
        interval: float = 1.0,
        max_age: float | None = 5.0,
        name: str = "background",
    ) -> None:
        self.compute = compute
        self.default = default
        self.interval = interval
        self.max_age = max_age

        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix=name
        )
        self._lock = threading.Lock()
        self._pending: Future | None = None
        self._last_submit = float("-inf")
        self._value = default
        self._value_time = float("-inf")
        # Bumped by reset(), so an answer to a frame from before the reset
        # isn't stored afterwards.
        self._generation = 0

    def _refresh(self, image: np.ndarray, generation: int) -> None:
        # Runs on the worker thread and stores its own answer. A done
        # callback could instead run inline on the caller, which already
        # holds the lock, if the request finished before it was attached.
        value = self.compute(image)
        with self._lock:
            if generation == self._generation:
                self._value = value
                self._value_time = time.monotonic()

    def run(self, image: np.ndarray) -> T:
        """Return the latest answer, refreshing it in the background."""
        now = time.monotonic()
        with self._lock:
            idle = self._pending is None or self._pending.done()
            if idle and now - self._last_submit >= self.interval:
                self._last_submit = now
                self._pending = self._executor.submit(
                    self._refresh, image.copy(), self._generation
                )
            if self.max_age is not None and (
                now - self._value_time > self.max_age
            ):
                return self.default
            return self._value

    def latest(self) -> T:
        """The current answer, without asking for a new one."""
        with self._lock:
            return self._value

    def reset(self) -> None:
        """Forget the current answer and any request still in flight."""
        with self._lock:
            self._generation += 1
            self._value = self.default
            self._value_time = float("-inf")
            self._last_submit = float("-inf")

    def wait(self, timeout: float | None = None) -> None:
        """Block until any in-flight request finishes."""
        with self._lock:
            pending = self._pending
        if pending is not None:
            pending.result(timeout=timeout)

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
