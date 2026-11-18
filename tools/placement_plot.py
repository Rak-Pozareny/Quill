#!/usr/bin/env python3
"""Placement plot: courtyards (with openings), pads coloured by net class, reference designators.

usage: placement_plot.py BOARD.kicad_pcb F|B OUT.png [x0 y0 x1 y1] [px_per_mm]
Board coordinates (origin top-left of the board, the files have it at +100/+100), always seen from the top: the
bottom side is drawn see-through, not mirrored, so it lines up with the top plot. Parts on the other side are faint.
Pads: red = switch nodes, orange = power rails, green = GND, blue = signals.
"""
import html
import os
import subprocess
import sys

import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gen'))
from sexpr import parse  # noqa: E402
b = pcbnew.LoadBoard(sys.argv[1])
side, out = sys.argv[2], sys.argv[3]
win = list(map(float, sys.argv[4:8])) if len(sys.argv) >= 8 else [-1, -1, 96, 66]
k = float(sys.argv[8]) if len(sys.argv) >= 9 else 20
O = 100
def mm(v): return pcbnew.ToMM(v)
X = lambda x: (x - O - win[0]) * k
Y = lambda y: (y - O - win[1]) * k
W, H = (win[2] - win[0]) * k, (win[3] - win[1]) * k
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}"><rect width="100%" height="100%" fill="white"/>']
# Edge.Cuts from the file (pcbnew's drawing iterators crash under Python 3.14)
for g in parse(open(sys.argv[1]).read())[0][1:]:
    if not (isinstance(g, list) and g and g[0] in ('gr_line', 'gr_arc', 'gr_circle')):
        continue
    if ['layer', 'Edge.Cuts'] not in [[str(v) for v in x] for x in g if isinstance(x, list) and x[0] == 'layer']:
        continue
    pt = {str(x[0]): (float(x[1]), float(x[2])) for x in g if isinstance(x, list) and x[0] in ('start', 'mid', 'end', 'center')}
    if g[0] == 'gr_line':
        (ax, ay), (bx, by) = pt['start'], pt['end']
        s.append(f'<line x1="{X(ax)}" y1="{Y(ay)}" x2="{X(bx)}" y2="{Y(by)}" stroke="black" stroke-width="2"/>')
    elif g[0] == 'gr_arc':
        (ax, ay), (mx, my), (bx, by) = pt['start'], pt['mid'], pt['end']
        d = 2 * (ax * (my - by) + mx * (by - ay) + bx * (ay - my))
        ux = ((ax**2 + ay**2) * (my - by) + (mx**2 + my**2) * (by - ay) + (bx**2 + by**2) * (ay - my)) / d
        uy = ((ax**2 + ay**2) * (bx - mx) + (mx**2 + my**2) * (ax - bx) + (bx**2 + by**2) * (mx - ax)) / d
        r = ((ax - ux) ** 2 + (ay - uy) ** 2) ** 0.5
        sweep = 1 if (mx - ax) * (by - ay) - (my - ay) * (bx - ax) > 0 else 0     # y down: >0 = clockwise on screen
        s.append(f'<path d="M {X(ax)} {Y(ay)} A {r * k} {r * k} 0 0 {sweep} {X(bx)} {Y(by)}" fill="none" '
                 f'stroke="black" stroke-width="2"/>')
    else:
        (cx, cy), (ex, ey) = pt['center'], pt['end']
        r = ((ex - cx) ** 2 + (ey - cy) ** 2) ** 0.5
        s.append(f'<circle cx="{X(cx)}" cy="{Y(cy)}" r="{r * k}" fill="none" stroke="black" stroke-width="2"/>')
def col(n):
    if n == 'GND': return '#4a8'
    if any(t in n for t in ('_SW', '_L1', '_L2', 'VLX', 'SW1', 'SW2', 'BL_SW')): return '#e33'
    if any(t in n for t in ('VSYS', 'VCC', 'VBUS', 'BAT_P', 'CHG_IN', 'CM5_VIN', '5V', '3V3', '1V8', 'VDD', 'LEDA')): return '#e90'
    return '#68c'
for f in b.GetFootprints():
    fs = 'B' if f.IsFlipped() else 'F'
    mine = fs == side
    op = 1.0 if mine else 0.18
    lay = pcbnew.B_CrtYd if fs == 'B' else pcbnew.F_CrtYd
    f.BuildCourtyardCaches()
    poly = f.GetCourtyard(lay)
    for i in range(poly.OutlineCount()):
        o = poly.Outline(i)
        pts = ' '.join(f'{X(mm(o.CPoint(j).x)):.1f},{Y(mm(o.CPoint(j).y)):.1f}' for j in range(o.PointCount()))
        s.append(f'<polygon points="{pts}" fill="none" stroke="#0aa" stroke-width="1" opacity="{op}"/>')
        for h in range(poly.HoleCount(i)):
            o = poly.Hole(i, h)
            pts = ' '.join(f'{X(mm(o.CPoint(j).x)):.1f},{Y(mm(o.CPoint(j).y)):.1f}' for j in range(o.PointCount()))
            s.append(f'<polygon points="{pts}" fill="none" stroke="#0aa" stroke-dasharray="3,2" stroke-width="1" opacity="{op}"/>')
    for p in f.Pads():
        on = p.IsOnLayer(pcbnew.B_Cu if side == 'B' else pcbnew.F_Cu)
        if not on and mine: continue
        bb = p.GetBoundingBox()
        po = 1.0 if (mine or (on and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH)) else 0.15
        s.append(f'<rect x="{X(mm(bb.GetX()))}" y="{Y(mm(bb.GetY()))}" width="{mm(bb.GetWidth())*k}" height="{mm(bb.GetHeight())*k}" fill="{col(p.GetNetname().split("/")[-1])}" opacity="{po*0.8}"/>')
    if mine:
        c = f.GetPosition()
        s.append(f'<text x="{X(mm(c.x))}" y="{Y(mm(c.y))}" font-size="{max(7, k*0.55):.0f}" text-anchor="middle" dominant-baseline="middle" font-family="sans-serif" font-weight="bold" fill="black">{html.escape(f.GetReference())}</text>')
s.append('</svg>')
subprocess.run(['rsvg-convert', '-o', out], input='\n'.join(s).encode(), check=True)
