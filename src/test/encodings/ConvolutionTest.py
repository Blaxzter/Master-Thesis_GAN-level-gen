import pickle
from typing import Dict, List

import cv2
import matplotlib.pyplot as plt
import numpy as np
from icecream import ic
from matplotlib.patches import Rectangle

from converter.to_img_converter import DecoderUtils
from converter.to_img_converter.LevelImgDecoder import LevelImgDecoder
from converter.to_img_converter.LevelImgEncoder import LevelImgEncoder
from converter.to_img_converter.MultiLayerStackDecoder import MultiLayerStackDecoder
from data_scripts.CreateEncodingData import create_element_for_each_block
from level import Constants
from level.Level import Level
from level.LevelVisualizer import LevelVisualizer
from test.TestEnvironment import TestEnvironment
from util.Config import Config

config = Config.get_instance()

plot_stuff = False

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


def plt_img(img, title, ax = None, flip = False):
    if not plot_stuff:
        return
    if ax is None:
        plt.imshow(img)
        plt.title(title)
        plt.colorbar()
        plt.show()
    else:
        if flip:
            ax.imshow(np.flip(img, axis = 0))
        else:
            ax.imshow(img)
        ax.set_title(title)


def create_plt_array(dpi = 100):
    if not plot_stuff:
        return None, None

    fig, axs = plt.subplots(5, 3, figsize = (15, 10), dpi = dpi)
    axs = axs.flatten()
    fig.delaxes(axs[-1])
    fig.delaxes(axs[-2])
    return fig, axs


def plot_matrix(matrix, blocks, axs):
    if not plot_stuff:
        return
    for layer in range(matrix.shape[-1]):
        _plot_img = matrix[:, :, layer]
        plt_img(_plot_img, blocks[layer]['name'], ax = axs[layer])
    plt.tight_layout()
    plt.show(block = False)


def plot_matrix_complete(matrix, blocks, title = None, add_max = True, block = False, position = None, delete_rectangles = None, flipped = False, selected_block = None):
    if not plot_stuff:
        return

    fig, axs = create_plt_array(dpi = 200)
    for layer_idx in range(matrix.shape[-1]):
        _plot_img = matrix[:, :, layer_idx]
        ax_title = blocks[layer_idx]['name'] + (f' {np.max(_plot_img).item()}' if add_max else '')
        plt_img(_plot_img, ax_title, ax = axs[layer_idx], flip = flipped)
        color = 'blue' if (selected_block is not None and selected_block == layer_idx) else 'red'

        if position is not None:
            height = _plot_img.shape[0]
            if flipped:
                axs[layer_idx].scatter([position[1]], [height - position[0]], color = 'red', s = 1)
            else:
                axs[layer_idx].scatter([position[1]], [position[0]], color = 'red', s = 1)

        if delete_rectangles is not None:
            height = _plot_img.shape[0]
            (start, end, top, bottom) = delete_rectangles[layer_idx]
            if flipped:
                axs[layer_idx].add_patch(
                    Rectangle((start, height - top - 1), end - start, top - bottom,
                              fill = False, color = color, linewidth = 1))
            else:
                axs[layer_idx].add_patch(
                    Rectangle((start, top), end - start, bottom - top,
                              fill = False, color = color,linewidth = 1))

    if title is not None:
        fig.suptitle(title)

    plt.tight_layout()
    plt.show(block = block)


if __name__ == '__main__':
    test_outputs = load_test_outputs_of_model('multilayer_with_air.pickle')

    direction = 'vertical'
    direction = 'horizontal'
    x_offset = 0
    y_offset = 0

    elements, sizes = create_element_for_each_block(direction, 2, x_offset, y_offset, diff_materials = False)
    level_img_encoder = LevelImgEncoder()
    testing_img = level_img_encoder.create_calculated_img(elements)

    # test_environment = TestEnvironment('generated/single_structure')
    # level_img_decoder = LevelImgDecoder()
    # level_img_encoder = LevelImgEncoder()
    # level = test_environment.get_level(0)
    # elements = level.get_used_elements()
    # testing_img = level_img_encoder.create_calculated_img(elements)
    # testing_img[testing_img != 2] = 0
    # testing_img[testing_img == 2] = 1

    test_image = list(test_outputs.keys())[0]
    ic(test_image)
    test_output = test_outputs[test_image]['output']
    test_output = (test_output[0] + 1) / 2

    for layer_idx in range(1, test_output.shape[-1]):

        layer = test_output[:, :, layer_idx]
        # layer = testing_img

        plt.imshow(layer)
        plt.show()

        layer = np.pad(layer, 10)
        layer = np.flip(layer, axis = 0)

        plt_img(layer, 'Original')
        frequency, bins = np.histogram(layer, bins = 100)

        plt.hist(layer, bins = np.linspace(0, 1, 100), histtype='step', log = True)
        plt.show()

        center = (bins[-1] - bins[0]) / 2
        highest_lowest_value = bins[0]
        for i in range(20):
            highest_count = frequency.argmax()
            highest_count_value = bins[highest_count]
            frequency[highest_count] = 0
            if highest_count_value < center:
                # print(highest_lowest_value, highest_count_value)
                if highest_lowest_value < highest_count_value:
                    highest_lowest_value = highest_count_value

        print(highest_lowest_value, center, bins[-1])
        layer[layer <= highest_lowest_value] = 0

        # plt.hist(layer, bins = np.linspace(0, 1, 100), histtype='step', log = True)
        # plt.show()

        trimmed_img, trim_data = DecoderUtils.trim_img(layer, ret_trims = True)
        trimmed_img = (trimmed_img * 2) - 1

        level_plot_

        avg_results = []
        sum_results = []
        for idx, possible_block in enumerate(block_data.values()):
            sum_convolution_kernel = np.ones((possible_block['height'] + 1, possible_block['width'] + 1))
            avg_convolution_kernel = sum_convolution_kernel / np.sum(sum_convolution_kernel)
            # sum_convolution_kernel = np.pad(sum_convolution_kernel, 1, 'constant', constant_values = -1)

            pad_size = np.max(sum_convolution_kernel.shape)
            padded_img = np.pad(trimmed_img, pad_size, 'constant', constant_values = -1)

            sum_result = cv2.filter2D(padded_img, -1, sum_convolution_kernel)[pad_size:-pad_size, pad_size:-pad_size]
            avg_result = cv2.filter2D(padded_img, -1, avg_convolution_kernel)[pad_size:-pad_size, pad_size:-pad_size]

            avg_results.append(avg_result)
            sum_results.append(sum_result)

            # fig, ax = plt.subplots(1, 2, figsize = (12, 6))
            # ax[1].hist(result, bins = np.linspace(0, 1, 100), histtype = 'step', log = True)
            # plt.show()

        # Create a matrix of block layer,
        # Start with a high hit rate 0.99 or something and iterate down with 0.01 (set prev position to 0)
        # Go from the bigger blocks that hit that "hit rate" and clear the remaining layers from that block.
        # Maybe recalibrate the hit rate? if only shit remains then return

        blocks: List[Dict] = list(block_data.values())

        hit_probabilities = np.stack(avg_results, axis = -1)
        size_ranking = np.stack(sum_results, axis = -1)
        stop_condition = np.sum(trimmed_img[trimmed_img > 0]).item()
        TOLERANCE = stop_condition * 0.1

        plot_matrix_complete(hit_probabilities, blocks, title = 'Hit Confidence', block = False)
        plot_matrix_complete(size_ranking, blocks, title = 'Size Ranking', block = False)


        def delete_blocks(_block_rankings, center_block, _position):
            ret_block_ranking = np.copy(_block_rankings)

            left_extension = (center_block['width'] + 1) // 2
            right_extension = (center_block['width'] + 1) // 2
            top_extension = (center_block['height'] + 1) // 2
            bottom_extension = (center_block['height'] + 1) // 2
            y, x = _position

            max_height, max_width = ret_block_ranking.shape[:2]

            delete_rectangles = []

            for block_idx, outside_block in enumerate(blocks):
                start = x - (((outside_block['width'] + 1) // 2) + left_extension)
                end = x + ((outside_block['width'] + 1) // 2) + right_extension - outside_block['width'] % 2

                top = y - ((outside_block['height'] + 1) // 2) - top_extension
                bottom = y + ((outside_block['height'] + 1) // 2) + bottom_extension - outside_block['height'] % 2

                start = start if start > 0 else 0
                end = end if end < max_width else max_width - 1
                top = top if top > 0 else 0
                bottom = bottom if bottom < max_height else max_height - 1

                x_cords = np.arange(start, end + 1, 1)
                y_cords = np.arange(top, bottom + 1, 1)
                x_pos, y_pos = np.meshgrid(y_cords, x_cords)
                ret_block_ranking[x_pos, y_pos, block_idx] = 0

                delete_rectangles.append((start, end, top, bottom))

            return ret_block_ranking, delete_rectangles


        def _select_blocks(_block_rankings, _selected_blocks: List, _stop_condition: float, _covered_area: float = 0):
            print(_covered_area, _stop_condition)
            if _stop_condition - _covered_area < 1:
                return _selected_blocks

            # select the most probable block that is also the biggest
            next_block = np.unravel_index(np.argmax(_block_rankings), _block_rankings.shape)

            # Extract the block
            selected_block = blocks[next_block[-1]]
            block_position = next_block[0:2]
            description = f"Selected Block: {selected_block['name']} with {_block_rankings[next_block]} area with {len(_selected_blocks)} selected"
            print(description)

            # Remove all blocks that cant work with that blocks together
            next_block_rankings, delete_rectangles = delete_blocks(_block_rankings, selected_block, block_position)

            plot_matrix_complete(_block_rankings, blocks, title = description, add_max = True, block = True, position = block_position, delete_rectangles = delete_rectangles, selected_block = next_block[-1])

            if np.all(next_block_rankings < 0.00001):
                print("No position available")
                return _selected_blocks

            next_blocks = _selected_blocks.copy()
            next_blocks.append(dict(
                position = block_position,
                block = selected_block,
            ))
            next_covered_area = _covered_area + ((selected_block['width'] + 1) * (selected_block['height'] + 1))
            return _select_blocks(next_block_rankings, next_blocks, _stop_condition, next_covered_area)


        for hit_rate in np.linspace(0.85, 0.5, 10):
            percentage_cut = np.copy(hit_probabilities)
            percentage_cut[hit_probabilities <= hit_rate] = 0

            current_size_ranking = percentage_cut * size_ranking
            plot_matrix_complete(current_size_ranking, blocks, "Current Size Rankings", add_max = True, block = False)
            rounded_block_rankings = np.around(current_size_ranking, 5)  # Round to remove floating point errors
            selected_blocks = _select_blocks(rounded_block_rankings, [], stop_condition, _covered_area = 0)

            # plot_matrix(current_size_ranking, blocks, axs)

            if selected_blocks is not None:
                print('Blocks Selected')
                ic(selected_blocks)
                for block in selected_blocks:
                    block['material'] = layer_idx
                break

            break

        stack_decoder = MultiLayerStackDecoder()
        level_elements = stack_decoder.create_level_elements(selected_blocks, [])
        created_level = Level.create_level_from_structure(level_elements)

        ic(created_level)

        level_visualizer = LevelVisualizer()
        level_visualizer.create_img_of_structure(level_elements)

        break

    plt.show()
