#!/usr/bin/env python3
"""Minimal R12 ASCII DXF reader: per-layer entity counts + bbox, circles, texts, polylines/lines extents.
usage: dxf_summary.py FILE [--circles] [--texts] [--layer NAME]"""
import sys, collections
def read_pairs(fn):
    with open(fn, 'r', errors='replace') as f:
        lines = f.read().splitlines()
    it = iter(lines)
    for code in it:
        try:
            val = next(it)
        except StopIteration:
            return
        yield code.strip(), val.strip()
def entities(fn):
    in_ent = False; cur = None
    for code, val in read_pairs(fn):
        if code == '2' and val == 'ENTITIES': in_ent = True; continue
        if not in_ent: continue
        if code == '0':
            if cur: yield cur
            if val == 'ENDSEC': return
            cur = {'type': val, 'pts': [], 'g': {}}
        elif cur is not None:
            if code in ('10', '11', '12', '13'):
                cur['pts'].append([float(val), None])
            elif code in ('20', '21', '22', '23') and cur['pts'] and cur['pts'][-1][1] is None:
                cur['pts'][-1][1] = float(val)
            else:
                cur['g'].setdefault(code, val)
if __name__ == '__main__':
    fn = sys.argv[1]; opts = sys.argv[2:]
    want_layer = opts[opts.index('--layer') + 1] if '--layer' in opts else None
    per = collections.defaultdict(lambda: {'n': collections.Counter(), 'bb': [1e9, 1e9, -1e9, -1e9]})
    circles, texts = [], []
    for e in entities(fn):
        lay = e['g'].get('8', '?')
        if want_layer and lay != want_layer: continue
        p = per[lay]; p['n'][e['type']] += 1
        pts = [q for q in e['pts'] if q[1] is not None]
        if e['type'] in ('CIRCLE', 'ARC') and pts:
            r = float(e['g'].get('40', 0)); x, y = pts[0]
            pts = [[x - r, y - r], [x + r, y + r]]
            if e['type'] == 'CIRCLE': circles.append((lay, x, y, r))
        if e['type'] in ('TEXT', 'MTEXT') and pts:
            texts.append((lay, pts[0][0], pts[0][1], e['g'].get('1', '')))
        for x, y in pts:
            bb = p['bb']; bb[0] = min(bb[0], x); bb[1] = min(bb[1], y); bb[2] = max(bb[2], x); bb[3] = max(bb[3], y)
    for lay, p in sorted(per.items()):
        bb = p['bb']
        print(f"LAYER {lay}: {dict(p['n'])} bbox x[{bb[0]:.3f},{bb[2]:.3f}] y[{bb[1]:.3f},{bb[3]:.3f}]  size {bb[2]-bb[0]:.3f} x {bb[3]-bb[1]:.3f}")
    if '--circles' in opts:
        for c in sorted(circles, key=lambda c: -c[3])[:60]:
            print(f"CIRCLE {c[0]} ({c[1]:.3f},{c[2]:.3f}) r={c[3]:.3f}")
    if '--texts' in opts:
        for t in texts[:400]:
            print(f"TEXT {t[0]} ({t[1]:.2f},{t[2]:.2f}) {t[3]}")
