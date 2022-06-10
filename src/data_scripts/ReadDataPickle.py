import json
import pickle
from matplotlib import pyplot as plt

from util.Config import Config


def load_data(data_name):
    with open(f'{data_name}.pickle', 'rb') as f:
        data = pickle.load(f)
    return data


def strip_screenshot_from_data(data: dict):
    print(data.keys())
    for key in data.keys():
        level_data = data[key]

        del level_data['level_screenshot']

    with open('pickles/level_data.pickle', 'wb') as handle:
            pickle.dump(data, handle, protocol = pickle.HIGHEST_PROTOCOL)


def parse_data(data: dict):

    print(len(data.keys()))
    for key in data.keys():
        level_data = data[key]

        level_data['img_data'] = level_data['img_data'][0]
        level_data['game_data'] = json.loads(level_data['game_data'][1]['data'])[0]

    with open('pickles/level_data.pickle', 'wb') as handle:
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
    print(f'MaxVal {max_value} MinVal: {min_value}')


def visualize_shape(data: dict):

    max_height = 86
    max_width = 212

    label_height = range(0, max_height + 1)
    label_width = range(0, max_width + 1)

    height_count_dict = {i: 0 for i in label_height}
    width_count_dict = {i: 0 for i in label_width}

    for key in data.keys():
        level_data = data[key]

        level_img_shape = level_data['img_data'].shape
        height_count_dict[level_img_shape[0]] += 1
        width_count_dict[level_img_shape[1]] += 1

    fig, axs = plt.subplots(1, 2, dpi = 300, figsize=(9, 4))
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

if __name__ == '__main__':

    config = Config.get_instance()

    # data_dict = load_data("../resources/data/pickles/level_data")
    # get_max_shape_size(data_dict)

    data_dict = load_data("../resources/data/pickles/level_data_with_screenshot")
    visualize_data(data_dict, start_index = 0, end_index = -1, width_filter = 150)
    data_dict = load_data("../resources/data/pickles/level_data")
    visualize_shape(data_dict)

    # data_dict = load_data("../resources/data/pickles/level_data_with_screenshot")
    # strip_screenshot_from_data(data_dict)
    #
    # data_dict = load_data("../resources/data/pickles/level_data")
    # parse_data(data_dict)
