import sys
import requests
from PyQt6.QtGui import QImage
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage, QPixmap


class StatsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.image = QLabel(self)
        self.inactiveIndicator = QLabel(self)
        self.inactiveIndicator.setText(
            "The visualizer is disabled. Enable it in the Settings tab."
        )

        self.image = QLabel(self)
        self.wins_label = QLabel("Wins: 0", self)
        self.losses_label = QLabel("Losses: 0", self)
        self.winrate_label = QLabel("Winrate: 0", self)
        self.trophy_label = QLabel("Trophies: 0", self)
        self.wins_label.setStyleSheet("font-size: 16px; color: green;")
        self.losses_label.setStyleSheet("font-size: 16px; color: red;")
        self.winrate_label.setStyleSheet("font-size: 16px; color: white;")
        self.trophy_label.setStyleSheet("font-size: 16px; color: white;")
        self.wins_label.move(10, 20)
        self.losses_label.move(10, 50)
        self.winrate_label.move(10, 80)
        self.trophy_label.move(10, 110)
        layout = QVBoxLayout()
        layout.addWidget(self.inactiveIndicator)
        layout.addWidget(self.image)
        self.setLayout(layout)
        self.update_data()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(180000)  # 180000 milliseconds = 3 minutes


    def update_data(self):
        file = open("token.txt", "r")
        token = file.read().strip('\n')
        file.close()
        base_url = "https://api.clashroyale.com/v1"
        # This is an example of enpoint of the reqest, for more check the documentation
        endpoint = "/players/%23VGP2YR0GG/battlelog"
        # Correct Authorization header looks like this: "Authorization: Bearer API_TOKEN".
        query = {"Authorization": f"Bearer {token}"}
        # Send the GET request
        response = requests.get(base_url+endpoint, params=query)
        if response.status_code == 200:
            data = response.json()  # Response is a list of battle logs
            wins = 0  # Initialize counters for wins and losses
            losses = 0
            overall_trophy_change = 0
            # Process each battle in the response
            for battle in data:
                player = battle['team'][0]
                opponent = battle['opponent'][0]
                player_king_hp = player['kingTowerHitPoints']
                opponent_king_hp = opponent['kingTowerHitPoints']
                # Determine the result of the battle
                trophy_change = player.get('trophyChange', 0)
                try:
                    trophy_change = int(trophy_change)
                except ValueError:
                    trophy_change = 0

                overall_trophy_change += trophy_change

                if player_king_hp > 0 and opponent_king_hp <= 0:
                    wins += 1
                elif opponent_king_hp > 0 and player_king_hp <= 0:
                    losses += 1
                elif player_king_hp > opponent_king_hp:
                    wins += 1
                else:
                    losses += 1

                total_games = wins + losses
                if total_games > 0:
                    win_rate = (wins / total_games) * 100
                else:
                    win_rate = 0

            
                self.wins_label.setText(f"Wins: {wins}")
                self.losses_label.setText(f"Losses: {losses}")
                self.winrate_label.setText(f"Winrate: {win_rate}")
                self.trophy_label.setText(f"Trophies: {overall_trophy_change}")
        else:
            print(f"Failed to retrieve data: {response.status_code}")

    def update_active_state(self, active):
        if not active:
            self.inactiveIndicator.show()
        else:
            self.inactiveIndicator.hide()
        self.image.clear()