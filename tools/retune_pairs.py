#!/usr/bin/env python3
"""P / N skew of every differential pair (gen/route_pairs.PAIRS) tuned again on a routed board: bumps on the shorter
trace (route_tune.tune_pair) for each pair whose skew is over --over, without route_tune.prune, whose one-width merge
made the touching joints of D110. The board is saved in place; run tools/close_joints.py before and after.

usage: retune_pairs.py BOARD.kicad_pcb [--over 0.1] [--tol 0.025]
"""
import argparse
import os
import sys

import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gen'))
import proute as R  # noqa: E402
import route_pairs  # noqa: E402
import route_tune  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board')
    ap.add_argument('--over', type=float, default=0.1, help='tune pairs whose skew is over this (mm)')
    ap.add_argument('--tol', type=float, default=0.025)
    a = ap.parse_args()
    b = pcbnew.LoadBoard(a.board)
    full = {}
    for n in R.net_names(b):
        full.setdefault(str(n).split('/')[-1], str(n))
    seen = set()
    for name, p, n, cls, *_ in route_pairs.PAIRS:
        if (p, n) in seen or p not in full or n not in full:
            continue
        seen.add((p, n))
        pc, nc = b.FindNet(full[p]).GetNetCode(), b.FindNet(full[n]).GetNetCode()
        d0 = route_tune.length(b, pc) - route_tune.length(b, nc)
        if abs(d0) <= a.over:
            print(f'{name:14s} skew {d0:+.3f} mm')
            continue
        d = route_tune.tune_pair(b, full[p], full[n], cls, tol=a.tol, log=print, name=name)
        print(f'{name:14s} skew {d0:+.3f} -> {d:+.3f} mm')
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(a.board, b)
    print(f'saved {a.board}')


if __name__ == '__main__':
    main()
