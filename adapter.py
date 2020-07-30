import sys
from PIL import Image, ImageDraw, ImageFont
import math
import cuflow as cu
import svgout
from dazzler import Dazzler
from collections import defaultdict

import xml.etree.ElementTree as ET
import shapely.geometry as sg
import shapely.affinity as sa
import shapely.ops as so

class LibraryPart(cu.Part):
    libraryfile = None
    partname = None
    use_silk = True
    use_pad_text = True
    def __init__(self, dc, val = None, source = {}):
        tree = ET.parse(self.libraryfile)
        root = tree.getroot()
        x_packages = root.find("drawing").find("library").find("packages")
        packages = {p.attrib["name"]:p for p in x_packages}
        self.pa = packages[self.partname]
        cu.Part.__init__(self, dc, val, source)

    def place(self, dc):
        ls = defaultdict(list)
        for c in self.pa:
            attr = c.attrib
            if c.tag == "wire" and attr["layer"] in ("20", "21"):
                (x1, y1, x2, y2) = [float(attr[t]) for t in "x1 y1 x2 y2".split()]
                p0 = dc.copy().goxy(x1, y1)
                p1 = dc.copy().goxy(x2, y2)
                ls[attr["layer"]].append(sg.LineString([p0.xy, p1.xy]))
            elif c.tag == "hole":
                (x, y, drill) = [float(attr[t]) for t in "x y drill".split()]
                p = dc.copy().goxy(x, y)
                dc.board.hole(p.xy, drill)
            elif c.tag == "circle" and attr["layer"] == "51":
                (x, y, radius) = [float(attr[t]) for t in "x y radius".split()]
                p = dc.copy().goxy(x, y)
                dc.board.hole(p.xy, 2 * radius)
            elif c.tag == "smd":
                (x, y, dx, dy) = [float(attr[t]) for t in "x y dx dy".split()]
                p = dc.copy().goxy(x, y)
                p.rect(dx, dy)
                p.setname(attr["name"])
                self.pad(p)
            elif c.tag == "pad":
                (x, y, diameter, drill) = [float(attr[t]) for t in "x y diameter drill".split()]
                nm = attr["name"]

                dc.push()
                dc.goxy(x, y)
                dc.board.hole(dc.xy, drill)
                n = {"circle" : 60, "octagon" : 8, "square" : 4}[attr.get("shape", "circle")]
                p = dc.copy()
                p.n_agon(diameter / 2, n)

                p.setname(nm)
                p.part = self.id
                self.pads.append(p)
                p.contact()

                if self.use_pad_text and nm not in ("RESERVED", ):
                    self.board.annotate(dc.xy[0], dc.xy[1], nm)
                dc.pop()
        if ls["20"]:
            g = so.linemerge(ls["20"])
            brd.layers['GML'].add(g)
        if self.use_silk and ls["21"]:
            g = so.linemerge(ls["21"]).buffer(brd.silk / 2)
            brd.layers['GTO'].add(g)

class ArduinoR3(LibraryPart):
    libraryfile = "adafruit.lbr"
    partname = "ARDUINOR3"
    use_pad_text = False
    family = "J"
    def escape(self):
        for nm in ("GND", "GND1", "GND2"):
            self.s(nm).setname("GL2").thermal(1.3).wire(layer = "GBL")

        spi = [self.s(n) for n in "D13 D11 D10 D9 D8 D7 D1".split()]
        for t in spi:
            t.w("r 180 f 2").wire(layer = "GBL")
        spi0 = self.board.enriver90(spi[:4], -90).right(90).wire()
        spi1 = self.board.enriver90(spi[4:], 90).left(90).wire()
        return spi0.join(spi1)
        # self.s("D1").w("r 180 f 2 r 90 f 15 l 90 f 1").wire("GBL")
        # spio1 = cu.River(self.board, [self.s("D0")])
        # return spio.join(spio1).wire()

class SD(LibraryPart):
    libraryfile = "x.lbrSD_TF_holder.lbr"
    partname = "MICROSD"
    family = "J"

__VERSION__ = "0.1.0"

def gentext(s):
    fn = "../../.fonts/Arista-Pro-Alternate-Light-trial.ttf"
    fn = "../../.fonts/IBMPlexSans-SemiBold.otf"
    font = ImageFont.truetype(fn, 120)
    im = Image.new("L", (2000, 1000))
    draw = ImageDraw.Draw(im)
    draw.text((200, 200), s, font=font, fill = 255)
    return im.crop(im.getbbox())

class DIP8(cu.Part):
    family = "J"
    inBOM = False
    def place(self, dc):
        for _ in range(2):
            dc.push()
            dc.goxy(cu.inches(-.15), cu.inches(.15)).left(180)
            def gh():
                dc.board.hole(dc.xy, .8)
                p = dc.copy()
                p.part = self.id
                p.n_agon(0.8, 60)
                p.contact()
                self.pads.append(dc.copy())
            self.train(dc, 4, gh, cu.inches(.1))
            dc.pop()
            dc.right(180)
    def escape(self):
        ii = cu.inches(.1) / 2
        q = math.sqrt((ii ** 2) + (ii ** 2))
        for p in self.pads[:4]:
            p.w("l 45").forward(q).left(45).forward(1)
        for p in self.pads[4:]:
            p.w("r 90 f 1")
        oo = list(sum(zip(self.pads[4:], self.pads[:4]), ()))
        cu.extend2(oo)
        [p.wire() for p in oo]
        return oo

class WSON8L(cu.Part):
    family = "U"
    def place(self, dc):
        self.chamfered(dc, 8, 6)
        self.chamfered(dc, 6, 5, False)
        e = 1.27
        for _ in range(2):
            dc.push()
            dc.goxy(-6.75 / 2, e * 1.5).left(180)
            self.train(dc, 4, lambda: self.rpad(dc, 0.5, 2.00), e)
            dc.pop()
            dc.right(180)
    def escape(self):
        ii = 1.27 / 2
        q = math.sqrt((ii ** 2) + (ii ** 2))
        for p in self.pads[4:]:
            p.w("i r 45").forward(q).left(45).forward(1)
        for p in self.pads[:4]:
            p.w("o f .2")
        oo = list(sum(zip(self.pads[4:], self.pads[:4]), ()))
        cu.extend2(oo)
        [p.wire() for p in oo]
        return oo

if __name__ == "__main__":
    brd = cu.Board(
        (24, 12),
        trace = cu.mil(6),
        space = cu.mil(5) * 2.0,
        via_hole = 0.3,
        via = 0.6,
        via_space = cu.mil(5),
        silk = cu.mil(6))

    dc = brd.DC((6, 6))
    u1 = DIP8(dc).escape()

    u2 = WSON8L(brd.DC((18, 6))).escape()

    for src,dst in zip(u1, u2):
        src.path.append(dst.xy)
        src.wire()

    p = brd.DC((6, 12))
    p.n_agon(1.5, 60)
    p.silko()

    brd.outline()

    brd.check()
    if 0:
        brd.fill_any("GTL", "VCC")
        brd.fill_any("GBL", "GL2")

    brd.save("adapter")
    svgout.write(brd, "adapter.svg")
