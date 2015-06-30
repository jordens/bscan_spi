#!/usr/bin/python3
# Robert Jordens <jordens@gmail.com> 2015

from migen.fhdl.std import *
from mibuild.generic_platform import ConstraintError


bscan_layout = [
    ("tdi", 1),
    ("tdo", 1),
    ("tck", 1),
    ("sel", 1),
    ("shift", 1),
]


class Spartan6(Module):
    def __init__(self, platform):
        spi = platform.request("spiflash")
        shift = Signal()
        self.specials += Instance("BSCAN_SPARTAN6", p_JTAG_CHAIN=1,
                                  o_TCK=spi.clk, o_SHIFT=shift,
                                  o_TDI=spi.mosi, i_TDO=spi.miso)
        self.comb += spi.cs_n.eq(~shift)
        try:
            self.comb += platform.request("user_led", 0).eq(1)
            self.comb += platform.request("user_led", 1).eq(shift)
        except ConstraintError:
            pass


class Series7(Module):
    def __init__(self, platform):
        spi = platform.request("spiflash")
        shift = Signal()
        clk = Signal()
        self.comb += spi.cs_n.eq(~shift)
        self.specials += Instance("BSCANE2", p_JTAG_CHAIN=1,
                                  o_SHIFT=shift, o_TCK=clk,
                                  io_TDI=spi.dq[0], io_TDO=spi.dq[1])
        self.specials += Instance("STARTUPE2", i_CLK=0, i_GSR=0, i_GTS=0,
                                  i_KEYCLEARB=0, i_PACK=1, i_USRCCLKO=clk,
                                  i_USRCCLKTS=0, i_USRDONEO=1, i_USRDONETS=1)
        try:
            self.comb += platform.request("user_led", 0).eq(1)
            self.comb += platform.request("user_led", 1).eq(shift)
        except ConstraintError:
            pass


def build_bscan_spi(platform, Top):
    platform.toolchain.bitgen_opt += " -g compress"
    name = "bscan_spi_{}".format(platform.device)
    top = Top(platform)
    platform.build_cmdline(top, build_name=name)


if __name__ == "__main__":
    from mibuild.platforms import pipistrello, papilio_pro, kc705

    p = pipistrello.Platform()
    build_bscan_spi(p, Spartan6)

    p = papilio_pro.Platform()
    build_bscan_spi(p, Spartan6)

    p = kc705.Platform(toolchain="ise")
    build_bscan_spi(p, Series7)
