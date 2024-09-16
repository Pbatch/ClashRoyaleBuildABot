import os

from loguru import logger
import yaml

from clashroyalebuildabot.constants import SRC_DIR


def load_config():
    config = None
    try:
        config_path = os.path.join(SRC_DIR, "config.yaml")
        with open(config_path, encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Can't parse config, stacktrace: {e}")
    return config


def save_config(config):
    try:
        config_path = os.path.join(SRC_DIR, "config.yaml")
        with open(config_path, "w", encoding="utf-8") as file:
            yaml.dump(config, file)
    except Exception as e:
        logger.error(f"Can't save config, stacktrace: {e}")
