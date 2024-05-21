import sys
import ctypes
import msvcrt
import time
from custom_bot import CustomBot
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from loguru import logger
from pathlib import Path
from datetime import datetime

ctypes.windll.kernel32.SetConsoleTitleW("Clash Royale Build-A-Bot")


def main():
    # Create logs directory if it doesn't exist
    logs_dir = Path("clashroyalebuildabot/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Configure Loguru
    log_file_name = f"bot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    log_file_path = logs_dir / log_file_name
    logger.add(log_file_path, rotation="10 MB", retention="1 month")

    console = Console()
    menu_options = [
        "Start (Default Config)",
        "Settings",
        "Exit",
    ]
    selected_option = 0
    print_menu(console, menu_options, selected_option)

    while True:
        key = msvcrt.getch()
        if key == b'\xe0':
            key = msvcrt.getch()
            if key == b'H':
                selected_option = (selected_option - 1) % len(menu_options)
            elif key == b'P':
                selected_option = (selected_option + 1) % len(menu_options)
        elif key == b'\r':
            handle_menu_selection(console, selected_option)  # Pass console here

        update_menu(console, menu_options, selected_option)
        time.sleep(0.1)


def handle_menu_selection(console, selected_option):
    if selected_option == 0:
        console.clear()
        print_title(console)
        logger.info("Starting the bot")
        start_bot()
    elif selected_option == 1:
        info_text = Text("[INFO] Settings coming soon...")  # Define info_text here
        console.print(Panel(info_text))
        time.sleep(2)
    elif selected_option == 2:
        sys.exit()


def print_menu(console, menu_options, selected_option):
    console.clear()

    print_title(console)  # Always print the title

    # Menu Options with Styling (more visually distinct)
    for index, option in enumerate(menu_options):
        if index == selected_option:
            prefix = "» "  # Arrow symbol for selected option
            style = "bold white on #4287f5"  # White text on blue background
        else:
            prefix = "  "
            style = "#cccccc"  # Lighter gray for unselected options
        console.print(f"{prefix}{option}", style=style)


def print_title(console):
    # ASCII Crown
    crown_art = r"""
             _.+._    
           (^\/^\/^)  
            \@*@*@/
            {_____}
    """
    crown_text = Text(crown_art, style="#FDDC5C")  # Darker gray for the crown

    # Community Edition text (optional darkening)
    community_text = Text("     - Community Edition -", style="#cccccc")  # Slightly darker gray

    # Version text with link and color
    link_text = Text.from_markup("[link=https://github.com/Pbatch]@Pbatch[/link]", style="#4287f5")  # Blue link
    version_text = Text(f") version 1.2.1", style="#999999")  # Lighter gray for version
    version_line = Text.assemble("by Pbatch (", link_text, version_text, style="#999999")

    # Combine crown, community edition, and version text
    combined_text = Text.assemble(
        crown_text,
        "\n",
        "  ",  # Space before community edition
        community_text,
        "\n",
        "  ",  # Space before version
        version_line,
        "\n\n"  # Two empty lines for better spacing
    )

    # Print the combined text
    console.print(combined_text)


def start_bot():
    try:
        card_names = ['minions', 'archers', 'arrows', 'giant',
                      'minipekka', 'fireball', 'knight', 'musketeer']
        bot = CustomBot(card_names, debug=False)
        bot.run()
    except ImportError:
        logger.error("Error: custom_bot.py not found. Make sure the file exists.")  # Use logger.error
        sys.exit(1)


def your_settings_function():
    # Insert your settings code here
    pass  # Placeholder, replace this with your code


def update_menu(console, menu_options, selected_option):
    console.clear()  # Clear the console before redrawing menu
    print_menu(console, menu_options, selected_option)


if __name__ == '__main__':
    main()
