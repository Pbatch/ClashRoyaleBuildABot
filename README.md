# Clash Royale Build-A-Bot

Build your own bot to play Clash Royale (Windows only).

![demo](images/demo.gif)

## Description

Open-source tools for creating Clash Royale bots are poor, 
largely due to the way they process the screen to generate a state.

Most repositories are missing data, or return incorrect data from the screen.

We present an advanced state generator, which is accurate and returns a lot of information.

For example, the image above returns the following:
![detector](images/detector.jpg)

```
{   'cards': [   {   'cost': 5,
                     'name': 'giant',
                     'target': 'buildings',
                     'type': 'troop'},
                 {   'cost': 3,
                     'name': 'arrows',
                     'target': 'air/ground',
                     'type': 'spell'},
                 {   'cost': 4,
                     'name': 'musketeer',
                     'target': 'air/ground',
                     'type': 'troop'},
                 {   'cost': 3,
                     'name': 'arrows',
                     'target': 'air/ground',
                     'type': 'spell'},
                 {   'cost': 3,
                     'name': 'arrows',
                     'target': 'air/ground',
                     'type': 'spell'}],
    'numbers': {   'ally_king_hp': {   'bounding_box': (188, 495, 216, 502),
                                       'confidence': [0.8971471190452576],
                                       'number': 3312},
                   'ally_king_level': {   'bounding_box': (162, 487, 190, 494),
                                          'confidence': [0.8971471190452576],
                                          'number': 6},
                   'elixir': {   'bounding_box': (100, 628, 350, 643),
                                 'confidence': 1.0,
                                 'number': 1},
                   'enemy_king_hp': {   'bounding_box': (188, 15, 216, 22),
                                        'confidence': [0.9022195935249329],
                                        'number': 3312},
                   'enemy_king_level': {   'bounding_box': (162, 19, 190, 26),
                                           'confidence': [0.9022195935249329],
                                           'number': 6},
                   'left_ally_princess_hp': {   'bounding_box': (   74, 401,
                                                                    102, 408),
                                                'confidence': [-1],
                                                'number': -1},
                   'left_enemy_princess_hp': {   'bounding_box': (   74, 93,
                                                                     102, 100),
                                                 'confidence': [   0.9093992114067078,
                                                                   0.8552120327949524,
                                                                   0.7632281184196472,
                                                                   0.8506384491920471],
                                                 'number': 2030},
                   'right_ally_princess_hp': {   'bounding_box': (   266, 401,
                                                                     294, 408),
                                                 'confidence': [-1],
                                                 'number': -1},
                   'right_enemy_princess_hp': {   'bounding_box': (   266, 93,
                                                                      294,
                                                                      100),
                                                  'confidence': [   0.8797102570533752,
                                                                    0.8611167073249817,
                                                                    0.7743588089942932,
                                                                    0.8635557293891907],
                                                  'number': 2030}},
    'screen': {'end_of_game': False, 'in_game': True, 'lobby': False},
    'units': {   'ally_archer': [   {   'bounding_box': [79, 318, 100, 348],
                                        'confidence': 0.8947366},
                                    {   'bounding_box': [97, 319, 121, 350],
                                        'confidence': 0.8853236}],
                 'ally_minion': [   {   'bounding_box': [247, 247, 271, 274],
                                        'confidence': 0.9168539},
                                    {   'bounding_box': [263, 243, 286, 271],
                                        'confidence': 0.91089755},
                                    {   'bounding_box': [250, 226, 277, 254],
                                        'confidence': 0.89560986}],
                 'ally_minipekka': [   {   'bounding_box': [61, 252, 98, 282],
                                           'confidence': 0.8354934}],
                 'enemy_minipekka': [   {   'bounding_box': [   231, 111, 263,
                                                                142],
                                            'confidence': 0.9178544}]}}
```

With a more powerful interpretation of the state,
we can start to build bots that can make intelligent decisions.

## Getting Started

* [Setup](https://github.com/Pbatch/ClashRoyaleBuildABot/wiki/Setup) your environment and the emulator.

* [Try](https://github.com/Pbatch/ClashRoyaleBuildABot/wiki/Tutorial-(Basic)) the basic tutorial.
