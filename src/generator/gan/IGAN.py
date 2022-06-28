class IGAN:

    def __init__(self):
        self.input_array_size = 256

        self.output_shape = (88, 212)

        self.data_augmentation = None
        self.generator = None
        self.discriminator = None

    def create_random_vector(self):
        """
        Returns a Tensor that has the input shape required for the generator model
        """
        pass

    def create_generator_model(self):
        pass

    def create_discriminator_model(self):
        pass

    def create_img(self, seed = None):
        if seed is None:
            random_input = self.create_random_vector()
        else:
            random_input = seed
        generated_img = self.generator(random_input, training = False)
        probability = self.discriminator(generated_img, training = False)
        return generated_img[0, :, :, :], round(probability.numpy().item() * 1000) / 1000