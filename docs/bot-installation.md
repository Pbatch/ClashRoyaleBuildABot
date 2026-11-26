### Wiki: Bot Installation Setup Guide
---
### Prerequisites
- Linux or Windows on x86-64. The bot is only tested on Linux.
- Optionally, an NVIDIA GPU with its driver installed. The unit detector runs several times faster on it, but the CPU works too.
- [uv](https://docs.astral.sh/uv/).

#### Step 1: Open a Shell
- Open a terminal (on Windows, PowerShell).

#### Step 2: Clone the Repository
- Clone the repository using the command:
  ```bash
  git clone https://github.com/Pbatch/ClashRoyaleBuildABot.git
  ```

#### Step 3: Enter Repository Directory
- Navigate to the bot directory:
  ```bash
  cd ClashRoyaleBuildABot
  ```

#### Step 4: Create a Virtual Environment
- Set up a Python virtual environment to manage dependencies:
  ```bash
  uv venv --python 3.12
  ```

#### Step 5: Activate the Virtual Environment
- This step is optional if you start the bot with `uv run`, which always uses the project's environment. To run `python` directly instead, activate the environment first:
  ```bash
  source .venv/bin/activate
  ```
  On Windows, in PowerShell:
  ```powershell
  .venv\Scripts\activate
  ```

#### Step 6: Install Dependencies
- Install the necessary project dependencies:
  ```bash
  uv sync
  ```
- With an NVIDIA GPU, add the `gpu` extra instead. It also installs the CUDA and cuDNN libraries the GPU needs, about 2 GB more:
  ```bash
  uv sync --extra gpu
  ```
  Add `--extra gpu` to every `uv sync` you run later too (for example `uv sync --extra gpu --extra dev`): a `uv sync` without it removes the libraries again, and the bot quietly falls back to the CPU.
- For development purposes, install the dev dependencies and the pre-commit hooks:
  ```bash
  uv sync --extra dev
  uv run pre-commit install
  ```
- Run the tests with:
  ```bash
  uv run pytest
  ```

#### Step 7: Run Setup
- Download the rest of what the bot needs:
  ```bash
  uv run python -m clashroyalebuildabot.install
  ```
- This downloads the bot's own copy of [ADB](https://developer.android.com/tools/adb), which it uses to talk to your device, into `platform-tools/`. Running it again keeps what's already there. If you skip this step, the bot downloads ADB when it starts (and updates it when a new version of the bot needs a newer one).

### Testing the Bot
Now, let’s verify that the bot operates correctly:

- Ensure you're in the Clash Royale lobby.
- Open the bot using:
  ```bash
  uv run python main.py
  ```
- In the web UI that opens in your browser, check the device serial in the settings (run `adb devices` to find it). If the configured device isn't found, the bot uses the first connected device.
- Press start (▶) to start the bot. Press it again (■) to stop.
- To run the bot without opening a browser, or to control it from scripts, see [The Web UI and the HTTP API](headless-and-api.md).

### Configuration
The default settings are in [`clashroyalebuildabot/default_config.yaml`](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/default_config.yaml). Don't edit that file: updates replace it.

To change a setting, either change it in the web UI's settings and press **Save to config.yaml**, or create `config.yaml` in the project folder yourself. It only needs the settings you want to change, in the same sections as the defaults:
```yaml
ingame:
  play_action: 1.5
```
Your `config.yaml` isn't tracked by git, so `git pull` never overwrites it. To go back to the defaults, delete it.

### Important Note
- If you don't use `uv run`, make sure the virtual environment `.venv` is activated each time you start the bot.

### Updating
The bot doesn't update itself. To get the latest version, run these in the project folder:
```bash
git pull
uv sync
```
Your settings in `config.yaml` are never touched by updates (see [Configuration](#configuration)).

#### Updating from an older version
- Settings used to be saved in `clashroyalebuildabot/config.yaml`. If `git pull` says your local changes to that file would be overwritten, copy the settings you changed into a new `config.yaml` in the project folder, then run `git checkout -- clashroyalebuildabot/config.yaml` and `git pull` again.
- Debug output (logs, screenshots and labels) is now saved in `debug` in the project folder, and ADB is downloaded again into `platform-tools` there. Move anything you want to keep out of `clashroyalebuildabot/debug`, then delete it and `clashroyalebuildabot/emulator/platform-tools`.
