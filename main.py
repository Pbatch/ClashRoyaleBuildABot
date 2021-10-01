from screen import Screen
from ocr import OCR
import time


def main():
    from pprint import pprint
    screen = Screen()
    ocr = OCR()
    screen.move_and_resize_emulator()
    while True:
        screenshot = screen.take_screenshot()
        details = ocr.run(screenshot)
        pprint(details)
        time.sleep(1)


if __name__ == '__main__':
    main()