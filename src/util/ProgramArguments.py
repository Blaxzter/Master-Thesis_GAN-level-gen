import os
import sys
import argparse

def get_program_arguments():

    parser = argparse.ArgumentParser(description = 'Generate levels for angry birds.')
    parser.add_argument('--generator', dest = 'generator', type = str, default = 'baseline', help = 'What generator to be used')
    parser.add_argument('--level_amount', dest = 'level_amount', type = int, default = 1, help = 'How many levels to generate')
    parser.add_argument('--level_path', dest = 'level_path', type = str, default = os.path.normpath('./data/generated_level/'), help = 'Path of generated levels')
    parser.add_argument('--game_folder_path', dest = 'game_folder_path', type = str, default = os.path.normpath('./science_birds/{os}'), help = 'Set a different path to the game')
    parser.add_argument('--ai_path', dest = 'ai_path', type = str, default = os.path.normpath('./ai/Naive-Agent-standalone-Streamlined.jar'), help = 'Set a different path to the ai')
    parser.add_argument('--rescue_level', dest = 'rescue_level', type = bool, default = True, help = 'If a delete shall copy levels in the game folder.')
    parser.add_argument('--evaluate', dest = 'evaluate', type = bool, default = False, help = 'If the generated level should be evaluated')

    return parser
