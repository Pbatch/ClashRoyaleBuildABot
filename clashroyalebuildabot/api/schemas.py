"""The JSON the API sends and accepts, and conversion from the bot's types.

Cards and units are named by their stable ``name`` (``"baby_dragon"``),
never by an index. Values the bot hasn't read yet (``UNKNOWN_HP`` and the
like, which are infinite internally and not valid JSON) are null.
"""

import math
from typing import Literal

from pydantic import BaseModel, Field

from clashroyalebuildabot.bot.bot import Observation
from clashroyalebuildabot.bot.plays import (
    HAND_SIZE,
    PlayResult,
    affordable_hand,
    hand_card,
    tiles_for,
)
from clashroyalebuildabot.constants.device_screen import (
    N_HEIGHT_TILES,
    N_WIDE_TILES,
    TOWER_TILES,
)
from clashroyalebuildabot.game import game_data
from clashroyalebuildabot.game.cards import Card, Cards
from clashroyalebuildabot.game.screens import ScreenName
from clashroyalebuildabot.game.state import State
from clashroyalebuildabot.game.towers import UNKNOWN_LEVEL, Tower
from clashroyalebuildabot.game.units import Unit, UnitDetection, Units

# The whole arena: our 15 rows, the 2 river rows, the enemy's 15.
GRID_WIDTH = N_WIDE_TILES
GRID_HEIGHT = 2 * N_HEIGHT_TILES + 2
RIVER_ROWS = [N_HEIGHT_TILES, N_HEIGHT_TILES + 1]


def _known(value: float) -> float | None:
    return None if math.isinf(value) else value


def _card_name(card: Card | None) -> str | None:
    return None if card is None else card.name


class TowerOut(BaseModel):
    destroyed: bool
    # Hit points, as written on the health bar: 0 once destroyed. A king
    # tower shows no health bar until it's hit: until then it's its full HP
    # for its level. Null when unknown: not read yet, or an untouched king
    # tower whose level isn't known.
    hp: float | None
    # From the princess towers' full HP at the start of the battle: a side's
    # three towers share a level. Null until then, or if the bot started
    # once they were hit.
    level: int | None

    @classmethod
    def of(cls, tower: Tower) -> "TowerOut":
        level = None if tower.level == UNKNOWN_LEVEL else tower.level
        return cls(destroyed=tower.hp == 0, hp=_known(tower.hp), level=level)


class TowersOut(BaseModel):
    left_enemy_princess: TowerOut
    right_enemy_princess: TowerOut
    left_ally_princess: TowerOut
    right_ally_princess: TowerOut
    enemy_king: TowerOut
    ally_king: TowerOut


class TimerOut(BaseModel):
    # Seconds left, of overtime when overtime is true. Null until read.
    time_left: float | None
    overtime: bool


class ElixirRateOut(BaseModel):
    seconds_per_elixir: float
    # 1, 2 or 3: single, double or triple elixir.
    multiplier: int


def elixir_rate(state: State) -> ElixirRateOut | None:
    seconds = game_data.seconds_per_elixir(state.timer)
    if seconds is None:
        return None
    normal = game_data.elixir()["phases"][0]["seconds_per_elixir"]
    return ElixirRateOut(
        seconds_per_elixir=seconds, multiplier=round(normal / seconds)
    )


class HandCardOut(BaseModel):
    # 0-3, left to right: what POST /api/play's hand_index refers to.
    hand_index: int
    # Null when the slot couldn't be read.
    card: str | None
    cost: int | None
    # Whether it can be played now: the game shows it in colour, not
    # greyed out, and the elixir read covers its cost.
    playable: bool


class DetectionOut(BaseModel):
    unit: str
    # Tile under the unit; see /api/meta for the grid.
    tile_x: int
    tile_y: int
    # The detector's confidence, 0-1. Detections are noisy: units flicker
    # in and out, and swarms may be miscounted.
    conf: float

    @classmethod
    def of(cls, detection: UnitDetection) -> "DetectionOut":
        position = detection.position
        return cls(
            unit=detection.unit.name,
            tile_x=position.tile_x,
            tile_y=position.tile_y,
            conf=position.conf,
        )


class PendingPlayOut(BaseModel):
    card: str
    hand_index: int


class BattleOut(BaseModel):
    elixir: int
    # How fast elixir comes in now, from the timer. Null until it's read.
    elixir_rate: ElixirRateOut | None
    timer: TimerOut
    towers: TowersOut
    next_card: str | None
    hand: list[HandCardOut]
    allies: list[DetectionOut]
    enemies: list[DetectionOut]

    @classmethod
    def of(cls, state: State) -> "BattleOut":
        playable = {i for i, _ in affordable_hand(state)}
        hand = []
        for i in range(HAND_SIZE):
            card = hand_card(state, i)
            hand.append(
                HandCardOut(
                    hand_index=i,
                    card=_card_name(card),
                    cost=None if card is None else card.cost,
                    playable=i in playable,
                )
            )
        return cls(
            elixir=state.elixir,
            elixir_rate=elixir_rate(state),
            timer=TimerOut(
                time_left=_known(state.timer.time_left),
                overtime=state.timer.overtime,
            ),
            towers=TowersOut(
                **{
                    name: TowerOut.of(tower)
                    for name, tower in state.towers.items()
                }
            ),
            next_card=_card_name(state.cards[0] if state.cards else None),
            hand=hand,
            allies=[DetectionOut.of(d) for d in state.allies],
            enemies=[DetectionOut.of(d) for d in state.enemies],
        )


# The screens a client sees. The bot tells two results screens apart, by
# which button leaves them, but to a client both are the end of a battle.
ScreenOut = Literal["in_game", "lobby", "end_of_game", "unknown"]

_SCREENS: dict[ScreenName, ScreenOut] = {
    ScreenName.IN_GAME: "in_game",
    ScreenName.LOBBY: "lobby",
    ScreenName.END_OF_GAME: "end_of_game",
    ScreenName.BYPASS_END_OF_GAME: "end_of_game",
    ScreenName.UNKNOWN: "unknown",
}


class StateOut(BaseModel):
    # Counts up for the life of the process. Pass it to POST /api/play so a
    # play decided on an old frame is refused.
    frame: int
    # Unix time it was read.
    time: float
    screen: ScreenOut
    # What's read from a battle. Null on any other screen, where there's
    # nothing to read.
    battle: BattleOut | None
    # A card the bot tapped that the screen doesn't show played yet. No
    # other card can be played until it does, or about a second passes.
    pending_play: PendingPlayOut | None

    @classmethod
    def of(cls, observation: Observation) -> "StateOut":
        state = observation.state
        in_battle = state.screen == ScreenName.IN_GAME
        pending = observation.pending
        return cls(
            frame=observation.frame,
            time=observation.time,
            screen=_SCREENS[state.screen],
            battle=BattleOut.of(state) if in_battle else None,
            pending_play=(
                PendingPlayOut(
                    card=pending.card.name, hand_index=pending.index
                )
                if pending is not None
                else None
            ),
        )


class LegalCardOut(BaseModel):
    hand_index: int
    card: str
    cost: int
    # Every [tile_x, tile_y] it can be played on now.
    tiles: list[tuple[int, int]]


class ActionsOut(BaseModel):
    # Null when the bot isn't running or hasn't read a frame.
    frame: int | None
    # Why nothing can be played right now, or null if a card in ``cards``
    # can be: one of not_running, builtin_policy, paused, not_in_battle,
    # play_pending, no_affordable_card.
    blocked_by: str | None
    # The playable cards, as in the state's hand, with where each can go.
    # Empty when blocked_by is anything but play_pending.
    cards: list[LegalCardOut]

    @staticmethod
    def legal_cards(state: State) -> list[LegalCardOut]:
        cards = []
        for i, card in affordable_hand(state):
            cards.append(
                LegalCardOut(
                    hand_index=i,
                    card=card.name,
                    cost=card.cost,
                    tiles=[(x, y) for x, y in tiles_for(card, state)],
                )
            )
        return cards


class PlayIn(BaseModel):
    hand_index: int = Field(ge=0, lt=HAND_SIZE)
    tile_x: int = Field(ge=0, lt=GRID_WIDTH)
    tile_y: int = Field(ge=0, lt=GRID_HEIGHT)
    # The frame the play was decided on. If given, the play is refused as
    # stale if that frame is older than max_age seconds when the bot gets
    # to it.
    frame: int | None = None
    max_age: float = Field(default=1.0, gt=0)


class PlayOut(BaseModel):
    card: str
    hand_index: int
    tile_x: int
    tile_y: int
    # The frame the play was checked against and tapped on. The screen
    # shows it played a few frames later.
    frame: int

    @classmethod
    def of(cls, result: PlayResult) -> "PlayOut":
        return cls(
            card=result.card.name,
            hand_index=result.play.hand_index,
            tile_x=result.play.tile_x,
            tile_y=result.play.tile_y,
            frame=result.frame,
        )


class RejectionOut(BaseModel):
    # Stable, for matching on: not_running, paused, builtin_policy,
    # not_in_battle, play_pending, busy, stale, timeout, bad_hand_index,
    # not_ready, not_enough_elixir, bad_tile.
    reason: str
    message: str


class TowerPlaceOut(BaseModel):
    # The tiles under the tower's base, both ends included.
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    # Its centre, in tiles, where tile (x, y) covers x to x + 1 and y to
    # y + 1: (9, 3) is the corner where four tiles meet.
    centre: tuple[float, float]


class GridOut(BaseModel):
    width: int
    height: int
    river_rows: list[int]
    # Named as in the state's towers.
    towers: dict[str, TowerPlaceOut]
    description: str


class CardOut(BaseModel):
    name: str
    cost: int
    # Spells and the like: playable on any tile, not just your side.
    target_anywhere: bool
    units: list[str]


class UnitOut(BaseModel):
    name: str
    category: str
    # What it attacks: air, ground, buildings or all. Null if it doesn't.
    target: str | None
    # How it moves: air or ground. Null for buildings.
    transport: str | None

    @classmethod
    def of(cls, unit: Unit) -> "UnitOut":
        return cls(
            name=unit.name,
            category=unit.category.value,
            target=unit.target.value if unit.target else None,
            transport=unit.transport.value if unit.transport else None,
        )


class ElixirPhaseOut(BaseModel):
    # Seconds from the start of the battle, overtime included.
    start: int = Field(alias="from")
    to: int
    seconds_per_elixir: float


class ElixirSectionOut(BaseModel):
    # "normal" (regulation time), then "overtime".
    type: str
    length: int


class ElixirOut(BaseModel):
    starting: int
    max: int
    sections: list[ElixirSectionOut]
    phases: list[ElixirPhaseOut]


class TowerStatsOut(BaseModel):
    # At level 1. Towers grow with level by their own table, which isn't in
    # the game files the bot reads.
    hitpoints_level_1: int
    damage_level_1: int | None
    # Seconds between shots.
    hit_speed: float | None
    # Tiles.
    range: float | None


class MetaOut(BaseModel):
    grid: GridOut
    # The deck the bot was set up with, which the card detector looks for.
    deck: list[CardOut]
    cards: list[CardOut]
    units: list[UnitOut]
    policy: Literal["builtin", "external"]
    elixir: ElixirOut
    # "princess" and "king".
    tower_stats: dict[str, TowerStatsOut]
    # Levels run from 1 to this. Stats are scaled to a level with ?level=
    # on /api/units/{name} and /api/cards/{name}.
    max_level: int
    # The level assumed when none is given.
    default_level: int


class SpawnOut(BaseModel):
    # The unit's name, as in detections. Null for a game entity the bot
    # doesn't detect.
    unit: str | None
    # The game's own name for it.
    game_name: str
    count: int
    # Seconds between spawns, for units that keep spawning (the Witch).
    interval: float | None = None


class UnitStatsOut(BaseModel):
    name: str
    level: int
    game_name: str | None
    hitpoints: int | None
    shield_hitpoints: int | None
    # Per hit. For splash damage, area_damage_radius is the radius, in
    # tiles.
    damage: int | None
    dps: float | None
    area_damage_radius: float | None
    death_damage: int | None
    # Seconds between hits, and before the first.
    hit_speed: float | None
    first_hit: float | None
    # In tiles.
    range: float | None
    sight_range: float | None
    collision_radius: float | None
    # The game's movement speed: 45 slow, 60 medium, 90 fast, 120 very
    # fast. Null for buildings.
    speed: int | None
    # Seconds from being played to acting.
    deploy_time: float | None
    mass: int | None
    flying: bool
    building: bool
    # Seconds a building lasts. Null for troops.
    lifetime: float | None
    attacks_air: bool
    attacks_ground: bool
    targets_only_buildings: bool
    spawns: SpawnOut | None = None
    death_spawns: SpawnOut | None = None


class SummonOut(SpawnOut):
    # The unit's stats at the card's level. Null if the bot doesn't know
    # the unit.
    stats: UnitStatsOut | None


class SpellOut(BaseModel):
    # Per wave, at the card's level. Null for spells whose damage comes
    # over time (Poison, Earthquake) or not at all.
    damage: int | None
    waves: int
    # What a wave does to a crown tower, and the percentage that is.
    crown_tower_damage: int | None
    crown_tower_damage_percent: int | None
    # In tiles.
    radius: float | None


class CardStatsOut(BaseModel):
    name: str
    level: int
    # The lowest level a card of its rarity can be.
    min_level: int
    game_name: str
    type: Literal["troop", "building", "spell"]
    rarity: str
    cost: int
    # What it puts in the arena, with each unit's stats.
    summons: list[SummonOut]
    spell: SpellOut | None = None


def card_out(card: Card) -> CardOut:
    return CardOut(
        name=card.name,
        cost=card.cost,
        target_anywhere=card.target_anywhere,
        units=[unit.name for unit in card.units],
    )


def all_cards() -> list[Card]:
    return sorted(Cards.all(), key=lambda card: card.name)


def meta(deck: list[Card], policy: Literal["builtin", "external"]) -> MetaOut:
    return MetaOut(
        grid=GridOut(
            width=GRID_WIDTH,
            height=GRID_HEIGHT,
            river_rows=RIVER_ROWS,
            towers={
                name: TowerPlaceOut(
                    x_min=x0,
                    y_min=y0,
                    x_max=x1,
                    y_max=y1,
                    centre=((x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2),
                )
                for name, (x0, y0, x1, y1) in TOWER_TILES.items()
            },
            description=(
                "Tile (0, 0) is the bottom-left of the arena as you see it: "
                "your side. x runs 0-17 left to right, y runs 0-31 from your "
                "end to the enemy's. Rows 0-14 are your half, rows 15 and "
                "16 the river, with bridges at x 3 and 14, and rows 17-31 "
                "the enemy's half."
            ),
        ),
        deck=[card_out(card) for card in deck],
        cards=[card_out(card) for card in all_cards()],
        units=[UnitOut.of(unit) for unit in Units.all()],
        policy=policy,
        elixir=ElixirOut.model_validate(game_data.elixir()),
        tower_stats={
            name: TowerStatsOut.model_validate(stats)
            for name, stats in game_data.towers().items()
        },
        max_level=game_data.max_level(),
        default_level=game_data.DEFAULT_LEVEL,
    )
