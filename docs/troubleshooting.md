## Errors list and fix:

### Error E000:
Unknown error, please create an issue.

### Error E001
A required import is missing. Install the dependencies by running `uv sync` in the project folder. Also, make sure that you're using the venv [as described in the setup guide](bot-installation.md#step-4-create-a-virtual-environment).


### Error E002
Parsing of config file failed. Your settings are in `config.yaml` in the project folder. If the error lists settings, fix each one it names: an unknown setting is usually misspelt or in the wrong section, and the others have a value of the wrong kind (for example text where a number should be). Otherwise, check the file is valid YAML. Compare it with [the defaults](https://github.com/Pbatch/ClashRoyaleBuildABot/blob/main/clashroyalebuildabot/default_config.yaml). To go back to the default settings, delete your `config.yaml`.


### Error E003
Bot crashed during its runtime with an unknown error. Please create an issue.


### Error E005
Strategy definition error: some part of the bot's strategy has been misconfigured (actions, cards, etc.). Check that you've listed exactly 8 actions in `main.py`, one for each card in your deck, and that each card has an embedding in `clashroyalebuildabot/models/card_embeddings.npz` (a card the game added recently may not have one yet). See [the bot development tutorial](bot-development.md) for more details.

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
Lost the connection to the screen server the bot runs on the device, the server couldn't start, or no picture arrived after connecting. Check that the device/emulator is still running and connected (`adb devices -l`), then restart the bot. If the screen is on and the error persists, please create an issue.


### Error E009
Couldn't save your settings to `config.yaml` in the project folder. Check that the file isn't read-only or open in another program, and that you have write permission for the project folder.


### Error E010
No longer used. Older versions of the bot raised it when they couldn't reach the vision model server they read the screen with; the bot no longer has one.

### Error E011
The bot's copy of ADB isn't installed, and the bot couldn't install it itself; the error says why (usually no internet). Run `uv run python -m clashroyalebuildabot.install` in the project folder (see [Bot Installation](bot-installation.md#step-7-run-setup)). It downloads ADB into `platform-tools/`.

If you also have another `adb` installed, for example from your package manager or Android Studio, don't run it while the bot is running: two different versions of ADB keep restarting each other's server, which drops the bot's connection.


### Error E012
No longer used. Older versions of the bot raised it when the vision model server they started didn't come up; the bot no longer has one.

### Error E013
The device runs a version of Android older than 14. The bot reads the screen with a small server it runs on the device, which needs Android 14 or newer. Use a newer phone, or an Android Studio emulator with an Android 14 or newer system image (see [Device Setup](emulator-setup.md)).
