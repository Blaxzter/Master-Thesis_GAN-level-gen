import os
import sys
import tensorflow as tf
from matplotlib import pyplot as plt
from tensorflow.keras import layers


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from util.Config import Config
from data_scripts.LevelDataset import LevelDataset
from generator.gan.GanNetwork import GanNetwork
from util.NetworkTrainer import NetworkTrainer

if __name__ == '__main__':

    with tf.device('/GPU:0'):
        config = Config.get_instance()
        print(str(config))

        dataset = LevelDataset(dataset_name = "raster_single_layer")
        dataset.load_dataset()

        train_dataset = dataset.get_dataset()

        data_augmentation = tf.keras.Sequential([
            layers.RandomFlip("horizontal")
        ])

        gan = GanNetwork(data_augmentation = data_augmentation)
        trainer = NetworkTrainer(run_name = "simple_gan", dataset = dataset, model = gan, epochs = 500)
        # trainer.load(run_name = "simple_gan", checkpoint_date = "20220607-153444")
        # img = gan.create_img()
        # plt.imshow(img)
        # plt.show()

        trainer.train()
