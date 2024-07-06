import cv2
import numpy as np

from loguru import logger

from PIL import ImageDraw
from PIL import ImageFont

from clashroyalebuildabot.constants import CARD_CONFIG
from clashroyalebuildabot.namespaces.units import NAME2UNIT


class Visualizer:
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

    def __init__(self):
        self.font = ImageFont.load_default()
        self.unit_names = [unit["name"] for unit in list(NAME2UNIT.values())]
        cv2.namedWindow("Visualizer", cv2.WINDOW_NORMAL)
        logger.info("Visualizer initialized.")


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

    def annotate_image(self, image, state):
        d = ImageDraw.Draw(image, "RGBA")
        for v in state.numbers.values():
            d.rectangle(tuple(v["bounding_box"]))
            self._draw_text(d, v["bounding_box"], str(v["number"]))

        self._draw_unit_bboxes(d, state.allies, "ally")
        self._draw_unit_bboxes(d, state.enemies, "enemy")

        for card, position in zip(state.cards, CARD_CONFIG):
            d.rectangle(tuple(position))
            self._draw_text(d, position, card.name)

        return image

    def run(self, image, state):
        annotated_image = self.annotate_image(image, state)
        annotated_image = np.array(annotated_image)
        cv2.imshow("Visualizer", cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
        cv2.waitKey(1)
