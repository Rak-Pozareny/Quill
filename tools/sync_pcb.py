#!/usr/bin/env python3
"""Bring the footprints' fields and attributes in line with the schematic (KiCad's "Update PCB from Schematic", for
fields and attributes only: nothing is moved, no copper changes). Reads <name>.net next to the board; the board is saved
in place.

usage: sync_pcb.py BOARD.kicad_pcb

Per footprint: every symbol field missing on it is added (hidden, on the Fab layer of its side, e.g. 'Status'), a
differing value is set to the schematic's, and 'Do not populate' and 'Exclude from bill of materials' follow the
symbol's. KiCad's schematic parity check then has nothing to report.
"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gen'))
from sexpr import parse, find, find_all  # noqa: E402

SKIP = {'Footprint', 'Datasheet', 'Description', 'Reference', 'Value'}


def main():
    path = sys.argv[1]
    net = os.path.splitext(path)[0] + '.net'
    root = parse(open(net).read())[0]
    sym = {}
    for c in find_all(find(root, 'components'), 'comp'):
        ref = str(find(c, 'ref')[1])
        fields = {}
        for x in find_all(find(c, 'fields') or [], 'field'):
            fields[str(find(x, 'name')[1])] = str(x[2]) if len(x) > 2 else ''
        props = {str(find(x, 'name')[1]) for x in find_all(c, 'property')}
        sym[ref] = (fields, 'dnp' in props, 'exclude_from_bom' in props)
    b = pcbnew.LoadBoard(path)
    added = changed = flags = 0
    for fp in b.GetFootprints():
        s = sym.get(fp.GetReference())
        if s is None:
            continue
        fields, dnp, no_bom = s
        have = {k: str(v) for k, v in fp.GetFieldsText().items()}
        for k, v in fields.items():
            if k in SKIP:
                continue
            if k not in have:
                fp.SetField(k, v)
                f = fp.GetField(k)
                f.SetVisible(False)
                f.SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
                added += 1
            elif have[k] != v:
                fp.SetField(k, v)
                changed += 1
        if fp.IsDNP() != dnp:
            fp.SetDNP(dnp)
            flags += 1
        if fp.IsExcludedFromBOM() != no_bom:
            fp.SetExcludedFromBOM(no_bom)
            flags += 1
    pcbnew.SaveBoard(path, b)
    print(f'fields added {added}, values changed {changed}, attributes changed {flags}')


if __name__ == '__main__':
    main()
