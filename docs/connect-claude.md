# Connecting Claude to the Bot

[Claude Code](https://code.claude.com/docs), Anthropic's AI coding assistant, can control the bot through its [MCP server](headless-and-api.md#letting-an-ai-agent-play-mcp). Once it's connected, you can ask Claude in plain English to set the bot up, start and stop it, look at the game, explain what the bot is doing, or play cards itself.

### Prerequisites

- The bot installed, as in [Install and Configure Your Bot](bot-installation.md).
- [Claude Code](https://code.claude.com/docs/en/quickstart), installed and signed in.

> **Only Claude Code can connect.** Claude Desktop and claude.ai connect to MCP servers from Anthropic's cloud, not from your computer, so they can't reach a server on `127.0.0.1`. Use Claude Code, in a terminal or in your editor.

#### Step 1: Start the bot with its API
The MCP server runs whenever the API does. In the bot's folder, run one of:
```bash
uv run python main.py              # opens the web UI too
uv run python main.py --headless   # without opening a browser
```
The bot prints where it's listening:
```
API listening on http://127.0.0.1:8000/api (docs at /docs), MCP at http://127.0.0.1:8000/mcp
```
This doesn't start playing. That waits until you press **Start**, or Claude starts it.

#### Step 2: Add the bot to Claude Code
In another terminal, run:
```bash
claude mcp add --transport http --scope user clash-royale http://127.0.0.1:8000/mcp
```
`--scope user` makes the bot available to Claude in every folder. Without it, Claude only sees it in the folder you ran the command in. If you changed `--port` when starting the bot, change `8000` here to match.

You only need to do this once. Claude reconnects whenever the bot is running.

#### Step 3: Check the connection
```bash
claude mcp list
```
`clash-royale` should show `✔ Connected`. If it shows `✘ Failed to connect`, check the bot is running and that the port matches.

Inside a Claude Code session, `/mcp` shows the same thing, and lists the bot's tools.

#### Step 4: Allow the bot's tools (optional)
Claude asks before it uses each tool for the first time. To stop the prompts, choose **Yes, and don't ask again** when it asks, or allow every tool of the bot at once by adding this to `~/.claude/settings.json`:
```json
{
  "permissions": {
    "allow": ["mcp__clash-royale__*"]
  }
}
```
Allowing the tools lets Claude start the bot and change its settings without asking you first.

### Things to ask Claude

Start a Claude Code session with `claude`, then ask, for example:

- "Is the Clash Royale bot running? Start it."
- "Show me a screenshot of the game and tell me what's happening."
- "Why didn't the bot play anything in the last few seconds?"
- "What are the Witch's stats at level 11? How does it compare to the Musketeer?"
- "Turn on show_images and save the config."
- "Set the bot's device serial to emulator-5554."

For screenshots, `visuals.show_images` must be on. Claude can turn it on itself, but it only takes effect when the bot next starts.

### Letting Claude play

By default the bot plays with its own [actions](bot-development.md), and Claude can only watch. To let Claude choose the cards, ask it to:

> Set the bot's policy to external, restart it, and play the next battle. Use a max_age of 30 seconds.

Claude then reads the arena, the hand and the units it can see, picks a card and a tile, and plays it, over and over. The bot still reads the screen and gets through the menus.

Keep your expectations low. Claude takes several seconds to decide each play, and a battle moves on fast. It plays like a slow, careful beginner, not like the built-in actions. Without a larger `max_age`, most of its plays are refused as `stale`, since the frame it decided on is more than a second old by the time it plays. It's best at the things around a battle: setting the bot up, watching, and explaining.

To give the bot back its own actions, ask Claude to set the policy to builtin and restart it.

### If something goes wrong

| What you see | What to do |
|---|---|
| `✘ Failed to connect` | The bot isn't running, or it's on a different port. Start it with `uv run python main.py` (Step 1). |
| `not_running: The bot isn't running.` | The server is up, but the bot hasn't been started. Ask Claude to start it, or press **Start**. |
| `builtin_policy: ...` | Claude tried to play while the bot uses its own actions. See [Letting Claude play](#letting-claude-play). |
| `stale: ...` | The play was decided on an old frame. Ask Claude to use a larger `max_age`. |
| `No frame yet: ...` from `screenshot` | Turn on `visuals.show_images`, then restart the bot. |
| Claude can't find the bot's tools | Run `/mcp` in Claude Code. If `clash-royale` isn't listed, repeat Step 2, with `--scope user`. |

> **Anyone who can reach the server can control the bot.** Like the rest of the API, the MCP server has no password. Leave `--host` at its default, `127.0.0.1`, so only programs on your own computer can reach it. See [Options](headless-and-api.md#options).
