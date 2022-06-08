import pickle
from pathlib import Path

from loguru import logger
from tqdm import tqdm

from level.LevelReader import LevelReader
from level.LevelVisualizer import LevelVisualizer
from level.Level import Level
from game_management.GameConnection import GameConnection
import os
from util.Config import Config
from game_management.GameManager import GameManager
from util import ProgramArguments

continue_at_level = 32


if __name__ == '__main__':

    parser = ProgramArguments.get_program_arguments()
    config = parser.parse_args()
    config.game_folder_path = os.path.normpath('../science_birds/{os}')
    config.ai_path = os.path.normpath('../ai/Naive-Agent-standalone-Streamlined.jar')

    config = Config(config)
    game_connection = GameConnection(conf = config)
    game_manager = GameManager(conf = config, game_connection = game_connection)
    level_reader = LevelReader()

    try:
        game_manager.start_game(is_running = False)

        data_dict = dict()
        if continue_at_level > 0:
            with open('pickles/level_data_with_screenshot.pickle', 'rb') as f:
                data_dict = pickle.load(f)

        levels = sorted(Path("train/generated/").glob('*.xml'))
        for level_idx, original_data_level in tqdm(enumerate(levels), total = len(levels)):
            if level_idx <= continue_at_level:
                continue

            parsed_level = level_reader.parse_level(
                str(original_data_level), use_blocks = True, use_pigs = True, use_platform = True)
            parsed_level.filter_slingshot_platform()

            parsed_level.normalize()
            parsed_level.create_polygons()
            level_structures = parsed_level.separate_structures()
            level_visualizer = LevelVisualizer()

            level_counter = 0
            for idx, structure in enumerate(level_structures):
                meta_data = Level.calc_structure_meta_data(structure)

                if meta_data.pig_amount == 0:
                    continue

                struct_doc = level_reader.create_level_from_structure(
                    structure = structure,
                    level = parsed_level,
                    move_to_ground = True
                )
                new_level_path = f'../data/train/structures/level-04.xml'
                level_reader.write_xml_file(struct_doc, new_level_path)
                game_manager.change_level(path = new_level_path, delete_level = True)

                new_level = level_reader.parse_level(new_level_path, use_platform = True)
                new_level.normalize()
                new_level.create_polygons()
                new_level.filter_slingshot_platform()
                new_level.separate_structures()

                level_screenshot = game_connection.create_level_img(structure = True)
                game_connection.startAi(start_level = 4, end_level = 4, print_ai_log = True)
                ret_pictures = new_level.create_img(per_structure = True, dot_version = True)
                all_levels_played = game_connection.wait_till_all_level_played()
                logger.debug(f'All levels Played: {all_levels_played}')
                game_connection.stopAI()
                if not all_levels_played:
                    continue

                new_level_data = game_connection.get_data()
                logger.debug(new_level_data)
                data_dict[f'{str(original_data_level).strip(".xml")}_{level_counter}'] = dict(
                    meta_data = meta_data,
                    game_data = new_level_data,
                    level_screenshot = level_screenshot,
                    img_data = ret_pictures
                )
                level_counter += 1

            with open('pickles/level_data_with_screenshot.pickle', 'wb') as handle:
                pickle.dump(data_dict, handle, protocol = pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print(e)

    game_manager.stop_game()
