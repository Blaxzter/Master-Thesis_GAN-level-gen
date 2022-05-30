from loguru import logger

from generator.GeneratorFramework import GeneratorFramework
from util import ProgramArguments
from util.Config import Config

if __name__ == '__main__':

    parser = ProgramArguments.get_program_arguments()
    parsed_args = parser.parse_args()

    conf = Config(parsed_args)
    generator = GeneratorFramework(conf)
    try:
        generator.run()
    except Exception as e:
        logger.debug(f"Exception occurred: {e}")
        generator.stop()

    generator.stop()
