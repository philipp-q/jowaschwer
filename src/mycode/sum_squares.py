# This function just computes the sum of squares of an array
# test how to reuse artifacts from previous orquestra step

#import numpy as np

def main(dictio):
    out = 0.0
    for key in dictio.keys():
        for kkeyy in dictio[key].keys():
            out += dictio[key][kkeyy]**2

    return {'value': out}
