# Bot State

Each step, the [state reader](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/detectors/state_reader.py) turns a screenshot into a `State`: the units on the field, tower health, the time left, elixir, the cards in your hand and the current screen.

It combines six parts: the card, screen and unit detectors, and the tower HP, timer and elixir readers.

## Card detector

To work out which cards are in your hand, and which card comes next, we use the [card_detector](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/detectors/card_detector.py).

A small CNN, [card_embedder.onnx](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/models/card_embedder.onnx), turns each card position into a vector, trained so that a position's vector lies close to its card art's whether the card is in colour, greyed out, raised or the small next card. Every card art's vector ships in `models/card_embeddings.npz`; the art itself doesn't. Before the game starts, the detector picks out the vectors of the cards in your deck, along with blank cards for empty hand slots. A card with an evolution also has its evolved art's vector (`<card>_ev1`), since an evolved card is drawn with that instead. A card the game adds later needs only its art's vector, not a new model (see `dev/cards`).

Then, each step, we embed the screen at each card position and match each position to the deck card whose art's vector is most alike, so that every position gets a different card.

Washed-out cards can look alike, so the detector also remembers what it saw. A card stays in its position until it's played, and the card that replaces it is the one that was next, so each position is nudged towards the card it held last frame, or the card that was next. Clear evidence of another card still wins. The memory is cleared between battles.

A card is ready to play when the middle of its art is in colour rather than grey. An empty slot is never ready.

If the game's card art changes, the card positions are `CARD_BOXES` in [constants/screenshot.py](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/constants/screenshot.py). The maintainers keep the card art and remake the vectors from it when cards are added or their art changes.

## Screen detector

To move between the lobby, the game and the end-of-game screens, we use the [screen_detector](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/detectors/screen_detector.py). It compares small thumbnails of fixed parts of the screen with references, so it costs next to nothing and runs on every frame.

- **Battle:** first, it reads the battle's HUD with the same models the bot reads it with: the timer must show a time, read for sure, and the elixir bar must be there (its number, or its pink fill). Both are needed, since the timer stays on screen, frozen, through the end-of-battle animation and onto the results screen, after the card and elixir bars have gone, and menus have pink of their own. If both are there, the screen is in game, so the bot plays as soon as a battle starts and stops as soon as it ends.
- **Lobby and results:** otherwise, it looks for the buttons the bot taps: Battle in the lobby, and Play Again and OK on the results screen, or OK alone in the centre in its other layout. Buttons look the same whatever the arena or event behind them. Each button's thumbnail is in [screen_hashes.py](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/constants/screen_hashes.py), and where each one is, `LOBBY_BATTLE_BOX` and the `RESULTS_*_BOX`es, in [constants/screenshot.py](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/constants/screenshot.py).
- **Anything else** (searching for an opponent, loading, the VS screen, popups) is unknown, and the bot waits. The elixir bar can also be hidden for a moment mid-battle, so an unknown screen keeps the tower, timer and hand readings; only the lobby or the results screen clears them for the next battle.

The card, unit, elixir, tower HP and timer detectors only run in a battle. On other screens the state has no units or cards and 0 elixir. Where to tap on each screen is in [screens.py](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/game/screens.py).

## Unit detector

To work out what units are on the battlefield, we use the [unit_detector](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/detectors/unit_detector.py).

It uses one model, [units_tiles.onnx](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/models/units_tiles.onnx), run with the ONNX runtime. Instead of drawing boxes, it reads the arena as its grid of 18 x 32 tiles and gives, for every tile, the chance that each unit, ours or the enemy's, is standing on it. A unit stands where its feet are, so a tile's answer can come from the sprite drawn above it.

- **Model:** a MobileNetV4 that reads the strip of the screenshot between the top of the arena and the cards. Its features at 1/8, 1/16 and 1/32 of the screen's size are combined, so a tile is about 2 x 2 feature cells, then read at each tile's centre.
- **Which tiles count:** a unit is reported on a tile that is the most likely of its 3 x 3 neighbours for that unit (with at least a 40% chance), or that is at least 70% likely on its own. The second rule keeps every member of a swarm on neighbouring tiles. The first alone would merge them into one, while a tile beside a unit whose feet are near a tile edge, which is often half likely, isn't reported twice.
- **Nothing walks on a tower:** while a tower stands, ground troops and buildings aren't reported on the tiles under it, so a unit the model sees in a tower's sprite (an X-Bow, say) is dropped. Flyers over a tower are still reported, and so are a balloon's bomb and a phoenix's egg, which land where they fall. Once a tower is destroyed, units can walk over its ruins.
- **Nothing walks in the river:** ground troops and buildings aren't reported in the river's water (rows 15 and 16, off the bridges at x 2-4 and 13-15). Flyers, a balloon's bomb, a phoenix's egg and the units that jump the river still are: the Hog Rider, Royal Hogs, Ram Rider, Prince, Dark Prince and the Mother Witch's cursed hog.
- **Allies:** your units can only come from your deck, including the units your cards spawn, like a witch's skeletons. So an ally is always named from your deck. On each tile, the model's strongest ally guess, whatever unit it's for, says how likely it is that one of yours is there, and it's named after the deck unit the model rates highest on that tile. A unit of yours that the model mistakes for one you don't have is still found, under the right name. Enemies can be any unit. The units the model knows are `DETECTOR_UNITS`, in the same file. New units are only ever added to the end of that list, so a model trained before they were added still works: it reports the units it was trained on.
- **Positions:** each detection's tile is in `tile_x` and `tile_y`, counted from the bottom left as elsewhere in the bot. There is no box around the sprite, just the tile it stands on.

The model is trained on synthetic frames: sprites of every unit pasted onto empty arenas, with health bars, spells and other clutter, so no frames need labelling by hand. The sprites come from the game's own textures and the [KataCR dataset](https://github.com/wty-yy/Clash-Royale-Detection-Dataset). It knows every unit the game's cards put on the battlefield, plus the bombs some of them drop. It has only been measured on synthetic frames so far (79% of units found and 91% of reports right); on real battles it misses some units and sometimes names the wrong one.

## Tower HP reader

To read every tower's health, we use the [tower_hp_reader](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/detectors/tower_hp_reader.py). Each tower's health bar has its exact HP written on it in the game's own font, and a small CNN, [tower_hp_digits.onnx](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/models/tower_hp_digits.onnx), reads all six towers' crops in one batch (see [digit_model](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/detectors/digit_model.py)). It was trained mostly on numbers drawn from the game's font onto real backgrounds, and it skips a number it isn't sure of, such as one half hidden by a pop-up. It takes a few milliseconds, even without a GPU.

- A number that can't be read isn't taken to mean much on its own, since "Elixir!" and other pop-ups often cover it. A princess tower without a number keeps its last HP while its bar's pink or blue is still there; only with neither number nor bar for 2 seconds is it rubble (0 HP), and it stays rubble for the rest of the battle.
- Until it's first hit, a king tower shows only its level badge, with no health bar, so a king tower without a number keeps its last HP, and a number is only taken while its bar is showing (otherwise a troop's level badge or a damage number passing over it would read as its HP). Before it's hit, its HP is its full HP for its level, or `inf` (standing) while that isn't known. If a king tower falls, the battle is over anyway.
- A number that is read can still be wrong (a troop or damage number over it can make a digit vanish for a frame), and towers can't heal, so each tower's readings are filtered. A reading above the tower's full HP is ignored. HP never goes up: a higher reading is ignored, unless readings stay higher for a second, in which case the HP taken before was the misread. A lower reading is only taken once the next reading is at or below it, and a drop of more than 1000 HP must hold for 0.3 seconds. So the HP lags a frame behind (0.3 seconds for a big hit), and one stray frame never gets through.
- The six towers are read on every frame, but only during a battle. Between battles the readings are cleared.
- Until the first reading of a battle, each tower's HP is `inf`: treated as standing, never as destroyed. Levels come from the HP, not the badges: a side's three towers share a level, and a princess tower's first reading is its full HP, which only one level has (`game_data.TOWER_HITPOINTS`, levels 1 to 14). When both of a side's princess towers' first readings give the same level, that's the side's `level`; until then, or if the bot started once they were hit, it's 0.
- The readings are in `State.towers`, one `Tower` (with `hp` and `level`) for each of `left_enemy_princess`, `right_enemy_princess`, `left_ally_princess`, `right_ally_princess`, `enemy_king` and `ally_king`. For example, `state.towers.left_enemy_princess.hp`. No action uses the king towers yet.
- The values are real HP, not fractions. The actions only check whether a tower is destroyed (`0`) and which enemy tower is weaker, and both enemy towers have the same maximum.

The bar positions are `PRINCESS_TOWER_BOXES` and `KING_TOWER_BOXES` in [constants/screenshot.py](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/constants/screenshot.py).

## Timer reader

To read the time left in a battle, we use the [timer_reader](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/detectors/timer_reader.py). The top-right corner shows "Time left:" above the minutes and seconds, or, once regulation time ends with the towers level, a red box with "Overtime" above them. A small CNN, [timer_digits.onnx](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/models/timer_digits.onnx), reads the crop as `m:ss`, with a `+` in front in overtime (see [digit_model](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/detectors/digit_model.py)).

- The reading is in `State.timer`: `time_left` in seconds, and `overtime`. In overtime, `time_left` counts down the overtime left.
- It's read on every frame, but only during a battle. Between battles it's cleared.
- Until the first reading of a battle, `time_left` is `inf`. If the timer can't be read, the previous reading is kept. No action uses the timer yet.

The timer's position is `TIMER_BOX` in [constants/screenshot.py](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/constants/screenshot.py).

## Elixir reader

To read elixir, we use the [elixir_reader](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/detectors/elixir_reader.py). The game writes the elixir beside the elixir drop, in the same font as tower HP, and a small CNN, [elixir_digits.onnx](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/models/elixir_digits.onnx), reads it. The number fades out for a moment each time elixir ticks over, and the model skips a number it isn't sure of; then the elixir comes from how far the bar's pink fill reaches. The result, from 0 to 10, is in `State.elixir`.

- Selecting a card draws a white outline on the bar, showing the card's cost. Only the pink counts as fill, so the outline isn't read as elixir. Where it cuts through the fill, the bar can read low, never high, so the bot never plays a card it can't afford. (The game refuses such a play and leaves the card selected, and the bot's next tap on that card would deselect it.)
- The positions are `ELIXIR_NUMBER_BOX` and `ELIXIR_BOX` in [constants/screenshot.py](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/constants/screenshot.py).
