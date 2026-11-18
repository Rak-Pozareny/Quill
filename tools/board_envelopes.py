#!/usr/bin/env python3
"""Export a board's mechanical envelope for the enclosure model: outline (with cut-outs and holes), thickness, and one
box per footprint (courtyard extent, else pad extent; height from tools/heights.py, i.e. the datasheet or the KiCad
STEP model).

usage: board_envelopes.py BOARD.kicad_pcb OUT.json

Coordinates are board coordinates: mm, origin at the board's top-left corner (KiCad + 100 subtracted from the outline's
bounding box origin), x right, y down, seen from the top face. z = 0 is the bottom face, the top face is at the
board thickness. Each part: side 'T' (above the top face) or 'B' (below the bottom face), x0 x1 y0 y1, h (height
away from its face), sink (how far a top part reaches below the top face, e.g. USB-A in its cut-out), src.
Parts whose height is unknown get h = null and are listed in 'unknown'.
"""
import json
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heights  # noqa: E402


def mm(v):
    return round(pcbnew.ToMM(v), 3)


def main():
    path, out = sys.argv[1:3]
    b = pcbnew.LoadBoard(path)
    th = pcbnew.ToMM(b.GetDesignSettings().GetBoardThickness())
    bb = b.GetBoardEdgesBoundingBox()
    w = b.GetDesignSettings().GetLineThickness(pcbnew.Edge_Cuts)
    ox, oy = pcbnew.ToMM(bb.GetX() + w // 2), pcbnew.ToMM(bb.GetY() + w // 2)
    ps = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(ps, True)
    outline = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        pts = [(round(pcbnew.ToMM(o.CPoint(k).x) - ox, 3), round(pcbnew.ToMM(o.CPoint(k).y) - oy, 3)) for k in range(o.PointCount())]
        holes = []
        for j in range(ps.HoleCount(i)):
            hh = ps.Hole(i, j)
            holes.append([(round(pcbnew.ToMM(hh.CPoint(k).x) - ox, 3), round(pcbnew.ToMM(hh.CPoint(k).y) - oy, 3)) for k in range(hh.PointCount())])
        outline.append({'outer': pts, 'holes': holes})
    drills = []
    parts, unknown = [], []
    for fp in b.GetFootprints():
        side = 'B' if fp.IsFlipped() else 'T'
        for p in fp.Pads():
            if p.GetDrillSize().x > 0:
                q = p.GetPosition()
                drills.append({'ref': fp.GetReference(), 'x': round(pcbnew.ToMM(q.x) - ox, 3), 'y': round(pcbnew.ToMM(q.y) - oy, 3),
                               'd': mm(p.GetDrillSize().x), 'plated': p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH})
        cy = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
        if cy.OutlineCount():
            c = cy.BBox()
            x0, x1, y0, y1 = mm(c.GetX()) - ox, mm(c.GetRight()) - ox, mm(c.GetY()) - oy, mm(c.GetBottom()) - oy
        else:
            pads = [p for p in fp.Pads()]
            if not pads:
                continue
            xs, ys = [], []
            for p in pads:
                r = p.GetBoundingBox()
                xs += [mm(r.GetX()), mm(r.GetRight())]
                ys += [mm(r.GetY()), mm(r.GetBottom())]
            x0, x1, y0, y1 = min(xs) - ox, max(xs) - ox, min(ys) - oy, max(ys) - oy
        h, below, src = heights.height_of(fp)
        rec = {'ref': fp.GetReference(), 'value': fp.GetValue(), 'side': side, 'x0': round(x0, 3), 'x1': round(x1, 3),
               'y0': round(y0, 3), 'y1': round(y1, 3), 'h': h, 'sink': below, 'src': src}
        if h is None:
            unknown.append(fp.GetReference())
        parts.append(rec)
    json.dump({'board': os.path.basename(path), 'thickness': th, 'outline': outline, 'drills': drills, 'parts': parts,
               'unknown': unknown}, open(out, 'w'), indent=1)
    print(f'{path}: {len(parts)} parts, {len(drills)} drilled pads, {len(outline)} outline(s); thickness {th}; unknown heights: {unknown}')


if __name__ == '__main__':
    main()
