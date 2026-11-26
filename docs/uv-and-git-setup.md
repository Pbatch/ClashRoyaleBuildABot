## Wiki: Setup `uv` & Git

The bot runs on Linux and Windows (see [Bot Installation](bot-installation.md#prerequisites)).

---

### Step 1: Install `uv`
`uv` is a standalone executable that manages your Python versions and environments automatically.

1.  **Install `uv`:**
    * **Linux:**
        ```bash
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```
    * **Windows,** in PowerShell:
        ```powershell
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
        ```

2.  **Restart your terminal** to ensure the `uv` command is available in your PATH.

---

### Step 2: Install Git

Git is used to download the bot and to get updates (`git pull`). Run `git --version` to check whether it's installed.

On Windows, install [Git for Windows](https://git-scm.com/download/win), or run `winget install --id Git.Git -e`.

Many Linux distributions already include Git. Otherwise, install it with your package manager:

* **Debian / Ubuntu:**
    ```bash
    sudo apt install git
    ```
* **Fedora:**
    ```bash
    sudo dnf install git
    ```
* **Arch Linux:**
    ```bash
    sudo pacman -S git
    ```

For other distributions, see [Git for Linux](https://git-scm.com/download/linux).

---

### Verification

These commands confirm that your tools are correctly configured and ready for development.

| Tool | Verification Command |
| :--- | :--- |
| **`uv`** | `uv --version` |
| **Git** | `git --version` |
