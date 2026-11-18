#!/usr/bin/env python3
"""Board A (CM5 carrier) PCB, checkpoint 3: outline, 6-layer stack-up, all footprints with their nets, placement.

    python3 gen/pcb_a.py            -> hw/board_a/cm5_carrier.kicad_pcb (+ placement report on stdout)

Board coordinates in this file: origin at the top-left board corner, x right, y down, mm; the KiCad file has the
board at (+100, +100). Major parts are placed by the FIXED table below (positions derived from the datasheet
drawings, see docs/checkpoint3/CHECKPOINT3.md); every other part is placed next to the part it connects to
(gen/pcbgen.py).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
import pcbnew  # noqa: E402
from pcbgen import Gen  # noqa: E402
from stages import BACKLIGHT, BB_AUX, BB_LTE, BOOST_5V, BOOST_CM5, CHARGER, stage  # noqa: E402

BOARD = os.path.join(ROOT, 'hw', 'board_a')
W, H = 95.0, 65.0

CM5 = (32.5155, 36.7865)   # CM5 module centre (Orange Pi CM5: JP1 right, JP2 left, JP3 at the bottom); placed so
                            # that JP2's pads are exactly where the Radxa CM5's connector B pads were (13.96 / 17.04,
                            # y 44.07 - 0.4 n): its 26 CSI / DSI / OTG pairs keep the same breakouts (D95)
M2 = (34.5, 12.7)     # M.2 socket origin (odd pad row), bottom side; module extends toward +y
USBA_X = (62.3, 80.5)
USBA_Y = H - 8.28     # footprint origin = top of the board cutout

# Orange Pi CM5 base board V1.2 DXF: M2.5 holes 48.001 x 32.999 apart, relative to their centre (gen/footprints.py
# OPI_CM5 for the rotation)
CM5_HOLES = {'H301': (16.4995, 24.0005), 'H302': (-16.4995, 24.0005), 'H303': (-16.4995, -24.0005),
             'H304': (16.4995, -24.0005)}

# ref: (x, y, rotation, side)
FIXED = {
    # ---- top: CM5 and its standoffs
    'J301': (*CM5, 0, 'F'), 'J302': (*CM5, 0, 'F'), 'J303': (*CM5, 0, 'F'),
    **{h: (CM5[0] + dx, CM5[1] + dy, 0, 'F') for h, (dx, dy) in CM5_HOLES.items()},
    # ---- top: edges
    'J101': (3.19, 12.5, 270, 'F'),                 # USB-C, left edge (HRO "PCB edge" at local y = +3.19)
    'J102': (65.0, 9.0, 180, 'F'),                  # battery, top edge, mating face toward -y (battery bay)
    'J502': (95.0 - 0.3 - 14.57, 14.75, 90, 'F'),   # nano-SIM, right edge; GND tabs 0.3 from the edge
    'J901': (95.0 - 0.4 - 8.325, 30.0, 90, 'F'),    # microSD, right edge, body front 0.4 inside
    'SW301': (93.0, 41.5, 90, 'F'), 'SW302': (93.0, 48.0, 90, 'F'), 'SW303': (93.0, 54.5, 90, 'F'),
    'J401': (USBA_X[0], USBA_Y, 0, 'F'), 'J402': (USBA_X[1], USBA_Y, 0, 'F'),
    'H305': (3.5, 3.5, 0, 'F'), 'H306': (3.5, 61.5, 0, 'F'), 'H307': (91.5, 3.5, 0, 'F'), 'H308': (92.0, 61.5, 0, 'F'),
    # ---- top: FPC / FFC (inboard)
    'J705': (3.0, 30.0, 270, 'F'),                  # CAM-B (front) FH35C 31P, ribbon enters from -x
    'J704': (3.0, 46.5, 270, 'F'),                  # CAM-A FH35C 31P, ribbon enters from -x
    'J1001': (47.0, 7.0, 0, 'F'),                   # keyboard FFC, ribbon enters from -y; on the device centreline
    'J703': (33.0, 7.0, 0, 'F'),                    # digitizer FFC, ribbon enters from -y
    'J701': (55.0, 23.0, 90, 'F'),                  # display 30P, ribbon enters from +x
    'J702': (55.0, 43.85, 90, 'F'),                 # touch 8P, ribbon enters from +x; 20.85 mm from J701 as the
                                                    # panel's tails (DisplayModule CAD drawing, D118)
    'SW304': (57.2, 36.25, 0, 'F'), 'SW305': (68.0, 47.0, 0, 'F'), 'SW306': (75.0, 47.0, 0, 'F'),
    # RTC with its crystal, decoupling and pull-ups where checkpoint 3 had them (the autoplacer anchors it elsewhere
    # since its interrupt and clock went to JP3)
    'U301': (63.1, 20.47, 90, 'F'), 'Y301': (67.195, 19.695, 90, 'F'), 'C308': (61.195, 15.995, 0, 'F'),
    'R303': (66.735, 22.945, 90, 'F'), 'R304': (63.465, 15.995, 0, 'F'),
    'D302': (89.0, 40.0, 90, 'F'),                  # status LED (light pipe), next to the power button
    'D501': (87.0, 40.0, 90, 'F'),                  # LTE LED
    'U803': (82.5, 47.0, 0, 'F'),                   # PDM mic, port hole through the board to the back
    # ---- bottom: M.2 + standoff, Wi-Fi
    'J501': (*M2, 0, 'B'),
    'H501': (M2[0], M2[1] + 44.525, 0, 'B'),
    # Wi-Fi: VLX / BUCK pins (25-29) up toward the free strip above the module (the M.2 module leaves 1 mm on its
    # right), antenna pins down to the u.FL pair, PCIe / UART toward the CM5 connector B
    # y 29.4375: the south pad row stays where it was before the pads were corrected (D114); the CSI-B lanes leave JP2
    # right beside it and have no other way out
    'U601': (11.5, 29.4375, 270, 'B'),
    # u.FL straight under WL_ANT0 (pin 2, x 15.1) / WL_ANT1 (pin 9, x 8.8): module pin -> 0 Ohm -> u.FL in one line
    'J601': (13.57, 42.3, 0, 'B'), 'J602': (7.27, 42.3, 0, 'B'),
    'R603': (15.1, 38.75, 90, 'B'), 'C615': (14.0, 38.75, 90, 'B'),    # shunt placeholders west of the RF line
    'R604': (8.8, 38.75, 90, 'B'), 'C616': (7.7, 38.75, 90, 'B'),
    # PCIe AC capacitors in a column right beside the module's PCIe pins (x 17.69, y 29.89-32.59), each level with its
    # pin, CM5 side (east) toward the strip under JP2's unused HDMI / DSI0 pins where the pairs from JP3 come up (D96).
    # x 19.0: 0.2 mm from the module's pads (they end at x 18.25, D114), bodies clear of the M.2 card (x 19.5)
    'C610': (19.0, 29.8875, 0, 'B'), 'C609': (19.0, 30.7875, 0, 'B'),      # CM5 TX -> module RX (pin 1 = CM5 side)
    'C612': (19.0, 31.6875, 180, 'B'), 'C611': (19.0, 32.5875, 180, 'B'),  # module TX -> CM5 RX (pin 2 = CM5 side)
    # REFCLK AC capacitors on the top north-west of the Wi-Fi module's REFCLK pins (U601.35 / 33 at x 15.1 / 13.3,
    # y 22.25), where the Radxa design's PCIe sideband translator was: pin 1 (CM5 side) north, P east (D98)
    'C613': (11.6, 20.9, 270, 'F'), 'C614': (10.9, 20.9, 270, 'F'),
    # USB3 TX AC capacitors just above the M.2 TX pins (x 34.8-35.3), the TX pair coming from JP2 (combo PHY2, west):
    # P over N, CM5 side (pin 1) west
    # USB3 TX AC caps: N above P, so neither TX segment has to cross its pair over (checked with the pair router)
    'C501': (33.6, 11.15, 180, 'B'), 'C502': (33.6, 10.45, 180, 'B'),
    'L601': (6.2, 19.85, 90, 'B'), 'L602': (9.3, 19.85, 90, 'B'),  # CSR / ASR buck inductors over pins 25-29
    # CM5_VIN test pad on its own pour (D114): where the autoplacer had it, SD_CMD and VCC3V3_AUX box it in on the bottom
    # and every run left it, or the 32 kHz clock it competes with, open
    'TP204': (55.75, 30.1, 0, 'B'),
    # ---- bottom: USB-C / PD (EEPROM + programming pads under the SIM, on the PD controller's I2C bus to the charger)
    'U101': (14.5, 5.5, 0, 'B'), 'U102': (82.0, 4.0, 0, 'B'),
    # ---- bottom: battery path and gauge at the battery connector (TI rule 5: QBAT and RSR near the battery terminal)
    'Q105': (70.0, 14.5, 180, 'B'),                 # BATFET: source pins (BAT_SRP) up toward the RSR, drain (VSYS) down
    'R109': (70.5, 10.0, 0, 'B'),                   # RSR 10 mOhm, battery sense (BAT+ -> BATFET)
    'R126': (61.0, 9.5, 0, 'B'),                    # 4 mOhm fuel-gauge shunt at the BAT- pins
    'U104': (57.5, 15.0, 0, 'B'),
    # LTE VCC per Quectel EM060K HD 3.5.2: one 220 uF + 1 uF / 100 nF / 33 pF / 10 pF array per VCC pin group.
    # The MLCCs sit in the J501 courtyard openings right behind the pins (under the module edge: 0402 = 0.55 mm
    # under a 1.25 mm gap), 10 / 33 pF nearest the pins. The socket ends are taken by the CM5 standoffs H303 / H304,
    # so the 220 uF bulk caps sit on the open side of the socket (about 11 mm of VCC_LTE pour to the pins, a few nH
    # and mOhm, small next to the POSCAP's own ESR / ESL). TVS between H303 and the socket, at pins 70-74.
    'D502': (21.2, 13.4, 270, 'B'),                                      # pins 70 / 72 / 74 (PMU)
    'C508': (24.55, 21.85, 0, 'B'), 'C507': (26.45, 21.85, 180, 'B'),
    'C506': (24.55, 22.95, 0, 'B'), 'C505': (26.45, 22.95, 180, 'B'),
    'C512': (42.35, 21.85, 0, 'B'), 'C511': (44.25, 21.85, 180, 'B'),   # pins 2 / 4 (APT)
    'C510': (42.35, 22.95, 0, 'B'), 'C509': (44.25, 22.95, 180, 'B'),
    'C504': (41.0, 3.3, 0, 'B'), 'C503': (41.0, 8.75, 0, 'B'),           # 2 x 220 uF, stacked beside the LTE stage
    # ---- bottom: hub, audio
    'U401': (71.0, 51.5, 0, 'B'),
    'J801': (3.05, 48.0, 270, 'B'), 'J802': (3.05, 55.0, 270, 'B'),   # openings to the left edge (D108)
    'U801': (11.0, 48.0, 0, 'B'), 'U802': (11.0, 55.0, 0, 'B'),
    # USB-A ESD arrays at their connectors, pins 1 / 2 (DP / DN) toward the hub
    'D402': (62.6, 54.0, 90, 'B'), 'D403': (80.0, 54.0, 90, 'B'),
    'R901': (52.3, 33.4, 0, 'B'),                    # SD_CLK series resistor at the CM5 pin (source termination)
    'TP501': (40.0, 3.0, 0, 'F'), 'TP502': (40.0, 5.6, 0, 'F'),      # LTE USB test pads, between the two FFCs
    # ---- switching power stages (gen/stages.py), each as one group
    **stage((69.5, 45.5), 180, 'B', CHARGER),        # bottom, under the SD / touch area; RAC end toward CHG_IN
    **stage((57.7, 26.0), 90, 'B', BOOST_CM5),       # bottom, output capacitors under the CM5 VIN pins (J301)
    **stage((65.7, 35.0), 0, 'F', BOOST_5V),         # top, beside the touch FPC (was over the charger, D65)
    **stage((25.5, 3.5), 90, 'B', BB_LTE),           # bottom above the socket, output toward VCC pins 70-74
    **stage((76.0, 22.0), 90, 'B', BB_AUX),          # bottom, between the CM5 boost and the SD card
    **stage((75.3, 30.0), 0, 'F', BACKLIGHT),        # top, north of the charger controller (D65)
}

# JLC06121H-3313A (6 layers, 1.2 mm, NP-155F; JLCPCB impedance-calculator template, see checkpoint 1)
STACKUP = [
    ('F.SilkS', 'Top Silk Screen', None, None, None), ('F.Paste', 'Top Solder Paste', None, None, None),
    ('F.Mask', 'Top Solder Mask', 0.01, None, None), ('F.Cu', 'copper', 0.035, None, None),
    ('dielectric 1', 'prepreg', 0.0994, '3313', 4.1), ('In1.Cu', 'copper', 0.0152, None, None),
    ('dielectric 2', 'core', 0.1, 'NP-155F', 4.36), ('In2.Cu', 'copper', 0.0152, None, None),
    ('dielectric 3', 'prepreg', 0.639, '3 x 7628', 4.4), ('In3.Cu', 'copper', 0.0152, None, None),
    ('dielectric 4', 'core', 0.1, 'NP-155F', 4.36), ('In4.Cu', 'copper', 0.0152, None, None),
    ('dielectric 5', 'prepreg', 0.0994, '3313', 4.1), ('B.Cu', 'copper', 0.035, None, None),
    ('B.Mask', 'Bottom Solder Mask', 0.01, None, None), ('B.Paste', 'Bottom Solder Paste', None, None, None),
    ('B.SilkS', 'Bottom Silk Screen', None, None, None)]


def outline():
    """95 x 65 with 1 mm corner radius and the two USB-A cutouts (HOAUC land, see the footprint)"""
    r = 1.0
    k = r * (1 - 1 / math.sqrt(2))
    s = [('L', (r, 0), (W - r, 0)), ('A', (W - r, 0), (W - k, k), (W, r)),
         ('L', (W, r), (W, H - r)), ('A', (W, H - r), (W - k, H - k), (W - r, H))]
    x = W - r
    y0, ystep, yrel = USBA_Y, USBA_Y + 2.5, USBA_Y + 6.83
    dy = math.sqrt(0.5 ** 2 - 0.25 ** 2)
    for cx in sorted(USBA_X, reverse=True):
        s += [('L', (x, H), (cx + 7.2, H)),
              ('L', (cx + 7.2, H), (cx + 7.2, yrel + dy)),
              ('A', (cx + 7.2, yrel + dy), (cx + 7.95, yrel), (cx + 7.2, yrel - dy)),
              ('L', (cx + 7.2, yrel - dy), (cx + 7.2, ystep)), ('L', (cx + 7.2, ystep), (cx + 7.45, ystep)),
              ('L', (cx + 7.45, ystep), (cx + 7.45, y0)), ('L', (cx + 7.45, y0), (cx - 7.45, y0)),
              ('L', (cx - 7.45, y0), (cx - 7.45, ystep)), ('L', (cx - 7.45, ystep), (cx - 7.2, ystep)),
              ('L', (cx - 7.2, ystep), (cx - 7.2, yrel - dy)),
              ('A', (cx - 7.2, yrel - dy), (cx - 7.95, yrel), (cx - 7.2, yrel + dy)),
              ('L', (cx - 7.2, yrel + dy), (cx - 7.2, H))]
        x = cx - 7.2
    s += [('L', (x, H), (r, H)), ('A', (r, H), (k, H - k), (0, H - r)),
          ('L', (0, H - r), (0, r)), ('A', (0, r), (k, k), (r, 0))]
    return s


def main():
    g = Gen(BOARD, os.path.join(BOARD, 'cm5_carrier.net'), os.path.join(BOARD, 'cm5_carrier.kicad_pcb'), W, H,
            copper_layers=6, thickness=1.2)
    g.edge(outline())
    # battery 8 x 65 x 85 beside the board, beyond the top edge (User.1)
    g.rect(pcbnew.User_1, 5.0, -3.0 - 65.0, 90.0, -3.0)
    g.text(pcbnew.User_1, 'BATTERY 85 x 65 x 8 mm (1S 5000 mAh), beside the board', 47.5, -38.0, 2.0)
    g.text(pcbnew.User_1, 'cable <= 80 mm to J102 (Molex 505570-0901 housing)', 47.5, -34.5, 1.5)
    # CM5 heat-spreader keep-out (User.2): nothing above the module except the spreader
    g.rect(pcbnew.User_2, CM5[0] - 20.0, CM5[1] - 27.5, CM5[0] + 20.0, CM5[1] + 27.5)
    g.text(pcbnew.User_2, 'CM5 heat spreader zone (module top ~4.6 mm, UNVERIFIED)', CM5[0], CM5[1], 1.2)

    # ribbon exits (User.3): from each FPC/FFC cable entry to the board edge it leaves by
    for x0, y0, x1, y1, label, tx, ty in (
            (59.74, 23.0, 95.0, 23.0, 'DISPLAY 30P ribbon -> right edge, 35 mm on board', 77.0, 22.0),
            (59.75, 38.5, 95.0, 38.5, 'TOUCH 8P ribbon -> right edge, 35 mm on board', 77.0, 37.5),
            (2.8, 30.0, -6.0, 30.0, 'CAM-B (front) 31P ribbon -> left edge', -6.0, 28.0),
            (2.8, 46.5, -6.0, 46.5, 'CAM-A (rear) 31P ribbon -> left edge', -6.0, 44.5),
            (47.0, 1.16, 47.0, -2.5, 'KBD FFC -> Board B', 47.0, -1.5),
            (33.0, 1.16, 33.0, -2.5, 'DIGITIZER FFC', 33.0, -1.5)):
        g.edge([('L', (x0, y0), (x1, y1))], layer=pcbnew.User_3, width=0.3)
        g.text(pcbnew.User_3, label, tx, ty, 0.8)
    for cx in USBA_X:                                  # USB-A cutouts: no board (+0.3 so copper keeps off the cut)
        g.block('both', (cx - 7.45 - 0.3, USBA_Y - 0.3, cx + 7.45 + 0.3, H + 1))
    g.place_fixed(FIXED)
    # NT101: Kelvin tap of the fuel-gauge shunt, right at the GND pad of R126 (outboard side)
    g.place_near_pad('NT101', 'R126', 'GND', 1.6, 'B')
    # the M.2 module (30 x 42 from the card-edge stop) blocks the bottom side even where its courtyard
    # stops short of the standoff
    g.block('B', (M2[0] - 15.0, M2[1] + 3.525, M2[0] + 15.0, M2[1] + 45.525))
    # keep the top side east of the camera connectors free where the CSI lanes come in (lane pins y 28.5-30.6 on
    # J705, 42.3-47.1 on J704): the camera passives go beside the other pins
    g.block('F', (6.6, 27.6, 12.0, 31.4))
    g.block('F', (6.6, 41.7, 12.0, 47.8))
    # the charger controller U103 (bottom) has the microSD contacts over its right edge: keep the rest of the top side
    # over it and west of it free, for the vias its pins need (its filter parts go on the bottom, around it)
    g.block('F', (69.0, 33.7, 80.2, 41.6))
    # ... and on its own side a ring of routing room around its pins (its filter / compensation parts go just outside)
    g.block('B', (72.3, 33.0, 80.0, 40.0))
    # parts whose schematic note says where they belong (the rule would pick another part on the same net)
    hints = {r: 'J502' for r in ('C513', 'C514', 'C515', 'C516', 'D503', 'R506', 'R507', 'R508', 'R509')}  # at the SIM
    hints.update({'C128': 'R109', 'C129': 'R109'})          # battery bulk caps at the battery sense resistor
    # the other parts stay where they were on the board ordered as Y4 (D114): that board was changed after its last full
    # placement (D105, D108), so a fresh autoplace would move 14 parts that have been routed and reviewed where they are
    # The Wi-Fi module's support parts north of its pads move north with its pad row (D114)
    frozen = json.load(open(os.path.join(HERE, 'data', 'placement_a_y4.json')))
    for r, dy in (('C601', 0.6), ('C602', 0.6), ('C603', 0.6), ('C604', 0.6), ('R602', 0.6), ('R605', 0.6), ('R606', 0.6),
                  ('FB601', 0.6), ('FB602', 0.6), ('TP1007', 0.425), ('TP1008', 0.375)):
        frozen[r][1] -= dy
    frozen['TP305'][:2] = [54.75, 49.75]        # D118: off J702's new pads
    g.place_fixed({r: tuple(v) for r, v in frozen.items() if r not in g.placed})
    pending = g.autoplace(tp_side='B', hints=hints)
    g.save(STACKUP, 1.2)
    g.report(pending)
    return 1 if pending else 0


if __name__ == '__main__':
    sys.exit(main())
