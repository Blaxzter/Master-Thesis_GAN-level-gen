from pathlib import Path
from time import sleep

import matplotlib.pyplot as plt

from converter.to_img_converter.LevelImgDecoder import LevelImgDecoder
from converter.to_img_converter.LevelImgEncoder import LevelImgEncoder
from testing.TestEnvironment import TestEnvironment


def img_encoding_decoding_test():
    test_environment = TestEnvironment('generated/single_structure')

    for level_idx, level in test_environment.iter_levels():
        img_rep = create_encoding(level)
        level = create_decoding(img_rep)
        break


def create_decoding(img_rep):
    level_img_decoder = LevelImgDecoder()
    level_img_decoder.visualize_contours(img_rep)
    level_img_decoder.visualize_rectangles(img_rep, material_id = 1)
    level_img_decoder.visualize_rectangles(img_rep, material_id = 2)
    level_img_decoder.visualize_rectangles(img_rep, material_id = 3)
    pass


def create_encoding(level):
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
    img_encoding_decoding_test()
