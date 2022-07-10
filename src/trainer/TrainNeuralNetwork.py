import os
import sys

import tensorflow as tf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from trainer.TrainerWrapper import NetworkTrainer
from util.Config import Config
from data_scripts.LevelDataset import LevelDataset
from generator.gan.BigGans import WGANGP128128

if __name__ == '__main__':
    with tf.device('/GPU:0'):
        config = Config.get_instance()
        config.tag = "wgan_GP_128_128"
        print(str(config))

        dataset = LevelDataset(dataset_name = "filtered_single_structure_128_128", batch_size = 64)
        dataset.load_dataset()

        data_augmentation = tf.keras.Sequential([
            tf.keras.layers.RandomFlip("horizontal")
        ])

        gan = WGANGP128128(data_augmentation = data_augmentation)
        run_name = "wasserstein-gan_GP_128_128_adam"
        trainer = NetworkTrainer(run_name = run_name, dataset = dataset, model = gan, epochs = 15000)
        # trainer.continue_training(run_name = run_name, checkpoint_date = "20220623-015436")

        trainer.train()
