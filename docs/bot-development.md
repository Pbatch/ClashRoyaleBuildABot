# Bot Development Tutorial

Hello and welcome to the bot development tutorial.

Each step the `Bot` (`clashroyalebuildabot/bot/bot.py`) does the following:

1.) Calculate the `State` of the game (`clashroyalebuildabot/namespaces/state.py`).
```python
@dataclass
class State:
    allies: list[UnitDetection]
    enemies: list[UnitDetection]
    numbers: Numbers
    # Five cards: the next card, then the four in hand.
    cards: list[Card]
    # Playable hand positions (0-3). Hand position i is cards[i + 1].
    ready: list[int]
    screen: Screen
```
The state tracks ally units, enemy units, tower health and elixir, your cards and the current screen. `cards` holds five cards: the next card first, then the four in your hand. `ready` lists the hand positions (0 to 3) that can be played, so hand position `i` is `cards[i + 1]`. See [Bot State](bot-state.md) for how it's calculated.

2.) Use the `State` to score all possible actions, and choose the action with the highest score.
Actions are scored on a per-card basis, so you'll need to write one for each card in your deck.
There are some pre-made actions in `clashroyalebuildabot/actions`.

An action is one card on one tile. Each step, the bot creates an action for every tile a ready card can be played on, if you have enough elixir for it. Troops and buildings can only go on your side of the arena, plus the enemy side once a princess tower there is destroyed. Spells, and cards like Goblin Barrel and Graveyard, can go anywhere.

`calculate_score` returns a list of numbers. Lists are compared item by item, so the first number matters most and later numbers break ties. The bot only plays an action if the first number of the best score is above 0. Return `[0]` for "don't play here".

When developing an action, you should start off as simply as possible.
```python
import random

from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.generic.action import Action


class RandomAction(Action):
    CARD = Cards.MINIPEKKA

    def calculate_score(self, state):
        return [random.random()]
```
This will play minipekka on a random tile on your side of the arena.


You can then start to add more sophisticated behaviour.
```python
from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.generic.action import Action


class MinipekkaAction(Action):
    CARD = Cards.MINIPEKKA

    def calculate_score(self, state):
        if (self.tile_x, self.tile_y) in {(3, 15), (14, 15)}:
            return [1]

        return [0]
```
This will only play minipekka on the bridge.

I used the tile-map to work out which squares corresponded to the start of the bridge.
![tile-map](https://user-images.githubusercontent.com/37177749/170822401-076fc4ec-93f0-441b-ac7b-3d7b875f683f.png)

For common behaviours, you can inherit from the generic actions in `clashroyalebuildabot/actions/generic` instead of writing `calculate_score` yourself. For example, the bundled `MinipekkaAction` inherits from `BridgeAction`, and `KnightAction` from `DefenseAction`.

3.) Once you've written an action for each card, list them in `main.py`. You need exactly 8 actions, one for each card in your deck.
```python
def main():
    actions = [
        ArchersAction,
        ZapAction,
        GoblinBarrelAction,
        GiantAction,
        KnightAction,
        MinionsAction,
        MinipekkaAction,
        MusketeerAction,
    ]
```
Then start the bot with `uv run python main.py` and press start (▶) in the window.

Join the Discord (https://discord.com/invite/K4UfbsfcMa) to discuss and improve the current action classes, and to share your ClashRoyaleBuildABot story :)
