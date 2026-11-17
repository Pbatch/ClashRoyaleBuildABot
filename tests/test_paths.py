import importlib
import os
import sys

import pytest

import clashroyalebuildabot.constants as constants

# Files the bot writes at runtime. They must live outside the package, so
# they don't conflict with git updates and survive in the PyInstaller .exe
# (which unpacks the package to a temporary folder on every run).
WRITTEN_AT_RUNTIME = [
    "USER_CONFIG_PATH",
    "DEBUG_DIR",
    "SCREENSHOTS_DIR",
    "LABELS_DIR",
    "ADB_DIR",
    "ADB_PATH",
]
# Files that ship with the bot and are only read.
SHIPPED = ["DEFAULT_CONFIG_PATH", "MODELS_DIR", "IMAGES_DIR"]


def _inside(path, directory):
    path, directory = os.path.abspath(path), os.path.abspath(directory)
    return os.path.commonpath([path, directory]) == directory


@pytest.mark.parametrize("name", WRITTEN_AT_RUNTIME)
def test_runtime_files_are_outside_the_package(name):
    path = getattr(constants, name)
    assert not _inside(path, constants.SRC_DIR)
    assert _inside(path, constants.APP_DIR)


@pytest.mark.parametrize("name", SHIPPED)
def test_shipped_files_are_inside_the_package(name):
    assert _inside(getattr(constants, name), constants.SRC_DIR)


def test_app_dir_is_next_to_the_exe_when_frozen(monkeypatch, tmp_path):
    exe = tmp_path / "ClashRoyaleBot.exe"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))
    try:
        frozen = importlib.reload(constants)
        assert frozen.APP_DIR == str(tmp_path)
        assert frozen.USER_CONFIG_PATH == str(tmp_path / "config.yaml")
        assert frozen.DEBUG_DIR == str(tmp_path / "debug")
    finally:
        monkeypatch.undo()
        importlib.reload(constants)
