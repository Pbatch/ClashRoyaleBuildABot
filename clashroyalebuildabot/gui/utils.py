import os

from loguru import logger
from ruamel.yaml import YAML

from clashroyalebuildabot.constants import SRC_DIR

yaml = YAML()


def load_config():
    try:
        config_path = os.path.join(SRC_DIR, "config.yaml")
        with open(config_path, encoding="utf-8") as file:
            return yaml.load(file)
    except Exception as e:
        logger.error(f"Can't parse config, stacktrace: {e}")


def save_config(config):
    try:
        config_path = os.path.join(SRC_DIR, "config.yaml")
        with open(config_path, "w", encoding="utf-8") as file:
            yaml.dump(config, file)
    except Exception as e:
        logger.error(f"Can't save config, stacktrace: {e}")
