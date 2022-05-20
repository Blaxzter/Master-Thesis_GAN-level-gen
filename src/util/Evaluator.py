from util.Config import Config
from GameManagement.GameConnection import GameConnection


class Evaluator:

    def __init__(self, conf: Config, game_connection: GameConnection):
        self.start_level = 4
        self.end_level = 4
        self.game_connection = game_connection
        self.data = {}

    def evaluate_level(self):
        print("\nChange Level")
        self.game_connection.change_level(index = 3)

        print("\nGet Data")
        self.game_connection.get_data()

        print("Start AI")
        self.game_connection.startAi(start_level = 3, end_level = 4)
        self.game_connection.wait_till_all_level_played()

        print("\nGet Data Again")
        self.game_connection.get_data()


