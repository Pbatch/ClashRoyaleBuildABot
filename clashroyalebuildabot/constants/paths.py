"""Where the bot's files are."""

import os
import sys

# The package folder, and the project folder above it.
SRC_DIR = os.path.dirname(os.path.dirname(__file__))
APP_DIR = os.path.dirname(SRC_DIR)

# Shipped with the bot, inside the package, and only read.
DEFAULT_CONFIG_PATH = os.path.join(SRC_DIR, "default_config.yaml")
MODELS_DIR = os.path.join(SRC_DIR, "models")
# Unit, card and elixir numbers from the game's files, made by
# dev/game_data/export_game_data.py.
GAME_DATA_PATH = os.path.join(SRC_DIR, "data", "game_data.json")
# The browser UI the API serves at /.
WEB_UI_PATH = os.path.join(SRC_DIR, "web", "index.html")
# The screen server the bot runs on the device: a dex jar, run with
# app_process. See jpeg_screen.py for what it does.
JPEG_SERVER_PATH = os.path.join(SRC_DIR, "data", "jpeg-server.jar")

# Shipped in git, in the project folder: only the GUIs use it, so it stays
# out of the installed package.
LOGO_PATH = os.path.join(APP_DIR, "media", "logo.png")

# Written at runtime, in the project folder, so they don't conflict with git
# updates.
USER_CONFIG_PATH = os.path.join(APP_DIR, "config.yaml")
DEBUG_DIR = os.path.join(APP_DIR, "debug")
SCREENSHOTS_DIR = os.path.join(DEBUG_DIR, "screenshots")
LABELS_DIR = os.path.join(DEBUG_DIR, "labels")
# Downloaded by setup (see clashroyalebuildabot/install.py).
ADB_DIR = os.path.join(APP_DIR, "platform-tools")
ADB_PATH = os.path.join(
    ADB_DIR, "adb.exe" if sys.platform == "win32" else "adb"
)
