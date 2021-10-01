from PIL import ImageGrab, ImageOps
import win32gui
from win32api import GetSystemMetrics
import numpy as np


class Screen:
    APP_WIDTH = 400
    APP_HEIGHT = 684

    def __init__(self):
        self.bluestacks_id = win32gui.FindWindow(None, 'BlueStacks')
        self.system_width = GetSystemMetrics(0)
        self.system_height = GetSystemMetrics(1)
        print(self.system_height)

        win32gui.SetForegroundWindow(self.bluestacks_id)

    def move_and_resize_emulator(self):
        """
        Move the emulator to the top-right of the screen
        """
        # Move the window to the top-right of the screen
        # Resize to APP_WIDTH x APP_HEIGHT
        win32gui.MoveWindow(self.bluestacks_id,
                            self.system_width - self.APP_WIDTH,
                            0,
                            self.APP_WIDTH,
                            self.APP_HEIGHT,
                            True)

    def take_screenshot(self):
        """
        Take a screenshot of the emulator and crop out the BlueStacks border
        """
        screen = win32gui.GetWindowRect(self.bluestacks_id)
        screenshot = ImageGrab.grab(screen)

        # The border goes from the top-left, to the top-right, to the bottom-right
        border = (0, 32, 32, 0)
        screenshot = ImageOps.crop(screenshot, border)
        return screenshot


def main():
    cls = Screen()
    cls.move_and_resize_emulator()
    screenshot = cls.take_screenshot()
    print(np.array(screenshot).shape)
    screenshot.save('screen.jpg')


if __name__ == '__main__':
    main()
