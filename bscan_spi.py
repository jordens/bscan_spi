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
    def __init__(self, bscan, spi, magic=0x59a659a6, tdi_len=48,
                 tdo_len=1 << 14, tdo_sr=False):
        """
        fpgaprog and papilio-loader need::
            magic=0x59a6, tdi_len=32, tdo_len=8, tdo_sr=True
        xc3sprog needs::
            magic=0x59a659a6, tdi_len=48, tdo_len=1 << 14, tdo_sr=False
            # IMHO xc3sprog requiring this is a design error and bug

        Basically none of this is needed. SPI could be hooked up to JTAG
        drectly. cs would be logic, at most one short shift register is needed
        to restore convenient 8-bit alignment.

        Some SPI/JTAG ground rules:
            * sampling is to be done on rising edges
            * shifting/setting/latching is to be done on falling edges
            * this is true for spi in cpha,cpol=0,0 or 1,1 and jtag
              and both master and slave
            * combinatorials can be forwarded between interfaces
        """
        self.active = active = Signal()

        ##

        self.clock_domains.cd_rise = ClockDomain()
        self.clock_domains.cd_fall = ClockDomain()

        rst = Signal()
        start = Signal()
        stop = Signal()
        tdi = Signal(tdi_len)
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
        ]
        self.sync.rise += tdi.eq(Cat(bscan.tdi, tdi))
        self.sync.fall += [
            If(~active,
                If(tdi[16:] == magic,
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
            If(start,
                stop.eq(len == 0),
            ),
        ]
        if tdo_sr:
            if tdo_len == 0:
                self.comb += bscan.tdo.eq(spi.miso)
            else:
                tdo = Signal(tdo_len)
                self.sync.rise += tdo.eq(Cat(spi.miso, tdo))
                self.sync.fall += bscan.tdo.eq(tdo[-1])
        else:
            tdo = Memory(1, tdo_len)
            tdo_w = tdo.get_port(write_capable=True, clock_domain="rise")
            tdo_r = tdo.get_port(write_capable=False, clock_domain="fall")
            self.specials += tdo, tdo_w, tdo_r
            self.comb += [
                tdo_w.dat_w.eq(spi.miso),
                bscan.tdo.eq(tdo_r.dat_r),
            ]
            self.sync.rise += [
                tdo_w.we.eq(~spi.cs_n),
                If(tdo_w.we,
                    tdo_w.adr.eq(tdo_w.adr + 1),
                ),
            ]
            tdo_r.adr.reset = 1
            self.sync.fall += tdo_r.adr.eq(tdo_r.adr + 1)
