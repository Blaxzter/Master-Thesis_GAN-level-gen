import os
import pickle
from collections import defaultdict

import cv2 as cv
import imageio
import matplotlib.pyplot as plt
import numpy as np
from loguru import logger
from tqdm.auto import tqdm

from util.Config import Config

upper_bound = None  # 96
lower_bound = None  # 337
left_bound = None  # 607
right_bound = None  # 1186

video_duration = 15

def get_rectangle(img):
    imgray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ret, thresh = cv.threshold(imgray, 254, 255, 0)
    contours, hierarchy = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    big_conts = list(sorted(map(lambda cont: (cv.contourArea(cont), cont), contours), key = lambda x: x[0]))[::-1][1:3]

    more_left = 0 if min(big_conts[0][1][:, :, 0:1]).item() > min(big_conts[1][1][:, :, 0:1]).item() else 1

    cords = big_conts[more_left][1]

    left_bound, right_bound, upper_bound, lower_bound = \
        (min(cords[:, :, 0:1]).item(), max(cords[:, :, 0:1]).item(), min(cords[:, :, 1:2]).item(), max(cords[:, :, 1:2]).item())

    logger.debug(f"Found Cords: left_bound {left_bound}, right_bound {right_bound}, upper_bound {upper_bound}, lower_bound {lower_bound},")

    return left_bound, right_bound, upper_bound, lower_bound


def create_pickle_data(event_filename, output_dir, run_name):
    data_file = config.get_run_data(run_name)
    if os.path.isfile(data_file):
        logger.debug(f"Pickle file {data_file} already exists")
        return

    import tensorflow as tf
    from tensorflow.core.util import event_pb2
    assert (os.path.isdir(output_dir))

    data_set = tf.data.TFRecordDataset(event_filename)
    serialized = list(map(event_pb2.Event.FromString, map(lambda x: x.numpy(), data_set)))

    data = defaultdict(dict)
    progress_bar = tqdm(total = len(serialized))

    def extract_data(element):
        global upper_bound, lower_bound, left_bound, right_bound
        for value in element.summary.value:
            if value.metadata.plugin_data.plugin_name == 'scalars':
                data[value.tag][element.step] = \
                    tf.io.decode_raw(value.tensor.tensor_content, tf.float32).numpy().item()

            elif value.metadata.plugin_data.plugin_name == 'images':
                s = value.tensor.string_val[2]  # first elements are W and H
                tf_img = tf.image.decode_image(s)  # [H, W, C]
                np_img = tf_img.numpy()

                if upper_bound is None:
                    left_bound, right_bound, upper_bound, lower_bound = get_rectangle(np_img)

                data['image'][element.step] = np_img[upper_bound:lower_bound, left_bound:right_bound]
        progress_bar.update()

    # for data in serialized:
    #     extract_data(data)

    np.vectorize(extract_data)(serialized)

    img_amount = len(data['image'])

    imageio.mimsave(f'{output_dir}/{run_name}.mp4', data['image'].values(), fps = img_amount // video_duration)

    last_img = list(data['image'].values())[-1]
    del data['image']

    data['image'] = last_img
    data_file = config.get_run_data(run_name)
    with open(data_file, 'wb') as handle:
        pickle.dump(data, handle, protocol = pickle.HIGHEST_PROTOCOL)


def create_run_img(run_name):
    data_file = config.get_run_data(run_name)
    if not os.path.isfile(data_file):
        logger.debug(f"Pickle file {data_file} doesn't exists")
        return

    with open(data_file, 'rb') as f:
        data = pickle.load(f)

    fig, axd = plt.subplot_mosaic([['generator_loss', 'discriminator_loss', 'img', 'img'],
                                   ['real_prediction', 'fake_prediction', 'img', 'img']],
                                  figsize = (14, 6))

    for name, c_data in data.items():
        if name == 'image':
            continue

        axd[name].plot(c_data.keys(), c_data.values())
        axd[name].set_title(name)

    axd['img'].imshow(data['image'])
    axd['img'].set_title("Last generated img")

    fig.suptitle(run_name)

    plt.tight_layout()
    plt.show()


def create_wgan_run_img(run_name):
    data_file = config.get_run_data(run_name)
    if not os.path.isfile(data_file):
        logger.debug(f"Pickle file {data_file} doesn't exists")
        return

    with open(data_file, 'rb') as f:
        data = pickle.load(f)

    fig, axd = plt.subplot_mosaic([['generator_loss', 'discriminator_loss', 'img', 'img'],
                                   ['real_prediction', 'fake_prediction', 'img', 'img']],
                                  figsize = (14, 6))

    for name, c_data in data.items():
        if name == 'image':
            continue

        axd[name].plot(c_data.keys(), c_data.values())
        axd[name].set_title(name)

    axd['img'].imshow(data['image'])
    axd['img'].set_title("Last generated img")

    fig.suptitle(run_name)

    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    config: Config = Config.get_instance()
    img_folder = config.get_img_path("generated")
    log_file, run_name = config.get_log_file("events.out.tfevents.1656354301.ubuntu.474168.0.v2")

    logger.debug(f'Extract data: run_name: {run_name}, log_file: {log_file}')

    create_pickle_data(log_file, img_folder, run_name)
    create_run_img(run_name)
