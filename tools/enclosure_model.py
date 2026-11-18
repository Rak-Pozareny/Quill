#!/usr/bin/env python3
"""Block model of the FLIPOUT-style shell (docs/enclosure/ENCLOSURE.md, E1-E6) and a first printable mock-up.

usage: enclosure_model.py OUT_DIR
       (needs build123d, shapely, numpy, pillow; reads docs/enclosure/model/board_*_envelope.json, written by
        tools/board_envelopes.py)

Writes to OUT_DIR:
  enclosure_open.step / enclosure_closed.step   halves, boards (part envelopes), battery, display, keyboard
                                                placeholder, rear camera, pivot
  mockup_screen_half.stl                        printable, front face down
  mockup_keyboard_half.stl                      printable, back face down
  view_*.png                                    pictures

World frame: mm, x to the right, y up, z out of the front, seen from the front with the device open and the keyboard
at the bottom. Keyboard half x 0-S, y 0-S, z 0-KB_T. The screen half sits on it (z from KB_T + GAP) and turns
about the pivot P; the screen half is modelled in its open position, and closed = turned +90 degrees about P.

This is a block model: the shells are solid blocks with the outside shape only (no wall, boss or clip design yet),
the boards are courtyard boxes at their real heights, and the keyboard outline is a placeholder (not measured).
"""
import json
import math
import os
import sys

import numpy as np
import shapely
from shapely import affinity
from PIL import Image, ImageDraw
from build123d import (Axis, Box, Compound, Cylinder, Location, Polyline, Pos, RegularPolygon, Rot, Solid,
                       export_step, export_stl, extrude, make_face, Color)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MODEL = os.path.join(ROOT, 'docs', 'enclosure', 'model')

# ---- parameters (ENCLOSURE.md E1-E5, mechanical_inputs.md) ----
S = 98.5            # square halves
A = 22.5            # pivot set in from the two edges
P = (S - A, S - A)  # pivot, right side (E5)
KB_T = 20.5         # keyboard half (E4)
SC_T = 16.1         # screen half: display 3.76 + 6.1 + board 1.2 + 3.55 + 0.3 + back 1.2
GAP = 0.5           # between the halves (washer / shim at the pivot)
Z_SB = KB_T + GAP   # screen half back face
Y0S = S - 2 * A     # screen half, open: y from Y0S to Y0S + S
BACK = 1.2          # back wall
# Board A in the screen half (open): turned 180 degrees, cable edge toward the keyboard
XA0, YA0 = S - 2.0, Y0S + 30.5            # world x = XA0 - xb, y = YA0 + yb
ZA = Z_SB + BACK + 0.3 + 3.55             # Board A bottom face
# Board B in the keyboard half: not turned, its top edge (carrier FFC) toward the screen half
XB0, YB0 = (S - 74.0) / 2, 1.5 + 53.1     # world x = XB0 + xb, y = YB0 - yb
KBD_H = 3.0                               # Q20 keyboard height: NOT MEASURED
ZB = KB_T - KBD_H - 0.8 - 2.0             # Board B bottom face (keyboard on J201's 0.8 mm stack)
BATT = (85.0, 65.0, 8.0)
DISP = (85.99, 84.0, 3.76)                # module, FPC edge toward the device's left (rotated 90 degrees)
# rear camera (E3 / E5): bump outline incl. walls, open frame
BUMP = (63.5, Y0S + 61.5, S, Y0S + 96.5)  # x0, y0, x1, y1
BUMP_D = 9.3                              # below the screen half's back
CAM = 32.0
CHANNEL_CLR = 0.5
M4_HOLE, M4_NUT_AF, M4_NUT_T, M4_HEAD_D, M4_HEAD_T = 4.4, 7.0, 3.2, 7.0, 7.2   # HEAD_T = counterbore depth: an M4 x 30 bolt ends at z 37.2, in the nut


def box(x0, y0, z0, x1, y1, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def poly_face(coords):
    pts = [(float(x), float(y)) for x, y in coords]
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    return make_face(Polyline(*pts, close=True))


def prism(sh_poly, z0, z1):
    """shapely polygon -> solid from z0 to z1"""
    f = poly_face(sh_poly.exterior.coords)
    for h in sh_poly.interiors:
        f = f - poly_face(h.coords)
    return Pos(0, 0, z0) * extrude(f, z1 - z0)


def load(name):
    return json.load(open(os.path.join(MODEL, name)))


def board_a():
    d = load('board_a_envelope.json')
    th = d['thickness']
    outer = shapely.Polygon([(XA0 - x, YA0 + y) for x, y in d['outline'][0]['outer']])
    parts = [prism(outer, ZA, ZA + th)]
    for p in d['parts']:
        h = p['h'] or 0.0
        if h <= 0.05:
            continue
        xa, xb = XA0 - p['x1'], XA0 - p['x0']
        ya, yb = YA0 + p['y0'], YA0 + p['y1']
        if p['side'] == 'T':
            z0 = ZA + th - (p['sink'] or 0.0)
            parts.append(box(xa, ya, z0, xb, yb, ZA + th + h))
        else:
            parts.append(box(xa, ya, ZA - h, xb, yb, ZA))
    return parts


def board_b():
    d = load('board_b_envelope.json')
    th = d['thickness']
    o = d['outline'][0]
    outer = shapely.Polygon([(XB0 + x, YB0 - y) for x, y in o['outer']],
                            [[(XB0 + x, YB0 - y) for x, y in h] for h in o['holes']])
    parts = [prism(outer.buffer(0), ZB, ZB + th)]
    for p in d['parts']:
        h = p['h'] or 0.0
        if h <= 0.05:
            continue
        xa, xb = XB0 + p['x0'], XB0 + p['x1']
        ya, yb = YB0 - p['y1'], YB0 - p['y0']
        if p['side'] == 'T':
            parts.append(box(xa, ya, ZB + th, xb, yb, ZB + th + h))
        else:
            parts.append(box(xa, ya, ZB - h, xb, yb, ZB))
    return parts


def bump_poly(clr=0.0):
    x0, y0, x1, y1 = BUMP
    return shapely.box(x0 - clr, y0 - clr, x1 + clr, y1 + clr)


def channel_poly():
    """the bump's sweep from open (0) to closed (+90 degrees about P), inside the keyboard half"""
    b = bump_poly(CHANNEL_CLR)
    sweep = shapely.union_all([affinity.rotate(b, k, origin=P) for k in np.linspace(0, 90, 181)])
    return sweep.intersection(shapely.box(-1, -1, S + 1, S + 1)).simplify(0.02)   # past the edges: no coincident faces


def groove(x0, y0, x1, y1, z_face, depth, w=0.6, top=True):
    """rectangular outline groove into a face (top = face looks +z)"""
    outer = shapely.box(x0 - w / 2, y0 - w / 2, x1 + w / 2, y1 + w / 2)
    inner = shapely.box(x0 + w / 2, y0 + w / 2, x1 - w / 2, y1 - w / 2)
    ring = outer.difference(inner)
    return prism(ring, z_face - depth, z_face + 0.01) if top else prism(ring, z_face - 0.01, z_face + depth)


def side_marker(face, c, z, w, h, depth=1.0):
    """1 mm recess marking a port / button on a side face of the screen half (open frame)"""
    if face == 'top':
        return box(c - w / 2, Y0S + S - depth, z - h / 2, c + w / 2, Y0S + S + 0.01, z + h / 2)
    if face == 'right':
        return box(S - depth, c - w / 2, z - h / 2, S + 0.01, c + w / 2, z + h / 2)
    return box(-0.01, c - w / 2, z - h / 2, depth, c + w / 2, z + h / 2)          # left


def screen_half():
    zf = Z_SB + SC_T
    body = box(0, Y0S, Z_SB, S, Y0S + S, zf)
    x0, y0, x1, y1 = BUMP
    body = body + box(x0, y0, Z_SB - BUMP_D, x1, y1, Z_SB)
    # lens window, 7 mm, centred on the camera
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    body = body - Pos(cx, cy, Z_SB - BUMP_D + 0.5) * Cylinder(3.5, 1.2)
    # display outline (groove) on the front
    dx0 = (S - DISP[0]) / 2
    dy0 = Y0S + (S - DISP[1]) / 2
    body = body - groove(dx0, dy0, dx0 + DISP[0], dy0 + DISP[1], zf, 0.5)
    # pivot: M4 through, nut pocket from the front (mock-up only: the real pivot must stay blind, the display covers it)
    body = body - Pos(P[0], P[1], (Z_SB + zf) / 2) * Cylinder(M4_HOLE / 2, SC_T + 0.2)
    body = body - Pos(P[0], P[1], zf - 1.75) * extrude(RegularPolygon((M4_NUT_AF + 0.3) / math.sqrt(3), 6), 3.6)
    # ports and buttons (1 mm markers), from Board A positions (mechanical_inputs.md)
    ztop = ZA + 1.2
    for xb in (62.33, 80.53):                                   # USB-A J401 / J402, cut-out 14.4 wide
        body = body - side_marker('top', XA0 - xb, ztop + (4.33 - 2.89) / 2, 14.4, 7.2)
    body = body - side_marker('right', YA0 + 12.5, ztop + 1.63, 9.4, 3.6)          # USB-C J101
    body = body - side_marker('left', YA0 + 14.75, ztop + 0.8, 12.3, 1.6)          # nano-SIM J502
    body = body - side_marker('left', YA0 + 30.0, ztop + 1.0, 13.8, 2.0)           # microSD J901
    for yb in (41.5, 48.0, 54.5):                               # POWER, VOL+, VOL-
        body = body - side_marker('left', YA0 + yb, ztop + 1.65, 4.0, 2.4)
    return body


def keyboard_half():
    body = box(0, 0, 0, S, S, KB_T)
    body = body - prism(channel_poly(), KB_T - BUMP_D - CHANNEL_CLR, KB_T + 0.1)
    body = body - groove(XB0, 1.5, XB0 + 74.0, 1.5 + 53.1, KB_T, 0.5)
    body = body - Pos(P[0], P[1], KB_T / 2) * Cylinder(M4_HOLE / 2, KB_T + 0.2)
    body = body - Pos(P[0], P[1], M4_HEAD_T / 2) * Cylinder(M4_HEAD_D / 2 + 0.6, M4_HEAD_T + 0.02)
    return body


def components():
    """everything inside, open position; returns {name: (list of shapes, colour, half)}"""
    c = {}
    c['board_a'] = (board_a(), (40, 120, 60), 'screen')
    c['board_b'] = (board_b(), (40, 120, 60), 'keyboard')
    bx0, by0 = (S - BATT[0]) / 2, 1.5
    c['battery'] = ([box(bx0, by0, BACK, bx0 + BATT[0], by0 + BATT[1], BACK + BATT[2])], (70, 110, 200), 'keyboard')
    c['keyboard'] = ([box(XB0, 1.5, KB_T - KBD_H, XB0 + 74.0, 1.5 + 53.1, KB_T)], (60, 60, 60), 'keyboard')
    dx0, dy0 = (S - DISP[0]) / 2, Y0S + (S - DISP[1]) / 2
    zf = Z_SB + SC_T
    c['display'] = ([box(dx0, dy0, zf - DISP[2], dx0 + DISP[0], dy0 + DISP[1], zf)], (20, 20, 30), 'screen')
    x0, y0, x1, y1 = BUMP
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    zl = Z_SB - BUMP_D + 1.0
    cam = [box(cx - 4.25, cy - 4.25, zl, cx + 4.25, cy + 4.25, zl + 6.38),
           box(cx - CAM / 2, cy - CAM / 2, zl + 6.38, cx + CAM / 2, cy + CAM / 2, zl + 7.98),
           box(cx - CAM / 2 + 2, cy - CAM / 2 + 2, zl + 7.98, cx + CAM / 2 - 2, cy + CAM / 2 - 2, zl + 9.48)]
    c['camera'] = (cam, (200, 160, 40), 'screen')
    c['pivot'] = ([Pos(P[0], P[1], (Z_SB + SC_T) / 2) * Cylinder(2.0, Z_SB + SC_T)], (150, 150, 160), 'fixed')
    return c


def turn_closed(shape):
    return shape.rotate(Axis((P[0], P[1], 0), (0, 0, 1)), 90)


# ---------------- simple z-buffer renderer ----------------
def tess(shape, tol=0.08):
    v, t = shape.tessellate(tol, 0.3)
    return np.array([(p.X, p.Y, p.Z) for p in v], float), np.array(t, int)


def render(items, az, el, out, W=1100, H=850, title=''):
    """items: list of (shape, rgb). az: degrees about z (0 = from the front), el: degrees above the horizon."""
    # az = el = 0 is the front view (looking along -z, y up). az turns the device about the vertical (y) axis:
    # negative shows the right side; el tilts the top toward the viewer.
    a, e = math.radians(az), math.radians(el)
    rx = np.array([[1, 0, 0], [0, math.cos(e), -math.sin(e)], [0, math.sin(e), math.cos(e)]])
    ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    M = rx @ ry
    tris_all, cols, ids = [], [], []
    for k, (shp, rgb) in enumerate(items):
        v, t = tess(shp)
        if len(t) == 0:
            continue
        vc = v @ M.T
        tris_all.append(vc[t])
        cols.append(np.repeat([rgb], len(t), axis=0))
        ids.append(np.full(len(t), k))
    T = np.concatenate(tris_all)
    C = np.concatenate(cols).astype(float)
    I = np.concatenate(ids)
    mn, mx = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
    pad = 30
    sc = min((W - 2 * pad) / (mx[0] - mn[0]), (H - 2 * pad - 30) / (mx[1] - mn[1]))
    X = (T[:, :, 0] - mn[0]) * sc + (W - (mx[0] - mn[0]) * sc) / 2
    Y = (mx[1] - T[:, :, 1]) * sc + pad
    Z = T[:, :, 2]
    zb = np.full((H, W), -np.inf)
    img = np.full((H, W, 3), 250.0)
    idb = np.full((H, W), -1)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    L = np.array([-0.4, 0.6, 0.7]); L /= np.linalg.norm(L)
    shade = 0.45 + 0.55 * np.abs(n @ L)
    for k in range(len(T)):
        xs, ys, zs = X[k], Y[k], Z[k]
        x0, x1 = int(max(0, math.floor(xs.min()))), int(min(W - 1, math.ceil(xs.max())))
        y0, y1 = int(max(0, math.floor(ys.min()))), int(min(H - 1, math.ceil(ys.max())))
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-9:
            continue
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not m.any():
            continue
        z = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        upd = m & (z > sub)
        sub[upd] = z[upd]
        img[y0:y1 + 1, x0:x1 + 1][upd] = C[k] * shade[k]
        idb[y0:y1 + 1, x0:x1 + 1][upd] = I[k]
    # outlines where the part changes or the depth jumps
    edge = np.zeros((H, W), bool)
    edge[:, 1:] |= idb[:, 1:] != idb[:, :-1]
    edge[1:, :] |= idb[1:, :] != idb[:-1, :]
    zz = np.where(np.isfinite(zb), zb, -1e6)
    edge[:, 1:] |= np.abs(zz[:, 1:] - zz[:, :-1]) > 1.5
    edge[1:, :] |= np.abs(zz[1:, :] - zz[:-1, :]) > 1.5
    img[edge] = img[edge] * 0.35
    im = Image.fromarray(img.clip(0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)
    dr.text((12, H - 22), title, fill=(0, 0, 0))
    im.save(out)


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    sh, kb = screen_half(), keyboard_half()
    comp = components()
    # report
    ch = channel_poly()
    print('channel in keyboard half: bounds', [round(v, 1) for v in ch.bounds], 'area %.0f mm2' % ch.area)
    bb_open = Compound([sh, kb]).bounding_box()
    bb_closed = Compound([turn_closed(sh), kb]).bounding_box()
    for nm, bb in (('open', bb_open), ('closed', bb_closed)):
        print(f'{nm}: x {bb.min.X:.1f}..{bb.max.X:.1f}  y {bb.min.Y:.1f}..{bb.max.Y:.1f}  z {bb.min.Z:.1f}..{bb.max.Z:.1f}'
              f'  ->  {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm')
    # clearance checks: components inside their halves' envelopes, bump vs keyboard half when closed
    bump_closed = turn_closed(box(BUMP[0], BUMP[1], Z_SB - BUMP_D, BUMP[2], BUMP[3], Z_SB))
    print('closed bump vs keyboard half (should be 0): %.3f mm3' % (bump_closed & kb).volume)
    ba = Compound(comp['board_a'][0])
    print('Board A envelope z %.2f..%.2f (screen half %.2f..%.2f)' % (ba.bounding_box().min.Z, ba.bounding_box().max.Z, Z_SB, Z_SB + SC_T))
    cam = Compound(comp['camera'][0])
    print('camera vs Board A parts (should be 0): %.3f mm3' % sum((cam & s).volume for s in comp['board_a'][0]))
    disp = comp['display'][0][0]
    print('display vs Board A parts (should be 0): %.3f mm3' % sum((disp & s).volume for s in comp['board_a'][0]))
    bb_b = Compound(comp['board_b'][0]).bounding_box()
    print('Board B envelope z %.2f..%.2f; battery top %.2f' % (bb_b.min.Z, bb_b.max.Z, BACK + BATT[2]))
    # 3D files
    def assembly(closed):
        f = turn_closed if closed else (lambda s: s)
        kids = []
        s2 = f(sh); s2.label, s2.color = 'screen half (block)', Color(0.85, 0.85, 0.88, 0.6); kids.append(s2)
        k2 = kb.moved(Location()); k2.label, k2.color = 'keyboard half (block)', Color(0.75, 0.75, 0.78, 0.6); kids.append(k2)
        for nm, (shapes, rgb, half) in comp.items():
            cc = Compound([f(s) if half == 'screen' else s for s in shapes])
            cc.label, cc.color = nm, Color(*[v / 255 for v in rgb])
            kids.append(cc)
        return Compound(children=kids, label='cm5-handheld swivel block model')
    export_step(assembly(False), os.path.join(out, 'enclosure_open.step'))
    export_step(assembly(True), os.path.join(out, 'enclosure_closed.step'))
    # printable mock-ups: screen half front face down, keyboard half back face down
    sh_print = sh.rotate(Axis.X, 180)
    bb = sh_print.bounding_box()
    sh_print = sh_print.moved(Location((-bb.min.X, -bb.min.Y, -bb.min.Z)))
    export_stl(sh_print, os.path.join(out, 'mockup_screen_half.stl'), tolerance=0.02, angular_tolerance=0.1)
    export_stl(kb, os.path.join(out, 'mockup_keyboard_half.stl'), tolerance=0.02, angular_tolerance=0.1)
    print('mock-up volumes: screen half %.0f cm3, keyboard half %.0f cm3' % (sh.volume / 1000, kb.volume / 1000))
    # pictures
    shell_col_s, shell_col_k = (205, 205, 215), (175, 175, 185)
    render([(sh, shell_col_s), (kb, shell_col_k)], -30, 25, os.path.join(out, 'view_open_front.png'),
           title='Open, from the front (block model; grooves mark the display and keyboard, recesses mark ports)')
    render([(turn_closed(sh), shell_col_s), (kb, shell_col_k)], -30, 25, os.path.join(out, 'view_closed_front.png'),
           title='Closed, from the front')
    render([(sh, shell_col_s), (kb, shell_col_k)], 150, 20, os.path.join(out, 'view_open_back.png'),
           title='Open, from the back: rear camera bump on the screen half')
    render([(sh, shell_col_s), (kb, shell_col_k)], -90, 0, os.path.join(out, 'view_open_side.png'),
           title='Open, from the right side')
    inner = [(s, rgb) for nm, (shapes, rgb, half) in comp.items() if nm not in ('display',) for s in shapes]
    render(inner, -30, 25, os.path.join(out, 'view_open_inside.png'),
           title='Open, inside (no shells, no display): Board A, Board B, battery, keyboard, camera, pivot')
    render([(kb, shell_col_k)] + [(s, rgb) for nm, (shapes, rgb, half) in comp.items() if nm == 'pivot' for s in shapes],
           -20, 45, os.path.join(out, 'view_keyboard_half_channel.png'),
           title='Keyboard half: the channel the camera bump turns through (top-left), pivot (right)')
    print('written to', out)


if __name__ == '__main__':
    main()
