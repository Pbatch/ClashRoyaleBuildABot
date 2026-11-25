"""The API's operations as MCP tools, for AI agents. Served at /mcp by
create_app, next to the REST routes, from the same functions."""

import functools
import inspect
import logging
from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.utilities.types import Image
from mcp.types import ToolAnnotations

from clashroyalebuildabot.api.operations import ApiError, Jpeg, Operation

INSTRUCTIONS = """\
Drives a Clash Royale bot on an Android device or emulator.

To play battles yourself, set bot.policy to external with update_config,
then start (or stop and start) the bot. The bot still reads the screen and
gets through the menus; you choose which card to play where.

Read get_meta once: it has the 18 x 32 tile grid, where the towers stand,
and every card and unit by name. Then, each turn: get_actions lists the
cards you can play now and every tile each can go on, or why nothing can
be played (blocked_by). get_state has the elixir, timer, towers, hand and
detected units; screenshot shows the screen itself. Then play.

The battle moves on while you think. Pass a generous max_age to play (or
leave frame out), or your plays will be refused as stale.
"""


def as_tool(fn: Callable[..., Any]) -> Callable[..., Any]:
    """fn as a tool: ApiError becomes ToolError, and Jpeg becomes an
    image. The signature and docstring, and so the schema, are fn's."""
    signature = inspect.signature(fn)
    returns_jpeg = signature.return_annotation is Jpeg

    @functools.wraps(fn)
    def tool(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        try:
            result = fn(*args, **kwargs)
        except ApiError as e:
            # Expected, like a REST 4xx: not worth an ERROR line per
            # refused play.
            raise ToolError(e.tool_message(), log_level=logging.DEBUG) from e
        if returns_jpeg:
            return Image(data=result.data, format="jpeg")
        return result

    if returns_jpeg:
        tool.__signature__ = signature.replace(  # ty: ignore[missing-attribute]
            return_annotation=Image
        )
        tool.__annotations__ = {**fn.__annotations__, "return": Image}
    return tool


def create_mcp(operations: list[Operation]) -> FastMCP:
    mcp = FastMCP("Clash Royale Build-A-Bot", instructions=INSTRUCTIONS)
    for operation in operations:
        mcp.tool(
            as_tool(operation.fn),
            name=operation.name,
            annotations=ToolAnnotations(read_only_hint=operation.read_only),
        )
    return mcp
