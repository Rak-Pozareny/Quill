#!/usr/bin/env python3
"""Board B (Q20 keyboard) routing (checkpoint 4).

    python3 gen/route_b.py [--out FILE] [--iters N]

2 layers, 2.0 mm (as BBQ20KBD). JLCPCB 1-2 layer limits (research/jlc/capabilities_2026-10-17.md): 0.1 / 0.1 mm
track / space; vias: diameter >= hole + 0.1 mm (0.15 preferred) -> routing via 0.6 mm / 0.3 mm, the via BBQ20KBD
itself uses (JLC's 0.18 mm "PTH annular ring" row is for component holes; Board B has none). The only fast signal is
USB full speed (12 Mbit/s, RP2040), without impedance control (not needed at 12 Mbit/s; a 90 ohm pair over 1.9 mm of
FR-4 would be ~3 mm wide).

Steps: GND fan-out (gen/fanout.py); every connection, GND included, with the grid router (gen/groute.py), with local
rip-up and re-route around whatever it leaves open; GND pours on both sides over the outline with a stitching grid;
stitching vias the pours do not reach removed (gen/gndfix.py).
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
import math  # noqa: E402

import pcbnew  # noqa: E402
import fanout  # noqa: E402
import gndfix  # noqa: E402
import groute  # noqa: E402
import proute as R  # noqa: E402
import route_power  # noqa: E402

BOARD = os.path.join(ROOT, 'hw', 'board_b', 'q20_keyboard.kicad_pcb')
PRO = os.path.join(ROOT, 'hw', 'board_b', 'q20_keyboard.kicad_pro')

CLASSES = {          # name: (clearance, track, via_dia, via_drill)
    'Default': (0.12, 0.15, 0.6, 0.3),
    'PWR': (0.12, 0.20, 0.6, 0.3),      # all < 0.3 A (RP2040, level shifters, keyboard backlight); 0.4 mm-pitch pins
    'USB': (0.12, 0.20, 0.6, 0.3),      # full speed, not impedance controlled
}
PWR = ('VBUS_KBD', '+3V3', '+1V8', '+2V8', 'DVDD', 'MIC_VDD', 'LEDK', 'BACKLIGHT')


def write_project(pro, nets):
    p = json.load(open(pro))
    ns = p['net_settings']
    ns['classes'] = []
    for n, (c, t, vd, vh) in CLASSES.items():
        ns['classes'].append({'bus_width': 12, 'clearance': c, 'diff_pair_gap': 0.15, 'diff_pair_via_gap': 0.25,
                              'diff_pair_width': 0.2, 'line_style': 0, 'microvia_diameter': 0.3, 'microvia_drill': 0.1,
                              'name': n, 'pcb_color': 'rgba(0, 0, 0, 0.000)',
                              'priority': 2147483647 if n == 'Default' else list(CLASSES).index(n),
                              'schematic_color': 'rgba(0, 0, 0, 0.000)', 'track_width': t, 'tuning_profile': '',
                              'via_diameter': vd, 'via_drill': vh, 'wire_width': 6})
    assign = {}
    for n in nets:
        s = n.split('/')[-1]
        if s.startswith('USB_D'):
            assign[n] = ['USB']
        elif s in PWR:
            assign[n] = ['PWR']
    ns['netclass_patterns'] = []
    ns['netclass_assignments'] = assign
    r = p['board']['design_settings']['rules']
    r.update(min_clearance=0.1, min_track_width=0.1, min_via_diameter=0.6, min_via_annular_width=0.15,
             min_through_hole_diameter=0.3, min_hole_clearance=0.2, min_hole_to_hole=0.2, min_copper_edge_clearance=0.2,
             min_text_height=0.8, min_text_thickness=0.12)
    p['board']['design_settings']['rule_severities'].update(track_dangling='error', via_dangling='error',
                                                             lib_footprint_issues='ignore', lib_footprint_mismatch='ignore')
    json.dump(p, open(pro, 'w'), indent=2)
    open(os.path.splitext(pro)[0] + '.kicad_dru', 'w').write(
        '(version 1)\n'
        '(rule "PTH pad hole to copper (JLC 0.28)" (condition "A.Type == \'Pad\' && A.Pad_Type == \'Through-hole\'")'
        ' (constraint hole_clearance (min 0.28mm)))\n'
        '(rule "NPTH to copper (JLC 0.2)" (condition "A.Pad_Type == \'NPTH, mechanical\'")'
        ' (constraint hole_clearance (min 0.2mm)))\n'
        '(rule "pad holes (JLC 0.45)" (condition "A.Type == \'Pad\' && B.Type == \'Pad\'")'
        ' (constraint hole_to_hole (min 0.45mm)))\n')


VIA = (0.6, 0.3)
EP_VIAS = [(0, 0), (-0.85, -0.85), (0.85, -0.85), (-0.85, 0.85), (0.85, 0.85)]   # RP2040 exposed pad (3.2 mm), GND


def rp2040_ep(f, fp, p):
    """the RP2040's exposed pad is its only GND: five vias in the pad (2-layer board: open vias, tented on the top)"""
    c = R.to_mm(p.GetPosition())
    for dx, dy in EP_VIAS:
        f.add_via(c[0] + dx, c[1] + dy)


R.ESCAPE_LAND = VIA[0] / 2


def gnd_fanout(b, log=print):
    """GND fan-out (gen/fanout.py): stub + via at every SMD GND pad (0.15 mm from other copper: the autorouter keeps
    0.13 mm from it); the keyboard connector's GND vias between its pad rows (under the receptacle body, tented) so its
    signal pins keep their outward escapes; RP2040 TESTEN (pin 19) straight into the exposed pad"""
    f = fanout.Fanout(b, VIA, layers=('F', 'B'), clearance=0.15, in_pad=False, inward=('J201',),
                      special={('U102', '57'): rp2040_ep}, log=log)
    f.run()                              # a pad without room is joined by the GND routing that follows
    return f


def gnd_pours(b, outline):
    gnd = route_power.full(b, 'GND')
    for L in ('F', 'B'):
        route_power.zone(b, gnd, L, outline, prio=0, clearance=0.25, min_w=0.25, thermal=True, name=f'GND {L}')


def net_class(net):
    s = net.split('/')[-1]
    if s.startswith('USB_D'):
        return 'USB'
    if s in PWR:
        return 'PWR'
    return 'Default'


def rules(skip_zone_nets=()):
    """grid-router rules (gen/groute.py) from the net classes above and the JLC 2-layer limits"""
    return groute.Rules(('F', 'B'), VIA, lambda n, L: CLASSES[net_class(n)][1], lambda n: CLASSES[net_class(n)][0],
                        h_def=CLASSES['Default'][1] / 2, c_def=CLASSES['Default'][0], hole_clr=0.2, pth_clr=0.28,
                        npth_clr=0.2, hole_to_hole=0.2, edge=0.2, res=0.05, margin=0.02, via_in_pad=False,
                        skip_zone_nets=skip_zone_nets)


def grid_route(b, out, iters, skip_nets=('GND',), skip_zone_nets=(), narrow=(), log=print):
    """route what KiCad reports open with the negotiated-congestion grid router; returns the connections left and
    the spots where their last paths met other nets"""
    pcbnew.SaveBoard(out, b)
    conns, skipped = groute.open_connections(b, out, ('F', 'B'), skip_nets=skip_nets, log=log)
    if not conns:
        return [], [], set()
    g = groute.Grid(b, rules(skip_zone_nets), log=log)
    r = groute.Router(g, conns, log=log, narrow=narrow)
    r.run(iters=iters)
    done = r.commit()
    log(f'grid router: {len(done)} of {len(conns)} connections committed')
    groute.merge_close_vias(b, VIA[1], 0.2, log=log)
    return ([conns[k] for k in range(len(conns)) if k not in done] + skipped, r.hotspots(done),
            {conns[k][0] for k in r.failed})



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=BOARD)
    ap.add_argument('--iters', type=int, default=40)
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    pro = os.path.splitext(out)[0] + '.kicad_pro'
    src = pcbnew.LoadBoard(BOARD)
    nets = R.net_names(src)
    if out != os.path.abspath(BOARD):
        shutil.copy(BOARD, out)
        shutil.copy(PRO, pro)
    write_project(pro, nets)
    n = R.strip_routing_file(out)                   # start from the placement
    if n:
        print(f'removed {n} tracks, vias and zones of an earlier run')
    b = pcbnew.LoadBoard(out)
    ds = b.GetDesignSettings()
    ds.m_MinClearance, ds.m_TrackMinWidth = pcbnew.FromMM(0.1), pcbnew.FromMM(0.1)
    ds.m_ViasMinSize, ds.m_ViasMinAnnularWidth = pcbnew.FromMM(0.6), pcbnew.FromMM(0.15)
    ds.m_MinThroughDrill, ds.m_HoleClearance = pcbnew.FromMM(0.3), pcbnew.FromMM(0.2)
    ds.m_HoleToHoleMin, ds.m_CopperEdgeClearance = pcbnew.FromMM(0.2), pcbnew.FromMM(0.2)
    ds.m_SolderMaskMinWidth = pcbnew.FromMM(0.1)
    log = lambda m: print(m, flush=True)
    # GND: a stub and via at every GND pad first; pours on both sides over the BBQ20KBD outline and a stitching grid
    # after the routing
    outl = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(outl, False)
    o = outl.Outline(0)
    pts = [R.to_mm(o.CPoint(i)) for i in range(o.PointCount())]
    gnd_fanout(b, log)
    # GND is routed like any other net between its pads and fan-out vias, so its connectivity does not depend on
    # how the pours added afterwards fragment; the pours only add copper
    narrow = set()
    left, hot, stuck = grid_route(b, out, 3 * a.iters, skip_nets=(), log=log)
    # what the first pass could not settle: rip up the router's copper around the conflicts and route again
    for _ in range(4):
        if not left:
            break
        # around conflicts, and around both ends of a connection that found no path at all
        hot += [e[:2] for n, a0, z0 in left if n in stuck for e in (a0, z0)]
        gndfix.rip_up_near(b, {n for n, _, _ in left}, hot, radius=1.0, log=log)
        narrow |= stuck                  # a net with no path at its class width tries the default width
        left, hot, stuck = grid_route(b, out, a.iters, skip_nets=(), narrow=narrow, log=log)
    log(f'left open: {len(left)}')
    gnd_pours(b, pts)
    before = {R.to_mm(t.GetPosition()) for t in R.tracks(b) if isinstance(t, pcbnew.PCB_VIA)}
    n = route_power.stitch(b, route_power.full(b, 'GND'), pts, pitch=3.0, via=VIA, clearance=0.25, res=0.05)
    log(f'GND stitching: {n} vias')
    stitched = [R.to_mm(t.GetPosition()) for t in R.tracks(b) if isinstance(t, pcbnew.PCB_VIA) and
                R.to_mm(t.GetPosition()) not in before]
    gndfix.prune_dangling(b, stitched, log=log)
    gndfix.solid_where_starved(b, out, log=log)
    gndfix.remove_dangling(b, out, log=log, locked=True)      # dead ends carry nothing (a GND via on one layer too)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(out, b)
    write_project(pro, nets)
    log(f'saved {out}')
    groute.log_drc(out, log)


if __name__ == '__main__':
    main()
