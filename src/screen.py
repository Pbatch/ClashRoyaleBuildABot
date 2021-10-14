from PIL import ImageGrab, ImageOps
import win32gui
from win32api import GetSystemMetrics, MAKELONG
from win32con import WM_LBUTTONDOWN, WM_LBUTTONUP, MK_LBUTTON
import numpy as np
from src.data.constants import APP_WIDTH, APP_HEIGHT, BORDER_SIZE


class Screen:
    def __init__(self):
        self.bluestacks_id = win32gui.FindWindow(None, 'BlueStacks')
        self.system_width = GetSystemMetrics(0)
        self.system_height = GetSystemMetrics(1)

        win32gui.SetForegroundWindow(self.bluestacks_id)

    def move_and_resize_emulator(self):
        """
        Move the emulator to the top-right of the screen
        """
        # Move the window to the top-right of the screen
        # Resize to APP_WIDTH x APP_HEIGHT
        win32gui.MoveWindow(self.bluestacks_id,
                            self.system_width - APP_WIDTH,
                            0,
                            APP_WIDTH,
                            APP_HEIGHT,
                            True)

    def take_screenshot(self):
        """
        Take a screenshot of the emulator and crop out the BlueStacks border
        """
        screen = win32gui.GetWindowRect(self.bluestacks_id)
        screenshot = ImageGrab.grab(screen)

        # The border goes from the top-left, to the top-right, to the bottom-right
        border = (0, BORDER_SIZE, BORDER_SIZE, 0)
        screenshot = ImageOps.crop(screenshot, border)
        return screenshot

    def click(self, x, y):
        """
        Click at the given (x, y) coordinate
        """
        screen = win32gui.FindWindowEx(self.bluestacks_id, None, None, None)
        lParam = MAKELONG(round(x), round(y))
        win32gui.SendMessage(screen, WM_LBUTTONDOWN, MK_LBUTTON, lParam)
        win32gui.SendMessage(screen, WM_LBUTTONUP, None, lParam)


def main():
    cls = Screen()
    cls.move_and_resize_emulator()
    screenshot = cls.take_screenshot()
    print(np.array(screenshot).shape)
    screenshot.save('screen.jpg')


if __name__ == '__main__':
    main()
