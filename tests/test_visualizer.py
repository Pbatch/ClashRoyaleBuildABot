import os

import pytest
from PIL import Image

from clashroyalebuildabot.visualizer import Visualizer


@pytest.fixture
def dirs(tmp_path):
    labels = tmp_path / "labels"
    screenshots = tmp_path / "screenshots"
    return labels, screenshots


def make_visualizer(dirs, save_labels=True, save_images=True):
    labels, screenshots = dirs
    return Visualizer(
        save_labels=save_labels,
        save_images=save_images,
        show_images=False,
        labels_dir=str(labels),
        screenshots_dir=str(screenshots),
    )


def saved(directory):
    return sorted(os.listdir(directory))


def test_creates_dirs_and_starts_at_one(dirs):
    visualizer = make_visualizer(dirs)
    assert dirs[0].is_dir() and dirs[1].is_dir()
    assert visualizer._next_index == 1


def test_continues_after_highest_existing_number(dirs):
    labels, screenshots = dirs
    labels.mkdir()
    screenshots.mkdir()
    # 3.png was deleted: counting files would reuse 3 and overwrite 4.txt.
    for name in ["1.txt", "2.txt", "4.txt"]:
        (labels / name).touch()
    (screenshots / "2.png").touch()
    (screenshots / "notes.md").touch()  # non-numbered files are ignored

    assert make_visualizer(dirs)._next_index == 5


def test_does_not_scan_dirs_per_frame(dirs, state_factory, monkeypatch):
    visualizer = make_visualizer(dirs)

    def fail(*args):
        raise AssertionError("os.listdir called during run()")

    monkeypatch.setattr(os, "listdir", fail)
    image = Image.new("RGB", (368, 652))
    for _ in range(3):
        visualizer.run(image.copy(), state_factory())


def test_label_and_screenshot_share_a_number(dirs, state_factory):
    visualizer = make_visualizer(dirs)
    image = Image.new("RGB", (368, 652))
    for _ in range(2):
        visualizer.run(image.copy(), state_factory())

    assert saved(dirs[0]) == ["1.txt", "2.txt"]
    assert saved(dirs[1]) == ["1.png", "2.png"]


def test_counter_does_not_advance_when_not_saving(dirs, state_factory):
    visualizer = make_visualizer(dirs, save_labels=False, save_images=False)
    visualizer.run(Image.new("RGB", (368, 652)), state_factory())
    assert visualizer._next_index == 1
