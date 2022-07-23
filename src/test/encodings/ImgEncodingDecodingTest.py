import matplotlib.pyplot as plt

from converter.to_img_converter.LevelImgDecoder import LevelImgDecoder
from converter.to_img_converter.LevelImgEncoder import LevelImgEncoder
from data_scripts.CreateEncodingData import create_element_for_each_block
from level.Level import Level
from level.LevelVisualizer import LevelVisualizer
from test.TestEnvironment import TestEnvironment


def decode_test_level():
    test_elements, _ = create_element_for_each_block()
    test_level = Level.create_level_from_structure(test_elements)
    img_rep = create_encoding(test_level)
    level_img_decoder = LevelImgDecoder()
    decoded_elements = level_img_decoder.decode_level(img_rep)
    created_level = Level.create_level_from_structure(decoded_elements)
    created_level.print_elements(as_table = True)

    visualizer = LevelVisualizer()
    visualizer.create_img_of_level(created_level, use_grid = False, add_dots = False)



def img_encoding_decoding_test():
    test_environment = TestEnvironment('generated/single_structure')

    for level_idx, level in test_environment.iter_levels():
        level.print_elements(as_table = True)

        img_rep = create_encoding(level)
        visualize_decoding(img_rep)
        break


def create_rectangles(img_rep):
    level_img_decoder = LevelImgDecoder()
    # decoded_level = level_img_decoder.visualize_contours(img_rep)
    # level_img_decoder.visualize_rectangles(img_rep, material_id = 1)
    level_img_decoder.visualize_rectangles(img_rep, material_id = 2)
    # level_img_decoder.visualize_rectangles(img_rep, material_id = 3)


def visualize_decoding(img_rep):
    level_img_decoder = LevelImgDecoder()
    # level_img_decoder.visualize_one_decoding(img_rep, material_id = 1)
    level_img_decoder.visualize_one_decoding(img_rep, material_id = 2)
    # level_img_decoder.visualize_rectangles(img_rep, material_id = 3)


def create_encoding(level):
    level_img_encoder = LevelImgEncoder()
    elements = level.get_used_elements()
    return level_img_encoder.create_calculated_img(elements)


def visualize_encoding(level):
    level_img_encoder = LevelImgEncoder()

    elements = level.get_used_elements()

    encoded_dots = level_img_encoder.create_dot_img(elements)
    encoded_calculated = level_img_encoder.create_calculated_img(elements)

    fig, axs = plt.subplots(1, 2, dpi = 300, figsize = (12, 6))
    axs[0].imshow(encoded_calculated)
    axs[0].set_title("Calculated")

    axs[1].imshow(encoded_dots)
    axs[1].set_title("Through Dots")

    plt.tight_layout()
    plt.show()

    return encoded_calculated

if __name__ == '__main__':
    # decode_test_level()
    decode_test_level()
