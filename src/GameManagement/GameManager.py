from GameManagement.GameConnection import GameConnection
from util import ProgramArguments
from util.Config import Config

import os
import shutil
import time
from pathlib import Path

from util.Evaluator import Evaluator


class GameManager:

    def __init__(self, conf: Config, game_connection: GameConnection):
        self.conf = conf
        self.rescue_level = conf.rescue_level
        self.rescue_level_path = conf.rescue_level_path
        self.game_connection = game_connection

    def start_game(self):
        self.game_connection.start()
        self.game_connection.start_game(self.conf.game_path)
        self.game_connection.wait_for_game_window()

    def stop_game(self):
        self.game_connection.stop_components()

    def copy_game_levels(self, level_path = None, rescue_level = None):
        if rescue_level is None:
            rescue_level = self.rescue_level

        if level_path is None:
            level_path = self.conf.level_path

        if rescue_level:
            current_rescue_level_pat = self.rescue_level_path
            timestr = time.strftime("%Y%m%d-%H%M%S")
            current_rescue_level_path = current_rescue_level_pat.replace("{timestamp}", timestr)
            os.mkdir(current_rescue_level_path)
            for src_file in Path(self.conf.get_game_level_path()).glob('*.*'):
                shutil.move(str(src_file), current_rescue_level_path)
        else:
            shutil.rmtree(os.path.join(self.conf.get_game_level_path(), '*'))

        ret_copied_levels = []

        for src_file in Path(level_path).glob('*.*'):
            ret_copied_levels.append(src_file)
            shutil.move(str(src_file), self.conf.get_game_level_path())

        self.game_connection.load_level_menu()

        return ret_copied_levels

    def change_level(self, path):
        for level in Path(self.conf.get_game_level_path()).glob('*.*'):
            os.remove(level)
        shutil.copy(str(path), self.conf.get_game_level_path())
        self.game_connection.load_level_menu()
        self.game_connection.change_level(index = 4)
        pass

    def create_img_of_level(self, index = 4):
        self.game_connection.load_level_menu()
        self.game_connection.change_level(index = index)
        img = self.game_connection.create_img_of_level()
        return img


if __name__ == '__main__':
    parser = ProgramArguments.get_program_arguments()
    config = parser.parse_args()
    config.game_folder_path = os.path.normpath('../science_birds/{os}')

    config = Config(config)
    game_connection = GameConnection(conf = config)
    game_manager = GameManager(conf = config, game_connection = game_connection)
    try:
        game_manager.start_game()
        for level in sorted(Path("../data/train/structures/").glob('*.xml')):
            game_manager.change_level(path = str(level))
            img = game_connection.create_img_of_level()
    except KeyboardInterrupt:
        game_manager.stop_game()
