import glob
from typing import List, AnyStr


def read_all_files():
    files = glob.glob('./converted_levels/**/*.xml', recursive = True)
    print(files)
    return files


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


fix_faulty_xml()
