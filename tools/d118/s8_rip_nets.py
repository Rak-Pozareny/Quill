#!/usr/bin/env python3
"""remove every track and via of the named nets (short names), e.g. a pair the router laid as two separate traces,
before routing it again as a pair with s5_route_dsi.py. usage: s8_rip_nets.py IN OUT NET[,NET...]"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gen'))
import proute as R  # noqa: E402

src, out, names = sys.argv[1], sys.argv[2], set(sys.argv[3].split(','))
b = pcbnew.LoadBoard(src)
n = 0
for t in list(R.tracks(b)):
    if t.GetNetname().split('/')[-1] in names:
        R.remove(b, t)
        n += 1
pcbnew.SaveBoard(out, b)
print(f'{n} tracks / vias of {sorted(names)} removed, saved {out}')
