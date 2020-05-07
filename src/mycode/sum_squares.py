# This function just computes the sum of squares of an array
# test how to reuse artifacts from previous orquestra step

#import numpy as np

def main(array):
    out = 0.0
    for elem in array:
        out += elem**2

    return {'value': out}
