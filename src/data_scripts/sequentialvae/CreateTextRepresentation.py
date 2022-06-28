
from tqdm import tqdm
import os
from glob import glob
import shutil

from data_scripts.sequentialvae.xml2text import xml2txt
from util.Config import Config


def main():
    config = Config.get_instance()
    orig_level_folder = config.get_data_train_path(folder = 'generated/single_structure')
    train_out_file = config.get_text_data('train')

    converter = xml2txt(orig_level_folder)
    train_data, remove_file_list = converter.xml2vector(True)
    for i, data in enumerate(train_data):
        data_ = []
        for d in data:
            if sum(d) == 0:
                break
            data_.append(d)
        train_data[i] = data_

    with open(train_out_file, "w") as f:
        for train_d in tqdm(train_data):
            train_d_ = ""
            for d in train_d:
                d = list(map(str, d))
                c = " ".join(d)
                train_d_ += c + "  "
            f.write(str(train_d_)+"\n")


def remove_file():
    converter = xml2txt.xml2txt("../../../IratusAves/levels")
    train_data, remove_file_list = converter.xml2vector(True)
    print(len(train_data))
    print(remove_file_list)
    file_list = glob("../../../IratusAves/levels/*")
    save_file_list = list(set(file_list) - set(remove_file_list))
    for file_name in save_file_list:
        shutil.copy(file_name, "save_level/"+ os.path.basename(file_name))

if __name__ == "__main__":
    main()
