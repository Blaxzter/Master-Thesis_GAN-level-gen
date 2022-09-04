import pickle

import cv2
import matplotlib.pyplot as plt
import numpy as np
from icecream import ic

from converter.to_img_converter import DecoderUtils
from level import Constants
from util.Config import Config

from scipy import stats

config = Config.get_instance()

block_data = config.get_encoding_data(f"encoding_res_{Constants.resolution}")
if type(block_data) is not str:
    resolution = block_data['resolution']
    del block_data['resolution']

def load_test_outputs_of_model(model_name):
    loaded_model = model_name.replace(' ', '_').lower()
    store_imgs_pickle_file = config.get_gan_img_store(loaded_model)

    with open(store_imgs_pickle_file, 'rb') as f:
        loaded_outputs = pickle.load(f)

    return loaded_outputs


def plt_img(img, title, ax = None):
    if ax is None:
        plt.imshow(img)
        plt.title(title)
        plt.colorbar()
        plt.show()
    else:
        ax.imshow(img)
        ax.set_title(title)

if __name__ == '__main__':
    test_outputs = load_test_outputs_of_model('multilayer_with_air.pickle')

    test_image = list(test_outputs.keys())[0]
    ic(test_image)
    test_output = test_outputs[test_image]['output']
    test_output = (test_output[0] + 1) / 2
    for layer_idx in range(1, test_output.shape[-1]):

        layer = test_output[:, :, layer_idx]
        plt_img(layer, 'Original')
        frequency, bins = np.histogram(layer, bins = 100)

        # plt.hist(layer, bins = np.linspace(0, 1, 100), histtype='step', log = True)
        # plt.show()

        center = (bins[-1] - bins[0]) / 2
        highest_lowest_value = bins[0]
        for i in range(20):
            highest_count = frequency.argmax()
            highest_count_value = bins[highest_count]
            frequency[highest_count] = 0
            if highest_count_value < center:
                print(highest_lowest_value, highest_count_value)
                if highest_lowest_value < highest_count_value:
                    highest_lowest_value = highest_count_value

        print(highest_lowest_value, center, bins[-1])
        layer[layer <= highest_lowest_value] = 0

        # plt.hist(layer, bins = np.linspace(0, 1, 100), histtype='step', log = True)
        # plt.show()

        trimmed_img, trim_data = DecoderUtils.trim_img(layer, ret_trims = True)
        trimmed_img = (trimmed_img * 2) - 1

        fig, axs = plt.subplots(2, (len(block_data.values()) // 2) + 1, figsize = (20, 6), dpi = 300)
        axs = axs.flatten()

        for idx, possible_block in enumerate(block_data.values()):
            convolution_kernel = np.ones((possible_block['width'], possible_block['height']))
            convolution_kernel = convolution_kernel / np.sum(convolution_kernel )

            pad_size = np.max(convolution_kernel.shape)
            padded_img = np.pad(trimmed_img, pad_size, 'constant', constant_values= -1)

            result = cv2.filter2D(padded_img, -1, convolution_kernel)

            result = result[pad_size:-pad_size, pad_size:-pad_size]

            title = possible_block['name'] + ' ' + str(np.max(result).item())
            # fig, ax = plt.subplots(1, 2, figsize = (12, 6))
            plt_img(result, title, ax = axs[idx])
            # ax[1].hist(result, bins = np.linspace(0, 1, 100), histtype = 'step', log = True)
            # plt.show()
        fig.delaxes(axs[-1])
        plt.tight_layout()
        plt.show()
        break

        # Create a matrix of block layer,
        # Start with a high hit rate 0.99 or something and iterate down with 0.01 (set prev position to 0)
        # Go from the bigger blocks that hit that "hit rate" and clear the remaining layers from that block.
        # Maybe recalibrate the hit rate? if only shit remains then return
