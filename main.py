from datetime import datetime
import os
import sys
import threading
import time
import yaml
from loguru import logger
from clashroyalebuildabot.bot.example.custom_bot import CustomBot
from clashroyalebuildabot.constants import DEBUG_DIR
from clashroyalebuildabot.updater import Updater

start_time = datetime.now()

def update_terminal_title():
    while True:
        elapsed_time = datetime.now() - start_time
        hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        sys.stdout.write(f"\x1b]2;{formatted_time} | BuildABot\x07")
        sys.stdout.flush()
        time.sleep(1)

def main():
    bot = CustomBot(debug=False)
    bot.run()

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), "clashroyalebuildabot/config.yaml")
    with open(config_path, encoding="utf-8") as file:
        config = yaml.safe_load(file)

    log_level = config.get("bot", {}).get("log_level", "INFO").upper()

    logger.remove()
    logger.add(sys.stdout, level=log_level)
    logger.add(os.path.join(DEBUG_DIR, "bot.log"), rotation="500 MB", level=log_level)

    # Update-Prüfung und Hauptprogramm starten
    Updater().check_for_update()
    title_thread = threading.Thread(target=update_terminal_title, daemon=True)
    title_thread.start()
    main()
