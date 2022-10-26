import pickle

from util.Config import Config


def load_run_data(run_name, img_index = 0):
    config = Config.get_instance()
    pickle_files = config.get_epoch_run_data_files(run_name)

    for pickle_file in pickle_files:
        with open(pickle_file, 'rb') as f:
            loaded_outputs = pickle.load(f)

        print(loaded_outputs)
        break

if __name__ == '__main__':
    run_name = "wgan_gp_128_128_multilayer_with_air_new"
    load_run_data(run_name)