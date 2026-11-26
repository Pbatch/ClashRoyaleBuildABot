import os
from collections.abc import Sequence

import numpy as np
from scipy.ndimage import maximum_filter

from clashroyalebuildabot.constants.paths import MODELS_DIR
from clashroyalebuildabot.constants.screenshot import (
    SCREENSHOT_HEIGHT,
    SCREENSHOT_WIDTH,
)
from clashroyalebuildabot.detectors import onnx_model
from clashroyalebuildabot.game.cards import Card
from clashroyalebuildabot.game.units import Position, UnitDetection, Units

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
    one of ours is there, not which.

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

    def name_allies(self, probs: np.ndarray) -> np.ndarray:
        """The model's probabilities with every ally named from our deck.

        On each tile, the strongest ally channel, whatever unit it's for,
        is the chance that one of ours stands there. That chance goes to
        the deck unit the model rates highest on the tile, if it's more
        than that unit's own, and the other units' ally channels are
        cleared. So a unit of ours the model mistakes for one we don't
        have is still found, under the right name. Each deck unit keeps
        its own channel, so two different units of ours on neighbouring
        tiles stay apart. With no deck units the model knows, nothing
        changes."""
        if not self.deck_units.size:
            return probs
        ally = probs[0::2]  # [units, ROWS, COLS]
        deck = ally[self.deck_units]
        best = np.argmax(deck, axis=0)  # index into deck_units, per tile
        named = np.zeros_like(ally)
        named[self.deck_units] = deck
        rows, cols = np.indices(best.shape)
        named[self.deck_units[best], rows, cols] = np.maximum(
            deck[best, rows, cols], ally.max(axis=0)
        )
        out = probs.copy()
        out[0::2] = named
        return out

    def decode(
        self, probs: np.ndarray
    ) -> tuple[list[UnitDetection], list[UnitDetection]]:
        """Detections from the model's [C, ROWS, COLS] probabilities:
        (allies, enemies) lists of UnitDetection."""
        probs = self.name_allies(probs)
        is_peak = probs >= self._local_max(probs)
        keep = (is_peak & (probs >= self.PEAK_CONF)) | (probs >= self.MIN_CONF)
        allies: list[UnitDetection] = []
        enemies: list[UnitDetection] = []
        for channel, row, col in zip(*np.nonzero(keep), strict=True):
            position = Position(
                float(probs[channel, row, col]),
                int(col),
                int(self.ROWS - 1 - row),  # the bot counts up from the bottom
            )
            detection = UnitDetection(self.units[channel // 2], position)
            (enemies if channel % 2 else allies).append(detection)
        return allies, enemies

    def run(
        self, image: np.ndarray
    ) -> tuple[list[UnitDetection], list[UnitDetection]]:
        if image.shape[:2] != (SCREENSHOT_HEIGHT, SCREENSHOT_WIDTH):
            raise ValueError(
                f"Expected a {SCREENSHOT_WIDTH}x{SCREENSHOT_HEIGHT} "
                f"screenshot, got {image.shape[1]}x{image.shape[0]}"
            )
        top, bottom = self.view_rows()
        view = np.ascontiguousarray(image[None, top:bottom])
        probs = self.model(view)[0]
        return self.decode(probs)
