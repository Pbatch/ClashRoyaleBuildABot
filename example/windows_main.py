import ctypes
import msvcrt
import sys
import time
from datetime import datetime
from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from clashroyalebuildabot.data.cards import Cards
from clashroyalebuildabot.state.error_handler import adb_fix
from custom_bot import CustomBot

ctypes.windll.kernel32.SetConsoleTitleW("Clash Royale Build-A-Bot")

def main():
    adb_fix()
    logs_dir = Path("clashroyalebuildabot/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_file_name = f"bot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    log_file_path = logs_dir / log_file_name
    logger.add(log_file_path, rotation="10 MB", retention="1 month")

    console = Console()
    menu_options = ["Start (Default Config)", "Settings", "Exit"]
    selected_option = 0
    print_menu(console, menu_options, selected_option)

    while True:
        key = msvcrt.getch()
        if key == b"\xe0":
            key = msvcrt.getch()
            if key == b"H":
                selected_option = (selected_option - 1) % len(menu_options)
            elif key == b"P":
                selected_option = (selected_option + 1) % len(menu_options)
        elif key == b"\r":
            handle_menu_selection(console, selected_option)

        update_menu(console, menu_options, selected_option)
        time.sleep(0.1)

def handle_menu_selection(console, selected_option):
    if selected_option == 0:
        console.clear()
        print_title(console)
        logger.info("Starting the bot")
        start_bot()
    elif selected_option == 1:
        info_text = Text("[INFO] Settings coming soon...")
        console.print(Panel(info_text))
        time.sleep(2)
    elif selected_option == 2:
        sys.exit()

def print_menu(console, menu_options, selected_option):
    console.clear()
    print_title(console)
    for index, option in enumerate(menu_options):
        if index == selected_option:
            prefix = "» "
            style = "bold white on #4287f5"
        else:
            prefix = "  "
            style = "#cccccc"
        console.print(f"{prefix}{option}", style=style)

def print_title(console):
    crown_art = r"""
             _.+._
           (^\/^\/^)
            \@*@*@/
            {_____}
    """
    crown_text = Text(crown_art, style="#FDDC5C")
    community_text = Text("     - Community Edition -", style="#cccccc")
    link_text = Text.from_markup("[link=https://github.com/Pbatch]@Pbatch[/link]", style="#4287f5")
    version_text = Text(") version 1.2.1", style="#999999")
    version_line = Text.assemble("by Pbatch (", link_text, version_text, style="#999999")

    combined_text = Text.assemble(
        crown_text,
        "\n",
        "  ",
        community_text,
        "\n",
        "  ",
        version_line,
        "\n\n"
    )
    console.print(combined_text)

def start_bot():
    try:
        card_names = [
            Cards.MINIONS,
            Cards.ARCHERS,
            Cards.ARROWS,
            Cards.GIANT,
            Cards.MINIPEKKA,
            Cards.FIREBALL,
            Cards.KNIGHT,
            Cards.MUSKETEER,
        ]
        bot = CustomBot(card_names, debug=False)
        bot.run()
    except ImportError:
        logger.error("Error: custom_bot.py not found. Make sure the file exists.")
        sys.exit(1)

def your_settings_function():
    pass

def update_menu(console, menu_options, selected_option):
    console.clear()
    print_menu(console, menu_options, selected_option)

if __name__ == "__main__":
    main()
