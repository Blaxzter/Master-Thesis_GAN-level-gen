import numpy as np
from pathlib import Path
from time import sleep

import matplotlib.pyplot as plt

from converter.to_img_converter.LevelImgEncoder import LevelImgEncoder
from testing.TestEnvironment import TestEnvironment


def img_encoding_test():
    test_environment = TestEnvironment('generated/single_structure')

    for level_idx, level in test_environment.iter_levels():
        compare_encodings(level, test_environment)
        if level_idx > 0:
            break

def create_encodings():
    test_environment = TestEnvironment('generated/single_structure')

    fig, axs = plt.subplots(2, 6, dpi = 300)

    level_img_encoder = LevelImgEncoder()
    for (level_idx, level), ax in zip(test_environment.iter_levels(0, 12), axs.flatten()):
        encoded_calculated_orig = level_img_encoder.create_calculated_img(level.get_used_elements())
        ax.imshow(encoded_calculated_orig)
        ax.axis('off')

    plt.show()

def create_encoding():
    test_environment = TestEnvironment('generated/single_structure')
    level = test_environment.get_level(2)

    level_img_encoder = LevelImgEncoder()
    encoded_calculated_orig = level_img_encoder.create_calculated_img(level.get_used_elements())
    plt.imshow(encoded_calculated_orig)
    plt.show()

def compare_encodings(level, test_environment):
    level_img_encoder = LevelImgEncoder()

    elements = level.get_used_elements()

    dot_encoding = level_img_encoder.create_dot_img(elements)
    encoded_calculated_orig = level_img_encoder.create_calculated_img(elements)
    no_size_check = level_img_encoder.create_calculated_img_no_size_check(elements)

    fig = plt.figure(constrained_layout = True, dpi = 300)
    fig.suptitle('Compare different level encodings')

    subfigs = fig.subfigures(nrows = 1, ncols = 4)
    ax = subfigs[0].subplots(nrows = 1, ncols = 1)
    test_environment.level_visualizer.create_img_of_structure(elements, ax = ax)
    ax.set_title("Patches")

    encoded_calculated = encoded_calculated_orig
    if no_size_check.shape != encoded_calculated_orig.shape:
        paddig = (no_size_check.shape[0] - encoded_calculated_orig.shape[0], 0), (no_size_check.shape[1] - encoded_calculated_orig.shape[1], 0)
        encoded_calculated = np.pad(encoded_calculated_orig, paddig)

    axs_1 = subfigs[1].subplots(nrows = 2, ncols = 1)
    axs_2 = subfigs[2].subplots(nrows = 2, ncols = 1)
    axs_3 = subfigs[3].subplots(nrows = 2, ncols = 1)

    axs_1[0].imshow(encoded_calculated)
    axs_1[0].set_title("With Size Checks")

    axs_2[0].imshow(no_size_check)
    axs_2[0].set_title("No Size Checks")

    axs_3[0].imshow(no_size_check - encoded_calculated)
    axs_3[0].set_title("Calc Difference")

    encoded_calculated = encoded_calculated_orig
    if dot_encoding.shape != encoded_calculated.shape:
        top_pad = dot_encoding.shape[0] - encoded_calculated_orig.shape[0]
        right_pad = dot_encoding.shape[1] - encoded_calculated_orig.shape[1]
        if top_pad < 0:
            dot_encoding = np.pad(dot_encoding, ((abs(top_pad), 0), (0, 0)))
        else:
            encoded_calculated = np.pad(encoded_calculated_orig, ((abs(top_pad), 0), (0, 0)))

        if right_pad < 0:
            dot_encoding = np.pad(dot_encoding, ((0, 0), (abs(right_pad), 0)))
        else:
            encoded_calculated = np.pad(encoded_calculated_orig, ((0, 0), (abs(right_pad), 0)))

    axs_1[1].imshow(encoded_calculated)
    axs_1[1].set_title("With Size Checks")

    axs_2[1].imshow(dot_encoding)
    axs_2[1].set_title("Dot Img")

    axs_3[1].imshow(dot_encoding - encoded_calculated)
    axs_3[1].set_title("Dot Difference")

    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    create_encodings()
