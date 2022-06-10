from generator.gan.GanNetwork import GanNetwork
from util.Config import Config
from util.TrainVisualizer import TensorBoardViz
import tensorflow as tf


def default_graph():
    config = Config.get_instance()
    log_dir = config.get_current_log_dir("Function_test")


    # The function to be traced.
    @tf.function
    def my_func(x, y):
        # A simple hand-rolled layer.
        return tf.nn.relu(tf.matmul(x, y))

    # Set up logging.
    writer = tf.summary.create_file_writer(log_dir)

    # Sample data for your function.
    x = tf.random.uniform((3, 3))
    y = tf.random.uniform((3, 3))

    # Bracket the function call with
    # tf.summary.trace_on() and tf.summary.trace_export().
    tf.summary.trace_on(graph = True, profiler = True)
    # Call only one tf.function when tracing.
    z = my_func(x, y)
    with writer.as_default():
        tf.summary.trace_export(
            name = "my_func_trace",
            step = 0,
            profiler_outdir = log_dir)

def create_graph_of_model():
    config = Config.get_instance()
    print(str(config))

    model = GanNetwork()
    model.generator.summary()
    model.discriminator.summary()

    visualizer: TensorBoardViz = TensorBoardViz(model = model, dataset = None, current_run = "gan_test")
    visualizer.visualize_models()

if __name__ == '__main__':
    create_graph_of_model()
