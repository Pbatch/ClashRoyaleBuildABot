# Bot Development Tutorial

Hello and welcome to the bot development tutorial.

Each step the `Bot` (`clashroyalebuildabot/bot/bot.py`) does the following:

1.) Calculate the `State` of the game (`clashroyalebuildabot/game/state.py`).
```python
@dataclass
class State:
    allies: list[UnitDetection]
    enemies: list[UnitDetection]
    elixir: int
    towers: Towers
    timer: Timer
    # Five cards: the next card, then the four in hand. None is an empty slot.
    cards: list[Card | None]
    # Playable hand positions (0-3). Hand position i is cards[i + 1].
    ready: list[int]
    screen: ScreenName
```
`elixir` is 0 to 10, `towers` has an `hp` and `level` for each tower (`state.towers.left_enemy_princess.hp`), and `timer` has `time_left` in seconds and `overtime`. A tower's HP is `inf` until it's been read, and 0 once it's destroyed.

The state tracks ally units, enemy units, tower health and elixir, your cards and the current screen. `cards` holds five cards: the next card first, then the four in your hand. `ready` lists the hand positions (0 to 3) that can be played, so hand position `i` is `cards[i + 1]`. See [Bot State](bot-state.md) for how it's calculated.

2.) Use the `State` to score all possible actions, and choose the action with the highest score.
Actions are scored on a per-card basis, so you'll need to write one for each card in your deck.
There are some pre-made actions in `clashroyalebuildabot/actions`.

An action is one card on one tile. Each step, the bot creates an action for every tile a ready card can be played on, if you have enough elixir for it. Troops and buildings can only go on your side of the arena, apart from the tiles under your own towers, plus the enemy side once a princess tower there is destroyed. Spells, and cards like Goblin Barrel and Graveyard, can go anywhere.

`calculate_score` returns a list of numbers. Lists are compared item by item, so the first number matters most and later numbers break ties. The bot only plays an action if the first number of the best score is above 0. Return `[0]` for "don't play here".

After playing a card, the bot doesn't score anything until the screen shows the card played (it has left your hand, or your elixir has dropped), so it doesn't play the same card twice. If that never shows, for example because the tap missed, it moves on after `play_action` seconds (under `ingame` in the [configuration](bot-installation.md#configuration)).

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
        if (self.tile_x, self.tile_y) in {(3, 14), (14, 14)}:
            return [1]

        return [0]
```
This will only play minipekka in front of the bridges.

I used the tile-map to work out which squares are in front of each bridge. The bridges themselves (`y = 15`) are on the enemy's side, so a troop can only go there once that princess tower is destroyed.
![tile-map](https://user-images.githubusercontent.com/37177749/170822401-076fc4ec-93f0-441b-ac7b-3d7b875f683f.png)

For common behaviours, you can inherit from the generic actions in `clashroyalebuildabot/actions/generic` instead of writing `calculate_score` yourself. For example, the bundled `MinipekkaAction` inherits from `BridgeAction`, and `KnightAction` from `DefenseAction`.

3.) Once you've written an action for each card, list them in `main.py`. You need exactly 8 actions, one for each card in your deck.
```python
def main() -> None:
    actions = [
        ArchersAction,
        GoblinBarrelAction,
        BabyDragonAction,
        CannonAction,
        KnightAction,
        MinipekkaAction,
        MusketeerAction,
        WitchAction,
    ]
```
Then start the bot with `uv run python main.py` and press start (▶) in the window.

Join the Discord (https://discord.com/invite/K4UfbsfcMa) to discuss and improve the current action classes, and to share your ClashRoyaleBuildABot story :)

## Writing a policy

Actions score one card on one tile at a time. To decide in your own way instead, for example by looking at the whole hand at once, write a policy: a class with a `choose` method that takes the `State` and returns a `Play`, or `None` to play nothing this frame.
```python
from clashroyalebuildabot.bot.plays import Play, affordable_hand


class FirstCardPolicy:
    def choose(self, state):
        hand = affordable_hand(state)
        if not hand:
            return None
        hand_index, _card = hand[0]
        return Play(hand_index=hand_index, tile_x=9, tile_y=5)
```
To use it, set `POLICY = FirstCardPolicy()` in `main.py`. Keep the list of actions there too: their cards tell the bot which deck to look for. The bot checks each play against the rules before tapping it (see `clashroyalebuildabot/bot/plays.py`), and `plays.tiles_for(card, state)` lists the tiles a card can go on. The built-in policy, `ScoringPolicy` in `clashroyalebuildabot/bot/policy.py`, is the scoring described above.

To decide in another language, or in another program, use the HTTP API instead: see [Playing the game from your own program](headless-and-api.md#playing-the-game-from-your-own-program).
