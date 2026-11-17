import os

import yaml

from clashroyalebuildabot.constants import (
    DEFAULT_CONFIG_PATH,
    USER_CONFIG_PATH,
)
from clashroyalebuildabot.utils.error_handling import WikifiedError

_USER_CONFIG_HEADER = """\
# Your settings. They override clashroyalebuildabot/default_config.yaml,
# so this file only needs the settings you want to change.
# Delete this file to go back to the defaults.

"""


def _merge(defaults: dict, overrides: dict) -> dict:
    """Return defaults with overrides applied, merging nested sections."""
    merged = dict(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _changes(config: dict, defaults: dict) -> dict:
    """Return only the parts of config that differ from defaults."""
    changes = {}
    for key, value in config.items():
        default = defaults.get(key)
        if isinstance(value, dict) and isinstance(default, dict):
            nested = _changes(value, default)
            if nested:
                changes[key] = nested
        elif key not in defaults or value != default:
            changes[key] = value
    return changes


def _read_yaml(path) -> dict:
    with open(path, encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping of settings")
    return data


def load_config(
    user_config_path=USER_CONFIG_PATH, default_config_path=DEFAULT_CONFIG_PATH
) -> dict:
    """The default settings, with the user's config.yaml applied on top."""
    try:
        config = _read_yaml(default_config_path)
        if os.path.exists(user_config_path):
            config = _merge(config, _read_yaml(user_config_path))
        return config
    except Exception as e:
        raise WikifiedError("002", "Can't parse config.") from e


def save_config(
    config: dict,
    user_config_path=USER_CONFIG_PATH,
    default_config_path=DEFAULT_CONFIG_PATH,
):
    """Save the settings that differ from the defaults to config.yaml."""
    try:
        changes = _changes(config, _read_yaml(default_config_path))
        with open(user_config_path, "w", encoding="utf-8") as file:
            file.write(_USER_CONFIG_HEADER)
            if changes:
                yaml.safe_dump(changes, file, sort_keys=False)
    except Exception as e:
        raise WikifiedError("009", "Can't save config.") from e
