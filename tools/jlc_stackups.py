#!/usr/bin/env python3
"""Dump JLCPCB impedance-calculator default stack-ups. usage: jlc_stackups.py LAYERS THICKNESS_MM INNER_OZ [OUTER_OZ] [--json FILE]"""
import sys, json, urllib.request
L, T, IN = int(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
OUT = float(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith('--') else 1
body = json.dumps({"boardType": 1, "plateLayerNumber": L, "plateThickness": T, "innerCopperThickness": IN,
                   "cuprumThickness": OUT, "templateAccessId": None, "unit": "mm", "currentPage": 1, "pageSize": 50}).encode()
req = urllib.request.Request('https://jlcpcb.com/api/jlcTools/impedance/selectPageImpedanceDefaultTemplate', data=body,
                             headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
d = json.load(urllib.request.urlopen(req, timeout=60))
lst = d['body']['list']
if '--json' in sys.argv:
    json.dump(lst, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
for t in lst:
    print(f"### {t['appointName']}  thickness={t['plateThickness']} inner={t['innerCopperThickness']}oz urgent={t.get('urgentState')} default={t.get('defaultFlag')}")
    for b in t['basicDataList']:
        keys = {k: v for k, v in b.items() if v not in (None, '', 0) and k not in ('createTime', 'updateTime')}
        print('   ', json.dumps(keys, ensure_ascii=False)[:300])
