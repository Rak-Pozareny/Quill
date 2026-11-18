#!/usr/bin/env python3
"""route DSI pairs one after another on a board whose J302 fan-out vias exist: fan_vias returns the existing via pair
of the two nets near the pads (else places new ones as usual). usage: pairtest2.py IN OUT MARGIN MAXEXP NAME[,NAME...]"""
import os, sys, time, math, pcbnew
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gen'))
import proute as _PR
_ObsInit = _PR.Obstacles.__init__
def _obs_init(self, *a, **k):
    k.setdefault('zones', 'hull')      # a routed board: the finished pours are refilled round new copper (D118)
    _ObsInit(self, *a, **k)
_PR.Obstacles.__init__ = _obs_init
import route_pairs
import proute as R
src, out, margin, maxexp, names = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4]), sys.argv[5].split(',')
route_pairs.MARGIN = margin if margin >= 0 else route_pairs.MARGIN
_orig_fan = route_pairs.PairRouter.fan_vias


def fan_existing(self, pnet, nnet, padp, padn, e, width, offsets=None):
    b = self.b
    P, N = R.to_mm(padp.GetPosition()), R.to_mm(padn.GetPosition())
    found = {}
    for t in R.tracks(b):
        if t.GetClass() != 'PCB_VIA':
            continue
        for key, net, Q in (('p', pnet, P), ('n', nnet, N)):
            if t.GetNetname() == net:
                v = R.to_mm(t.GetPosition())
                if math.dist(v, Q) < 3.0 and (key not in found or math.dist(v, Q) < math.dist(found[key], Q)):
                    found[key] = v
    if 'p' in found and 'n' in found:
        return (found['p'], found['n']), []
    return _orig_fan(self, pnet, nnet, padp, padn, e, width, offsets)


route_pairs.PairRouter.fan_vias = fan_existing
import os, json
EXTRA = json.loads(os.environ.get('DSI_OPTS', '{}'))
ONLY = set(filter(None, os.environ.get('DSI_OPTS_ONLY', '').split(',')))
if EXTRA:
    for i, e in enumerate(route_pairs.PAIRS):
        if e[0].startswith('DSI_') and (not ONLY or e[0] in ONLY):
            opt = dict(e[6]); opt.update({k: (tuple(v) if isinstance(v, list) else v) for k, v in EXTRA.items()})
            if 'layer_cost' in opt: opt['layer_cost'] = dict(opt['layer_cost'])
            route_pairs.PAIRS[i] = e[:6] + (opt,)
    print('DSI options', EXTRA, flush=True)
b = pcbnew.LoadBoard(src)
log = lambda m: print(m, flush=True) if 'retrying' not in m else None
pr = route_pairs.PairRouter(b, log)
pr.max_expand = maxexp
by = {p[0]: p for p in route_pairs.PAIRS}
res = {}
for nm in names:
    _, p, n, cls, a, z, opt = by[nm]
    t0 = time.time()
    ok = route_pairs._route(pr, nm, p, n, cls, a, z, opt)
    res[nm] = bool(ok)
    print(f'{nm}: {"OK" if ok else "FAILED"} in {time.time() - t0:.0f} s', flush=True)
pcbnew.SaveBoard(out, b)
print('RESULT', res)
import collections
L = collections.defaultdict(float); V = collections.Counter()
for t in b.GetTracks():
    n = t.GetNetname().split('/')[-1]
    if n.startswith('DSI_'):
        if t.GetClass() == 'PCB_VIA': V[n] += 1
        else: L[n] += pcbnew.ToMM(t.GetLength())
lanes = {k: (L[k + '_P'] + L[k + '_N']) / 2 for k in ('DSI_D0', 'DSI_D1', 'DSI_CLK', 'DSI_D2', 'DSI_D3')}
print('LENGTHS', {k: round(v, 2) for k, v in lanes.items()}, 'spread', round(max(lanes.values()) - min(lanes.values()), 2),
      'vias', sum(V.values()))
