# Bot State

Each step, the [detector](../clashroyalebuildabot/detectors/detector.py) turns a screenshot into a `State`: the units on the field, tower health, the time left, elixir, the cards in your hand and the current screen.

It combines six detectors: card, screen, unit, tower HP, timer and number (elixir).

## Card detector

To work out which cards are in your hand, and which card comes next, we use the [card_detector](../clashroyalebuildabot/detectors/card_detector.py).

Each card's art, cropped to the card's face (which is how cards are framed in your hand), has been shrunk to a tiny greyscale thumbnail (a hash). The hashes ship in [constants/card_hashes.py](../clashroyalebuildabot/constants/card_hashes.py); the art itself doesn't. Before the game starts, the detector loads the hashes of the cards in your deck, along with blank cards for empty hand slots. A card with an evolution also has a hash of its evolved art (`<card>_ev1`), since an evolved card is drawn with that instead.

Then, each step, we hash the screen at each card position and match the hashes to the cards, so that every position gets a different card. The bottom of each card is left out: in your hand it has the elixir cost badge, which the art doesn't.

A card you can't afford yet is drawn in grey and washed out, apart from a darker wedge that sweeps round from 12 o'clock as your elixir fills. So for a greyed card, each pixel is compared with the art as drawn normally, washed out or in the wedge, whichever is closest. A card in colour is compared with the art as it is.

Washed-out cards can look alike, so the detector also remembers what it saw. A card stays in its position until it's played, and the card that replaces it is the one that was next, so each position is nudged towards the card it held last frame, or the card that was next. Clear evidence of another card still wins. The memory is cleared between battles.

A card is ready to play when the middle of its art is in colour rather than grey. An empty slot is never ready.

If the game's card art changes, the card positions are `CARD_BOXES` in [constants/screenshot.py](../clashroyalebuildabot/constants/screenshot.py). The maintainers keep the card art and remake the hashes from it when cards are added or their art changes.

## Screen detector

To move between the lobby, the game and the end-of-game screens, we use the [screen_detector](../clashroyalebuildabot/detectors/screen_detector.py). It compares small thumbnails of fixed parts of the screen with references, so it costs next to nothing and runs on every frame.

- **Battle:** first, it looks for the elixir drop at the left end of the elixir bar, which only a battle shows, by comparing an 8x8 thumbnail of it with one stored in [screen_hashes.py](../clashroyalebuildabot/constants/screen_hashes.py). If it's there, the screen is in game, so the bot plays as soon as a battle starts and stops as soon as it ends.
- **Lobby and results:** otherwise, it looks for the buttons the bot taps: Battle in the lobby, and Play Again and OK on the results screen, or OK alone in the centre in its other layout. Buttons look the same whatever the arena or event behind them. Each button's thumbnail is in [screen_hashes.py](../clashroyalebuildabot/constants/screen_hashes.py), and where each one is, `LOBBY_BATTLE_BOX` and the `RESULTS_*_BOX`es, in [constants/screenshot.py](../clashroyalebuildabot/constants/screenshot.py).
- **Anything else** (searching for an opponent, loading, the VS screen, popups) is unknown, and the bot waits. The elixir bar can also be hidden for a moment mid-battle, so an unknown screen keeps the tower, timer and hand readings; only the lobby or the results screen clears them for the next battle.

The card, unit, elixir, tower HP and timer detectors only run in a battle. On other screens the state has no units or cards and 0 elixir. Where to tap on each screen is in [screens.py](../clashroyalebuildabot/game/screens.py).

## Unit detector

To work out what units are on the battlefield, we use the [unit_detector](../clashroyalebuildabot/detectors/unit_detector.py).

It uses one model, [units_tiles.onnx](../clashroyalebuildabot/models/units_tiles.onnx), run with the ONNX runtime. Instead of drawing boxes, it reads the arena as its grid of 18 x 32 tiles and gives, for every tile, the chance that each unit, ours or the enemy's, is standing on it. A unit stands where its feet are, so a tile's answer can come from the sprite drawn above it.

- **Model:** a MobileNetV4 that reads the strip of the screenshot between the top of the arena and the cards. Its features at 1/8, 1/16 and 1/32 of the screen's size are combined, so a tile is about 2 x 2 feature cells, then read at each tile's centre.
- **Which tiles count:** a unit is reported on a tile that is the most likely of its 3 x 3 neighbours for that unit (with at least a 40% chance), or that is at least 70% likely on its own. The second rule keeps every member of a swarm on neighbouring tiles. The first alone would merge them into one, while a tile beside a unit whose feet are near a tile edge, which is often half likely, isn't reported twice.
- **Allies:** your units can only come from your deck, including the units your cards spawn, like a witch's skeletons. So an ally is always named from your deck. On each tile, the model's strongest ally guess, whatever unit it's for, says how likely it is that one of yours is there, and it's named after the deck unit the model rates highest on that tile. A unit of yours that the model mistakes for one you don't have is still found, under the right name. Enemies can be any unit. The units the model knows are `DETECTOR_UNITS`, in the same file.
- **Positions:** each detection's tile is in `tile_x` and `tile_y`, counted from the bottom left as elsewhere in the bot. There is no box around the sprite: `bbox` is the tile itself, in screenshot pixels.

The model is trained on synthetic frames: sprites of every unit pasted onto empty arenas, with health bars, spells and other clutter, so no frames need labelling by hand. The sprites come from the game's own textures and the [KataCR dataset](https://github.com/wty-yy/Clash-Royale-Detection-Dataset). It has only been measured on synthetic frames so far (81% of units found and 90% of reports right); on real battles it misses some units and sometimes names the wrong one.

## Tower HP reader

To read every tower's health, we use the [tower_hp_reader](../clashroyalebuildabot/detectors/tower_hp_reader.py). Each tower's health bar has its exact HP written on it in the game's own font, so we match that font's digits across each bar's crop with the [digit_reader](../clashroyalebuildabot/detectors/digit_reader.py). It works on each pixel's darkest colour channel, which keeps the digits' light fill and turns the coloured bars, grass and badges dark. The digit templates were rendered from the font in the game's APK and are stored in `models/digit_glyphs.npz`. No GPU is needed.

- A number that can't be read isn't taken to mean much on its own, since "Elixir!" and other pop-ups often cover it. A princess tower without a number keeps its last HP while its bar's pink or blue is still there; only with neither number nor bar for 3 readings in a row is it rubble (0 HP), and it stays rubble for the rest of the battle.
- Until it's first hit, a king tower shows only its level badge, with no health bar, so a king tower without a number keeps its last HP: `inf` (standing) until it's hit. If a king tower falls, the battle is over anyway.
- The six towers are read in parallel, in the background, about once a second, and only during a battle. Between battles the readings are cleared.
- Until the first reading of a battle, each tower's HP is `inf`: treated as standing, never as destroyed. Tower levels aren't read, so `level` is always 0.
- The readings are in `State.numbers.towers`, one `Tower` (with `hp` and `level`) for each of `left_enemy_princess`, `right_enemy_princess`, `left_ally_princess`, `right_ally_princess`, `enemy_king` and `ally_king`. For example, `state.numbers.towers.left_enemy_princess.hp`. No action uses the king towers yet.
- The values are real HP, not fractions. The actions only check whether a tower is destroyed (`0`) and which enemy tower is weaker, and both enemy towers have the same maximum.

The bar positions are `PRINCESS_TOWER_BOXES` and `KING_TOWER_BOXES` in [constants/screenshot.py](../clashroyalebuildabot/constants/screenshot.py).

## Timer reader

To read the time left in a battle, we use the [timer_reader](../clashroyalebuildabot/detectors/timer_reader.py). The top-right corner shows "Time left:" above the minutes and seconds, or "Overtime:" once regulation time ends with the towers level. We crop it and read the time with the same [digit_reader](../clashroyalebuildabot/detectors/digit_reader.py) as the tower HP, and whether it's overtime by matching both labels, rendered in the game's font, against the line above.

- The reading is in `State.numbers.timer`: `time_left` in seconds, and `overtime`. In overtime, `time_left` counts down the overtime left.
- Like the tower HP, it's read in the background about once a second, and only during a battle, so a reading is about a second old. Between battles it's cleared.
- Until the first reading of a battle, `time_left` is `inf`. If the timer can't be read, the previous reading is kept. No action uses the timer yet.

The timer's position is `TIMER_BOX` in [constants/screenshot.py](../clashroyalebuildabot/constants/screenshot.py).

## Number detector

To read elixir, we use the [elixir_reader](../clashroyalebuildabot/detectors/elixir_reader.py). It doesn't use a model: the filled part of the elixir bar is more varied in colour than the empty part, so the point where it becomes uniform gives the elixir, from 0 to 10, in `State.numbers.elixir`. The bar position is `ELIXIR_BOX` in [constants/screenshot.py](../clashroyalebuildabot/constants/screenshot.py).
