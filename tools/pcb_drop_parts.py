#!/usr/bin/env python3
"""Take parts out of a routed board without routing it again: their footprints, every track and via of the nets that
only they used, then whatever copper that leaves dangling; pads whose net the schematic changed get the netlist's net.
The board is saved in place; run tools/package.py afterwards (zone refill, DRC with schematic parity).

usage: pcb_drop_parts.py BOARD.kicad_pcb --refs Q901 R904 R905 --nets SD_PWR_ON SD_PFET_G --pads J301.75

Net and pad names: the short names (the part after the last '/'). The new pad nets come from <board>.net.
"""
import argparse
import os
import sys

import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gen'))
import gndfix  # noqa: E402
import proute as R  # noqa: E402
from sexpr import parse, find, find_all  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board')
    ap.add_argument('--refs', nargs='+', default=[])
    ap.add_argument('--nets', nargs='+', default=[])
    ap.add_argument('--pads', nargs='+', default=[])
    a = ap.parse_args()
    b = pcbnew.LoadBoard(a.board)
    for ref in a.refs:
        fp = b.FindFootprintByReference(ref)
        if fp is None:
            sys.exit(f'{ref} not on the board')
        R.remove(b, fp)
        print(f'{ref}: footprint removed')
    codes = {b.FindNet(str(n)).GetNetCode() for n in R.net_names(b) if str(n).split('/')[-1] in a.nets}
    gone = [t for t in R.tracks(b) if t.GetNetCode() in codes]
    for t in gone:
        R.remove(b, t)
    print(f'{len(gone)} tracks / vias of {", ".join(a.nets)} removed')
    # new pad nets from the netlist
    root = parse(open(os.path.splitext(a.board)[0] + '.net').read())[0]
    want = {}
    for n in find_all(find(root, 'nets'), 'net'):
        name = str(find(n, 'name')[1])
        for nd in find_all(n, 'node'):
            want[f'{find(nd, "ref")[1]}.{find(nd, "pin")[1]}'] = name
    for rp in a.pads:
        ref, num = rp.split('.')
        net = want[rp]
        ni = b.FindNet(net)
        if ni is None:
            ni = pcbnew.NETINFO_ITEM(b, net)
            b.Add(ni)
        for p in b.FindFootprintByReference(ref).Pads():
            if p.GetNumber() == num:
                p.SetNet(ni)
        print(f'{rp}: net {net}')
    gndfix.remove_dangling(b, a.board, log=print, locked=True)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(a.board, b)
    print(f'saved {a.board}')


if __name__ == '__main__':
    main()
