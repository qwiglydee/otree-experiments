"""Calculating d-score in pure python

All data are list of float values

Implementation of d-score according to this snapshot:
http://faculty.washington.edu/agg/IATmaterials/Summary%20of%20Improved%20Scoring%20Algorithm.pdf
"""

import math


def mean(data: list):
    m = sum(data) / len(data)
    return m


def std(data: list):
    cnt = len(data)
    m = sum(data) / cnt
    sqs = sum((v - m) ** 2 for v in data)
    ssq = sqs / (cnt - 1)
    sstd = math.sqrt(ssq)
    return sstd


def dscore(data3: list, data4: list, data6: list, data7: list):
    # filter out too long

    def not_long(value):
        return value < 10.0

    data3 = list(filter(not_long, data3))
    data4 = list(filter(not_long, data4))
    data6 = list(filter(not_long, data6))
    data7 = list(filter(not_long, data7))

    # check for too short
    def too_short(value):
        return value < 0.300

    total_data = data3 + data4 + data6 + data7
    short_data = list(filter(too_short, total_data))
    if len(short_data) / len(total_data) > 0.1:
        return None

    # calculations

    std_3_6 = std(data3 + data6)
    std_4_7 = std(data4 + data7)

    mean_3_6 = mean(data6) - mean(data3)
    mean_4_7 = mean(data7) - mean(data4)

    dscore_3_6 = mean_3_6 / std_3_6
    dscore_4_7 = mean_4_7 / std_4_7

    dscore_mean = (dscore_3_6 + dscore_4_7) * 0.5

    return dscore_mean
