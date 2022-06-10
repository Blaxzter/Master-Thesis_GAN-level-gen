from game_management.GameConnection import GameConnection
from game_management.GameManager import GameManager
from generator.baseline.Baseline import BaselineGenerator
from util.Config import Config
from util.Evaluator import Evaluator


class GeneratorFramework:
    def __init__(self, conf: Config):
        self.generated_level_path = conf.generated_level_path
        self.generator = conf.get_generator()

        self.game_connection = GameConnection(conf = conf)
        self.game_manager = GameManager(conf = conf, game_connection = self.game_connection)
        self.evaluator = Evaluator(conf = conf, game_connection = self.game_connection)

    def run(self):
        self.generate()
        self.evaluate()

    def stop(self):
        self.game_manager.stop_game()

    def generate(self):
        self.generator.generate_level_init(
            folder_path = self.generated_level_path,
        )

    def evaluate(self):
        self.game_manager.start_game()
        copied_levels = self.game_manager.copy_game_levels()
        for copied_level in copied_levels:
            level_index = int(copied_level.name[6:8])
            self.evaluator.evaluate_levels(start_level = level_index)


