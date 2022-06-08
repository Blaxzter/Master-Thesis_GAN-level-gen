import os
import sys
import tensorflow as tf
from tensorflow.keras import layers

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from data_scripts.LevelDataset import LevelDataset
from generator.gan.GanNetwork import GanNetwork
from util.NetworkTrainer import NetworkTrainer

if __name__ == '__main__':
    dataset = LevelDataset(dataset_name = "raster_single_layer")
    dataset.load_dataset()

    train_dataset = dataset.get_dataset()

    data_augmentation = tf.keras.Sequential([
        layers.RandomFlip("horizontal")
    ])

    gan = GanNetwork(data_augmentation = data_augmentation)
    trainer = NetworkTrainer(dataset = dataset, model = gan, epochs = 100)
    trainer.load("20220607-153444")
    # trainer.train()
