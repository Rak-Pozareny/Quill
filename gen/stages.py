"""Board A switching power stages, laid out by hand from the TI layout examples.

Each stage is drawn as seen from the side it is mounted on (a top-side view of the parts: x right, y down, mm,
part rotations as KiCad shows them on the top). stage() mirrors a bottom-side drawing so it reads the same from below,
then turns the whole group and moves it to its board position.

Pin 1 of a two-pin part is the first net in the schematic call (capacitors: rail = pin 1, GND = pin 2; inductors:
input = pin 1). Rotation 90 puts pin 1 at +y, 270 at -y, 180 at +x.
"""
import math


def stage(origin, rot, side, parts):
    """parts {ref: (dx, dy, part_rot)} -> FIXED entries {ref: (x, y, rot, side)} in board coordinates"""
    a = math.radians(rot)
    out = {}
    for ref, (dx, dy, pr) in parts.items():
        if side == 'B':
            dx, pr = -dx, -pr
        x = origin[0] + dx * math.cos(a) + dy * math.sin(a)
        y = origin[1] - dx * math.sin(a) + dy * math.cos(a)
        out[ref] = (round(x, 3), round(y, 3), (pr + rot) % 360, side)
    return out


# ------------------------------------------------------------------------------------------------ BQ25713 charger
# TI SLUSD83C 12.1 / Fig. 12-1. Buck half bridge Q1 (HS) over Q2 (LS) with the shared SW1 column facing L1; RAC
# and the input capacitors on the other side so CBUS -> RAC -> Q1 -> Q2 -> GND is one tight loop (rule 2);
# boost half bridge Q3 (LS) over Q4 (HS) mirrored on the right of L1, the VSYS capacitors right of Q3/Q4 with a
# VSYS bus between the two rows and GND on the outer edges (rule 4). The controller sits under L1 with its gate-drive
# edge (pins 23-32) toward the FETs; bootstrap capacitors on the same side next to BTST1/BTST2 (rule 9).
# CSD17577Q3A: source pins 1-3 + gate 4 on one side, drain 5-8 + tab on the other; rot 0 = source left.
CHARGER = {
    'Q101': (0.0, 0.0, 180),            # Q1 buck HS: drain (CHG_IN_S) left, source (SW1) right
    'Q102': (0.0, 4.0, 0),              # Q2 buck LS: source (GND) left, drain (SW1) right
    'L101': (6.65, 2.0, 0),             # pad 1 SW1 left, pad 2 SW2 right
    'Q103': (13.3, 0.0, 180),           # Q3 boost LS: drain (SW2) left, source (GND) right
    'Q104': (13.3, 4.0, 0),             # Q4 boost HS: source (SW2) left, drain (VSYS) right
    'U103': (6.65, 8.62, 0),            # gate-drive pins 23-32 on the top / top-right edge
    'R108': (-6.5, 0.0, 0),             # RAC 10 mOhm: CHG_IN left, CHG_IN_S right (at Q1 drain)
    'C116': (-2.75, 3.0, 270), 'C117': (-4.3, 3.0, 270),               # 10 nF + 1 nF after RAC, to Q2 source
    'C110': (-5.9, 3.75, 270), 'C111': (-8.0, 3.75, 270),              # CBUS 4 x 10 uF before RAC
    'C112': (-10.1, 3.75, 270), 'C113': (-12.2, 3.75, 270),
    'C115': (-13.8, 3.0, 270),
    'C127': (15.97, 2.0, 90),                                          # CSYS: 100 nF nearest Q3 / Q4
    'C120': (17.29, 2.0, 90), 'C121': (18.89, 2.0, 90), 'C122': (20.49, 2.0, 90),
    'C123': (16.24, 5.6, 270), 'C124': (17.84, 5.6, 270), 'C125': (19.44, 5.6, 270), 'C126': (21.04, 5.6, 270),
    'C118': (3.45, 6.9, 90),            # BTST1 - SW1
    'C119': (9.85, 6.9, 90),            # BTST2 - SW2
    'C133': (10.9, 9.45, 90),           # REGN (1.3 mm from the right pin row: the pins between leave past it)
}

# ------------------------------------------------------------------------------------------------ TPS61088 boost
# TI ZHCSDP8A Fig. 19: inductor on the SW pins (bottom row 4-7), output capacitors along VOUT (top row 14-16) with
# their GND pads toward GND pin 12 / thermal pad, 1 uF right at VOUT/GND, bootstrap next to BOOT (8).
BOOST_CM5 = {
    'U201': (0.0, 0.0, 0),
    'L201': (-3.0, 6.04, 0),            # pad 2 (SW) under the SW pins, pad 1 (VSYS) left
    'C204': (2.1, 3.4, 270),            # BOOT (pin 1) at pin 8, SW to the inductor pad
    'C202': (3.45, 1.9, 90),            # 100 nF at VIN (pin 9)
    'C201': (-8.55, 6.04, 90),          # 10 uF at the inductor input
    'C207': (1.75, -3.4, 270),          # 1 uF: GND pad over pin 12, VOUT pad on the VOUT bus
    'C208': (-1.6, -6.1, 90), 'C209': (0.45, -6.1, 90), 'C210': (2.5, -6.1, 90),     # 3 x 22 uF
    # feedback divider over FB (17), sensed from the first output capacitor; compensation left of the IC
    'R205': (-3.7, -2.97, 0), 'R206': (-1.6, -2.97, 0),               # 169k VOUT->FB, 56k FB->GND
    'R204': (-4.6, -1.4, 270), 'C206': (-4.6, 1.0, 270),              # COMP 7.5k + 5.6 nF
}

# ------------------------------------------------------------------------------------------------ TPS61089 boost
# TI SLVSD38C Fig. 11-1: inductor straight on SW (pin 11), output capacitors across VOUT (6) / GND (5) right under the
# IC, input capacitors at VIN (9) and at the inductor input, bootstrap between BOOT (10) and the SW copper.
BOOST_5V = {
    'U202': (0.0, 0.0, 0),
    'L202': (-2.0, -6.0, 270),          # pad 2 (SW) down onto pin 11, pad 1 (VSYS) up
    'C214': (2.6, -2.1, 180),           # BOOT (pin 1) right, SW pad left on the SW copper
    'C212': (2.4, -0.2, 270),           # 100 nF at VIN
    'C211': (2.85, -8.0, 270),          # 10 uF at the inductor input
    'C216': (0.0, 2.02, 180),           # 1 uF: VOUT pad under pin 6, GND pad under pin 5
    'C217': (0.0, 3.56, 180), 'C218': (0.0, 5.61, 180), 'C219': (0.0, 7.66, 180),    # 3 x 22 uF
    # feedback divider straight off FB (3), the two FB pads stacked; compensation below it
    'R212': (-2.75, 0.25, 180), 'R211': (-2.75, 1.29, 0),             # 100k FB->GND, 324k VOUT->FB
    'R210': (-2.4, 2.85, 270), 'C215': (-2.4, 4.75, 270),             # COMP 8.2k + 6.8 nF
}


# ------------------------------------------------------------------------------------------------ TPS63020 buck-boost
# TI SLVS916I Fig. 31: inductor on the L1 / L2 end (pins 6-9), input capacitors at VIN (10, 11), output capacitors
# at VOUT (4, 5) with the first one's GND pad at GND pin 2.
# Feedback divider (optional) left of the IC, FB leaving pin 3 to the left under pins 1-2.
def buckboost(u, l, cin, cout, fb=None):
    d = {u: (0.0, 0.0, 0), l: (4.79, 0.0, 270),                         # pad 1 (L1) up, pad 2 (L2) down
         cin[0]: (-0.53, -2.8, 180), cin[1]: (-0.53, -4.38, 180),
         cout[0]: (-0.45, 3.03, 180), cout[1]: (-0.45, 5.08, 180), cout[2]: (-0.45, 7.13, 180)}
    if fb:
        d.update({fb[1]: (-3.45, 1.95, 180), fb[0]: (-3.45, 3.0, 0)})  # FB->GND, VOUT->FB (FB pads stacked)
    return d


# LTE: the left of the IC is the board edge; its divider goes on the top side right over FB (placer)
BB_LTE = buckboost('U203', 'L203', ('C221', 'C222'), ('C223', 'C224', 'C225'))
BB_AUX = buckboost('U204', 'L204', ('C227', 'C228'), ('C229', 'C230', 'C231'), ('R219', 'R220'))

# ------------------------------------------------------------------------------------------------ TPS61169 backlight
# TI SNVSA40B Fig. 7-15: inductor on SW, Schottky from SW to VOUT, output capacitor back to the IC ground, RSET at FB.
BACKLIGHT = {
    'U702': (0.0, 0.0, 0),
    'L701': (-3.6, -0.65, 0),           # pad 2 (SW) next to pin 1
    'D701': (-3.6, 2.4, 0),             # anode (pin 2) on the SW copper, cathode (LEDA) left
    'C704': (-3.9, 4.65, 0),            # 1 uF 50 V from LEDA to GND
    'C705': (1.0, -2.75, 90),           # 4.7 uF at VIN (pin 5)
    'R703': (0.6, 2.7, 270),            # RSET from FB (pin 3) to GND
}
