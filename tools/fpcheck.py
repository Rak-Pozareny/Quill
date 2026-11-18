#!/usr/bin/env python3
"""Check that every component in a KiCad netlist has a loadable footprint whose pads match the symbol pins.
usage: fpcheck.py BOARD_DIR NETLIST     (e.g. fpcheck.py hw/board_a hw/board_a/cm5_carrier.net)
Reports: unresolved footprints, symbol pins with no pad, numbered pads with no symbol pin."""
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'gen'))
import netlist  # noqa: E402
import pcbnew  # noqa: E402

KICAD_FP = '/usr/share/kicad/footprints'


def main(board_dir, net):
    comps, nets, pin_net = netlist.read(net)
    pins = {}
    for (ref, pin) in pin_net:
        pins.setdefault(ref, set()).add(pin)
    cache, problems = {}, 0
    for ref in sorted(comps, key=lambda r: (r.rstrip('0123456789'), int(''.join(c for c in r if c.isdigit()) or 0))):
        fpid = comps[ref]['footprint']
        lib, name = fpid.split(':', 1)
        path = os.path.join(board_dir, 'lib', 'cm5h.pretty') if lib == 'cm5h' else os.path.join(KICAD_FP, lib + '.pretty')
        if fpid not in cache:
            fp = pcbnew.FootprintLoad(path, name)
            cache[fpid] = None if fp is None else {p.GetNumber() for p in fp.Pads()}
        pads = cache[fpid]
        if pads is None:
            print(f'{ref}: footprint {fpid} NOT FOUND')
            problems += 1
            continue
        sym = pins.get(ref, set())
        no_pad = sorted(sym - pads)
        no_pin = sorted(p for p in pads - sym if p)
        if no_pad or no_pin:
            problems += 1
            print(f'{ref} {fpid}: pins without pad {no_pad}  pads without pin {no_pin}')
    print(f'{len(comps)} components, {len(cache)} footprints, {problems} problems')
    return problems


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1], sys.argv[2]) else 0)
