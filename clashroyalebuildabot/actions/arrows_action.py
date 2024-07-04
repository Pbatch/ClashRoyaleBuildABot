from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.spell_action import SpellAction


class ArrowsAction(SpellAction):
    CARD = Cards.ARROWS
    RADIUS = 4
    MIN_TO_HIT = 5
