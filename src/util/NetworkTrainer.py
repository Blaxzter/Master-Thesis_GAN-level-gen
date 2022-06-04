import os
import time

import tensorflow as tf
from matplotlib import pyplot as plt

from generator.Gan.GanNetwork import GanNetwork


class NetworkTrainer:

    def __init__(self, dataset, model, epochs = 50):
        # This method returns a helper function to compute cross entropy loss
        self.cross_entropy = tf.keras.losses.BinaryCrossentropy(from_logits = True)
        self.generator_optimizer = tf.keras.optimizers.Adam(1e-4)
        self.discriminator_optimizer = tf.keras.optimizers.Adam(1e-4)

        self.model: GanNetwork = model
        self.dataset = dataset

        self.checkpoint = None
        self.checkpoint_dir = './training_checkpoints'
        self.checkpoint_prefix = os.path.join(self.checkpoint_dir, "ckpt")
        self.checkpoint = tf.train.Checkpoint(
            generator_optimizer = self.generator_optimizer,
            discriminator_optimizer = self.discriminator_optimizer,
            generator = self.model.generator,
            discriminator = self.model.discriminator
        )

        self.image_store = "../imgs/generated/{timestamp}/"
        self.image_store = self.image_store.replace("{timestamp}", time.strftime("%Y%m%d-%H%M%S"))
        os.mkdir(self.image_store)

        self.batch_size = 50
        self.epochs = epochs
        self.noise_dim = self.model.input_array_size
        self.num_examples_to_generate = 16
        self.seed = tf.random.normal([self.num_examples_to_generate, self.noise_dim])

    def train(self):
        for epoch in range(self.epochs):
            start = time.time()

            for image_batch in self.dataset:
                self.train_step(image_batch)

            # Produce images for the GIF as you go
            self.generate_and_save_images(self.seed, epoch + 1)

            # Save the model every 15 epochs
            if (epoch + 1) % 15 == 0:
                self.checkpoint.save(file_prefix = self.checkpoint_prefix)

            print('Time for epoch {} is {} sec'.format(epoch + 1, time.time() - start))

        # Generate after the final epoch
        self.generate_and_save_images(self.seed, epoch + 1)
        self.checkpoint.save(file_prefix = self.checkpoint_prefix)

    @tf.function
    def train_step(self, images):
        noise = tf.random.normal([self.batch_size, self.noise_dim])

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

    def discriminator_loss(self, real_output, fake_output):
        real_loss = self.cross_entropy(tf.ones_like(real_output), real_output)
        fake_loss = self.cross_entropy(tf.zeros_like(fake_output), fake_output)
        total_loss = real_loss + fake_loss
        return total_loss

    def generator_loss(self, fake_output):
        return self.cross_entropy(tf.ones_like(fake_output), fake_output)

    def generate_and_save_images(self, test_input, epoch):
        # Notice `training` is set to False.
        # This is so all layers run in inference mode (batchnorm).
        predictions = self.model.generator.model(test_input, training = False)

        fig = plt.figure(figsize = (4, 4))

        for i in range(predictions.shape[0]):
            plt.subplot(4, 4, i + 1)
            plt.imshow(predictions[i, :, :, 0] * 127.5 + 127.5, cmap = 'gray')
            plt.axis('off')

        plt.savefig(f'{self.image_store}image_at_epoch_{epoch}.png')
        plt.show()
