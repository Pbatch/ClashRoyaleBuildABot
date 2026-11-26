from clashroyalebuildabot.detectors.unit_tracker import (
    SideTracker,
    UnitTracker,
)
from clashroyalebuildabot.game.units import Position, UnitDetection, Units


def det(unit, x, y, conf=0.5):
    return UnitDetection(unit, Position(conf, x, y))


def names_at(detections):
    return sorted(
        (d.unit.name, d.position.tile_x, d.position.tile_y) for d in detections
    )


def test_unsure_detection_is_reported_once_seen_twice():
    tracker = SideTracker()
    assert tracker.update([det(Units.KNIGHT, 5, 10)], now=0.0) == []
    assert names_at(tracker.update([det(Units.KNIGHT, 5, 10)], now=0.2)) == [
        ("knight", 5, 10)
    ]


def test_sure_detection_is_reported_at_once():
    tracker = SideTracker()
    out = tracker.update([det(Units.KNIGHT, 5, 10, conf=0.9)], now=0.0)
    assert names_at(out) == [("knight", 5, 10)]


def test_one_off_false_positive_is_never_reported():
    tracker = SideTracker()
    tracker.update([det(Units.GOBLIN, 3, 3)], now=0.0)
    assert tracker.update([], now=0.2) == []
    assert tracker.update([], now=1.0) == []
    assert tracker.tracks == []


def test_unit_survives_a_missed_frame_then_is_dropped():
    tracker = SideTracker()
    tracker.update([det(Units.KNIGHT, 5, 10, conf=0.9)], now=0.0)
    assert len(tracker.update([], now=0.3)) == 1  # missed: still there
    assert tracker.update([], now=1.0) == []  # gone for good


def test_moving_unit_keeps_its_track_and_is_carried_on():
    tracker = SideTracker()
    for i in range(5):
        tracker.update(
            [det(Units.HOG_RIDER, 8, 20 - i, conf=0.9)], now=i * 0.5
        )
    assert len(tracker.tracks) == 1
    assert tracker.tracks[0].vy < -1  # walking down, about 2 tiles/s
    # Missed for a frame: it's expected further on, not where it was seen.
    (out,) = tracker.update([], now=2.5)
    assert out.position.tile_y < 16


def test_wrong_name_for_a_frame_keeps_the_unit_and_its_name():
    tracker = SideTracker()
    for i in range(4):
        tracker.update([det(Units.MUSKETEER, 4, 8, conf=0.8)], now=i * 0.2)
    (out,) = tracker.update([det(Units.ARCHER, 4, 8, conf=0.5)], now=1.0)
    assert out.unit == Units.MUSKETEER
    assert len(tracker.tracks) == 1


def test_swarm_members_stay_apart():
    tracker = SideTracker()
    swarm = [det(Units.SKELETON, x, 12) for x in (4, 5, 6)]
    tracker.update(swarm, now=0.0)
    out = tracker.update(swarm, now=0.2)
    assert names_at(out) == [
        ("skeleton", 4, 12),
        ("skeleton", 5, 12),
        ("skeleton", 6, 12),
    ]
    assert len({t.id for t in tracker.tracks}) == 3


def test_far_detection_is_a_new_unit():
    tracker = SideTracker()
    tracker.update([det(Units.KNIGHT, 2, 5, conf=0.9)], now=0.0)
    tracker.update([det(Units.KNIGHT, 14, 25, conf=0.9)], now=0.2)
    assert len(tracker.tracks) == 2


def test_building_does_not_drift():
    tracker = SideTracker()
    tracker.update([det(Units.CANNON, 8, 12, conf=0.9)], now=0.0)
    tracker.update([det(Units.CANNON, 9, 12, conf=0.9)], now=0.5)
    (out,) = tracker.update([], now=0.9)
    assert out.position.tile_x in (8, 9)
    assert tracker.tracks[0].vx == 0


def test_sides_are_tracked_apart_and_reset():
    tracker = UnitTracker()
    allies, enemies = tracker.update(
        [det(Units.KNIGHT, 5, 5, conf=0.9)],
        [det(Units.KNIGHT, 5, 5, conf=0.9)],
        now=0.0,
    )
    assert len(allies) == len(enemies) == 1
    tracker.reset()
    assert tracker.allies.tracks == tracker.enemies.tracks == []
