import tensorflow as tf


# https://colab.research.google.com/drive/1xU_MJ3R8oj8YYYi-VI_WJTU3hD1OpAB7#scrollTo=rmTv61HFAv57
from generator.Gan.GanNetwork import GanNetwork
from util.NetworkTrainer import NetworkTrainer


def parse_tfr_element(element):
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
    score = content['score']
    raw_image = content['raw_image']

    # get our 'feature'-- our image -- and reshape it appropriately
    image = tf.io.parse_tensor(raw_image, out_type = tf.int16)
    image = tf.reshape(image, shape = [height, width, depth])
    return image


def get_dataset(filename):
    # create the dataset
    dataset = tf.data.TFRecordDataset(filename)

    # pass every single feature through our mapping function
    dataset = dataset.map(
        parse_tfr_element
    )

    return dataset


if __name__ == '__main__':

    dataset = get_dataset('../data/data.tfrecords')
    for sample in dataset.take(1):
        print(sample[0].shape)

    train_dataset = dataset.shuffle(buffer_size = 60000).batch(256)

    gan = GanNetwork()
    random_vec = gan.create_random_vector()
    output = gan.generator(random_vec)
    prescion = gan.discriminator(output)

    trainer = NetworkTrainer(dataset = train_dataset, model = gan)
    trainer.train()

    print(prescion)
