import io
import subprocess

import numpy as np
from PIL import Image

from clashroyalebuildabot.data.constants import SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT


class Screen:
    @staticmethod
    def take_screenshot():
        """
        Take a screenshot of the emulator
        """
        screenshot_bytes = subprocess.check_output(['adb', 'exec-out', 'screencap', '-p'])
        if screenshot_bytes and len(screenshot_bytes) > 5 and screenshot_bytes[5] == 0x0d:
            screenshot_bytes = screenshot_bytes.replace(b'\r\n', b'\n')
        screenshot = io.BytesIO(screenshot_bytes)
        screenshot = Image.open(screenshot).convert('RGB')
        screenshot = screenshot.resize((SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT), Image.BILINEAR)
        return screenshot

    @staticmethod
    def click(x, y):
        """
        Click at the given (x, y) coordinate
        """
        subprocess.run(['adb', 'shell', 'input', 'tap', str(x), str(y)])


def main():
    cls = Screen()
    screenshot = cls.take_screenshot()
    print(np.array(screenshot).shape)
    screenshot.save('screen.jpg')


if __name__ == '__main__':
    main()
