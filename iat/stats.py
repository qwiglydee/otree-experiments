import math


def stats(data):
    """Calculating sample mean and std in pure python"""
    cnt = len(data)
    s = sum(data)
    mean = s / cnt
    sqs = sum((v - mean) ** 2 for v in data)
    ssq = sqs / (cnt - 1)
    std = math.sqrt(ssq)
    return mean, std
