import io

import numpy as np
from PIL import Image
from ppadb.client import Client

from clashroyalebuildabot.data.constants import SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT


class Screen:
    def __init__(self, device_name="localhost:5555"):
        """Sets up the device screen

        Args:
            device_name (str, optional): The device's name in "adb devices". Defaults to "localhost:5555".
        """
        self.client = Client(host='127.0.0.1', port=5037)
        self.device = self.client.device(device_name)

    def take_screenshot(self):
        """
        Take a screenshot of the emulator
        """
        screenshot = self.device.screencap()
        screenshot = io.BytesIO(screenshot)
        screenshot = Image.open(screenshot).convert('RGB')
        screenshot = screenshot.resize((SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT), Image.BILINEAR)
        return screenshot

    def click(self, x, y):
        """
        Click at the given (x, y) coordinate
        """
        self.device.input_tap(x, y)


def main():
    cls = Screen()
    screenshot = cls.take_screenshot()
    print(np.array(screenshot).shape)
    screenshot.save('screen.jpg')


if __name__ == '__main__':
    main()
