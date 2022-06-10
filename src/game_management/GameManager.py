import os
import shutil
import time
from pathlib import Path

from loguru import logger

from game_management.GameConnection import GameConnection
from util.Config import Config


class GameManager:

    def __init__(self, conf: Config, game_connection: GameConnection):
        self.conf = conf
        self.rescue_level = conf.rescue_level
        self.rescue_level_path = conf.rescue_level_path
        self.game_connection = game_connection

    def start_game(self, is_running = False):
        logger.debug("Start Game and Game Connection Server")
        self.game_connection.start()
        if not is_running:
            self.game_connection.start_game(self.conf.game_path)
        self.game_connection.wait_for_game_window()

    def stop_game(self):
        logger.debug("Stop Game Components")
        self.game_connection.stop_components()

    def copy_game_levels(self, level_path = None, rescue_level = None):
        if rescue_level is None:
            rescue_level = self.rescue_level

        if level_path is None:
            level_path = self.conf.generated_level_path

        if rescue_level:
            current_rescue_level_pat = self.rescue_level_path
            timestr = time.strftime("%Y%m%d-%H%M%S")
            current_rescue_level_path = current_rescue_level_pat.replace("{timestamp}", timestr)
            os.mkdir(current_rescue_level_path)
            for src_file in Path(self.conf.get_game_level_path()).glob('*.*'):
                shutil.move(str(src_file), current_rescue_level_path)
        else:
            for level in Path(self.conf.get_game_level_path()).glob('*.*'):
                os.remove(level)

        ret_copied_levels = []

        for src_file in Path(level_path).glob('*.*'):
            ret_copied_levels.append(src_file)
            shutil.move(str(src_file), self.conf.get_game_level_path())

        self.game_connection.load_level_menu()

        return ret_copied_levels

    def change_level(self, path, delete_level = True):
        if delete_level:
            for level in Path(self.conf.get_game_level_path()).glob('*.*'):
                os.remove(level)
        shutil.copy(str(path), self.conf.get_game_level_path())
        self.game_connection.load_level_menu()
        self.game_connection.change_level(index = 4)
        pass

    def create_img_of_level(self, index = 4):
        self.game_connection.load_level_menu()
        self.game_connection.change_level(index = index)
        img = self.game_connection.get_img_data()
        return img

    def remove_game_levels(self):
        for level in Path(self.conf.get_game_level_path()).glob('*.*'):
            os.remove(level)
