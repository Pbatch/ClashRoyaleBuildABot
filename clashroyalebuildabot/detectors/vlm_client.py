"""Client for a small vision-language model served by vLLM.

The model runs in a separate vLLM server and is reached through its
OpenAI-compatible API with the ``openai`` SDK, so the bot itself gains no
heavy dependencies. Each answer is shaped by a Pydantic model: the SDK sends
its JSON schema as the ``response_format`` and parses the reply into it, and
vLLM only lets the model produce output that fits, so the reply parses.
"""

import base64
from typing import Protocol, TypeVar

import numpy as np
import openai
from pydantic import BaseModel, ValidationError

from clashroyalebuildabot.config import ScreenDetectorConfig
from clashroyalebuildabot.utils.error_handling import WikifiedError
from clashroyalebuildabot.utils.image import encode_png, resize

T = TypeVar("T", bound=BaseModel)


class VisionError(Exception):
    """A question the model couldn't answer: the server is unreachable or
    returned an error, or the reply didn't fit the schema."""


class VisionClient(Protocol):
    def ask(self, image: np.ndarray, prompt: str, schema: type[T]) -> T:
        """Answer a question about an image, in the shape of ``schema``.

        Raises VisionError if there's no answer.
        """
        ...


def encode_image(image: np.ndarray, max_side: int = 652) -> str:
    """Encode an image as a PNG data URI, shrinking it to fit within
    ``max_side`` pixels on its longer side if needed."""
    height, width = image.shape[:2]
    scale = max_side / max(height, width)
    if scale < 1:
        size = (max(1, round(width * scale)), max(1, round(height * scale)))
        image = resize(image, size)
    data = base64.b64encode(encode_png(image)).decode("ascii")
    return f"data:image/png;base64,{data}"


class VLMClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float = 10.0,
        max_side: int = 652,
        max_tokens: int = 64,
    ) -> None:

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_side = max_side
        # Caps the reply's length. The bot's answers are a few short fields;
        # a larger schema needs more, or its JSON is cut off.
        self.max_tokens = max_tokens
        self.client = openai.OpenAI(
            base_url=self.base_url + "/v1",
            api_key="unused",  # vLLM doesn't check it, but the SDK needs one
            timeout=timeout,
            # A failed reading is retried on the next interval anyway, with
            # a newer frame, so retrying the old one would only add lag.
            max_retries=0,
        )

    def check(self) -> None:
        """Raise if the vLLM server can't be reached."""
        try:
            self.client.models.list()
        except openai.OpenAIError as e:
            raise WikifiedError(
                "010",
                f"Can't reach the vision model server at {self.base_url}. "
                "Start it with `uv run python -m "
                "clashroyalebuildabot.vlm_server` before starting the bot.",
            ) from e

    def ask(self, image: np.ndarray, prompt: str, schema: type[T]) -> T:
        try:
            completion = self.client.chat.completions.parse(
                model=self.model,
                temperature=0,
                max_tokens=self.max_tokens,
                response_format=schema,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": encode_image(image, self.max_side)
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                # Answer directly instead of reasoning first.
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": False}
                },
            )
        except (openai.OpenAIError, ValidationError) as e:
            raise VisionError(str(e)) from e
        answer = completion.choices[0].message.parsed
        if answer is None:
            raise VisionError("The model didn't answer")
        return answer


def make_client(config: ScreenDetectorConfig) -> VLMClient:
    """Build a client from the ``screen_detector`` config and check that its
    server is up."""
    client = VLMClient(
        base_url=config.base_url,
        model=config.model,
        timeout=config.timeout,
    )
    client.check()
    return client
