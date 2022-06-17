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
        self.data_train_path = os.path.normpath(os.path.join(self.current_path, 'resources/data/source_files/'))
        self.generated_level_path: str = args.generated_level_path + os.sep if args.generated_level_path else \
            os.path.normpath(os.path.join(self.current_path, 'resources/data/generated_level/'))
        self.game_folder_path: str = args.game_folder_path if args.game_folder_path else \
            os.path.normpath(os.path.join(self.current_path, 'resources/science_birds/{os}'))
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

        self.ai_path = args.ai_path if args.ai_path else os.path.normpath(
            os.path.join(self.current_path, 'ai/Naive-Agent-standalone-Streamlined.jar')
        )
        self.rescue_level_path = os.path.normpath(
            os.path.join(self.current_path, 'resources/data/source_files/level_archive/{timestamp}/')
        )

        self.evaluate = args.evaluate if args.evaluate else False
        self.rescue_level = args.rescue_level if args.rescue_level else True

        # Ml stuff
        self.create_tensorflow_writer = True

        self.data_root = os.path.normpath(
            os.path.join(self.current_path, 'resources/data/')
        )
        self.run_data_root = os.path.normpath(
            os.path.join(self.current_path, 'resources/run_data/')
        )
        self.pickle_folder = os.path.normpath(
            os.path.join(self.current_path, 'resources/data/pickles')
        )
        self.tf_records_name = os.path.normpath(
            os.path.join(self.current_path, 'resources/data/tfrecords/{dataset_name}.tfrecords')
        )
        self.log_file_root = os.path.normpath(
            os.path.join(self.current_path, 'resources/logs/')
        )
        self.train_log_dir = os.path.normpath(
            os.path.join(self.current_path, 'resources/logs/{current_run}/{timestamp}/train')
        )
        self.image_root = os.path.normpath(
            os.path.join(self.current_path, 'resources/imgs/')
        )
        self.image_store = os.path.normpath(
            os.path.join(self.current_path, 'resources/imgs/generated/{timestamp}/')
        )
        self.checkpoint_dir = os.path.normpath(
            os.path.join(self.current_path, 'resources/models/{current_run}/{timestamp}/')
        )

        self.save_checkpoint_every = 15
        self.keep_checkpoints = 2

        self.tag = None

    def __str__(self):
        return f'Config:' \
               f'\tstrftime = {self.strftime} \n' \
               f'\tgenerator = {self.generator} \n' \
               f'\tcurrent_path = {self.current_path} \n' \
               f'\tlevel_amount = {self.level_amount} \n' \
               f'\tlevel_path = {self.generated_level_path} \n' \
               f'\tgame_folder_path = {self.game_folder_path} \n' \
               f'\tai_path = {self.ai_path} \n' \
               f'\trescue_level_path = {self.rescue_level_path} \n' \
               f'\tevaluate = {self.evaluate} \n' \
               f'\trescue_level = {self.rescue_level} \n' \
               f'\tcreate_tensorflow_writer = {self.create_tensorflow_writer} \n' \
               f'\ttf_records_name = {self.tf_records_name} \n' \
               f'\ttrain_log_dir = {self.train_log_dir} \n' \
               f'\timage_store = {self.image_store} \n' \
               f'\tsave_checkpoint_every = {self.save_checkpoint_every} \n' \
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

    def get_log_dir(self, run_name, strftime):
        return self.train_log_dir.replace("{timestamp}", strftime).replace("{current_run}", run_name)

    def get_current_log_dir(self, run_name):
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
        return self.generated_level_path

    def get_game_path(self):
        return self.game_path

    def get_game_folder_path(self):
        return self.game_folder_path

    def get_game_level_path(self):
        return os.path.join(self.game_folder_path, self.copy_dest)

    def get_ai_path(self):
        return self.ai_path

    def get_data_train_path(self, folder = None):

        if folder is None:
            return self.data_train_path
        else:
            if folder[-1] != '/':
                folder += '/'
            return os.path.join(self.data_train_path, folder)

    def get_pickle_folder(self):
        return self.pickle_folder

    def get_pickle_file(self, file_name):
        if '.pickle' not in file_name:
            file_name += '.pickle'
        return os.path.join(self.pickle_folder, file_name)

    def get_data_root(self):
        return self.data_root

    def get_log_file(self, log_name):
        for path in Path(self.log_file_root).rglob(log_name):
            split = str(path).split(os.sep)
            return str(path), split[split.index('logs') + 1]
        else:
            return None

    def get_img_path(self, img_folder = None):
        if img_folder is not None:
            return os.path.join(self.image_root, img_folder)
        else:
            return self.image_root

    def get_data_tag(self):
        if self.tag is None:
            raise Exception("Pls make a meaningful tag du hupen")

        return self.tag

    def get_run_data(self, folder):
        if folder is not None:
            return os.path.join(self.run_data_root, folder) + ".pickle"
        else:
            return self.run_data_root


if __name__ == '__main__':
    config = Config.get_instance()
