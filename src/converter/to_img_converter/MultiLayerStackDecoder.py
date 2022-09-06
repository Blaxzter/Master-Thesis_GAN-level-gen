from scipy import ndimage

from level import Constants
from level.LevelElement import LevelElement


class MultiLayerStackDecoder:

    def __init__(self):
        pass

    def preprocess_layer(self, layer):
        pass

    def decode(self):
        # Move each possible blocks like a convolution over the block mush
        # for every position store the overlap 1 = full overlap 0 = no overlap
        # sort by overlap with mush
        # Select top element, filter elements that overlap, repeat
        # If no element are over the coverage is high enough return with selected
        # Otherwise go with next block
        pass


    @staticmethod
    def create_level_elements(blocks, pig_position):
        ret_level_elements = []
        block_idx = 0
        for block_idx, block in enumerate(blocks):
            block_attribute = dict(
                type = block['block']['name'],
                material = Constants.materials[block['material'] - 1],
                x = block['position'][1] * Constants.resolution,
                y = block['position'][0] * Constants.resolution,
                rotation = 90 if block['block']['rotated'] else 0
            )
            element = LevelElement(id = block_idx, **block_attribute)
            element.create_set_geometry()
            ret_level_elements.append(element)
        block_idx += 1

        for pig_idx, pig in enumerate(pig_position):
            pig_attribute = dict(
                type = "BasicSmall",
                material = None,
                x = pig[1] * Constants.resolution,
                y = pig[0] * Constants.resolution,
                rotation = 0
            )
            element = LevelElement(id = pig_idx + block_idx, **pig_attribute)
            element.create_set_geometry()
            ret_level_elements.append(element)
        return ret_level_elements