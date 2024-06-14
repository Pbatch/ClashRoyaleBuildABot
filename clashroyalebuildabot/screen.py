import subprocess
from PIL import Image
from loguru import logger
from clashroyalebuildabot.data.constants import (
    SCREENSHOT_WIDTH,
    SCREENSHOT_HEIGHT,
)


class Screen:
    def __init__(self):
        try:
            window_size = subprocess.check_output(
                ["adb", "shell", "wm", "size"]
            )
            window_size = window_size.decode("ascii").replace(
                "Physical size: ", ""
            )
            self.width, self.height = [int(i) for i in window_size.split("x")]
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode("utf-8") if e.stderr else ""
            if "no devices/emulators found" in error_output:
                logger.critical(
                    "No Android devices or emulators found. Please connect a device or start an emulator."
                )
            elif "more than one device/emulator" in error_output:
                logger.critical(
                    "Multiple devices/emulators found. Please specify a target device using the -s option."
                )
            else:
                logger.error(f"Error getting screen size: {e}")
            logger.critical("Exiting due to device connection error.")
            raise SystemExit()

    @staticmethod
    def click(x, y):
        subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)])

    def take_screenshot(self):
        logger.debug("Starting to take screenshot...")
        try:
            screenshot_bytes = subprocess.run(
                ["adb", "exec-out", "screencap"],
                check=True,
                capture_output=True,
                timeout=10,
            ).stdout
            logger.debug("Screenshot captured successfully.")

            try:
                img = Image.frombuffer(
                    "RGBA",
                    (self.width, self.height),
                    screenshot_bytes[12:],
                    "raw",
                    "RGBX",
                    0,
                    1,
                )
                return img.convert("RGB").resize(
                    (SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT), Image.BILINEAR
                )
            except Exception as e:
                logger.warning(
                    f"Initial Image.frombuffer failed: {e}. Trying with header removed."
                )
                try:
                    img = Image.frombuffer(
                        "RGB", (self.width, self.height), screenshot_bytes
                    )
                    return img.resize(
                        (SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT), Image.BILINEAR
                    )
                except Exception as e:
                    logger.error(
                        f"Image creation failed after header adjustment: {e}"
                    )
                    raise

        except subprocess.CalledProcessError as e:
            logger.error(f"ADB command failed: {e.cmd}")
            logger.error(f"Error code: {e.returncode}")
            if e.stderr:
                logger.error(f"Stderr: {e.stderr.decode('utf-8')}")
            raise
