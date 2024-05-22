import subprocess
from loguru import logger

def adb_fix():
    try:
        # List all adb devices
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        devices = result.stdout.splitlines()[1:-1]  # Skip the first line which is a header
        
        # Filter out empty lines and unauthorized devices
        devices = [line for line in devices if line.strip() and "unauthorized" not in line]

        # Log the current connected devices
        logger.info(f"Connected ADB devices: {devices}")

        if len(devices) == 1:
            logger.info("Exactly one ADB device is connected.")
            return
        elif len(devices) > 1:
            logger.warning("More than one ADB device is connected. Attempting to disconnect 127.0.0.1:5555.")
            subprocess.run(["adb", "disconnect", "127.0.0.1:5555"])
        else:
            logger.info("No ADB devices connected. Attempting to connect to 127.0.0.1:5555.")
            subprocess.run(["adb", "connect", "127.0.0.1:5555"])
    except Exception as e:
        logger.error(f"An error occurred in adb_fix: {e}")