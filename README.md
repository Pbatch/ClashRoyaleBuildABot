# Clash Royale Build-A-Bot
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-7-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->
[![PyPI version](https://badge.fury.io/py/ClashRoyaleBuildABot.svg)](https://badge.fury.io/py/ClashRoyaleBuildABot)

Build your own bot to play Clash Royale

![demo](https://raw.githubusercontent.com/wiki/Pbatch/ClashRoyaleBuildABot/images/demo.gif)

## Description

We present an advanced state generator, which is accurate and returns a lot of information.
It uses:
* YOLOv5 to infer the units and numbers
* Image hashes to detect the cards
* A simple function of the pixels to deduce the elixir

![detector](https://raw.githubusercontent.com/wiki/Pbatch/ClashRoyaleBuildABot/images/demo.jpg)

With a more powerful interpretation of the state,
we can start to build bots that can make intelligent decisions.

## Getting Started

* [Setup](https://github.com/Pbatch/ClashRoyaleBuildABot/wiki/Setup) your environment and the emulator.

* [Try](https://github.com/Pbatch/ClashRoyaleBuildABot/wiki/Tutorial-(Basic)) the basic bot building tutorial.

* [Learn](https://github.com/Pbatch/ClashRoyaleBuildABot/wiki/State) how the state is generated.

## Releases

* 1.1.0
  * Moved to bigger Yolov5 model.
  * Predict 'ally/enemy' separately from the unit (Doubles training data + fewer classes to predict).

## Roadmap

* Improve flaws of PeteBot (Placement, elixir management, etc.).
* Label more images, of more diverse cards, so that more decks can be played.
* Add a layer that operates on the object detection output to produce more reliable unit predictions. 
(I.e. Tracking units over time).
* Add a basic Q-learning tutorial.
* Add a basic imitation learning tutorial.
* Publish the YOLOv5 training notebook.
* Add the ability to open chests and upgrade cards.
* Publish a leaderboard of the best bots made with the repo.
* ... Your next big idea?

## Community Creations

![Hog2.6Cycle](https://raw.githubusercontent.com/wiki/Pbatch/ClashRoyaleBuildABot/images/hog.gif)

Hog 2.6 Cycle Bot by OwenKruse

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/link-discord"><img src="https://avatars.githubusercontent.com/u/50463727?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Link</b></sub></a><br /><a href="#data-link-discord" title="Data">🔣</a></td>
    <td align="center"><a href="http://www.pazder.ca"><img src="https://avatars.githubusercontent.com/u/17608446?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Emgimeer-Bazder</b></sub></a><br /><a href="https://github.com/Pbatch/ClashRoyaleBuildABot/issues?q=author%3AEmgimeer-Bazder" title="Bug reports">🐛</a></td>
    <td align="center"><a href="https://github.com/GavriloviciEduard"><img src="https://avatars.githubusercontent.com/u/33176335?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Gavrilovici Eduard</b></sub></a><br /><a href="https://github.com/Pbatch/ClashRoyaleBuildABot/commits?author=GavriloviciEduard" title="Documentation">📖</a> <a href="https://github.com/Pbatch/ClashRoyaleBuildABot/commits?author=GavriloviciEduard" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/Nyantad"><img src="https://avatars.githubusercontent.com/u/68382673?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Nyantad</b></sub></a><br /><a href="https://github.com/Pbatch/ClashRoyaleBuildABot/issues?q=author%3ANyantad" title="Bug reports">🐛</a></td>
    <td align="center"><a href="https://github.com/OwenKruse"><img src="https://avatars.githubusercontent.com/u/91492770?v=4?s=100" width="100px;" alt=""/><br /><sub><b>OwenKruse</b></sub></a><br /><a href="https://github.com/Pbatch/ClashRoyaleBuildABot/commits?author=OwenKruse" title="Documentation">📖</a> <a href="#data-OwenKruse" title="Data">🔣</a> <a href="https://github.com/Pbatch/ClashRoyaleBuildABot/commits?author=OwenKruse" title="Code">💻</a> <a href="#example-OwenKruse" title="Examples">💡</a></td>
    <td align="center"><a href="http://martinmiglio.dev/?utm_source=github_bio&utm_medium=Social"><img src="https://avatars.githubusercontent.com/u/10036276?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Martin Miglio</b></sub></a><br /><a href="https://github.com/Pbatch/ClashRoyaleBuildABot/commits?author=marmig0404" title="Code">💻</a> <a href="https://github.com/Pbatch/ClashRoyaleBuildABot/commits?author=marmig0404" title="Documentation">📖</a> <a href="#a11y-marmig0404" title="Accessibility">️️️️♿️</a> <a href="#example-marmig0404" title="Examples">💡</a> <a href="#userTesting-marmig0404" title="User Testing">📓</a></td>
    <td align="center"><a href="https://github.com/ankushsethi"><img src="https://avatars.githubusercontent.com/u/22005886?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Ankush Sethi</b></sub></a><br /><a href="https://github.com/Pbatch/ClashRoyaleBuildABot/issues?q=author%3Aankushsethi" title="Bug reports">🐛</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
