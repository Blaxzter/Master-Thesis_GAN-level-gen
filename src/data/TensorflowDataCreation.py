import json
import pickle

import numpy as np
import tensorflow as tf
from matplotlib import pyplot as plt

max_height = 86
max_width = 212


# Take from tensorflow gan tutorial
def _bytes_feature(value):
    """Returns a bytes_list from a string / byte."""
    if isinstance(value, type(tf.constant(0))):  # if value ist tensor
        value = value.numpy()  # get value of tensor
    return tf.train.Feature(bytes_list = tf.train.BytesList(value = [value]))


def _float_feature(value):
    """Returns a floast_list from a float / double."""
    return tf.train.Feature(float_list = tf.train.FloatList(value = [value]))


def _int64_feature(value):
    """Returns an int64_list from a bool / enum / int / uint."""
    return tf.train.Feature(int64_list = tf.train.Int64List(value = [value]))


def serialize_array(array):
    array = tf.io.serialize_tensor(array)
    return array


def pad_image_to_size(image_data):
    pad_left = int((max_width - image_data.shape[1]) / 2)
    pad_right = int((max_width - image_data.shape[1]) / 2)
    pad_top = max_height - image_data.shape[0]

    padded_img = np.pad(image_data, ((pad_top, 0), (pad_left, pad_right)), 'constant')

    # plt.imshow(padded_img)
    # plt.show()

    return padded_img.reshape((padded_img.shape[0], padded_img.shape[1], 1)).astype(dtype = np.int16)


def parse_single_data_example(data_example):
    # define the dictionary -- the structure -- of our single example

    meta_data = data_example['meta_data']
    game_data = data_example['game_data']
    img_data = data_example['img_data']

    padded_img_data = pad_image_to_size(img_data)

    data = {
        # Img data
        'height': _int64_feature(padded_img_data.shape[0]),
        'width': _int64_feature(padded_img_data.shape[1]),
        'depth': _int64_feature(padded_img_data.shape[2]),
        'raw_image': _bytes_feature(serialize_array(padded_img_data)),

        # level data from playing
        'cumulative_damage': _float_feature(game_data['cumulative_damage']),
        'initial_damage': _float_feature(game_data['initial_damage']),
        'is_stable': _int64_feature(game_data['is_stable']),
        'death': _int64_feature(game_data['death']),
        'birds_used': _int64_feature(game_data['birds_used']),
        'won': _int64_feature(game_data['won']),
        'score': _int64_feature(game_data['score']),

        # Meta data
        'level_height': _float_feature(meta_data.height),
        'level_width': _float_feature(meta_data.width),
        'pixel_height': _int64_feature(img_data.shape[0]),
        'pixel_width': _int64_feature(img_data.shape[1]),
        'block_amount': _int64_feature(meta_data.block_amount),
        'pig_amount': _int64_feature(meta_data.pig_amount),
        'platform_amount': _int64_feature(meta_data.platform_amount),
        'special_block_amount': _int64_feature(meta_data.special_block_amount),
    }

    # create an Example, wrapping the single features
    out = tf.train.Example(features = tf.train.Features(feature = data))

    return out


def create_tensorflow_data():
    with open('level_data.pickle', 'rb') as f:
        data_dict = pickle.load(f)

    record_file = 'data.tfrecords'
    with tf.io.TFRecordWriter(record_file) as writer:
        for date_name, data_example in data_dict.items():
            tf_example = parse_single_data_example(data_example)
            writer.write(tf_example.SerializeToString())


if __name__ == '__main__':
    create_tensorflow_data()
