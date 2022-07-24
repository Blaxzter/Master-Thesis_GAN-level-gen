import numpy as np
import tensorflow as tf
from matplotlib import pyplot as plt

from generator.gan.IGAN import IGAN

layers = tf.keras.layers
activations = tf.keras.activations


# https://de.mathworks.com/help/deeplearning/ug/trainwasserstein-gan-with-gradient-penalty-wgan-gp.html#:~:text=To%20train%20a%20WGAN%2DGP%20model%2C%20you%20must%20train%20the,64%20for%2010%2C000%20generator%20iterations.
# Example for a WGAN-GP Network

class WGANGP128128(IGAN):

    def __init__(self, data_augmentation = None):
        super().__init__()
        self.input_array_size = 128
        self.channel_amount = 64

        self.input_shape = (1, 1, 128)
        self.output_shape = (128, 128)

        self.data_augmentation = data_augmentation

        self.generator = None
        self.discriminator = None
        self.create_generator_model()
        self.create_discriminator_model()

    def create_random_vector(self):
        return tf.random.normal([1, 1, 1, self.input_array_size])

    def create_random_vector_batch(self, batch):
        """
        Returns a Tensor that has the input shape required for the generator model
        """
        return tf.random.normal([batch, 1, 1, self.input_array_size])

    def create_generator_model(self):
        model = tf.keras.Sequential(name = 'Generator')

        model.add(layers.InputLayer(input_shape = self.input_shape))

        model.add(layers.Conv2DTranspose(filters = 512, kernel_size = (4, 4), strides = (1, 1), padding = 'valid',
                                         use_bias = False))
        model.add(layers.LayerNormalization())
        model.add(layers.ReLU())

        for i in range(4):
            d = min(self.channel_amount * 2 ** (4 - 2 - i), self.channel_amount * 8)
            model.add(layers.Conv2DTranspose(d, 4, strides = 2, padding = 'same', use_bias = False))
            model.add(layers.LayerNormalization())
            model.add(layers.ReLU())

        model.add(layers.Conv2DTranspose(1, 4, strides = 2, padding = 'same'))
        model.add(layers.Activation(activations.tanh))

        self.generator = model

    def create_discriminator_model(self):
        model = tf.keras.Sequential(name = 'Discriminator')

        model.add(layers.InputLayer(input_shape = [self.output_shape[0], self.output_shape[1], 1]))
        model.add(layers.Conv2D(self.channel_amount, (4, 4), strides = (2, 2), padding = 'same', use_bias = False))
        model.add(layers.LeakyReLU(0.2))

        for i in range(4):
            d = min(self.channel_amount * 2 ** (i + 1), self.channel_amount * 8)
            model.add(layers.Conv2D(d, (4, 4), strides = (2, 2), padding = 'same', use_bias = False))
            model.add(layers.LayerNormalization())
            model.add(layers.LeakyReLU(alpha = 0.2))

        model.add(layers.Conv2D(1, (4, 4), strides = (1, 1), padding = 'valid', use_bias = False))

        self.discriminator = model


class WGANGP128128_Multilayer(IGAN):

    def __init__(self, data_augmentation = None):
        super().__init__()
        self.input_array_size = 128
        self.channel_amount = 64

        self.input_shape = (1, 1, 128)
        self.output_shape = (128, 128, 5)

        self.data_augmentation = data_augmentation

        self.generator = None
        self.discriminator = None
        self.create_generator_model()
        self.create_discriminator_model()

    def create_random_vector(self):
        return tf.random.normal([1, 1, 1, self.input_array_size])

    def create_random_vector_batch(self, batch):
        """
        Returns a Tensor that has the input shape required for the generator model
        """
        return tf.random.normal([batch, 1, 1, self.input_array_size])

    def create_generator_model(self):
        model = tf.keras.Sequential(name = 'Generator')

        model.add(layers.InputLayer(input_shape = self.input_shape))

        model.add(layers.Conv2DTranspose(filters = 512, kernel_size = (4, 4), strides = (1, 1), padding = 'valid',
                                         use_bias = False))
        model.add(layers.LayerNormalization())
        model.add(layers.ReLU())

        for i in range(4):
            d = min(self.channel_amount * 2 ** (4 - 2 - i), self.channel_amount * 8)
            model.add(layers.Conv2DTranspose(d, 4, strides = 2, padding = 'same', use_bias = False))
            model.add(layers.LayerNormalization())
            model.add(layers.ReLU())

        model.add(layers.Conv2DTranspose(5, 4, strides = 2, padding = 'same'))
        model.add(layers.Activation(activations.tanh))

        self.generator = model

    def create_discriminator_model(self):
        model = tf.keras.Sequential(name = 'Discriminator')

        model.add(layers.InputLayer(input_shape = [self.output_shape[0], self.output_shape[1], 5]))
        model.add(layers.Conv2D(self.channel_amount, (4, 4), strides = (2, 2), padding = 'same', use_bias = False))
        model.add(layers.LeakyReLU(0.2))

        for i in range(4):
            d = min(self.channel_amount * 2 ** (i + 1), self.channel_amount * 8)
            model.add(layers.Conv2D(d, (4, 4), strides = (2, 2), padding = 'same', use_bias = False))
            model.add(layers.LayerNormalization())
            model.add(layers.LeakyReLU(alpha = 0.2))

        model.add(layers.Conv2D(1, (4, 4), strides = (1, 1), padding = 'valid', use_bias = False))

        self.discriminator = model

    def create_img(self, seed = None):
        if seed is None:
            random_input = self.create_random_vector()
        else:
            random_input = seed

        generated_img = self.generator(random_input, training = False)
        probability = self.discriminator(generated_img, training = False)

        return generated_img, np.round(probability * 1000) / 1000

if __name__ == '__main__':
    gan = WGANGP128128_Multilayer()
    gan.print_summary()

    created_img, img_probability = gan.create_img()

    plt.imshow(created_img)
    plt.suptitle(f'Probability: {img_probability}')
    plt.show()
