#!/usr/bin/env python3
"""Length-matching report for the high-speed nets of a routed board.

usage: length_report.py BOARD.kicad_pcb [OUT.md]

For each differential pair: routed length of P and N as KiCad's DRC counts it (gen/route_tune.length: tracks, the
copper inside vias and pads counted from their centres, via heights from the board's stack-up), intra-pair skew, and how much of the pair runs coupled at its impedance gap (segments of P
and N on the same layer, parallel, at the class gap +- 0.02 mm). For each matched group (MIPI DSI, CSI-A, CSI-B):
every lane against the clock lane. Targets and their sources: research/length_targets.md (TI SPRAAR7J for PCIe,
USB 3 and USB 2.0, the Raspberry Pi CM4 datasheet for MIPI, AMD UG863 for the lane-to-clock budget).
"""
import math
import os
import re
import sys

import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gen'))
from route_rules import GEOM, classify  # noqa: E402
from route_tune import length as net_length  # noqa: E402
PS_PER_MM = 7.0          # stripline in Er 4.4: sqrt(4.4) / c (outer layers are faster: an upper bound)


def intra_target(name, cls):
    """(limit mm, source) for the P/N skew of a pair"""
    if cls == 'PCIE85' or name.endswith('REFCLK'):
        return 0.127, 'TI SPRAAR7J (5 mil)'
    if name.startswith('USB3'):
        return 0.127, 'TI SPRAAR7J (5 mil)'
    if cls == 'USB90':
        return 1.27, 'TI SPRAAR7J (50 mil, USB 2.0)'
    return 0.15, 'RPi CM4 datasheet'


# MIPI lanes against their clock: +-1.0 mm (7 ps) is our own board allowance, a quarter of AMD UG863's 0.075 UI at
# 2.5 Gbps (+-30 ps); the rest is left for the CM5 module's own lane skew (not published) and the FPC
GROUPS = [('MIPI DSI', r'^DSI_', 'DSI_CLK', 1.0), ('MIPI CSI-A (rear camera)', r'^CSIA_', 'CSIA_CLK', 1.0),
          ('MIPI CSI-B (front camera)', r'^CSIB_', 'CSIB_CLK', 1.0)]


def tracks(board):
    ts = board.Tracks()
    return [ts[i].Cast() for i in range(len(ts))]


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    out = open(sys.argv[2], 'w') if len(sys.argv) > 2 else sys.stdout
    segs, length, vias = {}, {}, {}
    for t in tracks(b):
        n = t.GetNetname().split('/')[-1]
        if isinstance(t, pcbnew.PCB_VIA):
            vias.setdefault(n, []).append(t)
            continue
        segs.setdefault(n, []).append(t)
        length[n] = length.get(n, 0.0) + pcbnew.ToMM(t.GetLength())
    code = {t.GetNetname().split('/')[-1]: t.GetNetCode() for t in tracks(b)}
    pairs = []
    names = sorted(length)
    for n in names:
        m = re.match(r'^(.*?)(_P|DP)$', n)
        if not m:
            continue
        nn = m.group(1) + ('_N' if m.group(2) == '_P' else 'DN')
        if nn not in length:
            continue
        cls = classify(n)
        if cls not in ('MIPI100', 'PCIE85', 'USB90'):
            continue
        lp, ln = net_length(b, code[n]), net_length(b, code[nn])
        coupled = coupled_length(segs[n], segs[nn], cls)
        pairs.append((m.group(1).rstrip('_'), cls, lp, ln, coupled, len(vias.get(n, [])), len(vias.get(nn, []))))
    w = out.write
    w('| Pair | Class | P (mm) | N (mm) | Skew (mm) | Skew (ps) | Target (mm) | Source | Coupled (mm) | Vias P/N '
      '| Result |\n')
    w('|---|---|---|---|---|---|---|---|---|---|---|\n')
    bad = 0
    for name, cls, lp, ln, cp, vp, vn in pairs:
        lim, src = intra_target(name, cls)
        ok = abs(lp - ln) <= lim
        bad += not ok
        w(f'| {name} | {cls} | {lp:.2f} | {ln:.2f} | {lp - ln:+.3f} | {(lp - ln) * PS_PER_MM:+.1f} | <= {lim} | {src} '
          f'| {cp:.1f} | {vp}/{vn} | {"OK" if ok else "**OUT**"} |\n')
    w('\n')
    for title, rx, clk, lim in GROUPS:
        g = [p for p in pairs if re.match(rx, p[0] + '_')]
        ref = [p for p in g if p[0] == clk]
        if not ref:
            continue
        rl = (ref[0][2] + ref[0][3]) / 2
        w(f'**{title}** (lanes against {clk}, {rl:.2f} mm; target +-{lim} mm)\n\n'
          '| Lane | Length (mm) | vs clock (mm) | vs clock (ps) | Result |\n|---|---|---|---|---|\n')
        for p in g:
            L = (p[2] + p[3]) / 2
            ok = abs(L - rl) <= lim
            bad += not ok
            w(f'| {p[0]} | {L:.2f} | {L - rl:+.2f} | {(L - rl) * PS_PER_MM:+.1f} | {"OK" if ok else "**OUT**"} |\n')
        w('\n')
    w(f'{len(pairs)} pairs, {bad} out of target\n')


def coupled_length(sp, sn, cls):
    """length of P segments that have a parallel N segment on the same layer at the class gap (+-0.02 mm)"""
    tot = 0.0
    for a in sp:
        L = a.GetLayer()
        g = GEOM[cls]['out' if L in (pcbnew.F_Cu, pcbnew.B_Cu) else 'inn']
        pitch = g[0] + g[1]
        ax, ay = pcbnew.ToMM(a.GetStart().x), pcbnew.ToMM(a.GetStart().y)
        bx, by = pcbnew.ToMM(a.GetEnd().x), pcbnew.ToMM(a.GetEnd().y)
        la = math.hypot(bx - ax, by - ay)
        if la < 1e-6:
            continue
        ux, uy = (bx - ax) / la, (by - ay) / la
        for c in sn:
            if c.GetLayer() != L:
                continue
            cx, cy = pcbnew.ToMM(c.GetStart().x), pcbnew.ToMM(c.GetStart().y)
            dx, dy = pcbnew.ToMM(c.GetEnd().x), pcbnew.ToMM(c.GetEnd().y)
            lc = math.hypot(dx - cx, dy - cy)
            if lc < 1e-6 or abs(abs((dx - cx) / lc * ux + (dy - cy) / lc * uy) - 1) > 1e-3:
                continue
            dist = abs((cx - ax) * uy - (cy - ay) * ux)
            if abs(dist - pitch) > 0.02:
                continue
            t0, t1 = sorted(((cx - ax) * ux + (cy - ay) * uy, (dx - ax) * ux + (dy - ay) * uy))
            tot += max(0.0, min(la, t1) - max(0.0, t0))
    return tot


if __name__ == '__main__':
    main()
