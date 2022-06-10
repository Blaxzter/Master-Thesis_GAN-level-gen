from generator.baseline.Baseline import BaselineGenerator

from loguru import logger
logger.disable('generator.baseline.Baseline')

if __name__ == '__main__':
    generator = BaselineGenerator()
    generator.settings(number_levels = 200)
    generator.generate_level_init(folder_path = "../resources/data/source_files/generated/")
