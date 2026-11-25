"""Read numbers in the battle screenshot by matching the game's digits.

Tower HP and the timer are drawn as light digits with a dark outline, in the
game's own font. Every digit of that font is matched across a crop, and the
number is the left-to-right chain of matches, spaced as the font spaces
them, that matches best.

The matching works on each pixel's darkest channel. The digits' fill is
white, pale pink or pale blue, so it stays bright, while the coloured bars,
the grass and the gold badges all turn dark.

The templates were rendered from the font in the game's APK at the sizes
the digits appear on screen, and are loaded from models/digit_glyphs.npz.
"""

import json
import os
import re
from dataclasses import dataclass
from functools import cache

import cv2
import numpy as np

from clashroyalebuildabot.constants.paths import MODELS_DIR

GLYPHS_PATH = os.path.join(MODELS_DIR, "digit_glyphs.npz")
# Crops are enlarged this much before matching, for sub-pixel placement.
UPSCALE = 4
DIGITS = "0123456789"
# A digit counts as a match from this score (normalised correlation).
MIN_MATCH = 0.45
# How far a digit may sit from where the font would put it, as a share of
# the previous digit's width (plus one screenshot pixel).
SPACING_TOL = 0.18
# A tower's HP is accepted from this mean match score. Below it are rubble,
# badges and sparks that happen to look like a digit or two.
MIN_HP_SCORE = 0.72
# A lone digit has to match better still: on its own, a badge edge looks
# like a 1.
MIN_LONE_DIGIT_SCORE = 0.92
MIN_TIMER_MATCH = 0.6
_TIME = re.compile(r"(\d):(\d\d)")


@dataclass(frozen=True)
class Template:
    image: np.ndarray  # the glyph's fill as 1, its outline as 0
    mask: np.ndarray  # where the glyph or its outline is
    advance: float  # how far the font moves on after it, upscaled pixels
    left: int  # its left edge relative to the pen position


@dataclass(frozen=True)
class Reading:
    text: str
    # The digits' mean match score.
    score: float
    # Their summed scores above MIN_MATCH, each weighted by the digit's
    # width, so a reading is scored by how much of it matches.
    total: float


@cache
def _glyphs() -> tuple[dict, dict, dict]:
    """(digit templates by height, label templates, metadata)."""
    data = np.load(GLYPHS_PATH)
    meta = json.loads(str(data["meta"]))
    digits = {}
    for height, chars in meta["digits"].items():
        digits[height] = {
            c: Template(
                data[f"d{height}_{c}_fill"].astype(np.float32) / 255,
                data[f"d{height}_{c}_mask"].astype(np.float32),
                m["advance"],
                m["left"],
            )
            for c, m in chars.items()
        }
    labels = {
        over == "true": [
            (
                data[f"l_{key}_fill"].astype(np.float32) / 255,
                data[f"l_{key}_mask"].astype(np.float32),
            )
            for key in keys
        ]
        for over, keys in meta["labels"].items()
    }
    return digits, labels, meta


def text_map(crop: np.ndarray) -> np.ndarray:
    """The crop's darkest channel, enlarged: light text, dark everything
    else."""
    dark = crop.min(axis=2).astype(np.float32) / 255
    h, w = dark.shape
    return cv2.resize(
        dark, (w * UPSCALE, h * UPSCALE), interpolation=cv2.INTER_CUBIC
    )


def _match(image: np.ndarray, image_t: np.ndarray, mask: np.ndarray):
    if image_t.shape[0] > image.shape[0] or image_t.shape[1] > image.shape[1]:
        return None
    scores = cv2.matchTemplate(image, image_t, cv2.TM_CCOEFF_NORMED, mask=mask)
    return np.nan_to_num(scores, nan=-1, posinf=-1, neginf=-1)


def _decode(
    image: np.ndarray, temps: dict, max_len: int, min_match: float, gap: float
) -> Reading | None:
    """The best left-to-right chain of digits on one line of text."""
    maps = {c: _match(image, t.image, t.mask) for c, t in temps.items()}
    maps = {c: m for c, m in maps.items() if m is not None}
    if not maps:
        return None
    chars = list(maps)
    rows = min(m.shape[0] for m in maps.values())
    cols = min(m.shape[1] for m in maps.values())
    stack = np.stack([maps[c][:rows, :cols] for c in chars])
    # The digits share a line: try the rows where the best matches are, and
    # let each digit sit up to half a screenshot pixel off them.
    best = None
    row_scores = stack.max(axis=(0, 2))
    for y in np.argsort(row_scores)[::-1][:3]:
        lo = max(0, y - UPSCALE // 2)
        hi = min(rows, y + UPSCALE // 2 + 1)
        line = stack[:, lo:hi].max(axis=1)
        reading = _chain(line, chars, temps, max_len, min_match, gap)
        if reading and (best is None or reading.total > best.total):
            best = reading
    return best


def _chain(line, chars, temps, max_len, min_match, gap) -> Reading | None:
    """Each digit's peaks along the line, joined into the best chain.

    Candidates are visited left to right, and each keeps the best chain
    ending on it. A digit may follow another where the font would put it,
    or, once per chain, ``gap`` digit-widths further on: the timer's colon.
    """
    candidates = []
    for i, scores in enumerate(line):
        peaks = (
            (scores >= min_match)
            & (scores >= np.roll(scores, 1))
            & (scores >= np.roll(scores, -1))
        )
        candidates += [
            (int(x), i, float(scores[x])) for x in np.flatnonzero(peaks)
        ]
    if not candidates:
        return None
    candidates.sort()
    zero_width = temps["0"].advance
    # Per candidate: (total, text, scores, pen position of its digit).
    chains = []
    for x, i, score in candidates:
        c = chars[i]
        pen = x - temps[c].left
        gain = (score - min_match) * temps[c].advance
        best = (gain, c, [score], pen)
        for (px, pi, _), (total, text, scores, ppen) in zip(
            candidates, chains, strict=False
        ):
            if px >= x or len(text.replace(":", "")) >= max_len:
                continue
            prev = temps[chars[pi]]
            off = pen - (ppen + prev.advance)
            slack = SPACING_TOL * prev.advance + UPSCALE
            if abs(off) <= slack:
                joined = text + c
            elif (
                gap and ":" not in text and 0 < off - slack <= gap * zero_width
            ):
                joined = text + ":" + c
            else:
                continue
            if total + gain > best[0]:
                best = (total + gain, joined, [*scores, score], pen)
        chains.append(best)
    total, text, scores, _ = max(chains, key=lambda chain: chain[0])
    return Reading(text, float(np.mean(scores)), float(total))


def _best_over_heights(image, heights, **kw) -> Reading | None:
    """The best reading over the digit sizes, compared per unit height."""
    digits, _, _ = _glyphs()
    best = None
    for h in heights:
        reading = _decode(image, digits[h], **kw)
        if reading and (best is None or reading.total / float(h) > best[0]):
            best = (reading.total / float(h), reading)
    return best and best[1]


def read_number(crop: np.ndarray) -> int | None:
    """The tower HP written in a crop, or None if there isn't one."""
    _, _, meta = _glyphs()
    reading = _best_over_heights(
        text_map(crop),
        meta["hp_heights"],
        max_len=5,
        min_match=MIN_MATCH,
        gap=0.0,
    )
    if reading is None or reading.score < MIN_HP_SCORE:
        return None
    if len(reading.text) == 1 and reading.score < MIN_LONE_DIGIT_SCORE:
        return None
    return int(reading.text)


def read_overtime(crop: np.ndarray) -> bool:
    """Whether the timer's label says "Overtime:" rather than "Time
    left:"."""
    _, labels, _ = _glyphs()
    image = text_map(crop)
    best = {}
    for over, templates in labels.items():
        scores = [_match(image, fill, mask) for fill, mask in templates]
        best[over] = max(
            (s.max() for s in scores if s is not None), default=-1
        )
    return best[True] > best[False]


def read_timer(crop: np.ndarray) -> tuple[int, bool] | None:
    """(seconds left, overtime) from the timer's crop, or None."""
    _, _, meta = _glyphs()
    # The time is on the lower line, under the label.
    split = crop.shape[0] * 2 // 5
    image = text_map(crop[split:])
    digits, _, _ = _glyphs()
    best = None
    for h in meta["timer_heights"]:
        reading = _decode(
            image, digits[h], max_len=3, min_match=MIN_TIMER_MATCH, gap=0.8
        )
        if reading is None:
            continue
        time = _TIME.fullmatch(reading.text)
        if not time or int(time[2]) > 59:
            continue
        if best is None or reading.total / float(h) > best[0]:
            best = (reading.total / float(h), int(time[1]) * 60 + int(time[2]))
    if best is None:
        return None
    return best[1], read_overtime(crop[: split + 2])
