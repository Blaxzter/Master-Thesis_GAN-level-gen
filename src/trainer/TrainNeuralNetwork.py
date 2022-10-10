import os
import sys

import tensorflow as tf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from trainer.TrainerWrapper import NetworkTrainer
from util.Config import Config
from data_scripts.LevelDataset import LevelDataset
from generator.gan.BigGans import WGANGP128128_Multilayer, WGANGP128128

if __name__ == '__main__':
    with tf.device('/GPU:0'):
        config = Config.get_instance()
        config.tag = "wgan_gp_128_128_relu_multilayer_with_air"
        config.one_encoding = False
        config.multilayer = True
        print(str(config))

        dataset = LevelDataset(dataset_name = "multilayer_with_air_128_128", batch_size = 32)
        dataset.load_dataset()

        gan = WGANGP128128_Multilayer(data_augmentation = True, last_dim = 5, last_layer = 'relu')
        run_name = "wgan_gp_128_128_relu_multilayer_with_air"

        trainer = NetworkTrainer(run_name = run_name, dataset = dataset, model = gan, epochs = 15000)
        # trainer.continue_training(run_name = run_name, checkpoint_date = "20220623-015436")

        trainer.train()
