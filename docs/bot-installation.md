### Wiki: Bot Installation Setup Guide
---
### Prerequisites
- Ensure PowerShell (Windows) or Bash (Linux) is ready to use.
- Have administrative access if needed.

#### Step 1: Open a Shell
- **Windows:** Open PowerShell.
- **Linux:** Open Bash.

#### Step 2: Clone the Repository
- Clone the repository using the command:
  ```bash
  git clone https://github.com/Pbatch/ClashRoyaleBuildABot.git
  ```

> [!NOTE]  
> Don't install the bot (or anything for that matter) in the system32 folder, the bot won't work properly


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
  - **Windows (Powershell):**
    ```powershell
    .venv\Scripts\Activate.ps1
    ```
  - **Windows (Command Prompt):**
    ```cmd
    .venv\Scripts\Activate.bat
    ```
  - **macOS / Linux:**
    ```bash
    source .venv/bin/activate
    ```

#### Step 6: Install Dependencies
- Install the necessary project dependencies:
  ```bash
  uv sync --extra cpu
  ```
- If you are confident that your GPU will work with ONNX, instead run:
  ```bash
  uv sync --extra gpu
  ```
- For development purposes, install the dev dependencies and the pre-commit hooks:
  ```bash
  uv sync --extra cpu --extra dev
  uv run pre-commit install
  ```
- Run the tests with:
  ```bash
  uv run pytest
  ```

#### Step 7: Start the Screen Detector
The bot recognises screens with [OneJev](https://huggingface.co/OmniJev/OneJev1.6-0.8B), a small vision model that runs in its own server. It needs an NVIDIA GPU. Install it in a separate environment, outside the project folder, so its large dependencies stay out of the bot's:
  ```bash
  uv venv -p 3.12 ~/onejev
  VIRTUAL_ENV=~/onejev uv pip install flide torchvision
  ```
- Start it, and leave it running while you use the bot:
  ```bash
  ~/onejev/bin/flide serve --model OmniJev/OneJev1.6-0.8B --port 8000
  ```
- The first start downloads the model (about 1.7 GB). On a GPU with 6 GB or less, add `--no-cuda-graphs --session-cache-gb 0.25` so it fits in memory.

### Testing the Bot
Now, let’s verify that the bot operates correctly:

- Ensure you're in the Clash Royale lobby.
- Open the bot using:
  ```bash
  uv run python main.py
  ```
- In the window that opens, check the **Device Serial** in the Settings tab (run `adb devices` to find it). If the configured device isn't found, the bot uses the first connected device.
- Press start (▶) to start the bot. Press it again (■) to stop.

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
- The bot doesn't update itself. To get the latest version, run `git pull` and then `uv sync` in the project folder.
