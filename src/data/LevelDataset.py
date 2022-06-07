import numpy as np
import tensorflow as tf


class LevelDataset:

    def __init__(self, filename = './data.tfrecords', batch_size = 265, buffer_size = 60000):
        self.filename = filename
        self.dataset = None
        self.batch_size = batch_size
        self.buffer_size = buffer_size

        self.norm_layer = None
        self.reverse_norm_layer = None

    def get_dataset(self):
        return self.dataset.shuffle(buffer_size = self.buffer_size).batch(self.batch_size)

    def load_dataset(self):
        # Load the dataset from the tf record file
        self.dataset = tf.data.TFRecordDataset(self.filename)

        # pass every single feature through our mapping function
        self.dataset = self.dataset.map(self.parse_tfr_element)
        self.dataset = self.normalize()

    def normalize(self):
        images = np.concatenate([x for x, y in self.dataset], axis = 0)
        self.norm_layer = tf.keras.layers.Rescaling(1. / images.max())
        self.reverse_norm_layer = tf.keras.layers.Rescaling(images.max())
        return self.dataset.map(lambda x, y: (self.norm_layer(x), y))

    def parse_tfr_element(self, element):
        # use the same structure as above; it's kinda an outline of the structure we now want to create
        data = {
            # Img data
            'height': tf.io.FixedLenFeature([], tf.int64),
            'width': tf.io.FixedLenFeature([], tf.int64),
            'depth': tf.io.FixedLenFeature([], tf.int64),
            'raw_image': tf.io.FixedLenFeature([], tf.string),

            # level data from playing
            'cumulative_damage': tf.io.FixedLenFeature([], tf.float32),
            'initial_damage': tf.io.FixedLenFeature([], tf.float32),
            'is_stable': tf.io.FixedLenFeature([], tf.int64),
            'death': tf.io.FixedLenFeature([], tf.int64),
            'birds_used': tf.io.FixedLenFeature([], tf.int64),
            'won': tf.io.FixedLenFeature([], tf.int64),
            'score': tf.io.FixedLenFeature([], tf.int64),

            # Meta data
            'level_height': tf.io.FixedLenFeature([], tf.float32),
            'level_width': tf.io.FixedLenFeature([], tf.float32),
            'pixel_height': tf.io.FixedLenFeature([], tf.int64),
            'pixel_width': tf.io.FixedLenFeature([], tf.int64),
            'block_amount': tf.io.FixedLenFeature([], tf.int64),
            'pig_amount': tf.io.FixedLenFeature([], tf.int64),
            'platform_amount': tf.io.FixedLenFeature([], tf.int64),
            'special_block_amount': tf.io.FixedLenFeature([], tf.int64),
        }

        content = tf.io.parse_single_example(element, data)

        height = content['height']
        width = content['width']
        depth = content['depth']
        raw_image = content['raw_image']

        data_dict = content
        del data_dict['height']
        del data_dict['width']
        del data_dict['depth']
        del data_dict['raw_image']

        # get our 'feature'-- our image -- and reshape it appropriately
        image = tf.io.parse_tensor(raw_image, out_type = tf.int16)
        image = tf.reshape(image, shape = [height, width, depth])
        tf.cast(image, tf.float32)
        return image, data_dict
