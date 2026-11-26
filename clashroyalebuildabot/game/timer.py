"""The battle timer, read from the screen each step.

Where it is on the screen is fixed, so it lives in constants/screenshot.py
(``TIMER_BOX``), not here.
"""

import math

from pydantic.dataclasses import dataclass

UNKNOWN_TIME = math.inf


@dataclass(frozen=True)
class Timer:
    # Seconds left. In overtime, it counts down the overtime left.
    # UNKNOWN_TIME until read.
    time_left: float = UNKNOWN_TIME
    overtime: bool = False
