## Errors list and fix:

### Error E000:
Unknown error, please create an issue.

### Error E001
A required import is missing. Install the dependencies by running `uv sync` in the project folder. Also, make sure that you're using the venv [as described in the setup guide](bot-installation.md#step-4-create-a-virtual-environment).


### Error E002
Parsing of config file failed. Your settings are in `config.yaml` in the project folder. If the error lists settings, fix each one it names: an unknown setting is usually misspelt or in the wrong section, and the others have a value of the wrong kind (for example text where a number should be). Otherwise, check the file is valid YAML. Compare it with [the defaults](../clashroyalebuildabot/default_config.yaml). To go back to the default settings, delete your `config.yaml`.


### Error E003
Bot crashed during its runtime with an unknown error. Please create an issue.


### Error E004
GUI couldn't initialize. If you see this error despite not having modified files in the `/gui` folder, please create an issue.


### Error E005
Strategy definition error: some part of the bot's strategy has been misconfigured (actions, cards, etc.). Check that you've listed exactly 8 actions in `main.py`, one for each card in your deck, and that each card has an image in `clashroyalebuildabot/images/cards`. See [the bot development tutorial](bot-development.md) for more details.

Also, don't forget that each Action class must have a CARD attribute:
```
class ArchersAction(Action):
    CARD = Cards.ARCHERS
```


### Error E006
Error while connecting to the ADB device: Make sure to have ADB enabled on your device/emulator, and that your computer recognizes it by running `platform-tools/adb devices -l` in the project folder, and checking that your device is present in the displayed list. This is the bot's own copy of ADB, installed during [setup](bot-installation.md#step-7-run-setup).


### Error E007
Error while running a command on the device using ADB: if the error concerns a device not being found, see E006 above. Else, please create an issue.


### Error E008
Lost the video stream from the device, or no video arrived after connecting. Check that the device/emulator is still running and connected (`adb devices -l`), then restart the bot. If the screen is on and the error persists, please create an issue.


### Error E009
Couldn't save your settings to `config.yaml` in the project folder. Check that the file isn't read-only or open in another program, and that you have write permission for the project folder.


### Error E010
The bot couldn't reach the vision model server it uses to read the screen. The bot only starts a server itself when **Server URL** under Screen Detector in the Settings tab (`screen_detector.base_url` in `config.yaml`) is on this computer (`http://localhost:8001` by default) and `auto_start` is on. Otherwise, start the server before the bot, and check that the URL matches its address.


### Error E011
The bot's copy of ADB isn't installed. Run `uv run python -m clashroyalebuildabot.install` in the project folder (see [Bot Installation](bot-installation.md#step-7-run-setup)). It downloads ADB into `platform-tools/`.


### Error E012
The vision model server the bot started didn't come up. Its log, `debug/vlm_server.log` in the project folder, says why. Common causes:
- **Out of GPU memory:** close other programs using the GPU, or lower `gpu_memory_utilization` under `screen_detector` in `config.yaml`.
- **The model isn't downloaded and there's no internet:** run setup (see [Bot Installation](bot-installation.md#step-7-run-setup)).
- **The first start is slow:** vLLM compiles the model the first time, which can take several minutes on a slower GPU. Raise `startup_timeout` under `screen_detector`.
