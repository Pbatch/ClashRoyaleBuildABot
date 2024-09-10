import tkinter as tk
from threading import Thread
from typing import List, Type

from clashroyalebuildabot import Bot
from clashroyalebuildabot.actions.generic.action import Action


class Gui:
    def __init__(self, config, actions: List[Type[Action]]):
        self.bot = None
        self.config = config
        self.actions = actions
        self.bot_thread = None
        self.running = False

        self.save_labels = None
        self.save_images = None
        self.show_images = None
        self.load_deck = None
        self.auto_start_game = None
        self.action_delay = None

    def run(self):
        root = tk.Tk()
        root.title("CRBAB MENU")
        root.minsize(400, 350)

        start_button = tk.Button(root, text="Start bot ✅", command=self.start_bot, bg="lightgreen")
        start_button.pack(pady=10)

        start_button = tk.Button(root, text="Pause / Resume bot", command=Bot.pause_or_resume)
        start_button.pack(pady=10)

        stop_button = tk.Button(root, text="Stop bot ❌", command=self.stop_bot, bg="lightcoral")
        stop_button.pack(pady=10)

        restart_button = tk.Button(root, text="Update + restart bot 🔄", command=self.restart_bot, bg="lightblue")
        restart_button.pack(pady=10)

        self.save_labels = tk.IntVar(value=self.config["visuals"]["save_labels"])
        save_labels_checkbox = tk.Checkbutton(root, text="Save labels", variable=self.save_labels)
        save_labels_checkbox.pack(pady=5)

        self.save_images = tk.IntVar(value=self.config["visuals"]["save_images"])
        save_images_checkbox = tk.Checkbutton(root, text="Save images", variable=self.save_images)
        save_images_checkbox.pack(pady=5)

        self.show_images = tk.IntVar(value=self.config["visuals"]["show_images"])
        show_images_checkbox = tk.Checkbutton(root, text="Show images", variable=self.show_images)
        show_images_checkbox.pack(pady=5)

        self.load_deck = tk.IntVar(value=self.config["bot"]["load_deck"])
        load_deck_checkbox = tk.Checkbutton(root, text="Load Deck", variable=self.load_deck)
        load_deck_checkbox.pack(pady=5)

        self.auto_start_game = tk.IntVar(value=self.config["bot"]["auto_start_game"])
        auto_start_game_checkbox = tk.Checkbutton(root, text="Auto start game", variable=self.auto_start_game)
        auto_start_game_checkbox.pack(pady=5)

        # Log Level Dropdown
        action_delays = [0.5, 1, 1.25, 1.5]
        self.action_delay = tk.StringVar(value=self.config["ingame"]["play_action"])
        action_delay_menu = tk.OptionMenu(root, self.action_delay, *action_delays)
        tk.Label(root, text="Action delay").pack(pady=5)
        action_delay_menu.pack(pady=5)

        exit_button = tk.Button(root, text="Exit", command=root.quit)
        exit_button.pack(pady=10)

        root.mainloop()

    def restart_bot(self):
        """Restart the bot by stopping the current instance and starting a new one with the updated config."""
        if self.running:
            self.stop_bot()
        self.update_config()
        self.start_bot()

    def update_config(self):
        """Update the config with the current state of the checkboxes."""
        self.config["visuals"]["save_labels"] = self.save_labels.get()
        self.config["visuals"]["save_images"] = self.save_images.get()
        self.config["visuals"]["show_images"] = self.show_images.get()
        self.config["bot"]["load_deck"] = self.load_deck.get()
        self.config["bot"]["auto_start_game"] = self.auto_start_game.get()
        self.config["ingame"]["play_action"] = float(self.action_delay.get())

    def bot_task(self):
        self.bot = Bot(actions=self.actions, config=self.config)
        self.bot.run()

    def start_bot(self):
        """Start the bot in a separate thread to keep the GUI responsive."""
        if self.running:
            return
        self.update_config()
        self.running = True
        self.bot_thread = Thread(target=self.bot_task)
        self.bot_thread.daemon = True  # Daemon thread will close when the program exits
        self.bot_thread.start()

    def stop_bot(self):
        if not self.bot:
            return
        self.bot.stop()
        self.running = False

