import subprocess
from loguru import logger


def adb_fix():
    try:
        result = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, check=True
        )
        devices = result.stdout.strip().splitlines()[1:]

        devices = [
            line.split()[0] for line in devices if "unauthorized" not in line
        ]

        logger.debug(f"Connected ADB devices: {devices}")

        if len(devices) == 1:
            logger.debug("Exactly one ADB device is connected.")
            return True
        elif len(devices) > 1:
            logger.warning(
                "More than one ADB device is connected. Attempting to disconnect 127.0.0.1:5555."
            )
            subprocess.run(["adb", "disconnect", "127.0.0.1:5555"], check=True)
            return False
        else:
            logger.debug(
                "No ADB devices connected. Attempting to connect to 127.0.0.1:5555."
            )
            subprocess.run(["adb", "connect", "127.0.0.1:5555"], check=True)
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"An error occurred in adb_fix: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred in adb_fix: {e}")
        return False
