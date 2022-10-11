import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle

from util.Config import Config


class GanDecodingVisualization:

    def __init__(self, dpi = 100, add_color_bar = True, add_tab = False, plot_to_file = False,
                 plot_show_immediately = False, level_drawer = None, disable = False):

        self.config = Config.get_instance()

        self.dpi = dpi
        self.plot_counter = 0

        self.level_drawer = level_drawer

        self.add_color_bar = add_color_bar

        self.add_tab = add_tab
        self.plot_to_file = plot_to_file
        self.plot_show_immediately = plot_show_immediately
        self.disable = disable

    def plot_img(self, img, title = None, ax = None, flip = False):
        if self.disable:
            return

        if ax is None:
            fig, ax = plt.subplots(dpi = self.dpi)
            im = ax.imshow(img)

            if title is not None:
                ax.set_title(title)

            if self.add_color_bar:
                plt.colorbar(im)

            if self.plot_to_file:
                fig_name = self.config.get_conv_debug_img_file(
                    f'{self.plot_counter}_{title.replace(" ", "_").lower() if title is not None else "Img"}')
                fig.savefig(fig_name)
                self.plot_counter += 1
                plt.close(fig)

            if self.plot_show_immediately:
                plt.show()

            if self.add_tab:
                self.level_drawer.add_tab_to_fig_canvas(fig, ax, name = title)

            if not self.plot_to_file and not self.plot_show_immediately and not self.add_tab:
                plt.close(fig)

        else:
            if flip:
                ax.imshow(np.flip(img, axis = 0))
            else:
                ax.imshow(img)
            ax.set_title(title)

    def create_plt_array(self):
        fig, axs = plt.subplots(5, 3, dpi = self.dpi)
        axs = axs.flatten()
        fig.delaxes(axs[-1])
        fig.delaxes(axs[-2])
        return fig, axs

    def plot_matrix_complete(self, matrix, blocks = None, title = None, add_max = True, position = None,
                             delete_rectangles = None, flipped = False, selected_block = None, save_name = None):

        if self.disable:
            return

        fig, axs = self.create_plt_array()

        for layer_idx in range(matrix.shape[-1]):
            _plot_img = matrix[:, :, layer_idx]

            ax_title = ''
            if blocks is not None:
                ax_title = blocks[layer_idx]['name'] + (f' {np.round(np.max(_plot_img).item() * 100) / 100}' if add_max else '')

            self.plot_img(_plot_img, ax_title, ax = axs[layer_idx], flip = flipped)
            color = 'blue' if (selected_block is not None and selected_block == layer_idx) else 'red'

            if position is not None:
                height = _plot_img.shape[0]
                if flipped:
                    axs[layer_idx].scatter([position[1]], [height - position[0] - 1], color = 'red', s = 1)
                else:
                    axs[layer_idx].scatter([position[1]], [position[0]], color = 'red', s = 1)

            if delete_rectangles is not None:
                height = _plot_img.shape[0]
                (start, end, top, bottom) = delete_rectangles[layer_idx]
                if flipped:
                    axs[layer_idx].add_patch(
                        Rectangle((start, height - top - 1), end - start, top - bottom,
                                  fill = False, color = color, linewidth = 1))
                else:
                    axs[layer_idx].add_patch(
                        Rectangle((start, top), end - start, bottom - top,
                                  fill = False, color = color, linewidth = 1))

        if title is not None:
            fig.suptitle(title)

        fig.tight_layout()

        if self.plot_to_file:
            file_name = f'{self.plot_counter}_{title.replace(" ", "_").lower() if title is not None else "matrix"}'
            if save_name is not None:
                file_name = f'{self.plot_counter}_{save_name}'
            fig.savefig(self.config.get_conv_debug_img_file(file_name))
            self.plot_counter += 1
            plt.close(fig)

        if self.plot_show_immediately:
            plt.show()

        if self.add_tab:
            self.level_drawer.add_tab_to_fig_canvas(fig, None, name = title)

        if not self.plot_to_file and not self.plot_show_immediately and not self.add_tab:
            plt.close(fig)
