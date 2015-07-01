#!/usr/bin/python3
# Robert Jordens <jordens@gmail.com> 2015

from migen.fhdl.std import *
from mibuild.generic_platform import *
from mibuild.xilinx import XilinxPlatform


bscan_layout = [
    ("tdi", 1),
    ("tdo", 1),
    ("tck", 1),
    ("sel", 1),
    ("shift", 1),
]


class Series6(Module):
    def __init__(self, platform):
        self.clock_domains.dummy = ClockDomain()
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
        self.clock_domains.dummy = ClockDomain()
        spi = platform.request("spiflash")
        shift = Signal()
        clk = Signal()
        self.comb += spi.cs_n.eq(~shift)
        self.specials += Instance("BSCANE2", p_JTAG_CHAIN=1,
                                  o_SHIFT=shift, o_TCK=clk,
                                  io_TDI=spi.mosi, io_TDO=spi.miso)
        self.specials += Instance("STARTUPE2", i_CLK=0, i_GSR=0, i_GTS=0,
                                  i_KEYCLEARB=0, i_PACK=1, i_USRCCLKO=clk,
                                  i_USRCCLKTS=0, i_USRDONEO=1, i_USRDONETS=1)
        try:
            self.comb += platform.request("user_led", 0).eq(1)
            self.comb += platform.request("user_led", 1).eq(shift)
        except ConstraintError:
            pass


pinouts = {
    #                    cs_n, clk, mosi, miso
    "xc6slx45-csg324-2": (["V3", "R15", "T13", "R13"], "LVTTL", Series6),
    "xc6slx9-tqg144-2": (["P38", "P70", "P64", "P65"], "LVCMOS33", Series6),
    "xc7k325t-ffg900-2": (["U19", None, "R25", "R20"], "LVCMOS25", Series7),
}


def make_platform(name):
    (cs_n, clk, mosi, miso), std, cls = pinouts[name]
    io = ["spiflash", 0,
          Subsignal("cs_n", Pins(cs_n), Misc("PULLUP")),
          Subsignal("mosi", Pins(mosi)),
          Subsignal("miso", Pins(miso), Misc("PULLDOWN")),
          IOStandard(std)]
    if clk:
        io.append(Subsignal("clk", Pins(clk)))

    class Platform(XilinxPlatform):
        def __init__(self):
            XilinxPlatform.__init__(self, name, [io])
            self.name = "bscan_spi_{}".format(name)
            self.toolchain.bitgen_opt += " -g compress"
    return Platform, cls


if __name__ == "__main__":
    #from mibuild.platforms import pipistrello, papilio_pro, kc705
    #build_bscan_spi(pipistrello.Platform(), Spartan6)

    for name in sorted(pinouts):
        P, C = make_platform(name)
        p = P()
        p.build_cmdline(C(p), build_name=p.name)
