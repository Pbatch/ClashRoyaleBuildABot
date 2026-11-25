"""The bot's settings.

The defaults, with what each setting does, are in default_config.yaml. The
user's config.yaml holds only the settings they changed, and is applied on
top. The models below give the settings their types: they have no defaults
of their own, so default_config.yaml stays the one place defaults live, and
a misspelt setting or a value of the wrong type is an error rather than
silently ignored.
"""

import os
from typing import Literal

import yaml
from loguru import logger
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)

from clashroyalebuildabot.constants.paths import (
    DEFAULT_CONFIG_PATH,
    USER_CONFIG_PATH,
)
from clashroyalebuildabot.utils.error_handling import WikifiedError

# A file path, as a string or a pathlib.Path.
type StrPath = str | os.PathLike[str]


_USER_CONFIG_HEADER = """\
# Your settings. They override clashroyalebuildabot/default_config.yaml,
# so this file only needs the settings you want to change.
# Delete this file to go back to the defaults.

"""

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class _Section(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        # The GUI sets values after loading, so check those too.
        validate_assignment=True,
        # YAML reads a serial like 12345 as a number.
        coerce_numbers_to_str=True,
    )


class BotConfig(_Section):
    log_level: LogLevel
    load_deck: bool
    auto_start_game: bool

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_case(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value


class AdbConfig(_Section):
    device_serial: str


class VisualsConfig(_Section):
    save_labels: bool
    save_images: bool
    show_images: bool


class IngameConfig(_Section):
    play_action: float = Field(gt=0)


class Config(_Section):
    bot: BotConfig
    adb: AdbConfig
    visuals: VisualsConfig
    ingame: IngameConfig


# Sections older versions of the bot had. A user's config.yaml may still
# have them; they're ignored rather than refused.
_REMOVED_SECTIONS = ("screen_detector",)


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


def _read_yaml(path: StrPath) -> dict:
    with open(path, encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping of settings")
    return data


def _describe(error: ValidationError) -> str:
    """One line per bad setting, e.g. ``bot.log_level: Input should be...``"""
    lines = []
    for e in error.errors():
        setting = ".".join(str(part) for part in e["loc"])
        if e["type"] == "extra_forbidden":
            message = "unknown setting (check its spelling and section)"
        else:
            message = e["msg"]
        lines.append(f"  {setting}: {message}")
    return "\n".join(lines)


def load_config(
    user_config_path: StrPath = USER_CONFIG_PATH,
    default_config_path: StrPath = DEFAULT_CONFIG_PATH,
) -> Config:
    """The default settings, with the user's config.yaml applied on top."""
    try:
        data = _read_yaml(default_config_path)
        if os.path.exists(user_config_path):
            user = _read_yaml(user_config_path)
            for section in _REMOVED_SECTIONS:
                if user.pop(section, None) is not None:
                    logger.warning(
                        f"Ignoring the {section} settings in "
                        f"{user_config_path}: the bot no longer uses them."
                    )
            data = _merge(data, user)
        return Config.model_validate(data)
    except ValidationError as e:
        raise WikifiedError(
            "002", f"Invalid settings in config:\n{_describe(e)}\n"
        ) from e
    except Exception as e:
        raise WikifiedError("002", "Can't parse config.") from e


def save_config(
    config: Config,
    user_config_path: StrPath = USER_CONFIG_PATH,
    default_config_path: StrPath = DEFAULT_CONFIG_PATH,
) -> None:
    """Save the settings that differ from the defaults to config.yaml."""
    try:
        defaults = Config.model_validate(_read_yaml(default_config_path))
        changes = _changes(config.model_dump(), defaults.model_dump())
        with open(user_config_path, "w", encoding="utf-8") as file:
            file.write(_USER_CONFIG_HEADER)
            if changes:
                yaml.safe_dump(changes, file, sort_keys=False)
    except Exception as e:
        raise WikifiedError("009", "Can't save config.") from e


def apply_changes(config: Config, changes: dict) -> None:
    """Apply some settings, e.g. ``{"bot": {"load_deck": True}}``, to
    config in place, so everything holding it sees them. They're all checked
    first, so a bad value changes nothing. Raises pydantic's
    ValidationError."""
    updated = Config.model_validate(_merge(config.model_dump(), changes))
    for section in Config.model_fields:
        target = getattr(config, section)
        source = getattr(updated, section)
        for name in type(target).model_fields:
            setattr(target, name, getattr(source, name))
