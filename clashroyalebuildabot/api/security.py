"""Keeps web pages in the user's browser from driving the bot.

The API has no authentication, so on its own any web page could send it
requests: a form posted to /api/start needs no JavaScript, and a page can
open a WebSocket to anywhere. Two checks stop that, for every request:

- Origin. Browsers send it on cross-site requests and on WebSockets. A
  request with an Origin that isn't the server itself is refused. Programs
  (curl, scripts, MCP clients) send none, and aren't affected, and nor is
  the server's own /docs page.
- Host, while the server listens on loopback. A site can point its own
  domain at 127.0.0.1 (DNS rebinding), and the browser then treats the API
  as that site. Its requests still name that domain in Host, so only
  loopback names are accepted. Served on another address, any name might
  reach it, so the Host isn't checked there.
"""

import ipaddress
from urllib.parse import urlsplit

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

LOOPBACK_NAMES = frozenset({"localhost", "127.0.0.1", "::1"})


def is_loopback(host: str) -> bool:
    """Whether host, an address to listen on, only accepts connections
    from this machine."""
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _hostname(host_header: str) -> str:
    """The name in a Host header, without its port or IPv6 brackets."""
    if host_header.startswith("["):
        return host_header[1 : host_header.find("]")]
    return host_header.rsplit(":", 1)[0]


def refusal(headers: dict[str, str], check_host: bool) -> str | None:
    """Why a request with these headers (lower-case names) is refused, or
    None if it isn't."""
    host = headers.get("host", "").lower()
    if check_host and _hostname(host) not in LOOPBACK_NAMES:
        return (
            f"Host {host!r} isn't this machine. The API only answers "
            "requests to 127.0.0.1 or localhost."
        )
    origin = headers.get("origin")
    if origin is not None and urlsplit(origin.lower()).netloc != host:
        return (
            f"Requests from web pages at {origin} aren't allowed: they "
            "could control the bot without you knowing."
        )
    return None


class SameOriginOnly:
    """ASGI middleware refusing what refusal() refuses: HTTP requests with
    a 403, and WebSockets before they're accepted."""

    def __init__(self, app: ASGIApp, *, check_host: bool) -> None:
        self.app = app
        self.check_host = check_host

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return
        headers = {
            name.decode("latin-1").lower(): value.decode("latin-1")
            for name, value in scope["headers"]
        }
        reason = refusal(headers, self.check_host)
        if reason is None:
            await self.app(scope, receive, send)
        elif scope["type"] == "websocket":
            # Policy violation. Closing before accepting refuses the
            # handshake.
            await send({"type": "websocket.close", "code": 1008})
        else:
            response = JSONResponse({"detail": reason}, status_code=403)
            await response(scope, receive, send)
