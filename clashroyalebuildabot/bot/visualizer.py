import os
from collections.abc import Callable, Iterator

import cv2
import numpy as np

from clashroyalebuildabot.constants.device_screen import tile_box
from clashroyalebuildabot.constants.paths import LABELS_DIR, SCREENSHOTS_DIR
from clashroyalebuildabot.constants.screenshot import (
    CARD_BOXES,
    ELIXIR_BOX,
    KING_TOWER_BOXES,
    PRINCESS_TOWER_BOXES,
    TIMER_BOX,
)
from clashroyalebuildabot.game.state import State
from clashroyalebuildabot.game.units import UnitDetection
from clashroyalebuildabot.utils.image import Box, save

type RGBA = tuple[int, int, int, int]
type FrameCallback = Callable[[np.ndarray], None]

WHITE: RGBA = (255, 255, 255, 255)
# Frames are RGB.
ALLY_RGBA: RGBA = (0, 200, 80, 200)
ENEMY_RGBA: RGBA = (230, 40, 50, 200)
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.35


def display_name(name: str) -> str:
    """baby_dragon as Baby Dragon."""
    return name.replace("_", " ").title()


class Visualizer:
    def __init__(
        self,
        save_labels: bool,
        save_images: bool,
        show_images: bool,
        labels_dir: str = LABELS_DIR,
        screenshots_dir: str = SCREENSHOTS_DIR,
        on_frame: FrameCallback | None = None,
    ) -> None:
        """on_frame receives each annotated frame when show_images is on.
        It is called on the bot's thread, so a GUI must hand the frame to
        its own thread before touching widgets."""
        self.save_labels = save_labels
        self.save_images = save_images
        self.show_images = show_images
        self.labels_dir = labels_dir
        self.screenshots_dir = screenshots_dir
        self.on_frame = on_frame

        os.makedirs(self.labels_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        self._next_index = self._find_next_index()

    def _find_next_index(self) -> int:
        """
        One past the highest numbered file already saved, so earlier runs
        are never overwritten. Scanned once here, not on every frame.
        """
        highest = 0
        for directory in (self.labels_dir, self.screenshots_dir):
            for name in os.listdir(directory):
                stem = os.path.splitext(name)[0]
                if stem.isdigit():
                    highest = max(highest, int(stem))
        return highest + 1

    def _write_label(
        self, image: np.ndarray, state: State, basename: int
    ) -> None:
        height, width = image.shape[:2]
        labels = []
        for det in state.allies + state.enemies:
            bbox = tile_box(det.position.tile_x, det.position.tile_y)
            xc = (bbox[0] + bbox[2]) / (2 * width)
            yc = (bbox[1] + bbox[3]) / (2 * height)
            w = (bbox[2] - bbox[0]) / width
            h = (bbox[3] - bbox[1]) / height
            label = f"{det.unit.name} {xc} {yc} {w} {h}"
            labels.append(label)

        with open(
            os.path.join(self.labels_dir, f"{basename}.txt"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write("\n".join(labels))

    @staticmethod
    def _rectangle(
        image: np.ndarray, bbox: Box, rgba: RGBA = WHITE, filled: bool = False
    ) -> None:
        """Draw a box, blended by the colour's alpha. Its corners are both
        inside it."""
        left, top, right, bottom = (round(v) for v in bbox)
        height, width = image.shape[:2]
        # Only the pixels the box covers are blended.
        x0, y0 = max(left, 0), max(top, 0)
        x1, y1 = min(right, width - 1), min(bottom, height - 1)
        if x0 > x1 or y0 > y1:
            return
        region = image[y0 : y1 + 1, x0 : x1 + 1]
        drawn = region.copy()
        cv2.rectangle(
            drawn,
            (left - x0, top - y0),
            (right - x0, bottom - y0),
            rgba[:3],
            cv2.FILLED if filled else 1,
        )
        alpha = rgba[3] / 255
        region[:] = cv2.addWeighted(drawn, alpha, region, 1 - alpha, 0)

    def _draw_text(
        self,
        image: np.ndarray,
        bbox: Box,
        text: str,
        rgba: RGBA = (0, 0, 0, 255),
    ) -> None:
        (text_width, text_height), baseline = cv2.getTextSize(
            text, FONT, FONT_SCALE, 1
        )
        text_height += baseline
        text_bbox = (
            bbox[0],
            bbox[1] - text_height,
            bbox[0] + text_width,
            bbox[1],
        )
        self._rectangle(image, text_bbox, rgba, filled=True)
        self._rectangle(image, bbox, rgba)
        cv2.putText(
            image,
            text,
            (int(bbox[0]), int(bbox[1] - baseline)),
            FONT,
            FONT_SCALE,
            WHITE[:3],
            1,
            cv2.LINE_AA,
        )

    def _draw_unit_labels(
        self, d: np.ndarray, dets: list[UnitDetection], rgba: RGBA
    ) -> None:
        """Each unit's name, on a tag of its side's colour, centred just
        below its tile."""
        for det in dets:
            left, _, right, bottom = tile_box(
                det.position.tile_x, det.position.tile_y
            )
            name = display_name(det.unit.name)
            (text_width, text_height), baseline = cv2.getTextSize(
                name, FONT, FONT_SCALE, 1
            )
            x = round((left + right - text_width) / 2)
            top = round(bottom)
            self._rectangle(
                d,
                (x, top, x + text_width, top + text_height + baseline),
                rgba,
                filled=True,
            )
            cv2.putText(
                d,
                name,
                (x, top + text_height),
                FONT,
                FONT_SCALE,
                WHITE[:3],
                1,
                cv2.LINE_AA,
            )

    @staticmethod
    def _number_labels(state: State) -> Iterator[tuple[Box, str]]:
        """Where to draw each number, and what to write there."""
        yield ELIXIR_BOX, f"{state.elixir}"
        boxes = {**PRINCESS_TOWER_BOXES, **KING_TOWER_BOXES}
        for name, tower in state.towers.items():
            yield boxes[name], f"{tower.hp:g}"
        timer = state.timer
        overtime = " OT" if timer.overtime else ""
        yield TIMER_BOX, f"{timer.time_left:g}s{overtime}"

    def _annotate_image(self, image: np.ndarray, state: State) -> np.ndarray:
        # Drawn on a copy: the emulator hands the same frame out again when
        # the screen doesn't change, and it must reach the detectors clean.
        d = image.copy()
        for bbox, text in self._number_labels(state):
            self._rectangle(d, bbox)
            self._draw_text(d, bbox, text)

        self._draw_unit_labels(d, state.allies, ALLY_RGBA)
        self._draw_unit_labels(d, state.enemies, ENEMY_RGBA)

        for card, position in zip(state.cards, CARD_BOXES, strict=False):
            self._rectangle(d, position)
            self._draw_text(
                d,
                position,
                "Empty" if card is None else display_name(card.name),
            )

        return d

    def run(self, image: np.ndarray, state: State) -> None:

        # A frame's label and screenshot share one number.
        basename = self._next_index
        if self.save_labels or self.save_images:
            self._next_index += 1

        if self.save_labels:
            self._write_label(image, state, basename)

        if not self.save_images and not self.show_images:
            return

        annotated_image = self._annotate_image(image, state)

        if self.save_images:
            save(
                os.path.join(self.screenshots_dir, f"{basename}.png"),
                annotated_image,
            )

        if self.show_images and self.on_frame is not None:
            self.on_frame(annotated_image)
