import os
import pickle
import sys

import matplotlib.pyplot as plt
import numpy as np
from icecream import ic
from tabulate import tabulate

from converter.to_img_converter.LevelImgDecoder import LevelImgDecoder
from converter.to_img_converter.LevelImgEncoder import LevelImgEncoder
from game_management.GameManager import GameManager
from level import Constants
from level.LevelElement import LevelElement
from level.LevelVisualizer import LevelVisualizer
from util.Config import Config

config = Config.get_instance()


def create_element_for_each_block(x_offset = 0, y_offset = 0):
    elements = []
    start_x = 0
    sizes = Constants.get_sizes(print_data = False)
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
            y = size[1] / 2 + y_offset,
            rotation = 90 if block['rotated'] else 0
        )
        element = LevelElement(id = idx, **block_attribute)
        elements.append(element)

        start_x += size[0] / 2 + Constants.resolution * 2 + x_offset * idx
        element.shape_polygon = element.create_geometry()

    return elements, sizes


def get_debug_level():
    pickle_data = config.get_pickle_file("block_data")
    if os.path.isfile(pickle_data):
        with open(pickle_data, 'rb') as f:
            data = pickle.load(f)
        return data
    else:
        level_img_encoder = LevelImgEncoder()
        elements, sizes = create_element_for_each_block()
        level_img = level_img_encoder.create_img_of_structures([elements], dot_version = True)
        with open(pickle_data, 'wb') as handle:
            pickle.dump(level_img[0], handle, protocol = pickle.HIGHEST_PROTOCOL)
        return level_img[0]


def test_encoding_data(test_dot = True):
    level_img_encoder = LevelImgEncoder()
    level_img_decoder = LevelImgDecoder()

    offset_data = dict()

    fig, axs = plt.subplots(2, 1, dpi = 600, figsize = (8, 15))

    level_idx = 0
    for x_offset in np.linspace(0, 0.15, num = 2):
        elements, sizes = create_element_for_each_block(x_offset = x_offset)

        # Create the images
        if test_dot:
            level_rep = level_img_encoder.create_dot_img(elements)
        else:
            level_rep = level_img_encoder.create_calculated_img(elements)

        axs[level_idx].imshow(level_rep)
        axs[level_idx].axis('off')

        recs = level_img_decoder.get_rectangles(level_rep)
        recs = sorted(recs, key = lambda x: x['min_x'])

        for block_idx, block in enumerate(sizes):
            for key, value in block.items():
                recs[block_idx][f'block_{key}'] = value

        offset_data[x_offset] = recs
        level_idx += 1

    plt.tight_layout()
    plt.show()

    data_list = []
    for key_1, rect_list_1 in offset_data.items():
        c_list = [key_1]
        for key_2, rect_list_2 in offset_data.items():
            zipped = list(zip(rect_list_1, rect_list_2))
            max_width_difference = np.max(list(map(lambda pair: pair[0]['width'] - pair[1]['width'], zipped)))
            max_height_difference = np.max(list(map(lambda pair: pair[0]['height'] - pair[1]['height'], zipped)))
            average_width_difference = np.average(list(map(lambda pair: pair[0]['width'] - pair[1]['width'], zipped)))
            average_height_difference = np.average(list(map(lambda pair: pair[0]['height'] - pair[1]['height'], zipped)))

            max_width_difference = round(max_width_difference * 100) / 100
            max_height_difference = round(max_height_difference * 100) / 100
            average_width_difference = round(average_width_difference * 100) / 100
            average_height_difference = round(average_height_difference * 100) / 100

            # c_list.append(f"({max_width_difference}, {max_height_difference}) \n"
            #               f"({average_width_difference}, {average_height_difference})")
            c_list.append(f"{list(map(lambda pair: pair[0]['width'] - pair[1]['width'], zipped))} \n"
                          f"{list(map(lambda pair: pair[0]['height'] - pair[1]['height'], zipped))}")

        data_list.append(c_list)

    print(tabulate(data_list, headers = [' '] + list(offset_data.keys())))


def visualize_encoding_data():
    create_screen_shot = False

    if create_screen_shot:
        game_manager = GameManager(conf = config)
        game_manager.start_game()

    level_img_encoder = LevelImgEncoder()
    level_visualizer = LevelVisualizer()
    elements, sizes = create_element_for_each_block()

    fig, ax = plt.subplots(3 + (1 if create_screen_shot else 0), 1, dpi = 300)

    # Create the images
    level_visualizer.create_img_of_structure(elements, scaled = False, ax = ax[0])
    dot_img = level_img_encoder.create_dot_img(elements)
    calc_img = level_img_encoder.create_calculated_img(elements)

    ax[0].set_title('True Img')

    ax[1].imshow(np.pad(dot_img, 2))
    ax[1].set_title('Dot Encoding')
    ax[1].axis('off')

    ax[2].imshow(np.pad(calc_img, 2))
    ax[2].set_title('Calculated Encoding')
    ax[2].axis('off')

    if create_screen_shot:
        game_manager.switch_to_level_elements(elements)
        img = game_manager.get_img()
        ax[3].imshow(img)

    # level_img_decoder = LevelImgDecoder()
    # recs = level_img_decoder.get_rectangles(calc_img)
    # recs = sorted(recs, key = lambda x: x['min_x'])
    #
    # for block_idx, block in enumerate(sizes):
    #     for key, value in block.items():
    #         recs[block_idx][f'block_{key}'] = value

    plt.show()

    # print_rect_data(recs)

    if create_screen_shot:
        game_manager.stop_game()


def print_rect_data(recs):
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

    ic(recs)


if __name__ == '__main__':
    visualize_encoding_data()
    # test_encoding_data(test_dot = False)
