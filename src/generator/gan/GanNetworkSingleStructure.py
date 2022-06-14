import tensorflow as tf

from matplotlib import pyplot as plt
from tensorflow.keras import layers


class GanNetworkSingleStructure:

    def __init__(self, data_augmentation = None):
        self.input_array_size = 256

        self.output_shape = (100, 112)

        self.data_augmentation = data_augmentation

        self.generator = None
        self.discriminator = None
        self.create_generator_model()
        self.create_discriminator_model()

    def create_random_vector(self):
        return tf.random.normal([1, self.input_array_size])

    def create_generator_model(self):
        model = tf.keras.Sequential()
        model.add(
            layers.Dense(25 * 28 * self.input_array_size, use_bias = False, input_shape = (self.input_array_size,)))
        model.add(layers.BatchNormalization())
        model.add(layers.LeakyReLU())

        model.add(layers.Reshape((25, 28, self.input_array_size)))
        assert model.output_shape == (None, 25, 28, self.input_array_size)

        model.add(layers.Conv2DTranspose(filters = 128, kernel_size = (5, 5), strides = (1, 1), padding = 'same',
                                         use_bias = False))
        assert model.output_shape == (None, 25, 28, 128)
        model.add(layers.BatchNormalization())
        model.add(layers.LeakyReLU())

        model.add(layers.Conv2DTranspose(filters = 64, kernel_size = (5, 5), strides = (2, 2), padding = 'same',
                                         use_bias = False))
        assert model.output_shape == (None, 50, 56, 64)
        model.add(layers.BatchNormalization())
        model.add(layers.LeakyReLU())

        model.add(layers.Conv2DTranspose(1, (5, 5), strides = (2, 2), padding = 'same', use_bias = False,
                                         activation = 'tanh'))
        assert model.output_shape == (None, self.output_shape[0], self.output_shape[1], 1)

        self.generator = model

    def create_discriminator_model(self):
        model = tf.keras.Sequential()
        if self.data_augmentation:
            model.add(self.data_augmentation)

        model.add(layers.Conv2D(64, (5, 5), strides = (2, 2), padding = 'same',
                                input_shape = [self.output_shape[0], self.output_shape[1], 1]))
        model.add(layers.LeakyReLU())
        model.add(layers.Dropout(0.3))

        model.add(layers.Conv2D(128, (5, 5), strides = (2, 2), padding = 'same'))
        model.add(layers.LeakyReLU())
        model.add(layers.Dropout(0.3))

        model.add(layers.Flatten())
        model.add(layers.Dense(1))

        self.discriminator = model

    def create_img(self, seed = None):
        if seed is None:
            random_input = self.create_random_vector()
        else:
            random_input = seed
        generated_img = self.generator(random_input, training = False)
        probability = self.discriminator(generated_img, training = False)
        return generated_img[0, :, :, :], round(probability.numpy().item() * 1000) / 1000


if __name__ == '__main__':
    data_augmentation = tf.keras.Sequential([
        layers.RandomFlip("horizontal")
    ])

    gan = GanNetwork(
        data_augmentation = data_augmentation
    )

    random_vec = gan.create_random_vector()
    generated_img = gan.generator(random_vec)
    plt.imshow(generated_img[0, :, :, 0])
    plt.show()
