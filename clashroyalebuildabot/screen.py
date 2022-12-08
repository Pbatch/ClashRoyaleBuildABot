import subprocess

import numpy as np
from PIL import Image

from clashroyalebuildabot.data.constants import SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT


class Screen:
    def __init__(self):
        # Physical size: 720x1280 -> self.width = 720, self.height = 1280
        window_size = subprocess.check_output(['adb', 'shell', 'wm', 'size'])
        window_size = window_size.decode('ascii').replace('Physical size: ', '')
        self.width, self.height = [int(i) for i in window_size.split('x')]

    @staticmethod
    def click(x, y):
        """
        Click at the given (x, y) coordinate
        """
        subprocess.run(['adb', 'shell', 'input', 'tap', str(x), str(y)])

    def take_screenshot(self):
        """
        Take a screenshot of the emulator
        """
        screenshot_bytes = subprocess.run(['adb', 'exec-out', 'screencap'], check=True, capture_output=True).stdout
        screenshot = Image.frombuffer('RGBA', (self.width, self.height), screenshot_bytes[12:], 'raw', 'RGBX', 0, 1)
        screenshot = screenshot.convert('RGB').resize((SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT), Image.BILINEAR)
        return screenshot


def main():
    cls = Screen()
    screenshot = cls.take_screenshot()
    print(np.array(screenshot).shape)
    screenshot.save('screen.jpg')


if __name__ == '__main__':
    main()
