import os

from PIL import ImageDraw
from PIL import ImageFont

from clashroyalebuildabot.data.constants import CARD_CONFIG
from clashroyalebuildabot.data.constants import LABELS_DIR
from clashroyalebuildabot.data.constants import SCREENSHOTS_DIR
from clashroyalebuildabot.data.constants import UNITS


class Debugger:
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
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        os.makedirs(LABELS_DIR, exist_ok=True)
        self.font = ImageFont.load_default()

    @staticmethod
    def _write_label(image, state, basename):
        labels = []
        for side in ["ally", "enemy"]:
            for unit_name, v in state["units"][side].items():
                for i in v["positions"]:
                    bbox = i["bounding_box"]
                    xc = (bbox[0] + bbox[2]) / (2 * image.width)
                    yc = (bbox[1] + bbox[3]) / (2 * image.height)
                    w = (bbox[2] - bbox[0]) / image.width
                    h = (bbox[3] - bbox[1]) / image.height
                    label = f"{unit_name} {xc} {yc} {w} {h}"
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

    def _write_image(self, image, state, basename):
        d = ImageDraw.Draw(image, "RGBA")
        for v in state["numbers"].values():
            d.rectangle(tuple(v["bounding_box"]))
            self._draw_text(d, v["bounding_box"], str(v["number"]))

        for side in ["ally", "enemy"]:
            for unit_name, v in state["units"][side].items():
                colour_idx = UNITS.index(unit_name) % len(
                    self._COLOUR_AND_RGBA
                )
                rgba = self._COLOUR_AND_RGBA[colour_idx][1]
                for i in v["positions"]:
                    self._draw_text(d, i["bounding_box"], unit_name, rgba)

        for card, position in zip(state["cards"], CARD_CONFIG):
            d.rectangle(tuple(position))
            self._draw_text(d, position, card["name"])

        image.save(os.path.join(SCREENSHOTS_DIR, f"{basename}.png"))

    def run(self, image, state):
        n_screenshots = len(os.listdir(SCREENSHOTS_DIR))
        n_labels = len(os.listdir(LABELS_DIR))
        basename = max(n_labels, n_screenshots) + 1

        self._write_image(image, state, basename)
        self._write_label(image, state, basename)
