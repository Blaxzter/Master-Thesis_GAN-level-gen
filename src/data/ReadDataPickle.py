import pickle

from matplotlib import pyplot as plt


def strip_screenshot_from_data():
    with open('level_data_with_screenshot.pickle', 'rb') as f:
        data = pickle.load(f)

    print(data.keys())
    for key in data.keys():
        level_data = data[key]

        del level_data['level_screenshot']

    with open('level_data.pickle', 'wb') as handle:
            pickle.dump(data, handle, protocol = pickle.HIGHEST_PROTOCOL)


def visualize_data(start_index = 0, end_index = -1):
    with open('level_data_with_screenshot.pickle', 'rb') as f:
        data = pickle.load(f)

    print(data.keys())
    for key in data.keys()[start_index:end_index]:
        level_data = data[key]
        print(level_data['meta_data'])
        print(level_data['game_data'])

        plt.imshow(level_data['level_screenshot'])
        plt.show()

        plt.imshow(level_data['img_data'][0])
        plt.show()



if __name__ == '__main__':
    # strip_screenshot_from_data()

    with open('level_data.pickle', 'rb') as f:
        data = pickle.load(f)

        print(len(data))
