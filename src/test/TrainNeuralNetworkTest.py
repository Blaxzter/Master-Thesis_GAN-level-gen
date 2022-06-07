import numpy as np
import tensorflow as tf
from tensorflow.keras import layers

# https://colab.research.google.com/drive/1xU_MJ3R8oj8YYYi-VI_WJTU3hD1OpAB7#scrollTo=rmTv61HFAv57
from matplotlib import pyplot as plt

from data.LevelDataset import LevelDataset
from generator.gan.GanNetwork import GanNetwork
from util.NetworkTrainer import NetworkTrainer


if __name__ == '__main__':

    dataset = LevelDataset(filename = '../data/data.tfrecords')
    dataset.load_dataset()

    train_dataset = dataset.get_dataset()

    data_augmentation = tf.keras.Sequential([
        layers.RandomFlip("horizontal")
    ])

    gan = GanNetwork(data_augmentation = data_augmentation)
    trainer = NetworkTrainer(dataset = dataset, model = gan, epochs = 100)
    # trainer.load("20220607-153444")
    trainer.train()
