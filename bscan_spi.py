# Robert Jordens <jordens@gmail.com> 2015

from migen.fhdl.std import *
from migen.genlib.record import *


bscan_layout = [
    ("tdi", 1),
    ("tdo", 1),
    ("capture", 1),
    ("drck", 1),
    ("rst", 1),
    ("sel", 1),
    ("update", 1),
]


class BscanSpi(Module):
    magic = 0x59a6

    def __init__(self, bscan, spi):
        self.clock_domains.cd_rise = ClockDomain()
        self.clock_domains.cd_fall = ClockDomain()

        rst = Signal()
        active = Signal()
        start = Signal()
        stop = Signal()
        tdi = Signal(32)
        tdo = Signal(8)
        len = Signal(16)

        self.comb += [
            rst.eq(bscan.capture | bscan.rst | bscan.update | ~bscan.sel),
            self.cd_rise.clk.eq(bscan.drck),
            self.cd_rise.rst.eq(rst),
            self.cd_fall.clk.eq(~bscan.drck),
            self.cd_fall.rst.eq(rst),

            spi.cs_n.eq(~(bscan.sel & start & ~stop)),
            spi.clk.eq(bscan.drck),
            spi.mosi.eq(bscan.tdi),
            bscan.tdo.eq(tdo[-1]),
        ]
        self.sync.fall += [
            If(~active,
                If(tdi[-16:] == self.magic,
                    active.eq(1),
                    len.eq(tdi[:16]),
                    start.eq(tdi[:16] > 0),
                ),
            ),
            If(len > 0,
                len.eq(len - 1),
            ),
        ]
        self.sync.rise += [
            tdi.eq(Cat(bscan.tdi, tdi)),
            tdo.eq(Cat(spi.miso, tdo)),
            If(start,
                stop.eq(len == 0),
            ),
        ]
