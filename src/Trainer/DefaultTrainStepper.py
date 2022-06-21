import tensorflow as tf

from data_scripts.LevelDataset import LevelDataset
from generator.gan.IGAN import IGAN
from util.Config import Config
from util.TrainVisualizer import TensorBoardViz


class DefaultTrainStepper:

    def __init__(self, model: IGAN, dataset: LevelDataset, visualizer: TensorBoardViz):

        self.config: Config = Config.get_instance()

        # This method returns a helper function to compute cross entropy loss
        self.cross_entropy = tf.keras.losses.BinaryCrossentropy(from_logits = True)

        self.generator_optimizer = tf.keras.optimizers.Adam(1e-4)
        self.discriminator_optimizer = tf.keras.optimizers.Adam(1e-4)

        self.model: IGAN = model
        self.dataset: LevelDataset = dataset

        self.batch_size = dataset.batch_size
        self.visualizer = visualizer

    def train_batch(self):
        for image_batch, data in self.dataset.get_dataset():
            gen_loss, disc_loss, real_output, fake_output = self.train_step(image_batch)
            self.visualizer.losses(gen_loss, disc_loss, real_output, fake_output)

    def train_step(self, content):
        noise = tf.random.normal([self.batch_size, self.model.input_array_size])

        with tf.GradientTape() as gen_tape, tf.GradientTape() as disc_tape:
            generated_content = self.model.generator(noise, training = True)

            real_output = self.model.discriminator(content, training = True)
            fake_output = self.model.discriminator(generated_content, training = True)

            gen_loss = self.generator_loss(fake_output)
            disc_loss = self.discriminator_loss(real_output, fake_output)

        gradients_of_generator = gen_tape.gradient(gen_loss, self.model.generator.trainable_variables)
        gradients_of_discriminator = disc_tape.gradient(disc_loss, self.model.discriminator.trainable_variables)

        self.generator_optimizer.apply_gradients(
            zip(gradients_of_generator, self.model.generator.trainable_variables))
        self.discriminator_optimizer.apply_gradients(
            zip(gradients_of_discriminator, self.model.discriminator.trainable_variables))

        return gen_loss, disc_loss, real_output, fake_output

    def generator_loss(self, fake_output):
        return self.cross_entropy(tf.ones_like(fake_output), fake_output)

    def discriminator_loss(self, real_output, fake_output):
        real_loss = self.cross_entropy(tf.ones_like(real_output), real_output)
        fake_loss = self.cross_entropy(tf.zeros_like(fake_output), fake_output)
        total_loss = real_loss + fake_loss
        return total_loss



