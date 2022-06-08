import io
from loguru import logger
from pathlib import Path

import tensorflow as tf
from matplotlib import pyplot as plt

from util.Config import Config


class TensorBoardViz:
    def __init__(self, model, dataset, current_run = 'gan', show_imgs = False, to_file = False):

        self.config: Config = Config.get_instance()
        self.model = model
        self.dataset = dataset

        self.show_imgs = show_imgs
        self.to_file = to_file

        self.log_dir = self.config.get_log_dir(current_run)
        self.train_summary_writer = tf.summary.create_file_writer(self.log_dir)

        if to_file:
            Path(self.config.get_generated_image_store()).mkdir(parents=True, exist_ok=True)

        self.noise_dim = self.model.input_array_size
        self.seed = tf.random.normal([1, self.noise_dim])

        # Define our metrics
        self.gen_loss = tf.keras.metrics.Mean('generator_loss', dtype = tf.float32)
        self.disc_loss = tf.keras.metrics.Mean('discriminator_loss', dtype = tf.float32)

        self.visualize_models()

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
            tf.summary.image("Training data", img, step = step)

    def visualize(self, epoch):
        self.generate_and_save_images(self.seed, epoch)

        with self.train_summary_writer.as_default():
            tf.summary.scalar('generator_loss', self.gen_loss.result(), step = epoch)
            tf.summary.scalar('discriminator_loss', self.disc_loss.result(), step = epoch)

        template = 'Epoch {}, generator_loss: {}, discriminator_loss: {}'
        logger.debug(template.format(epoch + 1, self.gen_loss.result(), self.disc_loss.result()))

    def generate_and_save_images(self, test_input, epoch):
        # Notice `training` is set to False.
        # This is so all layers run in inference mode (batchnorm).
        predictions = self.model.generator(test_input, training = False)

        fig = plt.figure()
        normal_img = self.dataset.reverse_norm_layer(predictions[0, :, :, 0])
        plt.imshow(normal_img, cmap = 'gray')
        plt.axis('off')
        plt.tight_layout()

        if self.to_file:
            plt.savefig(f'{self.config.get_generated_image_store()}image_at_epoch_{epoch}.png')
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

    def losses(self, gen_loss, disc_loss):
        self.gen_loss(gen_loss)
        self.disc_loss(disc_loss)
