### Wiki: Bot Installation Setup Guide
---
### Prerequisites
- Linux on x86-64. The bot doesn't support Windows or macOS: vLLM, which serves its vision model, only runs on Linux.
- An NVIDIA GPU, with its driver installed.
- [uv](https://docs.astral.sh/uv/).

#### Step 1: Open a Shell
- Open a terminal.

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

#### Step 6: Install Dependencies
- Install the necessary project dependencies. They include vLLM and the GPU build of ONNX Runtime, which are large downloads:
  ```bash
  uv sync
  ```
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
- This downloads the bot's own copy of [ADB](https://developer.android.com/tools/adb), which it uses to talk to your device, into `platform-tools/`. It also downloads [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B), the small vision model the bot reads the screen with (about 1.7 GB), into the Hugging Face cache. Running it again keeps what's already there.

### Testing the Bot
Now, let’s verify that the bot operates correctly:

- Ensure you're in the Clash Royale lobby.
- Open the bot using:
  ```bash
  uv run python main.py
  ```
- In the window that opens, check the **Device Serial** in the Settings tab (run `adb devices` to find it). If the configured device isn't found, the bot uses the first connected device.
- Press start (▶) to start the bot. Press it again (■) to stop.
- The first press also starts the vision model's server, with [vLLM](https://github.com/vllm-project/vllm). That takes about a minute, or a few minutes the first time, while vLLM compiles the model. The server keeps running until you close the bot, so stopping and starting again is quick. Its log is in `debug/vlm_server.log`.
- The server reserves about 75% of your GPU's memory, which a 6 GB card needs, so close other programs using the GPU first. On a larger card you can lower `gpu_memory_utilization` under `screen_detector` in your [configuration](#configuration).
- To run the server yourself instead, for example to keep it running between sessions, start it in another terminal before the bot. The bot then uses that server and leaves it running:
  ```bash
  uv run python -m clashroyalebuildabot.vlm_server
  ```

### Configuration
The default settings are in [`clashroyalebuildabot/default_config.yaml`](../clashroyalebuildabot/default_config.yaml). Don't edit that file: updates replace it.

To change a setting, either change it in the GUI's Settings tab and press **Save config to file**, or create `config.yaml` in the project folder yourself. It only needs the settings you want to change, in the same sections as the defaults:
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
