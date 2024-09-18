import matplotlib.pyplot as plt
import pandas as pd


def draw_chart_from_battle_log():
    data = pd.read_csv("battle_log.csv")

    data["timestamp"] = pd.to_datetime(data["timestamp"])

    data["result"] = data["win"]

    plt.figure(figsize=(10, 5))
    plt.xlabel("Timestamp")
    plt.xticks(rotation=45)

    plt.plot(data["timestamp"], data["trophies"], color="orange", marker="x")
    plt.ylabel("Trophies")
    plt.title("Battle Results and Trophies Over Time")
    plt.legend(["Trophies"])

    # add lines for win and loss
    for i in range(len(data)):
        if data["result"][i] == 1:
            plt.axvline(x=data["timestamp"][i], color="green", alpha=0.5)
        else:
            plt.axvline(x=data["timestamp"][i], color="red", alpha=0.5)

    plt.grid()
    plt.show()


draw_chart_from_battle_log()
