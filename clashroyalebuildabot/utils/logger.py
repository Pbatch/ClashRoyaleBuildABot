import os
import sys

from loguru import logger
import yaml

from clashroyalebuildabot.constants import DEBUG_DIR
from clashroyalebuildabot.constants import SRC_DIR

COLORS = dict(context_info="#118aa2", time="#459028")


def setup_logger(main_window):
    config_path = os.path.join(SRC_DIR, "config.yaml")
    with open(config_path, encoding="utf-8") as file:
        config = yaml.safe_load(file)
    log_level = config.get("bot", {}).get("log_level", "INFO").upper()
    logger.remove()
    logger.add(sys.stdout, level=log_level)
    logger.add(
        os.path.join(DEBUG_DIR, "bot.log"),
        rotation="500 MB",
        level=log_level,
    )
    logger.add(
        main_window.log_handler_function,
        format="{time} {level} {module}:{function}:{line} - {message}",
        level=log_level,
    )


def colorize_log(message):
    log_record = message.record
    level = log_record["level"].name
    time = log_record["time"].strftime("%Y-%m-%d %H:%M:%S")
    module = log_record["module"]
    function = log_record["function"]
    line = log_record["line"]
    log_message = log_record["message"]

    if level == "DEBUG":
        color = "#147eb8"
    elif level == "INFO":
        color = "white"
        level = "INFO  "
    elif level == "WARNING":
        color = "orange"
    elif level == "ERROR":
        color = "red"
    else:
        color = "black"

    return f"""<span style="color:{COLORS['time']}">[{time}]</span>  <span style="color:{color}">{level}</span>     | <span style="color:{COLORS['context_info']}">{module}:{function}:{line}</span> - <span style="color:{color}">{log_message}</span></span>"""
