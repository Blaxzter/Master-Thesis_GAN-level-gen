import numpy as np
from matplotlib import pyplot as plt

from converter.to_img_converter.MultiLayerStackDecoder import MultiLayerStackDecoder
from level.LevelVisualizer import LevelVisualizer
from test.TestEnvironment import TestEnvironment

if __name__ == '__main__':
    test_environment = TestEnvironment()
    test_outputs = test_environment.load_test_outputs_of_model('multilayer_with_air')
    gan_output, image_name = test_environment.return_loaded_gan_output_by_idx(0)

    norm_img = (gan_output[0] + 1) / 2

    norm_img[norm_img[:, :, 0] < 0.1, 0] = 0
    img = np.argmax(norm_img, axis = 2)

    plt.imshow(img)
    plt.show()

    multiLayerStackDecoder = MultiLayerStackDecoder()
    created_level = multiLayerStackDecoder.decode(gan_output)

    fig, ax = plt.subplots()
    level_visualizer = LevelVisualizer()
    level_visualizer.create_img_of_structure(created_level.get_used_elements(), title = "Finished Structure")
    plt.show()
