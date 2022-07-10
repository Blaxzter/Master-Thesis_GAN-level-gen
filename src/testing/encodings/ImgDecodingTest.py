import itertools
import pickle

from converter.to_img_converter.LevelImgDecoder import LevelImgDecoder
from util.Config import Config

if __name__ == '__main__':
    config = Config.get_instance()
    file_filtered = config.get_pickle_file("single_structure_full_filtered")
    with open(file_filtered, 'rb') as f:
        data = pickle.load(f)

    level_idx = 1
    level_data = next(itertools.islice(iter(data.values()), level_idx, level_idx + 1))
    level_img = level_data['img_data']
    # plt.imshow(level_img)
    # plt.show()

    # level_img = get_debug_level()

    level_img_decoder = LevelImgDecoder()
    level_img_decoder.visualize_contours(level_img)
    # level_img_decoder.visualize_rectangles(level_img, material_id = 2)
    # level_elements = level_img_decoder.decode_level(level_img)
    # level_viz = LevelVisualizer()
    # level_viz.create_img_of_structure(level_elements)

    # level_img_decoder.get_pig_position(level_img)

    # level_elements = level_img_decoder.visualize_one_decoding(level_img, contour_color = 1)
    # level_elements = level_img_decoder.visualize_one_decoding(level_img, contour_color = 2)
    # level_elements = level_img_decoder.visualize_one_decoding(level_img, contour_color = 3)

    # game_manager = GameManager(conf = config)
    # game_manager.start_game()
    # game_manager.switch_to_level_elements(level_elements)
    # img = game_manager.create_img_of_level()
    # plt.imshow(img)
    # plt.show()
    #
    # time.sleep(20)
    # game_manager.stop_game()
