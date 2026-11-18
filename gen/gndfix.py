"""GND pour clean-up after the zones are filled (2-layer boards, where nothing else ties the pours together).

prune_dangling(): removes stitching vias that the filled pours do not reach on both layers.
solid_where_starved(): pads that KiCad's DRC finds with fewer than two thermal spokes get a solid connection to the
pour instead (each such GND pad has its own fan-out via anyway; they sit where other copper leaves no room for spokes).
rip_up_near(): removes the grid router's own copper around the spots where a connection it could not settle met other
nets, for a local re-route.
"""
import math

import pcbnew

import proute as R


def _fill(b):
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())


def _pt(x, y):
    return pcbnew.VECTOR2I(R.nm(R.O + x), R.nm(R.O + y))


def _islands(b, net, layers):
    """[(layer name, SHAPE_POLY_SET of one filled island)]"""
    out = []
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != net:
            continue
        for L in layers:
            lid = R.LAYER[L]
            if not z.IsOnLayer(lid):
                continue
            fp = z.GetFilledPolysList(lid)
            for k in range(fp.OutlineCount()):
                one = pcbnew.SHAPE_POLY_SET()
                one.AddOutline(fp.Outline(k))
                for h in range(fp.HoleCount(k)):
                    one.AddHole(fp.Hole(k, h))
                out.append((L, one))
    return out


def prune_dangling(b, vias, layers=('F', 'B'), net='GND', log=print):
    """vias: the stitching vias to check (positions in mm); removes those not inside filled `net` on every layer"""
    _fill(b)
    isl = _islands(b, net, layers)
    keep = {(round(x, 3), round(y, 3)) for x, y in vias}
    gone = 0
    for t in R.tracks(b):
        if not isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net:
            continue
        x, y = R.to_mm(t.GetPosition())
        if (round(x, 3), round(y, 3)) not in keep:
            continue
        if not all(any(L == L2 and poly.Contains(_pt(x, y)) for L2, poly in isl) for L in layers):
            R.remove(b, t)
            gone += 1
    log(f'{net} stitching: {gone} vias the pours do not reach removed')
    return gone


def rip_up_near(b, nets, spots, radius=1.0, log=print):
    """the router's own (unlocked) copper of every other net that comes within `radius` of the spots where the open
    connections of `nets` met it is removed, whole net at a time (no stubs are left), so the next router pass routes
    those nets again together with the open ones. Returns the number of items removed"""
    if not spots:
        return 0
    grid = {}
    for x, y in spots:
        grid.setdefault((int(x // radius), int(y // radius)), []).append((x, y))

    def near(x, y):
        ci, cj = int(x // radius), int(y // radius)
        return any(math.dist((x, y), q) <= radius for di in (-1, 0, 1) for dj in (-1, 0, 1)
                   for q in grid.get((ci + di, cj + dj), ()))
    items = [t for t in R.tracks(b) if not t.IsLocked() and t.GetNetname() not in nets]
    hit = set()
    for t in items:
        if t.GetNetCode() in hit:
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            pts = [R.to_mm(t.GetPosition())]
        else:
            a, z = R.to_mm(t.GetStart()), R.to_mm(t.GetEnd())
            n = max(1, int(math.dist(a, z) / 0.25))
            pts = [(a[0] + (z[0] - a[0]) * i / n, a[1] + (z[1] - a[1]) * i / n) for i in range(n + 1)]
        if any(near(x, y) for x, y in pts):
            hit.add(t.GetNetCode())
    gone = 0
    for t in items:
        if t.GetNetCode() in hit:
            R.remove(b, t)
            gone += 1
    log(f'rip-up at {len(spots)} conflict cells: {len(hit)} other nets ({gone} router tracks / vias) removed')
    return gone


def remove_dangling(b, path, log=print, rounds=20, locked=False):
    """router tracks and vias KiCad's DRC finds dangling (an end connected to nothing) are removed, until none;
    locked=True: pre-routed ones too (a dead end carries nothing, so removing it opens no connection). The zones are
    filled first each round, so the check sees the fill the board is saved with"""
    import groute
    total = 0
    for _ in range(rounds):
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        pcbnew.SaveBoard(path, b)
        d = groute.drc(path, refill=False)
        bad = {i['uuid'] for v in d['violations'] if v['type'] in ('track_dangling', 'via_dangling')
               for i in v['items']}
        items = [t for t in R.tracks(b) if (locked or not t.IsLocked()) and t.m_Uuid.AsString() in bad]
        if not items:
            break
        for t in items:
            R.remove(b, t)
        total += len(items)
    if total:
        log(f'{total} dangling router tracks / vias removed')
    return total


def solid_where_starved(b, path, log=print, rounds=3):
    """run KiCad's DRC on the board saved at `path`; pads with a starved thermal relief get a solid zone connection
    (again after the refill, which may starve others)"""
    import groute
    pads = {}
    for fp in R.footprints(b):
        for p in R.pads(fp):
            pads[p.m_Uuid.AsString()] = p
    total = 0
    for _ in range(rounds):
        pcbnew.SaveBoard(path, b)
        d = groute.drc(path)
        n = 0
        for v in d['violations']:
            if v['type'] != 'starved_thermal':
                continue
            for it in v['items']:
                p = pads.get(it['uuid'])
                if p is not None and p.GetLocalZoneConnection() != pcbnew.ZONE_CONNECTION_FULL:
                    p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
                    n += 1
        if not n:
            break
        _fill(b)
        total += n
    log(f'starved thermal reliefs: {total} pads connected solid')
    return total
