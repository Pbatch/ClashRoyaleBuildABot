# Bot State

Each step, the [detector](../clashroyalebuildabot/detectors/detector.py) turns a screenshot into a `State`: the units on the field, tower health, the time left, elixir, the cards in your hand and the current screen.

It combines six detectors: card, screen, unit, tower HP, timer and number (elixir). The unit detector also uses the side detector to decide which units are yours.

## Card detector

To work out which cards are in your hand, and which card comes next, we use the [card_detector](../clashroyalebuildabot/detectors/card_detector.py).

Before the game starts, the art of each card in your deck is shrunk to a tiny greyscale thumbnail (a hash), along with blank cards for empty hand slots. The art is in [images/cards](../clashroyalebuildabot/images/cards), cropped to the card's face, which is how cards are framed in your hand. A card with an evolution also has its evolved art (`<card>_ev1.jpg`), since an evolved card is drawn with that instead.

Then, each step, we hash the screen at each card position and match the hashes to the cards, so that every position gets a different card. The bottom of each card is left out: in your hand it has the elixir cost badge, which the art doesn't.

A card you can't afford yet is drawn in grey and washed out, apart from a darker wedge that sweeps round from 12 o'clock as your elixir fills. So for a greyed card, each pixel is compared with the art as drawn normally, washed out or in the wedge, whichever is closest. A card in colour is compared with the art as it is.

Washed-out cards can look alike, so the detector also remembers what it saw. A card stays in its position until it's played, and the card that replaces it is the one that was next, so each position is nudged towards the card it held last frame, or the card that was next. Clear evidence of another card still wins. The memory is cleared between battles.

A card is ready to play when the middle of its art is in colour rather than grey. An empty slot is never ready.

If the game's card art changes, the card positions are `CARD_BOXES` in [constants/screenshot.py](../clashroyalebuildabot/constants/screenshot.py), and the art comes from RoyaleAPI's card images (`https://cdn.royaleapi.com/static/img/cards/<card-name>.png`), cropped to the face inside the rarity border.

## Screen detector

To move between the lobby, the game and the end-of-game screens, we use the [screen_detector](../clashroyalebuildabot/detectors/screen_detector.py).

It asks [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B), a small vision-language model, which screen the screenshot shows. The model runs in a separate [vLLM](https://github.com/vllm-project/vllm) server, and the bot talks to it through [vlm_client.py](../clashroyalebuildabot/detectors/vlm_client.py).

The answer is shaped by a Pydantic model, `ScreenAnswer`: vLLM only lets the model produce JSON that fits its schema, so it can only name a known screen. The choices come straight from [screens.py](../clashroyalebuildabot/game/screens.py): lobby, in game and end of game, plus the screens in between (searching for an opponent, loading, the VS screen and the Match Over! banner), which the bot waits through without tapping or playing cards. Naming the in-between screens matters: given only lobby, in game and end of game to choose from, a model confidently picks the closest wrong one. Names matter too: with `matchmaking` and `match_over` as choices, the model wrote `match` and then picked the wrong ending, so the first is called `searching_for_opponent`. The same answer says where the OK button is, to tell the two end-of-game layouts apart.

The model takes a few hundred milliseconds, so it runs in the background about once a second and the bot uses its latest answer. That answer is a second or more old, so when a battle ends it still says "in game" while the results screen is up. Before the bot plays a card, the [battle_check](../clashroyalebuildabot/detectors/battle_check.py) confirms the current frame shows the elixir drop at the left end of the elixir bar, which only a battle shows, by comparing a few pixels with [in_game.jpg](../clashroyalebuildabot/images/screen/in_game.jpg). If it doesn't, the screen counts as unknown and the bot waits. The card, unit, elixir, tower HP and timer detectors only run in a battle. On other screens the state has no units or cards and 0 elixir.

The settings are under `screen_detector` in [default_config.yaml](../clashroyalebuildabot/default_config.yaml), and where to tap on each screen is in [screens.py](../clashroyalebuildabot/game/screens.py).

## Unit detector

To work out what units are on the battlefield, we use the [unit_detector](../clashroyalebuildabot/detectors/unit_detector.py).

It uses YOLOv10 (an object detector), trained on many labelled screenshots. The ONNX runtime is used to perform fast inference.

![image](https://github.com/Pbatch/ClashRoyaleBuildABot/assets/37177749/0887a413-880d-4381-a577-e757a8d87443)

Here you can see the confusion matrix of the performance. If you are interested in a certain deck where your cards have not been labelled,
post your deck in the Issues section and I'll see what I can do.

## Tower HP reader

To read every tower's health and level, we use the [tower_hp_reader](../clashroyalebuildabot/detectors/tower_hp_reader.py). Each tower's health bar has its exact HP written on it, with the tower's level on a badge to its left, so we crop each bar, enlarge it, and ask the same vision model the screen detector uses to read both numbers. Its answer is shaped by a Pydantic model, `TowerReading`: a level and an HP, with 0 HP for a destroyed tower. The level is asked for first; asked the other way round, the model read rubble as 100 HP.

- King towers are asked differently. Until it's first hit, a king tower shows only its level badge, with no health bar, so for a king tower "no bar" means untouched, not destroyed: its HP stays `inf` (standing) and its level is still read. If a king tower falls, the battle is over anyway.
- The six towers are read in parallel, in the background, about once a second, and only during a battle. Between battles the readings are cleared.
- Until the first reading of a battle, each tower's HP is `inf`: treated as standing, never as destroyed, and its level is 0. If one tower's reading fails, it keeps its previous values. A destroyed tower keeps its last level, since its badge is gone and levels don't change during a battle.
- The readings are in `State.numbers.towers`, one `Tower` (with `hp` and `level`) for each of `left_enemy_princess`, `right_enemy_princess`, `left_ally_princess`, `right_ally_princess`, `enemy_king` and `ally_king`. For example, `state.numbers.towers.left_enemy_princess.hp`. No action uses the levels or the king towers yet.
- The values are real HP, not fractions. The actions only check whether a tower is destroyed (`0`) and which enemy tower is weaker, and both enemy towers have the same maximum.

The bar positions are `PRINCESS_TOWER_BOXES` and `KING_TOWER_BOXES` in [constants/screenshot.py](../clashroyalebuildabot/constants/screenshot.py).

## Timer reader

To read the time left in a battle, we use the [timer_reader](../clashroyalebuildabot/detectors/timer_reader.py). The top-right corner shows "Time left:" above the minutes and seconds, or "Overtime:" once regulation time ends with the towers level. We crop it, enlarge it, and ask the same vision model to read it. Its answer is shaped by a Pydantic model, `TimerReading`: whether the label says overtime, then the minutes and seconds.

- The reading is in `State.numbers.timer`: `time_left` in seconds, and `overtime`. In overtime, `time_left` counts down the overtime left.
- Like the tower HP, it's read in the background about once a second, and only during a battle, so a reading is about a second old. Between battles it's cleared.
- Until the first reading of a battle, `time_left` is `inf`. If a reading fails, the previous one is kept. No action uses the timer yet.

The timer's position is `TIMER_BOX` in [constants/screenshot.py](../clashroyalebuildabot/constants/screenshot.py).

## Number detector

To read elixir, we use the [number_detector](../clashroyalebuildabot/detectors/number_detector.py). It doesn't use a model: the filled part of the elixir bar is more varied in colour than the empty part, so the point where it becomes uniform gives the elixir, from 0 to 10, in `State.numbers.elixir`. The bar position is `ELIXIR_BOX` in [constants/screenshot.py](../clashroyalebuildabot/constants/screenshot.py).

## Side detector

To work out if a unit is an ally or an enemy, we use the [side_detector](../clashroyalebuildabot/detectors/side_detector.py).

It is a small CNN that runs on 16x16 images. If a unit can't come from a card in your deck, it is always treated as an enemy.
