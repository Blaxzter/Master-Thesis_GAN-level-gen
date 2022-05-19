from xml.dom.minidom import parse, Document, Element

import numpy as np

from level import Constants
from level.Level import Level
from level.LevelElement import LevelElement

import matplotlib.pyplot as plt
import matplotlib.patches as patches

class LevelReader:
    def __init__(self, path = "../data/"):
        self.level_doc: Document = parse(path)

    def parse_level(self) -> Level:
        ret_level = Level(self.level_doc)
        for level_part in ["Block", "Pig", "Platform"]:
            elements: [Element] = self.level_doc.getElementsByTagName(level_part)
            for element in elements:
                element_attributes = dict()
                for attribute in Constants.attributes:
                    if attribute in element.attributes:
                        element_attributes[attribute] = element.attributes[attribute].value

                ret_level[level_part].append(
                    LevelElement(**element_attributes)
                )
        return ret_level

    def write_to_file(self, path):
        writer = open(path, 'w')
        self.level_doc.writexml(writer, indent=" ", addindent=" ", newl='')

    def create_img(self, level: Level):
        # Create figure and axes
        fig, ax = plt.subplots()

        min_x, min_y, max_x, max_y = (10000, 10000, -10000, -10000)

        element_list: [LevelElement] = level.create_element_list(blocks = True, pigs = True, platform = False)

        if level.structures is None:
            hsv = plt.get_cmap('Paired')
            colors = hsv(np.linspace(0, 0.8, len(element_list)))
        else:
            hsv = plt.get_cmap('brg')
            colors = hsv(np.linspace(0, 0.8, len(level.structures)))

        for idx, element in enumerate(element_list):

            min_x, min_y, max_x, max_y = min(min_x, element.x), min(min_y, element.y), max(max_x, element.x), max(max_y, element.y)

            bottom_left = element.get_bottom_left()
            width = element.size[0]
            height = element.size[1]
            # Create a Rectangle patch

            if level.structures is not None:
                idx = 0
                for structure in level.structures:
                    if element in structure:
                        current_color = colors[idx]
                        break
                    idx += 1
            else:
                current_color = colors[idx]

            rect = patches.Rectangle(bottom_left, width, height, linewidth = 1, edgecolor = current_color, facecolor = 'none')


            # Add the patch to the Axes
            ax.add_patch(rect)
            plt.text(element.x, element.y, str(element.id), color = current_color, fontsize = 12, ha = 'center',
                     va = 'center')

        plt.axis([min_x - 0.3, max_x + 0.3, min_y - 0.3, max_y + 0.3])
        fig.show()


if __name__ == '__main__':
    level_reader = LevelReader(path = "../data/converted_levels/NoRotation/level-06.xml")
    parse_level = level_reader.parse_level()


    parse_level.normalize()
    parse_level.create_polygons()
    parse_level.separate_structures()
    level_reader.create_img(parse_level)

    print(f"Parsed Level: {parse_level} ")

    parse_level.print_elements(as_table = True)
    #
    #
    # parse_level.create_img()
