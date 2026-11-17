import pytest
import yaml

from clashroyalebuildabot.constants import DEFAULT_CONFIG_PATH
from clashroyalebuildabot.gui.utils import load_config, save_config
from clashroyalebuildabot.utils.error_handling import WikifiedError

DEFAULTS = {
    "bot": {"log_level": "INFO", "load_deck": False},
    "ingame": {"play_action": 1},
}


@pytest.fixture
def defaults_path(tmp_path):
    path = tmp_path / "default_config.yaml"
    path.write_text(yaml.safe_dump(DEFAULTS), encoding="utf-8")
    return path


@pytest.fixture
def user_path(tmp_path):
    return tmp_path / "config.yaml"


def test_defaults_used_when_no_user_config(defaults_path, user_path):
    assert load_config(user_path, defaults_path) == DEFAULTS


def test_user_config_overrides_and_keeps_other_defaults(
    defaults_path, user_path
):
    user_path.write_text("bot:\n  log_level: DEBUG\n", encoding="utf-8")

    config = load_config(user_path, defaults_path)

    assert config["bot"] == {"log_level": "DEBUG", "load_deck": False}
    assert config["ingame"] == {"play_action": 1}


def test_empty_user_config_means_defaults(defaults_path, user_path):
    user_path.write_text("# nothing changed\n", encoding="utf-8")
    assert load_config(user_path, defaults_path) == DEFAULTS


def test_invalid_user_config_raises_e002(defaults_path, user_path):
    user_path.write_text("- not\n- a mapping\n", encoding="utf-8")
    with pytest.raises(WikifiedError, match="E002"):
        load_config(user_path, defaults_path)


def test_save_writes_only_changed_settings(defaults_path, user_path):
    config = load_config(user_path, defaults_path)
    config["ingame"]["play_action"] = 1.5

    save_config(config, user_path, defaults_path)

    saved = yaml.safe_load(user_path.read_text(encoding="utf-8"))
    assert saved == {"ingame": {"play_action": 1.5}}


def test_save_then_load_round_trips(defaults_path, user_path):
    config = load_config(user_path, defaults_path)
    config["bot"]["load_deck"] = True

    save_config(config, user_path, defaults_path)

    assert load_config(user_path, defaults_path) == config


def test_saving_defaults_writes_no_settings(defaults_path, user_path):
    save_config(
        load_config(user_path, defaults_path), user_path, defaults_path
    )
    assert yaml.safe_load(user_path.read_text(encoding="utf-8")) is None


def test_save_failure_raises_e009(defaults_path, tmp_path):
    with pytest.raises(WikifiedError, match="E009"):
        save_config(
            DEFAULTS, tmp_path / "missing" / "config.yaml", defaults_path
        )


def test_save_never_touches_the_defaults(defaults_path, user_path):
    before = defaults_path.read_text(encoding="utf-8")
    save_config({"bot": {"log_level": "ERROR"}}, user_path, defaults_path)
    assert defaults_path.read_text(encoding="utf-8") == before


def test_shipped_defaults_load():
    config = load_config(DEFAULT_CONFIG_PATH + ".missing", DEFAULT_CONFIG_PATH)
    for section in ("bot", "adb", "visuals", "ingame"):
        assert section in config
