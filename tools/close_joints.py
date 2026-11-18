#!/usr/bin/env python3
"""Track and via joints that only touch: a track end that is not inside same-net copper on its layer (another track, a
via, a pad, a filled zone) but meets it with its round end cap is joined by a neck narrower than the track. KiCad counts
the items as connected; a fab's CAM sees a sliver that can open (JLCPCB stopped board A's first order over it, D110).

The neck is measured against the shape of the other copper (D116):
- a straight edge (a pad, the side of a track): 2 * sqrt(r^2 - s^2) for an end cap of radius r whose centre is s
  outside it;
- a round end (another track's end cap, a via): the chord of the two overlapping circles. Two ends of the same width
  half a width apart are joined by 0.87 x the width, which the straight-edge formula counted as full (s = 0): route_tune's
  prune merges such ends and removes the copper between them, and 45 of them were on board A after D110.
A track joint is good when the neck is at least NECK x the narrower of the two widths.

Vias, on every copper layer where same-net copper touches them: at least one joint there must be good (the via's centre
on a track's centre line or end, inside a pad or a zone fill, or an overlap whose chord is NECK x the narrower width). A
via whose copper only touches a pad's edge, or only overlaps the side of a track, is reported (D116).

usage: close_joints.py BOARD.kicad_pcb [--check]

Without --check every weak joint gets a bridge: a track from the end (or the via's centre) to the nearest point inside
the other copper (on a track's centre line, a via's centre, or WIDTH/2 deep in a pad), as wide as the narrower of the
two, then the zones are refilled and the board is saved in place. With --check nothing is changed and the exit status
is 1 when such a joint exists.
"""
import collections
import math
import sys

import pcbnew

NECK = 0.95
EPS = 0.001                         # mm


def mm(v):
    return pcbnew.ToMM(v)


def nm(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def nearest_on_seg(p, a, c):
    """(nearest point, True when it is one of the segment's ends)"""
    dx, dy = c[0] - a[0], c[1] - a[1]
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L
    if t <= 0.0:
        return a, True
    if t >= 1.0:
        return c, True
    return (a[0] + t * dx, a[1] + t * dy), False


def neck(r, s):
    """width of the copper joining an end cap of radius r whose centre is s outside a straight copper edge"""
    if s <= 0:
        return 2 * r
    return 2 * math.sqrt(r * r - s * s) if s < r else 0.0


def lens(r1, r2, d):
    """width of the copper joining two overlapping circles (radii r1, r2, centres d apart): their common chord"""
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return 2 * min(r1, r2)
    k = (-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2)
    return math.sqrt(max(0.0, k)) / d


def joint_to_track(E, r, a2, c2, w2):
    """(neck, reference width, target) of copper of radius r centred at E against a track a2-c2 of width w2"""
    q, at_end = nearest_on_seg(E, a2, c2)
    d = math.dist(E, q)
    nk = lens(r, w2 / 2, d) if at_end else neck(r, d - w2 / 2)
    return nk, min(2 * r, w2), q


def items(b):
    cu = list(b.GetEnabledLayers().CuStack())
    segs = collections.defaultdict(list)
    vias = collections.defaultdict(list)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            vias[t.GetNetCode()].append(((mm(t.GetPosition().x), mm(t.GetPosition().y)), mm(t.GetWidth(pcbnew.F_Cu)) / 2, t))
        elif t.Type() == pcbnew.PCB_TRACE_T:
            segs[(t.GetLayer(), t.GetNetCode())].append(
                ((mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y)), mm(t.GetWidth()), t))
        elif t.Type() == pcbnew.PCB_ARC_T:
            sys.exit('close_joints.py: arc tracks are not handled')
    pads = collections.defaultdict(list)
    for fp in b.GetFootprints():
        for p in fp.Pads():
            for L in cu:
                if p.IsOnLayer(L) and p.GetNetCode() > 0:
                    sh = pcbnew.SHAPE_POLY_SET()
                    p.TransformShapeToPolygon(sh, L, 0, pcbnew.FromMM(0.001), pcbnew.ERROR_INSIDE)
                    pads[(L, p.GetNetCode())].append((p, sh))
    zones = collections.defaultdict(list)
    for z in b.Zones():
        if not z.GetIsRuleArea():
            for L in z.GetLayerSet().CuStack():
                zones[(L, z.GetNetCode())].append(z.GetFilledPolysList(L))
    return cu, segs, vias, pads, zones


def pad_dist(sh, V):
    return 0.0 if sh.Contains(V) else mm(int(math.sqrt(max(0, sh.SquaredDistance(V)))))


def find(b):
    """[(track, end point, width, neck, reference width, target)] for every track end whose best joint is under NECK x
    the narrower width"""
    cu, segs, vias, pads, zones = items(b)
    weak = []
    for (L, n), lst in segs.items():
        for i, (a, c, w, t) in enumerate(lst):
            r = w / 2
            for E, O in ((a, c), (c, a)):
                V = nm(*E)
                if any(ps.Contains(V) for ps in zones.get((L, n), [])):
                    continue
                # copper that the track reaches at its other end O is no joint at E (a track shorter than its width
                # overlaps it from E as well): only what lies nearer E than O counts
                best = None                   # (ratio, neck, reference width, target)
                for j, (a2, c2, w2, _) in enumerate(lst):
                    if j != i:
                        nk, ref, q = joint_to_track(E, r, a2, c2, w2)
                        if math.dist(q, O) < math.dist(q, E) - EPS:
                            continue
                        if nk > 0 and (best is None or nk / ref > best[0]):
                            best = (nk / ref, nk, ref, q)
                for vp, vr, vt in vias.get(n, []):
                    if vt.IsOnLayer(L) and math.dist(vp, O) >= math.dist(vp, E) - EPS:
                        nk, ref = lens(r, vr, math.dist(E, vp)), min(w, 2 * vr)
                        if nk > 0 and (best is None or nk / ref > best[0]):
                            best = (nk / ref, nk, ref, vp)
                for p, sh in pads.get((L, n), []):
                    s = pad_dist(sh, V)
                    if s > 0 and sh.Contains(nm(*O)):
                        continue
                    nk = neck(r, s)
                    if nk > 0 and (best is None or nk / w > best[0]):
                        best = (nk / w, nk, w, ('pad', p, sh))
                if best is not None and best[0] < NECK - EPS:
                    weak.append((t, E, w, best[1], best[2], best[3]))
    return weak


def find_vias(b):
    """[(via, layer, neck, reference width, target, bridge width)] for every via and layer where same-net copper touches
    the via but no joint there is good"""
    cu, segs, vias, pads, zones = items(b)
    weak = []
    for n, lst in vias.items():
        for vp, vr, v in lst:
            V = nm(*vp)
            for L in cu:
                if not v.IsOnLayer(L):
                    continue
                if any(ps.Contains(V) for ps in zones.get((L, n), [])):
                    continue
                touch, best = False, None     # best: (ratio, neck, reference, target, bridge width)
                for a2, c2, w2, _ in segs.get((L, n), []):
                    nk, ref, q = joint_to_track(vp, vr, a2, c2, w2)
                    if nk > 0:
                        touch = True
                        if best is None or nk / ref > best[0]:
                            best = (nk / ref, nk, ref, q, min(2 * vr, w2))
                for p, sh in pads.get((L, n), []):
                    s = pad_dist(sh, V)
                    nk = neck(vr, s)
                    if nk > 0:
                        touch = True
                        sz = p.GetSize(L)
                        ref = min(2 * vr, mm(min(sz.x, sz.y)))
                        if best is None or nk / ref > best[0]:
                            best = (nk / ref, nk, ref, ('pad', p, sh), ref)
                if touch and best[0] < NECK - EPS:
                    weak.append((v, L, best[1], best[2], best[3], best[4]))
    return weak


def duplicates(b):
    """tracks and vias that repeat another one exactly (same layer, net, ends and width; same via): the copper is the
    same, but every length KiCad and route_tune measure counts them twice"""
    seen, dup = {}, []
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            k = ('via', t.GetNetCode(), t.GetPosition().x, t.GetPosition().y, t.GetWidth(pcbnew.F_Cu), t.GetDrillValue())
        elif t.Type() == pcbnew.PCB_TRACE_T:
            s, e = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
            k = ('track', t.GetLayer(), t.GetNetCode(), min(s, e), max(s, e), t.GetWidth())
        else:
            continue
        if k in seen:
            dup.append(t)
            if t.IsLocked():
                seen[k].SetLocked(True)
        else:
            seen[k] = t
    return dup


def remove(b, items_):
    for t in items_:
        b.Remove(t)
        t.thisown = False          # as proute.remove: an unowned removed item leaks instead of breaking the bindings


def pad_target(E, p, sh, w):
    """a point WIDTH/2 inside the pad, on the way from E to the pad centre"""
    inner = pcbnew.SHAPE_POLY_SET(sh)
    inner.Deflate(pcbnew.FromMM(w / 2), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, pcbnew.FromMM(0.002))
    cx, cy = mm(p.GetPosition().x), mm(p.GetPosition().y)
    d = math.dist(E, (cx, cy))
    for k in range(1, 401):
        q = (E[0] + (cx - E[0]) * k / 400, E[1] + (cy - E[1]) * k / 400)
        if inner.OutlineCount() and inner.Contains(nm(*q)):
            return q
    return (cx, cy) if d > 0 else E


def bridge(b, E, target, w, layer, net):
    q = pad_target(E, target[1], target[2], w) if isinstance(target, tuple) and target and target[0] == 'pad' else target
    br = pcbnew.PCB_TRACK(b)
    br.SetStart(nm(*E))
    br.SetEnd(nm(*q))
    br.SetWidth(pcbnew.FromMM(w))
    br.SetLayer(layer)
    br.SetNet(net)
    br.SetLocked(True)
    b.Add(br)


def main():
    path = sys.argv[1]
    check = '--check' in sys.argv[2:]
    b = pcbnew.LoadBoard(path)
    dup = duplicates(b)
    print(f'{len(dup)} duplicate tracks / vias')
    if not check and dup:
        remove(b, dup)
    weak = find(b)
    for t, E, w, nk, ref, target in weak:
        print(f'{b.GetLayerName(t.GetLayer()):6s} {t.GetNetname().split("/")[-1]:22s} end ({E[0]:.3f}, {E[1]:.3f}) '
              f'width {w:.3f} neck {nk:.4f} of {ref:.3f} mm')
    print(f'{len(weak)} track joints with a neck under {NECK:.0%} of the narrower width')
    wv = find_vias(b)
    for v, L, nk, ref, target, bw in wv:
        print(f'{b.GetLayerName(L):6s} {v.GetNetname().split("/")[-1]:22s} via ({mm(v.GetPosition().x):.3f}, '
              f'{mm(v.GetPosition().y):.3f}) best joint {nk:.4f} of {ref:.3f} mm')
    print(f'{len(wv)} via joints with a neck under {NECK:.0%} of the narrower width')
    if check:
        sys.exit(1 if weak or dup or wv else 0)
    for t, E, w, nk, ref, target in weak:
        bridge(b, E, target, ref, t.GetLayer(), t.GetNet())
    for v, L, nk, ref, target, bw in wv:
        bridge(b, (mm(v.GetPosition().x), mm(v.GetPosition().y)), target, bw, L, v.GetNet())
    # a gap bridged from both of its ends gives the same bridge twice
    again = duplicates(b)
    remove(b, again)
    if weak or dup or wv:
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        pcbnew.SaveBoard(path, b)
        b2 = pcbnew.LoadBoard(path)
        print(f'{len(dup)} duplicates removed, {len(weak) + len(wv)} bridges added ({len(again)} of them twice, removed); '
              f'track joints still under {NECK:.0%}: {len(find(b2))}, via joints: {len(find_vias(b2))}, '
              f'duplicates: {len(duplicates(b2))}; saved {path}')


if __name__ == '__main__':
    main()
