from generator.baseline.baseline import BaselineGenerator
from util.Config import Config
from util.Evaluator import Evaluator


class GeneratorFramework:
    def __init__(self, conf: Config):
        self.generated_level_path = conf.level_path
        self.generator = conf.get_generator()
        self.evaluator = Evaluator(conf)

    def run(self):
        self.generate()
        self.evaluate()

    def stop(self):
        self.evaluator.stop_game()

    def generate(self):
        self.generator.generate_level_init(
            folder_path = self.generated_level_path,
        )

    def evaluate(self):
        self.evaluator.copy_game_levels()
        self.evaluator.start_game()
        self.evaluator.evaluate_level(4)


