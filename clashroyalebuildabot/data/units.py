from dataclasses import dataclass


@dataclass(frozen=True)
class Units:
    ARCHER: str = "archer"
    BOMBER: str = "bomber"
    BRAWLER: str = "brawler"
    GIANT: str = "giant"
    GOBLIN: str = "goblin"
    GOBLIN_CAGE: str = "goblin_cage"
    GOBLIN_HUT: str = "goblin_hut"
    HUNGRY_DRAGON: str = "hungry_dragon"
    HUNTER: str = "hunter"
    KNIGHT: str = "knight"
    MINION: str = "minion"
    MINIPEKKA: str = "minipekka"
    MUSKETEER: str = "musketeer"
    PRINCE: str = "prince"
    SKELETON: str = "skeleton"
    SPEAR_GOBLIN: str = "spear_goblin"
    TOMBSTONE: str = "tombstone"
    VALKYRIE: str = "valkyrie"
    WALL_BREAKER: str = "wall_breaker"
