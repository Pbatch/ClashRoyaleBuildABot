## Wiki: Setup `uv` & Git

---

### Step 1: Install `uv`
`uv` is a standalone executable that manages your Python versions and environments automatically.

1.  **Install `uv`:**
    * **macOS / Linux:**
        ```bash
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```
    * **Windows (PowerShell):**
        ```powershell
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
        ```

2.  **Restart your terminal** to ensure the `uv` command is available in your PATH.

---

### Step 2: Install Git

Git is used to download the bot and to get updates (`git pull`).

1.  **Download Git:**
    * Access [Git Downloads](https://www.git-scm.com/downloads) and choose the version for your operating system.
2.  **Installation:**
    * Follow the on-screen prompts to complete the installation.

---

### Verification

These commands confirm that your tools are correctly configured and ready for development.

| Tool | Verification Command |
| :--- | :--- |
| **`uv`** | `uv --version` |
| **Git** | `git --version` |
