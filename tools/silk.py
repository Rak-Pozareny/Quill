#!/usr/bin/env python3
"""Reference designators on the silkscreen where they can be read: each one is moved to a free spot around its part or
hidden where there is none. The board is saved in place.

usage: silk.py BOARD.kicad_pcb

A free spot keeps 0.15 mm from every pad's copper and mask opening (JLCPCB's silkscreen-to-pad minimum), clears every
other silkscreen line, polygon and reference, and stays 0.3 mm inside the board edge. Candidates, in order: where the
reference is now, then centred above, below, left and right of the part's pads and silkscreen, then the four corners,
upright and turned 90 degrees, at 0.1 and 0.6 mm from the part. KiCad's DRC is then run on the saved board; a reference
still in a silkscreen finding is hidden, and the DRC repeated until no reference is in one; where two parts' own
silkscreen drawings overlap, the smaller part's overlapping line is removed. Text size stays as it is
(1.0 mm, 0.15 mm line: JLCPCB's minimum). The references stay on the Fab layers' assembly drawing either way.
"""
import json
import math
import os
import subprocess
import sys
import tempfile

import pcbnew

PAD_GAP, SILK_GAP, EDGE_GAP = 0.15, 0.1, 0.3


def mm(v):
    return pcbnew.ToMM(v)


def box(bb, grow=0.0):
    return (mm(bb.GetX()) - grow, mm(bb.GetY()) - grow, mm(bb.GetRight()) + grow, mm(bb.GetBottom()) + grow)


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def seg_box_dist(p, q, r):
    """distance from segment p-q to rectangle r (0 if they touch)"""
    if r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3] or r[0] <= q[0] <= r[2] and r[1] <= q[1] <= r[3]:
        return 0.0
    n = max(2, int(math.dist(p, q) / 0.05))
    best = 1e9
    for k in range(n + 1):
        x, y = p[0] + (q[0] - p[0]) * k / n, p[1] + (q[1] - p[1]) * k / n
        dx = max(r[0] - x, 0, x - r[2])
        dy = max(r[1] - y, 0, y - r[3])
        best = min(best, math.hypot(dx, dy))
    return best


def obstacles(b, side_layers):
    """per silk layer: pad boxes (copper or mask), silk segments, other silk boxes"""
    silk, cu, mask = side_layers
    pads, segs, boxes = [], [], []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(cu) or p.IsOnLayer(mask):
                pads.append(box(p.GetBoundingBox(), PAD_GAP + 0.05))
        for g in fp.GraphicalItems():
            if g.GetLayer() != silk or not isinstance(g, pcbnew.PCB_SHAPE):
                continue
            if g.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                s, e = g.GetStart(), g.GetEnd()
                segs.append(((mm(s.x), mm(s.y)), (mm(e.x), mm(e.y)), mm(g.GetWidth()) / 2 + SILK_GAP))
            else:
                boxes.append(box(g.GetBoundingBox(), SILK_GAP))
    for d in b.GetDrawings():
        if d.GetLayer() == silk:
            boxes.append(box(d.GetBoundingBox(), SILK_GAP))
    return pads, segs, boxes


def free(r, pads, segs, boxes, refs, edge):
    if not (edge[0] <= r[0] and r[2] <= edge[2] and edge[1] <= r[1] and r[3] <= edge[3]):
        return False
    if any(overlap(r, p) for p in pads) or any(overlap(r, x) for x in boxes) or any(overlap(r, x) for x in refs):
        return False
    return all(seg_box_dist(p, q, r) >= w for p, q, w in segs)


def place(b):
    eb = b.GetBoardEdgesBoundingBox()
    edge = (mm(eb.GetX()) + EDGE_GAP, mm(eb.GetY()) + EDGE_GAP, mm(eb.GetRight()) - EDGE_GAP, mm(eb.GetBottom()) - EDGE_GAP)
    sides = {pcbnew.F_SilkS: (pcbnew.F_SilkS, pcbnew.F_Cu, pcbnew.F_Mask),
             pcbnew.B_SilkS: (pcbnew.B_SilkS, pcbnew.B_Cu, pcbnew.B_Mask)}
    obs = {L: obstacles(b, s) for L, s in sides.items()}
    placed = {L: [] for L in sides}
    moved = hidden = kept = 0
    fps = sorted(b.GetFootprints(), key=lambda f: -len(f.Pads()))      # big parts first: they have the fewest spots
    for fp in fps:
        ref = fp.Reference()
        L = ref.GetLayer()
        if L not in sides or not ref.IsVisible():
            continue
        pads, segs, boxes = obs[L]
        body = None
        for p in fp.Pads():
            body = box(p.GetBoundingBox()) if body is None else \
                (min(body[0], box(p.GetBoundingBox())[0]), min(body[1], box(p.GetBoundingBox())[1]),
                 max(body[2], box(p.GetBoundingBox())[2]), max(body[3], box(p.GetBoundingBox())[3]))
        for g in fp.GraphicalItems():
            if g.GetLayer() == L:
                gb = box(g.GetBoundingBox())
                body = gb if body is None else (min(body[0], gb[0]), min(body[1], gb[1]), max(body[2], gb[2]), max(body[3], gb[3]))
        if body is None:
            continue
        orig_pos, orig_ang = ref.GetPosition(), ref.GetTextAngleDegrees()
        cands = [(orig_pos, orig_ang)]
        cx, cy = (body[0] + body[2]) / 2, (body[1] + body[3]) / 2
        for ang in (0.0, 90.0):
            ref.SetTextAngleDegrees(ang)
            tb = box(ref.GetBoundingBox())
            w, h = tb[2] - tb[0], tb[3] - tb[1]
            for gap in (0.1, 0.6):
                for x, y in ((cx, body[1] - gap - h / 2), (cx, body[3] + gap + h / 2), (body[0] - gap - w / 2, cy),
                             (body[2] + gap + w / 2, cy), (body[0] - gap - w / 2, body[1] - gap - h / 2),
                             (body[2] + gap + w / 2, body[1] - gap - h / 2), (body[0] - gap - w / 2, body[3] + gap + h / 2),
                             (body[2] + gap + w / 2, body[3] + gap + h / 2)):
                    cands.append((pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)), ang))
        done = False
        for k, (pos, ang) in enumerate(cands):
            ref.SetTextAngleDegrees(ang)
            ref.SetPosition(pos)
            tb = box(ref.GetBoundingBox())
            if free(tb, pads, segs, boxes, placed[L], edge):
                placed[L].append(box(ref.GetBoundingBox(), SILK_GAP))
                moved += k > 0
                kept += k == 0
                done = True
                break
        if not done:
            ref.SetTextAngleDegrees(orig_ang)
            ref.SetPosition(orig_pos)
            ref.SetVisible(False)
            hidden += 1
    return moved, kept, hidden


def silk_findings(path):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'drc.json')
        subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all', '-o', out, path],
                       capture_output=True)
        rep = json.load(open(out))
    return [v for v in rep['violations'] if v['type'].startswith('silk')]


def main():
    path = sys.argv[1]
    b = pcbnew.LoadBoard(path)
    moved, kept, hidden = place(b)
    pcbnew.SaveBoard(path, b)
    print(f'references: {kept} kept, {moved} moved, {hidden} hidden (no free spot)')
    for _ in range(5):
        found = silk_findings(path)
        refs = {i['uuid'] for v in found for i in v['items'] if i['description'].startswith('Reference field')}
        if not refs:
            break
        b = pcbnew.LoadBoard(path)
        n = 0
        for fp in b.GetFootprints():
            if fp.Reference().m_Uuid.AsString() in refs and fp.Reference().IsVisible():
                fp.Reference().SetVisible(False)
                n += 1
        if not n:
            break
        pcbnew.SaveBoard(path, b)
        print(f'{n} more hidden after KiCad\'s DRC')
    # two parts' own silkscreen drawings overlapping (a small part placed tight against a big one): the smaller
    # part's overlapping line goes, the bigger part's outline and pin-1 mark stay
    found = silk_findings(path)
    pairs = [v for v in found if v['type'] == 'silk_overlap' and
             not any(i['description'].startswith(('Reference', 'Value')) for i in v['items'])]
    if pairs:
        b = pcbnew.LoadBoard(path)
        owner = {g.m_Uuid.AsString(): (fp, g) for fp in b.GetFootprints() for g in fp.GraphicalItems()}
        gone = 0
        for v in pairs:
            its = [owner.get(i['uuid']) for i in v['items']]
            if None in its:
                continue
            fp, g = min(its, key=lambda t: len(t[0].Pads()))
            if g.GetParent() is not None:
                fp.Remove(g)
                gone += 1
        pcbnew.SaveBoard(path, b)
        print(f'{gone} small-part silkscreen lines removed where they overlapped a bigger part\'s')
    # an edge-mounted part's own outline running to the board edge (USB sockets, side buttons): the segments too
    # close to the edge go (JLCPCB would trim them there anyway)
    found = silk_findings(path)
    edge = [v for v in found if v['type'] == 'silk_edge_clearance']
    if edge:
        b = pcbnew.LoadBoard(path)
        owner = {g.m_Uuid.AsString(): (fp, g) for fp in b.GetFootprints() for g in fp.GraphicalItems()}
        gone = set()
        for v in edge:
            for i in v['items']:
                t = owner.get(i['uuid'])
                if t and i['uuid'] not in gone:
                    t[0].Remove(t[1])
                    gone.add(i['uuid'])
        pcbnew.SaveBoard(path, b)
        print(f'{len(gone)} edge-mounted parts\' silkscreen lines at the board edge removed')
    found = silk_findings(path)
    print(f'silkscreen findings left: {len(found)}')
    for v in found:
        print('  ', v['type'], [i['description'][:60] for i in v['items']])


if __name__ == '__main__':
    main()
