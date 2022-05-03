import os
import sys
import argparse

from generator.GeneratorFramework import GeneratorFramework
from util.Config import Config

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'Generate levels for angry birds.')
    parser.add_argument('--generator', dest = 'generator', type = str, default = 'baseline', help = 'What generator to be used')
    parser.add_argument('--level_amount', dest = 'level_amount', type = int, default = 1, help = 'How many levels to generate')
    parser.add_argument('--level_path', dest = 'level_path', type = str, default = os.path.normpath('./data/generated_level/'), help = 'Path of generated levels')
    parser.add_argument('--game_folder_path', dest = 'game_folder_path', type = str, default = os.path.normpath('./science_birds/{os}'), help = 'Set a different path to the game')
    parser.add_argument('--rescue_level', dest = 'rescue_level', type = bool, default = True, help = 'If a delete shall copy levels in the game folder.')
    parser.add_argument('--evaluate', dest = 'evaluate', type = bool, default = False, help = 'If the generated level should be evaluated')

    parsed_args = parser.parse_args()

    conf = Config(parsed_args)
    generator = GeneratorFramework(conf)
    try:
        generator.run()
    except:
        print("Stop the generator framework")
        generator.stop()

    generator.stop()


