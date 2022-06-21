import os
import sys

import tensorflow as tf

from Trainer.TrainerWrapper import NetworkTrainer
from util.Config import Config
from data_scripts.LevelDataset import LevelDataset
from generator.gan.SimpleGans import SimpleGAN100116

if __name__ == '__main__':
    with tf.device('/GPU:0'):
        config = Config.get_instance()
        config.tag = "wgan_116_100_filtered"
        print(str(config))

        dataset = LevelDataset(dataset_name = "filtered_single_structure_116_100", batch_size = 32)
        dataset.load_dataset()

        data_augmentation = tf.keras.Sequential([
            tf.keras.layers.RandomFlip("horizontal")
        ])

        gan = SimpleGAN100116(data_augmentation = data_augmentation)
        run_name = "simple_gan_116_100"
        trainer = NetworkTrainer(run_name = run_name, dataset = dataset, model = gan, epochs = 5000)
        trainer.continue_training(run_name = run_name, checkpoint_date = "20220619-195718")

        trainer.train()
