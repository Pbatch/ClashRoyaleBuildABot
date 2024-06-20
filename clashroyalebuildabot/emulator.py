import os
import sys

from adb_shell.adb_device import AdbDeviceTcp
from loguru import logger
from PIL import Image
import yaml

from clashroyalebuildabot.constants import SCREENSHOT_HEIGHT
from clashroyalebuildabot.constants import SCREENSHOT_WIDTH
from clashroyalebuildabot.constants import SRC_DIR


class Emulator:
    def __init__(self):
        config_path = os.path.join(SRC_DIR, "config.yaml")
        with open(config_path, encoding="utf-8") as file:
            config = yaml.safe_load(file)

        log_level = config.get("bot", {}).get("log_level", "INFO").upper()
        logger.remove()
        logger.add(sys.stdout, level=log_level)
        logger.add(
            os.path.join(SRC_DIR, "bot.log"),
            rotation="500 MB",
            level=log_level,
        )

        adb_config = config["adb"]
        device_ip = adb_config["ip"]
        device_port = adb_config["port"]

        self.device = AdbDeviceTcp(device_ip, device_port)

        try:
            self.device.connect()
            window_size = self.device.shell("wm size")
            window_size = window_size.replace("Physical size: ", "")
            self.size = tuple(int(i) for i in window_size.split("x"))
        except Exception as e:
            logger.critical(f"Error getting screen size: {e}")
            logger.critical("Exiting due to device connection error.")
            raise SystemExit() from e

    def click(self, x, y):
        self.device.shell(f"input tap {x} {y}")

    def _take_screenshot(self):
        screenshot_bytes = self.device.shell("screencap", decode=False)
        logger.debug("Screenshot captured successfully.")

        image = None
        try:
            image = Image.frombuffer(
                "RGBA",
                self.size,
                screenshot_bytes[12:],
                "raw",
                "RGBX",
                0,
                1,
            )
        except Exception as e:
            logger.warning(
                f"Initial Image.frombuffer failed: {e}. Trying with header removed."
            )

        if image is None:
            try:
                image = Image.frombuffer("RGB", self.size, screenshot_bytes)
            except Exception as e:
                logger.error(
                    f"Image creation failed after header adjustment: {e}"
                )

        image = image.convert("RGB")
        image = image.resize(
            (SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT), Image.Resampling.BILINEAR
        )

        return image

    def take_screenshot(self):
        logger.debug("Starting to take screenshot...")
        try:
            image = self._take_screenshot()
        except Exception as e:
            logger.error(f"ADB command failed: {e}")
            raise

        return image
