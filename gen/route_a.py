#!/usr/bin/env python3
"""Board A routing (checkpoint 4).

    python3 gen/route_a.py [--out FILE] [--iters N] [--stop-after zones|pairs|trunks|fanout] [--resume]

Input: the placed board from gen/pcb_a.py (hw/board_a/cm5_carrier.kicad_pcb). Steps:
 1. JLC design rules, net classes with the JLC-solver impedance geometry, custom rules (gen/route_rules.py).
 2. Planes: GND on In1 and In4 (layers 2 and 5), the reference planes of every routing layer.
 3. Pre-routed copper, locked: power pours, via arrays and trunks (gen/route_power.py), differential pairs
    (gen/route_pairs.py), GND fan-out (gen/fanout.py: via-in-pad where it fits, else stub + via).
 4. Everything else with the negotiated-congestion grid router (gen/groute.py), for the connections KiCad reports
    open with the zones filled; then GND pours on the outer layers with a stitching grid, a second router pass for
    whatever is still open, zones filled.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
import pcbnew  # noqa: E402
import fanout  # noqa: E402
import gndfix  # noqa: E402
import groute  # noqa: E402
import proute as R  # noqa: E402
import route_pairs  # noqa: E402
import route_power  # noqa: E402
import route_rules  # noqa: E402
import route_tune  # noqa: E402

BOARD = os.path.join(ROOT, 'hw', 'board_a', 'cm5_carrier.kicad_pcb')
PRO = os.path.join(ROOT, 'hw', 'board_a', 'cm5_carrier.kicad_pro')
DRU = os.path.join(ROOT, 'hw', 'board_a', 'cm5_carrier.kicad_dru')
O = 100.0        # board origin in the file
W, H = 95.0, 65.0
VIA = (0.4, 0.2)    # routing / fan-out via (JLC 6-layer: 0.15 / 0.25 minimum, hole + 0.1)


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(O + x), mm(O + y))


def zone(b, net, layer, pts, prio=0, clearance=0.2, min_w=0.15, name='', thermal=True):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet(net))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(min_w))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(mm(0.2))
    z.SetThermalReliefSpokeWidth(mm(0.25))
    if name:
        z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(mm(O + x), mm(O + y))
    b.Add(z)
    return z


def board_rules(b):
    ds = b.GetDesignSettings()
    J = route_rules.JLC
    ds.m_MinClearance = mm(J['clearance'])
    ds.m_TrackMinWidth = mm(J['track'])
    ds.m_ViasMinSize = mm(J['via_dia'])
    ds.m_ViasMinAnnularWidth = mm(J['annular'])
    ds.m_MinThroughDrill = mm(J['via_hole'])
    ds.m_HoleClearance = mm(J['via_hole_to_track'])
    ds.m_HoleToHoleMin = mm(J['hole_to_hole'])
    ds.m_CopperEdgeClearance = mm(J['edge'])
    ds.m_SolderMaskMinWidth = mm(J['mask_bridge'])
    ds.m_SolderMaskExpansion = 0
    ds.m_FillVias = True            # via-in-pad: JLC fills and caps vias on 6-layer boards by default
    ds.m_CapVias = True


def plane_layers(b):
    """In1 / In4 are GND planes: power-plane layer type, so the autorouter does not route on them"""
    for L in (pcbnew.In1_Cu, pcbnew.In4_Cu):
        b.SetLayerType(L, pcbnew.LT_POWER)


def planes(b):
    e = 0.3
    outline = [(e, e), (W - e, e), (W - e, H - e), (e, H - e)]
    zone(b, 'GND', pcbnew.In1_Cu, outline, prio=0, clearance=0.2, name='GND plane L2')
    zone(b, 'GND', pcbnew.In4_Cu, outline, prio=0, clearance=0.2, name='GND plane L5')


def net_rules(skip_zone_nets=(), res=0.05, margin=0.02):
    """grid-router rules (gen/groute.py): the class widths and clearances of gen/route_rules.py, single-ended
    impedance nets at their per-layer width, filled via-in-pad allowed (JLC 6-layer default)"""
    def width_of(net, L):
        cls = route_rules.classify(net.split('/')[-1])
        if cls in route_rules.GEOM:
            return route_rules.GEOM[cls]['out' if L in ('F', 'B') else 'inn'][0]
        return route_rules.CLASSES[cls or 'Default'][1]

    def clearance_of(net):
        return route_rules.CLASSES[route_rules.classify(net.split('/')[-1]) or 'Default'][0]
    J = route_rules.JLC
    return groute.Rules(('F', 'In2', 'In3', 'B'), VIA, width_of, clearance_of,
                        h_def=route_rules.CLASSES['Default'][1] / 2, c_def=route_rules.CLASSES['Default'][0],
                        hole_clr=J['via_hole_to_track'], pth_clr=J['inner_pth_to_copper'], npth_clr=J['npth_to_track'],
                        hole_to_hole=J['hole_to_hole'], edge=J['edge'], res=res, margin=margin, via_in_pad=True,
                        skip_zone_nets=skip_zone_nets, full_states=0,    # one label per cell: 4 layers, big windows
                        keep_width=impedance)


def impedance(net):
    """impedance-controlled net: its track width per layer is a DRC rule (no neck-down at the pins)"""
    return route_rules.classify(net.split('/')[-1]) in route_rules.GEOM


def grid_route(b, out, iters, skip_nets=('GND',), skip_zone_nets=(), narrow=(), log=print):
    """route what KiCad reports open (zones refilled) with the negotiated-congestion grid router; returns the
    connections left, the spots where their last paths met other nets, and the nets the router found no path for"""
    pcbnew.SaveBoard(out, b)
    conns, skipped = groute.open_connections(b, out, ('F', 'In2', 'In3', 'B'), skip_nets=skip_nets, log=log)
    if not conns:
        return skipped, [], set()
    g = groute.Grid(b, net_rules(skip_zone_nets), log=log)
    r = groute.Router(g, conns, log=log, narrow=narrow)
    r.run(iters=iters)
    done = r.commit()
    log(f'grid router: {len(done)} of {len(conns)} connections committed')
    groute.merge_close_vias(b, VIA[1], 0.2, log=log)
    return ([conns[k] for k in range(len(conns)) if k not in done] + skipped, r.hotspots(done),
            {conns[k][0] for k in r.failed})


# Wi-Fi antenna lines (50 ohm, bottom side): module pin -> 0 ohm link -> U.FL, and the DNP shunt pad of each matching
# network. Routed before everything else, as the short straight lines they are (a GND fan-out via had landed on one)
RF = [('WL_ANT0_M', 'U601.2', 'R603.1'), ('WL_ANT0', 'R603.2', 'J601.1'), ('WL_ANT0', 'C615.1', 'R603.2'),
      ('WL_ANT1_M', 'U601.9', 'R604.1'), ('WL_ANT1', 'R604.2', 'J602.1'), ('WL_ANT1', 'C616.1', 'R604.2')]


def rf_lines(b, log):
    pr = route_pairs.PairRouter(b, log)
    failed = []
    for net, a, z in RF:
        ends = []
        for rp in (a, z):
            fp, p = route_pairs.pad_of(b, rp)
            x, y = R.to_mm(p.GetPosition())
            ends.append((x, y, route_pairs.pad_layer(fp)))
        if pr.single(net, 'SE50', ends[0], ends[1], layers=('B',), margin=1.5) is None and \
                pr.single(net, 'SE50', ends[0], ends[1], margin=3.0) is None:
            failed.append(f'{net} {a}-{z}')
    log(f'antenna lines: {len(RF) - len(failed)} of {len(RF)} routed; failed {failed}')


# the microSD bus (50 ohm, ~27 mm from the CM5 connector across the power section to the card socket) is routed before
# the other signals, as a group, and locked like the pairs: in the board-wide negotiation it was what lost out at the
# end in most runs (D75)
SD_BUS = ('SD_CLK_SOC', 'SD_CLK', 'SD_CMD', 'SD_D0', 'SD_D1', 'SD_D2', 'SD_D3')
ESCAPE_COST = 30.0    # per grid cell, on other pins' escapes (the base cost is 1 per cell)
PAD_RING, PAD_RING_COST = 0.45, 10.0   # mm around the other nets' SMD pads, cost per grid cell there


def bus_first(b, out, names, iters, log):
    pcbnew.SaveBoard(out, b)
    conns, _ = groute.open_connections(b, out, ('F', 'In2', 'In3', 'B'), skip_nets=(), log=lambda m: None)
    conns = [c for c in conns if c[0].split('/')[-1] in names]
    if not conns:
        return
    xs = [p[0] for c in conns for p in (c[1], c[2])]
    ys = [p[1] for c in conns for p in (c[1], c[2])]
    w = [max(-0.5, min(xs) - 3.0), max(-0.5, min(ys) - 3.0), min(W + 0.5, max(xs) + 3.0), min(H + 0.5, max(ys) + 3.0)]
    g = groute.Grid(b, net_rules(res=0.025, margin=0.02), log=log, window=w)
    # the other pins' escape stubs and via landings at the fine-pitch parts (D42): not blocked, but dear, so the bus
    # leaves them to their pins where it can
    codes = {b.FindNet(c[0]).GetNetCode() for c in conns}
    marks = {L: groute._buf('i', g.nx * g.ny) for L in g.layers}
    marks_v = groute._buf('i', g.nx * g.ny)
    for code, L, _, pts, land in R.escape_corridors(b):
        if code in codes or L not in g.layers:
            continue
        ps = pcbnew.SHAPE_POLY_SET()
        ps.NewOutline()
        for x, y in pts:
            ps.Append(R.nm(R.O + x), R.nm(R.O + y))
        g._fill((marks_v if land else marks[L])[1], ps, 1)
    for m, h in [(marks[L][0], g.hist[li][0]) for li, L in enumerate(g.layers)] + [(marks_v[0], g.hist_v[0])]:
        for idx in [k for k, v in enumerate(m) if v]:
            h[idx] += ESCAPE_COST
    # and the room around the other nets' SMD pads (GND has its fan-out already): a locked bus hugging a pad boxed
    # pins in (BST_CM5_FSW at U201, SD_DET_N at the card socket in run a29)
    rings = {L: groute._buf('i', g.nx * g.ny) for L in ('F', 'B')}
    for fp in R.footprints(b):
        for p in R.pads(fp):
            if p.GetNetCode() <= 0 or p.GetNetCode() in codes or p.GetNetname().split('/')[-1] == 'GND' or \
                    p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            L = 'B' if p.IsOnLayer(pcbnew.B_Cu) else 'F'
            ps = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(ps, R.LAYER[L], R.nm(PAD_RING), R.MAXERR, pcbnew.ERROR_OUTSIDE)
            g._fill(rings[L][1], ps, 1)
    for L, m in rings.items():
        h = g.hist[g.layers.index(L)][0]
        for idx in [k for k, v in enumerate(m[0]) if v]:
            h[idx] += PAD_RING_COST
    r = groute.Router(g, conns, log=lambda m: None)
    r.run(iters=iters)
    before = {t.m_Uuid.AsString() for t in R.tracks(b)}
    done = r.commit()
    groute.merge_close_vias(b, VIA[1], 0.2, log=log)
    for t in R.tracks(b):
        if t.m_Uuid.AsString() not in before:
            t.SetLocked(True)
    log(f'{"/".join(names)} first: {len(done)} of {len(conns)} connections routed and locked')


def fine_pass(b, out, left, iters, log, pad=4.0, margin=0.02, skip_zone_nets=()):
    """what the board-wide passes leave open is routed again at 0.025 mm (margin 0.02 mm, as on the 0.05 mm grid: the
    track pitch rounds to 0.225 mm either way, and a wide net's clearance disk needs it) in a window around it: the router's own copper inside the window is taken up and routed again with the
    open connections, closer than the 0.05 mm grid allows (0.4 mm-pitch pins)"""
    boxes = [[min(a0[0], z0[0]) - pad, min(a0[1], z0[1]) - pad, max(a0[0], z0[0]) + pad, max(a0[1], z0[1]) + pad]
             for _, a0, z0 in [c for c in left if isinstance(c, tuple)]]   # (items KiCad could not place: dicts)
    merged = True
    while merged:                                      # overlapping windows become one, until none overlap
        merged = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, c = boxes[i], boxes[j]
                if a[0] < c[2] and c[0] < a[2] and a[1] < c[3] and c[1] < a[3]:
                    boxes[i] = [min(a[0], c[0]), min(a[1], c[1]), max(a[2], c[2]), max(a[3], c[3])]
                    del boxes[j]
                    merged = True
                    break
            if merged:
                break
    for w in boxes:
        w = [max(-0.5, w[0]), max(-0.5, w[1]), min(W + 0.5, w[2]), min(H + 0.5, w[3])]
        inside = lambda p, m=0.0: w[0] + m <= p[0] <= w[2] - m and w[1] + m <= p[1] <= w[3] - m
        gone = 0
        for t in R.tracks(b):
            if t.IsLocked():
                continue
            pts = [R.to_mm(t.GetPosition())] if isinstance(t, pcbnew.PCB_VIA) else \
                [R.to_mm(t.GetStart()), R.to_mm(t.GetEnd())]
            if all(inside(p, 0.3) for p in pts):
                R.remove(b, t)
                gone += 1
        pcbnew.SaveBoard(out, b)
        conns, _ = groute.open_connections(b, out, ('F', 'In2', 'In3', 'B'), skip_nets=(), log=log)
        conns = [c for c in conns if inside(c[1], 0.1) and inside(c[2], 0.1)]
        log(f'fine pass in ({w[0]:.1f}, {w[1]:.1f})-({w[2]:.1f}, {w[3]:.1f}): {gone} router items taken up, '
            f'{len(conns)} connections')
        if not conns:
            continue
        g = groute.Grid(b, net_rules(skip_zone_nets, res=0.025, margin=margin), log=log, window=w)
        r = groute.Router(g, conns, log=log)
        r.run(iters=iters)
        done = r.commit()
        groute.merge_close_vias(b, VIA[1], 0.2, log=log)
        log(f'fine pass: {len(done)} of {len(conns)} committed')
    pcbnew.SaveBoard(out, b)
    conns, skipped = groute.open_connections(b, out, ('F', 'In2', 'In3', 'B'), skip_nets=(), log=log)
    return conns + skipped


def _hits(new, others, clr, slack=0.06):
    """the items of `others` closer to any of `new` than their nets' clearance clr(net name) plus slack, KiCad's own
    shapes; via holes keep 0.2 mm (plus slack) from copper and from other holes. The slack: what is left of a net that
    ran next to the new path ends far enough from it for the grid (which blocks track centres within clearance + half
    the default width + its 0.02 mm margin of other copper) to start a path there"""
    hit = []
    for o in others:
        ob = o.GetBoundingBox()
        for it in new:
            c = R.nm(max(clr(it.GetNetname()), clr(o.GetNetname())) + slack)
            bb = it.GetBoundingBox()
            bb.Inflate(c + R.nm(0.5))
            if not bb.Intersects(ob):
                continue
            if any(it.IsOnLayer(L) and o.IsOnLayer(L) and it.GetEffectiveShape(L).Collide(o.GetEffectiveShape(L), c)
                   for L in R.LAYER.values()):
                break
            vias = [v for v in (it, o) if isinstance(v, pcbnew.PCB_VIA)]
            if any(w.IsOnLayer(L) and w.GetEffectiveShape(L).Collide(v.GetEffectiveHoleShape(), R.nm(0.2 + slack))
                   for v in vias for w in (it, o) if w is not v for L in R.LAYER.values()):
                break
            if len(vias) == 2 and vias[0].GetEffectiveHoleShape().Collide(vias[1].GetEffectiveHoleShape(),
                                                                           R.nm(0.2 + slack)):
                break
        else:
            continue
        hit.append(o)
    return hit


def _trial(b, conn, soft, band, pad, rules, soft_nets=()):
    """route conn alone with the router's own copper soft (it may cross it, at a cost `soft` per cell); the router
    items that come within their clearance + `band` mm of that trial path are taken up, and the trial path with them.
    Returns the nets taken up (the connection's own included), None when there is no path even so"""
    net, a, z = conn
    w = [max(-0.5, min(a[0], z[0]) - pad), max(-0.5, min(a[1], z[1]) - pad),
         min(W + 0.5, max(a[0], z[0]) + pad), min(H + 0.5, max(a[1], z[1]) + pad)]
    g = groute.Grid(b, rules, log=lambda m: None, window=w, soft=soft, soft_nets=soft_nets)
    r = groute.Router(g, [conn], log=lambda m: None)
    r.run(iters=1)
    if 0 not in r.paths:
        return None
    before = {t.m_Uuid.AsString() for t in R.tracks(b)}
    r.commit(conflicts_ok=True)
    all_t = R.tracks(b)
    new = [t for t in all_t if t.m_Uuid.AsString() not in before]
    code = b.FindNet(net).GetNetCode()
    others = [t for t in all_t if (not t.IsLocked() or t.GetNetname() in soft_nets) and t.GetNetCode() != code
              and t.m_Uuid.AsString() in before]
    hit = _hits(new, others, g.cdef, slack=band)
    nets = {t.GetNetname() for t in hit} | {net}
    for t in hit + new:
        R.remove(b, t)
    return nets


SWAPS = 8      # per rip-up pass: transactions kept for trading a long open connection for shorter ones (D78)


def ripup_pass(b, out, left, iters, log, tries=((10.0, 0.06), (4.0, 0.06), (10.0, 0.4), (10.0, 0.8)), pad=3.0,
               passes=2, steps=3):
    """rip-up and re-route for what the window passes leave open (D74), one connection at a time, longest first, as a
    transaction: a trial route (_trial) takes up the router copper in the connection's way, then the connection and
    everything that opened are routed again together (negotiated, 0.025 mm grid, a window over all of them). What
    finds no path there gets a trial route of its own and the joint routing is repeated (up to `steps` times). The
    result is kept only when the board then has fewer open connections; else the board goes back and the next try
    (crossing cost, band of router copper taken up along the trial path beyond what collides with it) is made.
    Returns (board, open connections)"""
    layers = ('F', 'In2', 'In3', 'B')
    quiet = lambda m: None
    rules = net_rules(('GND',), res=0.025, margin=0.02)
    # the bus routed first (D75) is locked against the window passes, but may give way here like router copper
    bus = {n for n in R.net_names(b) if n.split('/')[-1] in SD_BUS}
    snap = out + '.ripup'                       # a file copy (a board saved under another name drags its project along)
    pcbnew.SaveBoard(out, b)
    n_open = len(left)
    key = lambda c: (c[0],) + tuple(round(v, 1) for v in c[1][:2] + c[2][:2])
    # total open length; one the router cannot take (skipped) counts as 100 mm, so it is never traded in
    span = lambda cs: round(sum(math.dist(c[1][:2], c[2][:2]) if isinstance(c, tuple) else 100.0 for c in cs), 3)
    snap0 = out + '.ripup0'
    for pas in range(passes):
        n0, s0, tried, swaps, ups, left0 = n_open, span(left), set(), 0, 0, list(left)
        shutil.copy(out, snap0)                 # the board as the pass found it (a trade that does not pay off)
        while True:                             # the longest open connection not tried yet in this pass
            todo = [c for c in left if isinstance(c, tuple) and key(c) not in tried]
            if not todo:
                break
            target = max(todo, key=lambda c: math.dist(c[1][:2], c[2][:2]))
            tried.add(key(target))
            net, a, z = target
            for soft, band in tries:
                shutil.copy(out, snap)
                was = [c for c in left if isinstance(c, tuple)]
                nets, trials, taken, routed, kept = set(), [target], 0, (0, 0), False
                for step in range(steps):
                    for c in trials:
                        got = _trial(b, c, soft, band, pad, rules, soft_nets=bus)
                        if got:
                            nets |= got
                            taken += len(got) - 1
                    if not nets:                # no path even through the router copper: no try helps
                        break
                    pcbnew.SaveBoard(out, b)
                    conns, _ = groute.open_connections(b, out, layers, skip_nets=(), log=quiet)
                    conns = [c for c in conns if c[0] in nets]
                    if not conns:
                        break
                    xs = [p[0] for c in conns for p in (c[1], c[2])]
                    ys = [p[1] for c in conns for p in (c[1], c[2])]
                    w2 = [max(-0.5, min(xs) - 1.5), max(-0.5, min(ys) - 1.5),
                          min(W + 0.5, max(xs) + 1.5), min(H + 0.5, max(ys) + 1.5)]
                    g2 = groute.Grid(b, rules, log=quiet, window=w2)
                    r2 = groute.Router(g2, conns, log=quiet)
                    r2.run(iters=iters)
                    done = r2.commit()
                    groute.merge_close_vias(b, VIA[1], 0.2, log=quiet)
                    routed = (routed[0] + len(done), routed[1] + len(conns))
                    pcbnew.SaveBoard(out, b)
                    c2, sk2 = groute.open_connections(b, out, layers, skip_nets=(), log=quiet)
                    msg = (f'rip-up: {net.split("/")[-1]} ({math.dist(a[:2], z[:2]):.0f} mm, soft {soft:g}, band '
                           f'{band:g}, step {step + 1}): router copper of {taken} other nets taken up, {routed[0]} of '
                           f'{routed[1]} routed again, {len(c2) + len(sk2)} open (was {n_open})')
                    n2 = len(c2) + len(sk2)
                    # as many open, but a long one traded for much shorter ones, counts too (D78): those are closed
                    # next, in windows of their own size
                    swap = (n2 == n_open and swaps < SWAPS and
                            span(c2 + sk2) <= span(left) - max(5.0, 0.5 * math.dist(a[:2], z[:2])))
                    # one more open, but the open length down to a quarter: also kept, and the pass is undone at
                    # its end if it then leaves more open than it found (D84)
                    up = n2 == n_open + 1 and ups < 2 and span(c2 + sk2) <= 0.25 * span(left)
                    if n2 < n_open or swap or up:
                        swaps += swap
                        ups += up
                        n_open, left, kept = n2, c2 + sk2, True
                        log(msg + (f': kept (open length {span(left):.0f} mm)' if swap or up else ': kept'))
                        break
                    log(msg)
                    # the next step chases only what this transaction broke (not the connections open before it)
                    trials = sorted([c for k, c in enumerate(conns) if k not in done and not any(
                        c[0] == o[0] and max(math.dist(c[1][:2], o[1][:2]), math.dist(c[2][:2], o[2][:2])) < 0.05
                        for o in was)], key=lambda c: -math.dist(c[1][:2], c[2][:2]))[:6]
                    if not trials:
                        break
                if kept:
                    break
                log(f'rip-up: {net.split("/")[-1]}: ' + ('undone' if nets else 'no path even through the router copper'))
                shutil.copy(snap, out)
                b = pcbnew.LoadBoard(out)
                if not nets:
                    break
        if n_open > n0:                         # a trade that did not pay off: the pass is undone
            log(f'rip-up pass undone: {n_open} open, {n0} before it')
            shutil.copy(snap0, out)
            b = pcbnew.LoadBoard(out)
            n_open, left = n0, left0
            break
        if not left or (n_open, span(left)) >= (n0, s0):
            break
    for f in (snap, snap0):
        if os.path.exists(f):
            os.remove(f)
    return b, left


DRC_KINDS = {'clearance', 'hole_clearance', 'shorting_items', 'hole_to_hole', 'copper_edge_clearance'}


def _error_spots(b, d):
    mine = {t.m_Uuid.AsString() for t in R.tracks(b) if not t.IsLocked()}
    return [(i['pos']['x'] - R.O, i['pos']['y'] - R.O) for v in d['violations']
            if v['type'] in DRC_KINDS and v['severity'] == 'error' and any(i['uuid'] in mine for i in v['items'])
            for i in v['items']]


def drc_repair(b, out, iters, log, rounds=3, pads=(1.5, 3.0, 5.0)):
    """clearance errors KiCad's DRC still finds on the router's own copper (a few thousandths of a mm, where a wide
    net's clearance disk meets a diagonal): the router's copper in a window around each is taken up and routed again
    on the 0.025 mm grid with a 0.03 mm margin (GND pours are filled around it afterwards). A window that leaves more
    connections open than before is undone and a bigger one tried; if none manages, the one with the fewest open
    connections is kept (the rip-up pass after it takes those). Returns the board (it may have been reloaded)"""
    snap = out + '.repair'
    for _ in range(rounds):
        pcbnew.SaveBoard(out, b)
        d = groute.drc(out)
        spots = _error_spots(b, d)
        log(f'DRC repair: {len(spots)} error spots on router copper')
        if not spots:
            break
        n0 = len(d['unconnected_items'])
        shutil.copy(out, snap)
        tries = []
        for k, pad in enumerate(pads):
            fine_pass(b, out, [('', s, s) for s in spots], iters, log, pad=pad, margin=0.03, skip_zone_nets=('GND',))
            pcbnew.SaveBoard(out, b)
            d2 = groute.drc(out)
            n2, e2 = len(d2['unconnected_items']), len(_error_spots(b, d2))
            log(f'DRC repair, window {pad:g} mm: {e2} error spots, {n2} open (was {n0})')
            if e2 == 0 and n2 <= n0:
                break
            shutil.copy(out, f'{out}.try{k}')
            tries.append((e2, n2, k))
            shutil.copy(snap, out)
            b = pcbnew.LoadBoard(out)
        else:
            _, _, k = min(tries)
            shutil.copy(f'{out}.try{k}', out)
            b = pcbnew.LoadBoard(out)
        for k in range(len(pads)):
            if os.path.exists(f'{out}.try{k}'):
                os.remove(f'{out}.try{k}')
    if os.path.exists(snap):
        os.remove(snap)
    return b


MIPI_GROUPS = [('MIPI DSI', 'DSI_', 'DSI_CLK'), ('MIPI CSI-A', 'CSIA_', 'CSIA_CLK'), ('MIPI CSI-B', 'CSIB_', 'CSIB_CLK')]


def tune(b, log):
    """length tuning while the board around the pairs is still empty: every pair's P/N skew first (bumps on the
    shorter trace), then the MIPI lanes to their group (whole-pair accordions, which keep P and N equal)"""
    full = {}
    for n in R.net_names(b):
        full.setdefault(str(n).split('/')[-1], str(n))
    pairs = {}
    for name, p, n, cls, *_ in route_pairs.PAIRS:
        pairs.setdefault((full[p], full[n]), (name, cls))
    res = route_tune.tune_all(b, [(name, P, N, cls) for (P, N), (name, cls) in pairs.items()], log)
    bad = [(n, round(d, 3)) for n, d in res if abs(d) > 0.127]
    log(f'intra-pair skew: {len(res)} pairs, over 0.127 mm: {bad}')
    for title, prefix, clk in MIPI_GROUPS:
        lanes = [(name, P, N) for (P, N), (name, cls) in pairs.items() if name.startswith(prefix)]
        Ls = route_tune.match_group(b, lanes, 'MIPI100', tol=0.5, log=log, title=title, clock=clk)
        log(f'{title}: ' + ', '.join(f'{k} {v:.2f}' for k, v in sorted(Ls.items())))


# DRC findings that are by design, with the reason (recorded as KiCad DRC exclusions in the project file)
BY_DESIGN = [
    ('pth_inside_courtyard', ('H301', 'H302', 'H303', 'H304'), 'J301',
     'CM5 standoffs: the module is fixed on them, at the hole positions of the Orange Pi CM5 base board'),
    ('pth_inside_courtyard', ('H501',), 'J301',
     'M.2 standoff on the bottom, under the CM5 outline; its shank (0.33 mm) is under 0402 / 0603 parts on the module '
     'underside, ~0.27 mm clear with 0.9 mm parts (D86)'),
    ('npth_inside_courtyard', ('J501',), 'J301',
     'M.2 socket locating holes (bottom part) under the CM5 outline; nothing protrudes on the top'),
]
# Hirose U.FL land (KiCad library footprint U.FL_Hirose_U.FL-R-SMT-1_Vertical): one solder-resist opening around the
# centre contact and the ground lands, as Hirose draws it. KiCad's footprint flag for exactly this case is set instead
# of an exclusion (the marker of a mask bridge sits at the collision point, which an exclusion cannot name reliably)
MASK_BRIDGES_ALLOWED = ('J601', 'J602')


def exclusions(d):
    """KiCad DRC exclusion keys ('type|x|y|uuid|uuid', nm) for the BY_DESIGN findings in DRC result d"""
    import re
    out = []
    for v in d['violations']:
        for typ, refs, other, why in BY_DESIGN:
            if v['type'] != typ:
                continue
            names = {m.group(1) for i in v['items'] for m in [re.search(r'(?: of |Footprint )(\S+)', i['description'])] if m}
            if names & set(refs) and (other is None or other in names or len(names) == 1):
                a, b2 = v['items'][0], v['items'][-1]
                out.append(f"{typ}|{round(a['pos']['x'] * 1e6)}|{round(a['pos']['y'] * 1e6)}|{a['uuid']}|{b2['uuid']}")
    return sorted(set(out))



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=BOARD)
    ap.add_argument('--iters', type=int, default=40)
    ap.add_argument('--stop-after', choices=('zones', 'pairs', 'trunks', 'fanout'), default=None)
    ap.add_argument('--resume', action='store_true', help='OUT was saved by --stop-after fanout: route it')
    ap.add_argument('--finish', action='store_true',
                    help='OUT is routed: run the rip-up and clean-up stage again for what is still open')
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    log = lambda m: print(m, flush=True)
    if a.resume:
        b = pcbnew.LoadBoard(out)
        route(b, out, a.iters, log)
        return
    if a.finish:
        b = pcbnew.LoadBoard(out)
        conns, skipped = groute.open_connections(b, out, ('F', 'In2', 'In3', 'B'), skip_nets=(), log=log)
        b, left = close_out(b, out, conns + skipped, a.iters, log)
        finish(b, out, log)
        return
    pro = os.path.splitext(out)[0] + '.kicad_pro'
    # net classes and rules live in the project file: write it first, then load the board with it
    src = pcbnew.LoadBoard(BOARD)
    nets = R.net_names(src)
    if out != os.path.abspath(BOARD):
        shutil.copy(BOARD, out)
        shutil.copy(PRO, pro)
    route_rules.write_project(pro, nets)
    # a full run starts without DRC exclusions: finish() writes this board's own (an earlier board's would only match
    # items that no longer exist)
    pj = json.load(open(pro))
    pj.setdefault('board', {}).setdefault('design_settings', {})['drc_exclusions'] = []
    json.dump(pj, open(pro, 'w'), indent=2)
    route_rules.write_dru(os.path.splitext(out)[0] + '.kicad_dru')
    n = R.strip_routing_file(out)                   # start from the placement
    if n:
        print(f'removed {n} tracks, vias and zones of an earlier run')
    b = pcbnew.LoadBoard(out)
    board_rules(b)
    for ref in MASK_BRIDGES_ALLOWED:
        b.FindFootprintByReference(ref).SetAllowSolderMaskBridges(True)
    plane_layers(b)
    planes(b)
    route_power.zones_and_vias(b, log)
    steps = ('zones', 'pairs', 'trunks', 'fanout')
    upto = steps.index(a.stop_after) if a.stop_after else len(steps)
    if upto >= 1:
        # camera connectors: front-row GND pins between two lanes are boxed in by the pass-through traces and then by
        # the pairs. J704.4 too since D119: it was left out before (its neighbours did not pass a trace by it, and a
        # via there was to keep clear of WL_REFCLK), but with CSI-A's new layer plan D3 / D2 box it in. Its via lands
        # 4.0 mm out: at 3.2 / 3.6 mm it is under or beside the Wi-Fi U.FL pad J602.1 on the back, closer in it is in
        # the U.FL's keepout.
        # Display FPC J701: the GND pins between the lanes (13, 16, 19, 22 since the pins are mirrored, D118) get
        # their via just in front of the pad, inside the lanes' launch, before the lanes take the room.
        # Connector B J302.20 (between the LTE USB 3.0 RX and TX pins): its fan-out via went 0.7 mm east of the pad,
        # between the pin rows; since D119 CSI-A's D3 / D2 run under there on L3, and in both D119 routes the pad was
        # left unconnected, so the via is placed first
        fanout.front_row_gnd(b, {'J704': ('4', '10', '16'), 'J705': ('10', '16'), 'J701': ('13', '16', '19', '22'),
                                 'J302': ('20',)},
                             VIA, log=log, toward={'J701': (-1, (0.9, 1.0, 1.1)), 'J302': (1, (0.7, 0.65))})
        rf_lines(b, log)
        failed = route_pairs.route_all(b, log)
        log(f'pairs: {len(failed)} failed {failed}')
        tune(b, log)
    if upto >= 2:
        tf = route_power.trunks(b, log)
        log(f'trunks: {len(tf)} failed {tf}')
    if upto >= 3:
        # CM5 connectors and camera FPC connectors: GND vias between the two pad rows (under the bodies) where there is
        # room, so signals keep the outward escapes
        # U101.19 (GND) is left to the grid router: the CHG_IN trunk now ends on F.Cu at its neighbour U101.20, and the
        # fan-out's next via spot boxed in U101.18 (PD_I2CC_IRQ_N, run o30, D102)
        fo = fanout.Fanout(b, VIA, clearance=0.15, in_pad=True, inward=('J301', 'J302', 'J303', 'J704', 'J705'), log=log,
                           special={('U101', '19'): lambda f, fp, p: None})
        fo.run()
    if a.stop_after is None:
        route(b, out, a.iters, log)
    else:
        pcbnew.SaveBoard(out, b)
        log(f'saved {out}')


def route(b, out, iters, log):
    bus_first(b, out, SD_BUS, 2 * iters, log)
    # GND pins the fan-out found no room for are routed with the signals (to the nearest GND via), so the negotiation
    # leaves them a way out; the planes on L2 / L5 are not routing layers
    left, hot, stuck = grid_route(b, out, 2 * iters, skip_nets=(), log=log)
    # what the board-wide pass could not settle is routed again locally on a finer grid, in growing windows (ripping
    # up whole nets around the conflicts and negotiating again board-wide did not converge: D61)
    for pad in (3.0, 5.0, 8.0):
        if not [c for c in left if isinstance(c, tuple)]:
            break
        left = fine_pass(b, out, left, 2 * iters, log, pad=pad)
    if [c for c in left if isinstance(c, tuple)]:
        # the last few, board-wide, everything else in place (long connections whose windows span the board)
        left, hot, stuck = grid_route(b, out, iters, skip_nets=(), log=log)
    log(f'left open after the signal passes: {len(left)}')
    route_power.gnd_pours(b, log)
    # GND pieces still apart, item to item: routed, the outer-layer GND pours fill around the new copper
    left, hot, stuck = grid_route(b, out, iters, skip_nets=(), skip_zone_nets=('GND',), log=log)
    b, left = close_out(b, out, left, iters, log)
    finish(b, out, log)


def finish(b, out, log):
    """zones filled, saved, the by-design DRC exclusions written, the final check"""
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    pcbnew.SaveBoard(out, b)
    log(f'saved {out}')
    # joints that only touch closed and duplicate copper removed (tools/close_joints.py), the pairs' skew tuned again on
    # the true lengths that leaves, and checked once more (D110)
    tools = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools')
    for step in (['close_joints.py', out], ['retune_pairs.py', out], ['close_joints.py', out]):
        r = subprocess.run([sys.executable, os.path.join(tools, step[0]), *step[1:]], capture_output=True, text=True)
        for ln in r.stdout.splitlines():
            if 'Debug' not in ln and not ln.startswith(('F.Cu', 'B.Cu', 'In')):
                log(ln)
    # the by-design findings go into the project file as DRC exclusions, then the final check
    pro = os.path.splitext(out)[0] + '.kicad_pro'
    # (a project that has them already, as after --finish, keeps them: KiCad's report leaves excluded findings out)
    had = json.load(open(pro)).get('board', {}).get('design_settings', {}).get('drc_exclusions', [])
    had = {e[0] if isinstance(e, list) else e for e in had}           # KiCad saves them as [key, comment]
    ex = sorted(had | set(exclusions(groute.drc(out, refill=False))))
    route_rules.write_project(pro, R.net_names(b), exclusions=ex)
    log(f'{len(ex)} DRC exclusions (by design) written to {os.path.basename(pro)}')
    groute.log_drc(out, log)


def pour_pieces(b, log):
    """log every pour whose fill came out in more than one piece with pads of its net on them (a piece joined to the
    rest only by a routed track, D81, would carry the pour's current through that track). Not GND: its outer-layer
    pours are pieces by design, each tied to the L2 / L5 planes by vias"""
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pads = [p for fp in R.footprints(b) for p in R.pads(fp)]
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() == 'GND':
            continue
        for L in z.GetLayerSet().CuStack():
            fp = z.GetFilledPolysList(L)
            held = [i for i in range(fp.OutlineCount())
                    if any(p.GetNetCode() == z.GetNetCode() and p.IsOnLayer(L) and fp.Outline(i).PointInside(p.GetPosition())
                           for p in pads)]
            if len(held) > 1:
                log(f'WARNING: pour {z.GetZoneName() or z.GetNetname()} on {b.GetLayerName(L)} in {len(held)} pieces with pads')


def close_out(b, out, left, iters, log):
    """rip-up and re-route for what is still open (D74), the clean-up (D77) and again for what that opened.
    Returns (board, open connections)"""
    if left:
        b, left = ripup_pass(b, out, left, iters, log)
    gndfix.solid_where_starved(b, out, log=log)
    gndfix.remove_dangling(b, out, log=log, locked=True)
    b = drc_repair(b, out, iters, log)
    gndfix.remove_dangling(b, out, log=log, locked=True)
    zn = {z.GetNetCode() for z in b.Zones()}
    last = None
    for _ in range(4):                          # what is still open: rip-up and re-route again, while it helps
        # loops and fold-backs on the router's copper (a connection routed again beside copper of its own net): the
        # copper off the pad-to-pad paths goes, on the nets without a pour (D79), and what KiCad then sees as a dead
        # end; counted after that, so a connection this opens is routed again in the same loop
        cut = sum(route_tune.prune(b, c) for c in sorted({t.GetNetCode() for t in R.tracks(b)} - zn - {0}))
        log(f'copper off the pad-to-pad paths removed: {cut:.1f} mm')
        gndfix.remove_dangling(b, out, log=log, locked=True)
        gndfix.solid_where_starved(b, out, log=log)   # the rip-up changed the pours too
        pcbnew.SaveBoard(out, b)
        conns, skipped = groute.open_connections(b, out, ('F', 'In2', 'In3', 'B'), skip_nets=(), log=log)
        left = conns + skipped
        if not conns or (last is not None and len(left) >= last):
            break
        last = len(left)
        b, left = ripup_pass(b, out, left, iters, log, passes=1)
        b = drc_repair(b, out, iters, log)
        gndfix.remove_dangling(b, out, log=log, locked=True)
    pour_pieces(b, log)
    log(f'left open: {len(left)}')
    return b, left


if __name__ == '__main__':
    main()
