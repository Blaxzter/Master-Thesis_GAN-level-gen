import itertools
import os
import pickle
import time

from matplotlib import pyplot as plt

from data_scripts import CreateEncodingData
from game_management.GameManager import GameManager
from level.Level import Level
from level.LevelVisualizer import LevelVisualizer
from level_decoder.LevelImgDecoder import LevelImgDecoder
from util.Config import Config


def get_debug_level():
    pickle_data = config.get_pickle_file("block_data")
    if os.path.isfile(pickle_data):
        with open(pickle_data, 'rb') as f:
            data = pickle.load(f)
        return data
    else:
        elements, sizes = CreateEncodingData.create_element_for_each_block()
        level_img = Level.create_structure_img([elements], dot_version = True)
        with open(pickle_data, 'wb') as handle:
            pickle.dump(level_img[0], handle, protocol = pickle.HIGHEST_PROTOCOL)
        return level_img[0]


if __name__ == '__main__':
    config = Config.get_instance()
    file_filtered = config.get_pickle_file("single_structure_full_filtered")
    with open(file_filtered, 'rb') as f:
        data = pickle.load(f)

    level_idx = 1
    level_data = next(itertools.islice(iter(data.values()), level_idx, level_idx + 1))
    level_img = level_data['img_data']
    # plt.imshow(level_img)
    # plt.show()

    # level_img = get_debug_level()

    level_img_decoder = LevelImgDecoder()
    level_img_decoder.visualize_contours(level_img)
    # level_img_decoder.visualize_rectangles(level_img, material_id = 2)
    # level_elements = level_img_decoder.decode_level(level_img)
    # level_viz = LevelVisualizer()
    # level_viz.create_img_of_structure(level_elements)

    # level_img_decoder.get_pig_position(level_img)

    # level_elements = level_img_decoder.visualize_one_decoding(level_img, contour_color = 1)
    # level_elements = level_img_decoder.visualize_one_decoding(level_img, contour_color = 2)
    # level_elements = level_img_decoder.visualize_one_decoding(level_img, contour_color = 3)

    # game_manager = GameManager(conf = config)
    # game_manager.start_game()
    # game_manager.switch_to_level_elements(level_elements)
    # img = game_manager.create_img_of_level()
    # plt.imshow(img)
    # plt.show()
    #
    # time.sleep(20)
    # game_manager.stop_game()
