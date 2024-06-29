import os

from adb_shell.adb_device import AdbDeviceTcp
from loguru import logger
from PIL import Image
import yaml

from clashroyalebuildabot.constants import SCREENSHOT_HEIGHT
from clashroyalebuildabot.constants import SCREENSHOT_WIDTH
from clashroyalebuildabot.constants import SRC_DIR
from clashroyalebuildabot.emulator.adbblitz import AdbShotTCP


class Emulator:
    def __init__(self):
        config_path = os.path.join(SRC_DIR, "config.yaml")
        with open(config_path, encoding="utf-8") as file:
            config = yaml.safe_load(file)

        adb_config = config["adb"]
        serial, ip, port = [
            adb_config[s] for s in ["device_serial", "ip", "port"]
        ]

        self.device = AdbDeviceTcp(ip, port)
        try:
            self.device.connect()
            window_size = self.device.shell("wm size")
            window_size = window_size.replace("Physical size: ", "")
            self.size = tuple(int(i) for i in window_size.split("x"))
        except Exception as e:
            logger.critical(f"Error getting screen size: {e}")
            logger.critical("Exiting due to device connection error.")
            raise SystemExit() from e

        self.blitz_device = AdbShotTCP(
            device_serial=serial,
            ip=ip,
            max_video_width=self.size[0],
        )

    def click(self, x, y):
        self.device.shell(f"input tap {x} {y}")

    def _take_screenshot(self):
        image = self.blitz_device.take_screenshot()
        image = Image.fromarray(image)
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
