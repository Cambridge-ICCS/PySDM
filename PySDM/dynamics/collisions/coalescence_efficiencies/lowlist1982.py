"""
See Low & List 1982
"""
import numpy as np

from PySDM.physics.constants import si


class LowList1982Ec:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, vmin=0.0, nfmax=None):
        self.particulator = None
        self.vmin = vmin
        self.nfmax = nfmax
        self.arrays = {}
        self.ll82_tmp = {}
        self.max_size = None
        self.sum_of_volumes = None
        self.const = None

    def register(self, builder):
        self.particulator = builder.particulator
        self.max_size = self.particulator.PairwiseStorage.empty(
            self.particulator.n_sd // 2, dtype=float
        )
        self.sum_of_volumes = self.particulator.PairwiseStorage.empty(
            self.particulator.n_sd // 2, dtype=float
        )
        self.const = self.particulator.formulae.constants
        builder.request_attribute("radius")
        builder.request_attribute("volume")
        builder.request_attribute("terminal velocity")
        for key in ("Sc", "St", "dS", "tmp", "tmp2", "CKE", "Et", "ds", "dl"):
            self.arrays[key] = self.particulator.PairwiseStorage.empty(
                self.particulator.n_sd // 2, dtype=float
            )

    def __call__(self, output, is_first_in_pair):
        self.max_size.max(self.particulator.attributes["volume"], is_first_in_pair)
        self.sum_of_volumes.sum(
            self.particulator.attributes["volume"], is_first_in_pair
        )
        self.arrays["ds"].min(self.particulator.attributes["radius"], is_first_in_pair)
        self.arrays["ds"] *= 2
        self.arrays["dl"].max(self.particulator.attributes["radius"], is_first_in_pair)
        self.arrays["dl"] *= 2

        # compute the surface energy, CKE
        self.arrays["Sc"].sum(self.particulator.attributes["volume"], is_first_in_pair)
        self.arrays["Sc"] **= 2 / 3
        self.arrays["Sc"] *= (
            self.const.PI * self.const.sgm_w * (6 / self.const.PI) ** (2 / 3)
        )
        self.arrays["St"].min(self.particulator.attributes["radius"], is_first_in_pair)
        self.arrays["St"] *= 2
        self.arrays["St"] **= 2
        self.arrays["tmp"].max(self.particulator.attributes["radius"], is_first_in_pair)
        self.arrays["tmp"] *= 2
        self.arrays["tmp"] **= 2
        self.arrays["St"] += self.arrays["tmp"]
        self.arrays["St"] *= self.const.PI * self.const.sgm_w
        self.arrays["dS"].fill(self.arrays["St"])
        self.arrays["dS"] -= self.arrays["Sc"]

        self.arrays["tmp"].sum(self.particulator.attributes["volume"], is_first_in_pair)
        self.arrays["tmp2"].distance(
            self.particulator.attributes["terminal velocity"], is_first_in_pair
        )
        self.arrays["tmp2"] **= 2
        self.arrays["CKE"].multiply(
            self.particulator.attributes["volume"], is_first_in_pair
        )
        self.arrays["CKE"].divide_if_not_zero(self.arrays["tmp"])
        self.arrays["CKE"] *= self.arrays["tmp2"]
        self.arrays["CKE"] *= self.const.rho_w / 2

        self.arrays["Et"].fill(self.arrays["CKE"])
        self.arrays["Et"] += self.arrays["dS"]

        a = 0.778
        b = 2.61e6 / si.J**2 * si.m**2

        self.arrays["tmp2"].fill(self.arrays["Et"])
        self.arrays["tmp2"] **= 2
        self.arrays["tmp2"] *= -1.0 * b * self.const.sgm_w
        self.arrays["tmp2"] /= self.arrays["Sc"]

        output.fill(self.arrays["ds"])
        output /= self.arrays["dl"]
        output += 1.0
        output **= -2.0
        output *= a
        output *= np.exp(self.arrays["tmp2"])

        self.particulator.backend.ll82_coalescence_check(
            Ec=output, dl=self.arrays["dl"]
        )
