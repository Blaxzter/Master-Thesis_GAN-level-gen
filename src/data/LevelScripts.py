import glob
from typing import List, AnyStr
from xml.dom.minidom import parse, Document, Node

from level.LevelReader import LevelReader


def read_all_files():
    files = glob.glob('./converted_levels/**/*.xml', recursive = True)

    return sorted(files)


def utf16_to_utf8():
    files = read_all_files()

    for file_name in files:
        with open(file_name, encoding = 'utf-8', mode = "r+") as file:
            content = file.read()
            rep_content = content.replace("utf-16", "utf-8")
            file.seek(0)
            file.write(rep_content)
            file.truncate()


def fix_faulty_xml():
    files = read_all_files()

    for file_name in files:
        with open(file_name, encoding = 'utf-8', mode = "r+") as file:
            lines = file.readlines()
            for idx, line in enumerate(lines):
                if 'Camera' in line or 'Slingshot' in line:
                    lines[idx] = line.replace('">', '"/>')
            file.seek(0)
            file.writelines(lines)


def filter_for_rotation():
    files = read_all_files()
    level_counter = 0

    for idx, file_name in enumerate(files):
        level_reader = LevelReader(file_name)
        level = level_reader.parse_level(file_name)
        if not level.contains_od_rotation():

            node = level_reader.level_doc.getElementsByTagName("Level")
            name_element = level_reader.level_doc.createElement("PrevLevelName")
            name_element.setAttribute("name", file_name)
            node[0].appendChild(name_element)

            new_level_idx = '0' + str(level_counter + 5) if len(str(level_counter + 5)) == 1 else level_counter + 5
            new_level_name = f"./converted_levels/NoRotation/level-{new_level_idx}.xml"
            level_reader.write_to_file(new_level_name)
            level_counter += 1

        print(f"Level contains od rotation: {file_name} \n")


if __name__ == '__main__':
    filter_for_rotation()
