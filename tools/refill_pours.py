#!/usr/bin/env python3
"""Zones refilled with the project's own design rules, and the board saved that way: KiCad's Python zone filler
(pcbnew.ZONE_FILLER, used by the scripts) leaves the custom rules of the .kicad_dru out, so a script's refill puts
the pours back at their plain clearance; kicad-cli's refill applies them (D112: pours 0.30 mm from controlled-impedance
tracks on the outer layers). Pads whose thermal relief that starves get a solid connection first
(gndfix.solid_where_starved, which finds them with kicad-cli's DRC).

usage: refill_pours.py BOARD.kicad_pcb
"""
import os
import subprocess
import sys
import tempfile

import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gen'))
import gndfix  # noqa: E402


def main():
    path = sys.argv[1]
    b = pcbnew.LoadBoard(path)
    gndfix.solid_where_starved(b, path, log=print)
    pcbnew.SaveBoard(path, b)
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run(['kicad-cli', 'pcb', 'drc', '--refill-zones', '--save-board', '--format', 'json',
                            '-o', os.path.join(d, 'drc.json'), path], capture_output=True, text=True)
    if not os.path.exists(path) or r.returncode not in (0, 5):
        sys.exit(f'kicad-cli refill failed\n{r.stdout}\n{r.stderr}')
    print(f'zones refilled with the design rules (kicad-cli), saved {path}')


if __name__ == '__main__':
    main()
