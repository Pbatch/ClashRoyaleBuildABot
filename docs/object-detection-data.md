# Object Detection Data

The datasets the detection models are trained on.

| Name              | Description            | Link                                                                 |
|-------------------|------------------------|----------------------------------------------------------------------|
| `units.tar.gz`    | Units in YOLOv5 format | [Download](https://drive.google.com/file/d/1ynIj-a5aR5ERtD_TSSrwVYQo98FX1LNB/view?usp=sharing) |
| `numbers.tar.gz`  | Numbers in YOLOv5 format| [Download](https://drive.google.com/file/d/1nsKOIdvvBMr_HveioFjv67Ti9sJh8ECM/view?usp=sharing) |

The units data was used by an earlier version of the unit detector. The current one is trained on synthetic frames instead (see [Bot State](bot-state.md#unit-detector)). The numbers data was used by an earlier version of the number detector. The current one reads the health and elixir bars directly, without a model (see [Bot State](bot-state.md#number-detector)).
