"""One-time setup, run after ``uv sync``:

    uv run python -m clashroyalebuildabot.install

Downloads Google's ADB (Android platform-tools) into the project folder, so
the bot talks to the device with a known copy rather than whichever ``adb``
is on the PATH, and the vision model into the Hugging Face cache. Safe to
run again: what's already there is kept.
"""

import os
import zipfile

import requests
from loguru import logger
from tqdm import tqdm

from clashroyalebuildabot.constants.paths import ADB_DIR, ADB_PATH, APP_DIR

ADB_URL = (
    "https://dl.google.com/android/repository/platform-tools-latest-linux.zip"
)


def extract_zip(zip_path, dest):
    """Extract a zip, keeping Unix permissions such as the executable bit.

    zipfile.extractall drops them, which leaves adb unable to run.
    """
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        for info in zip_ref.infolist():
            path = zip_ref.extract(info, dest)
            mode = (info.external_attr >> 16) & 0o777
            if mode and not info.is_dir():
                os.chmod(path, mode)


def adb_installed() -> bool:
    return os.access(ADB_PATH, os.X_OK)


def install_adb():
    if os.path.isfile(ADB_PATH):
        # Earlier versions lost the executable bit when extracting.
        if not adb_installed():
            os.chmod(ADB_PATH, os.stat(ADB_PATH).st_mode | 0o111)
        logger.info(f"ADB is already installed at {ADB_PATH}")
        return

    zip_path = os.path.join(APP_DIR, os.path.basename(ADB_URL))
    response = requests.get(ADB_URL, stream=True, timeout=60)
    response.raise_for_status()
    chunk_size = 1024 * 1024  # 1 MB chunks
    total_mb = int(response.headers.get("content-length", 0)) / chunk_size

    with open(zip_path, "wb") as file:
        with tqdm(
            unit="MB",
            desc="Downloading ADB",
            unit_scale=True,
            unit_divisor=1024,
            total=total_mb,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    pbar.update(file.write(chunk) / chunk_size)
    # The zip holds a platform-tools folder, so this creates ADB_DIR.
    extract_zip(zip_path, APP_DIR)
    os.remove(zip_path)
    logger.info(f"Installed ADB in {ADB_DIR}")


def download_model(model: str):
    """Download the vision model into the Hugging Face cache, where vLLM
    looks for it, so the bot's first start doesn't wait for it."""
    from huggingface_hub import snapshot_download

    logger.info(f"Downloading {model} (about 1.7 GB)")
    path = snapshot_download(model)
    logger.info(f"{model} is in {path}")


def main():
    from clashroyalebuildabot.config import load_config

    install_adb()
    download_model(load_config().screen_detector.model)


if __name__ == "__main__":
    main()
