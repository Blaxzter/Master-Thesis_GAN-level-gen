import os
from pathlib import Path
from xml.dom.minidom import parse, Document, Element

import matplotlib as mpl
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from loguru import logger

from level import Constants
from level.Constants import ObjectType
from level.Level import Level
from level.LevelCreator import create_basis_level_node
from level.LevelElement import LevelElement


class LevelReader:
    def __init__(self):
        pass

    def parse_level(self, path, blocks = True, pigs = True, platform = False) -> Level:
        level_doc: Document = parse(path)
        ret_level = Level(path, level_doc, blocks, pigs, platform)
        counter = 0
        for level_part in ["Block", "Pig", "Platform", "Bird"]:
            elements: [Element] = level_doc.getElementsByTagName(level_part)
            for element in elements:
                element_attributes = dict()
                for attribute in Constants.attributes:
                    if attribute in element.attributes:
                        element_attributes[attribute] = element.attributes[attribute].value

                ret_level[level_part].append(
                    LevelElement(id = counter, **element_attributes)
                )
                counter += 1
        slingshot = level_doc.getElementsByTagName("Slingshot")[0]
        ret_level.slingshot = LevelElement(id = counter, type = "Slingshot", material = None,
                                           x = slingshot.attributes['x'].value, y = slingshot.attributes['y'].value)

        return ret_level

    def write_level_to_file(self, ret_level: Level, new_level_name = None):
        level_name = ret_level.path if new_level_name is None else new_level_name
        self.write_xml_file(ret_level.original_doc, level_name)

    def write_xml_file(self, xml_file, name):
        writer = open(name, 'w')
        xml_file.writexml(writer, indent = " ", addindent = " ", newl = '\n')

    def create_level_from_structure(self, structure: [LevelElement], level: Level, move_to_ground: bool = True):
        doc, level_node = create_basis_level_node(level)

        data = None
        if move_to_ground:
            data = Level.calc_structure_dimensions(structure, use_original = True)

        game_objects = doc.createElement('GameObjects')
        for level_element in structure:
            block_name = 'Block'
            if level_element.object_type == ObjectType.Platform:
                block_name = 'Platform'
            elif level_element.object_type == ObjectType.Pig:
                block_name = 'Pig'

            current_element_doc = doc.createElement(block_name)
            current_element_doc.setAttribute("type", str(level_element.type))
            current_element_doc.setAttribute("material", str(level_element.material))

            current_element_doc.setAttribute("x", str(level_element.original_x))
            if move_to_ground:
                current_element_doc.setAttribute("y", str(level_element.original_y - (Constants.absolute_ground - data[1])))
            else:
                current_element_doc.setAttribute("y", str(level_element.original_y))

            current_element_doc.setAttribute("rotation", str(level_element.rotation))

            if level_element.object_type == ObjectType.Platform:
                if level_element.size[0] != 0.62:
                    current_element_doc.setAttribute("scaleX", str(level_element.size[0] * (1 / 0.62)))
                if level_element.size[1] != 0.62:
                    current_element_doc.setAttribute("scaleY", str(level_element.size[1] * (1 / 0.62)))

            game_objects.appendChild(current_element_doc)

        level_node.appendChild(game_objects)
        doc.appendChild(level_node)
        return doc

    def create_img_of_structure(self, structure: [LevelElement], use_grid = True, add_dots = False, element_ids = True, ax = None):

        show = False
        if ax is None:
            show = True
            fig, ax = plt.subplots(dpi = 300)

        hsv = plt.get_cmap('Paired')
        colors = hsv(np.linspace(0, 0.8, len(structure)))

        # Add Forms to img
        for idx, element in enumerate(structure):

            bottom_left = element.get_bottom_left()
            width = element.size[0]
            height = element.size[1]
            current_color = colors[idx]

            # Create the matplotlib patch for each element type
            new_patch = self.create_new_patch(ax, bottom_left, current_color, element, height, width)

            # Add the patch to the Axes
            ax.add_patch(new_patch)

            # If block ids should be printed add text at the center of the element
            if element_ids:
                plt.text(element.x, element.y, str(element.id), color = "black", fontsize = 5, ha = 'center', va = 'center')

        if use_grid or add_dots:
            min_x, min_y, max_x, max_y = Level.calc_structure_dimensions(structure)

        if add_dots:
            x_cords = np.arange(min_x + Constants.resolution / 2, max_x - Constants.resolution, Constants.resolution)
            y_cords = np.arange(min_y + Constants.resolution / 2, max_y - Constants.resolution, Constants.resolution)
            XX, YY = np.meshgrid(x_cords, y_cords)
            plt.scatter(XX, YY, s = 4)

        if use_grid:
            ax.set_xticks(np.arange(min_x, max_x, Constants.resolution))
            ax.set_yticks(np.arange(min_y, max_y, Constants.resolution))
            plt.tick_params(axis = 'both', which = 'both', grid_alpha = 0, grid_color = "white")
            plt.grid(alpha = 0.2)

        if show:
            plt.axis('scaled')
            fig.show()
            plt.close()

    def create_img(self, level: Level, use_grid = True, add_dots = True, element_ids = True, write_to_file = None,
                   ax = None):
        # Create figure and axes
        show = False
        if ax is None:
            show = True
            fig, ax = plt.subplots(dpi = 300)

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
            new_patch = self.create_new_patch(ax, bottom_left, current_color, element, height, width)

            # Add the patch to the Axes
            ax.add_patch(new_patch)

            # If block ids should be printed add text at the center of the element
            if element_ids:
                plt.text(element.x, element.y, str(element.id),
                         color = "black", fontsize = 5, ha = 'center', va = 'center')

        if use_grid or add_dots:
            min_x, min_y, max_x, max_y = Level.calc_structure_dimensions(element_list)

        if add_dots:
            x_cords = np.arange(min_x + Constants.resolution / 2, max_x - Constants.resolution, Constants.resolution)
            y_cords = np.arange(min_y + Constants.resolution / 2, max_y - Constants.resolution, Constants.resolution)
            XX, YY = np.meshgrid(x_cords, y_cords)
            plt.scatter(XX, YY, s = 4)

        if use_grid:
            ax.set_xticks(np.arange(min_x, max_x, Constants.resolution))
            ax.set_yticks(np.arange(min_y, max_y, Constants.resolution))
            plt.tick_params(axis = 'both', which = 'both', grid_alpha = 0, grid_color = "white")
            plt.grid(alpha = 0.2)

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

    def create_new_patch(self, ax, bottom_left, current_color, element, height, width):
        new_patch = self.get_patch(ax, bottom_left, element, height, width)
        new_patch.set_linewidth(1)
        new_patch.set_edgecolor(current_color)
        if "Basic" not in element.type:
            new_patch.set_facecolor('none')
        else:
            new_patch.set_facecolor(current_color)
        return new_patch

    def get_patch(self, ax, bottom_left, element, height, width):
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
        return new_patch

    def visualize_level_img(self, parsed_level: Level, per_structure = False, ax = None, dot_version = False):

        # Per structure and extern visualization not supported
        if ax is not None and per_structure:
            raise Exception("Not supported")

        level_representations = parsed_level.create_img(per_structure = per_structure, dot_version = dot_version)

        show = False
        if ax is None:
            show = True
            if len(level_representations) == 1:
                fig, ax = plt.subplots(1, 1, dpi = 300)
            else:
                fig, ax = plt.subplots(
                    int(len(level_representations) / 2), int(len(level_representations) / 2), dpi = 300)

        if len(level_representations) == 1:
            ax.imshow(level_representations[0])
        else:
            for level_img, cax in zip(level_representations, ax.flatten()):
                cax.imshow(level_img)

        if len(level_representations) == 1:
            plt.title(f"{parsed_level} method: {'dots' if dot_version else 'math'}", fontsize = 6)
        else:
            plt.suptitle(f"{parsed_level} method: {'dots' if dot_version else 'math'}", fontsize = 6)

        plt.axis('scaled')

        if show:
            plt.show()


if __name__ == '__main__':
    level = "../data/converted_levels/NoRotation/level-34.xml"

    for level in sorted(Path("../data/train/generated/").glob('*.xml')):
        level_reader = LevelReader()
        parse_level = level_reader.parse_level(str(level), blocks = True, pigs = True, platform = True)
        parse_level.filter_slingshot_platform()

        parse_level.normalize()
        parse_level.create_polygons()
        structures = parse_level.separate_structures()

        level_reader.create_img(level = parse_level, use_grid = True, add_dots = False, element_ids = True)

        level_counter = 0
        for idx, structure in enumerate(structures):
            meta_data = Level.calc_structure_meta_data(structure)
            if meta_data.total == 1:
                continue
            struct_doc = level_reader.create_level_from_structure(
                structure = structure,
                level = parse_level,
                move_to_ground = False
            )
            level_reader.create_img_of_structure(structure, use_grid = True, element_ids = True)
            level_reader.write_xml_file(struct_doc, f'../data/train/structures/level-0{level_counter + 4}.xml')
            level_counter += 1

        # logger.debug(f"Parsed Level: {parse_level} ")

        # parse_level.print_elements(as_table = True)
        # level_reader.visualize_level_img(parse_level, per_structure = True, dot_version = True)
        break
