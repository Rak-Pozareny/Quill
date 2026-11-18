"""Shared PCB generation for both boards (pcbnew API): footprints with nets, explicit + automatic placement,
Edge.Cuts helpers and the stack-up.

Board coordinates: origin at the top-left corner of the board's bounding box, x right, y down, mm. The KiCad file
places that origin at (OX, OY). Automatic placement puts every part not in the fixed table next to the part it
connects to (its "anchor"), on the anchor's side first, without overlapping courtyards (a footprint's far-side
copper and drilled pads block the other side too).
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bodies  # noqa: E402
import netlist  # noqa: E402
import pcbnew  # noqa: E402
from sexpr import Q, dump, parse  # noqa: E402

KICAD_FP = '/usr/share/kicad/footprints'
KICAD_3D = '/usr/share/kicad/3dmodels'
GAP = 0.15            # extra spacing between auto-placed courtyards
BIG_FANOUT = 14       # nets with more connections than this weigh little when choosing an anchor
PRIO = {'Y': 0, 'U': 1, 'Q': 2, 'D': 2, 'L': 2, 'FB': 3, 'SW': 3, 'J': 3, 'C': 4, 'R': 4, 'NT': 4, 'JP': 4, 'TP': 6}


def mm(v):
    return pcbnew.FromMM(v)


class Gen:
    def __init__(self, board_dir, net, out, W, H, ox=100.0, oy=100.0, edge=0.5, copper_layers=6, thickness=1.2):
        self.board_dir, self.net, self.out = board_dir, net, out
        self.W, self.H, self.OX, self.OY, self.EDGE = W, H, ox, oy, edge
        self.comps, self.nets, self.pin_net = netlist.read(net)
        gj = os.path.join(board_dir, 'groups.json')          # {ref: schematic group title}, written by build_*.py
        self.groups = json.load(open(gj)) if os.path.exists(gj) else {}
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(copper_layers)
        self.board.GetDesignSettings().SetBoardThickness(mm(thickness))
        self.netinfo = {}
        for name in sorted(self.nets):
            ni = pcbnew.NETINFO_ITEM(self.board, name)
            self.board.Add(ni)
            self.netinfo[name] = ni
        self.fps = {}
        self.placed = {}
        self.rects = {'F': [], 'B': []}
        self.region_ok = None     # optional: callable(rect) -> bool for outlines that are not rectangles
        self.log = []
        self.load_footprints()

    # ----------------------------------------------------------------------------------------- coordinates
    def V(self, x, y):
        return pcbnew.VECTOR2I(mm(self.OX + x), mm(self.OY + y))

    def to_board(self, p):
        return pcbnew.ToMM(p.x) - self.OX, pcbnew.ToMM(p.y) - self.OY

    def fp_path(self, fpid):
        lib, name = fpid.split(':', 1)
        if lib == 'cm5h':
            return os.path.join(self.board_dir, 'lib', 'cm5h.pretty'), name
        return os.path.join(KICAD_FP, lib + '.pretty'), name

    # ----------------------------------------------------------------------------------------- footprints
    def load_footprints(self):
        for ref, c in self.comps.items():
            lib, name = self.fp_path(c['footprint'])
            fp = pcbnew.FootprintLoad(lib, name)
            if fp is None:
                raise SystemExit(f'{ref}: cannot load {c["footprint"]}')
            if name in bodies.BODY and not self.model_exists(fp):        # no 3D model shipped: datasheet box
                ms = fp.Models()
                ms.clear()
                m = pcbnew.FP_3DMODEL()
                bodies.box_model(name, os.path.join(lib, name + '.kicad_mod'),
                                 os.path.join(self.board_dir, 'lib', 'cm5h.3dshapes'))
                m.m_Filename = '${KIPRJMOD}/lib/cm5h.3dshapes/body_' + name + '.wrl'
                fp.Add3DModel(m)
            fp.SetReference(ref)
            fp.SetValue(c['value'])
            fp.SetFPIDAsString(c['footprint'])
            for k, v in c['fields'].items():
                if k in ('Footprint', 'Datasheet', 'Description') or not v:
                    continue
                fp.SetField(k, v)
                f = fp.GetField(k)
                if f is not None:
                    f.SetVisible(False)
            for p in fp.Pads():
                n = self.pin_net.get((ref, p.GetNumber()))
                if n:
                    p.SetNet(self.netinfo[n])
            self.board.Add(fp)
            self.fps[ref] = fp

    def model_exists(self, fp):
        for m in fp.Models():
            p = m.m_Filename.replace('${KICAD10_3DMODEL_DIR}', KICAD_3D).replace('${KICAD9_3DMODEL_DIR}', KICAD_3D)
            p = p.replace('${KIPRJMOD}', self.board_dir)
            if any(os.path.exists(os.path.splitext(p)[0] + e) for e in ('.step', '.stp', '.wrl')):
                return True
        return False

    def place(self, fp, x, y, rot, side):
        """side 'F' top / 'B' bottom; rot = displayed rotation. A flipped footprint at KiCad orientation 180 is the
        plain left-right mirror of the top view, so "mirrored, then rotated by rot" is orientation rot + 180."""
        if (side == 'B') != fp.IsFlipped():
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetPosition(self.V(x, y))
        fp.SetOrientationDegrees((rot + 180) % 360 if side == 'B' else rot)

    def courtyard_bbox(self, fp, side):
        fp.BuildCourtyardCaches()
        poly = fp.GetCourtyard(pcbnew.F_CrtYd if side == 'F' else pcbnew.B_CrtYd)
        if poly.OutlineCount() == 0:
            return None
        bb = poly.BBox()
        x0, y0 = self.to_board(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop()))
        x1, y1 = self.to_board(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
        return (x0, y0, x1, y1)

    def courtyards_collide(self, a, b, side):
        """true courtyard polygons (with openings) of two footprints on the same side intersect"""
        layer = pcbnew.F_CrtYd if side == 'F' else pcbnew.B_CrtYd
        pa = a.GetCourtyard(layer).CloneDropTriangulation()
        pa.BooleanIntersection(b.GetCourtyard(layer))
        return pa.Area() > 0

    def pad_bbox(self, fp, margin):
        """bounding box of all pads (+margin), relative to the footprint position: for parts without a courtyard"""
        px, py = self.to_board(fp.GetPosition())
        bx = []
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            x0, y0 = self.to_board(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop()))
            x1, y1 = self.to_board(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
            bx.append((x0, y0, x1, y1))
        return (min(b[0] for b in bx) - px - margin, min(b[1] for b in bx) - py - margin,
                max(b[2] for b in bx) - px + margin, max(b[3] for b in bx) - py + margin)

    def far_side_rects(self, fp):
        """pads that occupy the opposite side: drilled pads, and copper a footprint puts on its far layer (some TI
        QFN footprints add B.Cu pads under the exposed pad, which land on the top when the part is flipped)"""
        far = pcbnew.F_Cu if fp.IsFlipped() else pcbnew.B_Cu
        out = []
        for p in fp.Pads():
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) or p.IsOnLayer(far):
                bb = p.GetBoundingBox()
                x0, y0 = self.to_board(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop()))
                x1, y1 = self.to_board(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
                out.append((x0, y0, x1, y1))
        return out

    # ----------------------------------------------------------------------------------------- occupancy
    def block(self, side, r):
        sides = ('F', 'B') if side == 'both' else (side,)
        for s in sides:
            self.rects[s].append(r)

    def free(self, side, r):
        x0, y0, x1, y1 = r
        e = self.EDGE
        if x0 < e or y0 < e or x1 > self.W - e or y1 > self.H - e:
            return False
        if self.region_ok and not self.region_ok(r):
            return False
        for (a, b, c, d) in self.rects[side]:
            if x0 < c + GAP and x1 > a - GAP and y0 < d + GAP and y1 > b - GAP:
                return False
        return True

    def spiral(self, side, bb, tx, ty, step=0.25, rmax=30.0):
        best = None
        n = int(rmax / step)
        for ring in range(n + 1):
            r = ring * step
            if best and r > best[0]:
                break
            pts = [(0, 0)] if ring == 0 else []
            if ring:
                for i in range(-ring, ring + 1):
                    pts += [(i * step, -r), (i * step, r)]
                for i in range(-ring + 1, ring):
                    pts += [(-r, i * step), (r, i * step)]
            for dx, dy in pts:
                x, y = tx + dx, ty + dy
                if self.free(side, (bb[0] + x, bb[1] + y, bb[2] + x, bb[3] + y)):
                    d = math.hypot(dx, dy)
                    if best is None or d < best[0]:
                        best = (d, x, y)
        return (best[1], best[2]) if best else None

    # ----------------------------------------------------------------------------------------- placement
    def place_fixed(self, fixed):
        """fixed: {ref: (x, y, rot, side)}; reports overlaps between fixed parts"""
        done = []
        for ref, (x, y, rot, side) in fixed.items():
            fp = self.fps[ref]
            self.place(fp, x, y, rot, side)
            self.placed[ref] = side
            bb = self.courtyard_bbox(fp, side)
            if bb:
                for (r2, s2, b2) in done:
                    if s2 == side and bb[0] < b2[2] and bb[2] > b2[0] and bb[1] < b2[3] and bb[3] > b2[1] \
                            and self.courtyards_collide(fp, self.fps[r2], side):
                        print(f'FIXED OVERLAP {ref} {r2} ({side})')
                done.append((ref, side, bb))
                self.block(side, bb)
            for r in self.far_side_rects(fp):
                self.block('B' if side == 'F' else 'F', r)

    def place_near_pad(self, ref, anchor, net, dx, side, rot=0):
        """put a part (e.g. a net tie) dx mm outboard of the anchor's pad on `net`"""
        a = self.fps[anchor]
        gx, gy = next(self.to_board(p.GetPosition()) for p in a.Pads() if p.GetNetname() == net)
        cx, _ = self.to_board(a.GetPosition())
        fp = self.fps[ref]
        x = gx + (dx if gx > cx else -dx)
        self.place(fp, x, gy, rot, side)
        self.placed[ref] = side
        bb = self.courtyard_bbox(fp, side) or tuple(v + o for v, o in zip(self.pad_bbox(fp, 0.25), (x, gy, x, gy)))
        self.block(side, bb)

    def autoplace(self, tp_side='B', only_side=None, hints=None):
        """Place every part not placed yet, next to the part it connects to (its anchor).

        Decoupling / filter capacitors (one net to GND) get a fixed anchor up front, the IC or connector on the same
        schematic sheet on that net (or the one in `hints`), and are placed right after their anchor, cycling over
        the anchor's pins on that net, so they get the spots next to those pins before anything else.
        only_side: restrict every auto-placed part to one side (Board B: the front is under the keyboard).
        hints: {ref: anchor_ref} for parts whose schematic note says where they belong."""
        comps, pin_net = self.comps, self.pin_net
        hints = hints or {}
        fanout = {n: len(v) for n, v in self.nets.items()}
        pads_by_net = {}
        for (r, p), n in pin_net.items():
            pads_by_net.setdefault(n, []).append((r, p))
        nets_of = {}
        for (r, p), n in pin_net.items():
            nets_of.setdefault(r, set()).add(n)

        def sheet(ref):
            return int(re.sub(r'\D', '', ref)) // 100

        def prefix(ref):
            return re.match(r'[A-Z]+', ref).group(0)

        def kin(a, b):
            """2: same schematic group, 1: same block (group titles equal up to ' - ', e.g. a power stage and its
            controller), 0: otherwise"""
            ga, gb = self.groups.get(a), self.groups.get(b)
            if not ga or not gb:
                return 0
            return 2 if ga == gb else (1 if ga.split(' - ')[0] == gb.split(' - ')[0] else 0)

        def rank(ref):
            return 0 if prefix(ref) in ('U', 'J', 'Q', 'L', 'D', 'Y', 'SW') else 1

        # ---- static anchors for capacitors from one net to GND
        decap = {}
        for ref in sorted(comps):
            if prefix(ref) != 'C' or ref in self.placed:
                continue
            nets = nets_of.get(ref, set())
            if len(nets) != 2 or 'GND' not in nets:
                continue
            rail = sorted(nets - {'GND'})[0]
            if rail.startswith('unconnected'):
                continue
            if ref in hints:
                decap[ref] = (hints[ref], rail)
                continue
            best = None
            for r in sorted({r for (r, p) in pads_by_net[rail]}):
                if r == ref or prefix(r) in ('C', 'R', 'TP', 'FB', 'NT', 'JP'):
                    continue
                npins = sum(1 for (rr, pp) in pads_by_net[rail] if rr == r)
                sc = 10 * kin(r, ref) + 5 * (sheet(r) == sheet(ref)) \
                    + {'U': 3}.get(prefix(r), 2 if prefix(r) in ('J', 'Q', 'L', 'D', 'Y') else 0) + 0.1 * npins
                if best is None or sc > best[0]:
                    best = (sc, r)
            if best:
                decap[ref] = (best[1], rail)
        caps_of = {}
        for cap, (a, rail) in decap.items():
            caps_of.setdefault(a, []).append((cap, rail))

        def anchor_for(ref):
            if ref in hints and hints[ref] in self.placed:
                shared = sorted((nets_of.get(ref, set()) & nets_of.get(hints[ref], set())) - {'GND'})
                return hints[ref], (shared[0] if shared else None)
            cand = {}
            for n in sorted(nets_of.get(ref, ())):          # sorted: deterministic tie-breaks
                if n == 'GND' or n.startswith('unconnected'):
                    continue
                w = 3.0 if fanout[n] <= BIG_FANOUT else 0.5
                for (r, p) in pads_by_net[n]:
                    if r == ref or r not in self.placed:
                        continue
                    sc = w + 2.0 * kin(r, ref) + (1.0 if sheet(r) == sheet(ref) else 0) + (1.0 if rank(r) == 0 else 0)
                    if sc > cand.get(r, (0, None))[0]:
                        cand[r] = (sc, n)
            if not cand:
                return ('@', None) if ref.startswith('TP') else None
            r = max(sorted(cand), key=lambda k: cand[k][0])
            return r, cand[r][1]

        def pads_on(ref, net):
            return sorted((self.to_board(p.GetPosition()) for p in self.fps[ref].Pads() if p.GetNetname() == net),
                          key=lambda q: (round(q[0], 2), round(q[1], 2)))

        def pad_xy(ref, net, k=0):
            if ref == '@':
                return (self.W / 2, self.H / 2)
            pts = pads_on(ref, net) if net else []
            if pts:
                return pts[k % len(pts)]
            return self.to_board(self.fps[ref].GetPosition())

        def put(ref, aref, net, tx, ty, pref):
            sides = [only_side] if only_side else [pref, 'B' if pref == 'F' else 'F']
            fp = self.fps[ref]
            best = None
            for rmax in (30.0, 150.0):          # near the anchor first, then anywhere on the board
                for si, side in enumerate(sides):
                    for rot in (0, 90):
                        self.place(fp, 0, 0, rot, side)
                        bb = self.courtyard_bbox(fp, side) or self.pad_bbox(fp, 0.25)
                        hit = self.spiral(side, bb, tx, ty, rmax=rmax)
                        if hit:
                            d = math.hypot(hit[0] - tx, hit[1] - ty) + (3.0 if si else 0)
                            if best is None or d < best[0]:
                                best = (d, hit[0], hit[1], rot, side, bb)
                if best:
                    break
            if best is None:
                return False
            d, x, y, rot, side, bb = best
            self.place(fp, x, y, rot, side)
            self.block(side, (bb[0] + x, bb[1] + y, bb[2] + x, bb[3] + y))
            for r in self.far_side_rects(fp):
                self.block('B' if side == 'F' else 'F', r)
            self.placed[ref] = side
            self.log.append((ref, aref, net, side, round(d, 1)))
            return True

        def place_caps_of(aref):
            for k, (cap, rail) in enumerate(sorted(caps_of.get(aref, ()))):
                if cap in self.placed:
                    continue
                tx, ty = pad_xy(aref, rail, k)
                put(cap, aref, rail, tx, ty, self.placed[aref])

        for aref in sorted(r for r in caps_of if r in self.placed):      # anchors placed by hand
            place_caps_of(aref)

        pending = sorted((r for r in comps if r not in self.placed and not (r in decap and decap[r][0] in comps)),
                         key=lambda r: (PRIO.get(prefix(r), 5), r))
        stuck = 0
        while pending and stuck < 3:
            progress, nxt = False, []
            for ref in pending:
                a = anchor_for(ref)
                if a is None:
                    nxt.append(ref)
                    continue
                aref, net = a
                tx, ty = pad_xy(aref, net)
                pref = tp_side if ref.startswith('TP') or aref == '@' else self.placed[aref]
                if not put(ref, aref, net, tx, ty, pref):
                    nxt.append(ref)
                    continue
                place_caps_of(ref)
                progress = True
            pending = nxt
            stuck = 0 if progress else stuck + 1
        # capacitors whose anchor could not be placed fall back to the normal search
        for cap in sorted(c for c in decap if c not in self.placed):
            a = anchor_for(cap)
            if a and put(cap, a[0], a[1], *pad_xy(a[0], a[1]), self.placed.get(a[0], 'B') if a[0] != '@' else 'B'):
                continue
            pending.append(cap)
        return pending

    # ----------------------------------------------------------------------------------------- drawing
    def edge(self, shapes, layer=None, width=0.05):
        """shapes: ('L', a, b) lines, ('A', start, mid, end) arcs, ('C', centre, r) circles in board coordinates"""
        layer = pcbnew.Edge_Cuts if layer is None else layer
        for s in shapes:
            sh = pcbnew.PCB_SHAPE(self.board)
            sh.SetLayer(layer)
            sh.SetWidth(mm(width))
            if s[0] == 'L':
                sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
                sh.SetStart(self.V(*s[1]))
                sh.SetEnd(self.V(*s[2]))
            elif s[0] == 'A':
                sh.SetShape(pcbnew.SHAPE_T_ARC)
                sh.SetArcGeometry(self.V(*s[1]), self.V(*s[2]), self.V(*s[3]))
            else:
                sh.SetShape(pcbnew.SHAPE_T_CIRCLE)
                sh.SetCenter(self.V(*s[1]))
                sh.SetEnd(self.V(s[1][0] + s[2], s[1][1]))
            self.board.Add(sh)

    def rect(self, layer, x0, y0, x1, y1, w=0.1):
        s = pcbnew.PCB_SHAPE(self.board)
        s.SetShape(pcbnew.SHAPE_T_RECT)
        s.SetLayer(layer)
        s.SetWidth(mm(w))
        s.SetStart(self.V(x0, y0))
        s.SetEnd(self.V(x1, y1))
        self.board.Add(s)

    def text(self, layer, s, x, y, size=1.0):
        t = pcbnew.PCB_TEXT(self.board)
        t.SetText(s)
        t.SetLayer(layer)
        t.SetPosition(self.V(x, y))
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(size * 0.15))
        self.board.Add(t)

    # ----------------------------------------------------------------------------------------- output
    def save(self, stackup, thickness, finish='ENIG'):
        pcbnew.SaveBoard(self.out, self.board)
        write_stackup(self.out, stackup, thickness, finish)

    def report(self, pending, n=12):
        print(f'{len(self.comps)} footprints, {len(self.log)} auto-placed, {len(pending)} unplaced')
        for ref in pending:
            print('UNPLACED', ref)
        print('farthest auto-placements (ref, anchor, net, side, mm):')
        for t in sorted(self.log, key=lambda t: -t[4])[:n]:
            print('  ', t)


def rounded_rect(x0, y0, x1, y1, r):
    """Edge.Cuts shapes of a rounded rectangle (slots, outlines)"""
    k = r * (1 - 1 / math.sqrt(2))
    return [('L', (x0 + r, y0), (x1 - r, y0)), ('A', (x1 - r, y0), (x1 - k, y0 + k), (x1, y0 + r)),
            ('L', (x1, y0 + r), (x1, y1 - r)), ('A', (x1, y1 - r), (x1 - k, y1 - k), (x1 - r, y1)),
            ('L', (x1 - r, y1), (x0 + r, y1)), ('A', (x0 + r, y1), (x0 + k, y1 - k), (x0, y1 - r)),
            ('L', (x0, y1 - r), (x0, y0 + r)), ('A', (x0, y0 + r), (x0 + k, y0 + k), (x0 + r, y0))]


def write_stackup(path, stackup, thickness, finish='ENIG'):
    root = parse(open(path).read())
    pcb = root[0]
    setup = next(n for n in pcb if isinstance(n, list) and n and n[0] == 'setup')
    setup[:] = [n for n in setup if not (isinstance(n, list) and n and n[0] == 'stackup')]
    st = ['stackup']
    for name, typ, th, mat, er in stackup:
        n = ['layer', Q(name), ['type', Q(typ)]]
        if th is not None:
            n.append(['thickness', th])
        if mat:
            n += [['material', Q(mat)], ['epsilon_r', er], ['loss_tangent', 0.02]]
        st.append(n)
    st += [['copper_finish', Q(finish)], ['dielectric_constraints', 'no']]
    setup.insert(1, st)
    gen = next(n for n in pcb if isinstance(n, list) and n and n[0] == 'general')
    for n in gen:
        if isinstance(n, list) and n[0] == 'thickness':
            n[1] = thickness
    open(path, 'w').write(dump(pcb) + '\n')
