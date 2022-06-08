import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import tensorflow as tf
from tensorflow.keras import layers

# https://colab.research.google.com/drive/1xU_MJ3R8oj8YYYi-VI_WJTU3hD1OpAB7#scrollTo=rmTv61HFAv57

import data.LevelDataset
import generator.gan.GanNetwork
import util.NetworkTrainer

if __name__ == '__main__':
    dataset = data.LevelDataset.LevelDataset(filename = 'data/data.tfrecords')
    dataset.load_dataset()

    train_dataset = dataset.get_dataset()

    data_augmentation = tf.keras.Sequential([
        layers.RandomFlip("horizontal")
    ])

    gan = generator.gan.GanNetwork.GanNetwork(data_augmentation = data_augmentation)
    trainer = util.NetworkTrainer.NetworkTrainer(dataset = dataset, model = gan, epochs = 100)
    # trainer.load("20220607-153444")
    trainer.train()
