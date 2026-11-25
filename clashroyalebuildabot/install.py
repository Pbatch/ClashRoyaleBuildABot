"""Setup, run after ``uv sync``:

    uv run python -m clashroyalebuildabot.install

Downloads Google's ADB (Android platform-tools) into the project folder, so
the bot talks to the device with a known copy rather than whichever ``adb``
is on the PATH, and the vision model into the Hugging Face cache. Safe to
run again: what's already there is kept, and an ADB other than the
pinned version is replaced.

The bot installs or updates ADB itself when it starts, and vLLM downloads the model
when it first starts, so this only gets both out of the way up front.
"""

import hashlib
import os
import shutil
import tempfile
import zipfile

import requests
from loguru import logger
from tqdm import tqdm

from clashroyalebuildabot.constants.paths import ADB_DIR, ADB_PATH, APP_DIR

# Pinned, so every install gets the same ADB. To update, take the version
# from https://dl.google.com/android/repository/repository2-3.xml (which
# lists the zip's SHA-1) and record the zip's SHA-256 here.
ADB_VERSION = "37.0.3"
ADB_URL = (
    "https://dl.google.com/android/repository/"
    f"platform-tools_r{ADB_VERSION}-linux.zip"
)
ADB_SHA256 = "214548146cadb2ca3508143d8a1d4be4c59de5bb837253e3ede89ed74cf450d1"


def extract_zip(
    zip_path: str | os.PathLike[str], dest: str | os.PathLike[str]
) -> None:
    """Extract a zip, keeping Unix permissions such as the executable bit.

    zipfile.extractall drops them, which leaves adb unable to run.
    """
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        for info in zip_ref.infolist():
            path = zip_ref.extract(info, dest)
            mode = (info.external_attr >> 16) & 0o777
            if mode and not info.is_dir():
                os.chmod(path, mode)


def download(url: str, path: str | os.PathLike[str], sha256: str) -> None:
    """Download ``url`` to ``path``, failing if its SHA-256 isn't
    ``sha256``."""
    digest = hashlib.sha256()
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        with (
            open(path, "wb") as file,
            tqdm(
                desc=f"Downloading {os.path.basename(url)}",
                total=total or None,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar,
        ):
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                file.write(chunk)
                digest.update(chunk)
                pbar.update(len(chunk))
    if digest.hexdigest() != sha256:
        raise ValueError(
            f"{url} has SHA-256 {digest.hexdigest()}, expected {sha256}"
        )


def adb_installed() -> bool:
    return os.access(ADB_PATH, os.X_OK)


def installed_adb_version() -> str | None:
    """The version of the installed platform-tools, from the
    ``source.properties`` file Google ships in the zip."""
    try:
        with open(os.path.join(ADB_DIR, "source.properties")) as file:
            for line in file:
                key, _, value = line.partition("=")
                if key.strip() == "Pkg.Revision":
                    return value.strip()
    except OSError:
        pass
    return None


def adb_up_to_date() -> bool:
    return adb_installed() and installed_adb_version() == ADB_VERSION


def install_adb() -> None:
    """Install the pinned ADB, replacing any other version."""
    if os.path.isfile(ADB_PATH):
        version = installed_adb_version()
        if version == ADB_VERSION:
            # Earlier versions lost the executable bit when extracting.
            if not adb_installed():
                os.chmod(ADB_PATH, os.stat(ADB_PATH).st_mode | 0o111)
            logger.info(f"ADB {ADB_VERSION} is already installed")
            return
        logger.info(
            f"Updating ADB from {version or 'an unknown version'} "
            f"to {ADB_VERSION}"
        )

    # Download and extract in a temporary folder next to ADB_DIR, then move
    # the result into place in one step, so an interrupted install leaves
    # nothing behind that looks installed.
    with tempfile.TemporaryDirectory(dir=APP_DIR) as tmp:
        zip_path = os.path.join(tmp, os.path.basename(ADB_URL))
        download(ADB_URL, zip_path, ADB_SHA256)
        extract_zip(zip_path, tmp)
        # The old version, or what's left of an interrupted install.
        shutil.rmtree(ADB_DIR, ignore_errors=True)
        # The zip holds a platform-tools folder.
        os.replace(os.path.join(tmp, "platform-tools"), ADB_DIR)
    logger.info(f"Installed ADB {ADB_VERSION} in {ADB_DIR}")


def download_model(model: str) -> None:
    """Download the vision model into the Hugging Face cache, where vLLM
    looks for it, so the bot's first start doesn't wait for it."""
    from huggingface_hub import snapshot_download

    logger.info(f"Downloading {model} (about 1.7 GB)")
    path = snapshot_download(model)
    logger.info(f"{model} is in {path}")


def main() -> None:
    from clashroyalebuildabot.config import load_config

    install_adb()
    download_model(load_config().screen_detector.model)


if __name__ == "__main__":
    main()
