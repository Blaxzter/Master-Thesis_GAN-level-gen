from generator.baseline.Baseline import BaselineGenerator

from loguru import logger

from util.Config import Config

logger.disable('generator.baseline.Baseline')

if __name__ == '__main__':
    config = Config.get_instance()

    generator = BaselineGenerator()
    generator.settings(number_levels = 1, ground_structure_range = (1, 1), air_structure_range=(0, 0))
    generator.generate_level_init(folder_path = "../resources/data/source_files/generated/single_structure/")
