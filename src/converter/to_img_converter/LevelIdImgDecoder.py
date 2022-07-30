import numpy as np

from converter.to_img_converter.DecoderUtils import recalibrate_blocks
from level import Constants
from level.Level import Level
from level.LevelElement import LevelElement
from level.LevelVisualizer import LevelVisualizer
from util.Config import Config


class LevelIdImgDecoder:

    def __init__(self):
        self.config = Config.get_instance()
        self.block_data = self.config.get_encoding_data(f"encoding_res_{Constants.resolution}")
        if type(self.block_data) is not str:
            self.resolution = self.block_data['resolution']
            del self.block_data['resolution']

        self.level_viz = LevelVisualizer()

    def decode_level(self, level_img):

        # Helper function that takes a img layer and creates
        # blocks based on the position of the pixel and the id
        def _create_elements_of_layer(img_layer, layer = -1):
            ret_elements = []
            used_blocks = np.unique(img_layer)

            for color_idx, material_idx in enumerate(used_blocks):
                if material_idx == 0:
                    continue
                current_img = img_layer == material_idx
                not_null = np.nonzero(current_img)
                for y, x in zip(not_null[0], not_null[1]):
                    block_typ = self.get_element_of_id_encoding(material_idx, layer = layer)
                    block_typ['x'] = x * Constants.resolution
                    block_typ['y'] = y * Constants.resolution * -1
                    ret_elements.append(block_typ)
            return ret_elements

        created_elements = []

        if len(level_img.shape) == 2:
            created_elements += _create_elements_of_layer(level_img, layer = -1)
        else:
            for layer in range(level_img.shape[-1]):
                created_elements += _create_elements_of_layer(level_img[:, :, layer], layer = layer)

        created_level_elements = []
        for element_idx, element in enumerate(created_elements):
            new_level_element = LevelElement(id = element_idx, **element)
            new_level_element.create_set_geometry()
            created_level_elements.append(
                new_level_element
            )

        created_level_elements = recalibrate_blocks(created_level_elements)

        return Level.create_level_from_structure(created_level_elements)

    def get_element_of_id_encoding(self, element_id, layer = -1):
        if layer < 0:
            material = int((element_id - 1) / 13)

            if element_id == 40:
                return dict(type = 'BasicSmall')
        else:
            material = layer
            if element_id == 14:
                return dict(type = 'BasicSmall')

        block_id = (element_id - 1) % 13

        block_attribute = dict(
            type = Constants.block_names[block_id + 1],
            material = Constants.materials[material],
            rotation = 90 if Constants.block_is_rotated[block_id + 1] else 0
        )

        return block_attribute
