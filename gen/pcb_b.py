#!/usr/bin/env python3
"""Board B (Q20 keyboard) PCB, checkpoint 3: BBQ20KBD outline, 2-layer 2.0 mm, footprints with nets, placement.

    python3 gen/pcb_b.py            -> hw/board_b/q20_keyboard.kicad_pcb (+ placement report on stdout)

Geometry source: Solder Party BBQ20KBD bbq20_keyboard.kicad_pcb (CERN-OHL v1.2), research/dl/kbd/bbq20kbd_hw.
Coordinates are relative to the top-left corner of its Edge.Cuts (110.8, 69.9 in that file; its footprint positions
are rounded to 110.75 / 69.85, i.e. 0.05 mm less). The keyboard connector is the only front-side part (the Q20
keyboard sits on the front); everything else is on the back, at the BBQ20KBD positions where the part exists there.
The 12-pin FFC to the carrier replaces BBQ20KBD's USB-C at the top edge.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
from pcbgen import Gen, rounded_rect  # noqa: E402

BOARD = os.path.join(ROOT, 'hw', 'board_b')
W, H = 74.0, 53.1
SLOTS = [(5.8, 7.5, 17.0, 11.5), (5.5, 14.7, 9.2, 29.4)]     # BBQ20KBD board slots, r = 0.4
HOLE2 = ((20.2, 48.1), 1.0)                                  # BBQ20KBD 2 mm hole

# Back-side angles: BBQ20KBD's file stores KiCad's own angle of a flipped footprint (KiCad flips top/bottom), while
# Gen.place_fixed takes the angle of the top-side footprint before a left/right mirror. The two differ by 180 degrees,
# so every back-side part copied from BBQ20KBD has its angle + 180 here; this puts each pin where BBQ20KBD has it
# (checked pad by pad against bbq20_keyboard.kicad_pcb: pin 1 / pin 2 offsets of U1, U2, U3, U5, U6, Q1-Q6, Y1, JP1).
FIXED = {
    'J201': (12.0, 22.2, 90, 'F'),          # Hirose BM20B keyboard connector (BBQ20KBD U4), front side
    'H101': (70.9, 3.1, 0, 'F'), 'H102': (11.4, 49.3, 0, 'F'),       # BBQ20KBD H1 / H2 (M2.5)
    'J101': (37.0, 6.4, 0, 'B'),            # carrier FFC (replaces BBQ20KBD USB-C J3), cable leaves the top edge
    'U102': (37.4, 26.7, 0, 'B'),           # RP2040 (BBQ20KBD U1, 180)
    'U103': (46.1, 19.6, 0, 'B'),           # QSPI flash (U3, 180)
    'Y101': (40.2, 34.0, 180, 'B'),         # 12 MHz crystal (Y1, 0)
    'U101': (29.0, 15.8, 0, 'B'),           # AP2112K-3.3 (U2, 180)
    'U201': (21.75, 20.9, 0, 'B'),          # ME6212C18 1.8 V (U5, 180)
    'U202': (21.75, 17.45, 0, 'B'),         # ME6212C28 2.8 V (U6, 180)
    # trackpad level shifters + backlight FET: BBQ20KBD column Q4, Q1, Q2, Q3, Q5, Q6 (x = 21.64; all at 0 there)
    'Q201': (21.64, 24.35, 180, 'B'), 'Q202': (21.64, 27.75, 180, 'B'), 'Q203': (21.64, 31.15, 180, 'B'),
    'Q204': (21.64, 34.55, 180, 'B'), 'Q205': (21.64, 37.95, 180, 'B'), 'Q206': (21.64, 41.35, 180, 'B'),
    # SWD / BOOT / UART test pads: BBQ20KBD row at y = 40.33 (pitch 2.8 instead of 2.54 so the courtyards clear)
    'TP105': (29.0, 40.33, 0, 'B'), 'TP103': (31.8, 40.33, 0, 'B'), 'TP104': (34.6, 40.33, 0, 'B'),
    'TP102': (37.4, 40.33, 0, 'B'), 'TP106': (40.2, 40.33, 0, 'B'), 'TP101': (43.0, 40.33, 0, 'B'),
    'TP107': (45.8, 40.33, 0, 'B'),
    'JP201': (19.65, 13.0, 0, 'B'),         # MIC_VDD solder jumper (JP1, 180)
}

# 2 layers, 2.0 mm FR-4 (as BBQ20KBD), 1 oz copper
STACKUP = [
    ('F.SilkS', 'Top Silk Screen', None, None, None), ('F.Paste', 'Top Solder Paste', None, None, None),
    ('F.Mask', 'Top Solder Mask', 0.01, None, None), ('F.Cu', 'copper', 0.035, None, None),
    ('dielectric 1', 'core', 1.91, 'FR4', 4.5), ('B.Cu', 'copper', 0.035, None, None),
    ('B.Mask', 'Bottom Solder Mask', 0.01, None, None), ('B.Paste', 'Bottom Solder Paste', None, None, None),
    ('B.SilkS', 'Bottom Silk Screen', None, None, None)]


def outline():
    def quarter(c, r, a0, a1):
        """arc from angle a0 to a1 (degrees, y down) around centre c"""
        pa = lambda a: (c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a)))
        return ('A', pa(a0), pa((a0 + a1) / 2), pa(a1))

    s = [('L', (3.1, 0), (70.9, 0)), quarter((70.9, 3.1), 3.1, -90, 0),
         ('L', (74.0, 3.1), (74.0, 39.1)), quarter((60.0, 39.1), 14.0, 0, 90),
         ('L', (60.0, 53.1), (14.0, 53.1)), quarter((14.0, 39.1), 14.0, 90, 180),
         ('L', (0, 39.1), (0, 3.1)), quarter((3.1, 3.1), 3.1, 180, 270)]
    for x0, y0, x1, y1 in SLOTS:
        s += rounded_rect(x0, y0, x1, y1, 0.4)
    s.append(('C', HOLE2[0], HOLE2[1]))
    return s


CORNERS = [((3.1, 3.1), 3.1, lambda x, y: x < 3.1 and y < 3.1), ((70.9, 3.1), 3.1, lambda x, y: x > 70.9 and y < 3.1),
           ((14.0, 39.1), 14.0, lambda x, y: x < 14.0 and y > 39.1), ((60.0, 39.1), 14.0, lambda x, y: x > 60.0 and y > 39.1)]


def inside_outline(r, margin=0.5):
    """all four corners of a courtyard box inside the rounded corners of the outline"""
    for (x, y) in ((r[0], r[1]), (r[2], r[1]), (r[0], r[3]), (r[2], r[3])):
        for (c, rad, zone) in CORNERS:
            if zone(x, y) and math.hypot(x - c[0], y - c[1]) > rad - margin:
                return False
    return True


def main():
    g = Gen(BOARD, os.path.join(BOARD, 'q20_keyboard.net'), os.path.join(BOARD, 'q20_keyboard.kicad_pcb'), W, H,
            copper_layers=2, thickness=2.0)
    g.edge(outline())
    for x0, y0, x1, y1 in SLOTS:
        g.block('both', (x0, y0, x1, y1))
    (cx, cy), r = HOLE2
    g.block('both', (cx - r, cy - r, cx + r, cy + r))
    g.region_ok = inside_outline
    g.place_fixed(FIXED)
    pending = g.autoplace(tp_side='B', only_side='B')
    g.save(STACKUP, 2.0)
    g.report(pending)
    return 1 if pending else 0


if __name__ == '__main__':
    sys.exit(main())
