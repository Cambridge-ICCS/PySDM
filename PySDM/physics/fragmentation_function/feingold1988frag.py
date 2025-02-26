"""
Scaled exponential PDF
"""
import numpy as np


class Feingold1988Frag:  # pylint: disable=too-few-public-methods
    def __init__(self, _):
        pass

    @staticmethod
    def frag_size(_, scale, rand, x_plus_y, fragtol):
        return -scale * np.log(max(1 - rand * scale / x_plus_y, fragtol))
