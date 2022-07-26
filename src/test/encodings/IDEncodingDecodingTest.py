import matplotlib.pyplot as plt

from converter.to_img_converter.LevelIdImgDecoder import LevelIdImgDecoder
from converter.to_img_converter.LevelImgEncoder import LevelImgEncoder
from game_management.GameManager import GameManager
from level.LevelVisualizer import LevelVisualizer
from test.TestEnvironment import TestEnvironment
from util.Config import Config


def encode_decode_test(test_with_game):
    test_environment = TestEnvironment('generated/single_structure')
    level_visualizer = LevelVisualizer()

    if test_with_game:
        game_manager = GameManager(Config.get_instance())
        game_manager.start_game()

    for level_idx, level in test_environment.iter_levels(start = 0, end = 5):

        fig, axs = plt.subplots(2 if test_with_game else 1, 2)
        axs = axs.flatten()

        if test_with_game:
            game_manager.switch_to_level_elements(level.get_used_elements(), 4)
            img = game_manager.get_img(structure = True)
            axs[0].imshow(img)

        img_rep = create_encoding(level)
        decoded_level = get_decoding(img_rep)

        level_visualizer.create_img_of_level(level, ax = axs[2], use_grid = False)
        level_visualizer.create_img_of_level(decoded_level, ax = axs[3], use_grid = False)

        if level == decoded_level:
            print(f'Not equal {level_idx}')

        if test_with_game:
            game_manager.switch_to_level_elements(decoded_level.get_used_elements(), 5)
            img = game_manager.get_img(structure = True)
            axs[1].imshow(img)

        plt.show()

    if test_with_game:
        game_manager.stop_game()


def create_encoding(level, multilayer = False):
    level_img_encoder = LevelImgEncoder()
    return level_img_encoder.create_one_element_img(level.get_used_elements(), multilayer)


def get_decoding(img_rep):
    level_img_decoder = LevelIdImgDecoder()
    return level_img_decoder.decode_level(img_rep)


if __name__ == '__main__':
    encode_decode_test(test_with_game = True)
