import pickle
from multiprocessing import Manager, Pool
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


logger.disable('level.Level')

continue_at_level = 300

config = Config.get_instance()
game_connection = GameConnection(conf = config)
# game_manager = GameManager(conf = config, game_connection = game_connection)
level_reader = LevelReader()

orig_level_folder = config.get_data_train_path(folder = 'generated/single_structure')

use_screen_shot = False
use_ai = False

data_file = f'{config.get_pickle_folder()}/single_structure_test.pickle'


def create_level_data(original_data_level, p_dict, lock):

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

        new_level_path = config.get_data_train_path("structures") + "level-04.xml"
        level_reader.write_xml_file(struct_doc, new_level_path)
        # game_manager.change_level(path = new_level_path, delete_level = True)

        new_level = level_reader.parse_level(new_level_path, use_platform = True)
        new_level.normalize()
        new_level.create_polygons()
        new_level.filter_slingshot_platform()
        new_level.separate_structures()

        if use_screen_shot:
            level_screenshot = game_connection.create_level_img(structure = True)
        if use_ai:
            game_connection.startAi(start_level = 4, end_level = 4, print_ai_log = True)

        ret_pictures = new_level.create_img(per_structure = True, dot_version = True)
        if use_ai:
            all_levels_played = game_connection.wait_till_all_level_played()
            logger.debug(f'All levels Played: {all_levels_played}')
            game_connection.stopAI()
            if not all_levels_played:
                continue

        # new_level_data = game_connection.get_data()
        #logger.debug(new_level_data)
        dict_idx = f'{str(original_data_level).strip(".xml")}_{level_counter}'
        p_dict[dict_idx] = dict(
            meta_data = meta_data,
        #    game_data = new_level_data,
            img_data = ret_pictures
        )
        if use_screen_shot:
            p_dict[dict_idx]['level_screenshot'] = level_screenshot,

        level_counter += 1

    lock.acquire()
    print(os.getpid())
    with open(data_file, 'wb') as handle:
        pickle.dump(dict(p_dict), handle, protocol = pickle.HIGHEST_PROTOCOL)
    lock.release()


if __name__ == '__main__':

    # game_manager.start_game(is_running = False)

    process_manager = Manager()
    lock = process_manager.Lock()
    p_dict = process_manager.dict()
    pool = Pool(None)

    data_dict = dict()
    if continue_at_level > 0:
        with open(data_file, 'rb') as f:
            data_dict = pickle.load(f)
            for key, value in data_dict.items():
                p_dict[key] = value

    levels = sorted(Path(orig_level_folder).glob('*.xml'))
    results = []
    p_bar = tqdm(enumerate(levels), total = len(levels[300:]))


    def update(*a):
        p_bar.update()

    for level_idx, original_data_level in enumerate(levels[300:]):
        if level_idx < continue_at_level:
            continue

        res = pool.apply_async(func = create_level_data, args = (original_data_level, p_dict, lock), callback=update)
        results.append(res)
        # create_level_data(original_data_level, p_dict, lock)

    [result.wait() for result in results]

    # game_manager.stop_game()
