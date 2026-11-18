"""Hole counts by size: ours (Excellon PTH + NPTH) vs JLC's drl (Gerber), board area only; and the mouse-bite holes'
clearance to our copper on each layer."""
import collections, re, sys
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, __file__.rsplit('/', 1)[0])
import jlc_vs_ours as jv
J, O = sys.argv[2], sys.argv[3]
def exc(path):
    tools, cur, out, slots = {}, None, collections.Counter(), collections.Counter()
    for line in open(path):
        line = line.strip()
        m = re.match(r'^T(\d+)C([\d.]+)', line)
        if m: tools[m.group(1)] = float(m.group(2)); continue
        m = re.match(r'^T(\d+)$', line)
        if m: cur = m.group(1); continue
        if line.startswith('X') or line.startswith('Y'):
            if 'G85' in line: slots[tools[cur]] += 1
            else: out[tools[cur]] += 1
    return out, slots
pth, pslot = exc(O + '/cm5_carrier-PTH.drl'); npth, nslot = exc(O + '/cm5_carrier-NPTH.drl')
print('ours PTH holes', dict(sorted(pth.items())), 'slots', dict(pslot)); print('ours NPTH', dict(sorted(npth.items())), 'slots', dict(nslot))
txt = open(J + '/drl').read().replace('\r', '')
aps = {int(m.group(1)): float(m.group(2)) * 25.4 for m in re.finditer(r'%ADD(\d+)C,([\d.]+)\*%', txt)}
cur, x, y, fl, dr, mb = None, 0, 0, collections.Counter(), collections.Counter(), []
for t in re.findall(r'[^%*\s][^*]*\*', re.sub(r'%[^%]*%', '', txt)):
    t = t[:-1]
    if t.startswith('G54'): t = t[3:]
    m = re.match(r'^D(\d+)$', t)
    if m and int(m.group(1)) >= 10: cur = int(m.group(1)); continue
    m = re.match(r'^(?:G0?1)?(?:X(-?\d+))?(?:Y(-?\d+))?D0?([123])$', t)
    if not m: continue
    nx = int(m.group(1)) / 1e6 * 25.4 if m.group(1) else x; ny = int(m.group(2)) / 1e6 * 25.4 if m.group(2) else y
    inb = 0 <= nx <= 95 and 7.0 <= ny <= 72.0
    if m.group(3) == '3':
        if inb: fl[round(aps[cur], 3)] += 1
        else: fl[('outside', round(aps[cur], 3))] += 1
        if abs(aps[cur] - 0.45) < 0.01: mb.append((nx + 100, 172 - ny))
    elif m.group(3) == '1' and inb: dr[round(aps[cur], 3)] += 1
    x, y = nx, ny
print('JLC holes', {k: v for k, v in sorted(fl.items(), key=str)}); print('JLC slot draws', dict(dr))
print('mouse-bite holes (KiCad coords):', len(mb))
