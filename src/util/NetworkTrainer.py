import os
import time

import tensorflow as tf

from data_scripts.LevelDataset import LevelDataset
from generator.gan.GanNetwork import GanNetwork
from util.Config import Config
from util.TrainVisualizer import TensorBoardViz


class NetworkTrainer:

    def __init__(self, run_name, dataset: LevelDataset, model, epochs = 50):

        self.config: Config = Config.get_instance()
        self.run_name = run_name

        # This method returns a helper function to compute cross entropy loss
        self.cross_entropy = tf.keras.losses.BinaryCrossentropy(from_logits = True)
        self.generator_optimizer = tf.keras.optimizers.Adam(1e-4)
        self.discriminator_optimizer = tf.keras.optimizers.Adam(1e-4)

        self.model: GanNetwork = model
        self.dataset: LevelDataset = dataset
        self.visualizer: TensorBoardViz = TensorBoardViz(model = model, dataset = dataset)
        self.trainer_dataset = dataset.get_dataset()

        self.checkpoint = None

        self.checkpoint_dir = self.config.get_current_checkpoint_dir(run_name)
        self.checkpoint_prefix = os.path.join(self.checkpoint_dir, "ckpt")
        self.checkpoint = tf.train.Checkpoint(
            generator_optimizer = self.generator_optimizer,
            discriminator_optimizer = self.discriminator_optimizer,
            generator = self.model.generator,
            discriminator = self.model.discriminator
        )

        self.batch_size = dataset.batch_size
        self.epochs = epochs

    def train(self):
        for epoch in range(self.epochs):
            start = time.time()

            for image_batch, data in self.trainer_dataset:
                gen_loss, disc_loss = self.train_step(image_batch)
                self.visualizer.losses(gen_loss, disc_loss)

            # Produce images for the GIF as you go
            self.visualizer.visualize(epoch + 1)

            # Save the model every 15 epochs
            if (epoch + 1) % 15 == 0:
                self.checkpoint.save(file_prefix = self.checkpoint_prefix)

            print('Time for epoch {} is {} sec'.format(epoch + 1, time.time() - start))

        # Generate after the final epoch
        self.visualizer.visualize(epoch + 1)
        self.checkpoint.save(file_prefix = self.checkpoint_prefix)

    @tf.function
    def train_step(self, images):
        noise = tf.random.normal([self.batch_size, self.model.input_array_size])

        with tf.GradientTape() as gen_tape, tf.GradientTape() as disc_tape:
            generated_images = self.model.generator(noise, training = True)

            real_output = self.model.discriminator(images, training = True)
            fake_output = self.model.discriminator(generated_images, training = True)

            gen_loss = self.generator_loss(fake_output)
            disc_loss = self.discriminator_loss(real_output, fake_output)

        gradients_of_generator = gen_tape.gradient(gen_loss, self.model.generator.trainable_variables)
        gradients_of_discriminator = disc_tape.gradient(disc_loss, self.model.discriminator.trainable_variables)

        self.generator_optimizer.apply_gradients(
            zip(gradients_of_generator, self.model.generator.trainable_variables))
        self.discriminator_optimizer.apply_gradients(
            zip(gradients_of_discriminator, self.model.discriminator.trainable_variables))

        return gen_loss, disc_loss

    def discriminator_loss(self, real_output, fake_output):
        real_loss = self.cross_entropy(tf.ones_like(real_output), real_output)
        fake_loss = self.cross_entropy(tf.zeros_like(fake_output), fake_output)
        total_loss = real_loss + fake_loss
        return total_loss

    def generator_loss(self, fake_output):
        return self.cross_entropy(tf.ones_like(fake_output), fake_output)

    def save(self):
        # Generate after the final epoch
        self.checkpoint.save(file_prefix = self.checkpoint_prefix)

    def load(self, run_name = None, checkpoint_date = None):
        if checkpoint_date is None:
            raise Exception("Pls define the checkpoint folder")

        checkpoint_dir = self.config.get_checkpoint_dir(run_name, checkpoint_date)
        last_checkpoint = tf.train.latest_checkpoint(checkpoint_dir)
        self.checkpoint.restore(last_checkpoint)

