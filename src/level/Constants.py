from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass
class LevelMetaData:
    """ Class that represents a levels / structures meta data """
    height: float = None
    width: float = None
    block_amount: int = None
    platform_amount: int = None
    pig_amount: int = None
    special_block_amount: int = None
    total: int = None
    stable: Optional[bool] = None

# blocks number and size
block_sizes = {
    '1': (0.84, 0.84),
    '2': (0.85, 0.43),
    '3': (0.43, 0.85),
    '4': (0.43, 0.43),
    '5': (0.22, 0.22),
    '6': (0.43, 0.22),
    '7': (0.22, 0.43),
    '8': (0.85, 0.22),
    '9': (0.22, 0.85),
    '10': (1.68, 0.22),
    '11': (0.22, 1.68),
    '12': (2.06, 0.22),
    '13': (0.22, 2.06)
}

absolute_ground = -3.5

additional_object_sizes = {
    '1': (0.82, 0.82),
    '2': (0.82, 0.82),
    '3': (0.8, 0.8),
    '4': (0.45, 0.45)
}

attributes = [
    "type", "material", "x", "y", "rotation", "scaleX", "scaleY"
]

# blocks number and name
# (blocks 3, 7, 9, 11 and 13) are their respective block names rotated 90 derees clockwise
block_names = {
    '1': 'SquareHole',
    '2': 'RectFat',
    '3': 'RectFat',
    '4': 'SquareSmall',
    '5': 'SquareTiny',
    '6': 'RectTiny',
    '7': 'RectTiny',
    '8': 'RectSmall',
    '9': 'RectSmall',
    '10': 'RectMedium',
    '11': 'RectMedium',
    '12': 'RectBig',
    '13': 'RectBig'
}

# (blocks 3, 7, 9, 11 and 13) are their respective block names rotated 90 derees clockwise
block_is_rotated = {
    '1': False,
    '2': False,
    '3': True,
    '4': False,
    '5': False,
    '6': False,
    '7': True,
    '8': False,
    '9': True,
    '10': False,
    '11': True,
    '12': False,
    '13': True,
}

pig_types = {
    '1': "BasicSmall",
    '2': "BasicMedium"
}

pig_size = (0.5, 0.5)

# additional objects number and name
additional_objects = {'1': "TriangleHole", '2': "Triangle", '3': "Circle", '4': "CircleSmall"}

# additional objects number and size
additional_object_sizes = {'1': [0.82, 0.82], '2': [0.82, 0.82], '3': [0.8, 0.8], '4': [0.45, 0.45]}

bird_names = {
    '1': "BirdRed",
    '2': "BirdBlue",
    '3': "BirdYellow",
    '4': "BirdBlack",
    '5': "BirdWhite"
}

materials = ["wood", "stone", "ice"]
materials_color = ["brown", "grey", "blue"]

coordinate_round = 100000
resolution = 0.11 / 2


class ObjectType(Enum):
    Block = 1
    Platform = 2
    Pig = 3
    Slingshot = 4
    SpecialBlock = 5
    Bird = 5


def get_sizes():
    from tabulate import tabulate

    data = [[
        block_names[block_idx],
        block_size[0] / resolution,
        block_size[1] / resolution,
        round(block_size[0] / resolution),
        round(block_size[1] / resolution),
        block_is_rotated[block_idx]
    ] for block_idx, block_size in block_sizes.items()]

    print(tabulate(data, headers = ['block_name', 'x', 'y', 'rounded x', 'rounded y', 'Rotated']))


if __name__ == '__main__':
    get_sizes()
