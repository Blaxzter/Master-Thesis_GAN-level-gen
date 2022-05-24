import os

from pathlib import Path

from xml.dom.minidom import parse, Document, Element

import numpy as np

from level import Constants
from level.Level import Level
from level.LevelElement import LevelElement

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches


class LevelReader:
    def __init__(self, path = "../data/"):
        self.path = path
        self.level_doc: Document = parse(path)

    def parse_level(self, path, blocks = True, pigs = True, platform = False) -> Level:
        ret_level = Level(path, self.level_doc, blocks, pigs, platform)
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
        slingshot = self.level_doc.getElementsByTagName("Slingshot")[0]
        ret_level.slingshot = LevelElement(
            "Slingshot", None, slingshot.attributes['x'].value, slingshot.attributes['y'].value, None)

        return ret_level

    def write_to_file(self, path):
        writer = open(path, 'w')
        self.level_doc.writexml(writer, indent = " ", addindent = " ", newl = '')

    def create_img(self, level: Level, use_grid = True, add_dots = True, element_ids = True, write_to_file = None, ax = None):
        # Create figure and axes
        show = False
        if ax is None:
            show = True
            fig, ax = plt.subplots()

        element_list: [LevelElement] = level.get_used_elements()

        if level.structures is None:
            hsv = plt.get_cmap('Paired')
            colors = hsv(np.linspace(0, 0.8, len(element_list)))
        else:
            hsv = plt.get_cmap('brg')
            colors = hsv(np.linspace(0, 0.8, len(level.structures)))

        # Add Forms to img
        for idx, element in enumerate(element_list):

            bottom_left = element.get_bottom_left()
            width = element.size[0]
            height = element.size[1]
            # Create a Rectangle patch

            # Define the color of the element, if there are strucutres then the stucture color else random
            current_color = "Black"
            if level.structures is not None:
                idx = 0
                for structure in level.structures:
                    if element in structure:
                        current_color = colors[idx]
                        break
                    idx += 1
            else:
                current_color = colors[idx]

            # Create the matplotlib patch for each element type
            if "Basic" in element.type or "Circle" in element.type:
                new_patch = patches.Circle((element.x, element.y), radius = element.size[0] / 2)
            elif "Platform" in element.type:
                new_patch = patches.Rectangle(bottom_left, width, height)
                platform_transform = mpl.transforms.Affine2D().rotate_deg_around(element.x, element.y,
                                                                                 element.rotation) + ax.transData
                new_patch.set_transform(platform_transform)
            elif "Triangle" in element.type:
                new_patch = patches.Polygon(np.asarray(
                    [bottom_left, bottom_left + np.array([width, 0]), bottom_left + np.array([width, height])]),
                                            closed = True)
                triangle_transform = mpl.transforms.Affine2D().rotate_deg_around(element.x, element.y,
                                                                                 element.rotation - 90) + ax.transData
                new_patch.set_transform(triangle_transform)
            else:
                new_patch = patches.Rectangle(bottom_left, width, height)

                # Set meta data color
            new_patch.set_linewidth(1)
            new_patch.set_edgecolor(current_color)
            if "Basic" not in element.type:
                new_patch.set_facecolor('none')
            else:
                new_patch.set_facecolor(current_color)

            # Add the patch to the Axes
            ax.add_patch(new_patch)

            # If block ids should be printed add text at the center of the element
            if element_ids:
                plt.text(element.x, element.y, str(element.id),
                         color = "black", fontsize = 12, ha = 'center', va = 'center')

        if use_grid or add_dots:
            min_x, min_y, max_x, max_y = level.calc_level_metadata(element_list)

        if add_dots:
            x_cords = np.arange(min_x + Constants.smallest_grid_size / 2, max_x - Constants.smallest_grid_size, Constants.smallest_grid_size)
            y_cords = np.arange(min_y + Constants.smallest_grid_size / 2, max_y - Constants.smallest_grid_size, Constants.smallest_grid_size)
            XX, YY = np.meshgrid(x_cords, y_cords)
            plt.scatter(XX, YY, s = 4)

        if use_grid:
            ax.set_xticks(np.arange(min_x, max_x, Constants.smallest_grid_size))
            ax.set_yticks(np.arange(min_y, max_y, Constants.smallest_grid_size))
            plt.tick_params(axis = 'both', which = 'both', bottom = 'off', top = 'off', labelbottom = 'off',
                            right = 'off', left = 'off', labelleft = 'off')
            plt.grid()

        if show:
            plt.title(level.path)
            plt.axis('scaled')

            if write_to_file is not None:
                imgs_folder = f'../imgs/{write_to_file + "/" if len(write_to_file) > 0 else ""}'
                if not Path(imgs_folder).is_dir():
                    os.mkdir(imgs_folder)
                plt.savefig(f'{imgs_folder}{str(level.path)[:-4]}.png')
            else:
                fig.show()

            plt.close()

    def visualize_level_img(self, parsed_level: Level, per_structure = False, ax = None):
        level_imgs = parsed_level.create_img(per_structure = per_structure)

        show = False
        if ax is None:
            show = True
            fig, ax = plt.subplots()

        if per_structure and ax is not list:
            raise Exception("Wiu wiu")

        for level_img in level_imgs:
            ax.imshow(level_img)
            if show:
                plt.show()


if __name__ == '__main__':
    level = "../data/converted_levels/NoRotation/level-34.xml"

    # for level in sorted(Path("../data/converted_levels/NoRotation/").glob('*.xml')):
    level_reader = LevelReader(str(level))
    parse_level = level_reader.parse_level(str(level), blocks = True, pigs = True, platform = True)
    parse_level.filter_slingshot_platform()

    parse_level.normalize()
    parse_level.create_polygons()
    parse_level.separate_structures()

    #level_reader.create_img(
    #       level = parse_level, use_grid = True, add_dots = False, element_ids = True
    #)

    print(f"Parsed Level: {parse_level} ")

    # parse_level.print_elements(as_table = True)
    level_reader.visualize_level_img(parse_level, per_structure = False)
