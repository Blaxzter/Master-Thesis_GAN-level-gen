from xml.dom.minidom import parse, Document, Element

from level import Constants
from level.Level import Level
from level.LevelElement import LevelElement


class LevelReader:
    def __init__(self, path = "../data/"):
        self.level_doc: Document = parse(path)

    def parse_level(self) -> Level:
        ret_level = Level(self.level_doc)
        for level_part in ["Block", "Platform", "Pig"]:
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

if __name__ == '__main__':
    level_reader = LevelReader(path = "../data/converted_levels/NoRotation/level-05.xml")
    parse_level = level_reader.parse_level()
    print(f"Parsed Level: {parse_level} ")
    parse_level.print_elements(as_table = True)

    parse_level.normalize()
    parse_level.create_polygons()
    parse_level.separate_structures()

    parse_level.create_img()
