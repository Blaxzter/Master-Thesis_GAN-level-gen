from pathlib import Path
from time import sleep

import matplotlib.pyplot as plt

from converter.to_img_converter.LevelImgEncoder import LevelImgEncoder
from testing.TestEnvironment import TestEnvironment


def img_encoding_decoding_test():
    test_environment = TestEnvironment()

    for level_idx, level in test_environment.iter_levels():
        create_encoding(level, test_environment)
        if level_idx > 5:
            break


def create_encoding(level, test_environment):
    level_img_encoder = LevelImgEncoder()

    elements = level.get_used_elements()

    encoded_calculated = level_img_encoder.create_calculated_img(elements)
    encoded_dots = level_img_encoder.create_calculated_img_no_size_check(elements)

    fig, axs = plt.subplots(1, 3, dpi = 300, figsize = (12, 4))

    test_environment.level_visualizer.create_img_of_structure(elements, ax = axs[0])
    axs[0].set_title("Patches")

    axs[1].imshow(encoded_calculated)
    axs[1].set_title("Calculated")

    axs[2].imshow(encoded_dots)
    axs[2].set_title("Through Dots")


    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    img_encoding_decoding_test()
