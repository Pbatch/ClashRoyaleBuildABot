"""Screen detection with OneJev, a small vision decision model.

OneJev runs in a separate Flide server (``flide serve``) and is reached over
its System One API, so the bot itself gains no heavy dependencies. Each
request asks multiple-choice questions about a screenshot and gets back a
calibrated probability for every option.

Inference takes a few hundred milliseconds, so ``run`` never blocks: it
hands the latest frame to a background worker at most once per ``interval``
seconds and returns the most recent answer.
"""

import base64
import io
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Protocol

import requests
from loguru import logger
from PIL import Image

from clashroyalebuildabot.namespaces import Screens
from clashroyalebuildabot.namespaces.screens import Screen
from clashroyalebuildabot.utils.error_handling import WikifiedError

SCREEN_QUESTION = "screen"
SCREEN_CRITERIA = {
    "in_game": "a battle in progress: the arena with towers, and a hand "
    "of cards with an elixir bar at the bottom",
    "lobby": "the main menu, with a large yellow Battle button and "
    "navigation tabs at the bottom",
    "end_of_game": "the battle results screen, with crowns or a winner "
    "banner and a blue OK button",
    "matchmaking": "searching for an opponent: a Searching for opponent "
    "banner and a red Cancel button",
    "loading": "a loading screen: the Clash Royale logo over game artwork, "
    "with a loading progress bar at the bottom",
    "vs": "the versus screen before a battle: both players' names and "
    "trophies, with a VS badge between them",
    "match_over": "the arena just after the battle ends, with a Match Over! "
    "banner and no results yet",
    "unknown": "anything else, such as a popup, shop or chest opening",
}
# Screens the bot only waits through are told apart for the model's sake,
# so it isn't pushed into a wrong label, but they all mean "do nothing".
SCREEN_LABELS = {
    "in_game": Screens.IN_GAME,
    "lobby": Screens.LOBBY,
    "end_of_game": Screens.END_OF_GAME,
    "matchmaking": Screens.UNKNOWN,
    "loading": Screens.UNKNOWN,
    "vs": Screens.UNKNOWN,
    "match_over": Screens.UNKNOWN,
    "unknown": Screens.UNKNOWN,
}

# The results screen has two layouts, which need the OK button tapped in
# different places. Asked in the same request, so it costs little extra.
OK_QUESTION = "ok_button"
OK_CRITERIA = {
    "right": "the blue OK button is on the right half of the screen, "
    "next to another button",
    "centre": "the blue OK button is on its own in the middle of the screen",
}
OK_LABELS = {
    "right": Screens.END_OF_GAME,
    "centre": Screens.BYPASS_END_OF_GAME,
}

Answers = dict[str, dict[str, float]]


class DecisionClient(Protocol):
    def ask(self, image: Image.Image) -> Answers:
        """Probability of each option, keyed by question then option."""
        ...


def encode_image(image: Image.Image, max_side=512) -> str:
    """Downscale and encode an image as a PNG data URI."""
    image = image.convert("RGB")
    image.thumbnail((max_side, max_side))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    data = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{data}"


class OneJevClient:
    """Talks to a OneJev model served by Flide's System One API."""

    def __init__(self, base_url, timeout=10.0, max_side=512):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_side = max_side
        self.session = requests.Session()

    def check(self):
        """Raise if the Flide server can't be reached."""
        try:
            self.session.get(self.base_url, timeout=self.timeout)
        except requests.RequestException as e:
            raise WikifiedError(
                "010",
                f"Can't reach the OneJev screen detector at {self.base_url}. "
                "Start it with `flide serve` before starting the bot.",
            ) from e

    def ask(self, image: Image.Image) -> Answers:
        payload = {
            "state": {
                "task": "Identify which screen of the mobile game Clash "
                "Royale is shown",
                "screen": "<image:1>",
            },
            "media": [
                {"type": "image", "data": encode_image(image, self.max_side)}
            ],
            "questions": {
                SCREEN_QUESTION: {
                    "type": "choice",
                    "instructions": "Which screen is this?",
                    "criteria": SCREEN_CRITERIA,
                },
                OK_QUESTION: {
                    "type": "choice",
                    "instructions": "If there is a blue OK button, where "
                    "is it?",
                    "criteria": OK_CRITERIA,
                },
            },
        }
        response = self.session.post(
            self.base_url + "/v1/systemone",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        answers = response.json()["answers"]
        return {
            name: {
                option: float(p)
                for option, p in answers[name]["probabilities"].items()
            }
            for name in (SCREEN_QUESTION, OK_QUESTION)
        }


def most_likely(probabilities: dict[str, float]) -> tuple[str, float]:
    label = max(probabilities, key=lambda k: probabilities[k])
    return label, probabilities[label]


class ScreenDetector:
    def __init__(
        self,
        client: DecisionClient,
        interval=1.0,
        max_age=5.0,
        min_confidence=0.5,
    ):
        self.client = client
        self.interval = interval
        self.max_age = max_age
        self.min_confidence = min_confidence

        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="screen-detector"
        )
        self._lock = threading.Lock()
        self._pending: Future | None = None
        self._last_submit = float("-inf")
        self._screen = Screens.UNKNOWN
        self._screen_time = 0.0

    @classmethod
    def from_config(cls, config: dict | None) -> "ScreenDetector":
        """Build from the ``screen_detector`` config, checking the server."""
        config = config or {}
        client = OneJevClient(
            base_url=config.get("base_url", "http://localhost:8000"),
            timeout=config.get("timeout", 10.0),
        )
        client.check()
        return cls(
            client,
            interval=config.get("interval", 1.0),
            max_age=config.get("max_age", 5.0),
            min_confidence=config.get("min_confidence", 0.5),
        )

    def classify(self, image: Image.Image) -> Screen:
        """Blocking classification of one frame."""
        try:
            answers = self.client.ask(image)
            label, p = most_likely(answers[SCREEN_QUESTION])
            screen = SCREEN_LABELS.get(label, Screens.UNKNOWN)
            if screen == Screens.END_OF_GAME:
                position, _ = most_likely(answers[OK_QUESTION])
                screen = OK_LABELS.get(position, Screens.END_OF_GAME)
        except (
            requests.RequestException,
            KeyError,
            TypeError,
            ValueError,
        ) as e:
            logger.warning(f"Screen detection failed: {e}")
            return Screens.UNKNOWN
        if p < self.min_confidence:
            return Screens.UNKNOWN
        return screen

    def _refresh(self, image: Image.Image):
        # Runs on the worker thread and stores its own answer. A done
        # callback could instead run inline on the caller, which already
        # holds the lock, if the request finished before it was attached.
        screen = self.classify(image)
        with self._lock:
            self._screen = screen
            self._screen_time = time.monotonic()

    def run(self, image: Image.Image) -> Screen:
        """Return the latest answer, refreshing it in the background."""
        now = time.monotonic()
        with self._lock:
            idle = self._pending is None or self._pending.done()
            if idle and now - self._last_submit >= self.interval:
                self._last_submit = now
                self._pending = self._executor.submit(
                    self._refresh, image.copy()
                )
            if now - self._screen_time > self.max_age:
                return Screens.UNKNOWN
            return self._screen

    def wait(self, timeout: float | None = None):
        """Block until any in-flight request finishes."""
        with self._lock:
            pending = self._pending
        if pending is not None:
            pending.result(timeout=timeout)

    def close(self):
        self._executor.shutdown(wait=False, cancel_futures=True)
