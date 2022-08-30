from tkinter import *
from tkinter import ttk
from tkinter.ttk import Notebook
from typing import Dict, List

import numpy as np
from loguru import logger
from matplotlib import pyplot as plt
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from applications import TkinterUtils
from applications.GeneratorApplication import GeneratorApplication
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
        self.draw_mode = StringVar()
        self.draw_mode.set('LevelImg')
        self.recalibrate = IntVar()

        self.block_data = Config.get_instance().get_encoding_data(f"encoding_res_{Constants.resolution}")
        del self.block_data['resolution']

        self.create_frames()

        self.grid_drawer = GridDrawer(
            level_drawer = self,
            frame = self.draw_canvas,
            draw_mode = self.draw_mode,
            draw_area_width = self.draw_area_width,
            draw_area_height = self.draw_area_height,
            level_height = 50,
            level_width = 50,
        )

        self.create_cursor_button()

        self.create_figure_frame()
        self.create_img_tab_panes()

        self.level_img_decoder = LevelImgDecoder()
        self.level_id_img_decoder = LevelIdImgDecoder()
        self.level_img_decoder_visualization = LevelImgDecoderVisualization()
        self.level_visualizer = LevelVisualizer()
        self.game_manager = GameManager(Config.get_instance())

        self.control_buttons()

        self.generator_application = GeneratorApplication(self.btm_frame, self)

    def create_frames(self):

        # Layout Frames
        self.top_frame = Frame(self.master, width = self.canvas_width, height = 50, pady = 3, padx = 3)
        self.center_frame = Frame(self.master, width = self.canvas_width, height = self.canvas_height - 100, pady = 3, padx = 3)
        self.btm_frame = Frame(self.master, width = self.canvas_width, height = 50, pady = 3, padx = 3)

        # Element Frames
        self.left_frame = Frame(self.center_frame, width = int(self.canvas_width / 2), height = self.canvas_height - 100,
                                pady = 3, padx = 3)
        self.right_frame = Frame(self.center_frame, width = int(self.canvas_width), height = self.canvas_height - 100,
                                 pady = 3, padx = 3)
        self.button_frame = Frame(self.center_frame, width = 40, height = self.canvas_height, pady = 3, padx = 3)

        # layout all of the main containers
        self.master.grid_rowconfigure(1, weight = 1)
        self.master.grid_columnconfigure(0, weight = 1)

        self.top_frame.grid(row = 0, sticky = "n")
        self.center_frame.grid(row = 1, sticky = "news")
        self.btm_frame.grid(row = 2, sticky = "s")

        self.button_frame.pack(side = LEFT)
        self.left_frame.pack(side = LEFT)
        self.right_frame.pack(side = RIGHT)

        self.draw_canvas = Canvas(self.left_frame, bg="white", height=self.draw_area_width, width=self.draw_area_width)
        self.draw_canvas.pack(fill = BOTH)

    def create_figure_frame(self):
        self.tab_control = Notebook(self.right_frame)
        self.tabs: List[Dict] = []
        self.selected_tab = 0
        self.create_img_tab_panes(2)
        self.tab_control.bind(
            "<<NotebookTabChanged>>",
            lambda event: setattr(self, 'selected_tab', self.tab_control.index(self.tab_control.select()))
        )

    def create_img_tab_panes(self, panel_amounts = 1):
        self.tabs = TkinterUtils.clear_tab_panes(self.tab_control, self.tabs)

        for tab_index in range(panel_amounts):
            create_tab = Frame(self.tab_control)
            self.tab_control.add(create_tab, text = 'Combined' if tab_index == 0 else f'Layer {tab_index}')
            self.tabs.append(dict(
                frame = create_tab,
            ))

        self.tab_control.pack(expand = 1, fill = "both")

        for tab_index in range(panel_amounts):
            self.create_img_canvas(tab_index)

    def create_img_canvas(self, tab = -1):
        if tab == -1: tab = self.selected_tab

        matplot_wrapper_canvas = Canvas(
            self.tabs[tab]['frame'],
            bg = "white", height = self.draw_area_width, width = self.draw_area_width)
        matplot_wrapper_canvas.pack(expand = YES, side = LEFT, pady = (30, 30), padx = (30, 30))
        self.tabs[tab]['matplot_wrapper_canvas'] = matplot_wrapper_canvas

    def control_buttons(self):

        self.recalibrate_button = Checkbutton(self.top_frame, text = "Recalibrate", variable = self.recalibrate)
        self.recalibrate_button.pack()

        # button that displays the plot
        self.decode_level = Button(self.top_frame, command = lambda: self.create_level(), height = 2,
                                   width = 15, text = "Decode Drawing")
        self.decode_level.pack(side = LEFT, padx = (20, 10))

        wrapper = Canvas(self.top_frame)
        wrapper.pack(side = LEFT, padx = (10, 10), pady = (20, 10))
        label = Label(wrapper, text = "Material Rectangle:")
        label.pack(side = TOP)

        self.rec_idx = Text(wrapper, height = 1, width = 3)
        self.rec_idx.insert('0.0', '1')
        self.rec_idx.pack(side = TOP)

        # button that displays the plot
        self.viz_rectangles = Button(self.top_frame, command = lambda: self.visualize_rectangle(), height = 2,
                                     width = 18, text = "Visualize Rectangles")
        self.viz_rectangles.pack(side = LEFT, padx = (10, 10), pady = (20, 10))

        wrapper = Canvas(self.top_frame)
        wrapper.pack(side = LEFT, padx = (10, 10), pady = (20, 10))
        label = Label(wrapper, text = "Load level ID:")
        label.pack(side = TOP)

        self.level_select = Text(wrapper, height = 1, width = 3)
        self.level_select.insert('0.0', '0')
        self.level_select.pack(side = TOP)

        # button that displays the plot
        self.plot_button = Button(self.top_frame, command = lambda: self.load_level(), height = 2, width = 10,
                                  text = "Load Level")
        self.plot_button.pack(side = LEFT, padx = (10, 10), pady = (20, 10))

        # button that displays the plot
        self.select_viz = Button(self.top_frame,
                                 command = lambda: self.level_img_decoder_visualization.create_tree_of_one_encoding(
                                     self.grid_drawer.current_elements()), height = 2, width = 18,
                                 text = "Visualize Block Selection")
        self.select_viz.pack(side = LEFT, padx = (10, 10), pady = (20, 10))

        # button that displays the plot
        self.plot_button = Button(self.top_frame, command = lambda: self.grid_drawer.delete_drawing(),
                                  height = 2, width = 10, text = "Delete")
        self.plot_button.pack(side = LEFT, padx = (10, 10), pady = (20, 10))

        self.start_game_button = Button(self.top_frame, command = lambda: self.start_game(), height = 2, width = 15, text = "Start Game")
        self.start_game_button.pack(side = LEFT, padx = (10, 10), pady = (20, 10))

        self.play_level = Button(self.top_frame, command = lambda: self.run_level_in_game(), height = 2, width = 15, text = "Send To Game")
        self.play_level.pack(side = LEFT, padx = (10, 10), pady = (20, 10))

        wrapper = Canvas(self.top_frame)
        wrapper.pack(side = LEFT, padx = (10, 10), pady = (20, 10))
        label = Label(wrapper, text = "Decoding Mode:")
        label.pack(side = TOP)

        self.combobox = ttk.Combobox(wrapper, textvariable = self.draw_mode)
        self.combobox['values'] = ('LevelImg', 'OneElement')
        self.combobox.set(self.draw_mode.get())
        self.combobox['state'] = 'readonly'
        self.combobox.bind('<<ComboboxSelected>>', lambda event: self.grid_drawer.delete_drawing())
        self.combobox.pack(side = TOP)

    def create_cursor_button(self):

        self.selected_button = dict()

        temp_button = Button(
            master = self.button_frame,
            command = lambda: self.grid_drawer.block_cursor(
                dict(width = 1, height = 1, name = '1x1', button = '1x1')
            ),
            height = 2,
            width = 10,
            text = '1 x 1'
        )
        temp_button.pack(side = TOP, pady = (10, 2), padx = (10, 10))
        self.selected_button['1x1'] = temp_button

        for block_idx, block in self.block_data.items():
            rotated_string = '\n Rotated' if block['rotated'] else ''
            temp_button = Button(
                master = self.button_frame,
                command = lambda block = dict(width = block['width'] + 1, height = block['height'] + 1,
                                              name = block['name'], button = f"{block['name']}_{rotated_string}"):
                                    self.grid_drawer.block_cursor(block),
                height = 2,
                width = 10,
                text = f"{block['name']} {rotated_string}"
            )
            temp_button.pack(side = TOP, pady = (2, 2), padx = (2, 2))
            self.selected_button[f"{block['name']}_{rotated_string}"] = temp_button

        temp_button = Button(
            master = self.button_frame,
            command = lambda: self.grid_drawer.block_cursor(dict(width = 7, height = 7, name = 'bird', button = 'bird')),
            height = 2,
            width = 10,
            text = 'Bird'
        )
        temp_button.pack(side = TOP, pady = (2, 10), padx = (2, 2))
        self.selected_button['bird'] = temp_button

        self.grid_drawer.block_cursor(dict(width = 1, height = 1, name = '1x1', button = '1x1'))

    def key_event(self, event):
        print(event.char)
        if event.char in ['1', '2', '3', '4']:
            self.grid_drawer.material_id = int(event.char)

    def create_level(self, tab = -1):
        self.clear_figure_canvas()

        fig, ax = plt.subplots(1, 1, dpi = 100)
        self.tabs[tab]['fig'] = fig
        self.tabs[tab]['ax'] = ax

        temp_level_img = DecoderUtils.trim_img(self.grid_drawer.current_elements())

        if self.draw_mode.get() == 'LevelImg':
            self.level = self.level_img_decoder.decode_level(temp_level_img)
        else:
            self.level = self.level_id_img_decoder.decode_level(
                temp_level_img,
                recalibrate = self.recalibrate.get(),
                small_version = self.generator_application.small_version
            )

        ax.imshow(np.flip(temp_level_img, axis = 0), origin = 'lower')
        self.level_visualizer.create_img_of_structure(
            self.level.get_used_elements(), use_grid = False, ax = ax, scaled = True
        )

        if len(self.level.get_used_elements()) == 0:
            ax.set_title("No Level Decoded")

        self.draw_img_to_fig_canvas()

    def new_fig(self):
        self.fig, self.ax = plt.subplots(1, 1, dpi = 100)
        return self.fig, self.ax

    def clear_figure_canvas(self):
        for tab in self.tabs:
            if 'fig' in tab.keys():
                plt.close(tab['fig'])

            if 'matplot_canvas' in tab.keys():
                tab['matplot_canvas'].get_tk_widget().destroy()

            if 'toolbar' in tab.keys():
                tab['toolbar'].destroy()

    def visualize_rectangle(self):
        self.clear_figure_canvas()

        self.fig, self.ax = plt.subplots(1, 1, dpi = 100)

        material_id = int(self.rec_idx.get('0.0', 'end'))

        trimmed_img = DecoderUtils.trim_img(self.grid_drawer.current_elements())
        self.level_img_decoder_visualization.visualize_rectangle(
            trimmed_img, material_id, ax = self.ax
        )

        self.draw_img_to_fig_canvas()

    def load_level(self):
        load_level = int(self.level_select.get('0.0', 'end'))

        test_environment = TestEnvironment('generated/single_structure')
        level = test_environment.get_level(load_level)
        level_img_encoder = LevelImgEncoder()
        elements = level.get_used_elements()

        if self.draw_mode.get() == 'LevelImg':
            encoded_img = level_img_encoder.create_calculated_img(elements)
        else:
            encoded_img = level_img_encoder.create_one_element_img(elements)

        self.draw_level(encoded_img)

    def draw_level(self, encoded_img, tab = -1):
        if tab == -1: tab = self.selected_tab
        self.grid_drawer.delete_drawing(tab)

        logger.debug(np.unique(encoded_img))

        level_width, level_height = self.grid_drawer.get_level_dims(tab)

        if level_width < encoded_img.shape[1] or level_height < encoded_img.shape[0]:
            max_dim = np.max(encoded_img.shape) + 2
            self.grid_drawer.set_level_dims(max_dim, max_dim, tab = tab)
            self.grid_drawer.create_grid(tab)

        level_width, level_height = self.grid_drawer.get_level_dims(tab)
        pad_left = int((level_width - encoded_img.shape[1]) / 2)
        pad_right = int((level_width - encoded_img.shape[1]) / 2)
        pad_top = level_height - encoded_img.shape[0]
        padded_img = np.pad(encoded_img, ((pad_top, 0), (pad_left, pad_right)), 'constant')

        for x_idx in range(padded_img.shape[1]):
            for y_idx in range(padded_img.shape[0]):

                use_x_idx = x_idx + 1

                if padded_img[y_idx, x_idx] != 0:
                    x = use_x_idx * self.grid_drawer.rec_width - self.grid_drawer.rec_width / 2
                    y = y_idx * self.grid_drawer.rec_height - self.grid_drawer.rec_height / 2

                    x1, y1 = int(x - self.grid_drawer.rec_width / 2), int(y - self.grid_drawer.rec_width / 2)
                    x2, y2 = int(x + self.grid_drawer.rec_height / 2), int(y + self.grid_drawer.rec_height / 2)

                    if self.draw_mode.get() == 'LevelImg':
                        fill_color = self.grid_drawer.colors[int(padded_img[y_idx, x_idx]) - 1]
                    else:
                        fill_color = self.grid_drawer.colors[int((padded_img[y_idx, x_idx] - 1) / 13)]

                    self.grid_drawer.rects(tab)[y_idx][use_x_idx] = \
                        self.grid_drawer.canvas(tab).create_rectangle(
                            x1, y1, x2, y2, fill = fill_color, tag = f'rectangle', outline = fill_color)
                    self.grid_drawer.elements(tab)[y_idx, use_x_idx] = int(padded_img[y_idx, x_idx])

    def draw_img_to_fig_canvas(self, tab = -1):
        if tab == -1: tab = self.selected_tab
        matplot_canvas = FigureCanvasTkAgg(self.tabs[tab]['fig'], master = self.tabs[tab]['matplot_wrapper_canvas'])
        matplot_canvas.draw()
        matplot_canvas.get_tk_widget().pack(fill = BOTH, expand = 1)
        toolbar = NavigationToolbar2Tk(matplot_canvas, self.tabs[tab]['matplot_wrapper_canvas'])
        toolbar.update()

        self.tabs[tab]['matplot_canvas'] = matplot_canvas
        self.tabs[tab]['toolbar'] = toolbar

    def start_game(self):
        self.game_manager.start_game()

    def run_level_in_game(self):
        if self.level is None:
            logger.debug("No level decoded")
            return

        self.game_manager.switch_to_level(self.level, stop_time = False)


if __name__ == '__main__':
    level_drawer = LevelDrawer()
    mainloop()
