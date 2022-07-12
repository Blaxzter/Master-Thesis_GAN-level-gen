import json
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
    """
    Creates structure list of each block type
    """
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
    """
    Returns the img of the debug level either from a pickle or newly created
    """
    pickle_data = config.get_pickle_file("block_data")
    if os.path.isfile(pickle_data):
        with open(pickle_data, 'rb') as f:
            data = pickle.load(f)
        return data
    else:
        level_img_encoder = LevelImgEncoder()
        elements, sizes = create_element_for_each_block()
        level_img = level_img_encoder.create_calculated_img(elements)
        with open(pickle_data, 'wb') as handle:
            pickle.dump(level_img[0], handle, protocol = pickle.HIGHEST_PROTOCOL)
        return level_img[0]


def test_encoding_data(test_dot = True):
    """
    Creates the testing level with more and more space between the blocks.
    Searches for the rectangles in the img representation and compares
    the width difference between offsets.
    """
    level_img_encoder = LevelImgEncoder()
    level_img_decoder = LevelImgDecoder()

    offset_data = dict()

    subplot_amount = 15

    fig, axs = plt.subplots(subplot_amount, 1, dpi = 600, figsize = (8, 15))

    for x_offset, ax in zip(np.linspace(0, 0.15, num = subplot_amount), axs.flatten()):
        elements, sizes = create_element_for_each_block(x_offset = x_offset)

        # Create the images
        if test_dot:
            level_rep = level_img_encoder.create_dot_img(elements)
        else:
            level_rep = level_img_encoder.create_calculated_img(elements)

        ax.imshow(level_rep)
        ax.axis('off')

        recs = level_img_decoder.get_rectangles(level_rep)
        recs = sorted(recs, key = lambda x: x['min_x'])

        for block_idx, block in enumerate(sizes):
            for key, value in block.items():
                recs[block_idx][f'block_{key}'] = value

        offset_data[x_offset] = recs

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
            average_height_difference = np.average(
                list(map(lambda pair: pair[0]['height'] - pair[1]['height'], zipped)))

            max_width_difference = round(max_width_difference * 100) / 100
            max_height_difference = round(max_height_difference * 100) / 100
            average_width_difference = round(average_width_difference * 100) / 100
            average_height_difference = round(average_height_difference * 100) / 100

            c_list.append(f"({max_width_difference}, {max_height_difference}) \n"
                          f"({average_width_difference}, {average_height_difference})")
            # c_list.append(f"{list(map(lambda pair: pair[0]['width'] - pair[1]['width'], zipped))} \n"
            #               f"{list(map(lambda pair: pair[0]['height'] - pair[1]['height'], zipped))}")

        data_list.append(c_list)

    print(tabulate(data_list, headers = [' '] + list(offset_data.keys())))


def visualize_encoding_data(viz_recs = True):
    create_screen_shot = False

    level_img_encoder = LevelImgEncoder()
    level_img_decoder = LevelImgDecoder()
    level_visualizer = LevelVisualizer()
    elements, sizes = create_element_for_each_block()

    # Create the images
    dot_img = level_img_encoder.create_dot_img(elements)
    calc_img = level_img_encoder.create_calculated_img(elements)
    calc_img_no_size_check = level_img_encoder.create_calculated_img_no_size_check(elements)

    fig = plt.figure(constrained_layout = True, dpi = 300)
    fig.suptitle('Encoding Data Level')
    # create 3x1 subfigs
    subfigs = fig.subfigures(nrows = 4 + (1 if create_screen_shot else 0), ncols = 1)

    ax = subfigs[0].subplots(nrows = 1, ncols = 1)
    if create_screen_shot:
        axs = subfigs.subplots(nrows = 1, ncols = 2)
        game_manager = GameManager(conf = config)
        game_manager.start_game()

        axs[1].set_title('Screenshot')
        game_manager.switch_to_level_elements(elements)
        img = game_manager.get_img()
        axs[1].imshow(img)
        ax = axs[0]

    level_visualizer.create_img_of_structure(elements, scaled = False, ax = ax)
    ax.set_title('No Size Reduction')

    iter_data = zip(subfigs[1:], [
        {'img': dot_img, 'name': 'Dot Encoding'},
        {'img': calc_img, 'name': 'Calculated Encoding'},
        {'img': calc_img_no_size_check, 'name': 'Calculated Encoding No Size Checks'},
    ])

    for subfig, data in iter_data:
        axs = subfig.subplots(nrows = 1, ncols = 2 if viz_recs else 1).flatten()

        if viz_recs:
            subfig.suptitle(data['name'])
        else:
            axs[0].set_title(data['name'])

        current_img = np.pad(data['img'], 2)
        axs[0].imshow(current_img)
        if viz_recs:
            level_img_decoder.visualize_rectangle(level_img = current_img, material_id = 1, ax = axs[1])

    plt.subplots_adjust(hspace = 0.4)
    plt.show()

    if create_screen_shot:
        game_manager.stop_game()


def create_decoding_data():
    level_img_encoder = LevelImgEncoder()
    level_img_decoder = LevelImgDecoder()

    data_dict = dict()

    elements, sizes = create_element_for_each_block()
    level_rep, cord_list = level_img_encoder.create_calculated_img(elements)

    recs = level_img_decoder.get_rectangles(np.pad(level_rep, 0))
    recs = sorted(recs, key = lambda x: x['min_x'])
    for block_idx, block in enumerate(sizes):
        for key, value in block.items():
            recs[block_idx][f'block_{key}'] = value

    data_dict['resolution'] = Constants.resolution
    for rec_idx, rec_data in enumerate(recs):
        data_dict[rec_idx] = dict(
            name = rec_data['block_name'],
            rotated = rec_data['block_rotated'],
            area = rec_data['area'],
            poly_area = rec_data['contour_area'],
            dim = (rec_data['height'], rec_data['width']),
            orig_dim = (rec_data['block_orig_width'], rec_data['block_orig_height'])
        )

    pickle_data = config.get_encoding_data(f"encoding_res_{Constants.resolution}")
    if type(pickle_data) != str:
        ic(pickle_data)
    else:
        with open(pickle_data, 'w') as f:
            f.write(json.dumps(data_dict, indent=4))



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
    # visualize_encoding_data()
    # test_encoding_data(test_dot = False)
    create_decoding_data()
