import os
from pathlib import Path

import matplotlib.pyplot as plt

from game_management.GameConnection import GameConnection
from game_management.GameManager import GameManager
from generator.baseline.Baseline import BaselineGenerator
from level.Level import Level
from level.LevelReader import LevelReader
from level.LevelVisualizer import LevelVisualizer
from util import ProgramArguments
from util.Config import Config


def generate_structure():
    config = Config.get_instance()

    level_dest = config.get_data_train_path(folder = 'generated/single_structure/')
    generator = BaselineGenerator()
    generator.settings(number_levels = 3, ground_structure_range = (1, 1), air_structure_range=(0, 0))
    generator.generate_level_init(folder_path = level_dest)


def leve_visualisation():
    # generate_structure()

    config = Config.get_instance()
    game_connection = GameConnection(conf = config)
    game_manager = GameManager(conf = config, game_connection = game_connection)
    game_manager.start_game(is_running = False)

    # config.game_folder_path = os.path.normpath('../science_birds/{os}')
    for level_path in sorted(Path(config.get_data_train_path(folder = 'generated/single_structure')).glob('*.xml')):
        level_reader = LevelReader()
        level_visualizer = LevelVisualizer()

        parse_level = level_reader.parse_level(str(level_path), use_blocks = True, use_pigs = True, use_platform = True)
        parse_level.filter_slingshot_platform()

        parse_level.normalize()
        parse_level.create_polygons()

        game_manager.change_level(path = str(level_path))

        fig, ax = plt.subplots(1, 3, dpi = 300, figsize=(15, 5))

        level_visualizer.visualize_screenshot(game_connection.create_level_img(structure = True), ax = ax[0])
        level_visualizer.create_img_of_level(level = parse_level, element_ids = False, use_grid = True, add_dots = False, ax = ax[1])
        level_visualizer.visualize_level_img(parse_level, dot_version = False, ax = ax[2])
        fig.suptitle(f'Level: {str(level_path)}', fontsize = 16)

        fig.tight_layout()
        plt.show()

    game_manager.stop_game()



if __name__ == '__main__':
    leve_visualisation()
