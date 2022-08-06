from tkinter import *

import numpy as np


class GridDrawer:
    def __init__(self, frame, draw_area_width, draw_area_height, level_height, level_width):
        self.left_frame = frame

        self.draw_area_width = draw_area_width
        self.draw_area_height = draw_area_height

        self.level_height = level_height
        self.level_width = level_width

        self.colors = ['#a8d399', '#aacdf6', '#f98387', '#dbcc81']

        self.create_draw_canvas()
        self.create_grid()

        self.material_id = 1

    def create_draw_canvas(self):
        self.draw_canvas = Canvas(self.left_frame, width = self.draw_area_width, height = self.draw_area_height)
        self.draw_canvas.pack(expand = YES, side = LEFT, pady = (30, 30), padx = (30, 30))

        self.draw_canvas.bind("<B1-Motion>", self.paint)
        self.draw_canvas.bind("<Button-1>", self.paint)
        self.draw_canvas.bind("<Motion>", self.hover)
        self.draw_canvas.bind("<B3-Motion>", lambda event: self.paint(event, clear = True))
        self.draw_canvas.bind("<Button-3>", lambda event: self.paint(event, clear = True))

    def set_level_dims(self, height, width):
        self.level_height = height
        self.level_width = width

    def create_grid(self):
        self.draw_canvas.delete('grid_line')
        self.canvas = np.zeros((self.level_height + 1, self.level_width + 1))
        self.rects = [[None for _ in range(self.canvas.shape[0])] for _ in range(self.canvas.shape[1])]

        self.rec_height = self.draw_area_height / self.level_height
        self.rec_width = self.draw_area_width / self.level_width
        self.draw_grid_lines()

    def draw_grid_lines(self):
        for i in range(self.level_height):
            self.draw_canvas.create_line(
                self.rec_height * i, self.rec_height,
                self.rec_height * i, self.draw_area_height - self.rec_height,
                width = 1,
                tag = 'grid_line'
            )

        for i in range(self.level_width):
            self.draw_canvas.create_line(
                self.rec_width, self.rec_width * i,
                self.draw_area_width - self.rec_width, self.rec_width * i,
                width = 1,
                tag = 'grid_line'
            )

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

    def block_cursor(self, block):
        self.selected_block = (block['width'], block['height'], block['name'])
        if block['name'] == 'bird':
            self.material_id = 4

    def delete_drawing(self):
        self.draw_canvas.delete('rectangle')
        self.rects = [[None for _ in range(self.canvas.shape[0])] for _ in range(self.canvas.shape[1])]
        self.canvas = np.zeros((self.level_height + 1, self.level_width + 1))