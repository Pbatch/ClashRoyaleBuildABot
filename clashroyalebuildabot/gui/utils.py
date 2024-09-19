import os

import yaml

from clashroyalebuildabot.constants import SRC_DIR
from error_handling import WikifiedError


def load_config():
    try:
        config_path = os.path.join(SRC_DIR, "config.yaml")
        with open(config_path, encoding="utf-8") as file:
            return yaml.safe_load(file)
    except Exception as e:
        raise WikifiedError("002", "Can't parse config.") from e


def save_config(config):
    try:
        config_path = os.path.join(SRC_DIR, "config.yaml")
        with open(config_path, "w", encoding="utf-8") as file:
            yaml.dump(config, file)
    except Exception as e:
        raise WikifiedError("000", "Can't save config.") from e
