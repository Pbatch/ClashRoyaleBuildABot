import os

from loguru import logger
import yaml

from clashroyalebuildabot.constants import SRC_DIR


def load_config():
    try:
        config_path = os.path.join(SRC_DIR, "config.yaml")
        with open(config_path, encoding="utf-8") as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Can't parse config, stacktrace: {e}")
