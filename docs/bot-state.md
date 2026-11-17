# Bot State

Each step, the [detector](../clashroyalebuildabot/detectors/detector.py) turns a screenshot into a `State`: the units on the field, tower health, elixir, the cards in your hand and the current screen.

It combines four detectors: card, screen, unit and number. The unit detector uses a fifth, the side detector, to decide which units are yours.

## Card detector

To work out which cards are in your hand, and which card comes next, we use the [card_detector](../clashroyalebuildabot/detectors/card_detector.py).

Before the game starts, an image of each card in your deck is hashed, along with blank cards for empty hand slots.

Then, each step, we hash the screen at each card position and match the hashes to the cards, so that every position gets a different card.

A card is ready to play when it isn't greyed out.

## Screen detector

To move between the lobby, the game and the end-of-game screens, we use the [screen_detector](../clashroyalebuildabot/detectors/screen_detector.py).

It asks [OneJev1.6-0.8B](https://huggingface.co/OmniJev/OneJev1.6-0.8B), a small vision model, which screen the screenshot shows. The model runs in a separate [Flide](https://github.com/OmniJev/Flide) server and returns a probability for each screen: lobby, in game, end of game, or one of the screens in between (matchmaking, loading, the VS screen and the Match Over! banner), which all count as `UNKNOWN`. Naming those in-between screens matters: given only lobby, in game and end of game to choose from, the model confidently picked the closest wrong one. If no screen reaches `min_confidence` (0.5 by default), the screen is `UNKNOWN`. The same request asks where the OK button is, to tell the two end-of-game layouts apart.

The model takes a few hundred milliseconds, so it runs in the background about once a second and the bot uses its latest answer. The settings are in the Settings tab under Screen Detector, and under `screen_detector` in the [config](bot-installation.md#configuration), and where to tap on each screen is in [screens.py](../clashroyalebuildabot/namespaces/screens.py).

## Unit detector

To work out what units are on the battlefield, we use the [unit_detector](../clashroyalebuildabot/detectors/unit_detector.py).

It uses YOLOv10 (an object detector), trained on many labelled screenshots. The ONNX runtime is used to perform fast inference.

![image](https://github.com/Pbatch/ClashRoyaleBuildABot/assets/37177749/0887a413-880d-4381-a577-e757a8d87443)

Here you can see the confusion matrix of the performance. If you are interested in a certain deck where your cards have not been labelled,
post your deck in the Issues section and I'll see what I can do.

## Number detector

To read tower health and elixir, we use the [number_detector](../clashroyalebuildabot/detectors/number_detector.py). It doesn't use a model: it reads the colours of the health and elixir bars directly.

- **Princess tower health** (all four towers): the health bar is two colours, a bright one for the remaining health and a dark one for the rest. The point where the colour changes gives the health as a fraction from 0 to 1. If neither colour is present, the tower is treated as destroyed (0).
- **Elixir**: the filled part of the elixir bar is more varied in colour than the empty part, so the point where it becomes uniform gives the elixir, from 0 to 10.

The bar positions and colours are in [constants.py](../clashroyalebuildabot/constants.py) (`NUMBER_CONFIG` and `ELIXIR_BOUNDING_BOX`).

## Side detector

To work out if a unit is an ally or an enemy, we use the [side_detector](../clashroyalebuildabot/detectors/side_detector.py).

It is a small CNN that runs on 16x16 images. If a unit can't come from a card in your deck, it is always treated as an enemy.
