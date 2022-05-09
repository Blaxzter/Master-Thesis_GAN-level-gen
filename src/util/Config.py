import os
import platform

from exceptions.Exceptions import ParameterException, OSNotSupported
from generator.baseline.baseline import BaselineGenerator

GeneratorOptions = [
    'baseline'
]


class Config:
    def __init__(self, args):
        self.generator = args.generator
        if self.generator not in GeneratorOptions:
            raise ParameterException(f"The selected generator is not an option: {GeneratorOptions}")

        self.level_amount: int = args.level_amount
        self.level_path: str = args.level_path + os.sep
        self.game_folder_path: str = args.game_folder_path
        if '{os}' in self.game_folder_path:
            os_name = platform.system()
            if os_name == 'Windows':
                self.game_folder_path = self.game_folder_path.replace('{os}', 'win-new')
                self.game_path = os.path.join(self.game_folder_path, "ScienceBirds.exe")
                self.copy_dest = os.path.normpath('ScienceBirds_Data/StreamingAssets/Levels/')
            elif os_name == 'Darwin':
                self.game_folder_path = self.game_folder_path.replace('{os}', 'osx-new')
                self.game_path = os.path.join(self.game_folder_path, "ScienceBirds.app")
                self.copy_dest = os.path.normpath('Sciencebirds.app/Contents/Resources/Data/StreamingAssets/Levels')
            else:
                raise OSNotSupported("OS is not support atm")

        self.evaluate = args.evaluate
        self.rescue_level = args.rescue_level
        self.rescue_level_path = os.path.normpath('./data/level_archive/{timestamp}/')

    def get_generator(self):
        if self.generator == 'baseline':
            return BaselineGenerator()

    def get_leve_path(self):
        return self.level_path

    def get_game_path(self):
        return self.game_path

    def get_game_folder_path(self):
        return self.game_folder_path

    def get_game_level_path(self):
        return os.path.join(self.game_folder_path, self.copy_dest)
