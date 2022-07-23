import time

from level.Constants import coordinate_round


def round_cord(*args):
    if len(args) == 1:
        p = args[0]
        return round(p[0] * coordinate_round) / coordinate_round, round(p[1] * coordinate_round) / coordinate_round
    else:
        x = args[0]
        y = args[1]
        return round(x * coordinate_round) / coordinate_round, round(y * coordinate_round) / coordinate_round


def round_to_cord(value):
    return round(value * coordinate_round) / coordinate_round


def timeit(function, args):
    start_time = time.time()
    ret_data = function(**args)
    end_time = time.time()

    return ret_data, round((end_time - start_time) * 1000) / 1000
