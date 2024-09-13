from dataclasses import asdict
import os

import numpy as np
from PIL import ImageDraw
from PIL import ImageFont
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import QObject

from clashroyalebuildabot.constants import CARD_CONFIG
from clashroyalebuildabot.constants import LABELS_DIR
from clashroyalebuildabot.constants import SCREENSHOTS_DIR
from clashroyalebuildabot.namespaces.numbers import NumberDetection
from clashroyalebuildabot.namespaces.units import NAME2UNIT


class Visualizer(QObject):
    _COLOUR_AND_RGBA = [
        ["navy", (0, 38, 63, 127)],
        ["blue", (0, 120, 210, 127)],
        ["aqua", (115, 221, 252, 127)],
        ["teal", (15, 205, 202, 127)],
        ["olive", (52, 153, 114, 127)],
        ["green", (0, 204, 84, 127)],
        ["lime", (1, 255, 127, 127)],
        ["yellow", (255, 216, 70, 127)],
        ["orange", (255, 125, 57, 127)],
        ["red", (255, 47, 65, 127)],
        ["maroon", (135, 13, 75, 127)],
        ["fuchsia", (246, 0, 184, 127)],
        ["purple", (179, 17, 193, 127)],
        ["gray", (168, 168, 168, 127)],
        ["silver", (220, 220, 220, 127)],
    ]

    frame_ready = pyqtSignal(np.ndarray)

    def __init__(self, save_labels, save_images, show_images):
        super().__init__()
        self.save_labels = save_labels
        self.save_images = save_images
        self.show_images = show_images

        self.font = ImageFont.load_default()
        self.unit_names = [unit["name"] for unit in list(NAME2UNIT.values())]

        os.makedirs(LABELS_DIR, exist_ok=True)
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    @staticmethod
    def _write_label(image, state, basename):
        labels = []
        for det in state.allies + state.enemies:
            bbox = det.position.bbox
            xc = (bbox[0] + bbox[2]) / (2 * image.width)
            yc = (bbox[1] + bbox[3]) / (2 * image.height)
            w = (bbox[2] - bbox[0]) / image.width
            h = (bbox[3] - bbox[1]) / image.height
            label = f"{det.unit.name} {xc} {yc} {w} {h}"
            labels.append(label)

        with open(
            os.path.join(LABELS_DIR, f"{basename}.txt"), "w", encoding="utf-8"
        ) as f:
            f.write("\n".join(labels))

    def _draw_text(self, d, bbox, text, rgba=(0, 0, 0, 255)):
        text_width, text_height = d.textbbox((0, 0), text, font=self.font)[2:]
        text_bbox = (
            bbox[0],
            bbox[1] - text_height,
            bbox[0] + text_width,
            bbox[1],
        )
        d.rectangle(text_bbox, fill=rgba)
        d.rectangle(tuple(bbox), outline=rgba)
        d.text(tuple(text_bbox[:2]), text=text, fill="white")

    def _draw_unit_bboxes(self, d, dets, prefix):
        for det in dets:
            colour_idx = self.unit_names.index(det.unit.name) % len(
                self._COLOUR_AND_RGBA
            )
            rgba = self._COLOUR_AND_RGBA[colour_idx][1]
            self._draw_text(
                d, det.position.bbox, f"{prefix}_{det.unit.name}", rgba
            )

    def _annotate_image(self, image, state):
        d = ImageDraw.Draw(image, "RGBA")
        for det in asdict(state.numbers).values():
            det = NumberDetection(**det)
            d.rectangle(det.bbox)
            self._draw_text(d, det.bbox, f"{det.number:.2f}")

        self._draw_unit_bboxes(d, state.allies, "ally")
        self._draw_unit_bboxes(d, state.enemies, "enemy")

        for card, position in zip(state.cards, CARD_CONFIG):
            d.rectangle(tuple(position))
            self._draw_text(d, position, card.name)

        return image

    def run(self, image, state):
        n_screenshots = len(os.listdir(SCREENSHOTS_DIR))
        n_labels = len(os.listdir(LABELS_DIR))
        basename = max(n_labels, n_screenshots) + 1

        if self.save_labels:
            self._write_label(image, state, basename)

        if not self.save_images and not self.show_images:
            return

        annotated_image = self._annotate_image(image, state)

        if self.save_images:
            annotated_image.save(
                os.path.join(SCREENSHOTS_DIR, f"{basename}.png")
            )

        if self.show_images:
            self.frame_ready.emit(np.array(annotated_image))
