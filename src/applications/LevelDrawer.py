from tkinter import *

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from converter.to_img_converter.LevelImgDecoder import LevelImgDecoder
from converter.to_img_converter.LevelImgEncoder import LevelImgEncoder
from level import Constants
from level.LevelVisualizer import LevelVisualizer
from test.TestEnvironment import TestEnvironment
from util.Config import Config


class LevelDrawer:
    def __init__(self):
        self.canvas_width = 1500
        self.canvas_height = 700

        self.draw_area_start_x = 50
        self.draw_area_start_y = 50
        self.draw_area_width = 500
        self.draw_area_height = 500

        self.level_height = 80
        self.level_width = 80

        self.canvas = np.zeros((self.level_height + 1, self.level_width + 1))
        self.rects = [[None for _ in range(self.canvas.shape[0])] for _ in range(self.canvas.shape[1])]

        self.rec_height = self.draw_area_height / self.level_height
        self.rec_width = self.draw_area_width / self.level_width

        self.myrect = None

        self.master = Tk()
        self.master.title("Painting using Ovals")
        self.master.bind('<Key>', lambda event: self.key_event(event))

        self.selected_block = None
        self.create_button()

        self.window = Canvas(self.master, width = self.canvas_width, height = self.canvas_height)
        self.window.pack()

        self.draw_canvas = Canvas(self.window, width = self.draw_area_width, height = self.draw_area_height)
        self.draw_canvas.pack(expand = YES, side = LEFT, pady = (30, 30), padx = (30, 30))

        self.draw_canvas.bind("<B1-Motion>", self.paint)
        self.draw_canvas.bind("<Button-1>", self.paint)
        self.draw_canvas.bind("<Motion>", self.hover)

        self.draw_canvas.bind("<B3-Motion>", lambda event: self.paint(event, clear = True))
        self.draw_canvas.bind("<Button-3>", lambda event: self.paint(event, clear = True))
        # message = Label(self.draw_canvas, text = "Press and Drag the mouse to draw")
        # message.pack(side = BOTTOM)

        self.img_canvas = Canvas(self.window, width = self.draw_area_width, height = self.draw_area_height)
        self.img_canvas.pack(expand = NO, side = RIGHT)


        self.figure_canvas = None
        self.fig, self.ax = None, None

        self.level_img_decoder = LevelImgDecoder()
        self.level_visualizer = LevelVisualizer()

        self.create_grid()
        self.material_id = 1
        self.colors = ['#a8d399', '#aacdf6', '#f98387', '#dbcc81']

        # button that displays the plot
        plot_button = Button(
            master = self.master,
            command = lambda: self.create_level(),
            height = 2,
            width = 10,
            text = "Generate"
        )

        plot_button.pack(side = BOTTOM)

        # button that displays the plot
        plot_button = Button(
            master = self.master,
            command = lambda: self.load_level(),
            height = 2,
            width = 10,
            text = "Load Level"
        )

        plot_button.pack(side = BOTTOM)


    def create_button(self):
        self.button_canvas = Canvas(self.master, width = self.canvas_width, height = 10)
        self.button_canvas.pack()

        temp_button = Button(
            master = self.button_canvas,
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
                master = self.button_canvas,
                command = lambda block = dict(width = block['width'] + 1, height = block['height'] + 1, name = block['name']): self.block_cursor(block),
                height = 2,
                width = 10,
                text = block['name']
            )
            temp_button.pack(side = LEFT, pady = (10, 10), padx = (2, 2))

        temp_button = Button(
            master = self.button_canvas,
            command = lambda: self.block_cursor(dict(width = 5, height = 5, name = 'bird')),
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
        for i in range(self.level_height + 1):
            self.draw_canvas.create_line(
                self.rec_height * i, self.rec_height,
                self.rec_height * i, self.draw_area_height,
                width = 1)

        for i in range(self.level_width + 1):
            self.draw_canvas.create_line(
                self.rec_width, self.rec_width * i,
                self.draw_area_width, self.rec_width * i,
                width = 1)

    def paint(self, event, clear = False):
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
                        self.rects[y_idx][x_idx] = \
                            self.draw_canvas.create_rectangle(x1, y1, x2, y2, fill = fill_color, tag = f'rectangle')
                        self.canvas[y_idx, x_idx] = self.material_id

        if clear:
            for x, x_idx in zip(x_pos, x_axis):
                for y, y_idx in zip(y_pos, y_axis):
                    if y_idx > 1 and y_idx < self.level_height and x_idx > 1 and x_idx < self.level_width:
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
                    x1, y1 = int(x - self.rec_width / 2), int(y - self.rec_width / 2)
                    x2, y2 = int(x + self.rec_height / 2), int(y + self.rec_height / 2)
                    self.draw_canvas.create_rectangle(x1, y1, x2, y2, fill = fill_color, tag = f'hover')

    def create_level(self):
        if self.figure_canvas is not None:
            plt.close(self.fig)
            self.figure_canvas.get_tk_widget().destroy()
            self.img_canvas.delete(self.figure_canvas)

        self.fig, self.ax = plt.subplots(1, 1, dpi = 100)

        level = self.level_img_decoder.decode_level(self.canvas)
        self.level_visualizer.create_img_of_level(level, use_grid = False, ax = self.ax)

        if len(level.get_used_elements()) == 0:
            self.ax.set_title("No Level Decoded")

        self.figure_canvas = FigureCanvasTkAgg(self.fig, master = self.img_canvas)
        self.figure_canvas.draw()
        self.figure_canvas.get_tk_widget().pack(fill = BOTH, expand = 1)

    def block_cursor(self, block):
        self.selected_block = (block['width'], block['height'], block['name'])
        pass

    def load_level(self):
        test_environment = TestEnvironment('generated/single_structure')
        level = test_environment.get_level(0)
        level_img_encoder = LevelImgEncoder()
        elements = level.get_used_elements()
        encoded_img = level_img_encoder.create_calculated_img(elements)

        level = self.level_img_decoder.decode_level(encoded_img)
        self.level_visualizer.create_img_of_level(level, use_grid = False)

        for x_idx in range(encoded_img.shape[1]):
            for y_idx in range(encoded_img.shape[0]):

                if encoded_img[y_idx, x_idx] != 0:

                    x = x_idx * self.rec_width - self.rec_width / 2
                    y = y_idx * self.rec_height - self.rec_height / 2

                    x1, y1 = int(x - self.rec_width / 2), int(y - self.rec_width / 2)
                    x2, y2 = int(x + self.rec_height / 2), int(y + self.rec_height / 2)
                    self.rects[y_idx][x_idx] = \
                        self.draw_canvas.create_rectangle(x1, y1, x2, y2, fill = self.colors[int(encoded_img[y_idx, x_idx]) - 1], tag = f'rectangle')
                    self.canvas[y_idx, x_idx] = self.material_id


if __name__ == '__main__':
    level_drawer = LevelDrawer()
    mainloop()
