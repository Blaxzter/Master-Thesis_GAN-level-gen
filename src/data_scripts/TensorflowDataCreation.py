import os
import pickle
import sys

import numpy as np
import tensorflow as tf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from converter.to_img_converter.LevelImgEncoder import LevelImgEncoder
from util.Config import Config

# max_height = 86 + 2
# max_width = 212

# max_height = 99 + 1
# max_width = 110 + 2

max_height = 99 + 1
max_width = 115 + 1

max_height = 128
max_width = 128


create_multi_dim_img = True

# Take from tensorflow simple_gan tutorial
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

    if pad_left + image_data.shape[1] + pad_right < max_width:
        pad_right += 1

    padded_img = np.pad(image_data, ((pad_top, 0), (pad_left, pad_right)), 'constant')

    # plt.imshow(padded_img)
    # plt.show()

    return padded_img.reshape((padded_img.shape[0], padded_img.shape[1], 1)).astype(dtype = np.int16)


def parse_single_data_example(data_example):
    # define the dictionary -- the structure -- of our single example

    meta_data = data_example['meta_data']
    img_data = data_example['img_data']
    game_data = data_example['game_data'] if 'game_data' in data_example else None

    padded_img_data = pad_image_to_size(img_data)

    if create_multi_dim_img:
        new_img = LevelImgEncoder.create_multi_dim_img_from_picture(padded_img_data)
    else:
        new_img = padded_img_data

    data = {
        # Img data
        'height': _int64_feature(new_img.shape[0]),
        'width': _int64_feature(new_img.shape[1]),
        'depth': _int64_feature(new_img.shape[2]),
        'raw_image': _bytes_feature(serialize_array(new_img)),

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

    if game_data is not None:
        # level data from playing
        data['cumulative_damage'] = _float_feature(game_data['cumulative_damage'])
        data['initial_damage'] = _float_feature(game_data['initial_damage'])
        data['is_stable'] = _int64_feature(game_data['is_stable'])
        data['death'] = _int64_feature(game_data['death'])
        data['birds_used'] = _int64_feature(game_data['birds_used'])
        data['won'] = _int64_feature(game_data['won'])
        data['score'] = _int64_feature(game_data['score'])

    # create an Example, wrapping the single features
    out = tf.train.Example(features = tf.train.Features(feature = data))

    return out


def create_tensorflow_data():
    config = Config.get_instance()

    data_pickle = config.get_pickle_file(f"new_encoding_unified.pickle")
    with open(data_pickle, 'rb') as f:
        data_dict = pickle.load(f)

    record_file = config.get_tf_records(dataset_name = f'new_encoding_multilayer_unified_{max_width}_{max_height}')
    with tf.io.TFRecordWriter(record_file) as writer:
        for date_name, data_example in data_dict.items():
            tf_example = parse_single_data_example(data_example)
            writer.write(tf_example.SerializeToString())


if __name__ == '__main__':
    create_tensorflow_data()
