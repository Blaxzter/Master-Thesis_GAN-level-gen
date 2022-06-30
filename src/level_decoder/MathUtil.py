import itertools

import numpy as np


def get_contour_dims(contour):
    max_x, max_y = max(contour[:, 0]), max(contour[:, 1])
    min_x, min_y = min(contour[:, 0]), min(contour[:, 1])

    width = max_x - min_x
    height = max_y - min_y
    return dict(
        width = width.item(),
        height = height.item(),
        area = (width * height).item(),
        center_pos = np.asarray([min_x + width / 2, min_y + height / 2]),
        max_x = max_x,
        max_y = max_y,
        min_x = min_x,
        min_y = min_y
    )


def get_rectangles(contour):
    rectangles = []
    contour_list = list(contour)
    # Creates additional points on the contour to create functioning rectangles
    create_new_points(contour_list)

    enumerated_contours = list(enumerate(contour_list))

    rec_counter = 0
    for (idx_1, p1), (idx_2, p2), (idx_3, p3), (idx_4, p4) in itertools.combinations(enumerated_contours, 4):

        # Check diags
        diag_1 = np.abs(np.linalg.norm(p1 - p3))
        diag_2 = np.abs(np.linalg.norm(p2 - p4))
        if abs(diag_1 - diag_2) > 0.001:
            continue

        # Check if diagonal corners are orthogonal to each other
        if np.abs(np.dot(p1 - p2, p2 - p3)) > 0.01:
            continue

        if np.abs(np.dot(p3 - p4, p4 - p1)) > 0.01:
            continue

        rectangle = np.asarray([p1, p2, p3, p4]).reshape((4, 1, 2))
        rectangles.append(rectangle)

    return rectangles, contour_list


def get_rectangles_through_diags(contour):
    rectangles = []
    contour = contour.reshape(len(contour), 2)
    contour_list = list(contour)
    # Creates additional points on the contour to create functioning rectangles
    create_new_points(contour_list)

    enumerated_contours = list(enumerate(contour_list))

    counter = 0
    for (p1_idx_1, p1_1), (p1_idx_2, p1_2) in itertools.combinations(enumerated_contours, 2):

        # Check that it is not the next or the previous point in the line
        if p1_idx_1 + 1 == p1_idx_2 or p1_idx_1 - 1 == p1_idx_2:
            continue

        # Check that the point of a diagonal are not horizontal
        if np.min(np.abs(p1_1 - p1_2)) <= 0.01:
            continue

        for (p2_idx_1, p2_1), (p2_idx_2, p2_2) in itertools.combinations(enumerated_contours, 2):

            # Check that it is not the next or the previous point in the line
            if p2_idx_1 + 1 == p2_idx_2 or p2_idx_1 - 1 == p2_idx_2:
                continue

            # Check if the two diagonals share a point
            if p1_idx_1 == p2_idx_1 or p1_idx_1 == p2_idx_2 or p1_idx_2 == p2_idx_1 or p1_idx_2 == p2_idx_2:
                continue

            if np.min(np.abs(p1_1 - p1_2)) <= 0.01:
                continue

            diag_1 = np.abs(np.linalg.norm(p1_1 - p1_2))
            diag_2 = np.abs(np.linalg.norm(p2_1 - p2_2))

            if abs(diag_1 - diag_2) < 0.0001:
                rectangle = np.asarray([p1_1, p2_1, p1_2, p2_2]) \
                    .reshape((4, 1, 2))
                rectangles.append(rectangle)

        counter += 1

    return rectangles, contour_list


def get_next_line(contour_list, idx):
    if idx + 1 >= len(contour_list):
        return (idx, contour_list[-1]), (0, contour_list[0])

    return (idx, contour_list[idx]), (idx + 1, contour_list[idx + 1])


def create_new_points(contour_list: list):

    # Search for inner corners
    counter_1 = 0
    while counter_1 < len(contour_list):
        (idx_1, p1), (idx_2, p2) = get_next_line(contour_list, idx = counter_1)
        (idx_3, p3), (idx_4, p4) = get_next_line(contour_list, idx = counter_1 + 2)

        # Check if it is a straight line
        if np.min(np.abs(p2 - p3)) >= 0.001:
            if np.dot(p1 - p2, p2 - p3) > 0.01:
                cord = intersecting_line(p1, p2, p3, p4)
                if cord is not False:
                    contour_list.insert(idx_2 + 1, np.asarray(cord))
        counter_1 += 1


    added_points = []

    counter_1 = 0
    while counter_1 < len(contour_list):
        (p1_idx_1, p1_1), (p1_idx_2, p1_2) = get_next_line(contour_list, idx = counter_1)
        # Check if it is a straight line
        if np.min(np.abs(p1_1 - p1_2)) >= 0.001:
            counter_1 += 1
            continue

        counter_2 = 0

        while counter_2 + counter_1 + 2 < len(contour_list):
            (p2_idx_1, p2_1), (p2_idx_2, p2_2) = get_next_line(contour_list, idx = counter_2 + counter_1 + 2)

            # if p1_idx_1 == 0 and p1_idx_2 == 1 and p2_idx_1 == 4 and p2_idx_2 == 5:
            #     pass

            if p1_idx_1 == p2_idx_1 or p1_idx_1 == p2_idx_2 or p1_idx_2 == p2_idx_1 or p1_idx_2 == p2_idx_2:
                counter_2 += 1
                continue

            if np.min(np.abs(p2_2 - p2_1)) >= 0.001:
                counter_2 += 1
                continue

            cord = intersecting_line(p1_1, p1_2, p2_1, p2_2)
            if not cord:
                counter_2 += 1
                continue

            d1 = np.linalg.norm(p1_1 - cord)
            d2 = np.linalg.norm(p1_2 - cord)
            d3 = np.linalg.norm(p2_1 - cord)
            d4 = np.linalg.norm(p2_2 - cord)
            if d1 < 0.01 or d2 < 0.01 or d3 < 0.01 or d4 < 0.01:
                counter_2 += 1
                continue

            isnt_on_first_line = d1 + d2 - np.linalg.norm(p1_2 - p1_1) > 0.01
            isnt_on_second_line = d3 + d4 - np.linalg.norm(p2_2 - p2_1) > 0.01
            if isnt_on_first_line and isnt_on_second_line:
                counter_2 += 1
                continue

            cord_array = np.asarray(cord)
            # Check if the point exists allready
            if len(added_points) > 0 and np.min(np.linalg.norm(np.asarray(added_points) - cord_array, axis = 1)) < 0.01:
                counter_1 += 1
                continue

            # If its on the first line then insert it between the first and second
            if not isnt_on_first_line:
                contour_list.insert(p1_idx_1 + 1, cord_array)
            else:
                # Otherwise between the second two points
                contour_list.insert(p2_idx_1 + 1, cord_array)

            added_points.append(cord_array)

            print(p1_idx_1, cord, p2_idx_1)
            counter_2 += 2

        counter_1 += 1


# https://stackoverflow.com/questions/434287/what-is-the-most-pythonic-way-to-iterate-over-a-list-in-chunks
def chunker(seq, size):
    return (seq[pos:pos + size] if pos + size < len(seq) else [seq[-1], seq[0]] for pos in range(0, len(seq), 1))


# Intersecting lines https://stackoverflow.com/questions/20677795/how-do-i-compute-the-intersection-point-of-two-lines

def line(p1, p2):
    A = (p1[1] - p2[1])
    B = (p2[0] - p1[0])
    C = (p1[0] * p2[1] - p2[0] * p1[1])
    return A, B, -C


def intersection(L1, L2):
    D = L1[0] * L2[1] - L1[1] * L2[0]
    Dx = L1[2] * L2[1] - L1[1] * L2[2]
    Dy = L1[0] * L2[2] - L1[2] * L2[0]
    if D != 0:
        x = Dx / D
        y = Dy / D
        return x, y
    else:
        return False


def intersecting_line(p1, p2, p3, p4):
    l1 = line(p1, p2)
    l2 = line(p3, p4)

    return intersection(l1, l2)