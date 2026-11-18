"""Project footprints (lib cm5h) for Board A and Board B, drawn from the cited datasheet drawings.

Run:  python3 gen/footprints.py      -> hw/board_a/lib/cm5h.pretty, hw/board_b/lib/cm5h.pretty,
                                        lib/cm5h.3dshapes/*.wrl (box models) and gen/data/fp_meta.json

Conventions: KiCad coordinates (mm, y down), top view, origin as stated per footprint. Every description names
its source drawing; values marked "approx." are body outlines read off a drawing (not dimensioned) and only
affect the fab outline, courtyard and 3D box, never the copper. fp_meta.json records the height above the board
(and below it, for parts that sink into a cutout or poke through the board) for the checkpoint 3 height check,
plus the verification status.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fpgen import Footprint  # noqa: E402

ROOT = os.path.join(HERE, '..')
MODEL = '${KIPRJMOD}/lib/cm5h.3dshapes/%s.wrl'
CM5_STEP = '${KIPRJMOD}/../../research/dl/radxa/step/radxa_cm5_3d_pcba.stp'

FPS = {}      # name -> (Footprint, build kwargs, boards, courtyard)
META = {}     # name -> dict(height, below, source, status, note)
BOXES = {}    # name -> [(x0, y0, x1, y1, z0, z1, rgb)] in footprint coordinates (y down), z from board top


def reg(f, boards, height, source, status='verified', note='', below=0.0, boxes=None, pin1=None, courtyard=True,
        silk=True, color=(0.15, 0.15, 0.15)):
    if boxes is None and f.body:
        x0, y0, x1, y1 = f.body
        boxes = [(x0, y0, x1, y1, 0.0, height, color)]
    if boxes:
        BOXES[f.name] = boxes
        f.model(MODEL % f.name)
    FPS[f.name] = (f, dict(pin1=pin1, silk=silk), boards, courtyard)
    META[f.name] = dict(height=height, below=below, source=source, status=status, note=note)


def paste_ring(f, r, d, n=8):
    """paste-only apertures on a ring (SMT nuts: keep paste out of the hole)"""
    for k in range(n):
        a = math.radians(180 / n + 360 / n * k)
        f.smd('', r * math.cos(a), r * math.sin(a), d, d, shape='circle', layers=('F.Paste',))


# --------------------------------------------------------------------------------------------- CM5 DF40 x 3
# Orange Pi CM5 (the module this carrier takes since the redesign, docs/opi/OPI_REDESIGN.md). Positions from the
# Orange Pi CM5 base board V1.2 top-side DXF (research/dl/orangepi/opi_cm5_base_v1.2_top.dxf, layer PIN_TOP: the
# three DF40 receptacle land rows, silkscreen pin numbers 1 / 2 / 99 / 100 and the four M2.5 holes, 48.001 x 32.999
# mm apart). Origin = module centre = centre of the four holes. Board orientation: the DXF is rotated so that JP1 is
# on the right, JP2 on the left and JP3 at the bottom (board x = -DXF y, board y = -DXF x, both relative to the hole
# centre): JP1 / JP2 pin 1 at the JP3 end. JP1 rows at x +16.9845 +-1.32 (odd row outer), JP2 at x -17.0155 +-1.32
# (odd row inner), pins 1..99 from y +7.2835 to -12.3165; JP3 rows at y +25.3235 +-1.32 (odd row outer), pins 1..99
# from x -9.8096 to +9.7904. Pads per the Hirose DF40C-100DS-0.4V recommended land (0.2 x 0.7 mm, outer 3.78 /
# inner 2.38 -> pad centres +-1.54 from the row centre), on Orange Pi's row centres. The module drawing
# (opi_cm5_v1.1_bot.dxf, plugs) agrees with these centres to 0.02 mm.
OPI_CM5 = {'JP1': ('x', 16.9845), 'JP2': ('x', -17.0155), 'JP3': ('y', 25.3235)}


def cm5_df40():
    pitch, off, pl, pw = 0.4, 1.54, 0.7, 0.2
    for jp, (axis, rc) in OPI_CM5.items():
        f = Footprint(f'OPi_CM5_DF40_{jp}',
                      f'Orange Pi CM5 board-to-board connector {jp}: Hirose DF40C-100DS-0.4V(51), 1.5 mm stack. '
                      'Position from the Orange Pi CM5 base board V1.2 DXF, pads per the Hirose DF40C-100DS '
                      'recommended land. Origin = CM5 module centre; place JP1, JP2 and JP3 at the same point.',
                      'Hirose DF40 Orange Pi CM5 board-to-board')
        for n in range(1, 101):
            s_ = ((n - 1) // 2) * pitch
            row = rc + (off if n % 2 else -off)    # odd row toward +x / +y: outer on JP1 and JP3, inner on JP2
            if axis == 'x':
                f.smd(n, row, 7.2835 - s_, pl, pw, rratio=0.25)
            else:
                f.smd(n, -9.8096 + s_, row, pw, pl, rratio=0.25)
        if axis == 'x':
            yc = 7.2835 - 49 * pitch / 2
            f.set_body(rc - 1.9, yc - 11.3, rc + 1.9, yc + 11.3, 1.5)
        else:
            xc = -9.8096 + 49 * pitch / 2
            f.set_body(xc - 11.3, rc - 1.9, xc + 11.3, rc + 1.9, 1.5)
        if jp == 'JP1':
            # the module itself: 40 x 55 mm (module DXF outline). No 3D model from Orange Pi: box model, module PCB
            # 1.6 mm on the 1.5 mm stack, top-side parts up to 1.5 mm (UNVERIFIED estimate, checkpoint REVIEW.md);
            # bottom-side parts sit inside the 1.5 mm stack. The courtyard covers the module.
            f.courtyard_extra.append((-20.0, -27.5, 20.0, 27.5))
            f.rect(-20.0, -27.5, 20.0, 27.5, 'F.Fab', 0.1)
            f.text('Orange Pi CM5 module outline 40 x 55', 0, 26.0)
            boxes = [(-20.0, -27.5, 20.0, 27.5, 1.5, 3.1, (0.1, 0.35, 0.15)),
                     (-17.0, -24.5, 17.0, 24.5, 3.1, 4.6, (0.6, 0.6, 0.62))]
            reg(f, ('a',), 4.6, 'Orange Pi CM5 V1.1 / V1.5 module DXF (outline 40 x 55, plug positions); heights '
                'estimated: 1.5 mm stack + 1.6 mm PCB + 1.5 mm parts', status='UNVERIFIED', boxes=boxes,
                note='carries the module courtyard; module height not published by Orange Pi')
            FPS[f.name] = (f, dict(pin1=None, silk=True), ('a',), True)
        else:
            FPS[f.name] = (f, dict(pin1=None, silk=True), ('a',), False)
            META[f.name] = dict(height=1.5, below=0.0, source='as connector JP1', status='verified',
                                note='no own courtyard: inside the module courtyard of connector JP1')


def cm5_hole():
    # Radxa IO board U33 pins 201-204 pad stack: 6.0 mm pad (outer layers), 4.0 mm inner, 2.6 mm plated hole
    f = Footprint('Radxa_CM5_MountingHole_M2.5', 'CM5 M2.5 mounting hole, plated, 2.6 mm drill, 6.0 mm pad, as the '
                  'Radxa CM5 IO board v2.200 (decal U33 pins 201-204). No courtyard: lies inside the CM5 courtyard.',
                  'Radxa CM5 mounting hole M2.5', attr='')
    f.th(1, 0, 0, 2.6, 6.0)
    FPS[f.name] = (f, dict(pin1=None, silk=False), ('a',), False)
    META[f.name] = dict(height=0.0, below=0.0, source='Radxa CM5 IO board v2.200 PADS layout', status='verified',
                        note='not used since checkpoint 3 (replaced by the SMT standoff)')


def cm5_standoff():
    f = Footprint('CM5_Standoff_SMT_M2.5_L1.5', 'CM5 mounting: YIYUAN SMTSOM2.515BTR M2.5 SMT standoff, 1.5 mm high '
                  '(= DF40 1.5 mm stack), at the M2.5 hole positions of the module. Hole 4.22 and minimum solder pad 6.2 per the '
                  'PEM SMTSO family table (YIYUAN SMTSO datasheet, M2.5 row: shank 4.09 x 1.53, body 5.56). The shank '
                  'protrudes ~0.33 mm through the 1.2 mm board. No courtyard: inside the CM5 courtyard.',
                  'CM5 module standoff M2.5 SMT nut')
    f.th('1', 0, 0, 4.22, 6.2)
    paste_ring(f, 2.6, 0.7)
    f.set_body(-2.78, -2.78, 2.78, 2.78, 1.5)
    BOXES[f.name] = [(-2.78, -2.78, 2.78, 2.78, 0.0, 1.5, (0.8, 0.75, 0.5)),
                     (-2.0, -2.0, 2.0, 2.0, -1.53, 0.0, (0.8, 0.75, 0.5))]
    f.model(MODEL % f.name)
    FPS[f.name] = (f, dict(pin1=None, silk=False), ('a',), False)
    META[f.name] = dict(height=1.5, below=0.33, source='YIYUAN SMTSO family table (C5301777 datasheet), M2.5 L 1.5',
                        status='verified', note='')


# --------------------------------------------------------------------------------------------- power ICs
def tps61088():
    f = Footprint('Texas_RHL0020A_VQFN-20-1EP_3.5x4.5mm_P0.5mm',
                  'TI RHL0020A VQFN-20 4.5 x 3.5 mm (TPS61088), land from TI SLVSCM8 "Example Board Layout" '
                  '(labels: 4.3 / 5.3 overall, pads 0.28 x 0.85, EP 3.05 x 2.05 with 4 tie bars 0.23 wide at '
                  '+-0.275). Drawing is not to scale; dimension labels used.', 'TPS61088 RHL VQFN')
    for p in range(2, 10):
        f.smd(p, -1.75 + (p - 2) * 0.5, 1.725, 0.28, 0.85, rratio=0.5)
    for p in range(12, 20):
        f.smd(p, 1.75 - (p - 12) * 0.5, -1.725, 0.28, 0.85, rratio=0.5)
    f.smd(1, -2.225, 0.75, 0.85, 0.28, rratio=0.5)
    f.smd(10, 2.225, 0.75, 0.85, 0.28, rratio=0.5)
    f.smd(11, 2.225, -0.75, 0.85, 0.28, rratio=0.5)
    f.smd(20, -2.225, -0.75, 0.85, 0.28, rratio=0.5)
    f.smd(21, 0, 0, 3.05, 2.05, rratio=0.05, paste_ratio=-0.2)
    for sx in (-1, 1):
        for sy in (-1, 1):
            f.smd(21, sx * 2.0875, sy * 0.275, 1.125, 0.23, rratio=0.0, shape='rect',
                  layers=('F.Cu', 'F.Mask'))
    f.set_body(-2.25, -1.75, 2.25, 1.75, 1.0)
    reg(f, ('a',), 1.0, 'TI TPS61088 SLVSCM8 RHL0020A package/land pages', pin1=(-2.95, 1.1))


def tps63020():
    f = Footprint('Texas_DSJ0014A_VSON-14-1EP_3x4mm_P0.5mm',
                  'TI DSJ0014A VSON-14 4 x 3 mm (TPS63020), land from the TI TPS63020 datasheet "Example Board '
                  'Layout": rows 2.8 apart, pads 0.24 x 0.6, EP 2.85 x 1.58 with 4 fingers per side (0.2 wide '
                  'at +-0.23 / +-0.69) out to +-2.2.', 'TPS63020 DSJ VSON')
    for p in range(1, 8):
        f.smd(p, -1.5 + (p - 1) * 0.5, 1.4, 0.24, 0.6, rratio=0.5)
    for p in range(8, 15):
        f.smd(p, 1.5 - (p - 8) * 0.5, -1.4, 0.24, 0.6, rratio=0.5)
    f.smd(15, 0, 0, 2.85, 1.58, rratio=0.05, paste_ratio=-0.2)
    for sx in (-1, 1):
        for y in (-0.69, -0.23, 0.23, 0.69):
            f.smd(15, sx * 1.8125, y, 0.775, 0.2, shape='rect', layers=('F.Cu', 'F.Mask'))
    f.set_body(-2.0, -1.5, 2.0, 1.5, 1.0)
    reg(f, ('a',), 1.0, 'TI TPS63020 datasheet DSJ0014A pages', pin1=(-2.2, 1.65))


def csd25404():
    f = Footprint('TI_VSON-CLIP-8_3.3x3.3mm_CSD25404Q3',
                  'TI CSD25404Q3 SON 3.3 x 3.3 mm, land per datasheet SLPS570 sec. 7.2: pins 1-4 0.5 x 0.63 at '
                  '0.65 pitch, pad 9 2.45 x 1.9 with tabs 5-8 (0.5 x 0.41).', 'CSD25404Q3 NexFET SON')
    for i, p in enumerate((1, 2, 3, 4)):
        f.smd(p, -0.975 + i * 0.65, 1.435, 0.5, 0.63, rratio=0.1)
    for i, p in enumerate((8, 7, 6, 5)):
        f.smd(p, -0.975 + i * 0.65, -1.545, 0.5, 0.41, rratio=0.1)
    f.smd(9, 0, -0.39, 2.45, 1.9, rratio=0.05, paste_ratio=-0.2)
    f.set_body(-1.65, -1.65, 1.65, 1.65, 1.0)
    reg(f, ('a',), 1.0, 'TI CSD25404Q3 SLPS570 sec. 7.2', pin1=(-1.95, 1.75))


def csd17577():
    f = Footprint('TI_VSONP-8_3.3x3.3mm_CSD17577Q3A',
                  'TI CSD17577Q3A SON 3.3 x 3.3 mm (Q3A), land per datasheet SLPS515A sec. 7.2: pins 1-4 0.6 x 0.3 '
                  'at x = -1.55, pad 9 1.775 x 2.45 from x = -0.56, drain fingers 5-8 0.635 x 0.3 beyond it. '
                  'Separate pads 5-8 (KiCad NexFET footprint merges them into pad 5).', 'CSD17577Q3A NexFET SON')
    for i, p in enumerate((1, 2, 3, 4)):
        f.smd(p, -1.55, -0.975 + i * 0.65, 0.6, 0.3, rratio=0.15)
    f.smd(9, -0.56 + 1.775 / 2, 0, 1.775, 2.45, rratio=0.03, paste_ratio=-0.2)
    for i, p in enumerate((8, 7, 6, 5)):
        f.smd(p, 1.215 + 0.635 / 2, -0.975 + i * 0.65, 0.635, 0.3, rratio=0.15)
    f.set_body(-1.65, -1.65, 1.65, 1.65, 1.0)
    reg(f, ('a',), 1.0, 'TI CSD17577Q3A SLPS515A sec. 7.2', pin1=(-2.05, -1.35))


def max17055():
    f = Footprint('Maxim_TDFN-10-1EP_2x2.5mm_P0.4mm_EP1.4x1.3mm',
                  'Maxim T102A2+1C TDFN-10 2.0 x 2.5 x 0.75 mm (MAX17055ETB+). Land per Maxim 90-100007 rev B '
                  '(pads 0.20 x 0.65 at 0.40 pitch, rows 2.45 apart, exposed pad 1.40 x 1.30); outline per Maxim '
                  '21-100013 rev C (pin 1 corner bottom-left in the top view, pins 1-5 along the 2.0 mm edge). '
                  'The earlier LCSC/EasyEDA land (0.685 pads, rows 2.433) differed by < 0.04 mm.', 'MAX17055 TDFN')
    for i in range(5):
        f.smd(1 + i, -0.8 + i * 0.4, 1.225, 0.2, 0.65, rratio=0.5)
        f.smd(6 + i, 0.8 - i * 0.4, -1.225, 0.2, 0.65, rratio=0.5)
    f.smd(11, 0, 0, 1.4, 1.3, rratio=0.05, paste_ratio=-0.15)
    f.set_body(-1.0, -1.25, 1.0, 1.25, 0.8)
    reg(f, ('a',), 0.8, 'Maxim 90-100007 rev B land pattern + 21-100013 rev C outline', pin1=(-1.2, 1.75))


# --------------------------------------------------------------------------------------------- inductors
def inductors():
    f = Footprint('L_Sunlord_WPN4020', 'Sunlord WPN4020H 4.0 x 4.0 x 2.0 mm, land per Sunlord WPN catalogue '
                  '(a = 1.9, b = 1.1, c = 3.7)', 'inductor Sunlord WPN4020')
    f.smd(1, -1.5, 0, 1.1, 3.7, rratio=0.1)
    f.smd(2, 1.5, 0, 1.1, 3.7, rratio=0.1)
    f.set_body(-2.0, -2.0, 2.0, 2.0, 2.0)
    reg(f, ('a',), 2.0, 'Sunlord WPN series catalogue, shape and land table')

    f = Footprint('L_Sunlord_WPN252012H', 'Sunlord WPN252012H 2.5 x 2.0 x 1.2 mm, land per Sunlord WPN catalogue '
                  '(a = 0.8, b = 0.85, c = 2.0)', 'inductor Sunlord WPN252012')
    f.smd(1, -0.825, 0, 0.85, 2.0, rratio=0.1)
    f.smd(2, 0.825, 0, 0.85, 2.0, rratio=0.1)
    f.set_body(-1.25, -1.0, 1.25, 1.0, 1.2)
    reg(f, ('a',), 1.2, 'Sunlord WPN series catalogue, shape and land table')

    f = Footprint('L_CMC_Murata_DLW21SN', 'Murata DLW21SN chip common-mode choke 2.0 x 1.2 x 1.2 mm, land per Murata '
                  'JEFL243C-0003V-01 sec. 16.7 (pads 0.9 x 0.4, gap 0.8, 2.6 x 1.2 overall); pads 1 top-left, 2 '
                  'top-right, 3 bottom-right, 4 bottom-left; windings 1-2 and 4-3 (sec. 5 equivalent circuit).',
                  'common mode choke Murata DLW21SN')
    f.smd(1, -0.85, -0.4, 0.9, 0.4, rratio=0.1)
    f.smd(2, 0.85, -0.4, 0.9, 0.4, rratio=0.1)
    f.smd(3, 0.85, 0.4, 0.9, 0.4, rratio=0.1)
    f.smd(4, -0.85, 0.4, 0.9, 0.4, rratio=0.1)
    f.set_body(-1.0, -0.6, 1.0, 0.6, 1.2)
    reg(f, ('a',), 1.2, 'Murata DLW21SN reference specification JEFL243C-0003V-01', pin1=(-1.5, -0.75))


# --------------------------------------------------------------------------------------------- Wi-Fi module
def ap6275p():
    # Sec. 6.2: the extension lines of 14.375 and 12.375 run through the pad centres, so these are centre-to-centre
    # spans (D114): 15.5 x 13.5 over the pads, which reach 0.25 mm past the 15.0 x 13.0 outline drawn there
    f = Footprint('AMPAK_AP6275P', 'AMPAK AP6275P 15.0 x 13.0 x 1.55 mm LGA, 50 pads 0.5 x 1.125 at 0.9 pitch, per '
                  'AP6275P datasheet sec. 6.2 Recommended footprint (11.70 / 9.00 spans, 14.375 x 12.375 between pad '
                  'centres: pads reach 0.25 past the outline). Pin 1 top of the left column.', 'AMPAK AP6275P WiFi')
    for i in range(11):
        f.smd(1 + i, -7.1875, -4.5 + i * 0.9, 1.125, 0.5, rratio=0.1)
    for i in range(14):
        f.smd(12 + i, -5.85 + i * 0.9, 6.1875, 0.5, 1.125, rratio=0.1)
    for i in range(11):
        f.smd(26 + i, 7.1875, 4.5 - i * 0.9, 1.125, 0.5, rratio=0.1)
    for i in range(14):
        f.smd(37 + i, 5.85 - i * 0.9, -6.1875, 0.5, 1.125, rratio=0.1)
    f.set_body(-7.5, -6.5, 7.5, 6.5, 1.55)
    reg(f, ('a',), 1.55, 'AMPAK AP6275P datasheet sec. 5.1 / 6.2', pin1=(-7.9, -5.2), color=(0.7, 0.7, 0.72))


# --------------------------------------------------------------------------------------------- FPC / FFC
def fpcs():
    # HDGC 0520-HX-30PWB: front insert, rear flip; tails (signal pads) at the rear, FPC enters from +y
    f = Footprint('FPC_0.5mm_30P_HDGC_0520-HX-30PWB', 'HDGC 0520-HX-30PWB 30-pin 0.5 mm FPC, 2.0 mm, front insert / '
                  'rear flip, double-sided contacts. Land per HDGC drawing (pads 0.25 x 1.30, mount pads 1.73 x '
                  '2.60, 2.80 / 5.03 dims). FPC enters from +y (side away from the signal pads). Body outline '
                  'approx. from the dashed outline.', 'FPC 0.5mm HDGC')
    for p in range(1, 31):
        f.smd(p, -7.25 + (p - 1) * 0.5, 0, 0.25, 1.30, rratio=0.1)
    for sx in (-1, 1):
        f.smd('MP', sx * 9.185, 3.08, 1.73, 2.60, rratio=0.1)
    f.set_body(-9.25, 0.28, 9.25, 4.74, 2.0)
    f.text('FPC in', 0, 5.6)
    reg(f, ('a',), 2.0, 'HDGC 0520-HX-nPWB drawing (2016-03-12)', note='3.27 mm with the actuator open',
        pin1=(-7.25, -1.0))

    f = Footprint('FPC_0.5mm_8P_XUNPU_FPC-05F-8PH15', 'XUNPU FPC-05F-8PH15 8-pin 0.5 mm FPC, 1.5 mm. Land per XUNPU '
                  'drawing (pads 0.30 x 0.90, mount pads 1.10 x 1.80, 2.70 / 4.05 dims). FPC enters from +y. '
                  'Body outline approx.', 'FPC 0.5mm XUNPU')
    for p in range(1, 9):
        f.smd(p, -1.75 + (p - 1) * 0.5, 0, 0.30, 0.90, rratio=0.1)
    for sx in (-1, 1):
        f.smd('MP', sx * 3.90, 2.70, 1.10, 1.80, rratio=0.1)
    f.set_body(-4.05, 0.35, 4.05, 4.75, 1.5)
    f.text('FPC in', 0, 5.5)
    reg(f, ('a',), 1.5, 'XUNPU FPC-05F-nPH15 drawing', pin1=(-1.75, -0.85))

    for name, n, pitch, pw, mpx, body_x, body_y0, src in (
            # body: 1.2 inside the pads' outer end, 5.99 deep (D115)
            ('FPC_0.5mm_12P_BXCONN_FC-05A12P11H20', 12, 0.5, 0.35, 4.45, 5.20, -6.45, 'BXCONN FC-05AxxP11H20'),):
        f = Footprint(name, f'{src} {n}-pin {pitch} mm FFC/FPC, 2.0 mm, easy-on R/A, bottom contact. Land per BXCONN '
                      f'drawing (pads {pw} x 1.5, mount pads 2.0 x 1.7 at 2.6 behind the pad row). Actuator and '
                      'cable entry at -y (side away from the signal pads). Body outline from the land drawing.',
                      'FFC FPC BXCONN')
        a = (n - 1) * pitch
        for p in range(1, n + 1):
            f.smd(p, -a / 2 + (p - 1) * pitch, 0, pw, 1.5, rratio=0.1)
        for sx in (-1, 1):
            f.smd('MP', sx * mpx, -2.6, 2.0, 1.7, rratio=0.1)
        f.set_body(-body_x, body_y0, body_x, -0.46, 2.0)
        f.text('FFC in', 0, body_y0 - 0.8)
        reg(f, ('a', 'b') if n == 12 else ('a',), 2.0, src + ' drawing (BXCONN)', note='3.6 mm with the actuator open',
            pin1=(-a / 2, 1.2))

    # Hirose FH35C-31S-0.3SHW: back flip, dual row staggered; odd pins front row (FPC side, +y)
    f = Footprint('Hirose_FH35C-31S-0.3SHW', 'Hirose FH35C-31S-0.3SHW(50) 0.3 mm pitch back-flip FPC, 0.9 mm. Land per '
                  'Hirose FH35C catalogue (front row odd pins 0.3 x 0.8, back row even pins 0.3 x 0.65 at 2.875, '
                  'fitting pads 0.4 x 0.95), positions as the Radxa CM5 IO board decal FH35C_31P_0_6SHW. FPC '
                  'enters from +y (front row side). Body outline approx.', 'FPC 0.3mm Hirose FH35C')
    for k in range(1, 32, 2):
        f.smd(k, -4.5 + (k - 1) / 2 * 0.6, 0, 0.3, 0.8, rratio=0.1)
    for k in range(2, 31, 2):
        f.smd(k, -4.2 + (k / 2 - 1) * 0.6, -2.875, 0.3, 0.65, rratio=0.1)
    for sx in (-1, 1):
        f.smd('MP', sx * 5.2, -0.275, 0.4, 0.95, rratio=0.1)
    f.set_body(-5.45, -3.25, 5.45, 0.2, 0.9)
    f.text('FPC in', 0, 1.3)
    reg(f, ('a',), 1.0, 'Hirose FH35C catalogue (2019) + Radxa CM5 IO board PADS decal', note='0.9 +-0.1 mm; 1.8 '
        'with the actuator open', pin1=(-4.5, 0.75))


# --------------------------------------------------------------------------------------------- SIM, USB-A
def nanosim():
    f = Footprint('GCT_SIM8066-6-1-14-01-A', 'GCT SIM8066-6-1-14-01-A nano-SIM push-push, 1.44 mm, card detect '
                  '(normally closed to GND). Land per GCT drawing (Recommended PCB Layout): contact row at y = 0, '
                  'GND tabs 0.70 x 2.10 at x = +-6.5, NPTH 0.75 locating pegs. Card inserts from +y; body 12.29 x '
                  '13.72 from y = 0.55. Keep-out areas (no copper) from the drawing, 0.1 mm added.',
                  'nano SIM GCT SIM8066')
    for name, x in (('C3', -4.83), ('C7', -3.56), ('C2', -2.29), ('C6', -1.02), ('C1', 0.25), ('C5', 1.52),
                    ('CD', 2.47)):
        f.smd(name, x, 0, 0.80, 1.14, rratio=0.1)
    # GND tabs: centre 2.05 below the top of the contact row, 12.00 apart; pegs 1.25 above the lower tabs (D115)
    for sx in (-1, 1):
        for y in (1.48, 13.48):
            f.smd('SH', sx * 6.5, y, 0.70, 2.10, rratio=0.1)
    f.th('', -5.0, 12.23, 0.75, 0.75, plated=False)
    f.th('', 3.5, 12.23, 0.75, 0.75, plated=False)
    m = 0.1
    for (x0, y0, x1, y1) in ((0.72, 1.66, 2.0, 4.21),
                             (-4.36, 5.07, -3.07, 8.22), (-1.83, 5.07, -0.52, 8.22), (0.72, 5.07, 2.0, 8.22),
                             (-4.64, 10.37, -2.78, 13.81), (-2.12, 10.37, -0.26, 13.81), (0.43, 10.37, 2.29, 13.81)):
        f.keepout([(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m), (x0 - m, y1 + m)], name='SIM keep-out')
    f.set_body(-6.145, 0.55, 6.145, 14.27, 1.45)
    f.text('card in', 0, 15.2)
    reg(f, ('a',), 1.45, 'GCT SIM8066 drawing rev. 19 March 2021', pin1=(-4.83, -1.0), color=(0.75, 0.75, 0.78))


def usba():
    # HOAUC HYCW236-USBA04-289B: mid-mount (sink) for a 1.2 mm board. Origin: x centre, y = 0 at the top edge of
    # the board cutout (= the edge of the signal pads in HOAUC's land); board edge at y = 8.28.
    f = Footprint('USB_A_HOAUC_HYCW236-USBA04-289B', 'HOAUC HYCW236-USBA04-289B USB-A 2.0 receptacle, mid-mount in a '
                  'board cutout (1.2 mm PCB), IPX8 gasket. Land per HOAUC drawing: pads 1.30 wide (4 3 2 1 at '
                  '-3.5 / -1.0 / +1.0 / +3.5, shell at +-6.4), plated slots 0.6 x 1.7 at x = +-8.05 (y = 4.63, '
                  'measured), cutout 14.90 wide to y = 2.5 then 14.40 wide to the board edge at y = 8.28, R0.5 '
                  'reliefs at (+-7.45, 6.83). Deviation: signal/shell pads end 0.3 mm short of the cutout edge '
                  '(JLC copper-to-edge rule); HOAUC pads reach the edge. The cutout is drawn on Dwgs.User here and '
                  'cut into Edge.Cuts by the board generator.', 'USB A mid-mount HOAUC', attr='through_hole')
    pl = 2.0 - 0.3
    for name, x in (('4', -3.5), ('3', -1.0), ('2', 1.0), ('1', 3.5), ('SH', -6.4), ('SH', 6.4)):
        f.smd(name, x, -0.3 - pl / 2, 1.30, pl, rratio=0.1)
    for sx in (-1, 1):
        f.th('SH', sx * 8.05, 4.63, None, (1.0, 2.1), shape='oval', slot=(0.6, 1.7))
    # cutout outline (documentation; the board generator cuts it)
    for (x0, y0, x1, y1) in ((-7.45, 0, 7.45, 0), (-7.45, 0, -7.45, 2.5), (7.45, 0, 7.45, 2.5),
                             (-7.45, 2.5, -7.2, 2.5), (7.45, 2.5, 7.2, 2.5), (-7.2, 2.5, -7.2, 8.28),
                             (7.2, 2.5, 7.2, 8.28)):
        f.line(x0, y0, x1, y1, 'Dwgs.User', 0.1)
    f.line(-10, 8.28, 10, 8.28, 'Dwgs.User', 0.05)
    f.text('board edge', 0, 8.9, 'Dwgs.User')
    f.set_body(-7.65, -0.05, 7.65, 9.8, 4.33)
    # Drawing: flange front 9.80 from the rear plate (y = 0), mouth 1.50 beyond it; board edge at y = 8.28 (D115)
    boxes = [(-7.2, 0.0, 7.2, 8.92, -2.89, 4.33, (0.75, 0.75, 0.78)),        # shell, sunk in the cutout
             (-7.65, 8.92, 7.65, 9.80, -2.89, 4.33, (0.75, 0.75, 0.78)),     # front flange
             (-6.55, 9.80, 6.55, 11.30, -2.5, 3.9, (0.1, 0.1, 0.1))]         # mouth (cross-section approx.)
    reg(f, ('a',), 4.33, 'HOAUC HYCW236-USBA04-289B drawing (2014-02-23)', below=2.89, boxes=boxes,
        note='4.33 above / 2.89 below the board top (1.69 below the bottom); flange front 1.52 mm and mouth front '
        '3.02 mm past the board edge', status='verified')


# --------------------------------------------------------------------------------------------- M.2 + standoff
def m2():
    # HOAUC HYCW11B-05NGFF-320B (H3.2). Origin: x centre, y = 0 at the odd (rear) pad row. Module bottom 1.25 mm
    # above the board. Card edge stop 1.75 mm behind the locating pegs (section A-A) -> y = 3.525; a 30 x 42 card
    # extends to y = 45.525; its mounting notch centre is 1.0 mm inside the card end (Quectel EM060K fig. 35).
    f = Footprint('M.2_Key-B_HOAUC_HYCW11B', 'HOAUC HYCW11B-05NGFF-320B M.2 Key-B socket, 3.2 mm, module bottom 1.25 '
                  'mm above the board. Land per HOAUC recommended PCB layout: 0.30 x 1.55 pads at 0.5 pitch, odd '
                  'row at y = 0, even row at y = 7.55, support pads 1.20 x 2.75 at x = +-10.35, NPTH 1.10 / 1.60 '
                  'at (-10, 5.275) / (10, 5.275). The module extends toward +y (slot on the even-row side, '
                  'section A-A); 3042 module outline and standoff position on F.Fab. The courtyard covers the '
                  'module; two openings behind the VCC pins (2/4 and 70/72/74, y 8.6 to 10.85) take the EM060K '
                  'reference MLCC arrays (Quectel EM060K HD 3.5.2) under the module edge: parts there must be '
                  '<= 0.6 mm high (module bottom 1.25 mm). The rest of the module area stays clear for the thermal '
                  'pad (HD 6.7).', 'M.2 NGFF key B HOAUC')
    for n in range(1, 76, 2):
        if 12 <= n <= 19:
            continue
        f.smd(n, -9.25 + (n - 1) / 2 * 0.5, 0, 0.30, 1.55, rratio=0.1)
    for n in range(2, 75, 2):
        if 12 <= n <= 19:
            continue
        f.smd(n, -9.0 + (n - 2) / 2 * 0.5, 7.55, 0.30, 1.55, rratio=0.1)
    for sx in (-1, 1):
        f.smd('', sx * 10.35, -0.775 + 0.155 + 1.375, 1.20, 2.75, rratio=0.1)
    f.th('', -10.0, 5.275, 1.10, 1.10, plated=False)
    f.th('', 10.0, 5.275, 1.60, 1.60, plated=False)
    f.rect(-15.0, 3.525, 15.0, 45.525, 'F.Fab', 0.1)
    f.circle(0, 44.525, 1.75, 'F.Fab', 0.1)
    f.text('M.2 3042 module (EM060K-GL)', 0, 25.0)
    f.set_body(-11.0, -0.9, 11.0, 7.3, 3.2)
    f.courtyard_extra.append((-15.0, 3.525, 15.0, 44.525 - 3.1 - 0.75))   # the standoff footprint owns the end
    for hx0, hx1 in ((-11.0, -6.6), (6.6, 11.0)):          # MLCC openings behind pins 2/4 and 70/72/74
        f.courtyard_holes.append((hx0, 8.6, hx1, 10.85))
        f.rect(hx0, 8.6, hx1, 10.85, 'F.Fab', 0.05)
    boxes = [(-11.0, -0.9, 11.0, 7.3, 0.0, 3.2, (0.1, 0.1, 0.1)),
             (-15.0, 3.525, 15.0, 45.525, 1.25, 2.05, (0.1, 0.45, 0.2)),   # module PCB 0.8 mm
             (-13.0, 8.0, 13.0, 42.0, 2.05, 3.55, (0.7, 0.7, 0.72))]       # shield/components 1.5 max
    reg(f, ('a',), 3.55, 'HOAUC HYCW11B-05NGFF-320B drawing (2014-02-23) + Quectel EM060K HD V1.1 fig. 35',
        boxes=boxes, note='socket 3.2 mm; module top 1.25 + 2.3 = 3.55 mm from the board', pin1=(-9.25, -1.3))

    f = Footprint('M.2_SMT_Standoff_M2', 'M.2 module standoff: Sinhoo SMTSO2010CTJ (M2 x 0.4 thread, 1.00 +-0.13 mm '
                  'high, flange 5.56, shank 3.60 x 1.53). Hole 3.73 and minimum solder pad 6.2 per the PEM SMTSO '
                  'family table (YIYUAN SMTSO datasheet, M2 row). The 1.53 mm shank protrudes ~0.33 mm through a '
                  '1.2 mm board. Solder pad 6.2 on the standoff side only; 4.3 mm (0.29 mm ring) on the inner layers and '
                  'the far side, which is under the CM5 module next to its JP3 connector.', 'M.2 standoff SMT nut M2')
    # plated (optional per YIYUAN: "plated through hole not required"); small far-side ring clears CM5 JP3 (D86)
    f.th('1', 0, 0, 3.73, 6.2, inner=4.3, back=4.3)
    paste_ring(f, 2.5, 0.85)
    f.set_body(-2.78, -2.78, 2.78, 2.78, 1.0)
    boxes = [(-2.78, -2.78, 2.78, 2.78, 0.0, 1.0, (0.8, 0.75, 0.5)), (-1.8, -1.8, 1.8, 1.8, -1.53, 0.0, (0.8, 0.75, 0.5))]
    reg(f, ('a',), 1.0, 'Sinhoo SMTSO2010CTJ drawing + YIYUAN SMTSO table', below=0.33, boxes=boxes,
        note='module notch rests on it; a 1.0 mm nut leaves the module end 0.25 mm lower than the socket (1.25)')


# --------------------------------------------------------------------------------------------- battery connector
def molex():
    # Molex 505578-0971 right-angle SMT plug (Micro-Lock Plus 2.0). Origin: x centre (between pins 1 and 9),
    # y = 0 at the signal pad centres. Mating face toward +y.
    f = Footprint('Molex_Micro-Lock_Plus_505578-0971_1x09_P2.00mm_Horizontal',
                  'Molex Micro-Lock Plus 2.0 505578-0971 right-angle SMT plug, 9 circuits, mates 505570-0901. Land '
                  'per Molex drawing 5055780001 rev C sheet 2: pads 1.0 x 2.5 at 2.0 pitch, nail pads 1.8 x 3.8 '
                  '(1.5 from pin 1 / N), nail pads 1.0 to 4.8 below the signal pad edge; body 22.0 x 8.45 x 5.9, '
                  'mating face toward +y.', 'Molex Micro-Lock Plus 505578')
    for p in range(1, 10):
        f.smd(p, -8.0 + (p - 1) * 2.0, 0, 1.0, 2.5, rratio=0.1)
    for sx in (-1, 1):
        f.smd('MP', sx * (8.0 + 2.4), 1.25 + 1.0 + 1.9, 1.8, 3.8, rratio=0.1)
    f.set_body(-11.0, 0.15, 11.0, 8.6, 5.9)
    f.text('battery plug in', 0, 9.6)
    reg(f, ('a',), 5.9, 'Molex 5055780001 PSD 000 rev C (LCSC C17389413 datasheet)', pin1=(-8.0, -1.8),
        color=(0.12, 0.12, 0.12))


# --------------------------------------------------------------------------------------------- Board B
def bm20b():
    f = Footprint('Hirose_BM20B_0.8_-40DS-0.4V', 'Hirose BM20B(0.8)-40DS-0.4V(51) 40-pin 0.4 mm board-to-FPC '
                  'receptacle, 0.8 mm mated. Land per Hirose BM20 catalogue (H = 0.8): pads 0.23 x 0.42, rows 2.6 / '
                  '1.76, fitting pads 0.3 x 0.75 (1.1 gap) at C = 10.02. Pin numbering as Solder Party BBQ20KBD '
                  '(1-20 one row, 21-40 the other, counter-clockwise).', 'Hirose BM20 BBQ20 keyboard')
    for i in range(20):
        f.smd(1 + i, -3.8 + i * 0.4, -1.09, 0.23, 0.42, rratio=0.1)
        f.smd(21 + i, 3.8 - i * 0.4, 1.09, 0.23, 0.42, rratio=0.1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            f.smd('', sx * 5.01, sy * 0.925, 0.3, 0.75, rratio=0.1)
    f.set_body(-5.24, -1.5, 5.24, 1.5, 0.8)
    reg(f, ('b',), 0.8, 'Hirose BM20 catalogue (Aug 2019) + BBQ20KBD', pin1=(-3.8, -1.75))


def side_switch():
    # Alps SKRTLAE010, land per the Alps drawing (C110293 datasheet p.3), in the coordinates of KiCad's
    # SW_Push_1P1T-MP_NO_Horizontal_Alps_SKRTLAE010 (so placements stay valid). Alps puts the two 0.9 mm guide-boss
    # holes 0.075 mm from the outer terminal pads and 0.15 mm from the MP pads; JLCPCB needs 0.2 mm from an NPTH to
    # copper. Here the outer terminal pads move 0.125 mm inward (still covering the 0.65 mm terminal) and the MP pads
    # lose 0.05 mm on the hole side. The hatched "prohibited area of copper tracks" is a keep-out.
    f = Footprint('SW_Alps_SKRTLAE010_JLC', 'Alps SKRTLAE010 side-push switch; Alps land (C110293 p.3) with pads moved '
                  'to keep 0.2 mm from the guide-boss holes (JLCPCB NPTH-to-copper rule)', 'switch side push Alps SKRT')
    for sx in (-1, 1):
        f.smd('1', sx * 1.1, -0.9, 0.75, 1.8, rratio=0.25)
        f.smd('MP', sx * 1.85, 1.075, 1.3, 0.85, rratio=0.25)
        f.th('', sx * 2.125, 0.0, 0.9, 0.9, plated=False)
    f.smd('2', 0.0, -0.9, 0.6, 1.8, rratio=0.25)
    # Hatched area: 2 x 1.2, its far side level with the MP pads' far side, 1.5 from the holes' centre line. Body: rear
    # 1.2 behind the guide bosses, 3.4 long with the button (D115)
    f.keepout([(-1.0, 0.30), (1.0, 0.30), (1.0, 1.50), (-1.0, 1.50)], name='Alps: no copper tracks')
    f.set_body(-2.25, -1.2, 2.25, 2.2, 3.3)
    reg(f, ('a',), 3.3, 'Alps SKRTLAE010 drawing + land (C110293)', color=(0.7, 0.7, 0.72),
        note='outer pads -0.125 mm inward, MP pads -0.05 mm, for 0.2 mm NPTH-to-copper')


def build_all():
    side_switch()
    cm5_df40()
    cm5_standoff()
    tps61088()
    tps63020()
    csd25404()
    csd17577()
    max17055()
    inductors()
    ap6275p()
    fpcs()
    nanosim()
    usba()
    m2()
    molex()
    bm20b()


def write():
    build_all()
    out = {'a': os.path.join(ROOT, 'hw', 'board_a', 'lib'), 'b': os.path.join(ROOT, 'hw', 'board_b', 'lib')}
    for name, (f, kw, boards, courtyard) in FPS.items():
        for b in boards:
            f.write(os.path.join(out[b], 'cm5h.pretty'), courtyard=courtyard, **kw)
            if name in BOXES:
                _vrml(os.path.join(out[b], 'cm5h.3dshapes', name + '.wrl'), BOXES[name])
    json.dump(META, open(os.path.join(HERE, 'data', 'fp_meta.json'), 'w'), indent=1, sort_keys=True)
    print(f'{len(FPS)} footprints written')


def _vrml(path, boxes):
    """VRML 2.0 boxes; KiCad VRML unit = 0.1 inch, model y up (= -y of the footprint)"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = ['#VRML V2.0 utf8']
    for (x0, y0, x1, y1, z0, z1, c) in boxes:
        my0, my1 = -y1, -y0
        cx, cy, cz = (x0 + x1) / 2 / 2.54, (my0 + my1) / 2 / 2.54, (z0 + z1) / 2 / 2.54
        sx, sy, sz = abs(x1 - x0) / 2.54, abs(my1 - my0) / 2.54, abs(z1 - z0) / 2.54
        out.append('Transform { translation %.5f %.5f %.5f children [ Shape { appearance Appearance { material '
                   'Material { diffuseColor %.2f %.2f %.2f } } geometry Box { size %.5f %.5f %.5f } } ] }'
                   % (cx, cy, cz, c[0], c[1], c[2], sx, sy, sz))
    open(path, 'w').write('\n'.join(out) + '\n')


if __name__ == '__main__':
    write()
