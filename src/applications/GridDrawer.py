from tkinter import *

import numpy as np

from level import Constants
from util import Utils


class GridDrawer:
    def __init__(self, level_drawer, frame, draw_mode, draw_area_width, draw_area_height, level_height, level_width):
        self.level_drawer = level_drawer
        self.left_frame = frame

        self.draw_mode = draw_mode

        self.draw_area_width = draw_area_width
        self.draw_area_height = draw_area_height

        self.level_height = level_height
        self.level_width = level_width

        self.colors = ['#a8d399', '#aacdf6', '#f98387', '#dbcc81']

        self.create_draw_canvas()
        self.create_grid()

        self.material_id = 1

        self.init_blocks()

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

        block_name, x_axis, x_pos, y_axis, y_pos = self.get_block_position(x_index, y_index, self.selected_block)


        if not clear:
            self.set_block(block_name, fill_color, self.material_id, x_axis, x_pos, y_axis, y_pos)

        single_element = self.draw_mode.get() != '' and self.draw_mode.get() != 'LevelImg'
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
                        if single_element:
                            self.draw_canvas.delete(str((x_idx, y_idx)))
                        else:
                            self.draw_canvas.delete(self.rects[y_idx][x_idx])
                            self.rects[y_idx][x_idx] = None


    def hover(self, event):
        self.draw_canvas.delete('hover')

        fill_color = self.colors[self.material_id - 1]
        lighten_fill_color = Utils.lighten_color(fill_color, 0.5)

        x_index = round((event.x + (self.rec_width / 2) - 0) / self.rec_width)
        y_index = round((event.y + (self.rec_height / 2) - 0) / self.rec_height)

        block_name, x_axis, x_pos, y_axis, y_pos = self.get_block_position(x_index, y_index, self.selected_block)

        single_element = self.draw_mode.get() != 'LevelImg'

        for x_pos_idx, (x, x_idx) in enumerate(zip(x_pos, x_axis)):
            for y_pos_idx, (y, y_idx) in enumerate(zip(y_pos, y_axis)):
                if 1 < y_idx < self.level_height and 1 < x_idx < self.level_width:

                    if block_name == 'bird':
                        x_center = np.average(x_pos)
                        y_center = np.average(y_pos)
                        r = np.sqrt((x - x_center) ** 2 + (y - y_center) ** 2) / np.max([x_pos - x_center, y_pos - y_center])
                        if r > 1.2:
                            continue

                    x1, y1 = int(x - self.rec_width / 2), int(y - self.rec_width / 2)
                    x2, y2 = int(x + self.rec_height / 2), int(y + self.rec_height / 2)

                    next_color = fill_color
                    if single_element:
                        if x_pos_idx == int(len(x_axis) / 2) and y_pos_idx == int(len(y_axis) - 1):
                            next_color = lighten_fill_color

                    self.draw_canvas.create_rectangle(x1, y1, x2, y2, fill = next_color, tag = f'hover')

    def get_block_position(self, x_index, y_index, block):
        block_width, block_height, block_name = block
        x_axis = np.array([x for x in range(x_index, x_index + block_width)])
        y_axis = np.array([y for y in range(y_index, y_index + block_height)])
        x_pos = x_axis * self.rec_width - self.rec_width / 2
        y_pos = y_axis * self.rec_height - self.rec_height / 2
        return block_name, x_axis, x_pos, y_axis, y_pos

    def set_block(self, block_name, fill_color, material_id, x_axis, x_pos, y_axis, y_pos):

        single_element = self.draw_mode.get() != '' and self.draw_mode.get() != 'LevelImg'
        lighten_fill_color = Utils.lighten_color(fill_color, 0.6)

        centerpos = (x_axis[int(len(x_axis) / 2)], y_axis[int(len(y_axis) - 1)])

        for x, x_idx in zip(x_pos, x_axis):
            for y, y_idx in zip(y_pos, y_axis):
                x1, y1 = int(x - self.rec_width / 2), int(y - self.rec_width / 2)
                x2, y2 = int(x + self.rec_height / 2), int(y + self.rec_height / 2)

                if 1 < y_idx < self.level_height and 1 < x_idx < self.level_width:

                    if block_name == 'bird':
                        x_center = np.average(x_pos)
                        y_center = np.average(y_pos)
                        r = np.sqrt((x - x_center) ** 2 + (y - y_center) ** 2) / np.max(
                            [x_pos - x_center, y_pos - y_center])
                        if r > 1.2:
                            continue

                    # Only original color the middle element
                    next_color = fill_color
                    if single_element:
                        if x_idx == centerpos[0] and y_idx == centerpos[1]:
                            next_color = lighten_fill_color

                    if self.canvas[y_idx][x_idx] == 0:
                        next_tag = ['rectangle'] + ([str(centerpos)] if single_element else [])
                        self.rects[y_idx][x_idx] = \
                            self.draw_canvas.create_rectangle(
                                x1, y1, x2, y2, fill = next_color,
                                tag = next_tag,
                                outline = fill_color)

                        # Only set center element
                        if single_element:
                            if x_idx == centerpos[0] and y_idx == centerpos[1]:
                                self.canvas[y_idx, x_idx] = (list(Constants.block_names.values()).index(block_name) + 1) + (material_id - 1) * 13
                        else:
                            self.canvas[y_idx, x_idx] = material_id


    def block_cursor(self, block):
        self.selected_block = (block['width'], block['height'], block['name'])
        if block['name'] == 'bird':
            self.material_id = 4

        for button in self.level_drawer.selected_button.values():
            button.config(bg = 'grey')

        self.level_drawer.selected_button[block['button']].config(bg = 'lightblue')

    def delete_drawing(self):
        self.draw_canvas.delete('rectangle')
        self.rects = [[None for _ in range(self.canvas.shape[0])] for _ in range(self.canvas.shape[1])]
        self.canvas = np.zeros((self.level_height + 1, self.level_width + 1))

    def init_blocks(self):

        blocks_placed = 0

        prev_blocks = []

        while blocks_placed <= 4:

            random_x = np.random.randint(3, self.level_width - 4)
            random_y = np.random.randint(3, self.level_width - 4)

            block_amount = len(self.level_drawer.block_data)
            random_block = self.level_drawer.block_data[str(np.random.randint(block_amount))]
            material = np.random.randint(1, 4)

            new_block = (random_block['width'] + 1, random_block['height'] + 1, random_block['name'])

            block_name, x_axis, x_pos, y_axis, y_pos = self.get_block_position(random_x, random_y, new_block)
            xx, yy = np.meshgrid(x_axis, y_axis)
            positions = np.vstack([xx.ravel(), yy.ravel()])

            if np.max(x_axis) > self.level_width or np.max(y_axis) > self.level_height:
                continue

            overlapping = False
            for comp_pos in prev_blocks:
                pos_stack = np.hstack([positions, comp_pos])
                if np.unique(pos_stack, axis = 1).shape[-1] != pos_stack.shape[-1]:
                    overlapping = True
                    break

            if overlapping:
                continue

            self.set_block(block_name, self.colors[material - 1], material, x_axis, x_pos, y_axis, y_pos)
            blocks_placed += 1
            prev_blocks.append(positions)
