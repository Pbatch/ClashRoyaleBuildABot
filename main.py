from clashroyalebuildabot.utils.error_handling import WikifiedError

try:
    import argparse
    import contextlib
    import ipaddress
    import signal
    import sys
    import threading
    import time
    import webbrowser
    from collections.abc import Sequence

    import uvicorn
    from loguru import logger
    from PyQt6.QtWidgets import QApplication

    from clashroyalebuildabot.actions import (
        ArchersAction,
        BabyDragonAction,
        CannonAction,
        GoblinBarrelAction,
        KnightAction,
        MinipekkaAction,
        MusketeerAction,
        WitchAction,
    )
    from clashroyalebuildabot.actions.generic.action import Action
    from clashroyalebuildabot.api import EventHub, create_app
    from clashroyalebuildabot.bot.controller import BotController
    from clashroyalebuildabot.bot.policy import Policy
    from clashroyalebuildabot.config import Config, load_config
    from clashroyalebuildabot.gui.main_window import MainWindow
    from clashroyalebuildabot.utils.logger import follow_log_level
except Exception as e:
    raise WikifiedError("001", "Missing imports.") from e


# Your own Policy here replaces the actions' scoring; see "Writing a
# policy" in docs/bot-development.md. None: bot.policy in the config decides.
POLICY: Policy | None = None

ACTIONS: list[type[Action]] = [
    ArchersAction,
    GoblinBarrelAction,
    BabyDragonAction,
    CannonAction,
    KnightAction,
    MinipekkaAction,
    MusketeerAction,
    WitchAction,
]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clash Royale Build-A-Bot")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="run without the GUI, controlled through the HTTP API",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="run without the window and open the browser UI instead",
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="serve the HTTP API alongside the GUI",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="address for the API (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="port for the API (default: %(default)s)",
    )
    return parser.parse_args(argv)


def _is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _warn_if_exposed(host: str) -> None:
    if not _is_loopback(host):
        logger.warning(
            f"The API has no authentication, and {host} may be reachable "
            "from other machines: anyone who can reach it can control the "
            "device."
        )


def _api_server(
    controller: BotController, hub: EventHub, host: str, port: int
) -> uvicorn.Server:
    _warn_if_exposed(host)
    app = create_app(controller, hub)
    logger.info(
        f"Web UI at http://{host}:{port}/, API at http://{host}:{port}/api "
        f"(docs at /docs), MCP at http://{host}:{port}/mcp"
    )
    return uvicorn.Server(
        uvicorn.Config(app, host=host, port=port, log_level="warning")
    )


def run_gui(config: Config, api: bool, host: str, port: int) -> None:
    # Qt's event loop never lets Python's Ctrl+C handler run, so Ctrl+C
    # just ends the process.
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication([])
    window = MainWindow(config, ACTIONS, POLICY)
    hub = EventHub()
    sinks = [window.log_handler_function]
    if api:
        sinks.append(hub.log_sink)
    follow_log_level(window.controller, sinks)

    server_thread = None
    if api:
        # The window and the API share one controller, and so one bot and
        # one config. uvicorn skips its signal handlers off the main thread.
        server = _api_server(window.controller, hub, host, port)
        server_thread = threading.Thread(target=server.run, daemon=True)
        server_thread.start()

    window.show()
    code = app.exec()
    if server_thread is not None:
        server.should_exit = True
        server_thread.join(timeout=10)
    sys.exit(code)


def _open_when_started(server: uvicorn.Server, url: str) -> None:
    """Open url in a browser once server is accepting connections."""

    def wait_then_open() -> None:
        while not server.started:
            if server.should_exit:
                return
            time.sleep(0.05)
        logger.info(f"Opening the web UI at {url}")
        webbrowser.open(url)

    threading.Thread(target=wait_then_open, daemon=True).start()


def run_headless(
    config: Config, host: str, port: int, open_browser: bool = False
) -> None:
    hub = EventHub()
    controller = BotController(config, ACTIONS, POLICY)
    follow_log_level(controller, [hub.log_sink])
    server = _api_server(controller, hub, host, port)
    if open_browser:
        # A browser can't reach 0.0.0.0 or ::, so open those on loopback.
        browse_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
        if ":" in browse_host:
            browse_host = f"[{browse_host}]"
        _open_when_started(server, f"http://{browse_host}:{port}/")
    # Ctrl+C makes uvicorn shut down, which stops the bot cleanly. uvicorn
    # then raises the KeyboardInterrupt again, which needs no traceback.
    with contextlib.suppress(KeyboardInterrupt):
        server.run()


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    try:
        config = load_config()
        if args.headless or args.web:
            run_headless(config, args.host, args.port, open_browser=args.web)
        else:
            run_gui(config, args.api, args.host, args.port)
    except WikifiedError:
        raise
    except Exception as e:
        logger.error(f"An error occurred in main loop: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
