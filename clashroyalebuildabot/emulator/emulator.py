import os
import subprocess

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

        self.blitz_device = AdbShotTCP(
            device_serial=f"localhost:{device_port}",
            adb_path=self._adb_path(),
            ip=device_ip,
            max_video_width=self.size[0]
        )

    @staticmethod
    def _adb_path():
        p = subprocess.run(["which", "adb"], capture_output=True, text=True, check=True)
        path = p.stdout.strip()
        path = path.replace('/', '\\')
        if path.startswith('\\'):
            path = f'{path[1].upper()}:{path[2:]}'

        return path

    def click(self, x, y):
        self.device.shell(f"input tap {x} {y}")

    def _take_screenshot(self):
        image = self.blitz_device.get_one_screenshot()
        image = Image.fromarray(image[..., ::-1])
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
