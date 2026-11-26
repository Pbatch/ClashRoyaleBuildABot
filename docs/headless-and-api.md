# The Web UI and the HTTP API

The bot is controlled over HTTP, from its web UI or from your own scripts and programs. You can run it on a machine with no screen, script it, or watch it from another program.

There are two ways to run it:

| Command | What you get |
|---|---|
| `uv run python main.py` | The bot's controls, a map of the arena, battle state, settings and logs open in your browser. |
| `uv run python main.py --headless` | The same, but no browser is opened. Use it on a machine with no screen, or when only scripts control the bot. |

Both start the API at `http://127.0.0.1:8000/api`, and serve the browser UI at `http://127.0.0.1:8000/`. Open `http://127.0.0.1:8000/docs` in a browser for an interactive page that lists every endpoint and lets you try them.

They also serve the same API to AI agents, as an MCP server at `http://127.0.0.1:8000/mcp`. See [Letting an AI agent play](#letting-an-ai-agent-play-mcp).

### Options

| Option | Default | Meaning |
|---|---|---|
| `--headless` | | Don't open the web UI in a browser. |
| `--host` | `127.0.0.1` | Address the API listens on. |
| `--port` | `8000` | Port the API listens on. |

> **The API has no password.** Anyone who can reach it can start the bot and change its settings. By default it only listens on `127.0.0.1`, so only programs on the same machine can reach it. Only use `--host 0.0.0.0` (or another address) on a network you trust. The bot prints a warning when you do.

### Running headless

1. Make sure your `config.yaml` has the right `adb.device_serial` (see [Configuration](bot-installation.md#configuration)), or set it through the API as shown below.
2. Start the bot:
   ```bash
   uv run python main.py --headless
   ```
3. Start playing:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/start
   ```
4. Press **Ctrl+C** to quit. The bot stops cleanly first and closes its connection to the device.

Logs go to the terminal and to `debug/bot.log`.

The web UI and the API share one bot and one set of settings, so you can use both at once. If you start, pause or stop the bot through the API, the web UI updates to match.

### Controlling the bot

| Request | What it does |
|---|---|
| `GET /api/status` | The bot's status: `stopped`, `running`, `paused` or `stopping`. |
| `POST /api/start` | Start the bot. |
| `POST /api/stop` | Stop the bot. It finishes its current step, so the status is `stopping` for a moment before `stopped`. |
| `POST /api/pause` | Pause the bot. It stops playing but stays connected to the device. |
| `POST /api/resume` | Resume a paused bot. |

Each `POST` returns the new status:
```bash
$ curl -X POST http://127.0.0.1:8000/api/start
{"status":"running"}
```
If the action isn't possible right now, you get a `409` error that says why, and nothing changes:
```bash
$ curl -X POST http://127.0.0.1:8000/api/pause
{"detail":"Can't pause while the bot is stopped."}
```

### Changing settings

`GET /api/config` returns every setting, in the same sections as [`default_config.yaml`](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/default_config.yaml).

`PATCH /api/config` changes only the settings you send:
```bash
curl -X PATCH http://127.0.0.1:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"adb": {"device_serial": "emulator-5554"}, "ingame": {"play_action": 1.5}}'
```
It returns all the settings with your changes applied. Keep in mind:

- **A running bot keeps the settings it started with.** Changes apply from the next start, so stop and start the bot to use them. The log level is the exception: it changes straight away.
- **Settings are checked before any are changed.** If one is invalid, for example a misspelt name or a negative `play_action`, you get a `422` error that names it, and none of the settings change.
- **Changes aren't saved to `config.yaml`.** They last until the bot quits. To keep them, press **Save to config.yaml** in the web UI's settings, call `POST /api/config/save`, or add them to `config.yaml` yourself.

### Live events and frames

Two [WebSocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) streams send updates as they happen:

- **`/api/events`** sends JSON messages: the current status as soon as you connect, then each status change and each log line.
  ```json
  {"type": "status", "status": "running"}
  {"type": "log", "time": "2026-11-25T00:41:05.234+00:00", "level": "INFO", "source": "bot:step:186", "message": "New screen state: IN_GAME"}
  ```
- **`/api/frames`** sends each annotated screenshot as a JPEG image. It only sends frames while `visuals.show_images` is on. A slow connection skips frames instead of slowing the bot down.

For example, this prints every event. It uses the `websockets` library, which is installed with the bot:
```bash
uv run python -c '
import asyncio, websockets

async def main():
    async with websockets.connect("ws://127.0.0.1:8000/api/events") as ws:
        async for message in ws:
            print(message)

asyncio.run(main())
'
```
And this saves the next frame as `frame.jpg`:
```bash
uv run python -c '
import asyncio, websockets

async def main():
    async with websockets.connect("ws://127.0.0.1:8000/api/frames") as ws:
        with open("frame.jpg", "wb") as f:
            f.write(await ws.recv())

asyncio.run(main())
'
```

## Playing the game from your own program

The bot can leave the decisions to another program: a script, a bot of your own written in any language, or an AI agent. The bot still reads the screen and gets through the menus. Your program reads the game state and says which card to play where.

1. Set `bot.policy` to `external`, in `config.yaml` or through the API, then start (or restart) the bot:
   ```bash
   curl -X PATCH http://127.0.0.1:8000/api/config \
     -H "Content-Type: application/json" -d '{"bot": {"policy": "external"}}'
   curl -X POST http://127.0.0.1:8000/api/start
   ```
   With the default, `builtin`, the bot plays with its own [actions](bot-development.md), and `POST /api/play` is refused.
2. Read the state, decide, and play. Repeat.

| Request | What it does |
|---|---|
| `GET /api/meta` | The arena's grid, the deck, every card and unit, the elixir timeline and tower stats. Read it once at the start. |
| `GET /api/units/{name}?level=11` | A unit's stats at a level: hitpoints, damage, speed, range and more. See [Unit and card stats](#unit-and-card-stats). |
| `GET /api/cards/{name}?level=11` | A card's stats, with the stats of every unit it deploys. |
| `GET /api/state` | The game as of the latest frame. `404` until the bot has read one. |
| `GET /api/actions` | The cards you can play right now, with every tile each can go on, or why nothing can be played. |
| `POST /api/play` | Play a card. Waits until the bot has tapped it, then returns. |
| `GET /api/screenshot.jpg` | The latest annotated screenshot, as a JPEG, while `visuals.show_images` is on. `404` until there is one. |
| `/api/states` (WebSocket) | Every frame's state as it's read, the same as `GET /api/state` returns: up to 10 a second in a battle, and 2 a second outside one. A slow connection skips to the newest. |

Every request is listed, with its exact JSON, at `http://127.0.0.1:8000/docs`. The schema is at `/openapi.json`, if you want to generate a client from it.

### The arena

Positions are tiles on an 18 × 32 grid. Tile (0, 0) is the bottom-left of the arena as you see it, on your side. `tile_x` runs 0–17 from left to right, and `tile_y` runs 0–31 from your end to the enemy's. Rows 0–14 are your half, rows 15 and 16 are the river (with the bridges at x 3 and 14), and rows 17–31 are the enemy's half.

The towers stand on these tiles (`grid.towers` in `/api/meta`, both ends included):

| Tower | Tiles (x, y) | Centre |
|---|---|---|
| `ally_king` | x 7–10, y 1–4 | (9, 3) |
| `left_ally_princess` | x 2–4, y 5–7 | (3.5, 6.5) |
| `right_ally_princess` | x 13–15, y 5–7 | (14.5, 6.5) |
| `left_enemy_princess` | x 2–4, y 24–26 | (3.5, 25.5) |
| `right_enemy_princess` | x 13–15, y 24–26 | (14.5, 25.5) |
| `enemy_king` | x 7–10, y 27–30 | (9, 29) |

A centre is in tile units, where tile (x, y) covers x to x + 1: a princess tower's centre is the middle of tile (3, 6), a king's the corner where four tiles meet. The towers are drawn leaning up the screen, so on screen they reach above their tiles.

There's a picture of the grid in the [Bot Development Tutorial](bot-development.md).

Troops and buildings can only go on your half, apart from the tiles under your own towers, and on the enemy's half behind a princess tower you've destroyed. Spells (cards with `target_anywhere` in `/api/meta`) can go anywhere. You don't need to work this out yourself: `GET /api/actions` lists the tiles.

### The state

```json
{
  "frame": 1234,
  "time": 1764031265.12,
  "screen": "in_game",
  "battle": {
    "elixir": 7,
    "elixir_rate": {"seconds_per_elixir": 2.8, "multiplier": 1},
    "timer": {"time_left": 95, "overtime": false},
    "towers": {
      "left_enemy_princess": {"destroyed": true, "hp": 0, "level": null},
      "enemy_king": {"destroyed": false, "hp": null, "level": null},
      "...": "..."
    },
    "next_card": "musketeer",
    "hand": [
      {"hand_index": 0, "card": "knight", "cost": 3, "playable": true},
      "..."
    ],
    "allies": [],
    "enemies": [
      {"unit": "giant", "tile_x": 4, "tile_y": 20, "conf": 0.81}
    ]
  },
  "pending_play": null
}
```

- Cards and units are named, for example `"baby_dragon"`. The names are the same everywhere in the API.
- `screen` is `in_game` during a battle. The other screens are `lobby`, `end_of_game` (the results screen) and `unknown` (loading, searching for an opponent, a popup).
- `battle` is everything read from the battle. It's `null` on every screen but `in_game`, since there's nothing to read there.
- `null` inside `battle` means "not read yet". A tower's `hp` is `null` until its health bar is first read, and a king tower's stays `null` until it's first hit, since it shows no health bar before then. Use `destroyed` to tell whether a tower is standing.
- A hand card is `playable` when the game shows it in colour (not greyed out) and the elixir read covers its cost. That's when `POST /api/play` will take it.
- **Detections are noisy.** They come from the unit detector, so units can flicker in and out between frames, and a swarm may be miscounted. `conf` is the detector's confidence, from 0 to 1. Look at a few frames before you react to a single detection.
- `elixir_rate` is how fast elixir comes in now: one every 2.8 seconds, then double (1.4 s) from the last minute of regulation time, then triple (0.93 s) for the last minute of overtime. It comes from the timer, so it's `null` until the timer has been read.
- `pending_play` is the card the bot last tapped, while the screen doesn't yet show it played. Nothing else can be played until it does, or about a second passes (`ingame.play_action`).

### Playing a card

```bash
$ curl -X POST http://127.0.0.1:8000/api/play \
    -H "Content-Type: application/json" \
    -d '{"hand_index": 0, "tile_x": 3, "tile_y": 14, "frame": 1234}'
{"card":"knight","hand_index":0,"tile_x":3,"tile_y":14,"frame":1236}
```

`hand_index` is the card's place in your hand, 0–3 from left to right, as in `hand` in the state. The bot checks the play against the newest frame, just before tapping, so the response's `frame` may be later than the one you sent.

Pass the `frame` you decided on, so a decision made on an old frame isn't played. If that frame is older than `max_age` seconds (default 1) when the bot gets to the play, the play is refused as `stale`. This matters most for slow deciders: by the time an AI model answers, the battle may have moved on.

If the card isn't played, you get a `409` with a reason you can match on, and a message:
```json
{"reason": "not_enough_elixir", "message": "witch costs 5, elixir is 3."}
```

| Reason | Meaning |
|---|---|
| `not_running` | The bot isn't running. |
| `paused` | The bot is paused. |
| `builtin_policy` | `bot.policy` isn't `external`. Change it, then restart the bot. |
| `not_in_battle` | The screen isn't a battle. |
| `play_pending` | The last card played hasn't shown as played yet. Try again in a moment. |
| `busy` | Another play is waiting to be made. Plays are made one at a time. |
| `stale` | The `frame` you sent is older than `max_age` seconds, or too old to remember. |
| `timeout` | The bot didn't get to the play within 2 seconds, so it never will. |
| `bad_hand_index` | There's no card at that hand position. |
| `not_ready` | The card isn't ready to play. |
| `not_enough_elixir` | You can't afford it. |
| `bad_tile` | The card can't go on that tile. |

A `hand_index` or tile outside the grid is a `422` instead, as with settings.

### Unit and card stats

`GET /api/units/{name}` returns a unit's stats, named as in detections, so you can look up anything you see in `allies` or `enemies`:
```bash
$ curl "http://127.0.0.1:8000/api/units/knight?level=11"
{"name":"knight","level":11,"hitpoints":1766,"damage":202,"dps":168.3,"hit_speed":1.2,"range":1.2,"speed":60,"flying":false,"attacks_air":false,"attacks_ground":true,"targets_only_buildings":false,...}
```

`GET /api/cards/{name}` returns a card's cost, rarity and type, what it deploys (the Skeleton Army's 15 skeletons, say) with each unit's stats, and for spells their damage, radius and damage to crown towers.

- **Levels** are the game's 1–15 scale (higher levels are accepted too). Each rarity starts higher: rare cards at 3, epic at 6, legendary at 9, champions at 11. A level below a card's rarity's start is a `422`. Without `level`, it's 11, the tournament standard, or the card's lowest level if that's higher. You can't see your opponent's card levels, but they're usually close to their king tower's level.
- **Distances** (range, radius) are in tiles. **Times** are in seconds. **Speed** is the game's own number: 45 slow, 60 medium, 90 fast, 120 very fast.
- **Damage** is per hit, or per wave for spells with several (Arrows). Spells that do their damage over time, like Poison and Earthquake, have `null` damage for now.
- **Tower stats** (`tower_stats` in `/api/meta`) are for level 1 only: towers grow with level by a table the game files the bot reads don't include.

The numbers come from the game's own files. Stats that grow with level are the level-1 value times the game's multiplier for that level, rounded down. That rule matches all 4,945 per-level values in RoyaleAPI's public data, and the Knight matches its published level-11 stats. The base values are as current as the game files they were exported from, which are newer than RoyaleAPI's data (October 2023), so the two differ wherever a card has been rebalanced since. They're exported by `dev/game_data/export_game_data.py`; after a game update, re-run it to bring them up to date.

### A complete example

This plays a random affordable card on a random tile it can go on, whenever it can. It uses `requests`, which is installed with the bot:
```python
import random
import time

import requests

API = "http://127.0.0.1:8000/api"

while True:
    actions = requests.get(f"{API}/actions").json()
    if actions["blocked_by"] is None:
        card = random.choice(actions["cards"])
        tile_x, tile_y = random.choice(card["tiles"])
        response = requests.post(
            f"{API}/play",
            json={
                "hand_index": card["hand_index"],
                "tile_x": tile_x,
                "tile_y": tile_y,
                "frame": actions["frame"],
            },
        )
        print(response.json())
    time.sleep(0.2)
```

If your bot is written in Python, you can also skip the API and run it inside the bot, as a policy. See [Writing a policy](bot-development.md#writing-a-policy).

## Letting an AI agent play (MCP)

The bot is also an [MCP](https://modelcontextprotocol.io) server, so an AI agent such as Claude Code can start and stop the bot, change its settings, look at the game and play cards. It runs whenever the API does, at `http://127.0.0.1:8000/mcp`.

To connect Claude Code, see [Connecting Claude to the Bot](connect-claude.md). Other MCP clients take the same URL, with the "streamable HTTP" transport.

Every request in this page is also a tool, with the same name as its `operationId` at `/docs`, the same arguments and the same answer:

| Tool | Request |
|---|---|
| `get_status`, `start`, `stop`, `pause`, `resume` | `GET /api/status`, `POST /api/start`, ... |
| `get_config`, `update_config`, `save_config` | `GET` and `PATCH /api/config`, and `POST /api/config/save`. `update_config` takes the changes as `changes`. |
| `get_meta`, `get_unit`, `get_card` | `GET /api/meta`, `/api/units/{name}`, `/api/cards/{name}` |
| `get_state`, `get_actions` | `GET /api/state`, `/api/actions` |
| `play` | `POST /api/play`. It takes the play as `request`: `{"hand_index": 0, "tile_x": 9, "tile_y": 5}`. |
| `screenshot` | `GET /api/screenshot.jpg`, as an image the agent can look at. Needs `visuals.show_images` on. |

An error comes back as a tool error with the same message. A refused play starts with its reason, for example `not_enough_elixir: witch costs 5, elixir is 3.`

To let the agent play, set `bot.policy` to `external`, as for [your own program](#playing-the-game-from-your-own-program). An agent can do that itself with `update_config`, then `stop` and `start`.

> **Agents are slow.** An agent takes seconds to decide, and the battle moves on meanwhile. Unless it passes a larger `max_age` to `play`, or leaves `frame` out, most of its plays will be refused as `stale`. Expect it to play like a slow, thoughtful player, not a fast one. It's also useful away from battles: to set the bot up, watch it, or work out why it played what it did.

The streams (`/api/events`, `/api/states` and `/api/frames`) are WebSockets only. MCP has nothing like them.

The MCP server has no password either, so the [same warning](#options) applies: anyone who can reach it can control the device.

### Adding an operation

Requests and tools are made from the same functions, in [`clashroyalebuildabot/api/operations.py`](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/api/operations.py). To add one, write a function there and add it to the list at the end of `operations()`. It becomes a request under `/api` and a tool at `/mcp`, both described by its arguments, return type and docstring. Write the docstring for someone who has never seen the code, since that's what an agent reads. Raise `ApiError` for anything that can't be done, and return `Jpeg` for an image.
