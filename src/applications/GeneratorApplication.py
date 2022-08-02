import os

import matplotlib
import numpy as np
from loguru import logger

matplotlib.use("TkAgg")

from tkinter import *
import matplotlib.pyplot as plt
import tensorflow as tf
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

from generator.gan.SimpleGans import SimpleGAN100116, SimpleGAN100112
from generator.gan.BigGans import WGANGP128128_Multilayer
from util.Config import Config


class GeneratorApplication:
    def __init__(self):
        self.config: Config = Config.get_instance()
        self.canvas = None

        self.toolbar = None
        self.gan = None

        self.load_gan()

        if self.gan is not None:
            self.seed = self.gan.create_random_vector()

    def generate_img(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        if self.toolbar:
            self.toolbar.destroy()

        fig, ax = plt.subplots(1, 1, dpi = 100)

        img, pred = self.gan.create_img(seed = self.seed)

        if img.shape[-1] > 1:
            threshold = float(self.threshold_text.get('0.0', 'end'))

            norm_img = tf.keras.layers.Rescaling(1 / 2)(img + 1)
            stacked_img = np.dstack((np.zeros((128, 128)) + threshold, norm_img[0].numpy()))
            img = np.argmax(stacked_img, axis = 2)

        ax.imshow(img)
        ax.set_title(f'Probability {pred}')

        self.canvas = FigureCanvasTkAgg(fig, master = self.window)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

        # creating the Matplotlib toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.window)
        self.toolbar.update()

    def load_gan(self):
        # self.load_model_0()
        self.load_multilayer_encoding()
        # self.load_model_2()
        # self.load_model_3()
        checkpoint = tf.train.Checkpoint(
            generator_optimizer = tf.keras.optimizers.Adam(1e-4),
            discriminator_optimizer = tf.keras.optimizers.Adam(1e-4),
            generator = self.gan.generator,
            discriminator = self.gan.discriminator
        )
        checkpoint_prefix = os.path.join(self.checkpoint_dir, "ckpt")
        manager = tf.train.CheckpointManager(
            checkpoint, checkpoint_prefix, max_to_keep = 2
        )
        checkpoint.restore(manager.latest_checkpoint)
        if manager.latest_checkpoint:
            logger.debug("Restored from {}".format(manager.latest_checkpoint))
        else:
            logger.debug("Initializing from scratch.")

    def new_seed(self):
        self.seed = self.gan.create_random_vector()

    def create_window(self):

        self.window = Tk()
        self.window.title('Gan Level Generator')
        self.window.geometry("1200x800")

        self.top_frame = Frame(self.window, width = 1200, height = 50, pady = 3)
        self.top_frame.pack()

        plot_button = Button(
            master = self.top_frame,
            command = lambda: self.generate_img(),
            height = 2,
            width = 10,
            text = "Generate Img")

        plot_button.pack(side = LEFT, pady = 10, padx = 10)

        plot_button = Button(
            master = self.top_frame,
            command = lambda: self.new_seed(),
            height = 2,
            width = 10,
            text = "New Seed")

        plot_button.pack(side = LEFT, pady = 10, padx = 10)

        self.threshold_text = Text(self.top_frame, height = 1, width = 10)
        self.threshold_text.insert('0.0', '0.5')
        self.threshold_text.pack(side = LEFT, padx = (10, 10))

        def on_closing():
            print("Wup Wup")
            self.window.destroy()

        self.window.protocol("WM_DELETE_WINDOW", on_closing)

        # run the gui
        self.window.mainloop()

    def load_model_0(self):
        self.checkpoint_dir = self.config.get_checkpoint_dir('simple_gan_112_100', '20220614-155205')
        self.gan = SimpleGAN100112()

    def load_model_1(self):
        self.checkpoint_dir = self.config.get_checkpoint_dir('gan_116_100', '20220619-195718')
        self.gan = SimpleGAN100116()

    def load_model_2(self):
        self.checkpoint_dir = self.config.get_checkpoint_dir('wasserstein-gan_116_100', '20220623-015436')
        self.gan = SimpleGAN100116()

    def load_model_3(self):
        self.checkpoint_dir = self.config.get_checkpoint_dir('wasserstein-gan_116_100_adam', '20220627-202454')
        self.gan = SimpleGAN100116()

    def load_multilayer_encoding(self):
        self.checkpoint_dir = self.config.get_checkpoint_dir('wasserstein-gan_GP_128_128_multi_layer_fixed', '20220728-172004')
        self.gan = WGANGP128128_Multilayer()

if __name__ == '__main__':
    generator_application = GeneratorApplication()
    generator_application.create_window()
