import os

import matplotlib

matplotlib.use("TkAgg")

from tkinter import *
import matplotlib.pyplot as plt
import tensorflow as tf
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

from generator.gan.SimpleGans import SimpleGAN100116
from util.Config import Config

canvas = None
toolbar = None

def generate_img(gan):
    global canvas
    global toolbar
    if canvas:
        canvas.get_tk_widget().destroy()
    if toolbar:
        toolbar.destroy()

    fig, ax = plt.subplots(1, 1, figsize = (5, 10), dpi = 300)

    img, pred = gan.create_img()
    ax.imshow(img)
    ax.set_title(f'Probability {pred}')

    canvas = FigureCanvasTkAgg(fig, master = window)
    canvas.draw()
    canvas.get_tk_widget().pack()

    # creating the Matplotlib toolbar
    toolbar = NavigationToolbar2Tk(canvas, window)
    toolbar.update()

    canvas.get_tk_widget().pack()


if __name__ == '__main__':
    # the main Tkinter window
    window = Tk()

    # setting the title
    window.title('Gan Level Generator')

    # dimensions of the main window
    window.geometry("1200x800")

    config: Config = Config.get_instance()
    checkpoint_dir = config.get_checkpoint_dir('simple_gan_116_100', '20220619-195718')

    simple_gan = SimpleGAN100116()
    # simple_gan.generator.load_weights(last_checkpoint)
    # simple_gan.discriminator.load_weights(last_checkpoint)

    checkpoint = tf.train.Checkpoint(
        generator_optimizer = tf.keras.optimizers.Adam(1e-4),
        discriminator_optimizer = tf.keras.optimizers.Adam(1e-4),
        generator = simple_gan.generator,
        discriminator = simple_gan.discriminator
    )
    checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt")
    manager = tf.train.CheckpointManager(
        checkpoint, checkpoint_prefix, max_to_keep = 2
    )

    simple_gan.create_img()

    checkpoint.restore(manager.latest_checkpoint)
    if manager.latest_checkpoint:
        print("Restored from {}".format(manager.latest_checkpoint))
    else:
        print("Initializing from scratch.")

    label = Label(text = "Graph Page!", font = 16)
    label.pack(pady = 10, padx = 10)

    # button that displays the plot
    plot_button = Button(
        master = window,
        command = lambda: generate_img(simple_gan),
        height = 2,
        width = 10,
        text = "Generate")

    # place the button
    # in main window
    plot_button.pack(pady = 10, padx = 10)


    def on_closing():
        print("Wup Wup")
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_closing)
    # run the gui
    window.mainloop()