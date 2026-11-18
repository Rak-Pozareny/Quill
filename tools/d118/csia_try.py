#!/usr/bin/env python3
"""CSI-A trial on a pair-stage board (route_a.py --stop-after pairs): the named pairs' copper removed, then routed
again in the given order with the table's options, changed per pair from the JSON in PAIR_OPTS
({"CSIA_CLK": {"layers": ["In3", "F"], ...}}); the CSI-A lanes matched to their group as route_a.tune does; lengths
printed. usage: csia_try.py IN OUT NAME[,NAME...]   (RIP=NAME,... removes more pairs first without routing them)"""
import json
import os
import sys
import time

import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gen'))
import proute as R  # noqa: E402
import route_pairs  # noqa: E402
import route_tune  # noqa: E402

src, out, names = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
extra = json.loads(os.environ.get('PAIR_OPTS', '{}'))
rip = names + [x for x in os.environ.get('RIP', '').split(',') if x]
log = lambda m: print(m, flush=True) if 'retrying' not in m else None
b = pcbnew.LoadBoard(src)
by = {p[0]: p for p in route_pairs.PAIRS}
full = {}
for n in R.net_names(b):
    full.setdefault(str(n).split('/')[-1], str(n))
codes = {b.FindNet(full[x]).GetNetCode() for nm in rip for x in by[nm][1:3]}
gone = 0
for t in list(R.tracks(b)):
    if t.GetNetCode() in codes:
        R.remove(b, t)
        gone += 1
log(f'{gone} tracks / vias of {rip} removed')
pr = route_pairs.PairRouter(b, log)
pr.corridors = route_pairs.corridors(b, route_pairs.PAIRS)
res = {}
for nm in names:
    _, p, n, cls, a, z, opt = by[nm]
    if nm in extra:
        opt = dict(opt)
        for k, v in extra[nm].items():
            opt[k] = dict(v) if isinstance(v, dict) else (tuple(tuple(x) if isinstance(x, list) else x for x in v)
                                                         if isinstance(v, list) else v)
    t0 = time.time()
    ok = route_pairs._route(pr, nm, p, n, cls, a, z, opt)
    res[nm] = bool(ok)
    log(f'{nm}: {"OK" if ok else "FAILED"} in {time.time() - t0:.0f} s')
lanes = [(nm, full[by[nm][1]], full[by[nm][2]]) for nm in by if nm.startswith('CSIA_')]
before = {nm: route_tune.pair_length(b, p, q) for nm, p, q in lanes}
Ls = route_tune.match_group(b, lanes, 'MIPI100', tol=0.5, log=log, title='MIPI CSI-A', clock='CSIA_CLK')
pcbnew.SaveBoard(out, b)
vias = {nm: sum(1 for t in R.tracks(b) if t.GetClass() == 'PCB_VIA' and t.GetNetname() in (p, q)) for nm, p, q in lanes}
print('RESULT', res)
print('BEFORE', {k: round(v, 2) for k, v in sorted(before.items())})
print('AFTER ', {k: round(v, 2) for k, v in sorted(Ls.items())}, 'vias', vias)
d = [Ls[k] for k in Ls if k != 'CSIA_CLK']
print(f"clock - data: {Ls['CSIA_CLK'] - max(d):+.2f} .. {Ls['CSIA_CLK'] - min(d):+.2f} mm")
