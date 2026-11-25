import os

import pytest

import clashroyalebuildabot.constants.paths as constants

# Files the bot writes at runtime. They must live outside the package, so
# they don't conflict with git updates.
WRITTEN_AT_RUNTIME = [
    "USER_CONFIG_PATH",
    "DEBUG_DIR",
    "SCREENSHOTS_DIR",
    "LABELS_DIR",
    "ADB_DIR",
    "ADB_PATH",
]
# Files that ship with the bot and are only read.
SHIPPED = ["DEFAULT_CONFIG_PATH", "MODELS_DIR"]


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


def test_logo_is_in_the_project_folder():
    assert os.path.isfile(constants.LOGO_PATH)
    assert not _inside(constants.LOGO_PATH, constants.SRC_DIR)
