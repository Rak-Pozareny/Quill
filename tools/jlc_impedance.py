#!/usr/bin/env python3
"""Trace impedance from JLCPCB's own impedance calculator (the solver behind jlcpcb.com/pcb-impedance-calculator).

The calculator posts each case to /api/jlcTools/impedance/calc and receives the result on a websocket keyed by a
session uuid (wss://tools.jlc.com/jlcTools/webSocket/<uuid>). This script does the same: it opens the websocket with
curl in the background, posts every case, and collects the results. Dimensions in mil, as the calculator uses.

usage: jlc_impedance.py OUT.json            -> sweeps the cases below for the JLC06121H-3313A stack-up
Models (Polar Si9000 names, as the calculator): CoatedMicrostrip1B, DiffEdgeCoupledCoatedMicrostrip1B (outer),
OffsetStripline1B1A, DiffOffsetStripline1B1A (inner). Copper thickness, etch (W2 = W1 - delta) and solder-mask
coating come from JLC's own configuration tables (impedance-config/copper-trace-width and /coverlay): 1 oz finished
outer copper = 1.6 mil, delta 0.5 mil, mask 1.0 / 0.6 / 1.0 mil (er 3.8, calculator default); 0.5 oz inner = 0.6 mil,
delta 0.5 mil. Calculation mode 3, as the calculator page sends.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid

MM = 1 / 0.0254          # mil per mm
# JLC06121H-3313A (impedance-calculator template): L1 35 um | 3313 0.0994 er 4.1 | L2 15.2 um | core 0.10 er 4.36 |
# L3 | 3 x 7628 0.6388 er 4.4 | L4 | core 0.10 | L5 | 3313 0.0994 | L6. Outer copper 1 oz + plating: the calculator's
# default finished thickness 1.6 mil; inner 0.5 oz = 0.6 mil.
OUTER = dict(H1=round(0.0994 * MM, 3), Er1=4.1, T1=1.6, C1=1.0, C2=0.6, C3=1.0, CEr=3.8)
# L3: plane L2 0.10 mm above (core er 4.36); far plane L5 below through 0.6388 PP + L4 copper + 0.10 core (L4 carries
# signals, so it is not counted as a plane). L4 is the mirror image (near plane L5).
INNER = dict(H1=round(0.10 * MM, 3), Er1=4.36, H2=round((0.6388 + 0.0152 + 0.10) * MM, 3), Er2=4.4, T1=0.6)


def case(model, w, s=None):
    outer = 'Microstrip' in model
    a = dict(OUTER if outer else INNER)
    a['W1'] = round(w * MM, 3)
    a['W2'] = round(a['W1'] - 0.5, 3)
    if s is not None:
        a['S1'] = round(s * MM, 3)
    a.update(dCalculateMode=3, isLinkComputingMode=False, W2LinkW1Incr=0.5)
    return a


def run(cases, timeout=120):
    """cases: {key: (model, arg)} -> {key: result dict}"""
    sid = uuid.uuid4().hex
    out = tempfile.NamedTemporaryFile(delete=False, suffix='.ws')
    ws = subprocess.Popen(['curl', '-s', '-N', '-m', str(timeout + 10), '-H', 'Origin: https://jlcpcb.com',
                           '-H', 'User-Agent: Mozilla/5.0', f'wss://tools.jlc.com/jlcTools/webSocket/{sid}'],
                          stdout=out, stderr=subprocess.DEVNULL)
    time.sleep(3)
    for key, (model, arg) in cases.items():
        body = json.dumps({'accessId': key, 'impedance_calc_mark': model,
                           'paramMd5': hashlib.md5(json.dumps(arg, separators=(',', ':')).encode()).hexdigest(),
                           'impedance_calc_arg': arg, 'uuid': sid}).encode()
        req = urllib.request.Request('https://jlcpcb.com/api/jlcTools/impedance/calc', data=body,
                                     headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
        r = json.load(urllib.request.urlopen(req, timeout=30))
        if r.get('result') != 'success':
            raise SystemExit(f'{key}: {r}')
        time.sleep(0.3)
    res, t0 = {}, time.time()
    dec = json.JSONDecoder()
    while time.time() - t0 < timeout and len(res) < len(cases):
        time.sleep(1)
        txt = open(out.name, errors='ignore').read()
        i = 0
        res = {}
        while True:
            j = txt.find('{', i)
            if j < 0:
                break
            try:
                obj, k = dec.raw_decode(txt, j)
            except ValueError:
                break
            res[obj.get('accessId')] = obj
            i = k
    ws.kill()
    os.unlink(out.name)
    return res


def main():
    cases = {}
    for w in [x / 1000 for x in range(80, 241, 10)]:                  # single-ended 0.08-0.24 mm
        cases[f'SE_out_{w:.3f}'] = ('CoatedMicrostrip1B', case('CoatedMicrostrip1B', w))
        cases[f'SE_in_{w:.3f}'] = ('OffsetStripline1B1A', case('OffsetStripline1B1A', w))
    for w in [x / 1000 for x in range(90, 161, 10)]:                  # differential, W 0.09-0.16, S 0.09-0.25
        for s in [x / 1000 for x in (90, 100, 110, 125, 150, 175, 200, 250)]:
            cases[f'D_out_{w:.3f}_{s:.3f}'] = ('DiffEdgeCoupledCoatedMicrostrip1B',
                                               case('DiffEdgeCoupledCoatedMicrostrip1B', w, s))
            cases[f'D_in_{w:.3f}_{s:.3f}'] = ('DiffOffsetStripline1B1A', case('DiffOffsetStripline1B1A', w, s))
    res = {}
    keys = sorted(cases)
    for i in range(0, len(keys), 30):                                  # batches of 30 per websocket session
        part = {k: cases[k] for k in keys[i:i + 30]}
        r = run(part)
        res.update(r)
        print(f'{len(res)}/{len(cases)}', file=sys.stderr)
    table = {k: dict(model=cases[k][0], arg=cases[k][1],
                     Z=res[k]['impedance_calc_result'].get('dImpedance') if k in res and res[k].get('impedance_calc_status') == 0 else None)
             for k in keys}
    json.dump(table, open(sys.argv[1], 'w'), indent=1, sort_keys=True)
    missing = [k for k in keys if table[k]['Z'] is None]
    print(f'{len(keys) - len(missing)} results, {len(missing)} missing: {missing[:10]}')


if __name__ == '__main__':
    main()
