"""Start and stop the vLLM server that runs the vision model.

The bot reads screens, tower HP and the timer with a small vision model,
served by vLLM in a separate process. The GUI starts it on the first press
of start, if it isn't already running, and stops it when the GUI closes. A
server that was already running (started by hand, or on another machine) is
used as it is and left alone.

To run the server by itself, with the same settings:

    uv run python -m clashroyalebuildabot.vlm_server
"""

import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import requests
from loguru import logger

from clashroyalebuildabot.config import ScreenDetectorConfig
from clashroyalebuildabot.constants.paths import DEBUG_DIR
from clashroyalebuildabot.utils.error_handling import WikifiedError

LOG_PATH = os.path.join(DEBUG_DIR, "vlm_server.log")
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
# How often to check whether a starting server is ready.
POLL_INTERVAL = 2.0
# How long a server gets to shut down before it's killed.
STOP_TIMEOUT = 30.0
# Runs a command in a process that Linux sends SIGTERM when the thread that
# started it ends, so a crashed or killed bot doesn't leave the server
# holding the GPU. It sets that up (prctl PR_SET_PDEATHSIG = 1) and then
# becomes the command, which keeps the setting. Done in a fresh process,
# because running Python between fork and exec (Popen's preexec_fn) can
# deadlock when the app has other threads.
_EXIT_WITH_PARENT = (
    "import ctypes, os, signal, sys\n"
    "ctypes.CDLL(None).prctl(1, signal.SIGTERM)\n"
    "if os.getppid() != int(sys.argv[1]):\n"
    "    sys.exit()  # the parent ended before prctl\n"
    "os.execv(sys.argv[2], sys.argv[2:])\n"
)


def port(config: ScreenDetectorConfig) -> int:
    return urlparse(config.base_url).port or 80


def is_local(config: ScreenDetectorConfig) -> bool:
    return urlparse(config.base_url).hostname in LOCAL_HOSTS


def serve_command(config: ScreenDetectorConfig) -> list[str]:
    """The ``vllm serve`` command for the ``screen_detector`` config."""
    # The vllm executable sits beside this Python in the project's venv.
    vllm = os.path.join(os.path.dirname(sys.executable), "vllm")
    return [
        vllm,
        "serve",
        config.model,
        "--port",
        str(port(config)),
        "--gpu-memory-utilization",
        str(config.gpu_memory_utilization),
        # The bot's prompts are short, with one small image each, and it
        # sends at most 8 at once (6 towers, the timer and the screen).
        "--max-model-len",
        "2048",
        "--max-num-seqs",
        "8",
        "--limit-mm-per-prompt",
        '{"image": 1}',
    ]


def is_up(config: ScreenDetectorConfig, timeout=2.0) -> bool:
    try:
        response = requests.get(
            config.base_url.rstrip("/") + "/v1/models", timeout=timeout
        )
    except requests.RequestException:
        return False
    return response.ok


class VLMServer:
    """The vLLM server process this app started, if any."""

    def __init__(self):
        self.process: subprocess.Popen | None = None
        self._command: list[str] | None = None
        # The server exits when the thread that started it ends (see
        # _EXIT_WITH_PARENT), so it's started from this thread, which lasts
        # as long as the app, not from a bot thread.
        self._spawner = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="vlm-server"
        )

    def ensure_running(
        self,
        config: ScreenDetectorConfig,
        cancelled: Callable[[], bool] = lambda: False,
    ) -> bool:
        """Make sure a server for ``config`` is up, starting one if needed.

        Blocks until it's ready: about a minute, or a few more the first
        time, while vLLM compiles the model. Returns False if ``cancelled``
        became true while waiting, and raises if the server can't start.
        """
        command = serve_command(config)
        if self.process is not None and command != self._command:
            # The settings changed since we started it.
            self.stop()
        if is_up(config):
            return True
        if not is_local(config) or not config.auto_start:
            raise WikifiedError(
                "010",
                f"Can't reach the vision model server at "
                f"{config.base_url}. Start it before starting the bot.",
            )

        if self.process is None or self.process.poll() is not None:
            self._start(command)
        return self._wait_until_up(config, cancelled)

    def _start(self, command: list[str]):
        logger.info(
            "Starting the vision model server. This takes about a minute, "
            f"or a few the first time. Its log is in {LOG_PATH}"
        )
        os.makedirs(DEBUG_DIR, exist_ok=True)
        with open(LOG_PATH, "w") as log:
            # A new session, so stop() can end vLLM's worker processes too.
            self.process = self._spawner.submit(
                subprocess.Popen,
                [
                    sys.executable,
                    "-c",
                    _EXIT_WITH_PARENT,
                    str(os.getpid()),
                    *command,
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            ).result()
        self._command = command

    def _wait_until_up(self, config: ScreenDetectorConfig, cancelled) -> bool:
        timeout = config.startup_timeout
        deadline = time.monotonic() + timeout
        while not is_up(config):
            if cancelled():
                return False
            assert self.process is not None
            if self.process.poll() is not None:
                self.process = None
                raise WikifiedError(
                    "012",
                    f"The vision model server stopped while starting. "
                    f"See its log in {LOG_PATH}",
                )
            if time.monotonic() > deadline:
                self.stop()
                raise WikifiedError(
                    "012",
                    f"The vision model server didn't start within "
                    f"{timeout:g} seconds. See its log in {LOG_PATH}",
                )
            time.sleep(POLL_INTERVAL)
        logger.info("The vision model server is ready")
        return True

    def stop(self):
        """Stop the server, if this app started it."""
        process, self.process = self.process, None
        if process is None or process.poll() is not None:
            return
        logger.info("Stopping the vision model server")
        self._signal(process, signal.SIGTERM)
        try:
            process.wait(timeout=STOP_TIMEOUT)
        except subprocess.TimeoutExpired:
            self._signal(process, signal.SIGKILL)
            process.wait()

    @staticmethod
    def _signal(process: subprocess.Popen, sig: int):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass


def main():
    from clashroyalebuildabot.config import load_config

    command = serve_command(load_config().screen_detector)
    os.execv(command[0], command)


if __name__ == "__main__":
    main()
