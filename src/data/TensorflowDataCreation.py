import pickle
import tensorflow as tf

# Take from tensorflow gan tutorial
def _bytes_feature(value):
    """Returns a bytes_list from a string / byte."""
    if isinstance(value, type(tf.constant(0))):  # if value ist tensor
        value = value.numpy()  # get value of tensor
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def _float_feature(value):
    """Returns a floast_list from a float / double."""
    return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))


def _int64_feature(value):
    """Returns an int64_list from a bool / enum / int / uint."""
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))


def serialize_array(array):
    array = tf.io.serialize_tensor(array)
    return array

def parse_single_data_example(data_example):
    # define the dictionary -- the structure -- of our single example

    meta_data = data_example['meta_data']
    game_data = data_example['game_data']
    img_data = data_example['img_data']

    data = {
        'height': _int64_feature(img_data.shape[0]),
        'width': _int64_feature(img_data.shape[1]),
        'depth': _int64_feature(img_data.shape[2]),
        'raw_image': _bytes_feature(serialize_array(img_data)),
    }

    #create an Example, wrapping the single features
    out = tf.train.Example(features=tf.train.Features(feature=data))

    return out

def create_tensorflow_data():
    with open('level_data_with_screenshot.pickle', 'rb') as f:
        data = pickle.load(f)

    record_file = 'data.tfrecords'
    with tf.io.TFRecordWriter(record_file) as writer:
        for filename, label in image_labels.items():
            image_string = open(filename, 'rb').read()
            tf_example = image_example(image_string, label)
            writer.write(tf_example.SerializeToString())
