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
        self.create_summary_writer(current_run)

        self.global_step = 0

        if to_file:
            Path(self.config.get_generated_image_store()).mkdir(parents=True, exist_ok=True)

        self.noise_dim = self.model.input_array_size
        self.seed = tf.random.normal([1, self.noise_dim])

        # Define our metrics
        self.gen_loss = tf.keras.metrics.Mean('generator_loss', dtype = tf.float32)
        self.disc_loss = tf.keras.metrics.Mean('discriminator_loss', dtype = tf.float32)
        self.real_prediction = tf.keras.metrics.Mean('real_prediction', dtype = tf.float32)
        self.fake_prediction = tf.keras.metrics.Mean('fake_prediction', dtype = tf.float32)

        self.visualize_models()

    def create_summary_writer(self, run_name, run_time = None):
        if run_time is None:
            self.log_dir = self.config.get_current_log_dir(run_name)
        else:
            self.log_dir = self.config.get_log_dir(run_name, run_time)
        self.train_summary_writer = tf.summary.create_file_writer(self.log_dir)

    def visualize_models(self):

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

            tf.summary.trace_off()

    def show_image(self, img, step = 0):
        with self.train_summary_writer.as_default():
            tf.summary.image("Training data", img, step = step + self.global_step)

    def visualize(self, epoch, start_timer):
        self.generate_and_save_images(self.seed, epoch)

        with self.train_summary_writer.as_default():
            tf.summary.scalar('generator_loss', self.gen_loss.result(), step = epoch + self.global_step)
            tf.summary.scalar('discriminator_loss', self.disc_loss.result(), step = epoch + self.global_step)
            tf.summary.scalar('real_prediction', self.real_prediction.result(), step = epoch + self.global_step)
            tf.summary.scalar('fake_prediction', self.fake_prediction.result(), step = epoch + self.global_step)

        end_timer = time.time()

        template = 'Elapsed Time {}, Epoch {}, generator_loss: {}, discriminator_loss: {}'
        logger.debug(template.format(int(end_timer - start_timer), epoch + 1 + self.global_step, self.gen_loss.result(), self.disc_loss.result()))

    def generate_and_save_images(self, test_input, epoch):
        # Notice `training` is set to False.
        # This is so all layers run in inference mode (batchnorm).
        img, pred = self.model.create_img(test_input)

        fig, axs = plt.subplots(1, 2, figsize=(12, 4))
        normal_img = self.dataset.reverse_norm_layer(img)
        plt.suptitle(f'Epoch {epoch} Probability {pred}', fontsize = 16)
        axs[0].imshow(normal_img)
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
            self.show_image(img = image, step = epoch)

        if self.show_imgs:
            plt.show()

    def losses(self, gen_loss, disc_loss, real_output, fake_output):
        self.gen_loss(gen_loss)
        self.disc_loss(disc_loss)
        self.real_prediction(real_output)
        self.fake_prediction(fake_output)
