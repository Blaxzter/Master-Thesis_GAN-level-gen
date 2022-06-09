import os
import time

import matplotlib.pyplot as plt
import tensorflow as tf
from loguru import logger
from tensorflow.python.summary.summary_iterator import summary_iterator

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

        self.final_learning_rate = 1e-4
        self.initial_learning_rate = 1e-2
        learning_rate_decay_factor = (self.final_learning_rate / self.initial_learning_rate) ** (1 / epochs)
        steps_per_epoch = int(dataset.get_data_amount() / dataset.batch_size)

        lr_schedule = tf.keras.optimizers.schedules.ExponentialDecay(
            initial_learning_rate = self.initial_learning_rate, decay_steps = steps_per_epoch, decay_rate = learning_rate_decay_factor)
        self.generator_optimizer = tf.keras.optimizers.Adam(learning_rate = lr_schedule)
        self.discriminator_optimizer = tf.keras.optimizers.Adam(learning_rate = lr_schedule)

        self.model: GanNetwork = model
        self.dataset: LevelDataset = dataset
        self.visualizer: TensorBoardViz = TensorBoardViz(model = model, dataset = dataset, current_run = self.run_name)
        self.trainer_dataset = dataset.get_dataset()

        self.checkpoint = None
        self.checkpoint_dir = None
        self.checkpoint_prefix = None
        self.manager = None
        self.create_checkpoint_manager(run_name)

        self.batch_size = dataset.batch_size
        self.epochs = epochs

    def train(self):
        logger.debug(f'Start Training of {self.run_name} for {self.epochs} epochs')
        for epoch in range(self.epochs):
            start_time = time.time()

            for image_batch, data in self.trainer_dataset:
                gen_loss, disc_loss, real_output, fake_output = self.train_step(image_batch)
                self.visualizer.losses(gen_loss, disc_loss, real_output, fake_output)

            # Produce images for the GIF as you go
            self.visualizer.visualize(epoch + 1, start_time)

            # Save the model every 15 epochs
            if (epoch + 1) % self.config.save_checkpoint_every == 0:
                self.manager.save()

        # Generate after the final epoch
        self.visualizer.visualize(epoch + 1)
        self.manager.save()

    @tf.function
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

    def save(self):
        self.manager.save()

    def create_checkpoint_manager(self, run_name, run_time = None):
        if run_time is None:
            self.checkpoint_dir = self.config.get_current_checkpoint_dir(run_name)
        else:
            self.checkpoint_dir = self.config.get_checkpoint_dir(run_name, run_time)

        self.checkpoint_prefix = os.path.join(self.checkpoint_dir, "ckpt")
        self.checkpoint = tf.train.Checkpoint(
            generator_optimizer = self.generator_optimizer,
            discriminator_optimizer = self.discriminator_optimizer,
            generator = self.model.generator,
            discriminator = self.model.discriminator
        )
        self.manager = tf.train.CheckpointManager(
            self.checkpoint, self.checkpoint_prefix, max_to_keep = self.config.keep_checkpoints
        )

    def load(self, run_name = None, checkpoint_date = None):
        if checkpoint_date is None:
            raise Exception("Pls define the checkpoint folder")

        checkpoint_dir = self.config.get_checkpoint_dir(run_name, checkpoint_date)
        last_checkpoint = tf.train.latest_checkpoint(checkpoint_dir)
        self.checkpoint.restore(last_checkpoint)

    def continue_training(self, run_name, checkpoint_date, at_epoch):
        self.visualizer.create_summary_writer(run_name = run_name, run_time = checkpoint_date)
        self.create_checkpoint_manager(run_name, checkpoint_date)

        self.load(run_name = run_name, checkpoint_date = checkpoint_date)
        self.visualizer.global_step = at_epoch



