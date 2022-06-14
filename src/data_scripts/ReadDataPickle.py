import json
import pickle
from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt

from level.Constants import LevelMetaData
from level.LevelReader import LevelReader
from util.Config import Config


def load_data(data_name):
    with open(data_name, 'rb') as f:
        data = pickle.load(f)
    return data


def strip_screenshot_from_data(data: dict, out_file):
    print(data.keys())
    for key in data.keys():
        level_data = data[key]

        del level_data['level_screenshot']

    with open(out_file, 'wb') as handle:
        pickle.dump(data, handle, protocol = pickle.HIGHEST_PROTOCOL)


def parse_data(data: dict, out_file: str):
    print(len(data.keys()))
    for key in data.keys():
        level_data = data[key]

        level_idx = np.argmax(list(map(lambda x: x.shape[0] * x.shape[1], level_data['img_data'])))
        level_data['img_data'] = level_data['img_data'][level_idx]

        if 'game_data' in level_data:
            level_data['game_data'] = json.loads(level_data['game_data'][1]['data'])[0]

    with open(out_file, 'wb') as handle:
        pickle.dump(data, handle, protocol = pickle.HIGHEST_PROTOCOL)


def visualize_data(data, start_index = 0, end_index = -1, height_filter = -1, width_filter = -1):
    print(data.keys())
    for key in list(data.keys())[start_index:end_index if end_index != -1 else len(data)]:
        level_data = data[key]
        level_data_shape = level_data['img_data'][0].shape

        if height_filter != -1 and level_data_shape[0] < height_filter:
            continue

        if width_filter != -1 and level_data_shape[1] < width_filter:
            continue

        print(level_data['meta_data'])
        print(level_data['game_data'])

        plt.imshow(level_data['level_screenshot'])
        plt.show()

        print(level_data['img_data'][0].shape)
        plt.imshow(level_data['img_data'][0])
        plt.show()


def get_max_shape_size(data: dict):
    max_height = -10000
    max_width = -10000

    max_value = -10000
    min_value = 10000

    for key in data.keys():
        level_data = data[key]

        img_data = level_data['img_data']
        level_img_shape = img_data.shape

        max_height = max(max_height, level_img_shape[0])
        max_width = max(max_width, level_img_shape[1])

        max_value = max(max_value, img_data.max())
        min_value = min(min_value, img_data.min())

    print(f'Height {max_height} Width: {max_width}')
    print(f'MaxVal {max_value} MinVal: {min_value}')  #

    return max_height, max_width, max_value, min_value


def visualize_shape(data: dict, max_height = 86, max_width = 212):
    label_height = range(0, max_height + 1)
    label_width = range(0, max_width + 1)

    height_count_dict = {i: 0 for i in label_height}
    width_count_dict = {i: 0 for i in label_width}

    for key in data.keys():
        level_data = data[key]

        level_img_shape = level_data['img_data'].shape
        height_count_dict[level_img_shape[0]] += 1
        width_count_dict[level_img_shape[1]] += 1

    fig, axs = plt.subplots(1, 2, dpi = 300, figsize = (9, 4))
    axs[0].bar(label_height, list(height_count_dict.values()))
    axs[0].set_title('Height distribution')
    axs[0].set_ylabel('Amount of levels')
    axs[0].set_xlabel('Height of Levels')

    axs[1].bar(label_width, list(width_count_dict.values()))
    axs[1].set_title('Width distribution')
    axs[1].set_ylabel('Amount of levels')
    axs[1].set_xlabel('Width of Levels')

    fig.suptitle('Height distribution', fontsize = 16)
    plt.show()


def view_files_with_prop(data, amount = -1, min_width = -1, max_width = -1, min_height = -1, max_height = -1):
    counter = 0
    for key in list(data.keys()):

        level_data = data[key]
        level_data_shape = level_data['img_data'].shape

        if min_width != -1 and not level_data_shape[0] >= min_width or \
                max_width != -1 and not level_data_shape[0] < max_width or \
                min_height != -1 and not level_data_shape[1] >= min_height or \
                max_height != -1 and not level_data_shape[1] < max_height:
            continue

        plt.imshow(level_data['img_data'])
        plt.show()

        counter += 1
        if amount != -1 and counter > amount:
            break


def filter_level(data, out_file):
    out_dict = dict()
    for key in list(data.keys()):
        level_data = data[key]
        meta_data: LevelMetaData = level_data['meta_data']
        if meta_data.block_amount <= 0:
            continue

        level_data_shape = level_data['img_data'].shape

        out_dict[key] = level_data

    with open(out_file, 'wb') as handle:
        pickle.dump(out_dict, handle, protocol = pickle.HIGHEST_PROTOCOL)



if __name__ == '__main__':
    config = Config.get_instance()
    file_name = config.get_pickle_file(file_name = 'single_structure')

    # data_dict = load_data("../resources/data/pickles/level_data_with_screenshot")
    # strip_screenshot_from_data(data_dict)

    data_dict = load_data(file_name)
    parse_data(data_dict, config.get_pickle_file("single_structure_out"))

    file_name = config.get_pickle_file(file_name = 'single_structure_out')
    data_dict = load_data(file_name)
    level_dest = config.get_data_train_path(folder = 'generated/single_structure/')
    out_file_filtered = config.get_pickle_file("single_structure_filtered")
    filter_level(data_dict, out_file = out_file_filtered)

    max_height, max_width, max_value, min_value = get_max_shape_size(data_dict)

    data_dict = load_data(out_file_filtered)
    visualize_shape(data_dict, max_height, max_width)

    data_dict = load_data(out_file_filtered)
    view_files_with_prop(data_dict, amount = 5, min_width = 0, max_width = 15, min_height = 0, max_height = -1)

    # data_dict = load_data("../resources/data/pickles/single_structure")d
    # visualize_data(data_dict, start_index = 0, end_index = -1, width_filter = 150)

    # data_dict = load_data("../resources/data/pickles/level_data_with_screenshot")
    # strip_screenshot_from_data(data_dict)
