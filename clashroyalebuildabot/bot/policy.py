"""How the bot decides what to play in a battle.

A policy sees each battle frame's State and returns a Play, or None to
play nothing this frame. The bot checks the play against the rules (see
plays.check) and taps it. Write your own by implementing ``choose``, and
pass it to Bot(policy=...).

With ``bot.policy: external`` in the config there's no policy: the bot
plays what clients send to the API's /api/play instead.
"""

import random
from collections.abc import Sequence
from typing import Protocol

from loguru import logger

from clashroyalebuildabot.actions.generic.action import Action
from clashroyalebuildabot.bot.plays import Play, affordable_hand, tiles_for
from clashroyalebuildabot.game.state import State


class Policy(Protocol):
    def choose(self, state: State) -> Play | None: ...


class ScoringPolicy:
    """The built-in policy: scores every affordable card on every tile it
    can go on, with the card's Action, and plays the best, if its score is
    above 0."""

    def __init__(self, actions: Sequence[type[Action]]) -> None:
        self.cards_to_actions = {action.CARD: action for action in actions}

    def get_actions(self, state: State) -> list[Action]:
        actions: list[Action] = []
        for i, card in affordable_hand(state):
            action = self.cards_to_actions.get(card)
            if action is None:
                continue
            actions.extend(action(i, x, y) for x, y in tiles_for(card, state))
        return actions

    def choose(self, state: State) -> Play | None:
        actions = self.get_actions(state)
        if not actions:
            logger.debug("No actions available")
            return None

        random.shuffle(actions)
        best_score: list[float] = [0]
        best_action = None
        for action in actions:
            score = action.calculate_score(state)
            if score > best_score:
                best_action = action
                best_score = score

        if best_action is None or best_score[0] == 0:
            logger.debug("No good actions available")
            return None

        logger.info(f"Playing {best_action} with score {best_score}")
        return Play(best_action.index, best_action.tile_x, best_action.tile_y)
