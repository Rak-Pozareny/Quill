#!/usr/bin/env python3
"""Generate Board A (CM5 carrier) schematics, run ERC and check the netlist against the intended nets.
usage: python3 -I gen/build_a.py"""
import json
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dsl
import libwriter
import symbols
import verify
import board_a_power
import board_a_main

OUT = os.path.join(HERE, '..', 'hw', 'board_a')
NAME = 'cm5_carrier'


def build():
    d = dsl.Design(NAME, 'CM5 handheld carrier (Board A)')
    d.S = symbols.make_all(d)
    for c, jp in (('A', 'JP1'), ('B', 'JP2'), ('C', 'JP3')):
        d.S['CM5_' + c] = symbols.opi_connector(d, jp)
    board_a_power.sheet_power_in(d)
    board_a_power.sheet_power_rails(d)
    for f in (board_a_main.sheet_cm5, board_a_main.sheet_usb, board_a_main.sheet_lte, board_a_main.sheet_wireless,
              board_a_main.sheet_display, board_a_main.sheet_audio, board_a_main.sheet_storage,
              board_a_main.sheet_keyboard):
        f(d)
    return d


def main():
    d = build()
    os.makedirs(OUT, exist_ok=True)
    flags = d.proj.write(OUT)
    libwriter.write_project_libs(OUT, d.symbols)
    verify.write_project_file(OUT, NAME)
    viol = verify.run_erc(OUT, NAME)
    errs = [v for v in viol if v[0] == 'error']
    warns = [v for v in viol if v[0] != 'error']
    print(f'ERC: {len(errs)} errors, {len(warns)} warnings; PWR_FLAG nets: {flags}')
    for v in viol:
        print('  ', v[0], v[1], '|', v[2], '|', v[3], '|', '; '.join(v[4])[:200])
    # schematic group of every part (the PCB placer anchors passives to an IC of their own group)
    groups = {p.ref: t.split('\n')[0] for sb in d.sheets for t, ps in sb.sheet.groups for p in ps}
    json.dump(groups, open(os.path.join(OUT, 'groups.json'), 'w'), indent=0, sort_keys=True)
    nets, comps = verify.export_netlist(OUT, NAME)
    probs = verify.compare(d.proj.expected_netlist(), nets)
    print(f'netlist: {len(nets)} nets, {len(comps)} components, {len(probs)} mismatches')
    for p in probs[:50]:
        print('  ', p)
    if d.missing_passives:
        print(f'passives without LCSC mapping: {len(d.missing_passives)} (listed in hw/board_a/missing_passives.txt)')
    open(os.path.join(OUT, 'missing_passives.txt'), 'w').write('\n'.join(sorted(d.missing_passives)) + '\n')
    return d


if __name__ == '__main__':
    main()
