#!/usr/bin/env python3
"""Move parts on a routed board without routing it again: each footprint goes to its new position and orientation, every
track and via of the listed nets is removed, then whatever copper that leaves dangling. The board is saved in place; then
route what is open with `gen/route_a.py --out BOARD --finish` and run tools/package.py.

usage: pcb_move_parts.py BOARD.kicad_pcb --place J801=103.05,148,90 J802=103.05,155,90 --nets SPK_L_P SPK_L_N

Positions are board coordinates in mm, the angle is KiCad's orientation as the board shows it (on the footprint's
current side). Net names: the short names (the part after the last '/').
"""
import argparse
import os
import sys

import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gen'))
import gndfix  # noqa: E402
import proute as R  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board')
    ap.add_argument('--place', nargs='+', default=[])
    ap.add_argument('--nets', nargs='+', default=[])
    a = ap.parse_args()
    b = pcbnew.LoadBoard(a.board)
    for spec in a.place:
        ref, v = spec.split('=')
        x, y, ang = (float(t) for t in v.split(','))
        fp = b.FindFootprintByReference(ref)
        if fp is None:
            sys.exit(f'{ref} not on the board')
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        fp.SetOrientationDegrees(ang)
        print(f'{ref}: at ({x}, {y}), {ang} degrees')
    codes = {b.FindNet(str(n)).GetNetCode() for n in R.net_names(b) if str(n).split('/')[-1] in a.nets}
    gone = [t for t in R.tracks(b) if t.GetNetCode() in codes]
    for t in gone:
        R.remove(b, t)
    print(f'{len(gone)} tracks / vias of {", ".join(a.nets)} removed')
    gndfix.remove_dangling(b, a.board, log=print, locked=True)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(a.board, b)
    print(f'saved {a.board}')


if __name__ == '__main__':
    main()
