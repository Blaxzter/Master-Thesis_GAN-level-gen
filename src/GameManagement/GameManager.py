from GameManagement.GameConnection import GameConnection
from util import ProgramArguments
from util.Config import Config

import os
import shutil
import time
from pathlib import Path

from util.Evaluator import Evaluator


class GameManager:

    def __init__(self, conf: Config):
        self.conf = conf
        self.rescue_level = conf.rescue_level
        self.rescue_level_path = conf.rescue_level_path
        self.game_connection = GameConnection()
        self.evaluator = Evaluator(conf, self.game_connection)

    def start_game(self):
        self.game_connection.start()
        self.game_connection.start_game(self.conf.game_path)
        self.game_connection.wait_for_game_window()

    def stop_game(self):
        self.game_connection.stop()

    def copy_game_levels(self):
        if self.rescue_level:
            current_rescue_level_pat = self.rescue_level_path
            timestr = time.strftime("%Y%m%d-%H%M%S")
            current_rescue_level_path = current_rescue_level_pat.replace("{timestamp}", timestr)
            os.mkdir(current_rescue_level_path)
            for src_file in Path(self.conf.get_game_level_path()).glob('*.*'):
                shutil.move(str(src_file), current_rescue_level_path)
        else:
            shutil.rmtree(os.path.join(self.conf.get_game_level_path(), '*'))

        ret_copied_levels = []

        for src_file in Path(self.conf.level_path).glob('*.*'):
            ret_copied_levels.append(src_file)
            shutil.move(str(src_file), self.conf.get_game_level_path())

        return ret_copied_levels

    def change_level(self, path):
        shutil.copy(str(path), self.conf.get_game_level_path())
        self.game_connection.change_level(path.split("/")[-1][:-4])
        pass


if __name__ == '__main__':
    parser = ProgramArguments.get_program_arguments()
    config = parser.parse_args()
    config.game_folder_path = os.path.normpath('../science_birds/{os}')
    game_manager = GameManager(Config(config))
    game_manager.start_game()
    game_manager.change_level(path = "../data/converted_levels/NoRotation/level-08.xml")
