import io
import time
from pathlib import Path

import tensorflow as tf
from matplotlib import pyplot as plt


class TensorBoardViz:
    def __init__(self, model, dataset, current_run = 'gan', logs_dir = '../logs/', show_imgs = False, to_file = False):

        self.model = model
        self.dataset = dataset

        self.show_imgs = show_imgs
        self.to_file = to_file

        strftime = time.strftime("%Y%m%d-%H%M%S")
        self.train_log_dir = f'{logs_dir}{current_run}/{{timestamp}}/train'.replace("{timestamp}", strftime)
        self.train_summary_writer = tf.summary.create_file_writer(self.train_log_dir)

        if to_file:
            self.image_store = "../imgs/generated/{timestamp}/"
            self.image_store = self.image_store.replace("{timestamp}", strftime)
            Path(self.image_store).mkdir(parents=True, exist_ok=True)

        self.noise_dim = self.model.input_array_size
        self.num_examples_to_generate = 16
        self.seed = tf.random.normal([self.num_examples_to_generate, self.noise_dim])

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
                    profiler_outdir = self.train_log_dir)

            tf.summary.trace_off()

    def show_image(self, img):
        with self.train_summary_writer.as_default():
            tf.summary.image("Training data", img, step = 0)

    def visualize(self, epoch):
        self.generate_and_save_images(self.seed, epoch)

        with self.train_summary_writer.as_default():
            tf.summary.scalar('generator_loss', self.gen_loss.result(), step = epoch)
            tf.summary.scalar('discriminator_loss', self.disc_loss.result(), step = epoch)

    def generate_and_save_images(self, test_input, epoch):
        # Notice `training` is set to False.
        # This is so all layers run in inference mode (batchnorm).
        predictions = self.model.generator(test_input, training = False)

        fig = plt.figure(figsize = (4, 4))

        for i in range(predictions.shape[0]):
            plt.subplot(4, 4, i + 1)
            normal_img = self.dataset.reverse_norm_layer(predictions[i, :, :, 0])
            plt.imshow(normal_img, cmap = 'gray')
            plt.axis('off')


        plt.tight_layout()

        if self.to_file:
            plt.savefig(f'{self.image_store}image_at_epoch_{epoch}.png')
        else:
            buf = io.BytesIO()
            plt.savefig(buf, format = 'png')
            plt.close(fig)
            # Convert PNG buffer to TF image
            image = tf.image.decode_png(buf.getvalue(), channels = 4)
            # Add the batch dimension
            image = tf.expand_dims(image, 0)
            self.show_image(image)

        if self.show_imgs:
            plt.show()

    def losses(self, gen_loss, disc_loss):
        self.gen_loss(gen_loss)
        self.disc_loss(disc_loss)