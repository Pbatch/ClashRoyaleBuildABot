import os
import sys

import pytest

import clashroyalebuildabot.vlm_server as vlm_server
from clashroyalebuildabot.utils.error_handling import WikifiedError
from clashroyalebuildabot.vlm_server import VLMServer, is_local, serve_command
from tests.conftest import default_config

CONFIG = default_config().screen_detector.model_copy(
    update={
        "base_url": "http://localhost:8123",
        "model": "Qwen/Qwen3.5-0.8B",
        "gpu_memory_utilization": 0.6,
        "startup_timeout": 5,
    }
)


def with_settings(**settings):
    return CONFIG.model_copy(update=settings)


# Stand-ins for `vllm serve`: one that runs until stopped, one that fails.
ENDLESS = [sys.executable, "-c", "import time\nwhile True: time.sleep(1)"]
CRASHES = [sys.executable, "-c", "raise SystemExit(1)"]


@pytest.fixture
def server(monkeypatch, tmp_path):
    monkeypatch.setattr(vlm_server, "DEBUG_DIR", str(tmp_path))
    monkeypatch.setattr(vlm_server, "LOG_PATH", str(tmp_path / "vlm.log"))
    monkeypatch.setattr(vlm_server, "POLL_INTERVAL", 0.01)
    server = VLMServer()
    yield server
    server.stop()


def fake_vllm(monkeypatch, command, up_after_start=True):
    """Run ``command`` instead of vLLM. The server counts as up while a
    process this app started is running, if ``up_after_start``."""
    started = []
    processes = []
    monkeypatch.setattr(
        vlm_server, "serve_command", lambda config: [*command, config.model]
    )
    real_start = VLMServer._start

    def start(self, cmd):
        started.append(cmd)
        real_start(self, cmd[:-1])  # the model name isn't a real argument
        self._command = cmd
        processes.append(self.process)

    monkeypatch.setattr(VLMServer, "_start", start)
    monkeypatch.setattr(
        vlm_server,
        "is_up",
        lambda config: (
            up_after_start and any(p.poll() is None for p in processes)
        ),
    )
    return started


def test_serve_command_uses_the_config():
    command = serve_command(CONFIG)
    assert os.path.basename(command[0]) == "vllm"
    assert command[1:5] == ["serve", "Qwen/Qwen3.5-0.8B", "--port", "8123"]
    i = command.index("--gpu-memory-utilization")
    assert command[i + 1] == "0.6"


def test_only_local_servers_are_started():
    assert is_local(CONFIG)
    assert is_local(with_settings(base_url="http://127.0.0.1:8001"))
    assert not is_local(with_settings(base_url="http://gpu-box:8001"))


def test_uses_a_server_that_is_already_up(server, monkeypatch):
    monkeypatch.setattr(vlm_server, "is_up", lambda config: True)
    assert server.ensure_running(CONFIG)
    assert server.process is None
    server.stop()  # leaves a server it didn't start alone


def test_starts_a_server_and_waits_until_it_is_up(server, monkeypatch):
    started = fake_vllm(monkeypatch, ENDLESS)
    assert server.ensure_running(CONFIG)
    assert len(started) == 1
    process = server.process
    assert process is not None and process.poll() is None

    server.stop()
    assert process.poll() is not None
    assert server.process is None


def test_stopped_while_starting(server, monkeypatch):
    fake_vllm(monkeypatch, ENDLESS, up_after_start=False)
    assert not server.ensure_running(CONFIG, cancelled=lambda: True)
    # Still starting, ready for the next press of start.
    assert server.process is not None


def test_server_that_exits_while_starting_raises_e012(server, monkeypatch):
    fake_vllm(monkeypatch, CRASHES, up_after_start=False)
    with pytest.raises(WikifiedError, match="stopped while starting") as e:
        server.ensure_running(CONFIG)
    assert e.value.error_code == "012"
    assert server.process is None


def test_server_that_never_comes_up_is_stopped(server, monkeypatch):
    fake_vllm(monkeypatch, ENDLESS, up_after_start=False)
    with pytest.raises(WikifiedError, match="didn't start within") as e:
        server.ensure_running(with_settings(startup_timeout=0.1))
    assert e.value.error_code == "012"
    assert server.process is None


def test_restarts_when_the_settings_change(server, monkeypatch):
    started = fake_vllm(monkeypatch, ENDLESS)
    server.ensure_running(CONFIG)
    first = server.process
    assert first is not None

    # A server is up, but for the old settings.
    server.ensure_running(with_settings(model="other"))
    assert first.poll() is not None
    assert len(started) == 2


@pytest.mark.parametrize(
    "config",
    [
        with_settings(base_url="http://gpu-box:8001"),
        with_settings(auto_start=False),
    ],
)
def test_unreachable_server_it_cannot_start_raises_e010(
    server, monkeypatch, config
):
    monkeypatch.setattr(vlm_server, "is_up", lambda config: False)
    with pytest.raises(WikifiedError) as e:
        server.ensure_running(config)
    assert e.value.error_code == "010"
    assert server.process is None
