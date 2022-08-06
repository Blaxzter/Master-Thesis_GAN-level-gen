from tkinter import *
from tkinter import ttk

import numpy as np
from loguru import logger
from matplotlib import pyplot as plt
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from applications.GridDrawer import GridDrawer
from converter.to_img_converter import DecoderUtils
from converter.to_img_converter.LevelIdImgDecoder import LevelIdImgDecoder
from converter.to_img_converter.LevelImgDecoder import LevelImgDecoder
from converter.to_img_converter.LevelImgEncoder import LevelImgEncoder
from game_management.GameManager import GameManager
from level import Constants
from level.LevelVisualizer import LevelVisualizer
from test.TestEnvironment import TestEnvironment
from test.visualization.LevelImgDecoderVisualization import LevelImgDecoderVisualization
from util.Config import Config


class LevelDrawer:
    def __init__(self):
        self.canvas_width = 1600
        self.canvas_height = 1000

        self.draw_area_width = 600
        self.draw_area_height = 600

        self.master = Tk()
        self.master.title("Painting using Ovals")
        self.master.bind('<Key>', lambda event: self.key_event(event))

        self.selected_block = None

        self.create_frames()

        self.grid_drawer = GridDrawer(
            self.left_frame,
            draw_area_width = self.draw_area_width,
            draw_area_height = self.draw_area_height,
            level_height = 50,
            level_width = 50,
        )

        self.create_cursor_button()
        self.create_img_canvas()

        self.level_img_decoder = LevelImgDecoder()
        self.level_id_img_decoder = LevelIdImgDecoder()
        self.level_img_decoder_visualization = LevelImgDecoderVisualization()
        self.level_visualizer = LevelVisualizer()
        self.game_manager = GameManager(Config.get_instance())

        self.bottom_buttons()

    def create_img_canvas(self):
        self.img_canvas = Canvas(self.right_frame, width = self.draw_area_width, height = self.draw_area_height, bd = 0)
        self.img_canvas.pack(expand = NO, side = RIGHT)
        self.figure_canvas = None
        self.fig, self.ax = None, None

    def create_frames(self):
        self.top_frame = Frame(self.master, width = self.canvas_width, height = 50, pady = 3)
        self.left_frame = Frame(self.master, width = int(self.canvas_width / 2), height = self.canvas_height - 100,
                                pady = 3)
        self.right_frame = Frame(self.master, width = int(self.canvas_width), height = self.canvas_height - 100,
                                 pady = 3)
        self.btm_frame = Frame(self.master, width = self.canvas_width, height = 50, pady = 3)

        # layout all of the main containers
        self.master.grid_rowconfigure(1, weight = 1)
        self.master.grid_columnconfigure(0, weight = 1)

        self.top_frame.grid(row = 0, sticky = "n")
        self.left_frame.grid(row = 1, sticky = "w")
        self.right_frame.grid(row = 1, sticky = "e")
        self.btm_frame.grid(row = 2, sticky = "s")

    def bottom_buttons(self):

        # button that displays the plot
        plot_button = Button(
            master = self.btm_frame,
            command = lambda: self.create_level(),
            height = 2,
            width = 15,
            text = "Decode Drawing"
        )
        plot_button.pack(side = LEFT)

        self.rec_idx = Text(self.btm_frame, height = 1, width = 3)
        self.rec_idx.insert('0.0', '1')
        self.rec_idx.pack(side = LEFT, padx = (10, 10))

        # button that displays the plot
        plot_button = Button(
            master = self.btm_frame,
            command = lambda: self.visualize_rectangle(),
            height = 2,
            width = 18,
            text = "Visualize Rectangles"
        )
        plot_button.pack(side = LEFT)

        self.level_select = Text(self.btm_frame, height = 1, width = 3)
        self.level_select.insert('0.0', '0')
        self.level_select.pack(side = LEFT, padx = (10, 10))

        # button that displays the plot
        plot_button = Button(
            master = self.btm_frame,
            command = lambda: self.load_level(),
            height = 2,
            width = 10,
            text = "Load Level"
        )
        plot_button.pack(side = LEFT)

        # button that displays the plot
        select_viz = Button(
            master = self.btm_frame,
            command = lambda: self.level_img_decoder_visualization.create_tree_of_one_encoding(self.grid_drawer.canvas),
            height = 2,
            width = 15,
            text = "Visualize Block Selection"
        )
        select_viz.pack(side = LEFT, padx = (10, 10))

        # button that displays the plot
        plot_button = Button(
            master = self.btm_frame,
            command = lambda: self.grid_drawer.delete_drawing(),
            height = 2,
            width = 10,
            text = "Delete"
        )
        plot_button.pack(side = LEFT, padx = (10, 10))

        start_game_button = Button(
            master = self.btm_frame,
            command = lambda: self.start_game(),
            height = 2,
            width = 15,
            text = "Start Game"
        )
        start_game_button.pack(side = LEFT)

        play_level = Button(
            master = self.btm_frame,
            command = lambda: self.run_level_in_game(),
            height = 2,
            width = 15,
            text = "Send To Game"
        )
        play_level.pack(side = LEFT)

        self.selected_decoding = StringVar()
        combobox = ttk.Combobox(self.btm_frame, textvariable = self.selected_decoding)
        combobox['values'] = ('LevelImg', 'OneElement')
        combobox.set('LevelImg')
        combobox['state'] = 'readonly'
        combobox.pack(side = LEFT)

    def create_cursor_button(self):
        temp_button = Button(
            master = self.top_frame,
            command = lambda: self.grid_drawer.block_cursor(dict(width = 1, height = 1, name = '1x1')),
            height = 2,
            width = 10,
            text = '1 x 1'
        )
        temp_button.pack(side = LEFT, pady = (10, 10), padx = (2, 2))

        self.block_data = Config.get_instance().get_encoding_data(f"encoding_res_{Constants.resolution}")
        del self.block_data['resolution']
        for block_idx, block in self.block_data.items():
            temp_button = Button(
                master = self.top_frame,
                command = lambda block = dict(width = block['width'] + 1, height = block['height'] + 1,
                                              name = block['name']): self.grid_drawer.block_cursor(block),
                height = 2,
                width = 10,
                text = block['name']
            )
            temp_button.pack(side = LEFT, pady = (10, 10), padx = (2, 2))

        temp_button = Button(
            master = self.top_frame,
            command = lambda: self.grid_drawer.block_cursor(dict(width = 7, height = 7, name = 'bird')),
            height = 2,
            width = 10,
            text = 'Bird'
        )
        temp_button.pack(side = LEFT, pady = (10, 10), padx = (2, 2))

        self.grid_drawer.block_cursor(dict(width = 1, height = 1, name = '1x1'))

    def key_event(self, event):
        print(event.char)
        if event.char in ['1', '2', '3', '4']:
            self.grid_drawer.material_id = int(event.char)

    def create_level(self):
        self.clear_figure_canvas()

        self.fig, self.ax = plt.subplots(1, 1, dpi = 100)

        temp_level_img = DecoderUtils.trim_img(self.grid_drawer.canvas)

        if self.selected_decoding.get() == 'LevelImg':
            self.level = self.level_img_decoder.decode_level(temp_level_img)
        else:
            self.level = self.level_id_img_decoder.decode_level(temp_level_img)

        self.ax.imshow(np.flip(temp_level_img, axis = 0), origin = 'lower')
        self.level_visualizer.create_img_of_structure(
            self.level.get_used_elements(), use_grid = False, ax = self.ax, scaled = True
        )

        if len(self.level.get_used_elements()) == 0:
            self.ax.set_title("No Level Decoded")

        self.draw_img_to_fig_canvas()

    def clear_figure_canvas(self):
        if self.figure_canvas is not None:
            plt.close(self.fig)
            self.figure_canvas.get_tk_widget().destroy()
            self.img_canvas.delete(self.figure_canvas)
            if self.toolbar is not None:
                self.toolbar.destroy()

    def visualize_rectangle(self):
        self.clear_figure_canvas()

        self.fig, self.ax = plt.subplots(1, 1, dpi = 100)

        material_id = int(self.rec_idx.get('0.0', 'end'))

        trimmed_img = DecoderUtils.trim_img(self.grid_drawer.canvas)
        self.level_img_decoder_visualization.visualize_rectangle(
            trimmed_img, material_id, ax = self.ax
        )

        self.draw_img_to_fig_canvas()

    def draw_img_to_fig_canvas(self):
        self.figure_canvas = FigureCanvasTkAgg(self.fig, master = self.img_canvas)
        self.figure_canvas.draw()
        self.figure_canvas.get_tk_widget().pack(fill = BOTH, expand = 1)
        self.toolbar = NavigationToolbar2Tk(self.figure_canvas, self.img_canvas)
        self.toolbar.update()

    def start_game(self):
        self.game_manager.start_game()

    def run_level_in_game(self):
        if self.level is None:
            logger.debug("No level decoded")
            return

        self.game_manager.switch_to_level(self.level, stop_time = False)

    def load_level(self):
        self.grid_drawer.delete_drawing()

        load_level = int(self.level_select.get('0.0', 'end'))

        test_environment = TestEnvironment('generated/single_structure')
        level = test_environment.get_level(load_level)
        level_img_encoder = LevelImgEncoder()
        elements = level.get_used_elements()
        encoded_img = level_img_encoder.create_calculated_img(elements)

        if self.grid_drawer.level_width < encoded_img.shape[1] or self.grid_drawer.level_height < encoded_img.shape[0]:
            max_dim = np.max(encoded_img.shape) + 2
            self.grid_drawer.set_level_dims(max_dim, max_dim)
            self.grid_drawer.create_grid()

        pad_left = int((self.grid_drawer.level_width - encoded_img.shape[1]) / 2)
        pad_right = int((self.grid_drawer.level_width - encoded_img.shape[1]) / 2)
        pad_top = self.grid_drawer.level_height - encoded_img.shape[0]

        padded_img = np.pad(encoded_img, ((pad_top, 0), (pad_left, pad_right)), 'constant')

        for x_idx in range(padded_img.shape[1]):
            for y_idx in range(padded_img.shape[0]):

                use_x_idx = x_idx + 1

                if padded_img[y_idx, x_idx] != 0:
                    x = use_x_idx * self.grid_drawer.rec_width - self.grid_drawer.rec_width / 2
                    y = y_idx * self.grid_drawer.rec_height - self.grid_drawer.rec_height / 2

                    x1, y1 = int(x - self.grid_drawer.rec_width / 2), int(y - self.grid_drawer.rec_width / 2)
                    x2, y2 = int(x + self.grid_drawer.rec_height / 2), int(y + self.grid_drawer.rec_height / 2)
                    fill_color = self.grid_drawer.colors[int(padded_img[y_idx, x_idx]) - 1]
                    self.grid_drawer.rects[y_idx][use_x_idx] = \
                        self.grid_drawer.draw_canvas.create_rectangle(
                            x1, y1, x2, y2, fill = fill_color, tag = f'rectangle', outline = fill_color)
                    self.grid_drawer.canvas[y_idx, use_x_idx] = int(padded_img[y_idx, x_idx])


if __name__ == '__main__':
    level_drawer = LevelDrawer()
    mainloop()
