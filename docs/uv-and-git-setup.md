## Wiki: Setup `uv` & Git

The bot only runs on Linux (see [Bot Installation](bot-installation.md#prerequisites)), so these steps are for Linux.

---

### Step 1: Install `uv`
`uv` is a standalone executable that manages your Python versions and environments automatically.

1.  **Install `uv`:**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Restart your terminal** to ensure the `uv` command is available in your PATH.

---

### Step 2: Install Git

Git is used to download the bot and to get updates (`git pull`). Many distributions already include it; run `git --version` to check. Otherwise, install it with your package manager:

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
