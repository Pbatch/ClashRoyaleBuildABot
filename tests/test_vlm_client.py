"""The client's requests and replies, through the real openai SDK, with a
fake vLLM server behind a mock HTTP transport."""

import json

import httpx2
import openai
import pytest
from PIL import Image
from pydantic import BaseModel

from clashroyalebuildabot.detectors.vlm_client import VisionError, VLMClient
from clashroyalebuildabot.utils.error_handling import WikifiedError


class Answer(BaseModel):
    hp: int


class FakeVLLM:
    """Answers chat completions with ``content``, or fails with ``status``
    or by refusing connections."""

    def __init__(self, content='{"hp": 931}', status=200, down=False):
        self.content = content
        self.status = status
        self.down = down
        self.requests: list[tuple[str, dict]] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        if self.down:
            raise httpx2.ConnectError("refused", request=request)
        body = json.loads(request.content) if request.content else {}
        self.requests.append((str(request.url), body))
        if self.status != 200:
            return httpx2.Response(self.status, json={"error": "boom"})
        if request.url.path == "/v1/models":
            return httpx2.Response(200, json={"object": "list", "data": []})
        return httpx2.Response(
            200,
            json={
                "id": "1",
                "object": "chat.completion",
                "created": 0,
                "model": body["model"],
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": self.content,
                        },
                    }
                ],
            },
        )


def client_with(server: FakeVLLM) -> VLMClient:
    client = VLMClient("http://vllm:8001/", "Qwen/Qwen3.5-0.8B")
    client.client = client.client.with_options(
        http_client=httpx2.Client(transport=httpx2.MockTransport(server))
    )
    return client


def image():
    return Image.new("RGB", (368, 652), (40, 40, 40))


def test_request_sends_schema_image_and_prompt():
    server = FakeVLLM()
    answer = client_with(server).ask(image(), "Read the HP", Answer)
    assert answer == Answer(hp=931)

    url, body = server.requests[0]
    assert url == "http://vllm:8001/v1/chat/completions"
    assert body["model"] == "Qwen/Qwen3.5-0.8B"
    assert body["temperature"] == 0
    assert body["max_tokens"] == 64
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    response_format = body["response_format"]
    assert response_format["type"] == "json_schema"
    schema = response_format["json_schema"]["schema"]
    assert schema["properties"] == Answer.model_json_schema()["properties"]
    assert schema["additionalProperties"] is False
    content = body["messages"][0]["content"]
    assert content[0]["image_url"]["url"].startswith("data:image/png;base64,")
    assert content[1] == {"type": "text", "text": "Read the HP"}


@pytest.mark.parametrize(
    "server",
    [
        FakeVLLM(content='{"hp": "lots"}'),  # breaks the schema
        FakeVLLM(content='{"hp": 9'),  # cut off
        FakeVLLM(status=500),
        FakeVLLM(down=True),
    ],
    ids=["bad reply", "cut-off reply", "server error", "server down"],
)
def test_failures_raise_vision_error(server):
    with pytest.raises(VisionError):
        client_with(server).ask(image(), "Read the HP", Answer)


def test_failed_request_is_not_retried():
    server = FakeVLLM(status=500)
    with pytest.raises(VisionError):
        client_with(server).ask(image(), "Read the HP", Answer)
    assert len(server.requests) == 1


def test_check_passes_when_server_is_up():
    server = FakeVLLM()
    client_with(server).check()
    assert server.requests[0][0] == "http://vllm:8001/v1/models"


def test_unreachable_server_raises_e010():
    with pytest.raises(WikifiedError) as e:
        client_with(FakeVLLM(down=True)).check()
    assert e.value.error_code == "010"
    assert isinstance(e.value.__cause__, openai.APIConnectionError)
