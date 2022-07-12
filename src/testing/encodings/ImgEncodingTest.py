import numpy as np
from pathlib import Path
from time import sleep

import matplotlib.pyplot as plt

from converter.to_img_converter.LevelImgEncoder import LevelImgEncoder
from testing.TestEnvironment import TestEnvironment


def img_encoding_test():
    test_environment = TestEnvironment('generated/single_structure')

    for level_idx, level in test_environment.iter_levels():
        create_encoding(level, test_environment)


def create_encoding(level, test_environment):
    level_img_encoder = LevelImgEncoder()

    elements = level.get_used_elements()

    encoded_calculated = level_img_encoder.create_calculated_img(elements)
    no_size_check = level_img_encoder.create_calculated_img_no_size_check(elements)

    fig, axs = plt.subplots(1, 4, dpi = 300, figsize = (12, 4))

    test_environment.level_visualizer.create_img_of_structure(elements, ax = axs[0])
    axs[0].set_title("Patches")

    if no_size_check.shape != encoded_calculated.shape:
        paddig = (no_size_check.shape[0] - encoded_calculated.shape[0], 0), (no_size_check.shape[1] - encoded_calculated.shape[1], 0)
        encoded_calculated = np.pad(encoded_calculated, paddig)

    axs[1].imshow(encoded_calculated)
    axs[1].set_title("With Size Checks")

    axs[2].imshow(no_size_check)
    axs[2].set_title("No Size Checks")

    axs[3].imshow(no_size_check - encoded_calculated)
    axs[3].set_title("Difference")

    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    img_encoding_test()
