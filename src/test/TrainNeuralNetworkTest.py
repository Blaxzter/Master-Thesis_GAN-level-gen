import os
import sys

import numpy as np
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

        dataset = LevelDataset(dataset_name = "raster_single_layer", batch_size = 32)
        dataset.load_dataset()

        data_augmentation = tf.keras.Sequential([
            layers.RandomFlip("horizontal")
        ])

        gan = GanNetwork(data_augmentation = data_augmentation)
        trainer = NetworkTrainer(run_name = "simple_gan", dataset = dataset, model = gan, epochs = 5000)
        # trainer.continue_training(run_name = "simple_gan", checkpoint_date = "20220607-215307")

        # trainer.load(run_name = "simple_gan", checkpoint_date = "20220607-215307")
        # img, pred = gan.create_img()
        #
        # fig, axs = plt.subplots(1, 2, figsize=(12, 4))
        # normal_img = dataset.reverse_norm_layer(img)
        # plt.suptitle(f'Epoch {0} Probability {pred}', fontsize = 16)
        # axs[0].imshow(normal_img)
        # axs[0].axis('off')
        #
        # axs[1].imshow(np.rint(normal_img))
        # axs[1].axis('off')
        # plt.tight_layout()
        # plt.show()

        trainer.train()

