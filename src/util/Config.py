import os
import platform
import time
from enum import Enum
from pathlib import Path

from exceptions.Exceptions import ParameterException, OSNotSupported
from generator.baseline.Baseline import BaselineGenerator
from util.ProgramArguments import get_program_arguments


class GeneratorOptions(Enum):
    baseline = 1
    gan = 2


class Config:
    instance = None

    def __init__(self, args):

        self.strftime = time.strftime("%Y%m%d-%H%M%S")

        self.generator = args.generator if args.generator else GeneratorOptions.baseline
        if self.generator not in GeneratorOptions:
            raise ParameterException(f"The selected generator is not an option: {GeneratorOptions}")

        self.current_path = Path(".")
        found_src = False
        while not found_src:
            for file in self.current_path.glob("*"):
                if file.name == "src":
                    found_src = True
                    break
            if not found_src:
                self.current_path = Path(f'{self.current_path}/..')
        self.current_path = str(self.current_path)[:-2]

        self.level_amount: int = args.level_amount if args.level_amount else 1
        self.level_path: str = args.level_path + os.sep if args.level_path else os.path.normpath(
            f'{self.current_path}/resources/data/generated_level/')
        self.game_folder_path: str = args.game_folder_path if args.game_folder_path else os.path.normpath(
            f'{self.current_path}/resources/science_birds/{{os}}')
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

        self.ai_path = args.ai_path if args.ai_path else os.path.normpath(
            f'{self.current_path}/ai/Naive-Agent-standalone-Streamlined.jar')
        self.rescue_level_path = os.path.normpath(f'{self.current_path}/data/level_archive/{{timestamp}}/')

        self.evaluate = args.evaluate if args.evaluate else False
        self.rescue_level = args.rescue_level if args.rescue_level else True

        # Ml stuff
        self.tf_records_name = os.path.normpath(f'{self.current_path}/resources/data/tfrecords/{{dataset_name}}.tfrecords')
        self.train_log_dir = os.path.normpath(f'{self.current_path}/resources/logs/{{current_run}}/{{timestamp}}/train')
        self.image_store = os.path.normpath(f"{self.current_path}/resources/imgs/generated/{{timestamp}}/")
        self.checkpoint_dir = os.path.normpath(f'{self.current_path}/resources/models/{{current_run}}/{{timestamp}}/')

    def __str__(self):
        return f'Config:' \
               f'\tstrftime = {self.strftime} \n' \
               f'\tgenerator = {self.generator} \n' \
               f'\tcurrent_path = {self.current_path} \n' \
               f'\tlevel_amount = {self.level_amount} \n' \
               f'\tlevel_path = {self.level_path} \n' \
               f'\tgame_folder_path = {self.game_folder_path} \n' \
               f'\tai_path = {self.ai_path} \n' \
               f'\trescue_level_path = {self.rescue_level_path} \n' \
               f'\tevaluate = {self.evaluate} \n' \
               f'\trescue_level = {self.rescue_level} \n' \
               f'\ttf_records_name = {self.tf_records_name} \n' \
               f'\ttrain_log_dir = {self.train_log_dir} \n' \
               f'\timage_store = {self.image_store} \n' \
               f'\tcheckpoint_dir = {self.checkpoint_dir} \n'

    @staticmethod
    def get_instance(args = None):
        if Config.instance is None:
            parser = get_program_arguments()
            parsed_args = parser.parse_args(args = args)
            Config.instance = Config(parsed_args)

        return Config.instance

    def get_generated_image_store(self):
        return self.image_store.replace("{timestamp}", self.strftime)

    def get_log_dir(self, run_name):
        return self.train_log_dir.replace("{timestamp}", self.strftime).replace("{current_run}", run_name)

    def get_current_checkpoint_dir(self, run_name):
        return self.checkpoint_dir.replace("{timestamp}", self.strftime).replace("{current_run}", run_name)

    def get_checkpoint_dir(self, run_name, strftime):
        return self.checkpoint_dir.replace("{timestamp}", strftime).replace("{current_run}", run_name)

    def get_generator(self):
        if self.generator == GeneratorOptions.baseline:
            return BaselineGenerator()

    def get_tf_records(self, dataset_name: str):
        return self.tf_records_name.replace("{dataset_name}", dataset_name)

    def get_leve_path(self):
        return self.level_path

    def get_game_path(self):
        return self.game_path

    def get_game_folder_path(self):
        return self.game_folder_path

    def get_game_level_path(self):
        return os.path.join(self.game_folder_path, self.copy_dest)

    def get_ai_path(self):
        return self.ai_path


if __name__ == '__main__':
    config = Config.get_instance()
