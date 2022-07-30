import numpy as np


def recalibrate_blocks(created_level_elements):
    # Post process
    sorted_elements = sorted(created_level_elements, key = lambda _element: (_element.y, _element.x))
    for element_idx, element in enumerate(sorted_elements):
        # search for element lower then itself
        for lower_element in sorted_elements[:element_idx]:
            if element.shape_polygon.overlaps(lower_element.shape_polygon):

                if abs(lower_element.y - element.y) <= 0.1:
                    # move element upwards out of the overlapping element
                    left_x = lower_element.x + lower_element.width / 2
                    right_x = element.x - element.width / 2

                    move_upwards = abs(left_x - right_x)
                    element.x += move_upwards
                else:
                    # move element upwards out of the overlapping element
                    lower_element_y = lower_element.y + lower_element.height / 2
                    upper_element_y = element.y - element.height / 2

                    move_upwards = abs(upper_element_y - lower_element_y)
                    element.y += move_upwards

    # move everything to zero
    lowest_value = np.min(list(map(lambda _element: _element.y - element.height / 2, sorted_elements)))
    for element_idx, element in enumerate(sorted_elements):
        element.y -= lowest_value

    return sorted_elements
