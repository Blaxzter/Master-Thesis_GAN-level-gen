import io
import time

import numpy as np
from loguru import logger
from pathlib import Path

import tensorflow as tf
from matplotlib import pyplot as plt

from util.Config import Config


class TensorBoardViz:
    def __init__(self, model, dataset, current_run = 'simple_gan', show_imgs = False, to_file = False):

        self.config: Config = Config.get_instance()
        self.model = model
        self.dataset = dataset

        self.show_imgs = show_imgs
        self.to_file = to_file

        self.log_dir = None
        self.train_summary_writer = None

        self.global_step = 0

        if to_file:
            Path(self.config.get_generated_image_store()).mkdir(parents=True, exist_ok=True)

        self.noise_dim = self.model.input_array_size
        self.seed = tf.random.normal([1, self.noise_dim])

        # Define our metrics
        self.metric_dicts = dict()


        # self.visualize_models()

    def create_summary_writer(self, run_name, run_time = None):
        # Check if writer is enabled
        if self.config.create_tensorflow_writer is False:
            return

        if run_time is None:
            self.log_dir = self.config.get_current_log_dir(run_name)
        else:
            self.log_dir = self.config.get_log_dir(run_name, run_time)

        self.train_summary_writer = tf.summary.create_file_writer(self.log_dir)
        return self.log_dir

    def visualize_models(self):
        # Check if writer is enabled
        if self.config.create_tensorflow_writer is False:
            return

        generated = None
        for model, name in zip([self.model.generator, self.model.discriminator], ['generator', 'discriminator']):
            tf.summary.trace_on(graph = True, profiler = True)

            # Call only one tf.function when tracing.
            if generated is None:
                generated = model(self.model.create_random_vector())
            else:
                model(generated)

            with self.train_summary_writer.as_default():
                tf.summary.trace_export(
                    name = name,
                    step = 0,
                    profiler_outdir = self.log_dir)

            model.run_eagerly = False
            tf.summary.trace_off()

    def show_image(self, img, step = 0):
        # Check if writer is enabled
        if self.config.create_tensorflow_writer is False:
            return

        with self.train_summary_writer.as_default():
            tf.summary.image("Example Image", img, step = step + self.global_step)

    def visualize(self, epoch, start_timer):
        # Check if writer is enabled
        if self.config.create_tensorflow_writer is False:
            return

        self.generate_and_save_images(self.seed, epoch)

        with self.train_summary_writer.as_default():
            for name, aggregator in self.metric_dicts.items():
                tf.summary.scalar(f'{self.config.get_data_tag()}/{name}', aggregator.result(), step = epoch + self.global_step)

        end_timer = time.time()

        template = 'Elapsed Time {}, Epoch {}, generator_loss: {}, discriminator_loss: {}'
        logger.debug(
            template.format(int(end_timer - start_timer), epoch + 1 + self.global_step,
                            self.metric_dicts['generator_loss'].result(), self.metric_dicts['discriminator_loss'].result()))

        # Reset the state of the metrics
        for aggregator in self.metric_dicts.values():
            aggregator.reset_state()

    def generate_and_save_images(self, test_input, epoch):
        # Check if writer is enabled
        if self.config.create_tensorflow_writer is False:
            return

        # Notice `training` is set to False.
        # This is so all layers run in inference mode (batchnorm).
        img, pred = self.model.create_img(test_input)

        fig, axs = plt.subplots(1, 2, figsize=(12, 4))
        normal_img = self.dataset.reverse_norm_layer(img)
        plt.suptitle(f'Epoch {epoch} Probability {pred}', fontsize = 16)
        axs[0].imshow(normal_img, cmap = 'gray')
        axs[0].axis('off')

        axs[1].imshow(np.rint(normal_img))
        axs[1].axis('off')
        plt.tight_layout()

        if self.to_file:
            plt.savefig(f'{self.config.get_generated_image_store()}image_at_epoch_{epoch + self.global_step}.png')
        else:
            buf = io.BytesIO()
            plt.savefig(buf, format = 'png')
            plt.close(fig)
            # Convert PNG buffer to TF image
            image = tf.image.decode_png(buf.getvalue(), channels = 4)
            # Add the batch dimension
            image = tf.expand_dims(image, 0)
            self.show_image(img = image, step = epoch + self.global_step)

        if self.show_imgs:
            plt.show()

    def add_data(self, data_dict: dict):
        for name, value in data_dict.items():
            self.metric_dicts[name](value)

    def create_aggregator(self, param):
        for name in param:
            self.metric_dicts[name] = tf.keras.metrics.Mean(name, dtype = tf.float32)
