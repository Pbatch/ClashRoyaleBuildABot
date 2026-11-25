### Wiki: Device Setup
---
The bot plays on an Android device it reaches over [ADB](https://developer.android.com/tools/adb). That's either an Android phone connected by USB or the Android emulator from Android Studio.

### Recommended Settings

Whichever device you use, set it up like this:

- **Orientation:** Portrait
- **Display Resolution:** 720x1280
- **Pixel Density:** 240 DPI
- **Android Version:** 11 or newer

**Security Notice:** Be careful about entering credentials into any device or emulator image. Only sign in with your Google account on devices and images from trusted sources.

---

### Option 1: An Android Phone

A real phone is the simplest option: it runs the game natively and doesn't need a powerful computer.

1. **Enable Developer Options:** Open `Settings > About phone` and tap **Build number** seven times.
2. **Enable USB Debugging:** Turn it on in `Settings > System > Developer options`. The menu's location varies between phones.
3. **Connect the Phone** to your computer with a USB cable, and accept the "Allow USB debugging?" prompt on the phone. On Windows, ADB may also need your phone maker's USB driver (see [Install OEM USB drivers](https://developer.android.com/studio/run/oem-usb)); Pixel phones use the [Google USB Driver](https://developer.android.com/studio/run/win-usb).
4. **Set the Resolution:** Most phones have a taller screen than 720x1280. Once you've installed the bot's copy of ADB ([Bot Installation, Step 7](bot-installation.md#step-7-run-setup)), run these commands in the project folder:
   ```bash
   platform-tools/adb shell wm size 720x1280
   platform-tools/adb shell wm density 240
   ```
   On Windows, write `platform-tools\adb` instead of `platform-tools/adb`, here and below.

   To undo them later, run `platform-tools/adb shell wm size reset` and `platform-tools/adb shell wm density reset`.
5. **Find the Serial:** `platform-tools/adb devices` lists your phone's serial. Enter it as the **Device Serial** in the bot's Settings tab.

---

### Option 2: The Android Studio Emulator

The emulator needs hardware virtualization. On Linux, check that `/dev/kvm` exists. On Windows, check that **Virtualization** says **Enabled** on the Performance tab of Task Manager, and the Android Studio installer sets up the rest. If virtualization is off, enable it (VT-x or AMD-V) in your BIOS.

1. **Install [Android Studio](https://developer.android.com/studio/install).**
2. **Create a Virtual Device:** Open `Tools > Device Manager` and create a phone with a **Google Play** system image for **x86_64**, Android 11 or newer. Clash Royale is an ARM app, and these images can run ARM apps.
3. **Set the Display:** In the device's advanced settings, set the resolution to 720x1280 and the density to 240 DPI, and give it at least 4 CPU cores and 4 GB of RAM.
4. **Start the Device** from the Device Manager. The first emulator is usually listed by `adb devices` as `emulator-5554`, which is the bot's default **Device Serial**.

---

### Next Steps with Clash Royale

1. **Install Clash Royale** from the Google Play Store on the device.
2. **Complete the Tutorial:** Play through the initial tutorial to familiarize yourself with the game mechanics.
3. **Language Settings:** Set the game language to English via the in-game settings menu.
4. **Log in to Your Supercell Account** to sync your game progress.

If your device doesn't work with the bot, please [create an issue](https://github.com/Pbatch/ClashRoyaleBuildABot/issues/new) on this repo.
