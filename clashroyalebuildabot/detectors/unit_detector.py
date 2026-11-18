import os

import numpy as np

from clashroyalebuildabot.constants.device_screen import (
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    TILE_HEIGHT,
    TILE_INIT_X,
    TILE_INIT_Y,
    TILE_WIDTH,
)
from clashroyalebuildabot.constants.paths import MODELS_DIR
from clashroyalebuildabot.constants.screenshot import (
    SCREENSHOT_HEIGHT,
    SCREENSHOT_WIDTH,
)
from clashroyalebuildabot.detectors.onnx_detector import OnnxDetector
from clashroyalebuildabot.detectors.side_detector import SideDetector
from clashroyalebuildabot.game.units import Position, UnitDetection, Units

# The units the model detects, in the order of its class indices.
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
    Units.FIRE_CRACKER,
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
]


class UnitDetector(OnnxDetector):
    MIN_CONF = 0.3
    UNIT_Y_START = 0.05
    UNIT_Y_END = 0.80

    def __init__(self, model_path, cards):
        super().__init__(model_path)
        self.cards = cards

        self.side_detector = SideDetector(
            os.path.join(MODELS_DIR, "side.onnx")
        )
        self.possible_ally_names = self._get_possible_ally_names()

    @staticmethod
    def _get_tile_xy(bbox):
        x = (bbox[0] + bbox[2]) * DISPLAY_WIDTH / (2 * SCREENSHOT_WIDTH)
        y = bbox[3] * DISPLAY_HEIGHT / SCREENSHOT_HEIGHT
        tile_x = round(((x - TILE_INIT_X) / TILE_WIDTH) - 0.5)
        tile_y = round(
            ((DISPLAY_HEIGHT - TILE_INIT_Y - y) / TILE_HEIGHT) - 0.5
        )
        return tile_x, tile_y

    def _get_possible_ally_names(self):
        possible_ally_names = set()
        for card in self.cards:
            for unit in card.units:
                possible_ally_names.add(unit.name)
        return possible_ally_names

    def _calculate_side(self, image, bbox, name):
        if name not in self.possible_ally_names:
            side = "enemy"
        else:
            crop = image.crop(bbox)
            side = self.side_detector.run(crop)
        return side

    def _preprocess(self, image):
        image = image.crop(
            (
                0,
                self.UNIT_Y_START * image.height,
                image.width,
                self.UNIT_Y_END * image.height,
            )
        )
        image, padding = self.resize_and_pad(image)
        image = np.expand_dims(image, axis=0)
        return image, padding

    def _post_process(self, pred, height, image):
        pred[:, [1, 3]] *= self.UNIT_Y_END - self.UNIT_Y_START
        pred[:, [1, 3]] += self.UNIT_Y_START * height

        allies = []
        enemies = []
        for p in pred:
            left, top, right, bottom, conf, cls = p
            bbox = (round(left), round(top), round(right), round(bottom))
            tile_x, tile_y = self._get_tile_xy(bbox)
            position = Position(bbox, conf, tile_x, tile_y)
            unit = DETECTOR_UNITS[int(cls)]
            unit_detection = UnitDetection(unit, position)

            side = self._calculate_side(image, bbox, unit.name)
            if side == "ally":
                allies.append(unit_detection)
            else:
                enemies.append(unit_detection)

        return allies, enemies

    def run(self, image):
        height, width = image.height, image.width
        np_image, padding = self._preprocess(image)
        pred = self._infer(np_image)[0]
        pred = pred[pred[:, 4] > self.MIN_CONF]
        pred = self.fix_bboxes(pred, width, height, padding)
        allies, enemies = self._post_process(pred, height, image)
        return allies, enemies
