#!/usr/bin/env python3
"""D118 stage 1 on a routed board A: J701 / J702 pad nets from the netlist (panel pins mirrored), J702 / SW304 / TP305
moved, the CHG_IN trunk's top-layer run past J702 re-laid, every net of the display connectors' signals ripped, and
other copper that now collides with the moved or renamed pads removed; then what is left dangling.

usage: stage1.py BOARD.kicad_pcb NETFILE
"""
import math
import os
import re
import sys

import pcbnew

GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gen')
sys.path.insert(0, GEN)
import gndfix  # noqa: E402
import proute as R  # noqa: E402

O = 100.0
MOVES = {'J702': (55.0, 43.85), 'SW304': (57.2, 36.25), 'TP305': (54.75, 49.75)}   # board mm; orientation kept
RIP_NETS = ['DSI_CLK_P', 'DSI_CLK_N', 'DSI_D0_P', 'DSI_D0_N', 'DSI_D1_P', 'DSI_D1_N', 'DSI_D2_P', 'DSI_D2_N',
            'DSI_D3_P', 'DSI_D3_N', 'BL_LEDA', 'BL_LEDK', 'LCD_IOVCC', 'LCD_RESET_N', 'LCD_VCI', 'TP_INT', 'TP_RST_N']
# CHG_IN on F.Cu, 1.2 mm: the old run along y 45.26 / 45.86 crosses J702's new pads 1-3; the new one passes below the
# pad column (y 46.55) and between pad 1 and the lower mounting tab on a 45-degree line to the via cluster at y 45.26
CHG_OLD = [((57.88, 45.26), (55.78, 45.26)), ((55.78, 45.26), (55.18, 45.86)), ((55.18, 45.86), (43.57, 45.86))]
CHG_NEW = [(43.57, 45.86), (44.26, 46.55), (56.05, 46.55), (57.34, 45.26), (58.43, 45.26)]
CHG_W = 1.2
CLR = 0.15          # kept from foreign copper (net classes: 0.10-0.12)
KEEP_DSI_X = 19.6
GND_CLEAR = (51.5, 15.0, 54.4, 26.5)


def full_pin_nets(netfile, refs):
    s = open(netfile).read()
    out = {}
    for blk in re.split(r'\n\t\t\(net\n', s)[1:]:
        name = re.search(r'\(name "([^"]+)"\)', blk).group(1)
        for r, p in re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', blk):
            if r in refs:
                out.setdefault((r, p), name)
    return out


def mm(v):
    return pcbnew.ToMM(v)


def seg_dist(p, q, a, b):
    """distance between segments pq and ab"""
    def pt_seg(c, u, v):
        dx, dy = v[0] - u[0], v[1] - u[1]
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((c[0] - u[0]) * dx + (c[1] - u[1]) * dy) / L2))
        return math.hypot(c[0] - u[0] - t * dx, c[1] - u[1] - t * dy)
    def cross(u, v, w):
        return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    d1, d2, d3, d4 = cross(a, b, p), cross(a, b, q), cross(p, q, a), cross(p, q, b)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(pt_seg(p, a, b), pt_seg(q, a, b), pt_seg(a, p, q), pt_seg(b, p, q))


def rect_seg_dist(r, p, q):
    x0, y0, x1, y1 = r
    if x0 <= p[0] <= x1 and y0 <= p[1] <= y1:
        return 0.0
    edges = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    return min(seg_dist(p, q, a, b) for a, b in edges)


def main():
    path, netfile = sys.argv[1:3]
    b = pcbnew.LoadBoard(path)
    log = lambda m: print(m, flush=True)
    # 1. pad nets
    old_nets = {(r, p.GetNumber()): p.GetNetname() for r in ('J701', 'J702') for p in b.FindFootprintByReference(r).Pads()}
    want = full_pin_nets(netfile, {'J701', 'J702'})
    changed = 0
    for ref in ('J701', 'J702'):
        fp = b.FindFootprintByReference(ref)
        for p in fp.Pads():
            name = want.get((ref, p.GetNumber()))
            if name is None:
                sys.exit(f'{ref}.{p.GetNumber()} not in the netlist')
            net = b.FindNet(name)
            if net is None:
                net = pcbnew.NETINFO_ITEM(b, name)
                b.Add(net)
                log(f'net added: {name}')
            if p.GetNetname() != name:
                p.SetNet(net)
                changed += 1
    log(f'pad nets changed: {changed}')
    # 2. moves
    for ref, (x, y) in MOVES.items():
        fp = b.FindFootprintByReference(ref)
        old = (mm(fp.GetPosition().x) - O, mm(fp.GetPosition().y) - O)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(O + x), pcbnew.FromMM(O + y)))
        log(f'{ref}: ({old[0]:.3f}, {old[1]:.3f}) -> ({x}, {y})')
    # 3. CHG_IN re-laid past J702
    chg = b.FindNet([str(n) for n in R.net_names(b) if str(n).split('/')[-1] == 'CHG_IN'][0])
    gone = 0
    for t in list(R.tracks(b)):
        if t.GetClass() == 'PCB_VIA' or t.GetNetCode() != chg.GetNetCode() or b.GetLayerName(t.GetLayer()) != 'F.Cu':
            continue
        s = (round(mm(t.GetStart().x) - O, 2), round(mm(t.GetStart().y) - O, 2))
        e = (round(mm(t.GetEnd().x) - O, 2), round(mm(t.GetEnd().y) - O, 2))
        if any({s, e} == {u, v} for u, v in CHG_OLD):
            R.remove(b, t)
            gone += 1
    if gone != len(CHG_OLD):
        sys.exit(f'CHG_IN: {gone} of {len(CHG_OLD)} old segments found')
    new_chg = []
    for u, v in zip(CHG_NEW, CHG_NEW[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(O + u[0]), pcbnew.FromMM(O + u[1])))
        t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(O + v[0]), pcbnew.FromMM(O + v[1])))
        t.SetWidth(pcbnew.FromMM(CHG_W))
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(chg)
        t.SetLocked(True)
        b.Add(t)
        new_chg.append(t)
    log(f'CHG_IN: {gone} segments replaced by {len(new_chg)}')
    # 4. whole nets ripped
    short = {str(n).split('/')[-1]: str(n) for n in R.net_names(b)}
    codes = {b.FindNet(short[n]).GetNetCode() for n in RIP_NETS}
    dsi = {b.FindNet(short[n]).GetNetCode() for n in RIP_NETS if n.startswith('DSI_')}
    n_rip = n_kept = 0
    for t in list(R.tracks(b)):
        if t.GetNetCode() not in codes:
            continue
        # the DSI fan-out at the CM5 connector (pad stubs and staggered vias west of x 19.6) stays: the Wi-Fi module's
        # bottom-side breakouts were routed round it at 0.14-0.18 mm, closer than the pair router places a via again
        if t.GetNetCode() in dsi:
            pts = [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]
            if all(mm(q.x) - O < KEEP_DSI_X for q in pts):
                n_kept += 1
                continue
        R.remove(b, t)
        n_rip += 1
    log(f'ripped {n_rip} tracks / vias of {len(RIP_NETS)} nets, kept {n_kept} of the DSI fan-out at J302')
    # J701's old GND fan-out vias in front of the pads that now carry the lanes (the new GND pads are routed afresh)
    n_g = 0
    for t in list(R.tracks(b)):
        if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND':
            x, y = mm(t.GetPosition().x) - O, mm(t.GetPosition().y) - O
            if GND_CLEAR[0] <= x <= GND_CLEAR[2] and GND_CLEAR[1] <= y <= GND_CLEAR[3]:
                R.remove(b, t)
                n_g += 1
    log(f'GND vias removed in front of J701: {n_g}')
    # 5. copper of another net that touches a J701 / J702 pad whose net changed (the old fan-out stubs)
    changed_pads = set()
    for ref in ('J701', 'J702'):
        for p in b.FindFootprintByReference(ref).Pads():
            if (ref, p.GetNumber()) in old_nets and old_nets[(ref, p.GetNumber())] != p.GetNetname():
                changed_pads.add(p.m_Uuid.AsString())
    n5 = 0
    for ref in ('J701', 'J702'):
        for p in b.FindFootprintByReference(ref).Pads():
            if p.m_Uuid.AsString() not in changed_pads:
                continue
            bb = p.GetBoundingBox()
            r = (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom()))
            for t in list(R.tracks(b)):
                if t.GetNetCode() == p.GetNetCode():
                    continue
                if t.GetClass() == 'PCB_VIA':
                    c = (mm(t.GetPosition().x), mm(t.GetPosition().y))
                    d = rect_seg_dist(r, c, c) - mm(t.GetWidth(pcbnew.F_Cu)) / 2
                elif b.GetLayerName(t.GetLayer()) == 'F.Cu':
                    d = rect_seg_dist(r, (mm(t.GetStart().x), mm(t.GetStart().y)),
                                      (mm(t.GetEnd().x), mm(t.GetEnd().y))) - mm(t.GetWidth()) / 2
                else:
                    continue
                if d <= 0.0:
                    R.remove(b, t)
                    n5 += 1
    log(f'stubs on renamed pads removed: {n5}')
    # 6. KiCad's DRC decides the rest: a track or via in a clearance / short with a moved part's pad, a renamed pad or
    # the new CHG_IN run goes (the other item stays)
    import groute
    keep = {t.m_Uuid.AsString() for t in new_chg} | changed_pads
    for ref in MOVES:
        keep |= {p.m_Uuid.AsString() for p in b.FindFootprintByReference(ref).Pads()}
    for rnd in range(6):
        pcbnew.SaveBoard(path, b)
        d = groute.drc(path, refill=False)
        by = {t.m_Uuid.AsString(): t for t in R.tracks(b)}
        drop = {}
        for v in d['violations']:
            if v['type'] not in ('clearance', 'shorting_items', 'tracks_crossing', 'hole_clearance', 'hole_to_hole'):
                continue
            us = [i['uuid'] for i in v['items']]
            if not any(u in keep for u in us):
                continue
            for u in us:
                if u not in keep and u in by:
                    drop[u] = (v['type'], by[u].GetNetname().split('/')[-1])
        if not drop:
            break
        for u, (typ, net) in drop.items():
            R.remove(b, by[u])
        nets = sorted({n for _, n in drop.values()})
        log(f'DRC round {rnd + 1}: {len(drop)} tracks / vias removed ({", ".join(nets)})')
    pcbnew.SaveBoard(path, b)
    gndfix.remove_dangling(b, path, log=log, locked=True)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(path, b)
    log(f'saved {path}')


if __name__ == '__main__':
    main()
