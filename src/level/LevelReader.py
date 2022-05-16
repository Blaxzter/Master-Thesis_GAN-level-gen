from xml.dom.minidom import parse, Document, Element

from level import Constants
from level.Level import Level


class LevelReader:
    def __init__(self, path = "../data/"):
        self.level_doc: Document = parse(path)

    def parse_level(self) -> Level:
        ret_level = Level()
        for level_part in ["Block", "Platform", "Pig", "Bird"]:
            elements: [Element] = self.level_doc.getElementsByTagName(level_part)
            for element in elements:
                element_attributes = dict()
                for attribute in Constants.attributes:
                    if attribute in element.attributes:
                        element_attributes[attribute] = element.attributes[attribute].value

                ret_level[level_part].append(
                    element_attributes
                )
        return ret_level


if __name__ == '__main__':
    level_reader = LevelReader(path = "../data/converted_levels/Benchmark converted levels 1 (poached eggs 1)/level-07.xml")
    parse_level = level_reader.parse_level()
    print(f"Parsed Level: {parse_level} ")

    parse_level.create_img()
