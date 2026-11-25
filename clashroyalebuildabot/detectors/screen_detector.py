"""Screen detection with a small vision-language model.

The model (Qwen3.5-0.8B by default, served by vLLM) is asked which screen a
screenshot shows. Its answer is constrained to the ``ScreenAnswer`` schema,
so it can only name one of the known screens.

Inference takes a few hundred milliseconds, so ``run`` never blocks: it
hands the latest frame to a background worker at most once per ``interval``
seconds and returns the most recent answer.
"""

from typing import Literal

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field, field_validator

from clashroyalebuildabot.config import ScreenDetectorConfig
from clashroyalebuildabot.detectors.background import LatestResult
from clashroyalebuildabot.detectors.vlm_client import (
    VisionClient,
    VisionError,
    make_client,
)
from clashroyalebuildabot.game import ScreenName, Screens

# The screens the model chooses between: those with a description, in the
# order screens.py lists them. BYPASS_END_OF_GAME has none: it's END_OF_GAME
# with the OK button in the centre, so it comes from the ``ok_button`` answer.
OFFERED_SCREENS = tuple(
    screen for screen in Screens.all() if screen.description
)
OFFERED_NAMES = tuple(str(screen.name) for screen in OFFERED_SCREENS)

# The results screen has two layouts, which need the OK button tapped in
# different places. With no OK button yet, the results are still appearing,
# so the bot waits rather than tap blind.
OK_BUTTON_SCREENS = {
    "right": ScreenName.END_OF_GAME,
    "centre": ScreenName.BYPASS_END_OF_GAME,
    "none": ScreenName.UNKNOWN,
}


class ScreenAnswer(BaseModel):
    # The enum in the schema limits the model to these names.
    screen: str = Field(
        description="which screen of the game is shown",
        json_schema_extra={"enum": list(OFFERED_NAMES)},
    )
    ok_button: Literal["right", "centre", "none"] = Field(
        description="where the blue OK button is: on the right half next to "
        "another button, on its own in the centre, or none if there isn't one"
    )

    @field_validator("screen")
    @classmethod
    def _known_screen(cls, name: str) -> str:
        if name not in OFFERED_NAMES:
            raise ValueError(f"unknown screen {name!r}")
        return name


PROMPT = (
    "This is a screenshot of the mobile game Clash Royale. Which screen is "
    "it?\n"
    + "\n".join(
        f"- {screen.name}: {screen.description}" for screen in OFFERED_SCREENS
    )
    + "\nAlso say where the blue OK button is, if there is one. Answer in JSON."
)


class ScreenDetector:
    def __init__(
        self,
        client: VisionClient,
        interval: float = 1.0,
        max_age: float | None = 5.0,
    ) -> None:
        self.client = client
        self._latest = LatestResult(
            self.classify,
            default=ScreenName.UNKNOWN,
            interval=interval,
            max_age=max_age,
            name="screen-detector",
        )

    @classmethod
    def from_config(
        cls,
        config: ScreenDetectorConfig,
        client: VisionClient | None = None,
    ) -> "ScreenDetector":
        """Build from the ``screen_detector`` config.

        Without a ``client``, one is made from the config and the server is
        checked.
        """
        if client is None:
            client = make_client(config)
        return cls(
            client,
            interval=config.interval,
            max_age=config.max_age,
        )

    def classify(self, image: np.ndarray) -> ScreenName:
        """Blocking classification of one frame."""
        try:
            answer = self.client.ask(image, PROMPT, ScreenAnswer)
        except VisionError as e:
            logger.warning(f"Screen detection failed: {e}")
            return ScreenName.UNKNOWN
        screen = ScreenName(answer.screen)
        if screen == ScreenName.END_OF_GAME:
            screen = OK_BUTTON_SCREENS[answer.ok_button]
        return screen

    def run(self, image: np.ndarray) -> ScreenName:
        """Return the latest answer, refreshing it in the background."""
        return self._latest.run(image)

    def wait(self, timeout: float | None = None) -> None:
        self._latest.wait(timeout)

    def close(self) -> None:
        self._latest.close()
