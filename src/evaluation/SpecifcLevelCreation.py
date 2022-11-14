import pickle
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go

from converter.to_img_converter.MultiLayerStackDecoder import MultiLayerStackDecoder
from game_management.GameConnection import GameConnection
from game_management.GameManager import GameManager
from util.Config import Config

mpl.rcParams["savefig.format"] = 'pdf'


def create_screenshots():
    config = Config.get_instance()
    quantitative_search_output = config.get_grid_search_file(f"quantitative_search_output")
    if Path(quantitative_search_output).exists():
        with open(quantitative_search_output, 'rb') as f:
            data_output_list = pickle.load(f)

    multilayer_stack_decoder = MultiLayerStackDecoder()

    multilayer_stack_decoder.round_to_next_int = True
    multilayer_stack_decoder.custom_kernel_scale = True
    multilayer_stack_decoder.minus_one_border = True
    multilayer_stack_decoder.combine_layers = True
    multilayer_stack_decoder.negative_air_value = -1
    multilayer_stack_decoder.cutoff_point = 0.5
    multilayer_stack_decoder.display_decoding = False

    print(len(data_output_list))

    filtered_levels = list(filter(lambda element: True if 'is_stable' in element['data'] else False, data_output_list))

    # Number of levels with heigehst block
    stable_levels = list(filter(lambda element: element['data']['is_stable'], filtered_levels))

    low_damage_levels = list(filter(lambda element: element['data']['damage'] < 20, filtered_levels))

    unstable_levels = list(
        filter(lambda element: not element['data']['is_stable'] if 'is_stable' in element['data'] else False,
               data_output_list))

    # sorted_by_block_amount = sorted(stable_levels, key = lambda element: (element['data']['damage'], -element['data']['total']), reverse = False)
    sorted_by_block_amount = sorted(stable_levels,
                                    key = lambda element: (-element['data']['pig_amount']),
                                    reverse = False)

    # Create pictures
    game_connection = GameConnection(conf = config, port = 9001)
    game_manager: GameManager = GameManager(config, game_connection = game_connection)
    game_manager.start_game()

    amount_of_pictures = 20

    for idx in range(amount_of_pictures):
        fig, ax = plt.subplots(1, 1)
        level = sorted_by_block_amount[idx]['level']

        print(sorted_by_block_amount[idx]['data'])

        game_manager.create_levels_xml_file([level], store_level_name = f"stable_level_{idx}")
        game_manager.copy_game_levels(
            level_path = config.get_data_train_path(folder = 'temp'),
            rescue_level = False
        )
        game_manager.select_level(4)
        screenshot = game_manager.get_img()
        ax.imshow(screenshot)

        file_name = config.get_quality_search_folder(f'{idx}_pig_amount')
        # mpl.rcParams["savefig.directory"] = config.quality_root
        plt.savefig(file_name)


def create_bar_chart():
    config = Config.get_instance()
    quantitative_search_output = config.get_grid_search_file(f"quantitative_search_output")
    if Path(quantitative_search_output).exists():
        with open(quantitative_search_output, 'rb') as f:
            data_output_list = pickle.load(f)

    filtered_levels = list(filter(lambda element: True if 'is_stable' in element['data'] else False, data_output_list))

    # Number of levels with heigehst block
    stable_levels = list(
        filter(lambda element: element['data']['damage'] <= 0 if 'damage' in element['data'] else False,
               filtered_levels))
    unstable_levels = list(
        filter(lambda element: element['data']['damage'] > 0 if 'damage' in element['data'] else False,
               data_output_list))

    print(len(stable_levels))
    print(len(unstable_levels))

    sim_data = ['damage', 'is_stable', 'woodBlockDestroyed', 'iceBlockDestroyed', 'stoneBlockDestroyed',
                'totalBlocksDestroyed']

    meta_data_options = [
        'min_x', 'max_x', 'min_y', 'max_y', 'height', 'width', 'block_amount',
        'height_width_ration', 'platform_amount', 'pig_amount', 'special_block_amount', 'total', 'ice_blocks',
        'stone_blocks', 'wood_blocks'
    ]
    collected_data = sim_data + meta_data_options
    show_in_graph = {k: True for k in collected_data}
    show_in_graph['platform_amount'] = False
    show_in_graph['is_stable'] = False
    show_in_graph['pig_amount'] = False
    show_in_graph['special_block_amount'] = False
    show_in_graph['woodBlockDestroyed'] = False
    show_in_graph['iceBlockDestroyed'] = False
    show_in_graph['stoneBlockDestroyed'] = False
    show_in_graph['ice_blocks'] = False
    show_in_graph['ice_blocks'] = False
    show_in_graph['stone_blocks'] = False
    show_in_graph['wood_blocks'] = False
    show_in_graph['min_x'] = False
    show_in_graph['max_x'] = False
    show_in_graph['min_y'] = False
    show_in_graph['max_y'] = False

    collected_data_label_map = dict(
        damage = 'Damage',
        is_stable = 'Is Stable',
        woodBlockDestroyed = '# Wood Blocks Destroyed',
        iceBlockDestroyed = '# Ice Blocks Destroyed',
        stoneBlockDestroyed = '# Stone Blocks Destroyed',
        totalBlocksDestroyed = '# Total Blocks Destroyed',
        height_width_ration = 'Height width ratio',
        min_x = 'Min X',
        max_x = 'Max X',
        min_y = 'Min Y',
        max_y = 'Max Y',
        height = 'Height',
        width = 'Width',
        block_amount = '# Block',
        platform_amount = '# Platform',
        pig_amount = '# Pig',
        special_block_amount = '# Special Block',
        total = '# Total Elements',
        ice_blocks = '# ice block',
        stone_blocks = '# stone block',
        wood_blocks = '# wood block'
    )

    data = []

    for data_name, data_source in [('Stable Levels', stable_levels), ('Unstable Levels', unstable_levels)]:
        collected_data_labels = []
        y_data = []
        for collected_data_key in collected_data:
            if not show_in_graph[collected_data_key]:
                continue

            collected_data_labels.append(collected_data_label_map[collected_data_key])

            if collected_data_key == 'height_width_ration':
                avg_value_list = list(
                    map(lambda element: element['data']['height'] / element['data']['width'], data_source))
            else:
                avg_value_list = list(map(lambda element: element['data'][collected_data_key], data_source))

            cleared = [i for i in avg_value_list if i is not None and i != -1]
            if type(cleared[0]) == bool:
                print(collected_data_key)
                y_data.append(len([True for value in avg_value_list if value is True]) / len(
                    [True for value in avg_value_list if value is False]) * 100)
            else:
                y_data.append(np.average(cleared))

        data.append(
            go.Bar(name = data_name, x = collected_data_labels, y = y_data, text = np.round(y_data, decimals = 2))
        )

    current_figure = go.Figure(data = data)
    current_figure.update_layout(
        barmode = 'group',
        font = dict(
            size = 18,
        ))
    current_figure.show()


    # img_bytes = current_figure.to_image(format = "pdf", width = 1200, height = 600, scale = 2)
    # f = open("stable_vs_unstable.pdf", "wb")
    # f.write(img_bytes)
    # f.close()


if __name__ == '__main__':
    # create_bar_chart()
    create_screenshots()
