"""Measure the OneJev screen detector on labelled screenshots.

Put full screenshots in folders named after the expected screen:

    <dir>/in_game/*.png
    <dir>/lobby/*.png
    <dir>/end_of_game/*.png
    <dir>/bypass_end_of_game/*.png
    <dir>/unknown/*.png

then, with the OneJev server running (see docs/bot-installation.md), run:

    uv run python scripts/eval_screen_detector.py <dir>
"""

import argparse
import time
from collections import Counter
from pathlib import Path

from PIL import Image

from clashroyalebuildabot.constants import (
    SCREENSHOT_HEIGHT,
    SCREENSHOT_WIDTH,
)
from clashroyalebuildabot.detectors.screen_detector import (
    SCREEN_QUESTION,
    OneJevClient,
    ScreenDetector,
    most_likely,
)

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def load_samples(root: Path):
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() in IMAGE_SUFFIXES:
                yield folder.name, path


def main():
    parser = argparse.ArgumentParser(
        description="Measure the OneJev screen detector."
    )
    parser.add_argument("dir", type=Path)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--min-confidence", type=float, default=0.5)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    client = OneJevClient(args.base_url, timeout=args.timeout)
    client.check()
    detector = ScreenDetector(client, min_confidence=args.min_confidence)

    samples = list(load_samples(args.dir))
    if not samples:
        raise SystemExit(f"No labelled screenshots found in {args.dir}")

    correct = 0
    mistakes = Counter()
    latencies = []
    print(f"{'file':40} {'expected':20} {'got':20} {'p':>5} {'ms':>6}")
    for expected, path in samples:
        # Match what the bot sees: frames are downscaled before detection.
        image = Image.open(path).convert("RGB")
        image = image.resize((SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT))

        start = time.perf_counter()
        answers = client.ask(image)
        latencies.append((time.perf_counter() - start) * 1000)
        _, p = most_likely(answers[SCREEN_QUESTION])
        got = detector.classify(image).name

        correct += got == expected
        if got != expected:
            mistakes[(expected, got)] += 1
        print(
            f"{path.parent.name + '/' + path.name:40.40} {expected:20} "
            f"{got:20} {p:5.2f} {latencies[-1]:6.0f}"
        )

    n = len(samples)
    print(f"\naccuracy: {correct}/{n}")
    for (expected, got), count in mistakes.most_common():
        print(f"  {expected} -> {got}: {count}")
    # The first call can include warm-up, so report it separately.
    warm = sorted(latencies[1:]) or latencies
    print(
        f"latency: first {latencies[0]:.0f} ms, "
        f"median {warm[len(warm) // 2]:.0f} ms, max {max(warm):.0f} ms"
    )


if __name__ == "__main__":
    main()
