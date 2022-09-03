import os
import pickle
from tkinter import ttk

import matplotlib
import numpy as np
from loguru import logger
from mpl_toolkits.axes_grid1 import make_axes_locatable

from converter.gan_processing.DecodingFunctions import DecodingFunctions
from converter.to_img_converter import DecoderUtils

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
            'One Element Encoding': self.load_one_element_encoding,
            'One Element Multilayer': self.load_one_element_multilayer,
            'True One Hot': self.load_true_one_hot,
            'Small True One Hot With Air': self.small_true_one_hot_with_air,
            'Multilayer With Air': self.multilayer_with_air,
        }

        if frame is None:
            self.create_window()

        self.selected_model = StringVar()
        self.load_stored_img = StringVar()
        self.create_buttons()

        if self.gan is not None:
            self.seed = self.gan.create_random_vector()

        self.decoding_functions = DecodingFunctions(threshold_callback = lambda: self.threshold_text.get('0.0', 'end'))
        self.img_decoding = self.decoding_functions.default_rint_rescaling

        if frame is None:
            # run the gui
            self.window.mainloop()

    def generate_img(self, created_img = None):
        if created_img is None:
            orig_img, pred = self.gan.create_img(seed = self.seed)
        else:
            orig_img, pred = created_img

        if self.level_drawer is None:
            if self.canvas:
                self.canvas.get_tk_widget().destroy()

            if self.toolbar:
                self.toolbar.destroy()

            fig, ax = plt.subplots(1, 1, dpi = 100)
        else:
            self.level_drawer.clear_figure_canvas()
            for i in range(len(self.level_drawer.tabs)):
                fig, ax = self.level_drawer.new_fig()
                self.level_drawer.tabs[i]['fig'] = fig
                self.level_drawer.tabs[i]['ax'] = ax

            fig = self.level_drawer.tabs[0]['fig']
            ax = self.level_drawer.tabs[0]['ax']

        # Use the defined decoding algorithm
        img, norm_img = self.img_decoding(orig_img[0])

        if len(orig_img[0].shape) == 3:
            viz_img = np.max(orig_img[0], axis = 2)
        else:
            viz_img = orig_img[1].numpy()

        trimmed_img, trim_data = DecoderUtils.trim_img(img.reshape(img.shape[0:2]), ret_trims = True)
        self.create_plt_img(ax, fig, f'Probability {pred.item()}', viz_img)

        if self.level_drawer is None:
            self.canvas = FigureCanvasTkAgg(fig, master = self.window)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack()

            # creating the Matplotlib toolbar
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.window)
            self.toolbar.update()
        else:
            self.level_drawer.draw_img_to_fig_canvas(tab = 0)
            self.level_drawer.draw_level(trimmed_img, tab = 0)

            for i in range(1, len(self.level_drawer.tabs)):
                fig = self.level_drawer.tabs[i]['fig']
                ax = self.level_drawer.tabs[i]['ax']
                self.create_plt_img(ax, fig, f'Layer {i}', orig_img[0, :, :, i - 1])
                self.level_drawer.draw_img_to_fig_canvas(tab = i)
                self.level_drawer.draw_level(
                    np.rint(norm_img[trim_data[0]:trim_data[1], trim_data[2]: trim_data[3], i - 1]), tab = i)

    def create_plt_img(self, ax, fig, plt_title, viz_img):
        im = ax.imshow(viz_img)
        ax.set_title(plt_title)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size = '5%', pad = 0.05)
        fig.colorbar(im, cax = cax, orientation = 'vertical')

    def load_gan(self):
        import tensorflow as tf

        # Load the model
        self.model_loads[self.selected_model.get()]()
        self.seed = self.gan.create_random_vector()
        self.level_drawer.draw_mode.set('OneElement' if self.single_element else 'LevelImg')
        self.level_drawer.combobox.set(self.level_drawer.draw_mode.get())

        self.load_stored_imgs()
        self.decoding_functions.set_rescaling(rescaling = tf.keras.layers.Rescaling)

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

        orig_img, pred = self.gan.create_img(self.seed)
        depth = orig_img.shape[-1]
        self.level_drawer.grid_drawer.create_tab_panes(1 if depth == 1 else depth + 1)
        self.level_drawer.create_img_tab_panes(1 if depth == 1 else depth + 1)
        self.generate_img(created_img = (orig_img, pred))

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

        self.combobox = ttk.Combobox(wrapper, textvariable = self.selected_model, width = 30, state = "readonly")
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

        wrapper = Canvas(self.top_frame)
        wrapper.pack(side = LEFT, padx = (20, 10), pady = (20, 10))
        label = Label(wrapper, text = "Store Comment:")
        label.pack(side = LEFT)

        self.img_store_comment = Text(wrapper, height = 1, width = 30)
        self.img_store_comment.insert('0.0', ' ')
        self.img_store_comment.pack(side = LEFT, padx = (10, 10))

        store_img = Button(
            master = self.top_frame,
            command = lambda: self.store_gan_img(),
            height = 2,
            width = 15,
            text = "Store GAN Output")
        store_img.pack(side = LEFT, pady = (20, 10), padx = (10, 10))

        # Display loaded images
        wrapper = Canvas(self.top_frame)
        wrapper.pack(side = LEFT, padx = (10, 10), pady = (20, 10))
        label = Label(wrapper, text = "Loaded Model:")
        label.pack(side = TOP)

        self.stored_images = ttk.Combobox(wrapper, textvariable = self.load_stored_img, width = 30, state = "readonly")
        self.stored_images['state'] = 'readonly'
        self.stored_images.bind('<<ComboboxSelected>>', lambda event: self.display_loaded_img())
        self.stored_images.pack(side = TOP)

        store_img = Button(
            master = self.top_frame,
            command = lambda: self.delete_selected_img(),
            height = 2,
            width = 2,
            text = "X")
        store_img.pack(side = LEFT, pady = (20, 10), padx = (10, 10))

    def load_stored_imgs(self):
        loaded_model = self.selected_model.get().replace(' ', '_').lower()
        self.store_imgs_pickle_file = self.config.get_gan_img_store(loaded_model)

        with open(self.store_imgs_pickle_file, 'rb') as f:
            self.loaded_outputs = pickle.load(f)

        self.stored_images['values'] = list(self.loaded_outputs.keys())
        self.stored_images.set('')
        self.img_store_comment.delete('0.0', END)

    def store_gan_img(self):
        orig_img, prediction = self.gan.create_img(self.seed)
        comment = self.img_store_comment.get('0.0', 'end')
        comment = comment.strip()
        self.loaded_outputs[comment] = dict(
            output = orig_img,
            prediction = prediction,
            seed = self.seed,
            comment = comment
        )

        with open(self.store_imgs_pickle_file, 'wb') as handle:
            pickle.dump(self.loaded_outputs, handle, protocol = pickle.HIGHEST_PROTOCOL)

        self.stored_images['values'] = list(self.loaded_outputs.keys())
        self.img_store_comment.delete('0.0', END)

    def display_loaded_img(self):
        loaded_data = self.loaded_outputs[self.stored_images.get()]
        orig_img = loaded_data['output']
        prediction = loaded_data['prediction']
        self.seed = loaded_data['seed']
        depth = orig_img.shape[-1]

        self.level_drawer.grid_drawer.create_tab_panes(1 if depth == 1 else depth + 1)
        self.level_drawer.create_img_tab_panes(1 if depth == 1 else depth + 1)
        self.generate_img(created_img = (orig_img, prediction))

    def delete_selected_img(self):
        del self.loaded_outputs[self.stored_images.get()]

        with open(self.store_imgs_pickle_file, 'wb') as handle:
            pickle.dump(self.loaded_outputs, handle, protocol = pickle.HIGHEST_PROTOCOL)

        self.stored_images['values'] = list(self.loaded_outputs.keys())

    def load_model_0(self):
        from generator.gan.SimpleGans import SimpleGAN100112
        self.checkpoint_dir = self.config.get_checkpoint_dir('simple_gan_112_100', '20220614-155205')
        self.gan = SimpleGAN100112()
        self.decoding_functions.update_rescale_values(max_value = 4, shift_value = 0)
        self.img_decoding = self.decoding_functions.default_rint_rescaling
        self.single_element = False
        self.small_version = False

    def load_model_1(self):
        from generator.gan.SimpleGans import SimpleGAN100116
        self.checkpoint_dir = self.config.get_checkpoint_dir('simple_gan_116_100', '20220619-195718')
        self.gan = SimpleGAN100116()
        self.decoding_functions.update_rescale_values(max_value = 4, shift_value = 0)
        self.img_decoding = self.decoding_functions.default_rint_rescaling
        self.single_element = False
        self.small_version = False

    def load_model_2(self):
        from generator.gan.SimpleGans import SimpleGAN100116
        self.checkpoint_dir = self.config.get_checkpoint_dir('wasserstein-gan_116_100', '20220623-015436')
        self.gan = SimpleGAN100116()
        self.decoding_functions.update_rescale_values(max_value = 4, shift_value = 0)
        self.img_decoding = self.decoding_functions.default_rint_rescaling
        self.single_element = False
        self.small_version = False

    def load_model_3(self):
        from generator.gan.SimpleGans import SimpleGAN100116
        self.checkpoint_dir = self.config.get_checkpoint_dir('wasserstein-gan_116_100_adam', '20220627-202454')
        self.gan = SimpleGAN100116()
        self.decoding_functions.update_rescale_values(max_value = 4, shift_value = 0)
        self.img_decoding = self.decoding_functions.default_rint_rescaling
        self.single_element = False
        self.small_version = False

    def load_multilayer_encoding(self):
        from generator.gan.BigGans import WGANGP128128_Multilayer
        self.checkpoint_dir = self.config.get_checkpoint_dir('wasserstein-gan_GP_128_128_multi_layer_fixed',
                                                             '20220728-172004')
        self.gan = WGANGP128128_Multilayer()
        self.decoding_functions.update_rescale_values(max_value = 1, shift_value = 1)
        self.img_decoding = self.decoding_functions.argmax_multilayer_decoding
        self.single_element = False
        self.small_version = False

    def load_one_element_encoding(self):
        from generator.gan.BigGans import WGANGP128128
        self.checkpoint_dir = self.config.get_checkpoint_dir('wgan_gp_128_128_one_element_encoding_fixed',
                                                             '20220802-221136')
        self.decoding_functions.update_rescale_values(max_value = 40, shift_value = 1)
        self.img_decoding = self.decoding_functions.threshold_rint_rescaling
        self.gan = WGANGP128128()
        self.single_element = True
        self.small_version = False

    def load_one_element_multilayer(self):
        from generator.gan.BigGans import WGANGP128128_Multilayer
        self.checkpoint_dir = self.config.get_checkpoint_dir('wgan_gp_128_128_one_element_multilayer_fixed',
                                                             '20220806-145814')
        self.decoding_functions.update_rescale_values(max_value = 14, shift_value = 1)
        self.img_decoding = self.decoding_functions.one_element_multilayer
        self.gan = WGANGP128128_Multilayer()
        self.single_element = True
        self.small_version = False

    def load_true_one_hot(self):
        from generator.gan.BigGans import WGANGP128128_Multilayer
        self.checkpoint_dir = self.config.get_checkpoint_dir('wgan_gp_128_128_true_one_hot', '20220808-192940')
        self.decoding_functions.update_rescale_values(max_value = 1, shift_value = 1)
        self.img_decoding = self.decoding_functions.argmax_multilayer_decoding
        self.gan = WGANGP128128_Multilayer(last_dim = 40)
        self.single_element = True
        self.small_version = False

    def small_true_one_hot_with_air(self):
        from generator.gan.BigGans import WGANGP128128_Multilayer
        self.checkpoint_dir = self.config.get_checkpoint_dir('wgan_gp_128_128_small_one_element_true_one_hot_with_air',
                                                             '20220813-182630')
        self.decoding_functions.update_rescale_values(max_value = 1, shift_value = 1)
        self.img_decoding = self.decoding_functions.argmax_multilayer_decoding_with_air
        self.gan = WGANGP128128_Multilayer(last_dim = 15)
        self.single_element = True
        self.small_version = True

    def multilayer_with_air(self):
        from generator.gan.BigGans import WGANGP128128_Multilayer
        self.checkpoint_dir = self.config.get_checkpoint_dir('wgan_gp_128_128_multilayer_with_air', '20220816-202429')
        self.decoding_functions.update_rescale_values(max_value = 1, shift_value = 1)
        self.img_decoding = self.decoding_functions.argmax_multilayer_decoding_with_air
        self.gan = WGANGP128128_Multilayer(last_dim = 5)
        self.single_element = False
        self.small_version = False


if __name__ == '__main__':
    generator_application = GeneratorApplication()
