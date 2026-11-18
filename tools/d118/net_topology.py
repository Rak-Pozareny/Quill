#!/usr/bin/env python3
"""copper graph of a net: pad-to-pad shortest copper distances, loops (independent cycles), dead ends.
Joints by overlap: endpoint inside a via / pad, endpoint on another segment (T), endpoints within half a width.
usage: net_topology.py BOARD NET"""
import sys, math, heapq, itertools
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); net = sys.argv[2]
nets = [n for n in b.GetNetInfo().NetsByName().values() if n.GetNetname() == net or n.GetNetname().endswith('/' + net)]
nc = nets[0].GetNetCode()
M = lambda v: (pcbnew.ToMM(v.x), pcbnew.ToMM(v.y))
segs, vias = [], []
for t in b.GetTracks():
    if t.GetNetCode() != nc: continue
    if t.GetClass() == 'PCB_VIA': vias.append((M(t.GetPosition()), t.GetWidth(pcbnew.F_Cu) / 2e6))
    else: segs.append((t.GetLayerName(), M(t.GetStart()), M(t.GetEnd()), pcbnew.ToMM(t.GetWidth()) / 2))
pads = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetCode() == nc:
            pads.append((f'{fp.GetReference()}.{p.GetNumber()}', p))
# split points per segment: own ends + any other endpoint lying on it
def onseg(q, a, c, tol):
    dx, dy = c[0] - a[0], c[1] - a[1]; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / L))
    return math.dist(q, (a[0] + t * dx, a[1] + t * dy)) <= tol, t
ends = [(s[0], s[1]) for s in segs] + [(s[0], s[2]) for s in segs]
nodes = {}
def node(L, q):
    k = (L, round(q[0], 4), round(q[1], 4)); nodes.setdefault(k, len(nodes)); return nodes[k]
edges = []
for L, a, c, h in segs:
    pts = [(0.0, a), (1.0, c)]
    for L2, q in ends:
        if L2 == L and q not in (a, c):
            ok, t = onseg(q, a, c, h)
            if ok and 0 < t < 1: pts.append((t, q))
    pts.sort()
    for (t1, p1), (t2, p2) in zip(pts, pts[1:]):
        edges.append((node(L, p1), node(L, p2), math.dist(p1, p2)))
# endpoints on the same layer within half a width of each other
keys = list(nodes)
for k1, k2 in itertools.combinations(keys, 2):
    if k1[0] == k2[0] and k1[0] != 'via' and 0 < math.dist(k1[1:], k2[1:]) <= 0.05:
        edges.append((nodes[k1], nodes[k2], math.dist(k1[1:], k2[1:])))
# vias: a node per via, joined to every track node inside its pad
for (q, r) in vias:
    v = node('via', q)
    for k in keys:
        if k[0] != 'via' and math.dist(k[1:], q) <= r: edges.append((v, nodes[k], 0.0))
# pads
padn = {}
for name, p in pads:
    v = node('pad', (name,) * 2) if False else len(nodes); nodes[('pad', name, 0)] = v; padn[name] = v
    for k in keys:
        if k[0] == 'via' or p.IsOnLayer(b.GetLayerID(k[0])):
            if p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(k[1]), pcbnew.FromMM(k[2]))): edges.append((v, nodes[k], 0.0))
    for (q, r) in vias:
        if p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(q[0]), pcbnew.FromMM(q[1]))): edges.append((v, nodes[('via', round(q[0], 4), round(q[1], 4))], 0.0))
adj = {}
for a, c, w in edges:
    adj.setdefault(a, []).append((c, w)); adj.setdefault(c, []).append((a, w))
# components and cycles
seen, comps = set(), 0
for n in range(len(nodes)):
    if n in seen or n not in adj: continue
    comps += 1; st = [n]; seen.add(n)
    while st:
        u = st.pop()
        for v, _ in adj[u]:
            if v not in seen: seen.add(v); st.append(v)
E = len({(min(a, c), max(a, c)) for a, c, w in edges if a != c}); V = len(seen)
def dij(s):
    d = {s: 0.0}; pq = [(0.0, s)]
    while pq:
        x, u = heapq.heappop(pq)
        if x > d[u]: continue
        for v, w in adj.get(u, []):
            if x + w < d.get(v, 1e9): d[v] = x + w; heapq.heappush(pq, (x + w, v))
    return d
print(f'{nets[0].GetNetname()}: tracks {sum(math.dist(a, c) for _, a, c, _ in segs):.3f} mm, {len(vias)} vias, '
      f'{comps} copper piece(s), {E - V + comps} loop(s)')
names = [n for n, _ in pads]
for i, a in enumerate(names):
    d = dij(padn[a])
    print('  ' + a.ljust(10) + ' '.join(f'{nm}:{d[padn[nm]]:.2f}' if padn[nm] in d else f'{nm}:--' for nm in names[i + 1:]))
