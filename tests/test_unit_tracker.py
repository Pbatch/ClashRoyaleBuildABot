import numpy as np

from clashroyalebuildabot.detectors.opponent_deck import OpponentDeck
from clashroyalebuildabot.detectors.unit_tracker import (
    ALLY,
    ENEMY,
    ScoredDetection,
    UnitTracker,
)
from clashroyalebuildabot.game.units import Position, Units

ALL = Units.all()


def det(unit, x, y, conf=0.5, side=ENEMY):
    """A detection on side, scoring conf for unit and nothing else."""
    scores = np.zeros((2, len(ALL)), np.float32)
    scores[side, ALL.index(unit)] = conf
    return ScoredDetection(
        unit, Position(conf, x, y), scores=scores, units=ALL
    )


def follow(tracker, detections, now):
    """The opponent's units tracker reports after detections of theirs."""
    _, enemies = tracker.update([], detections, now, OpponentDeck())
    return enemies


def names_at(detections):
    return sorted(
        (d.unit.name, d.position.tile_x, d.position.tile_y) for d in detections
    )


def test_unsure_detection_is_reported_once_seen_twice():
    tracker = UnitTracker(())
    assert follow(tracker, [det(Units.KNIGHT, 5, 10)], now=0.0) == []
    assert names_at(follow(tracker, [det(Units.KNIGHT, 5, 10)], now=0.2)) == [
        ("knight", 5, 10)
    ]


def test_sure_detection_is_reported_at_once():
    tracker = UnitTracker(())
    out = follow(tracker, [det(Units.KNIGHT, 5, 10, conf=0.9)], now=0.0)
    assert names_at(out) == [("knight", 5, 10)]


def test_one_off_false_positive_is_never_reported():
    tracker = UnitTracker(())
    follow(tracker, [det(Units.GOBLIN, 3, 3)], now=0.0)
    assert follow(tracker, [], now=0.2) == []
    assert follow(tracker, [], now=1.0) == []
    assert tracker.tracks == []


def test_unit_survives_a_missed_frame_then_is_dropped():
    tracker = UnitTracker(())
    follow(tracker, [det(Units.KNIGHT, 5, 10, conf=0.9)], now=0.0)
    assert len(follow(tracker, [], now=0.3)) == 1  # missed: still there
    assert follow(tracker, [], now=1.0) == []  # gone for good


def test_moving_unit_keeps_its_track_and_is_carried_on():
    tracker = UnitTracker(())
    for i in range(5):
        follow(
            tracker, [det(Units.HOG_RIDER, 8, 20 - i, conf=0.9)], now=i * 0.5
        )
    assert len(tracker.tracks) == 1
    assert tracker.tracks[0].vy < -1  # walking down, about 2 tiles/s
    # Missed for a frame: it's expected further on, not where it was seen.
    (out,) = follow(tracker, [], now=2.5)
    assert out.position.tile_y < 16


def test_wrong_name_for_a_frame_keeps_the_unit_and_its_name():
    tracker = UnitTracker(())
    for i in range(4):
        follow(tracker, [det(Units.MUSKETEER, 4, 8, conf=0.8)], now=i * 0.2)
    (out,) = follow(tracker, [det(Units.ARCHER, 4, 8, conf=0.5)], now=1.0)
    assert out.unit == Units.MUSKETEER
    assert len(tracker.tracks) == 1


def test_swarm_members_stay_apart():
    tracker = UnitTracker(())
    swarm = [det(Units.SKELETON, x, 12) for x in (4, 5, 6)]
    follow(tracker, swarm, now=0.0)
    out = follow(tracker, swarm, now=0.2)
    assert names_at(out) == [
        ("skeleton", 4, 12),
        ("skeleton", 5, 12),
        ("skeleton", 6, 12),
    ]
    assert len({t.id for t in tracker.tracks}) == 3


def test_far_detection_is_a_new_unit():
    tracker = UnitTracker(())
    follow(tracker, [det(Units.KNIGHT, 2, 5, conf=0.9)], now=0.0)
    follow(tracker, [det(Units.KNIGHT, 14, 25, conf=0.9)], now=0.2)
    assert len(tracker.tracks) == 2


def test_building_does_not_drift():
    tracker = UnitTracker(())
    follow(tracker, [det(Units.CANNON, 8, 12, conf=0.9)], now=0.0)
    follow(tracker, [det(Units.CANNON, 9, 12, conf=0.9)], now=0.5)
    (out,) = follow(tracker, [], now=0.9)
    assert out.position.tile_x in (8, 9)
    assert tracker.tracks[0].vx == 0


def test_sides_are_tracked_apart_and_reset():
    tracker = UnitTracker(())
    allies, enemies = tracker.update(
        [det(Units.KNIGHT, 5, 5, conf=0.9, side=ALLY)],
        [det(Units.KNIGHT, 5, 5, conf=0.9)],
        now=0.0,
        opponent=OpponentDeck(),
    )
    assert len(allies) == len(enemies) == 1
    tracker.reset()
    assert tracker.tracks == []


UNITS = (Units.ARCHER, Units.MUSKETEER, Units.WIZARD)


def scored(scores, x=4, y=8, side=ENEMY):
    """A detection on side scored scores, the other side scoring nothing."""
    both = np.zeros((2, len(UNITS)), np.float32)
    both[side] = scores
    unit = UNITS[int(np.argmax(both[side]))]
    return ScoredDetection(
        unit,
        Position(float(both[side].max()), x, y),
        scores=both,
        units=UNITS,
    )


def test_track_sums_every_frames_scores():
    tracker = UnitTracker(())
    for i in range(3):
        follow(tracker, [scored([0.6, 0.5, 0.0])], now=i * 0.1)
    (track,) = tracker.tracks
    np.testing.assert_allclose(track.total_scores[ENEMY], [1.8, 1.5, 0.0])
    assert track.units == UNITS


def test_best_unit_weighs_every_unit_over_every_frame():
    # Named an archer every frame by a hair, but a musketeer by far once.
    tracker = UnitTracker(())
    frames = [[0.55, 0.5, 0.0]] * 3 + [[0.1, 0.9, 0.0]]
    for i, scores in enumerate(frames):
        follow(tracker, [scored(scores)], now=i * 0.1)
    (track,) = tracker.tracks
    assert track.unit == Units.MUSKETEER
    assert track.best_unit(recent=False) == Units.MUSKETEER


def test_best_unit_favours_units_as_asked():
    tracker = UnitTracker(())
    follow(tracker, [scored([0.8, 0.5, 0.3])], now=0.0)
    (track,) = tracker.tracks
    assert track.best_unit() == Units.ARCHER
    favoured = {Units.MUSKETEER, Units.WIZARD}
    assert track.best_unit(ENEMY, favoured, 0.5) == Units.MUSKETEER
    assert track.best_unit(ENEMY, {Units.WIZARD}, 0.0) == Units.WIZARD


def test_unit_on_the_wrong_side_for_a_frame_stays_on_its_side():
    tracker = UnitTracker(())
    for i in range(4):
        tracker.update(
            [scored([0.9, 0, 0], side=ALLY)],
            [],
            now=i * 0.1,
            opponent=OpponentDeck(),
        )
    # Taken for theirs this frame, a little.
    flipped = scored([0.5, 0, 0], side=ENEMY)
    both = flipped.scores.copy()
    both[ALLY, 0] = 0.4
    flipped = ScoredDetection(
        flipped.unit, flipped.position, scores=both, units=UNITS
    )
    allies, enemies = tracker.update(
        [], [flipped], now=0.4, opponent=OpponentDeck()
    )
    assert len(tracker.tracks) == 1
    assert [d.unit for d in allies] == [Units.ARCHER]
    assert enemies == []


def test_side_is_what_most_frames_say():
    # Taken for ours as it appears, then seen as theirs from then on.
    tracker = UnitTracker(())
    tracker.update(
        [scored([0.6, 0, 0], side=ALLY)], [], now=0.0, opponent=OpponentDeck()
    )
    for i in range(1, 5):
        tracker.update(
            [], [scored([0.9, 0, 0])], now=i * 0.1, opponent=OpponentDeck()
        )
    allies, enemies = tracker.update(
        [], [scored([0.9, 0, 0])], now=0.5, opponent=OpponentDeck()
    )
    assert len(tracker.tracks) == 1
    assert allies == []
    assert [d.unit for d in enemies] == [Units.ARCHER]


def test_two_units_fighting_on_neighbouring_tiles_keep_their_sides():
    tracker = UnitTracker(())
    for i in range(4):
        tracker.update(
            [scored([0.9, 0, 0], x=5, y=10, side=ALLY)],
            [scored([0, 0.9, 0], x=5, y=11)],
            now=i * 0.1,
            opponent=OpponentDeck(),
        )
    allies, enemies = tracker.update(
        [scored([0.9, 0, 0], x=5, y=10, side=ALLY)],
        [scored([0, 0.9, 0], x=5, y=11)],
        now=0.4,
        opponent=OpponentDeck(),
    )
    assert [d.unit for d in allies] == [Units.ARCHER]
    assert [d.unit for d in enemies] == [Units.MUSKETEER]
    assert len(tracker.tracks) == 2


def test_allies_are_named_from_our_deck():
    # The model rates one of ours higher as a wizard, which we don't have.
    tracker = UnitTracker([Units.ARCHER, Units.MUSKETEER])
    for i in range(2):
        allies, _ = tracker.update(
            [scored([0.2, 0.4, 0.9], side=ALLY)],
            [],
            now=i * 0.1,
            opponent=OpponentDeck(),
        )
    assert [d.unit for d in allies] == [Units.MUSKETEER]


def test_enemies_are_named_in_favour_of_their_cards():
    opponent = OpponentDeck()
    opponent.saw(Units.MUSKETEER)
    tracker = UnitTracker(())
    for i in range(2):
        _, enemies = tracker.update(
            [], [scored([0.7, 0.4, 0.0])], now=i * 0.1, opponent=opponent
        )
    assert [d.unit for d in enemies] == [Units.MUSKETEER]
    # Sure it's an archer: a card they hadn't played yet.
    tracker.reset()
    for i in range(2):
        _, enemies = tracker.update(
            [], [scored([0.9, 0.3, 0.0])], now=i * 0.1, opponent=opponent
        )
    assert [d.unit for d in enemies] == [Units.ARCHER]


def test_unit_gone_too_long_is_not_matched_to_a_new_one():
    tracker = UnitTracker(())
    follow(tracker, [det(Units.KNIGHT, 5, 10, conf=0.9)], now=0.0)
    follow(tracker, [det(Units.KNIGHT, 5, 10, conf=0.9)], now=5.0)
    (track,) = tracker.tracks
    assert track.born == 5.0
