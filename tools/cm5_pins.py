"""Parse Radxa CM5 v2.21 pinout (research/cm5_pinout_v2210.tsv, exported from radxa_cm5_v2210_pinout.xlsx)
into gen/data/cm5_pins.json: {"A": {"1": {"net":..., "ball":..., "gpio":..., "funcs": [...]}}, "B": ..., "C": ...}.
Connector letters: A = U13-A (pins 1-100), B = U13-B (101-200), C = J1 (1-100)."""
import json, os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
src = os.path.join(ROOT, 'research', 'cm5_pinout_v2210.tsv')
out = {}
sheet = None
hdr = None
for line in open(src, encoding='utf-8'):
    line = line.rstrip('\n')
    if line.startswith('#### SHEET:'):
        sheet = {'U13-A': 'A', 'U13-B': 'B', 'J1': 'C'}[line.split(':', 1)[1].strip()]
        out[sheet] = {}
        hdr = None
        continue
    cols = line.split('\t')
    if cols[0] == 'r2':
        hdr = cols
        continue
    if hdr is None or len(cols) < 3 or not re.fullmatch(r'\d+', cols[1].strip()):
        continue
    i_net = hdr.index('Radxa CM5')
    i_ball = hdr.index('RK3588S SoC')
    i_f1 = hdr.index('Func1')
    i_note = hdr.index('Note') if 'Note' in hdr else None
    funcs = [c.strip() for c in cols[i_f1:i_note] if c.strip()]
    gpio = next((re.sub(r'_[ud]$', '', f) for f in funcs if re.fullmatch(r'GPIO\d_[A-D]\d(_[ud])?', f)), '')
    out[sheet][cols[1].strip()] = {'net': cols[i_net].strip(), 'ball': cols[i_ball].strip(), 'gpio': gpio,
                                   'funcs': funcs, 'note': cols[i_note].strip() if i_note is not None and len(cols) > i_note else ''}
for k, v in out.items():
    assert len(v) == 100, (k, len(v))
json.dump(out, open(os.path.join(ROOT, 'gen', 'data', 'cm5_pins.json'), 'w'), indent=1)
print({k: len(v) for k, v in out.items()})
