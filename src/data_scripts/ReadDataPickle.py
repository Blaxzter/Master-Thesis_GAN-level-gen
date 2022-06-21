import json
import os
import pickle
from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt

from level.Constants import StructureMetaData
from level.LevelReader import LevelReader
from util.Config import Config


def load_data(data_name):
    with open(data_name, 'rb') as f:
        data = pickle.load(f)
    return data


def get_level_from_data(data_key, data_example):
    level_path = config.get_instance().get_data_train_path('generated/single_structure')
    level_names = list(Path(level_path).glob("*"))
    parsed_level_names = list(map(lambda x: x.name[:-4], level_names))
    key_name = data_key.split(os.sep)[-1][:-2]

    position = parsed_level_names.index(key_name)
    if position == -1:
        return None

    level_reader = LevelReader()
    level = level_reader.parse_level(path = str(level_names[position]), use_platform = True)

    return level



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

        if 'meta_data' in level_data:
            print(level_data['meta_data'])

        if 'game_data' in level_data:
            print(level_data['game_data'])

        if 'level_screenshot' in level_data:
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
    level_list = []
    data_idx = dict()
    for key in list(data.keys()):

        level_data = data[key]
        level_data_shape = level_data['img_data'].shape

        level = get_level_from_data(key, level_data)

        if min_width != -1 and not level_data_shape[1] >= min_width or \
                max_width != -1 and not level_data_shape[1] <= max_width or \
                min_height != -1 and not level_data_shape[0] >= min_height or \
                max_height != -1 and not level_data_shape[0] <= max_height:
            continue

        if level in level_list:
            pos = level_list.index(level)
            ref_level_data = data_idx[pos]

            fig, axs = plt.subplots(1, 2)
            axs[0].imshow(level_data['img_data'])
            axs[0].set_title("Current Level")

            axs[1].imshow(ref_level_data['img_data'])
            axs[1].set_title("Ref Level")

            plt.title("Found duplicate")
            plt.show()
        else:
            plt.imshow(level_data['img_data'])
            plt.title(level_data_shape)
            plt.show()

        level_list.append(level)
        data_idx[len(level_list) - 1] = level_data

        counter += 1
        if amount != -1 and counter > amount:
            break

    print(f'Showed {counter} files')


def filter_level(data, out_file):

    meta_data_list = []
    temp_data = []

    out_dict = dict()
    for key in list(data.keys()):
        level_data = data[key]
        meta_data: StructureMetaData = level_data['meta_data']
        if meta_data.block_amount <= 0:
            continue

        for idx, comp_meta_data in enumerate(meta_data_list):
            if comp_meta_data == meta_data:
                comp_level = temp_data[idx]

                fig, axs = plt.subplots(1, 2)
                fig.suptitle("Found same metadata")

                level_data_shape = comp_level.shape
                axs[0].set_title(str(level_data_shape))
                axs[0].imshow(comp_level)

                level_data_shape = level_data['img_data'].shape
                axs[1].set_title(str(level_data_shape))
                axs[1].imshow(level_data['img_data'])
                plt.show()

                equal = comp_meta_data == meta_data
                continue

        temp_data.append(level_data['img_data'])
        meta_data_list.append(meta_data)
        out_dict[key] = level_data

    with open(out_file, 'wb') as handle:
        pickle.dump(out_dict, handle, protocol = pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    config = Config.get_instance()
    file_name = config.get_pickle_file(file_name = 'single_structure_full')

    # data_dict = load_data("../resources/data/pickles/level_data_with_screenshot")
    # strip_screenshot_from_data(data_dict)

    data_dict = load_data(file_name)
    parse_data(data_dict, config.get_pickle_file("single_structure_full_out"))
    #
    file_name = config.get_pickle_file(file_name = 'single_structure_full_out')
    data_dict = load_data(file_name)

    out_file_filtered = config.get_pickle_file("single_structure_full_filtered")
    filter_level(data_dict, out_file = out_file_filtered)

    file_filtered = config.get_pickle_file("single_structure_full_filtered")
    data_dict = load_data(file_filtered)
    max_height, max_width, max_value, min_value = get_max_shape_size(data_dict)
    #
    data_dict = load_data(file_filtered)
    visualize_shape(data_dict, max_height, max_width)
    #
    data_dict = load_data(file_filtered)
    view_files_with_prop(data_dict, amount = -1, min_width = 0, max_width = 30, min_height = 0, max_height = 13)

    # data_dict = load_data(file_name)
    # visualize_data(data_dict, start_index = 0, end_index = 10, width_filter = -1)

    # data_dict = load_data("../resources/data/pickles/level_data_with_screenshot")
    # strip_screenshot_from_data(data_dict)
