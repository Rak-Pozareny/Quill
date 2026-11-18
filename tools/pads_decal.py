#!/usr/bin/env python3
"""Extract terminal (pad) positions and pad stacks for named decals from a PADS ASCII file; place parts.
usage: pads_decal.py FILE.asc OUT.json PART [PART...]   (coordinates in mm, PADS y-up)"""
import sys, json, re
fn, out, parts = sys.argv[1], sys.argv[2], sys.argv[3:]
lines = open(fn, errors='replace').read().splitlines()
U = 1.5e6  # units per mm (determined from 0.4 mm DF40 pitch)
# part placements
place = {}
i = next(k for k, l in enumerate(lines) if l.startswith('*PART*'))
for l in lines[i:]:
    f = l.split()
    if len(f) > 5 and f[0] in parts:
        place[f[0]] = {'decal': f[1], 'x': float(f[2]) / U, 'y': float(f[3]) / U, 'ori': float(f[4]), 'mirror': f[6]}
res = {}
for ref, pl in place.items():
    d = pl['decal']
    k = next(k for k, l in enumerate(lines) if l.startswith(d + ' ') and len(l.split()) >= 9 and l.split()[1] in ('M', 'I', 'U'))
    hdr = lines[k].split()
    nterm = int(hdr[5]); nstack = int(hdr[6])
    terms = []
    j = k + 1
    while len(terms) < nterm:
        l = lines[j]
        if l.startswith('T') and re.match(r'^T-?\d', l):
            f = l.split()
            terms.append({'pin': f[4], 'x': float(f[0][1:]) / U, 'y': float(f[1]) / U})
        j += 1
    stacks = []
    while len(stacks) < nstack:
        l = lines[j]
        if l.startswith('PAD '):
            f = l.split(); pin = f[1]; n = int(f[2]); layers = []
            for q in range(n):
                g = lines[j + 1 + q].split()
                layers.append(g)
            stacks.append({'pin': pin, 'layers': layers})
            j += n
        j += 1
    res[ref] = {'place': pl, 'terms': terms, 'stacks': stacks}
json.dump(res, open(out, 'w'), indent=1)
for ref, r in res.items():
    xs = [t['x'] for t in r['terms']]; ys = [t['y'] for t in r['terms']]
    print(ref, r['place'], len(r['terms']), 'terms; x', min(xs), max(xs), 'y', min(ys), max(ys))
    for s in r['stacks']:
        print('  PAD', s['pin'], s['layers'][:2])
