import numpy as np
import win32gui
from PIL import Image
from mss import mss
from win32api import MAKELONG
from win32con import WM_LBUTTONUP, WM_LBUTTONDOWN, MK_LBUTTON

from src.data.constants import APP_WIDTH, APP_HEIGHT, BORDER_SIZE, SCREEN_WIDTH


class Screen:
    def __init__(self):
        self.bluestacks_id = win32gui.FindWindow(None, 'BlueStacks')

    @staticmethod
    def take_screenshot():
        """
        Take a screenshot of the emulator

        You MUST call `move_and_resize_emulator` first
        """
        bbox = (SCREEN_WIDTH - APP_WIDTH,
                BORDER_SIZE,
                SCREEN_WIDTH - BORDER_SIZE,
                APP_HEIGHT)
        with mss() as sct:
            screenshot = sct.grab(bbox)

        screenshot = np.array(screenshot, dtype=np.uint8)
        screenshot = np.flip(screenshot[:, :, :3], 2)
        screenshot = Image.fromarray(screenshot)

        return screenshot

    def _set_foreground_window(self):
        """
        Bring the emulator to the foreground
        """
        win32gui.SetForegroundWindow(self.bluestacks_id)

    def _move_and_resize_emulator(self):
        """
        Move the emulator to the top-right of the screen
        Resize the emulator to APP_WIDTH x APP_HEIGHT
        """
        win32gui.MoveWindow(self.bluestacks_id,
                            SCREEN_WIDTH - APP_WIDTH,
                            0,
                            APP_WIDTH,
                            APP_HEIGHT,
                            True)

    def click(self, x, y):
        """
        Click at the given (x, y) coordinate
        """
        screen = win32gui.FindWindowEx(self.bluestacks_id, None, None, None)
        l_param = MAKELONG(round(x), round(y))
        win32gui.SendMessage(screen, WM_LBUTTONDOWN, MK_LBUTTON, l_param)
        win32gui.SendMessage(screen, WM_LBUTTONUP, None, l_param)

    def reset(self):
        """
        Reset the size and position of the emulator
        """
        self._set_foreground_window()
        self._move_and_resize_emulator()


def main():
    cls = Screen()
    cls.reset()
    screenshot = cls.take_screenshot()
    print(np.array(screenshot).shape)
    screenshot.save('screen.jpg')


if __name__ == '__main__':
    main()
