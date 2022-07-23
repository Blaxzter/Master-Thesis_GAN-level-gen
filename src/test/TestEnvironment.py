from pathlib import Path

from game_management.GameConnection import GameConnection
from game_management.GameManager import GameManager
from level.LevelReader import LevelReader
from level.LevelVisualizer import LevelVisualizer
from util.Config import Config


class TestEnvironment:

    def __init__(self, level_folder = 'structures'):
        self.config = Config.get_instance()
        self.game_connection = GameConnection(conf = self.config)
        self.game_manager = GameManager(conf = self.config, game_connection = self.game_connection)
        self.level_reader = LevelReader()
        self.level_visualizer = LevelVisualizer()
        self.level_path = self.config.get_data_train_path(folder = level_folder)

        self.levels = list(map(str, Path(self.level_path).glob('*.xml')))

    def __len__(self):
        return

    def iter_levels(self, start = 0, end_number = -1):
        if end_number == -1:
            end_number = len(self.levels)

        for level_counter, level_path in enumerate(self.levels[start:end_number]):
            level = self.level_reader.parse_level(level_path)
            level.normalize()
            level.create_polygons()
            yield level_counter, level

    def get_level(self, idx):
        level_path = self.levels[idx]
        level = self.level_reader.parse_level(level_path)
        level.normalize()
        level.create_polygons()
        return level

    def start_game(self, is_running = False):
        self.game_manager.start_game(is_running = is_running)

    def get_levels(self):
        return sorted(self.levels)

