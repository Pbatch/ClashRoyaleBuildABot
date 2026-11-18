import math

from PIL import Image

from clashroyalebuildabot.constants.screenshot import TIMER_BOX
from clashroyalebuildabot.detectors.timer_reader import (
    CROP_SCALE,
    TimerReader,
    TimerReading,
)
from clashroyalebuildabot.detectors.vlm_client import VisionError
from clashroyalebuildabot.game.numbers import UNKNOWN_TIME, Timer


class FakeClient:
    def __init__(self, minutes=1, seconds=57, overtime=False):
        self.answer = TimerReading(
            overtime=overtime, minutes=minutes, seconds=seconds
        )
        self.fail = False
        self.crops = []

    def ask(self, image, prompt, schema):
        assert schema is TimerReading
        self.crops.append(image.size)
        if self.fail:
            raise VisionError("down")
        return self.answer


def frame():
    return Image.new("RGB", (368, 652))


def read_in_background(reader):
    reader.run(frame())
    reader.wait(5)
    return reader.latest()


def test_reads_seconds_left_from_an_enlarged_crop():
    client = FakeClient(minutes=1, seconds=57)
    reading = TimerReader(client).read(frame())
    assert reading == Timer(time_left=117, overtime=False)
    left, top, right, bottom = TIMER_BOX
    assert client.crops == [
        ((right - left) * CROP_SCALE, (bottom - top) * CROP_SCALE)
    ]


def test_reads_overtime():
    reading = TimerReader(FakeClient(0, 42, overtime=True)).read(frame())
    assert reading.time_left == 42
    assert reading.overtime is True


def test_unknown_until_first_reading():
    reader = TimerReader(FakeClient())
    assert reader.latest().time_left == UNKNOWN_TIME
    assert reader.latest().overtime is False
    reader.close()


def test_failed_reading_keeps_the_previous_one():
    client = FakeClient(1, 57)
    reader = TimerReader(client, interval=0)
    read_in_background(reader)

    client.fail = True
    assert read_in_background(reader).time_left == 117
    reader.close()


def test_failed_first_reading_stays_unknown():
    client = FakeClient()
    client.fail = True
    reading = TimerReader(client).read(frame())
    assert math.isinf(reading.time_left)


def test_reset_forgets_the_reading():
    reader = TimerReader(FakeClient(), interval=0)
    assert read_in_background(reader).time_left == 117
    reader.reset()
    assert math.isinf(reader.latest().time_left)
    reader.close()
