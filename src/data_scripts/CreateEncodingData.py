import sys
import time

from icecream import ic

import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate

from game_management.GameConnection import GameConnection
from game_management.GameManager import GameManager
from level import Constants
from level.Level import Level
from level.LevelElement import LevelElement
from level.LevelReader import LevelReader
from level.LevelVisualizer import LevelVisualizer
from level_decoder.LevelImgDecoder import LevelImgDecoder
from util.Config import Config

if __name__ == '__main__':

    config = Config.get_instance()
    # game_connection = GameConnection(conf = config)
    # game_manager = GameManager(conf = config, game_connection = game_connection)
    # game_manager.start_game()
    level_visualizer = LevelVisualizer()
    elements = []

    start_x = 0
    sizes = Constants.get_sizes()
    for idx, block in enumerate(sizes):
        index = list(Constants.block_names.values()).index(block['name']) + 1
        if block['rotated']:
            index += 1
        size = Constants.block_sizes[str(index)]

        start_x += size[0] / 2
        block_attribute = dict(
            type = block['name'],
            material = "wood",
            x = start_x,
            y = size[1] / 2 + 0.2,
            rotation = 90 if block['rotated'] else 0
        )
        element = LevelElement(id = idx, **block_attribute)
        elements.append(element)

        start_x += size[0] / 2 + Constants.resolution * 2
        element.shape_polygon = element.create_geometry()

    fig, ax = plt.subplots(4, 1, dpi = 300)

    element_img = level_visualizer.create_img_of_structure(elements, ax = ax[0])
    level_rep = Level.create_structure_img([elements], dot_version = True)
    level_rep2 = Level.create_structure_img([elements], dot_version = False)
    ax[1].imshow(np.pad(level_rep[0], 2))
    ax[2].imshow(np.pad(level_rep2[0], 2))

    # level_reader = LevelReader()
    # level = level_reader.create_level_from_structure(elements, red_birds = True)
    # level_folder = config.get_data_train_path(folder = 'data_level')
    # level_path = f'{level_folder}/level-04.xml'
    # level_reader.write_xml_file(level, level_path)
    # game_manager.change_level(path = str(level_path))
    # img = game_connection.create_level_img(structure = True)
    # ax[3].imshow(img)

    time.sleep(1)


    level_img_decoder = LevelImgDecoder()
    recs = level_img_decoder.visualize_rectangles(np.pad(level_rep[0], 3), material_id = 1, ax = ax[3])

    recs = sorted(recs, key = lambda x: x['min_x'])
    for block_idx, block in enumerate(sizes):
        for key, value in block.items():
            recs[block_idx][f'block_{key}'] = value

    np.set_printoptions(threshold = sys.maxsize, linewidth = sys.maxsize)
    print(tabulate([[
        c_dict['block_name'],
        c_dict['area'],
        c_dict['contour_area'],
        c_dict['area'] - c_dict['contour_area'],
        c_dict['block_area'],
        c_dict['height'],
        c_dict['width'],
        c_dict['block_width'],
        c_dict['block_height'],
        c_dict['block_rounded_width'],
        c_dict['block_rounded_height'],
        c_dict['block_rotated']
        ] for c_dict in recs],
        headers = [
            'block_name',
            'area',
            'contour_area',
            'area',
            'block_area',
            'height',
            'width',
            'block_width',
            'block_height',
            'block_rounded_width',
            'block_rounded_height',
            'block_rotated'
        ])
    )

    plt.show()

    # game_manager.stop_game()
