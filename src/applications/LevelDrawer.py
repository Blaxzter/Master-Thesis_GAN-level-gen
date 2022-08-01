from tkinter import *

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from converter.to_img_converter import DecoderUtils
from converter.to_img_converter.LevelImgDecoder import LevelImgDecoder
from converter.to_img_converter.LevelImgEncoder import LevelImgEncoder
from game_management.GameManager import GameManager
from level import Constants
from level.LevelVisualizer import LevelVisualizer
from test.TestEnvironment import TestEnvironment
from util.Config import Config


class LevelDrawer:
    def __init__(self):
        self.canvas_width = 1600
        self.canvas_height = 1000

        self.draw_area_width = 600
        self.draw_area_height = 600

        self.level_height = 50
        self.level_width = 50

        self.canvas = np.zeros((self.level_height + 1, self.level_width + 1))
        self.rects = [[None for _ in range(self.canvas.shape[0])] for _ in range(self.canvas.shape[1])]

        self.rec_height = self.draw_area_height / self.level_height
        self.rec_width = self.draw_area_width / self.level_width

        self.myrect = None

        self.master = Tk()
        self.master.title("Painting using Ovals")
        self.master.bind('<Key>', lambda event: self.key_event(event))

        self.selected_block = None

        self.create_frames()
        self.create_button()
        self.create_draw_canvas()
        self.create_img_canvas()

        self.level_img_decoder = LevelImgDecoder()
        self.level_visualizer = LevelVisualizer()

        self.create_grid()
        self.material_id = 1
        self.colors = ['#a8d399', '#aacdf6', '#f98387', '#dbcc81']

        self.bottom_buttons()

    def create_img_canvas(self):
        self.img_canvas = Canvas(self.right_frame, width = self.draw_area_width, height = self.draw_area_height, bd = 0)
        self.img_canvas.pack(expand = NO, side = RIGHT)
        self.figure_canvas = None
        self.fig, self.ax = None, None

    def create_draw_canvas(self):
        self.draw_canvas = Canvas(self.left_frame, width = self.draw_area_width, height = self.draw_area_height)
        self.draw_canvas.pack(expand = YES, side = LEFT, pady = (30, 30), padx = (30, 30))

        self.draw_canvas.bind("<B1-Motion>", self.paint)
        self.draw_canvas.bind("<Button-1>", self.paint)
        self.draw_canvas.bind("<Motion>", self.hover)
        self.draw_canvas.bind("<B3-Motion>", lambda event: self.paint(event, clear = True))
        self.draw_canvas.bind("<Button-3>", lambda event: self.paint(event, clear = True))

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
        plot_button = Button(
            master = self.btm_frame,
            command = lambda: self.delete_drawing(),
            height = 2,
            width = 10,
            text = "Delete"
        )
        plot_button.pack(side = LEFT, padx = (10, 10))

    def create_button(self):
        temp_button = Button(
            master = self.top_frame,
            command = lambda: self.block_cursor(dict(width = 1, height = 1, name = '1x1')),
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
                                              name = block['name']): self.block_cursor(block),
                height = 2,
                width = 10,
                text = block['name']
            )
            temp_button.pack(side = LEFT, pady = (10, 10), padx = (2, 2))

        temp_button = Button(
            master = self.top_frame,
            command = lambda: self.block_cursor(dict(width = 7, height = 7, name = 'bird')),
            height = 2,
            width = 10,
            text = 'Bird'
        )
        temp_button.pack(side = LEFT, pady = (10, 10), padx = (2, 2))

        self.block_cursor(dict(width = 1, height = 1, name = '1x1'))

    def key_event(self, event):
        print(event.char)
        if event.char in ['1', '2', '3', '4']:
            self.material_id = int(event.char)
            print(self.material_id)

    def create_grid(self):
        for i in range(self.level_height):
            self.draw_canvas.create_line(
                self.rec_height * i, self.rec_height,
                self.rec_height * i, self.draw_area_height - self.rec_height,
                width = 1)

        for i in range(self.level_width):
            self.draw_canvas.create_line(
                self.rec_width, self.rec_width * i,
                                self.draw_area_width - self.rec_width, self.rec_width * i,
                width = 1)

    def paint(self, event, clear = False):
        self.hover(event)

        fill_color = self.colors[self.material_id - 1]

        x_index = round((event.x + (self.rec_width / 2) - 0) / self.rec_width)
        y_index = round((event.y + (self.rec_height / 2) - 0) / self.rec_height)

        block_width, block_height, block_name = self.selected_block

        x_axis = np.array([x for x in range(x_index, x_index + block_width)])
        y_axis = np.array([y for y in range(y_index, y_index + block_height)])
        x_pos = x_axis * self.rec_width - self.rec_width / 2
        y_pos = y_axis * self.rec_height - self.rec_height / 2

        if not clear:
            for x, x_idx in zip(x_pos, x_axis):
                for y, y_idx in zip(y_pos, y_axis):
                    x1, y1 = int(x - self.rec_width / 2), int(y - self.rec_width / 2)
                    x2, y2 = int(x + self.rec_height / 2), int(y + self.rec_height / 2)

                    if y_idx > 1 and y_idx < self.level_height and x_idx > 1 and x_idx < self.level_width:

                        if block_name == 'bird':
                            x_center = np.average(x_pos)
                            y_center = np.average(y_pos)
                            r = np.sqrt((x - x_center) ** 2 + (y - y_center) ** 2) / np.max(
                                [x_pos - x_center, y_pos - y_center])
                            if r > 1.2:
                                continue

                        if self.rects[y_idx][x_idx] is None:
                            self.rects[y_idx][x_idx] = \
                                self.draw_canvas.create_rectangle(x1, y1, x2, y2, fill = fill_color, tag = f'rectangle',
                                                                  outline = fill_color)
                            self.canvas[y_idx, x_idx] = self.material_id

        if clear:
            for x, x_idx in zip(x_pos, x_axis):
                for y, y_idx in zip(y_pos, y_axis):
                    if y_idx > 1 and y_idx < self.level_height and x_idx > 1 and x_idx < self.level_width:

                        if block_name == 'bird':
                            x_center = np.average(x_pos)
                            y_center = np.average(y_pos)
                            r = np.sqrt((x - x_center) ** 2 + (y - y_center) ** 2) / np.max(
                                [x_pos - x_center, y_pos - y_center])
                            if r > 1.2:
                                continue

                        self.canvas[y_idx, x_idx] = 0
                        self.draw_canvas.delete(self.rects[y_idx][x_idx])
                        self.rects[y_idx][x_idx] = None

    def hover(self, event):
        self.draw_canvas.delete('hover')
        fill_color = self.colors[self.material_id - 1]

        x_index = round((event.x + (self.rec_width / 2) - 0) / self.rec_width)
        y_index = round((event.y + (self.rec_height / 2) - 0) / self.rec_height)

        block_width, block_height, block_name = self.selected_block

        x_axis = np.array([x for x in range(x_index, x_index + block_width)])
        y_axis = np.array([y for y in range(y_index, y_index + block_height)])
        x_pos = x_axis * self.rec_width - self.rec_width / 2
        y_pos = y_axis * self.rec_height - self.rec_height / 2

        for x, x_idx in zip(x_pos, x_axis):
            for y, y_idx in zip(y_pos, y_axis):
                if y_idx > 1 and y_idx < self.level_height and x_idx > 1 and x_idx < self.level_width:

                    if block_name == 'bird':
                        x_center = np.average(x_pos)
                        y_center = np.average(y_pos)
                        r = np.sqrt((x - x_center) ** 2 + (y - y_center) ** 2) / np.max([x_pos - x_center, y_pos - y_center])
                        if r > 1.2:
                            continue

                    x1, y1 = int(x - self.rec_width / 2), int(y - self.rec_width / 2)
                    x2, y2 = int(x + self.rec_height / 2), int(y + self.rec_height / 2)
                    self.draw_canvas.create_rectangle(x1, y1, x2, y2, fill = fill_color, tag = f'hover')

    def create_level(self):
        if self.figure_canvas is not None:
            plt.close(self.fig)
            self.figure_canvas.get_tk_widget().destroy()
            self.img_canvas.delete(self.figure_canvas)
            if self.toolbar is not None:
                self.toolbar.destroy()

        self.fig, self.ax = plt.subplots(1, 1, dpi = 100)

        temp_level_img = DecoderUtils.trim_img(self.canvas)

        level = self.level_img_decoder.decode_level(temp_level_img)

        # game_manager = GameManager(Config.get_instance())
        # game_manager.start_game()
        # game_manager.switch_to_level_elements(level.get_used_elements(), 4)

        self.ax.imshow(np.flip(temp_level_img, axis = 0), origin = 'lower')
        self.level_visualizer.create_img_of_structure(
            level.get_used_elements(), use_grid = False, ax = self.ax, scaled = True
        )

        # self.level_visualizer.create_img_of_level(level, use_grid = False, ax = self.ax)

        if len(level.get_used_elements()) == 0:
            self.ax.set_title("No Level Decoded")

        self.figure_canvas = FigureCanvasTkAgg(self.fig, master = self.img_canvas)
        self.figure_canvas.draw()
        self.figure_canvas.get_tk_widget().pack(fill = BOTH, expand = 1)

        self.toolbar = NavigationToolbar2Tk(self.figure_canvas, self.img_canvas)
        self.toolbar.update()

    def visualize_rectangle(self):
        if self.figure_canvas is not None:
            plt.close(self.fig)
            self.figure_canvas.get_tk_widget().destroy()
            self.img_canvas.delete(self.figure_canvas)
            if self.toolbar is not None:
                self.toolbar.destroy()

        self.fig, self.ax = plt.subplots(1, 1, dpi = 100)

        material_id = int(self.rec_idx.get('0.0', 'end'))

        self.level_img_decoder.visualize_rectangle(DecoderUtils.trim_img(self.canvas), material_id, ax = self.ax)

        self.figure_canvas = FigureCanvasTkAgg(self.fig, master = self.img_canvas)
        self.figure_canvas.draw()
        self.figure_canvas.get_tk_widget().pack(fill = BOTH, expand = 1)

        self.toolbar = NavigationToolbar2Tk(self.figure_canvas, self.img_canvas)
        self.toolbar.update()


    def block_cursor(self, block):
        self.selected_block = (block['width'], block['height'], block['name'])
        if block['name'] == 'bird':
            self.material_id = 4

    def load_level(self):
        self.delete_drawing()

        load_level = int(self.level_select.get('0.0', 'end'))

        test_environment = TestEnvironment('generated/single_structure')
        level = test_environment.get_level(load_level)
        level_img_encoder = LevelImgEncoder()
        elements = level.get_used_elements()
        encoded_img = level_img_encoder.create_calculated_img(elements)

        pad_left = int((self.level_width - encoded_img.shape[1]) / 2)
        pad_right = int((self.level_width - encoded_img.shape[1]) / 2)
        pad_top = self.level_height - encoded_img.shape[0]

        if pad_left + encoded_img.shape[1] + pad_right < self.level_width:
            pad_right += 1

        padded_img = np.pad(encoded_img, ((pad_top, 0), (pad_left, pad_right)), 'constant')

        for x_idx in range(padded_img.shape[1]):
            for y_idx in range(padded_img.shape[0]):

                if padded_img[y_idx, x_idx] != 0:
                    x = x_idx * self.rec_width - self.rec_width / 2
                    y = y_idx * self.rec_height - self.rec_height / 2

                    x1, y1 = int(x - self.rec_width / 2), int(y - self.rec_width / 2)
                    x2, y2 = int(x + self.rec_height / 2), int(y + self.rec_height / 2)
                    fill_color = self.colors[int(padded_img[y_idx, x_idx]) - 1]
                    self.rects[y_idx][x_idx] = \
                        self.draw_canvas.create_rectangle(x1, y1, x2, y2, fill = fill_color, tag = f'rectangle',
                                                          outline = fill_color)
                    self.canvas[y_idx, x_idx] = int(padded_img[y_idx, x_idx])

    def delete_drawing(self):
        self.draw_canvas.delete('rectangle')
        self.rects = [[None for _ in range(self.canvas.shape[0])] for _ in range(self.canvas.shape[1])]
        self.canvas = np.zeros((self.level_height + 1, self.level_width + 1))


if __name__ == '__main__':
    level_drawer = LevelDrawer()
    mainloop()
