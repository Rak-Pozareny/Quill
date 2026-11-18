#!/usr/bin/env python3
"""Board A artwork: the check-on-a-cube logo on the top silkscreen and a line of text on the bottom silkscreen.
The board is saved in place; tools/package.py runs this before the silkscreen references are placed.

usage: art_a.py BOARD.kicad_pcb

Logo: gen/data/art/logo_check_cube.png (500 x 500, transparent background) turned into white silkscreen. The green
check and the purple cube are told apart by colour; the cube is cut into its three faces along its edges (vertices
read off the image). The check, the top face and the front face are filled, the dark side face is an outline, with
0.2 mm gaps between them. 7 mm tall, at the left edge between the camera connectors J704 / J705: the largest spot on
either side that is clear of parts, pads and other silkscreen and not under the CM5 module or the M.2 card. Copper
there carries tracks, so the check could not be exposed gold.
Text: white silkscreen on the bottom (B.SilkS, mirrored to read from below), two lines at 1.5 mm: the largest
block that fits on either side clear of pads (0.2 mm), holes, other silkscreen (0.1 mm), the board edge (0.3 mm) and
every courtyard on that side, at the right edge behind J502 / J901 (D121; the top has no such spot left). Until
2026-11-11 it was hidden copper text on B.Cu (D106).
Re-running replaces the items of the group "artwork".
"""
import os
import sys

import pcbnew
from PIL import Image, ImageChops, ImageFilter

import proute as R

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
LOGO = os.path.join(ROOT, 'gen', 'data', 'art', 'logo_check_cube.png')
LOGO_AT, LOGO_H = (109.4, 141.5), 7.0          # centre and height on the board, mm
TEXT = 'I love\nyou :)'                        # D121 (was 'Beetroot on pizza / should be legal', D106)
TEXT_AT, TEXT_SIZE, TEXT_LINE = (188.40, 125.15), 1.5, 0.2      # block centre (free range x 187.65-189.15, y 124.67-125.62)
GAP = 0.2                                       # between the logo's parts, and the side face's outline width, mm
# the cube's edges in image pixels: left vertex, top-front vertex, right vertex, bottom vertex
LV, TF, RV, BV = (106, 252), (240, 315), (380, 262), (238, 470)


def _mask(im, fn):
    w, h = im.size
    px = im.load()
    m = Image.new('L', (w, h), 0)
    mp = m.load()
    for y in range(h):
        for x in range(w):
            if fn(*px[x, y]):
                mp[x, y] = 255
    return m


def _grow(m, r):
    return m.filter(ImageFilter.MaxFilter(2 * r + 1))


def _shrink(m, r):
    return m.filter(ImageFilter.MinFilter(2 * r + 1))


def logo_mask():
    """(white mask, its bounding box in pixels, mm per pixel)"""
    im = Image.open(LOGO).convert('RGBA')
    w, h = im.size
    green = _mask(im, lambda r, g, b, a: a >= 128 and g > r + 30 and g > b + 30)
    green = _shrink(_grow(green, 2), 2)                     # close the highlight seams on the check
    opaque = _mask(im, lambda r, g, b, a: a >= 128)
    check = ImageChops.multiply(green, opaque).filter(ImageFilter.MedianFilter(5))
    cube = ImageChops.subtract(opaque, check).filter(ImageFilter.MedianFilter(5))
    bbox = opaque.getbbox()
    scale = LOGO_H / (bbox[3] - bbox[1])
    gap = max(1, round(GAP / scale / 2))

    def above(p, q, x, y):
        return y < p[1] + (x - p[0]) / (q[0] - p[0]) * (q[1] - p[1])

    faces = {k: Image.new('L', (w, h), 0) for k in ('top', 'front', 'side')}
    fp = {k: v.load() for k, v in faces.items()}
    cp = cube.load()
    for y in range(h):
        for x in range(w):
            if not cp[x, y]:
                continue
            if above(LV, TF, x, y) if x < TF[0] else above(TF, RV, x, y):
                fp['top'][x, y] = 255
            elif x < TF[0] + (BV[0] - TF[0]) * (y - TF[1]) / (BV[1] - TF[1]):
                fp['front'][x, y] = 255
            else:
                fp['side'][x, y] = 255
    parts = {'check': check, **faces}
    cut = {}
    for k, m in parts.items():
        others = Image.new('L', (w, h), 0)
        for k2, m2 in parts.items():
            if k2 != k:
                others = ImageChops.lighter(others, m2)
        cut[k] = ImageChops.subtract(m, _grow(others, gap))
    outline = ImageChops.subtract(cut['side'], _shrink(cut['side'], 2 * gap))
    white = cut['check']
    for m in (cut['top'], cut['front'], outline):
        white = ImageChops.lighter(white, m)
    return white, bbox, scale


def mask_polys(mask, bbox, scale, centre):
    """the mask's pixels as a fractured SHAPE_POLY_SET centred on centre (mm)"""
    x0 = centre[0] - (bbox[2] - bbox[0]) * scale / 2
    y0 = centre[1] - (bbox[3] - bbox[1]) * scale / 2
    nm = lambda v: pcbnew.FromMM(v)
    ps = pcbnew.SHAPE_POLY_SET()
    mp = mask.load()
    for y in range(bbox[1], bbox[3]):
        x = bbox[0]
        while x < bbox[2]:
            if not mp[x, y]:
                x += 1
                continue
            s = x
            while x < bbox[2] and mp[x, y]:
                x += 1
            ax, bx = nm(x0 + (s - bbox[0]) * scale), nm(x0 + (x - bbox[0]) * scale)
            ay, by = nm(y0 + (y - bbox[1]) * scale), nm(y0 + (y + 1 - bbox[1]) * scale) + 1000   # rows overlap 1 um
            ch = pcbnew.SHAPE_LINE_CHAIN()
            for px, py in ((ax, ay), (bx, ay), (bx, by), (ax, by)):
                ch.Append(px, py)
            ch.SetClosed(True)
            ps.AddOutline(ch)
    ps.Simplify()
    ps.SimplifyOutlines(pcbnew.FromMM(0.005))
    ps.Fracture()
    return ps


def main():
    path = sys.argv[1]
    b = pcbnew.LoadBoard(path)
    for g in list(b.Groups()):
        if g.GetName() == 'artwork':
            for it in list(g.GetItems()):
                R.remove(b, it.Cast())
            R.remove(b, g)
    grp = pcbnew.PCB_GROUP(b)
    grp.SetName('artwork')
    b.Add(grp)

    mask, bbox, scale = logo_mask()
    ps = mask_polys(mask, bbox, scale, LOGO_AT)
    for k in range(ps.OutlineCount()):
        one = pcbnew.SHAPE_POLY_SET()
        one.AddOutline(ps.Outline(k))
        sh = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_POLY)
        sh.SetPolyShape(one)
        sh.SetFilled(True)
        sh.SetWidth(0)
        sh.SetLayer(pcbnew.F_SilkS)
        b.Add(sh)
        grp.AddItem(sh)

    t = pcbnew.PCB_TEXT(b)
    t.SetText(TEXT)
    t.SetLayer(pcbnew.B_SilkS)
    t.SetMirrored(True)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(TEXT_SIZE), pcbnew.FromMM(TEXT_SIZE)))
    t.SetTextThickness(pcbnew.FromMM(TEXT_LINE))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(TEXT_AT[0]), pcbnew.FromMM(TEXT_AT[1])))
    b.Add(t)
    grp.AddItem(t)
    # the block centred on TEXT_AT (multi-line text is anchored by its first line)
    c = t.GetBoundingBox().Centre()
    t.Move(pcbnew.VECTOR2I(pcbnew.FromMM(TEXT_AT[0]) - c.x, pcbnew.FromMM(TEXT_AT[1]) - c.y))
    kb = t.GetBoundingBox()

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(path, b)
    print(f'artwork: logo {ps.OutlineCount()} polygons on F.SilkS, {(bbox[2] - bbox[0]) * scale:.2f} x '
          f'{LOGO_H:.2f} mm at {LOGO_AT}; text on B.SilkS at {TEXT_AT} '
          f'({pcbnew.ToMM(kb.GetWidth()):.2f} x {pcbnew.ToMM(kb.GetHeight()):.2f} mm, centre '
          f'({pcbnew.ToMM(kb.Centre().x):.2f}, {pcbnew.ToMM(kb.Centre().y):.2f})); saved {path}')


if __name__ == '__main__':
    main()
