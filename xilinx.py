#!/usr/bin/python3
# Robert Jordens <jordens@gmail.com> 2015

from migen import *
from migen.build.generic_platform import ConstraintError

from bscan_spi import bscan_layout, BscanSpi

class Spartan3A(Module):
    def __init__(self, platform):
        bscan = Record(bscan_layout)
        spi = platform.request("spiflash")
        dummy = Constant(0) # Both inputs must be used, or bitgen will complain.
        self.submodules.bscan2spi = BscanSpi(bscan, spi)
        self.specials += Instance(
            "BSCAN_SPARTAN3A",
            o_CAPTURE=bscan.capture, o_DRCK1=bscan.drck,
            o_RESET=bscan.rst, o_SEL1=bscan.sel, o_UPDATE=bscan.update,
            o_TDI=bscan.tdi, i_TDO1=bscan.tdo, i_TDO2=dummy)
        try:
            self.comb += platform.request("user_led").eq(~spi.cs_n)
            self.comb += platform.request("user_led").eq(1)
        except ConstraintError:
            pass


class Spartan6(Module):
    def __init__(self, platform):
        bscan = Record(bscan_layout)
        spi = platform.request("spiflash")
        self.submodules.bscan2spi = BscanSpi(bscan, spi)
        self.specials += Instance(
            "BSCAN_SPARTAN6", p_JTAG_CHAIN=1,
            o_CAPTURE=bscan.capture, o_DRCK=bscan.drck,
            o_RESET=bscan.rst, o_SEL=bscan.sel, o_UPDATE=bscan.update,
            o_TDI=bscan.tdi, i_TDO=bscan.tdo)
        try:
            self.comb += platform.request("user_led").eq(~spi.cs_n)
            self.comb += platform.request("user_led").eq(1)
        except ConstraintError:
            pass


class Series7(Module):
    def __init__(self, platform):
        bscan = Record(bscan_layout)
        spi4 = platform.request("spiflash")
        spi = Record([("clk", 1), ("miso", 1), ("mosi", 1), ("cs_n", 1)])
        self.comb += [
            spi4.dq[0].eq(spi.mosi),
            spi.miso.eq(spi4.dq[1]),
            spi4.cs_n.eq(spi.cs_n),
            # spi.clk == usrcclko == bscan.drck
        ]
        self.submodules.bscan2spi = BscanSpi(bscan, spi)
        self.specials += Instance(
            "BSCANE2", p_JTAG_CHAIN=1,
            o_CAPTURE=bscan.capture, o_DRCK=bscan.drck,
            o_RESET=bscan.rst, o_SEL=bscan.sel, o_UPDATE=bscan.update,
            o_TDI=bscan.tdi, i_TDO=bscan.tdo)
        self.specials += Instance(
            "STARTUPE2", i_CLK=0, i_GSR=0, i_GTS=0, i_KEYCLEARB=0,
            i_PACK=1, i_USRCCLKO=bscan.drck, i_USRCCLKTS=0, i_USRDONEO=1,
            i_USRDONETS=1)
        try:
            self.comb += platform.request("user_led").eq(~spi.cs_n)
            self.comb += platform.request("user_led").eq(1)
        except ConstraintError:
            pass


def build_bscan_spi(platform, Top):
    name = "bscan_spi_{}".format(platform.device)
    top = Top(platform)
    platform.build(top, build_name=name)


if __name__ == "__main__":
    from migen.build.platforms import pipistrello, papilio_pro, kc705, mercury

    p = pipistrello.Platform()
    p.toolchain.bitgen_opt += " -g compress"
    build_bscan_spi(p, Spartan6)

    p = papilio_pro.Platform()
    p.toolchain.bitgen_opt += " -g compress"
    build_bscan_spi(p, Spartan6)

    p = kc705.Platform(toolchain="ise")
    p.toolchain.bitgen_opt += " -g compress"
    build_bscan_spi(p, Series7)

    p = mercury.Platform()
    p.toolchain.bitgen_opt += " -g compress"
    build_bscan_spi(p, Spartan3A)
