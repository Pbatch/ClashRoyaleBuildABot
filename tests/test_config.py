import shutil

import pytest
import yaml

from clashroyalebuildabot.config import Config, load_config, save_config
from clashroyalebuildabot.constants.paths import DEFAULT_CONFIG_PATH
from clashroyalebuildabot.utils.error_handling import WikifiedError


@pytest.fixture
def defaults_path(tmp_path):
    path = tmp_path / "default_config.yaml"
    shutil.copy(DEFAULT_CONFIG_PATH, path)
    return path


@pytest.fixture
def user_path(tmp_path):
    return tmp_path / "config.yaml"


@pytest.fixture
def defaults(defaults_path, user_path):
    return load_config(user_path, defaults_path)


def write(path, text):
    path.write_text(text, encoding="utf-8")


def test_shipped_defaults_load(defaults):
    assert isinstance(defaults, Config)
    assert defaults.ingame.play_action == 1


def test_user_config_overrides_and_keeps_other_defaults(
    defaults, defaults_path, user_path
):
    write(user_path, "bot:\n  log_level: ERROR\n")

    config = load_config(user_path, defaults_path)

    assert config.bot.log_level == "ERROR"
    assert config.bot.load_deck == defaults.bot.load_deck
    assert config.ingame == defaults.ingame


def test_empty_user_config_means_defaults(defaults, defaults_path, user_path):
    write(user_path, "# nothing changed\n")
    assert load_config(user_path, defaults_path) == defaults


def test_log_level_is_case_insensitive(defaults_path, user_path):
    write(user_path, "bot:\n  log_level: warning\n")
    assert load_config(user_path, defaults_path).bot.log_level == "WARNING"


def test_numeric_device_serial_is_read_as_text(defaults_path, user_path):
    write(user_path, "adb:\n  device_serial: 12345\n")
    assert load_config(user_path, defaults_path).adb.device_serial == "12345"


def test_non_mapping_user_config_raises_e002(defaults_path, user_path):
    write(user_path, "- not\n- a mapping\n")
    with pytest.raises(WikifiedError, match="E002"):
        load_config(user_path, defaults_path)


@pytest.mark.parametrize(
    ("text", "setting"),
    [
        ("ingame:\n  play_actoin: 1.5\n", "ingame.play_actoin"),
        ("ingame:\n  play_action: fast\n", "ingame.play_action"),
        ("ingame:\n  play_action: 0\n", "ingame.play_action"),
        ("bot:\n  log_level: LOUD\n", "bot.log_level"),
        ("visual:\n  show_images: true\n", "visual"),
    ],
)
def test_invalid_setting_raises_e002_naming_it(
    defaults_path, user_path, text, setting
):
    write(user_path, text)
    with pytest.raises(WikifiedError, match="E002") as e:
        load_config(user_path, defaults_path)
    assert setting in str(e.value)


def test_gui_assignment_is_validated(defaults):
    with pytest.raises(ValueError, match="greater than 0"):
        defaults.ingame.play_action = -1


def test_old_screen_detector_settings_are_ignored(defaults_path, user_path):
    # Written by a version of the bot that had a vision model.
    write(
        user_path,
        "bot:\n  log_level: ERROR\n"
        "screen_detector:\n  base_url: http://gpu-box:9000\n",
    )
    config = load_config(user_path, defaults_path)
    assert config.bot.log_level == "ERROR"
    assert "screen_detector" not in config.model_dump()


def test_save_writes_only_changed_settings(defaults, defaults_path, user_path):
    defaults.ingame.play_action = 1.5

    save_config(defaults, user_path, defaults_path)

    saved = yaml.safe_load(user_path.read_text(encoding="utf-8"))
    assert saved == {"ingame": {"play_action": 1.5}}


def test_save_then_load_round_trips(defaults, defaults_path, user_path):
    defaults.bot.load_deck = not defaults.bot.load_deck

    save_config(defaults, user_path, defaults_path)

    assert load_config(user_path, defaults_path) == defaults


def test_saving_defaults_writes_no_settings(
    defaults, defaults_path, user_path
):
    save_config(defaults, user_path, defaults_path)
    assert yaml.safe_load(user_path.read_text(encoding="utf-8")) is None


def test_save_failure_raises_e009(defaults, defaults_path, tmp_path):
    with pytest.raises(WikifiedError, match="E009"):
        save_config(
            defaults, tmp_path / "missing" / "config.yaml", defaults_path
        )


def test_save_never_touches_the_defaults(defaults, defaults_path, user_path):
    before = defaults_path.read_text(encoding="utf-8")
    defaults.bot.log_level = "ERROR"
    save_config(defaults, user_path, defaults_path)
    assert defaults_path.read_text(encoding="utf-8") == before
