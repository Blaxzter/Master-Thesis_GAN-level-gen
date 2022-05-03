import os
import shutil
import time
from pathlib import Path

from util.Config import Config
from util.GameConnection import GameConnection


class Evaluator:

    def __init__(self, conf: Config):
        self.conf = conf
        self.rescue_level = conf.rescue_level
        self.rescue_level_path = conf.rescue_level_path
        self.game_connection = GameConnection()
        self.data = {}

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

        for src_file in Path(self.conf.level_path).glob('*.*'):
            shutil.move(str(src_file), self.conf.get_game_level_path())


    def evaluate_level(self, index = 4):
        self.game_connection.change_level(index = index)
        time.sleep(2)
        ret_dat = self.game_connection.getData()
        self.data[index] = ret_dat


