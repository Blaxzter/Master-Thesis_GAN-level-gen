
from typing import List, Dict

import cv2
import numpy as np
from scipy import ndimage

from converter import MathUtil
from converter.to_img_converter import DecoderUtils
from level import Constants
from level.LevelElement import LevelElement
from test.TestUtils import plot_matrix_complete
from test.encodings.ConvolutionTest import get_cutoff_point
from util.Config import Config


class MultiLayerStackDecoder:

    def __init__(self):
        self.config = Config.get_instance()
        self.block_data = self.config.get_block_data(Constants.resolution)
        self.blocks: List[Dict] = list(self.block_data.values())
        self.delete_matrices = self.create_delete_block_matrices()

        # Decoding parameter
        self.round_to_next_int = False
        self.move_to_minus_one_one = False
        self.custom_kernel_scale = True
        self.minus_one_border = True
        self.cutoff_point = 0.85
        self.bird_cutoff = 0.5

    def preprocess_layer(self, layer):
        pass

    def decode(self):
        # Move each possible blocks like a convolution over the block mush
        # for every position store the overlap 1 = full overlap 0 = no overlap
        # sort by overlap with mush
        # Select top element, filter elements that overlap, repeat
        # If no element are over the coverage is high enough return with selected
        # Otherwise go with next block
        pass

    def decode_layer(self, layer, layer_idx):
        layer = np.flip(layer, axis = 0)
        # Normalize Layer
        layer = (layer - np.min(layer)) / (np.max(layer) - np.min(layer))

        if self.round_to_next_int:
            layer = np.rint(layer)

        # Unify the lowest values
        highest_lowest_value = self.get_cutoff_point(layer)
        layer[layer <= highest_lowest_value] = 0

        trimmed_img, trim_data = DecoderUtils.trim_img(layer, ret_trims = True)

        if self.move_to_minus_one_one:
            trimmed_img = (trimmed_img * 2) - 1

        hit_probabilities, size_ranking = self.create_confidence_matrix(trimmed_img)

        stop_condition = np.sum(trimmed_img[trimmed_img > 0]).item()

        hit_probabilities[hit_probabilities <= self.cutoff_point] = 0

        # Create a ranking depending on the hit probability and the covering of the block
        current_size_ranking = hit_probabilities * size_ranking

        rounded_block_rankings = np.around(current_size_ranking, 5)  # Round to remove floating point errors
        selected_blocks = self.select_blocks(rounded_block_rankings, [], stop_condition, _covered_area = 0)

        ret_blocks = []

        top_space, bottom_space, left_space, right_space = trim_data
        if selected_blocks is not None:
            for block in selected_blocks:
                block['position'][0] += top_space
                block['position'][1] += left_space
                block['material'] = layer_idx
                ret_blocks.append(block)

        return ret_blocks

    def create_confidence_matrix(self, layer):
        avg_results = []
        sum_results = []
        
        for idx, possible_block in enumerate(self.block_data.values()):
            sum_convolution_kernel = np.ones((possible_block['height'] + 1, possible_block['width'] + 1))

            if self.custom_kernel_scale:
                sum_convolution_kernel = sum_convolution_kernel * possible_block['scalar']

            avg_convolution_kernel = sum_convolution_kernel / np.sum(sum_convolution_kernel)

            if self.minus_one_border:
                sum_convolution_kernel = np.pad(sum_convolution_kernel, 1, 'constant', constant_values = -1)

            pad_value = -1 if recalibrate else 0

            pad_size = np.max(sum_convolution_kernel.shape)
            padded_img = np.pad(layer, pad_size, 'constant', constant_values = pad_value)

            sum_result = cv2.filter2D(padded_img, -1, sum_convolution_kernel)[pad_size:-pad_size, pad_size:-pad_size]
            avg_result = cv2.filter2D(padded_img, -1, avg_convolution_kernel)[pad_size:-pad_size, pad_size:-pad_size]

            avg_results.append(avg_result)
            sum_results.append(sum_result)

        hit_probabilities = np.stack(avg_results, axis = -1)
        size_ranking = np.stack(sum_results, axis = -1)

        return hit_probabilities, size_ranking

    def _get_pig_position(self, bird_layer):
        current_img = np.copy(bird_layer)

        current_img = np.flip(current_img, axis = 0)

        highest_lowest_value = get_cutoff_point(bird_layer)
        current_img[current_img <= highest_lowest_value] = 0

        kernel = MathUtil.get_circular_kernel(7)
        kernel = kernel / np.sum(kernel)
        padded_img = np.pad(current_img, 6, 'constant', constant_values = -1)
        bird_probabilities = cv2.filter2D(padded_img, -1, kernel)[6:-6, 6:-6]

        bird_probabilities[bird_probabilities < self.bird_cutoff] = 0
        trimmed_bird_img, trim_data = DecoderUtils.trim_img(bird_probabilities, ret_trims = True)

        max_height, max_width = trimmed_bird_img.shape
        top_space, bottom_space, left_space, right_space = trim_data

        bird_positions = []
        trim_counter = 0
        while not np.all(trimmed_bird_img < 0.00001):
            bird_position = np.unravel_index(np.argmax(trimmed_bird_img), trimmed_bird_img.shape)
            y, x = bird_position
            bird_positions.append([
                top_space + y, left_space + x
            ])

            # Remove the location the bird was picked
            x_cords = np.arange(x - 6, x + 6 + 1, 1)
            y_cords = np.arange(y - 6, y + 6 + 1, 1)
            x_cords[x_cords < 0] = 0
            x_cords[x_cords >= max_width] = max_width - 1
            y_cords[y_cords < 0] = 0
            y_cords[y_cords >= max_height] = max_height - 1
            x_pos, y_pos = np.meshgrid(y_cords, x_cords)

            trimmed_bird_img[x_pos, y_pos] = 0
            if plot_stuff:
                plt.imshow(trimmed_bird_img)
                plt.title(f'Bird Removed at: x_pos: {x} ,y_pos: {y}')
                if plot_to_file:
                    global img_counter
                    plt.savefig(config.get_conv_debug_img_file(f'{img_counter}_{trim_counter}_bird_after_trim'))
                    img_counter += 1
                    plt.close()
                else:
                    plt.show()

            trim_counter += 1

        return bird_positions

    def select_blocks(self, _block_rankings, _selected_blocks: List, _stop_condition: float, _covered_area: float = 0):
        print(_covered_area, _stop_condition)
        if _stop_condition - _covered_area < 1:
            return _selected_blocks

        # select the most probable block that is also the biggest
        next_block = np.unravel_index(np.argmax(_block_rankings), _block_rankings.shape)

        # Extract the block
        selected_block = blocks[next_block[-1]]
        block_position = list(next_block[0:2])
        description = f"Selected Block: {selected_block['name']} with {_block_rankings[next_block]} area with {len(_selected_blocks)} selected"
        print(description)

        # Remove all blocks that cant work with that blocks together
        next_block_rankings, delete_rectangles = delete_blocks(_block_rankings, selected_block, block_position)

        if allow_plot:
            plot_matrix_complete(_block_rankings, blocks, title = description, add_max = True, block = True,
                                 position = block_position, delete_rectangles = delete_rectangles,
                                 selected_block = next_block[-1], save_name = f'{selected_block["name"]}_selected')

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

    def create_delete_block_matrices(self):
        """
        Function that creates a matrix that deletes the possible blocks at this location over the layer matrix
        """

        def _get_block_ranges(blocks):
            """
            Internal function that creates a list for each block for each range
            """
            ret_ranges = dict()

            for center_block_idx, center_block in enumerate(blocks):

                current_list = list()

                left_extension = (center_block['width'] + 1) // 2
                right_extension = (center_block['width'] + 1) // 2
                top_extension = (center_block['height'] + 1) // 2
                bottom_extension = (center_block['height'] + 1) // 2

                x_max = -np.inf
                y_max = -np.inf

                for outside_block_idx, outside_block in enumerate(blocks):
                    start = -(((outside_block['width'] + 1) // 2) + left_extension)
                    end = ((outside_block['width'] + 1) // 2) + right_extension - outside_block['width'] % 2

                    top = -(((outside_block['height'] + 1) // 2) + top_extension)
                    bottom = ((outside_block['height'] + 1) // 2) + bottom_extension - outside_block['height'] % 2

                    x_cords = np.arange(start, end + 1, 1)
                    y_cords = np.arange(top, bottom + 1, 1)

                    x_max = len(x_cords) if len(x_cords) > x_max else x_max
                    y_max = len(y_cords) if len(y_cords) > y_max else y_max

                    current_list.append((x_cords, y_cords))

                ret_ranges[center_block_idx] = dict(
                    name = center_block['name'],
                    range_list = current_list,
                    x_max = x_max,
                    y_max = y_max,
                )
            return ret_ranges

        block_ranges = _get_block_ranges(self.blocks)
        ret_matrices = dict()

        for block_idx, block_range in block_ranges.items():
            range_list, x_max, y_max = block_range['range_list'], block_range['x_max'], block_range['y_max']
            multiply_matrix = np.ones((x_max, y_max, len(range_list)))

            center_pos_x, center_pos_y = x_max // 2, y_max // 2

            for layer_idx, (x_cords, y_cords) in enumerate(range_list):
                x_cords += center_pos_x
                y_cords += center_pos_y
                x_pos, y_pos = np.meshgrid(y_cords, x_cords)
                multiply_matrix[y_pos, x_pos, layer_idx] = 0

            ret_matrices[block_idx] = multiply_matrix
            plot_matrix_complete(multiply_matrix, decoder.blocks, title = f'Delete Matrix of {block_range["name"]}')

        return ret_matrices

    def get_cutoff_point(self, layer):
        frequency, bins = np.histogram(layer, bins = 100)

        center = (bins[-1] - bins[0]) / 2
        highest_lowest_value = bins[0]
        for i in range(20):
            highest_count = frequency.argmax()
            highest_count_value = bins[highest_count]
            frequency[highest_count] = 0

            if highest_count_value < center:

                if highest_lowest_value < highest_count_value:
                    highest_lowest_value = highest_count_value

        return highest_lowest_value

    @staticmethod
    def create_level_elements(blocks, pig_position):
        ret_level_elements = []
        block_idx = 0
        for block_idx, block in enumerate(blocks):
            block_attribute = dict(
                type = block['block']['name'],
                material = Constants.materials[block['material'] - 1],
                x = block['position'][1] * Constants.resolution,
                y = block['position'][0] * Constants.resolution,
                rotation = 90 if block['block']['rotated'] else 0
            )
            element = LevelElement(id = block_idx, **block_attribute)
            element.create_set_geometry()
            ret_level_elements.append(element)
        block_idx += 1

        for pig_idx, pig in enumerate(pig_position):
            pig_attribute = dict(
                type = "BasicSmall",
                material = None,
                x = pig[1] * Constants.resolution,
                y = pig[0] * Constants.resolution,
                rotation = 0
            )
            element = LevelElement(id = pig_idx + block_idx, **pig_attribute)
            element.create_set_geometry()
            ret_level_elements.append(element)

        return ret_level_elements


if __name__ == '__main__':
    decoder = MultiLayerStackDecoder()
    delete_matrix = decoder.create_delete_block_matrices()

    plot_matrix_complete(delete_matrix, decoder.blocks)

