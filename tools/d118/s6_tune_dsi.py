#!/usr/bin/env python3
"""DSI: P / N skew of each pair tuned, then the lanes matched to the group (as gen/route_a.tune). usage: tune_dsi.py BOARD"""
import os
import sys, pcbnew
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gen'))
import proute as R, route_pairs, route_tune
DSI = ['DSI_D0', 'DSI_D1', 'DSI_CLK', 'DSI_D2', 'DSI_D3']
path = sys.argv[1]
log = lambda m: print(m, flush=True)
b = pcbnew.LoadBoard(path)
full = {str(n).split('/')[-1]: str(n) for n in R.net_names(b)}
pairs = [(name, full[p], full[n], cls) for name, p, n, cls, *_ in route_pairs.PAIRS if name in DSI]
res = route_tune.tune_all(b, pairs, log)
log('intra-pair skew: ' + ', '.join(f'{n} {d:+.3f}' for n, d in res))
Ls = route_tune.match_group(b, [(name, P, N) for name, P, N, _ in pairs], 'MIPI100', tol=0.5, log=log, title='MIPI DSI', clock='DSI_CLK')
log('MIPI DSI: ' + ', '.join(f'{k} {v:.2f}' for k, v in sorted(Ls.items())))
pcbnew.SaveBoard(path, b)
