from clashroyalebuildabot.actions.generic.spell_action import SpellAction
from clashroyalebuildabot.game.cards import Cards


class FireballAction(SpellAction):
    CARD = Cards.FIREBALL
    RADIUS = 2.5
