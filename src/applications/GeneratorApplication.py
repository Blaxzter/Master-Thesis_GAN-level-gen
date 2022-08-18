import os
from tkinter import ttk

import matplotlib
import numpy as np
from loguru import logger
from mpl_toolkits.axes_grid1 import make_axes_locatable

from converter.to_img_converter import DecoderUtils
from converter.to_img_converter.LevelIdImgDecoder import LevelIdImgDecoder

matplotlib.use("TkAgg")

from tkinter import *
from matplotlib import pyplot as plt

from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from util.Config import Config


class GeneratorApplication:

    def __init__(self, frame = None, level_drawer = None):
        self.config: Config = Config.get_instance()
        self.canvas = None

        self.level_drawer = level_drawer

        self.toolbar = None
        self.gan = None

        self.top_frame = frame

        self.single_element = False
        self.rescaling = None
        self.seed = None

        self.model_loads = {
            'Standard GAN Old': self.load_model_0,
            'Standard GAN Next': self.load_model_1,
            'W-GAN SGD': self.load_model_2,
            'W-GAN ADAM': self.load_model_3,
            'Big Gan Multilayer': self.load_multilayer_encoding,
            'Single Element': self.load_single_element_encoding,
            'One Encoding': self.load_one_encoding,
            'One Element Multilayer': self.load_one_element_multilayer,
            'True One Hot': self.load_true_one_hot,
            'Small True One Hot With Air': self.small_true_one_hot_with_air
        }

        self.img_decoding = self.default_rint_rescaling

        if frame is None:
            self.create_window()

        self.selected_model = StringVar()
        self.create_buttons()

        if self.gan is not None:
            self.seed = self.gan.create_random_vector()

        if frame is None:
            # run the gui
            self.window.mainloop()

    def generate_img(self):

        if self.level_drawer is None:
            if self.canvas:
                self.canvas.get_tk_widget().destroy()

            if self.toolbar:
                self.toolbar.destroy()

            fig, ax = plt.subplots(1, 1, dpi = 100)
        else:
            self.level_drawer.clear_figure_canvas()
            fig, ax = self.level_drawer.new_fig()

        orig_img, pred = self.gan.create_img(seed = self.seed)

        # Use the defined decoding algorithm
        img = self.img_decoding(orig_img[0])

        if len(orig_img[0].shape) == 3:
            viz_img = np.max(orig_img[0], axis = 2)
        else:
            viz_img = orig_img[1].numpy()

        trimmed_img = DecoderUtils.trim_img(img.reshape(img.shape[0:2]))

        im = ax.imshow(viz_img)
        ax.set_title(f'Probability {pred.item()}')
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size = '5%', pad = 0.05)
        fig.colorbar(im, cax = cax, orientation = 'vertical')

        if self.level_drawer is None:
            self.canvas = FigureCanvasTkAgg(fig, master = self.window)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack()

            # creating the Matplotlib toolbar
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.window)
            self.toolbar.update()
        else:
            self.level_drawer.draw_img_to_fig_canvas()

            self.level_drawer.draw_level(trimmed_img)

    def default_rint_rescaling(self, orig_img):
        norm_img = self.rescaling(self.max_value / 2)(orig_img + self.shift_value).numpy()
        return np.rint(norm_img)

    def threshold_rint_rescaling(self, orig_img):
        threshold = float(self.threshold_text.get('0.0', 'end'))

        norm_img = self.rescaling(self.max_value / 2)(orig_img + self.shift_value).numpy()
        norm_img[norm_img < threshold] = 0

        return np.rint(norm_img)

    def default_rint_rescaling(self, orig_img):
        norm_img = self.rescaling(self.max_value / 2)(orig_img + self.shift_value).numpy()
        return np.rint(norm_img)

    def argmax_multilayer_decoding(self, orig_img):
        threshold = float(self.threshold_text.get('0.0', 'end'))

        norm_img = self.rescaling(self.max_value / 2)(orig_img + self.shift_value).numpy()
        stacked_img = np.dstack((np.zeros((128, 128)) + threshold, norm_img))
        return np.argmax(stacked_img, axis = 2)

    def argmax_multilayer_decoding_with_air(self, orig_img):
        norm_img = self.rescaling(self.max_value / 2)(orig_img + self.shift_value).numpy()

        threshold = float(self.threshold_text.get('0.0', 'end'))
        norm_img[norm_img[:, :, 0] < threshold, 0] = 0

        return np.argmax(norm_img, axis = 2)

    def one_element_multilayer(self, orig_img):
        threshold = float(self.threshold_text.get('0.0', 'end'))

        norm_img = self.rescaling(self.max_value / 2)(orig_img + self.shift_value).numpy()
        return LevelIdImgDecoder.create_single_layer_img(multilayer_img = norm_img, air_threshold = threshold)

    def load_gan(self):
        import tensorflow as tf

        # Load the model
        self.model_loads[self.selected_model.get()]()
        self.seed = self.gan.create_random_vector()
        self.level_drawer.draw_mode.set('OneElement' if self.single_element else 'LevelImg')
        self.level_drawer.combobox.set(self.level_drawer.draw_mode.get())

        self.rescaling = tf.keras.layers.Rescaling

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

        self.gan.create_img()

    def new_seed(self):
        self.seed = self.gan.create_random_vector()

    def create_window(self):

        self.window = Tk()
        self.window.title('Gan Level Generator')
        self.window.geometry("1200x800")

        self.top_frame = Frame(self.window, width = 1200, height = 50, pady = 3)
        self.top_frame.pack()

    def create_buttons(self):

        wrapper = Canvas(self.top_frame)
        wrapper.pack(side = LEFT, padx = (10, 10), pady = (20, 10))
        label = Label(wrapper, text = "Loaded Model:")
        label.pack(side = TOP)

        self.combobox = ttk.Combobox(wrapper, textvariable = self.selected_model)
        self.combobox['values'] = list(self.model_loads.keys())
        self.combobox['state'] = 'readonly'
        self.combobox.bind('<<ComboboxSelected>>', lambda event: self.load_gan())
        self.combobox.pack(side = TOP)

        plot_button = Button(
            master = self.top_frame,
            command = lambda: self.generate_img(),
            height = 2,
            width = 10,
            text = "Generate Img")

        plot_button.pack(side = LEFT, pady = (20, 10), padx = (10, 10))

        plot_button = Button(
            master = self.top_frame,
            command = lambda: self.new_seed(),
            height = 2,
            width = 10,
            text = "New Seed")

        plot_button.pack(side = LEFT, pady = (20, 10), padx = (10, 10))

        wrapper = Canvas(self.top_frame)
        wrapper.pack(side = LEFT, padx = (10, 10), pady = (20, 10))
        label = Label(wrapper, text = "Multilayer Threshold")
        label.pack(side = LEFT)

        self.threshold_text = Text(wrapper, height = 1, width = 10)
        self.threshold_text.insert('0.0', '0.5')
        self.threshold_text.pack(side = LEFT, padx = (10, 10))

    def load_model_0(self):
        from generator.gan.SimpleGans import SimpleGAN100112
        self.checkpoint_dir = self.config.get_checkpoint_dir('simple_gan_112_100', '20220614-155205')
        self.gan = SimpleGAN100112()
        self.max_value = 4
        self.shift_value = 0
        self.single_element = False
        self.small_version = False
        self.img_decoding = self.default_rint_rescaling

    def load_model_1(self):
        from generator.gan.SimpleGans import SimpleGAN100116
        self.checkpoint_dir = self.config.get_checkpoint_dir('simple_gan_116_100', '20220619-195718')
        self.gan = SimpleGAN100116()
        self.max_value = 4
        self.shift_value = 0
        self.single_element = False
        self.small_version = False
        self.img_decoding = self.default_rint_rescaling

    def load_model_2(self):
        from generator.gan.SimpleGans import SimpleGAN100116
        self.checkpoint_dir = self.config.get_checkpoint_dir('wasserstein-gan_116_100', '20220623-015436')
        self.gan = SimpleGAN100116()
        self.max_value = 4
        self.shift_value = 0
        self.single_element = False
        self.small_version = False
        self.img_decoding = self.default_rint_rescaling

    def load_model_3(self):
        from generator.gan.SimpleGans import SimpleGAN100116
        self.checkpoint_dir = self.config.get_checkpoint_dir('wasserstein-gan_116_100_adam', '20220627-202454')
        self.gan = SimpleGAN100116()
        self.max_value = 4
        self.shift_value = 0
        self.single_element = False
        self.small_version = False
        self.img_decoding = self.default_rint_rescaling

    def load_multilayer_encoding(self):
        from generator.gan.BigGans import WGANGP128128_Multilayer
        self.checkpoint_dir = self.config.get_checkpoint_dir('wasserstein-gan_GP_128_128_multi_layer_fixed', '20220728-172004')
        self.gan = WGANGP128128_Multilayer()
        self.max_value = 1
        self.shift_value = 1
        self.single_element = False
        self.small_version = False
        self.img_decoding = self.argmax_multilayer_decoding

    def load_single_element_encoding(self):
        from generator.gan.BigGans import WGANGP128128
        self.checkpoint_dir = self.config.get_checkpoint_dir('wgan_gp_128_128_one_element_encoding_fixed', '20220802-221136')
        self.max_value = 40
        self.shift_value = 1
        self.gan = WGANGP128128()
        self.single_element = True
        self.small_version = False
        self.img_decoding = self.threshold_rint_rescaling

    def load_one_encoding(self):
        from generator.gan.BigGans import WGANGP128128_Multilayer
        self.checkpoint_dir = self.config.get_checkpoint_dir('wgan_gp_128_128_one_encoding_fixed', '20220728-172004')
        self.max_value = 1
        self.shift_value = 1
        self.gan = WGANGP128128_Multilayer()
        self.single_element = True
        self.small_version = False
        self.img_decoding = self.one_element_multilayer

    def load_one_element_multilayer(self):
        from generator.gan.BigGans import WGANGP128128_Multilayer
        self.checkpoint_dir = self.config.get_checkpoint_dir('wgan_gp_128_128_one_element_multilayer_fixed', '20220806-145814')
        self.max_value = 14
        self.shift_value = 1
        self.gan = WGANGP128128_Multilayer()
        self.single_element = True
        self.small_version = False
        self.img_decoding = self.one_element_multilayer

    def load_true_one_hot(self):
        from generator.gan.BigGans import WGANGP128128_Multilayer
        self.checkpoint_dir = self.config.get_checkpoint_dir('wgan_gp_128_128_true_one_hot', '20220808-192940')
        self.max_value = 1
        self.shift_value = 1
        self.gan = WGANGP128128_Multilayer(last_dim = 40)
        self.single_element = True
        self.small_version = False
        self.img_decoding = self.argmax_multilayer_decoding

    def small_true_one_hot_with_air(self):
        from generator.gan.BigGans import WGANGP128128_Multilayer
        self.checkpoint_dir = self.config.get_checkpoint_dir('wgan_gp_128_128_small_one_element_true_one_hot_with_air', '20220813-182630')
        self.max_value = 1
        self.shift_value = 1
        self.gan = WGANGP128128_Multilayer(last_dim = 15)
        self.single_element = True
        self.small_version = True
        self.img_decoding = self.argmax_multilayer_decoding_with_air


if __name__ == '__main__':
    generator_application = GeneratorApplication()

