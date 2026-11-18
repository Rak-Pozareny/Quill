"""Differential pairs of Board A, routed with gen/proute.py before Freerouting.

Each pair: a coupled section (one fat centreline, offset into the two traces, impedance geometry per layer from the JLC
solver) between two launch points just outside the pads, and four short single-trace breakouts from the pads to the
ends of the coupled section (these may change layer, which also untwists a pair whose P/N order flips between the
ends).
"""
import math

import pcbnew

import proute as R
from route_rules import GEOM

VIA = (0.4, 0.2)                  # routing via: 0.4 mm pad, 0.2 mm drill (0.1 annular: hole-to-copper 0.2 with 0.1 clearance)
VIA_PITCH = 0.52                  # pair vias, centre to centre (0.12 mm copper gap; each hole 0.22 mm from the other via's
                                  # copper: JLC via hole to copper 0.2)
VIA_STRAIGHT = 0                  # cells straight on either side of a pair's layer change (proute.astar via_straight):
                                  # 4 and 8 were tried and made the coupled paths chain layer changes in tight spots;
                                  # the exact P/N check and _straighten() handle vias on corners instead
MAX_LAYER_CHANGES = 4             # a coupled section with more is rejected (an artefact, never a good route)
CLR = 0.12                        # clearance used while routing (net class 0.12) ...
MARGIN = 0.03                     # ... plus grid quantisation margin
PAIR_GAP_MIN = 0.09               # DRC rule inside a coupled pair (route_rules.write_dru)
PARTNER_CLR = (0.10, 0.12)        # breakout to the other trace of its pair, rasterised on a 0.025 mm grid (a segment
                                  # between cell centres may come 0.009 mm closer): tried in turn, each result checked
                                  # exactly against PAIR_GAP_MIN
RES = 0.05


def geom(cls, L):
    w, s = GEOM[cls]['out' if L in ('F', 'B') else 'inn']
    return w, s


def pad_of(board, ref_pad):
    ref, num = ref_pad.split('.')
    fp = board.FindFootprintByReference(ref)
    for p in R.pads(fp):
        if p.GetNumber() == num:
            return fp, p
    raise KeyError(ref_pad)


def pad_layer(fp):
    return 'B' if fp.IsFlipped() else 'F'


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def dir_index(e):
    a = math.atan2(e[1], e[0])
    return int(round(a / (math.pi / 4))) % 8


class PairRouter:
    def __init__(self, board, log=print):
        self.b = board
        self.log = log
        self.done = {}                     # pair name -> board items added
        self.loose_used = {}               # pair name -> True when routed as two separate traces
        self.skew = {}                     # pair name -> P / N skew left after tuning it as routed (tune_now)
        self.max_expand = 4_000_000        # A* budget of a coupled path (raised for the final retry)
        self.keepouts = []                 # (layer | 'via', polygon) reserved for other pairs (route_all: corridors)
        self.corridors = {}                # pair name -> its reserved fan-out corridors
        self.full = {}                     # short net name -> full (hierarchical) net name
        for n in R.net_names(board):
            n = str(n)
            self.full.setdefault(n.split('/')[-1], n)

    def net(self, short):
        return self.full[short]

    def route(self, name, pnet, nnet, cls, start, end, layers=None, loose=False, margins=(6.0, 12.0), **kw):
        """try layer sets in turn: same outer layer for short pairs, L3, L4, then both inner layers with via pairs,
        then every layer"""
        # the fan-out corridors reserved for the other pairs are obstacles to this one
        self.keepouts = [k for other, ks in self.corridors.items() if other != name for k in ks]
        pnet, nnet = self.net(pnet), self.net(nnet)
        if layers:
            tries = [(tuple(layers), kw.pop('allow_vias', False))]
        else:
            fa, _ = pad_of(self.b, start[0])
            fz, _ = pad_of(self.b, end[0])
            pa, pz = R.to_mm(_pad_pos(self.b, start[0])), R.to_mm(_pad_pos(self.b, end[0]))
            tries = []
            if pad_layer(fa) == pad_layer(fz) and math.dist(pa, pz) < 8.0:
                tries.append(((pad_layer(fa),), False))
            tries += [(('In2',), False), (('In3',), False), (('In2', 'In3'), True), (('In2', 'In3', 'F', 'B'), True)]
        for lay, vias in tries:
            for margin in margins:
                r = self.route_on(name, pnet, nnet, cls, start, end, layers=lay, allow_vias=vias, margin=margin, **kw)
                if r is not None:
                    return r
        # last resort where the pair table allows it (short stubs to ESD arrays, test pads, AC capacitors):
        # the two traces routed separately
        if loose:
            added = []
            for pp, zz, net in ((start[0], end[0], pnet), (start[1], end[1], nnet)):
                fa, pa = pad_of(self.b, pp)
                fz, pz = pad_of(self.b, zz)
                a, z = R.to_mm(pa.GetPosition()), R.to_mm(pz.GetPosition())
                r = self.single(net, cls, (a[0], a[1], pad_layer(fa)), (z[0], z[1], pad_layer(fz)), margin=5.0)
                if r is None:
                    for it in added:
                        R.remove(self.b, it)
                    self.log(f'{name}: FAILED (coupled and separate)')
                    return False
                added += r
            self.done[name] = added
            self.loose_used[name] = True
            self.log(f'{name}: routed as two separate traces (short connection)')
            return True
        self.log(f'{name}: FAILED on every layer set ({getattr(self, "why", "")})')
        return False

    def route_on(self, name, pnet, nnet, cls, start, end, layers=('In2',), d_launch=(1.2, 1.2), layer_cost=None,
                 allow_vias=False, margin=6.0, fan=(False, False), fan_off=None, thru=(False, False), twist=True,
                 launch_no_via=(0.0, 0.0), room=None):
        """start / end: (P pad 'REF.n', N pad 'REF.n', exit direction (dx, dy)[, coupled direction]). None = no
        coupled path found (nothing added); True = routed.
        fan: per end, drop both pads to the inner layers through a staggered via pair right at the pad ends (fine-pitch
        board-to-board connector rows), so the coupled section starts below the connector"""
        b = self.b
        ends = []
        fan_items = []
        for k, (end_, dl) in enumerate(zip((start, end), d_launch)):
            pp, pn, e = end_[:3]
            c = end_[3] if len(end_) > 3 else e          # direction of the coupled section at this end
            fpp, padp = pad_of(b, pp)
            fpn, padn = pad_of(b, pn)
            P, N = R.to_mm(padp.GetPosition()), R.to_mm(padn.GetPosition())
            M = ((P[0] + N[0]) / 2, (P[1] + N[1]) / 2)
            el = math.hypot(*e)
            e = (e[0] / el, e[1] / el)
            cl = math.hypot(*c)
            c = (c[0] / cl, c[1] / cl)
            if c != e:
                dl = 0.8                                  # turn back under the pads: launch just past them
            Lp, Ln = pad_layer(fpp), pad_layer(fpn)
            launch = (M[0] + e[0] * dl, M[1] + e[1] * dl)
            # the trace with the via nearer its pad has the longer breakout: mirror the stagger at the second end so
            # the two ends cancel instead of adding up
            offs = fan_off[k] if fan_off and fan_off[k] else FAN_OPTS
            if k == 1:
                offs = tuple((far, near) for near, far in offs)
            f = self.fan_vias(pnet, nnet, padp, padn, e, geom(cls, pad_layer(fpp))[0], offsets=offs) if fan[k] else None
            if thru[k]:
                # two-row staggered connector (FH35C): each pin straight out along e on its pad layer, the rear-row
                # pin between two front-row pads (the connector is drawn for it), both stubs to 0.3 mm past the
                # front row; the pair starts there
                wl = geom(cls, Lp)[0]
                proj = []
                for pad, Q in ((padp, P), (padn, N)):
                    pb = pad.GetBoundingBox()
                    ext = (pcbnew.ToMM(pb.GetWidth()) if abs(e[0]) > abs(e[1]) else pcbnew.ToMM(pb.GetHeight())) / 2
                    proj.append((Q[0] - M[0]) * e[0] + (Q[1] - M[1]) * e[1] + ext)
                reach = max(proj) + 0.3
                stubs = []
                for net, Q in ((pnet, P), (nnet, N)):
                    t = reach - ((Q[0] - M[0]) * e[0] + (Q[1] - M[1]) * e[1])
                    Q2 = (Q[0] + e[0] * t, Q[1] + e[1] * t)
                    fan_items += R.add_track(b, net, Lp, [Q, Q2], wl)
                    stubs.append(Q2)
                P, N = stubs
                M = ((P[0] + N[0]) / 2, (P[1] + N[1]) / 2)
                launch = (M[0] + c[0] * 0.9, M[1] + c[1] * 0.9)
                ends.append(dict(P=P, N=N, M=M, e=c, Lp=Lp, Ln=Ln, dl=0.9, launch=launch))
                continue
            if f is not None:
                (P, N), items = f
                fan_items += items
                Lp = Ln = None                            # the breakout continues on the coupled layer
                M = ((P[0] + N[0]) / 2, (P[1] + N[1]) / 2)
                # 0.65 mm past the via furthest along the coupled direction, so the coupled traces clear both vias
                reach = max((v[0] - M[0]) * c[0] + (v[1] - M[1]) * c[1] for v in (P, N)) + 0.65
                launch = (M[0] + c[0] * reach, M[1] + c[1] * reach)
            ends.append(dict(P=P, N=N, M=M, e=c, Lp=Lp, Ln=Ln, dl=dl, launch=launch))
        s, t = ends
        xs = [s['launch'][0], t['launch'][0], s['P'][0], s['N'][0], t['P'][0], t['N'][0]]
        ys = [s['launch'][1], t['launch'][1], s['P'][1], s['N'][1], t['P'][1], t['N'][1]]
        win = R.Window(max(-1.0, min(xs) - margin), max(-1.0, min(ys) - margin), min(96.0, max(xs) + margin),
                       min(66.0, max(ys) + margin), RES)
        half = {L: geom(cls, L)[0] + geom(cls, L)[1] / 2 for L in R.ROUTE_LAYERS}
        own = {b.FindNet(pnet).GetNetCode(), b.FindNet(nnet).GetNetCode()}
        via_r = VIA_PITCH / 2 + VIA[0] / 2
        # the pair's own copper already on the board (its fan-out vias and stubs, the other section of a pair split at
        # a test point or ESD array) is an obstacle to the coupled section: a P via or trace under the N trace
        solid = [t for t in R.tracks(b) if t.GetNetCode() in own]
        # room=(net name prefix, mm): the coupled section keeps that much more from those nets, so the length tuning
        # has room for its bumps between them (D100)
        net_clr = None
        if room:
            net_clr = {code: CLR + MARGIN + room[1] for nm, code in ((str(n).split('/')[-1], nn.GetNetCode())
                       for n, nn in b.GetNetsByName().items()) if nm.startswith(room[0]) and code not in own}
        obs = R.Obstacles(b, win, own, half, CLR + MARGIN, via_r=via_r, escapes='coarse', solid=solid,
                          extra_keepouts=self.keepouts, net_clr=net_clr)
        cost = layer_cost or {L: (1.0 if L.startswith('In') else 1.25) for L in layers}
        cost = {L: c for L, c in cost.items() if L in layers}
        for E in (s, t):
            for L in layers:
                obs.clear_disk(L, E['launch'][0], E['launch'][1], 0.0)
        da, dz = dir_index(s['e']), dir_index((-t['e'][0], -t['e'][1]))
        # a pass-through end starts / ends on its stubs' layer (no room for vias between the stubs)
        la = [s['Lp']] if thru[0] else layers
        lz = [t['Lp']] if thru[1] else layers
        path = R.astar(obs, [(s['launch'][0], s['launch'][1], L, d) for L in la for d in (da, (da + 1) % 8, (da - 1) % 8)],
                       [(t['launch'][0], t['launch'][1], L, d) for L in lz for d in (dz, (dz + 1) % 8, (dz - 1) % 8)],
                       cost, via_cost=1.5 / RES, allow_vias=allow_vias, max_expand=self.max_expand,
                       via_straight=VIA_STRAIGHT,
                       # no layer change right at a launch point, where one trace would pass the other's via (table)
                       no_via=[(E['launch'][0], E['launch'][1], r) for E, r in ((s, launch_no_via[0]),
                                                                              (t, launch_no_via[1])) if r])
        if path is None:
            for it in fan_items:
                R.remove(b, it)
            self.why = (f'no coupled path on {layers} {getattr(R.astar, "last", "")}: launch {s["launch"]} free='
                        f'{[obs.free(L, *win.ij(*s["launch"])) for L in layers]} -> {t["launch"]} free='
                        f'{[obs.free(L, *win.ij(*t["launch"])) for L in layers]}, fan {[bool(x) for x in fan]}')
            return None
        # a run of one point is a layer change right at a launch (or two stacked vias): no direction to offset the
        # pair from, so drop it; the breakout (or the via of the next run) changes layer instead
        runs = [r for r in R.simplify(path) if len(r[1]) >= 2]
        # one-cell steps at the very ends (the turn onto the launch direction) fold the offset traces into each other:
        # the coupled section ends on its last real segment instead, the breakouts take it from there (not at a
        # pass-through end, whose stubs run straight into the launch point)
        if runs:
            L0, p0 = runs[0]
            p0 = list(p0)
            while not thru[0] and len(p0) > 2 and math.dist(p0[0], p0[1]) < 0.35:
                p0.pop(0)
            runs[0] = (L0, p0)
            L1, p1 = runs[-1]
            p1 = list(p1)
            while not thru[1] and len(p1) > 2 and math.dist(p1[-1], p1[-2]) < 0.35:
                p1.pop()
            runs[-1] = (L1, p1)
        if not runs:
            for it in fan_items:
                R.remove(b, it)
            self.why = 'coupled path has no straight run'
            return None
        if len(runs) - 1 > MAX_LAYER_CHANGES:
            for it in fan_items:
                R.remove(b, it)
            self.why = f'{len(runs) - 1} layer changes'
            return None
        self._straighten(runs, cls, pnet, nnet)
        # P side from the start pads: left of travel <=> cross(e, P - M) < 0 (y down)
        p_left = cross(s['e'], (s['P'][0] - s['M'][0], s['P'][1] - s['M'][1])) < 0
        a_end = (-t['e'][0], -t['e'][1])
        p_left_end = cross(a_end, (t['P'][0] - t['M'][0], t['P'][1] - t['M'][1])) < 0
        p_left0, p_left_end0 = p_left, p_left_end
        if thru[1] and not thru[0]:          # the pass-through end fixes the order; any twist goes to the other end
            p_left, p_left_end = p_left_end, p_left
        added = list(fan_items)
        ends_xy = {}
        # P and N in a different order at the two ends: twist at a layer change if one has a straight approach
        tw = self._twist_at(runs, pnet, nnet, cls, 1 if p_left0 else -1) if p_left0 != p_left_end0 and twist else None
        for k, (L, pts) in enumerate(runs):
            w, sp = geom(cls, L)
            o = (w + sp) / 2
            s0 = 1 if p_left else -1
            if tw:                               # start order up to the twist, end order after it
                s0 = (1 if p_left0 else -1) * (-1 if k >= tw['t'] else 1)
            for which, net, sign in (('P', pnet, s0), ('N', nnet, -s0)):
                line = R.offset_polyline(pts, sign * o)
                if tw and k == tw['t'] - 1:      # into the twist
                    line = _cut_end(line, tw['cut_in'][which]) + [tw['via'][which]]
                    added.append(R.add_via(b, net, *tw['via'][which], VIA[0], VIA[1]))
                elif tw and k == tw['t']:        # out of the twist
                    line = [tw['via'][which]] + tw['lead_out'][which] + _cut_start(line, tw['cut_out'][which])
                    if k < len(runs) - 1:
                        vx, vy = _via_xy(pts, sign)
                        line = line + [(vx, vy)]
                        added.append(R.add_via(b, net, vx, vy, VIA[0], VIA[1]))
                else:
                    if k > 0:                       # from the via of this trace
                        vx, vy = _via_xy(runs[k - 1][1], sign)
                        line = [(vx, vy)] + line
                    if k < len(runs) - 1:
                        vx, vy = _via_xy(pts, sign)
                        line = line + [(vx, vy)]
                        added.append(R.add_via(b, net, vx, vy, VIA[0], VIA[1]))
                added += R.add_track(b, net, L, line, w)
                if k == 0:
                    ends_xy[(which, 0)] = (line[0], L)
                if k == len(runs) - 1:
                    ends_xy[(which, 1)] = (line[-1], L)
        if tw:
            p_left_end = p_left                  # the breakouts no longer untwist anything
        # breakouts: pad -> end of its coupled trace (may change layer, which also undoes a P/N swap)
        for idx, E in ((0, s), (1, t)):
            for which, net, pad_xy, pl in (('P', pnet, E['P'], E['Lp']), ('N', nnet, E['N'], E['Ln'])):
                (tx, ty), tl = ends_xy[(which, idx)]
                pl = pl or tl
                other = nnet if which == 'P' else pnet
                oc = b.FindNet(other).GetNetCode()
                r = None
                for pc in PARTNER_CLR:
                    r = self.single(net, cls, (pad_xy[0], pad_xy[1], pl), (tx, ty, tl), partner=(oc, pc))
                    if r is None or R.clear_of(b, r, {oc}, PAIR_GAP_MIN + 0.002):
                        break
                    for it in r:
                        R.remove(b, it)
                    r = None
                if r is None:
                    self.why = f'breakout {which}{idx} from {pad_xy} ({pl}) to {(tx, ty, tl)}'
                    for it in added:
                        R.remove(b, it)
                    self.log(f'{name}: {"/".join(layers)} breakout {which}{idx} blocked, retrying')
                    return None
                added += r
        # the whole pair, exactly (KiCad shapes): P's copper against N's, 0.09 mm, and the via holes
        pc = b.FindNet(pnet).GetNetCode()
        if not R.clear_of(b, [it for it in added if it.GetNetCode() == pc], {b.FindNet(nnet).GetNetCode()},
                          PAIR_GAP_MIN + 0.002):
            self.why = 'P and N closer than the pair rule somewhere (exact check)'
            for it in added:
                R.remove(b, it)
            if tw:                               # the twist's vias are the usual culprit: untwist in the breakout
                return self.route_on(name, pnet, nnet, cls, start, end, layers=layers, d_launch=d_launch,
                                     layer_cost=layer_cost, allow_vias=allow_vias, margin=margin, fan=fan,
                                     fan_off=fan_off, thru=thru, twist=False, launch_no_via=launch_no_via)
            self.log(f'{name}: {"/".join(layers)} fails the exact P/N check, retrying')
            return None
        swap = p_left != p_left_end and not tw
        self.log(f'{name}: coupled {"/".join(L for L, _ in runs)}, {len(runs) - 1} via pairs'
                 f'{", P/N order flips (untwisted in the breakout)" if swap else ""}')
        self.done[name] = added
        return True

    def _straighten(self, runs, cls, pnet, nnet):
        """a layer change on a corner puts one trace's outgoing segment beside the other trace's via: move the change
        back along the straight incoming run (0.7-1.2 mm) where the outgoing layer is free, so the via pair sits on a
        straight stretch. Changes `runs` in place"""
        b = self.b
        own = {b.FindNet(pnet).GetNetCode(), b.FindNet(nnet).GetNetCode()}
        for t in range(1, len(runs)):
            Lin, pin = runs[t - 1]
            Lout, pout = runs[t]
            T = pin[-1]
            lin, lo = math.dist(pin[-2], T), math.dist(T, pout[1])
            if lin < 1e-6 or lo < 1e-6:
                continue
            u = ((T[0] - pin[-2][0]) / lin, (T[1] - pin[-2][1]) / lin)
            uo = ((pout[1][0] - T[0]) / lo, (pout[1][1] - T[1]) / lo)
            if abs(u[0] * uo[0] + u[1] * uo[1] - 1) < 1e-6:
                continue                                   # straight through already
            half = geom(cls, Lout)[0] + geom(cls, Lout)[1] / 2
            for back in (0.7, 0.9, 1.2):
                if lin - back < 0.35:
                    break
                T2 = (T[0] - u[0] * back, T[1] - u[1] * back)
                win = R.Window(min(T[0], T2[0]) - 1.5, min(T[1], T2[1]) - 1.5, max(T[0], T2[0]) + 1.5,
                               max(T[1], T2[1]) + 1.5, RES)
                obs = R.Obstacles(b, win, own, {L: half for L in R.ROUTE_LAYERS}, CLR + MARGIN, layers=(Lout,),
                                  via_r=VIA[0] / 2)
                n = max(2, int(back / 0.02))
                if not all(obs.free(Lout, *win.ij(T2[0] + (T[0] - T2[0]) * i / n, T2[1] + (T[1] - T2[1]) * i / n))
                           for i in range(n + 1)):
                    continue
                vias = [_via_xy([pin[-2], T2], sg) for sg in (1, -1)]
                if not all(obs.via_free(*win.ij(*v)) for v in vias):
                    continue
                runs[t - 1] = (Lin, list(pin[:-1]) + [T2])
                runs[t] = (Lout, [T2] + list(pout))
                break

    def _twist_at(self, runs, pnet, nnet, cls, s0, D=0.6, a=0.3):
        """P/N twist at a layer change of the coupled path: both vias on P's side, P's 0.6 mm before the change
        and N's 0.6 mm after it, so each trace crosses over while the other one is on the other layer (equal extra
        length within ~0.05 mm, no detour). Needs a straight, collinear approach and exit of >= 1.3 mm and room for
        the two vias; the layer change may be moved back along a long straight approach (exit layer free there).
        Changes `runs` in place when it moves the layer change. Returns the geometry, or None"""
        b = self.b
        own = {b.FindNet(pnet).GetNetCode(), b.FindNet(nnet).GetNetCode()}
        for t in range(1, len(runs)):
            Lin, Lout = runs[t - 1][0], runs[t][0]
            pin0, pout0 = runs[t - 1][1], runs[t][1]
            T0 = pin0[-1]
            li0, lo0 = math.dist(pin0[-2], T0), math.dist(T0, pout0[1])
            u = ((T0[0] - pin0[-2][0]) / li0, (T0[1] - pin0[-2][1]) / li0)
            uo = ((pout0[1][0] - T0[0]) / lo0, (pout0[1][1] - T0[1]) / lo0)
            straight_exit = lo0 >= 1.3 and abs(u[0] * uo[0] + u[1] * uo[1] - 1) < 1e-6
            for back in ((0.0,) if straight_exit else ()) + (1.5, 2.0, 2.5, 3.0):
                if li0 - back < 1.3:
                    break
                T = (T0[0] - u[0] * back, T0[1] - u[1] * back)
                if back:
                    half = geom(cls, Lout)[0] + geom(cls, Lout)[1] / 2
                    win = R.Window(min(T[0], T0[0]) - 1.5, min(T[1], T0[1]) - 1.5, max(T[0], T0[0]) + 1.5,
                                   max(T[1], T0[1]) + 1.5, RES)
                    obs = R.Obstacles(b, win, own, {L: half for L in R.ROUTE_LAYERS}, CLR + MARGIN, layers=(Lout,))
                    n = max(2, int(back / 0.02))
                    if not all(obs.free(Lout, *win.ij(T[0] + (T0[0] - T[0]) * i / n, T[1] + (T0[1] - T[1]) * i / n))
                               for i in range(n + 1)):
                        continue
                nrm = R._normal(pin0[-2], T0)                    # offset_polyline's left of travel
                o_out = sum(geom(cls, Lout)) / 2
                P = lambda d, lat: (T[0] + u[0] * d + nrm[0] * lat, T[1] + u[1] * d + nrm[1] * lat)
                via = {'P': P(-D, s0 * a), 'N': P(D, s0 * a)}
                win = R.Window(T[0] - 2, T[1] - 2, T[0] + 2, T[1] + 2, RES)
                obs = R.Obstacles(b, win, own, 0.06, CLR + MARGIN, via_r=VIA[0] / 2, extra_keepouts=self.keepouts)
                if not all(obs.via_free(*win.ij(*v)) for v in via.values()):
                    continue
                if back:
                    runs[t - 1] = (Lin, list(pin0[:-1]) + [T])
                    runs[t] = (Lout, [T] + list(pout0))
                return dict(t=t, via=via,
                            cut_in={'P': D + 0.4, 'N': 0.2},       # P leaves its offset 1.0 mm early, N 0.2 mm
                            lead_out={'P': [P(-0.2, -s0 * o_out)], 'N': []},
                            cut_out={'P': 0.0, 'N': D + 0.2})
        return None

    def fan_vias(self, pnet, nnet, padp, padn, e, width, offsets=None):
        """staggered via pair at the free ends of two adjacent pads (0.4 mm pitch rows): one via 0.30 mm past its pad
        end, the other 0.80 mm past, each on its pad's axis, joined by straight stubs. Returns ((P via, N via), items)
        or None when no arrangement fits"""
        b = self.b
        P, N = R.to_mm(padp.GetPosition()), R.to_mm(padn.GetPosition())
        layer = 'B' if padp.GetParentFootprint().IsFlipped() else 'F'
        bb = padp.GetBoundingBox()
        ext = (pcbnew.ToMM(bb.GetWidth()) if abs(e[0]) > abs(e[1]) else pcbnew.ToMM(bb.GetHeight())) / 2
        opts = offsets or FAN_OPTS
        reach = ext + max(max(o) for o in opts) + 1.0
        xs = [P[0], N[0], P[0] + e[0] * reach, N[0] + e[0] * reach]
        ys = [P[1], N[1], P[1] + e[1] * reach, N[1] + e[1] * reach]
        win = R.Window(min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1, 0.025)
        own = {padp.GetNetCode(), padn.GetNetCode()}
        obs = R.Obstacles(b, win, own, width / 2, CLR + 0.015, via_r=VIA[0] / 2, escapes='coarse',
                          extra_keepouts=self.keepouts)

        def stub_free(a, z):
            n = max(2, int(math.dist(a, z) / 0.02))
            return all(obs.free(layer, *win.ij(a[0] + (z[0] - a[0]) * i / n, a[1] + (z[1] - a[1]) * i / n))
                       for i in range(n + 1))
        for near, far in opts:
            vp = (P[0] + e[0] * (ext + near), P[1] + e[1] * (ext + near))
            vn = (N[0] + e[0] * (ext + far), N[1] + e[1] * (ext + far))
            if all(obs.via_free(*win.ij(*v)) for v in (vp, vn)) and stub_free(P, vp) and stub_free(N, vn):
                items = []
                for net, pad_xy, v in ((pnet, P, vp), (nnet, N, vn)):
                    items += R.add_track(b, net, layer, [pad_xy, v], width)
                    items.append(R.add_via(b, net, v[0], v[1], VIA[0], VIA[1]))
                return (vp, vn), items
        return None

    def single(self, net, cls, a, z, layers=('F', 'In2', 'In3', 'B'), margin=3.0, partner=None):
        """single trace from a = (x, y, L) to z = (x, y, L), pair-class width per layer, vias allowed.
        Returns the added items, or None"""
        net = self.full.get(net, net)
        b = self.b
        xs, ys = [a[0], z[0]], [a[1], z[1]]
        win = R.Window(min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin, 0.025)
        half = {L: (geom(cls, L)[0] if cls in GEOM else 0.1) / 2 for L in R.ROUTE_LAYERS}
        own = {b.FindNet(net).GetNetCode()}
        obs = R.Obstacles(b, win, own, half, CLR + 0.015, via_r=VIA[0] / 2, escapes='coarse',
                          extra_keepouts=self.keepouts,
                          net_clr=({partner[0]: partner[1]} if partner else None))
        for L in layers:
            obs.clear_disk(L, a[0], a[1], 0.0)
            obs.clear_disk(L, z[0], z[1], 0.0)
        cost = {L: (1.0 if L == a[2] or L == z[2] else 1.6) for L in layers}
        path = R.astar(obs, [(a[0], a[1], a[2], None)], [(z[0], z[1], z[2], None)], cost, via_cost=0.6 / 0.025,
                       turn_cost=0.2)
        if path is None:
            return None
        runs = R.simplify(path)
        added = []
        for k, (L, pts) in enumerate(runs):
            w = geom(cls, L)[0] if cls in GEOM else 0.1
            pts = list(pts)
            if k == 0:
                pts[0] = (a[0], a[1])
            if k == len(runs) - 1:
                pts[-1] = (z[0], z[1])
            added += R.add_track(b, net, L, pts, w)
            if k < len(runs) - 1:
                added.append(R.add_via(b, net, pts[-1][0], pts[-1][1], VIA[0], VIA[1]))
        return added


def _pad_pos(board, ref_pad):
    return pad_of(board, ref_pad)[1].GetPosition()


def _cut_end(line, d):
    """polyline shortened by length d at its end"""
    out = list(line)
    while d > 1e-9 and len(out) >= 2:
        a, z = out[-2], out[-1]
        ln = math.dist(a, z)
        if ln > d:
            out[-1] = (z[0] + (a[0] - z[0]) * d / ln, z[1] + (a[1] - z[1]) * d / ln)
            return out
        out.pop()
        d -= ln
    return out


def _cut_start(line, d):
    return list(reversed(_cut_end(list(reversed(line)), d)))


def _via_xy(pts, sign):
    """via position of one trace of the pair at the end of a centreline run (beside the centreline end point)"""
    a, c = pts[-2], pts[-1]
    nx, ny = R._normal(a, c)
    return c[0] + sign * nx * VIA_PITCH / 2, c[1] + sign * ny * VIA_PITCH / 2


# ------------------------------------------------------------------------------------------------- pair table
# (name, P net, N net, class, start (P pad, N pad, exit), end (P pad, N pad, exit), options)
# Exit = direction in which the traces leave the pads (away from the part body / the cable side).
XP, XN, YP, YN = (1, 0), (-1, 0), (0, 1), (0, -1)
CSIA_COST = {'In2': 1.0, 'F': 1.25, 'In3': 1.4}     # CSI-A on L3, L4 only to get round something
CSIB_COST = {'In3': 1.0, 'F': 1.25, 'In2': 1.4}     # CSI-B on L4, L3 only to get round something
CSIA_UNDER = {'In3': 1.0, 'F': 1.25}                # CSI-A D1 / D0: on L4, under the clock (D119)
FH35 = dict(d_launch=(1.2, 2.6))            # FH35C: launch beyond the rear pad row
LOOSE = dict(loose=True)                    # short stub: may fall back to two separate traces
ROWS = ((1.25, 1.75), (1.75, 1.25), (1.45, 1.95), (1.95, 1.45))   # outer-row pads fanned east, vias between the rows
# LTE USB 3.0 from JP2: vias between the pin rows, then north under the connector on L4 (In3) only, clear of the CSI-A
# lanes (L3 east of and under the connector, whose length tuning needs the room) and the CSI-B lanes (L4 west of it);
# no further layer change: a via pair south-east of the connector pushed the CSI-A lanes together (D99)
USB3_NORTH = dict(fan_off=(ROWS, None), layers=('In3',))
EAST = ((2.5, 3.0), (3.0, 2.5), (2.8, 3.3), (3.3, 2.8),    # fan-out 2.5-4.1 mm out (past the Wi-Fi pin column);
        (3.6, 4.1), (4.1, 3.6))                            # the farther pairs leave room for a P/N twist
PAIRS = [
    # Layer plan at connector B (J302): the outer-row lanes leave west, the inner-row lanes east.
    # - CSI-B (J302 -> J705): fanned to L4 at the CM5 connector (CSI-A and DSI use L3), up to the top layer at the
    #   camera connector, whose rear-row pins leave straight between the front-row pads.
    # - CSI-A (inner row -> J704): vias 2.5-3.3 mm east of the connector, then west under it. The clock sits between
    #   D2 and D1 on connector B but last on the camera connector, so it crosses D1 and D0: D3, D2 and the clock
    #   run on L3 in connector B's order, D1 and D0 on L4 under the clock, one via pair per lane (D119; routed
    #   last, the clock went round D1 / D0's vias on L4 and came out 4.6-6.5 mm longer than the lanes, D117).
    #   The PCIe REFCLK, which crossed that area on L4, is routed after them (not in FIRST).
    # - LTE USB 3.0 (combo PHY2) leaves JP2's outer row east, its fan-out vias between the two pin rows (D97), then
    #   north between the rows on L4 and on under the module to the M.2 socket (D99).
    # PCIe 2.0 to the Wi-Fi module (combo PHY0) starts at JP3 (inner row, fanned north under the module) and runs to the
    # AC capacitors beside the module; the REFCLK goes to its capacitors on the top west of JP2.
    ('CSIB_CLK', 'CSIB_CLK_P', 'CSIB_CLK_N', 'MIPI100', ('J302.42', 'J302.40', XN), ('J705.18', 'J705.17', XP),
     dict(FH35, tune_now=True, layers=('In3', 'F', 'In2'), allow_vias=True, fan=(True, False), thru=(False, True), layer_cost=CSIB_COST)),
    ('CSIB_D1', 'CSIB_D1_P', 'CSIB_D1_N', 'MIPI100', ('J302.36', 'J302.34', XN), ('J705.12', 'J705.11', XP),
     dict(FH35, tune_now=True, layers=('In3', 'F', 'In2'), allow_vias=True, fan=(True, False), thru=(False, True), layer_cost=CSIB_COST)),
    ('CSIB_D0', 'CSIB_D0_P', 'CSIB_D0_N', 'MIPI100', ('J302.30', 'J302.28', XN), ('J705.15', 'J705.14', XP),
     dict(FH35, tune_now=True, layers=('In3', 'F', 'In2'), allow_vias=True, fan=(True, False), thru=(False, True), layer_cost=CSIB_COST)),
    ('CSIA_D3', 'CSIA_D3_P', 'CSIA_D3_N', 'MIPI100', ('J302.41', 'J302.39', XP, XN), ('J704.3', 'J704.2', XP),
     dict(FH35, tune_now=True, fan_off=(EAST, None), layers=('In2', 'F', 'In3'), allow_vias=True, thru=(False, True), layer_cost=CSIA_COST,
          launch_no_via=(0.0, 0.7))),
    ('CSIA_D2', 'CSIA_D2_P', 'CSIA_D2_N', 'MIPI100', ('J302.35', 'J302.33', XP, XN), ('J704.6', 'J704.5', XP),
     dict(FH35, tune_now=True, fan_off=(EAST, None), layers=('In2', 'F', 'In3'), allow_vias=True, thru=(False, True), layer_cost=CSIA_COST,
          launch_no_via=(0.0, 0.7))),
    ('CSIA_CLK', 'CSIA_CLK_P', 'CSIA_CLK_N', 'MIPI100', ('J302.29', 'J302.27', XP, XN), ('J704.18', 'J704.17', XP),
     dict(FH35, tune_now=True, fan_off=(EAST, None), layers=('In2', 'F'), allow_vias=True, thru=(False, True), layer_cost=CSIA_COST,
          launch_no_via=(0.0, 0.7))),
    ('CSIA_D1', 'CSIA_D1_P', 'CSIA_D1_N', 'MIPI100', ('J302.23', 'J302.21', XP, XN), ('J704.12', 'J704.11', XP),
     dict(FH35, tune_now=True, fan_off=(EAST, None), layers=('In3', 'F'), allow_vias=True, thru=(False, True), layer_cost=CSIA_UNDER,
          launch_no_via=(0.0, 0.7))),
    ('CSIA_D0', 'CSIA_D0_P', 'CSIA_D0_N', 'MIPI100', ('J302.17', 'J302.15', XP, XN), ('J704.15', 'J704.14', XP),
     dict(FH35, tune_now=True, fan_off=(EAST, None), layers=('In3', 'F'), allow_vias=True, thru=(False, True), layer_cost=CSIA_UNDER,
          launch_no_via=(0.0, 0.7))),
    # MIPI DSI: connector B -> display FPC J701 east of the CM5, under the module on L3. J701's pins are the panel's
    # mirrored (pad k = panel pin 31 - k, D118), so the lanes reach it in the reverse order of connector B's and cross
    # on L4.
    # the clock's P / N skew is tuned as it is routed: its P / N order flips on the way to the mirrored J701 and, tuned
    # after the four lanes, it had no room left for a bump (1.2 mm, D118)
    ('DSI_CLK', 'DSI_CLK_P', 'DSI_CLK_N', 'MIPI100', ('J302.89', 'J302.87', XP), ('J701.17', 'J701.18', XN),
     dict(tune_now=True)),
    # launched 1.5 mm from the display connector: at 1.2 mm the N via landed beyond the P via and N hooked back
    # round it (2.4 mm skew, D80)
    # D118: D0 lands on pads 23/24, over FB701 / R314 / C304 on the bottom: no via pair fits by the pads, so it leaves
    # J701 on the top layer (pass-through end) and changes layer where the bottom has room
    ('DSI_D0', 'DSI_D0_P', 'DSI_D0_N', 'MIPI100', ('J302.77', 'J302.75', XP), ('J701.23', 'J701.24', XN),
     dict(d_launch=(1.2, 1.5), thru=(False, True), layers=('In2', 'In3', 'F'), allow_vias=True,
          layer_cost={'In2': 1.0, 'In3': 1.3, 'F': 1.6})),
    ('DSI_D1', 'DSI_D1_P', 'DSI_D1_N', 'MIPI100', ('J302.83', 'J302.81', XP), ('J701.20', 'J701.21', XN), {}),
    ('DSI_D2', 'DSI_D2_P', 'DSI_D2_N', 'MIPI100', ('J302.95', 'J302.93', XP), ('J701.14', 'J701.15', XN), {}),
    ('DSI_D3', 'DSI_D3_P', 'DSI_D3_N', 'MIPI100', ('J302.96', 'J302.94', XN, XP), ('J701.11', 'J701.12', XN), {}),
    # PCIe 2.0 x1 to the Wi-Fi module
    ('PCIE_TX', 'PCIE_TX_P', 'PCIE_TX_N', 'PCIE85', ('J303.82', 'J303.84', YN), ('C609.1', 'C610.1', XP), {}),
    ('PCIE_RX', 'PCIE_RX_P', 'PCIE_RX_N', 'PCIE85', ('C611.2', 'C612.2', XP), ('J303.90', 'J303.88', YN), {}),
    # module side: each capacitor sits level with its module pin, 1 mm away (D96)
    ('WL_PCIE_RX', 'WL_PCIE_RX_P', 'WL_PCIE_RX_N', 'PCIE85', ('C609.2', 'C610.2', XN), ('U601.45', 'U601.44', XP),
     dict(LOOSE, d_launch=(0.3, 0.3))),
    ('WL_PCIE_TX', 'WL_PCIE_TX_P', 'WL_PCIE_TX_N', 'PCIE85', ('U601.47', 'U601.46', XP), ('C611.1', 'C612.1', XN),
     dict(LOOSE, d_launch=(0.3, 0.3))),
    ('PCIE_REFCLK', 'PCIE_REFCLK_P', 'PCIE_REFCLK_N', 'MIPI100', ('J303.76', 'J303.78', YN), ('C613.1', 'C614.1', YN), {}),
    ('WL_REFCLK', 'WL_REFCLK_P', 'WL_REFCLK_N', 'MIPI100', ('C613.2', 'C614.2', YP), ('U601.35', 'U601.33', YN), {}),
    # USB 3.0 / 2.0
    ('USB_OTG', 'USB_OTG_DP', 'USB_OTG_DN', 'USB90', ('J302.5', 'J302.3', XP, XN), ('L401.2', 'L401.3', YP), {}),
    # USB-C D+ / D- to the common-mode choke: from A6 / B7, the adjacent pins with D- on the north side as at the choke
    # (A6 / A7 would cross over on the way); A7 / B6, the ESD array D401 and the BC1.2 resistors R101 / R102 are
    # stubs for the grid router. Left to it as two single nets, D+ ran 17.8 mm to the choke and D- 9.1 mm in the
    # third D119 route (D116: 1.3 / about 6 mm). In the installed route the clean-up's pruning (route_tune.prune)
    # dropped D-'s pair section for a shorter path the grid router made by the ESD stub: 3.4 / 2.8 mm, uncoupled (D120)
    ('USBC', 'USBC_DP', 'USBC_DN', 'USB90', ('J101.A6', 'J101.B7', XP), ('L401.1', 'L401.4', YN), {}),
    ('USB3_RX', 'USB3_LTE_RX_P', 'USB3_LTE_RX_N', 'USB90', ('J302.16', 'J302.18', XP, YN), ('J501.31', 'J501.29', YP),
     USB3_NORTH),
    ('USB3_TX', 'USB3_LTE_TX_P', 'USB3_LTE_TX_N', 'USB90', ('J302.22', 'J302.24', XP, YN), ('C501.1', 'C502.1', XN),
     USB3_NORTH),
    ('USB3_TXC', 'USB3_LTE_TXC_P', 'USB3_LTE_TXC_N', 'USB90', ('C501.2', 'C502.2', XP), ('J501.37', 'J501.35', YN),
     dict(d_launch=(0.6, 0.6), loose=True)),
    ('USB_HUB_UP', 'USB_HUB_UP_DP', 'USB_HUB_UP_DN', 'USB90', ('J303.13', 'J303.15', YN), ('U401.31', 'U401.30', YN), {}),
    # the modem's USB 2.0 passes two test pads: section A arrives at them from the west, B leaves east (each its own
    # launch point; a shared one tangled the two sections)
    ('USB_LTE_A', 'USB_LTE_DP', 'USB_LTE_DN', 'USB90', ('J303.1', 'J303.3', YN), ('TP501.1', 'TP502.1', XN), {}),
    ('USB_LTE_B', 'USB_LTE_DP', 'USB_LTE_DN', 'USB90', ('TP501.1', 'TP502.1', XP), ('J501.7', 'J501.9', YN), {}),
    ('KBD_B', 'KBD_DP', 'KBD_DN', 'USB90', ('D1001.1', 'D1001.2', YN), ('U401.7', 'U401.6', XP), {}),
    ('KBD_A', 'KBD_DP', 'KBD_DN', 'USB90', ('J1001.6', 'J1001.5', YP), ('D1001.1', 'D1001.2', YN), LOOSE),
    ('DIG', 'DIG_DP', 'DIG_DN', 'USB90', ('J703.6', 'J703.5', YP), ('U401.9', 'U401.8', XP), {}),
    ('USB_P1_A', 'USB_P1_DP', 'USB_P1_DN', 'USB90', ('U401.2', 'U401.1', XP), ('D402.1', 'D402.2', YN), {}),
    ('USB_P1_B', 'USB_P1_DP', 'USB_P1_DN', 'USB90', ('D402.1', 'D402.2', YN), ('J401.3', 'J401.2', YN), LOOSE),
    ('USB_P2_A', 'USB_P2_DP', 'USB_P2_DN', 'USB90', ('U401.4', 'U401.3', XP), ('D403.1', 'D403.2', YN), {}),
    ('USB_P2_B', 'USB_P2_DP', 'USB_P2_DN', 'USB90', ('D403.1', 'D403.2', YN), ('J402.3', 'J402.2', YN), LOOSE),
]


SKEW_BAD = 0.5                    # mm of P / N skew left after tuning a pair as routed: the round counts it as failed
# PCIE_REFCLK goes in table order, after the CSI-A lanes: routed first, it took the diagonal on L4 south-west of
# connector B that CSI-A's D1 / D0 need to pass under their clock (D119)
FIRST = ('PCIE_TX', 'PCIE_RX', 'WL_PCIE_TX', 'WL_PCIE_RX', 'WL_REFCLK')
# the last four only for pins level with the Wi-Fi module's east pad column, which ends 1.2 mm past JP2's east row (D114)
FAN_OPTS = ((0.30, 0.80), (0.80, 0.30), (0.45, 0.95), (0.95, 0.45), (0.65, 1.15), (1.15, 0.65), (0.95, 1.45), (1.45, 0.95),
            (1.25, 1.75), (1.75, 1.25), (1.45, 1.95), (1.95, 1.45))
FAN_REFS = ('J302', 'J303')                  # CM5 connectors B and C: 0.4 mm rows, fan out through staggered vias


def options(start, end, opt):
    o = dict(opt)
    o.setdefault('fan', tuple(x[0].split('.')[0] in FAN_REFS for x in (start, end)))
    o.pop('tune_now', None)
    return o


def _route(pr, name, p, n, cls, a, z, opt, **extra):
    """route one pair; a pair marked tune_now gets its P / N skew tuned right away, so the pairs routed after it
    keep clear of its bumps (D100)"""
    ok = pr.route(name, p, n, cls, a, z, **extra, **options(a, z, opt))
    if ok and opt.get('tune_now') and not pr.loose_used.get(name):
        import route_tune
        d = route_tune.tune_pair(pr.b, pr.net(p), pr.net(n), cls, log=pr.log, name=name)
        pr.skew[name] = d
        pr.log(f'{name}: P / N skew tuned before the next pair: {d:+.3f} mm')
    return ok


def corridors(board, table):
    """the long east fan-outs of the CSI-A lanes (2.5-4.1 mm past the CM5 connector's inner pin row, D38 / D44) run
    past the PCIe AC capacitors: each gets its strip (F.Cu tracks and vias of the other pairs kept out) before anything
    is routed, so the PCIe breakout vias go elsewhere"""
    out = {}
    for name, _, _, _, a, z, opt in table:
        if not (opt.get('fan_off') and opt['fan_off'][0] is EAST):
            continue
        rects = []
        for rp in a[:2]:
            fp, p = pad_of(board, rp)
            x, y = R.to_mm(p.GetPosition())
            x0, x1 = x + 0.35, x + 0.35 + max(max(o) for o in EAST) + 0.25
            # the keep-out is applied to the other pairs' centrelines and via centres as is (not inflated): it covers
            # the stub, its clearance and a via radius / pair half-width
            r = [(x0, y - 0.42), (x1, y - 0.42), (x1, y + 0.42), (x0, y + 0.42)]
            rects += [(pad_layer(fp), r), ('via', r)]
        out[name] = rects
    return out


def route_all(board, log=print, only=None, rounds=6):
    """route_rounds(), then the last resort for a pair that is still open: its two traces routed separately, at the
    pair's impedance width (the length tuning matches them afterwards; listed as an open point)"""
    failed = route_rounds(board, log, only, rounds)
    if not failed:
        return failed
    table = [p for p in PAIRS if not only or p[0] in only]
    by = {p[0]: p for p in table}
    pr = PairRouter(board, log)
    pr.corridors = corridors(board, table)
    still = []
    for name in failed:
        _, p, n, cls, a, z, opt = by[name]
        o = dict(options(a, z, opt))
        o['loose'] = True
        if not pr.route(name, p, n, cls, a, z, **o):
            still.append(name)
        elif pr.loose_used.get(name):
            log(f'{name}: routed as two separate traces (no coupled route found in {rounds} rounds)')
    return still


def route_rounds(board, log=print, only=None, rounds=6):
    """Route the table in order; pairs that fail move to the front and everything is routed again (rip-up), up to
    `rounds` times. The board keeps the best round (fewest failures, then fewest pairs routed as separate traces). A
    pair tuned as routed (tune_now) whose P / N skew could not be brought under SKEW_BAD counts as a failure of its
    round: its traces zig-zag (D101)."""
    table = [p for p in PAIRS if not only or p[0] in only]
    # PCIe first (5 GT/s; the AC caps are boxed in between the Wi-Fi module and connector JP2), then the table order
    order = [p[0] for p in table if p[0] in FIRST] + [p[0] for p in table if p[0] not in FIRST]
    by = {p[0]: p for p in table}
    best = None
    corr = corridors(board, table)
    for rnd in range(rounds):
        pr = PairRouter(board, log)
        pr.corridors = corr
        failed, loose = [], []
        for name in order:
            _, p, n, cls, a, z, opt = by[name]
            if not _route(pr, name, p, n, cls, a, z, opt):
                failed.append(name)
            elif pr.loose_used.get(name):
                loose.append(name)
        failed = _retry(pr, by, failed, log)
        bad = [k for k, d in pr.skew.items() if abs(d) > SKEW_BAD and k not in failed]
        score = (len(failed) + len(bad), len(failed), len(loose))
        log(f'round {rnd + 1}: {len(failed)} failed {failed}, {len(loose)} as separate traces {loose}' +
            (f', {len(bad)} with P / N skew over {SKEW_BAD} mm {bad}' if bad else ''))
        if best is None or score < best[0]:
            best = (score, list(order), failed, loose)
        if not failed and not bad:      # pairs routed as two traces are only the short LOOSE stubs: accepted
            return failed
        if rnd == rounds - 1:
            break
        _rip_all(board, pr, by)                              # rip up everything, try the failures first
        order = failed + bad + [x for x in order if x not in failed and x not in bad]   # a pair routed as two traces
                                                                                      # keeps its turn
    if best[1] != order:                                      # the last round was not the best: redo the best
        _rip_all(board, pr, by)
        pr = PairRouter(board, log)
        pr.corridors = corr
        failed = []
        for name in best[1]:
            _, p, n, cls, a, z, opt = by[name]
            if not _route(pr, name, p, n, cls, a, z, opt):
                failed.append(name)
        failed = _retry(pr, by, failed, log)
    return failed


def _rip_all(board, pr, by):
    """every track and via on the pairs' nets (tuning replaces the router's own items, so go by net)"""
    codes = {board.FindNet(pr.net(x)).GetNetCode() for e in by.values() for x in (e[1], e[2])}
    for t in R.tracks(board):
        if t.GetNetCode() in codes:
            R.remove(board, t)


def _retry(pr, by, failed, log):
    """what is still open gets wider windows and a bigger search budget, everything else in place"""
    if not failed:
        return failed
    global VIA_STRAIGHT
    pr.max_expand = 12_000_000
    still = []
    for name in failed:
        _, p, n, cls, a, z, opt = by[name]
        ok = _route(pr, name, p, n, cls, a, z, opt, margins=(10.0, 20.0))
        if not ok:                            # layer changes anywhere (the exact P/N check still guards the result)
            vs, VIA_STRAIGHT = VIA_STRAIGHT, 0
            ok = _route(pr, name, p, n, cls, a, z, opt, margins=(6.0, 12.0))
            VIA_STRAIGHT = vs
        if not ok:
            still.append(name)
    pr.max_expand = 4_000_000
    log(f'retry with wider windows: {len(failed) - len(still)} of {len(failed)} routed')
    return still
