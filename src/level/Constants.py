from enum import Enum

import numpy as np

# blocks number and size
block_sizes = {
    1: (0.84, 0.84),
    2: (0.85, 0.43),
    3: (0.43, 0.85),
    4: (0.43, 0.43),
    5: (0.22, 0.22),
    6: (0.43, 0.22),
    7: (0.22, 0.43),
    8: (0.85, 0.22),
    9: (0.22, 0.85),
    10: (1.68, 0.22),
    11: (0.22, 1.68),
    12: (2.06, 0.22),
    13: (0.22, 2.06)
}

absolute_ground = -3.5

additional_object_sizes = {
    1: (0.82, 0.82),
    2: (0.82, 0.82),
    3: (0.8, 0.8),
    4: (0.45, 0.45)
}

attributes = [
    "type", "material", "x", "y", "rotation", "scaleX", "scaleY"
]

# blocks number and name
# (blocks 3, 7, 9, 11 and 13) are their respective block names rotated 90 derees clockwise
block_names = {
    1: 'SquareHole',
    2: 'RectFat',
    3: 'RectFat',
    4: 'SquareSmall',
    5: 'SquareTiny',
    6: 'RectTiny',
    7: 'RectTiny',
    8: 'RectSmall',
    9: 'RectSmall',
    10: 'RectMedium',
    11: 'RectMedium',
    12: 'RectBig',
    13: 'RectBig'
}

# (blocks 3, 7, 9, 11 and 13) are their respective block names rotated 90 derees clockwise
block_is_rotated = {
    1: False,
    2: False,
    3: True,
    4: False,
    5: False,
    6: False,
    7: True,
    8: False,
    9: True,
    10: False,
    11: True,
    12: False,
    13: True,
}

pig_types = {
    1: "BasicSmall",
    2: "BasicMedium"
}

pig_size = (0.5, 0.5)

# additional objects number and name
additional_objects = {'1': "TriangleHole", '2': "Triangle", '3': "Circle", '4': "CircleSmall"}

# additional objects number and size
additional_object_sizes = {'1': [0.82, 0.82], '2': [0.82, 0.82], '3': [0.8, 0.8], '4': [0.45, 0.45]}

bird_names = {
    1: "BirdRed",
    2: "BirdBlue",
    3: "BirdYellow",
    4: "BirdBlack",
    5: "BirdWhite"
}

materials = ["wood", "stone", "ice"]
materials_color = ["brown", "grey", "blue"]

coordinate_round = 100000
resolution = 0.11 / 2
resolution = 0.07

min_distance_to_slingshot = 2


class ObjectType(Enum):
    Block = 1
    Platform = 2
    Pig = 3
    Slingshot = 4
    SpecialBlock = 5
    Bird = 5


def get_sizes(print_data = True):
    from tabulate import tabulate

    data = [[
        block_names[block_idx],
        block_size[0],
        block_size[1],
        block_size[0] / resolution,
        block_size[1] / resolution,
        round(block_size[0] / resolution),
        round(block_size[1] / resolution),
        block_is_rotated[block_idx]
    ] for block_idx, block_size in block_sizes.items()]

    if print_data:
        print(tabulate(data, headers = ['block_name', 'width', 'height', 'width in res', 'height in res', 'rounded width', 'rounded height', 'Rotated']))

    return [dict(
        name = x[0],
        orig_width = x[1],
        orig_height = x[2],
        width_res = x[3],
        height_res = x[4],
        rounded_width = x[5],
        rounded_height = x[6],
        area = x[5] * x[6],
        rotated = x[7],
    ) for x in data]


if __name__ == '__main__':
    size_list = []
    for i in range(1, 20):
        module_list = []
        for width, height in block_sizes.values():
            i_width = int(width * 100) / i - int(int(width * 100) / i)
            module_list.append(i_width)
            module_list.append(int(height * 100) / i - int(int(height * 100) / i))
        size_list.append(np.max(module_list))

    print(size_list)

    for div_list in size_list:
        print(div_list)

    # get_sizes()
