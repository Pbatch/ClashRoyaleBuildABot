import os
from collections.abc import Sequence

import numpy as np
from scipy.ndimage import maximum_filter

from clashroyalebuildabot.constants.device_screen import (
    N_HEIGHT_TILES,
    N_WIDE_TILES,
    TOWER_TILES,
)
from clashroyalebuildabot.constants.paths import MODELS_DIR
from clashroyalebuildabot.constants.screenshot import (
    SCREENSHOT_HEIGHT,
    SCREENSHOT_WIDTH,
)
from clashroyalebuildabot.detectors import onnx_model
from clashroyalebuildabot.detectors.opponent_deck import OpponentDeck
from clashroyalebuildabot.detectors.unit_tracker import ScoredDetection
from clashroyalebuildabot.game.cards import Card
from clashroyalebuildabot.game.towers import Towers
from clashroyalebuildabot.game.units import (
    Position,
    Transport,
    Unit,
    UnitCategory,
    Units,
)

MODEL_PATH = os.path.join(MODELS_DIR, "units_tiles.onnx")

# The units the model knows, in the order of its channels: unit i is
# channels 2 * i (ours) and 2 * i + 1 (the enemy's). Only ever append, so
# a model trained on a shorter list still reads as the units it knows.
DETECTOR_UNITS = [
    Units.ARCHER,
    Units.ARCHER_QUEEN,
    Units.BALLOON,
    Units.BANDIT,
    Units.BARBARIAN,
    Units.BARBARIAN_HUT,
    Units.BAT,
    Units.BATTLE_HEALER,
    Units.BATTLE_RAM,
    Units.BOMB_TOWER,
    Units.BOMBER,
    Units.BOWLER,
    Units.BRAWLER,
    Units.CANNON,
    Units.CANNON_CART,
    Units.DARK_PRINCE,
    Units.DART_GOBLIN,
    Units.ELECTRO_DRAGON,
    Units.ELECTRO_GIANT,
    Units.ELECTRO_SPIRIT,
    Units.ELECTRO_WIZARD,
    Units.ELITE_BARBARIAN,
    Units.ELIXIR_COLLECTOR,
    Units.ELIXIR_GOLEM_LARGE,
    Units.ELIXIR_GOLEM_MEDIUM,
    Units.ELIXIR_GOLEM_SMALL,
    Units.EXECUTIONER,
    Units.FIRE_SPIRIT,
    Units.FIRECRACKER,
    Units.FISHERMAN,
    Units.FLYING_MACHINE,
    Units.FURNACE,
    Units.GIANT,
    Units.GIANT_SKELETON,
    Units.GIANT_SNOWBALL,
    Units.GOBLIN,
    Units.GOBLIN_CAGE,
    Units.GOBLIN_DRILL,
    Units.GOBLIN_HUT,
    Units.GOLDEN_KNIGHT,
    Units.GOLEM,
    Units.GOLEMITE,
    Units.GUARD,
    Units.HEAL_SPIRIT,
    Units.HOG,
    Units.HOG_RIDER,
    Units.BABY_DRAGON,
    Units.HUNTER,
    Units.ICE_GOLEM,
    Units.ICE_SPIRIT,
    Units.ICE_WIZARD,
    Units.INFERNO_DRAGON,
    Units.INFERNO_TOWER,
    Units.KNIGHT,
    Units.LAVA_HOUND,
    Units.LAVA_PUP,
    Units.LITTLE_PRINCE,
    Units.LUMBERJACK,
    Units.MAGIC_ARCHER,
    Units.MEGA_KNIGHT,
    Units.MEGA_MINION,
    Units.MIGHTY_MINER,
    Units.MINER,
    Units.MINION,
    Units.MINIPEKKA,
    Units.MONK,
    Units.MORTAR,
    Units.MOTHER_WITCH,
    Units.MUSKETEER,
    Units.NIGHT_WITCH,
    Units.PEKKA,
    Units.PHOENIX_EGG,
    Units.PHOENIX_LARGE,
    Units.PHOENIX_SMALL,
    Units.PRINCE,
    Units.PRINCESS,
    Units.RAM_RIDER,
    Units.RASCAL_BOY,
    Units.RASCAL_GIRL,
    Units.ROYAL_GHOST,
    Units.ROYAL_GIANT,
    Units.ROYAL_GUARDIAN,
    Units.ROYAL_HOG,
    Units.ROYAL_RECRUIT,
    Units.SKELETON,
    Units.SKELETON_DRAGON,
    Units.SKELETON_KING,
    Units.SPARKY,
    Units.SPEAR_GOBLIN,
    Units.TESLA,
    Units.TOMBSTONE,
    Units.VALKYRIE,
    Units.WALL_BREAKER,
    Units.WITCH,
    Units.WIZARD,
    Units.X_BOW,
    Units.ZAPPY,
    # Added 2026-11-25.
    Units.BERSERKER,
    Units.BOSS_BANDIT,
    Units.GOBLIN_DEMOLISHER,
    Units.GOBLIN_GIANT,
    Units.GOBLIN_MACHINE,
    Units.GOBLINSTEIN,
    Units.GOBLINSTEIN_DOCTOR,
    Units.RUNE_GIANT,
    Units.SKELETON_BARREL,
    Units.SPIRIT_EMPRESS,
    Units.SPIRIT_EMPRESS_MOUNTED,
    Units.SUSPICIOUS_BUSH,
    Units.BOMB,
]

# Ground units that can still end up on a tower's tiles: a balloon's bomb
# falls where it dies, and so does a phoenix's egg.
CAN_LAND_ON_TOWERS = frozenset({Units.BOMB.name, Units.PHOENIX_EGG.name})


def blocked_by_towers(unit: Unit) -> bool:
    """Whether a standing tower keeps this unit off its tiles: ground
    troops walk around it and buildings can't be placed on it. Flyers and
    projectiles pass over."""
    if unit.name in CAN_LAND_ON_TOWERS:
        return False
    return (
        unit.transport == Transport.GROUND
        or unit.category == UnitCategory.BUILDING
    )


# The river's rows, and the tiles of the two bridges across it (the game's
# bridges span x 2.5-4.5 and 13.5-15.5, so a unit on one stands on these).
RIVER_ROWS = (N_HEIGHT_TILES, N_HEIGHT_TILES + 1)
BRIDGE_COLS = frozenset({2, 3, 4, 13, 14, 15})
# The units that jump the river (JumpEnabled in the game's logic files),
# seen over the water mid-jump. "hog" is the Mother Witch's cursed hog.
JUMPS_RIVER = frozenset(
    unit.name
    for unit in (
        Units.DARK_PRINCE,
        Units.HOG,
        Units.HOG_RIDER,
        Units.PRINCE,
        Units.RAM_RIDER,
        Units.ROYAL_HOG,
    )
)


def blocked_by_river(unit: Unit) -> bool:
    """Whether the river keeps this unit off its water: what a tower keeps
    off its tiles (see blocked_by_towers), but the units that jump it."""
    return blocked_by_towers(unit) and unit.name not in JUMPS_RIVER


class UnitDetector:
    """Finds the units on the battlefield, as the tiles they stand on.

    One model reads the arena as its 18 x 32 tile grid and gives, for each
    tile, the chance that a unit of each kind and side stands there: a
    [2 * len(DETECTOR_UNITS), 32, 18] map, rows from the top. A unit is
    reported on a tile that is the highest of its 3 x 3 neighbours on its
    channel (above PEAK_CONF), or that is confident on its own (above
    MIN_CONF): the second keeps every member of a swarm on neighbouring
    tiles, while a half-confident tile beside a unit near a tile edge is
    dropped.

    Our units can only come from our deck, so an ally is named from the
    deck's units alone (see name_allies): the model only has to see that
    one of ours is there, not which. The opponent's units are named the
    same way from the cards of theirs seen so far (see name_enemies and
    OpponentDeck), favoured until their deck is complete, then only those.

    Nothing that walks or is built can stand on a standing tower, so the
    tiles under each tower (TOWER_TILES) are cleared on those units'
    channels until it falls (see clear_towers): an X-Bow the model sees in
    a tower's sprite isn't reported. The river's water, off the bridges,
    is cleared the same way, but for the units that jump it (see
    blocked_by_river).

    There's no box: a detection is a unit on a tile.
    """

    PEAK_CONF = 0.4
    MIN_CONF = 0.7
    UNIT_Y_START = 0.05
    UNIT_Y_END = 0.80
    ROWS, COLS = 32, 18

    def __init__(
        self, cards: Sequence[Card], model_path: str = MODEL_PATH
    ) -> None:
        self.model = onnx_model.load(model_path)
        top, bottom = self.view_rows()
        if self.model.input_size != (bottom - top, SCREENSHOT_WIDTH):
            raise ValueError(
                f"{model_path} takes {self.model.input_size} images, not "
                f"the {(bottom - top, SCREENSHOT_WIDTH)} unit view"
            )
        # The units this model knows: the first n of DETECTOR_UNITS, as
        # one trained before units were appended knows fewer.
        channels = self.model.output_shape[1]
        if (
            not isinstance(channels, int)
            or channels % 2
            or not (0 < channels <= 2 * len(DETECTOR_UNITS))
        ):
            raise ValueError(
                f"{model_path} gives {channels} channels, not an ally and "
                f"an enemy channel for up to {len(DETECTOR_UNITS)} units"
            )
        self.units = DETECTOR_UNITS[: channels // 2]
        # The indices of the units our cards can put on the battlefield,
        # spawned units included (a witch's skeletons).
        deck = {unit.name for card in cards for unit in card.units}
        self.deck_units = np.array(
            [i for i, unit in enumerate(self.units) if unit.name in deck],
            dtype=np.int64,
        )
        # Per tower, the [C, ROWS, COLS] cells a standing tower clears:
        # its tiles, on both sides' channels of every unit it blocks.
        blocked = np.repeat(
            [blocked_by_towers(unit) for unit in self.units], 2
        )
        self.tower_masks: dict[str, np.ndarray] = {}
        for name, (x0, y0, x1, y1) in TOWER_TILES.items():
            mask = np.zeros((channels, self.ROWS, self.COLS), dtype=bool)
            rows = slice(self.ROWS - 1 - y1, self.ROWS - y0)  # model rows
            mask[blocked, rows, x0 : x1 + 1] = True
            self.tower_masks[name] = mask
        # The water: the river's rows off the bridges, on the channels of
        # every unit that can't cross it but by a bridge.
        swims = np.repeat([blocked_by_river(unit) for unit in self.units], 2)
        water = np.zeros((self.ROWS, self.COLS), dtype=bool)
        for y in RIVER_ROWS:
            water[self.ROWS - 1 - y] = [
                x not in BRIDGE_COLS for x in range(N_WIDE_TILES)
            ]
        self.river_mask = swims[:, None, None] & water

    @classmethod
    def view_rows(cls) -> tuple[int, int]:
        """The screenshot rows the model reads: the unit view."""
        return (
            round(cls.UNIT_Y_START * SCREENSHOT_HEIGHT),
            round(cls.UNIT_Y_END * SCREENSHOT_HEIGHT),
        )

    @staticmethod
    def _local_max(probs: np.ndarray) -> np.ndarray:
        """The highest value in each tile's 3 x 3 neighbourhood, per channel."""
        return maximum_filter(probs, size=(1, 3, 3), mode="constant", cval=-1)

    @staticmethod
    def _name_from(
        side: np.ndarray, favoured: np.ndarray, others: float
    ) -> np.ndarray:
        """One side's [units, ROWS, COLS] probabilities, renamed in favour
        of the units at indices favoured.

        On each tile, the strongest channel, whatever unit it's for, is the
        chance that a unit of this side stands there. Which unit it is goes
        by the model's ratings, with every unit that isn't favoured rated
        at others times its own (0: never named). The winner gets that
        chance, if it's more than its own, and the other units' channels
        that aren't favoured are cleared there. So a unit the model mistakes
        for one this side doesn't have is still found, under the right
        name. Each favoured unit keeps its own channel, so two different
        units on neighbouring tiles stay apart."""
        weight = np.full(len(side), others, dtype=side.dtype)
        weight[favoured] = 1
        if others > 0:
            best = np.argmax(side * weight[:, None, None], axis=0)
        else:  # only the favoured can win, even where they're all 0
            best = favoured[np.argmax(side[favoured], axis=0)]
        named = np.zeros_like(side)
        named[favoured] = side[favoured]
        rows, cols = np.indices(best.shape)
        named[best, rows, cols] = np.maximum(
            side[best, rows, cols], side.max(axis=0)
        )
        return named

    def name_allies(self, probs: np.ndarray) -> np.ndarray:
        """The model's probabilities with every ally named from our deck
        (see _name_from). With no deck units the model knows, nothing
        changes."""
        if not self.deck_units.size:
            return probs
        out = probs.copy()
        out[0::2] = self._name_from(probs[0::2], self.deck_units, 0.0)
        return out

    def name_enemies(
        self, probs: np.ndarray, opponent: OpponentDeck | None
    ) -> np.ndarray:
        """The model's probabilities with enemies named in favour of the
        opponent's known cards (see _name_from and OpponentDeck.favour):
        a unit from a card of theirs not seen yet has to rate twice as
        high as every unit their known cards make. Once their deck is
        complete, enemies are named only from it. The tracker names them
        again from their scores over every frame (UnitTracker)."""
        if opponent is None:
            return probs
        possible, others = opponent.favour()
        known = np.array(
            [i for i, unit in enumerate(self.units) if unit in possible],
            dtype=np.int64,
        )
        if not known.size:
            return probs
        out = probs.copy()
        out[1::2] = self._name_from(probs[1::2], known, others)
        return out

    def clear_blocked(
        self, probs: np.ndarray, towers: Towers | None
    ) -> np.ndarray:
        """The model's probabilities with the units that can't be where
        they're seen cleared there: on a standing tower's tiles (see
        blocked_by_towers), or in the river off the bridges (see
        blocked_by_river). A tower not read yet counts as standing; once
        destroyed, units can walk over its ruins. With no towers given,
        all six stand."""
        standing = [
            name
            for name, tower in (towers or Towers()).items()
            if tower.hp != 0
        ]
        mask = np.logical_or.reduce(
            [self.river_mask, *(self.tower_masks[n] for n in standing)]
        )
        return np.where(mask, 0, probs).astype(probs.dtype, copy=False)

    def decode(
        self,
        probs: np.ndarray,
        opponent: OpponentDeck | None = None,
        towers: Towers | None = None,
    ) -> tuple[list[ScoredDetection], list[ScoredDetection]]:
        """Detections from the model's [C, ROWS, COLS] probabilities:
        (allies, enemies) lists of ScoredDetection, with nothing that walks
        or is built on a standing tower or in the river (see
        clear_blocked), enemies named
        in favour of the opponent's cards seen so far, if given, each with
        the model's scores for every unit on both sides on its tile, before
        naming."""
        # Cleared before naming, so an X-Bow on a tower isn't renamed as
        # one of the deck's units either.
        probs = raw = self.clear_blocked(probs, towers)
        probs = self.name_enemies(self.name_allies(probs), opponent)
        is_peak = probs >= self._local_max(probs)
        keep = (is_peak & (probs >= self.PEAK_CONF)) | (probs >= self.MIN_CONF)
        allies: list[ScoredDetection] = []
        enemies: list[ScoredDetection] = []
        for channel, row, col in zip(*np.nonzero(keep), strict=True):
            position = Position(
                float(probs[channel, row, col]),
                int(col),
                int(self.ROWS - 1 - row),  # the bot counts up from the bottom
            )
            detection = ScoredDetection(
                self.units[channel // 2],
                position,
                scores=np.stack((raw[0::2, row, col], raw[1::2, row, col])),
                units=self.units,
            )
            (enemies if channel % 2 else allies).append(detection)
        return allies, enemies

    def run(
        self,
        image: np.ndarray,
        opponent: OpponentDeck | None = None,
        towers: Towers | None = None,
    ) -> tuple[list[ScoredDetection], list[ScoredDetection]]:
        if image.shape[:2] != (SCREENSHOT_HEIGHT, SCREENSHOT_WIDTH):
            raise ValueError(
                f"Expected a {SCREENSHOT_WIDTH}x{SCREENSHOT_HEIGHT} "
                f"screenshot, got {image.shape[1]}x{image.shape[0]}"
            )
        top, bottom = self.view_rows()
        view = np.ascontiguousarray(image[None, top:bottom])
        probs = self.model(view)[0]
        return self.decode(probs, opponent, towers)
