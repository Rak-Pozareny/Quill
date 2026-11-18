#!/usr/bin/env python3
"""Height check for a board: height of every footprint above (top side) or below (bottom side) the board.

usage: heights.py BOARD.kicad_pcb [N]      -> the N tallest parts per side, the stack, and parts sinking into
                                              a cutout (USB-A). Board thickness from the file.
Sources: gen/data/fp_meta.json for project (cm5h) footprints, which records the datasheet height; the maximum z of
the KiCad library STEP model for the others (KiCad models sit on the board surface, z up). Parts whose height
comes from neither are listed as UNKNOWN.
"""
import json
import os
import re
import sys

import pcbnew

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
META = json.load(open(os.path.join(ROOT, 'gen', 'data', 'fp_meta.json')))
sys.path.insert(0, os.path.join(ROOT, 'gen'))
import bodies  # noqa: E402
MODELDIR = '/usr/share/kicad/3dmodels'
# datasheet heights for parts whose KiCad model is missing or generic (by reference, then by footprint name)
OVERRIDE = {
    'C503': (1.9, 'Panasonic 6TPE220MI, TPE case D2E 7.3 x 4.3 x 1.8 +-0.1 (C129173 datasheet)'),
    'C504': (1.9, 'Panasonic 6TPE220MI, TPE case D2E 7.3 x 4.3 x 1.8 +-0.1 (C129173 datasheet)'),
}
FP_OVERRIDE = bodies.BODY          # library footprints without a 3D model: datasheet heights (gen/bodies.py)
NO_BODY = ('TestPoint:', 'MountingHole:', 'NetTie:', 'Jumper:SolderJumper')
_cache = {}


def step_zmax(path):
    if path in _cache:
        return _cache[path]
    z = None
    try:
        txt = open(path, errors='ignore').read()
        zs = [float(m.group(1)) for m in re.finditer(r"CARTESIAN_POINT\(\s*'[^']*'\s*,\s*\(\s*[-\d.Ee+]+\s*,\s*"
                                                         r"[-\d.Ee+]+\s*,\s*([-\d.Ee+]+)\s*\)", txt)]
        if zs:
            z = max(zs)
            # some models are in inches? KiCad library STEP files are in mm
    except OSError:
        pass
    _cache[path] = z
    return z


def height_of(fp):
    fpid = fp.GetFPIDAsString()
    lib, name = fpid.split(':', 1)
    ref = fp.GetReference()
    if ref in OVERRIDE:
        h, src = OVERRIDE[ref]
        return h, 0.0, src
    if name in FP_OVERRIDE:
        h, src = FP_OVERRIDE[name]
        return h, 0.0, src
    if fpid.startswith(NO_BODY):
        return 0.0, 0.0, 'pad only'
    if lib == 'cm5h':
        m = META.get(name)
        if m:
            return m['height'], m.get('below', 0.0), 'datasheet (fp_meta)'
        return None, 0.0, 'UNKNOWN'
    for mdl in fp.Models():
        p = mdl.m_Filename.replace('${KICAD10_3DMODEL_DIR}', MODELDIR).replace('${KICAD9_3DMODEL_DIR}', MODELDIR)
        if p.lower().endswith('.wrl'):
            p = p[:-4] + '.step'
        z = step_zmax(p)
        if z is not None:
            return round(z + mdl.m_Offset.z, 3), 0.0, 'KiCad STEP ' + os.path.basename(p)
    return None, 0.0, 'UNKNOWN (no model)'


def main(path, n=8):
    b = pcbnew.LoadBoard(path)
    th = pcbnew.ToMM(b.GetDesignSettings().GetBoardThickness())
    rows = {'F': [], 'B': []}
    unknown = []
    for fp in b.GetFootprints():
        side = 'B' if fp.IsFlipped() else 'F'
        h, below, src = height_of(fp)
        if h is None:
            unknown.append((fp.GetReference(), fp.GetFPIDAsString()))
            continue
        rows[side].append((h, below, fp.GetReference(), fp.GetValue(), src))
    for side, title in (('F', 'TOP (above the top surface)'), ('B', 'BOTTOM (below the bottom surface)')):
        print(f'== {title}')
        for h, below, ref, val, src in sorted(rows[side], reverse=True)[:n]:
            extra = f'  (also {below:.2f} below the {"top" if side == "F" else "bottom"} surface)' if below else ''
            print(f'  {h:5.2f} mm  {ref:6} {val[:34]:34} {src}{extra}')
    top = max(r[0] for r in rows['F'])
    bot = max(r[0] for r in rows['B'])
    sink = max([r[1] - th for r in rows['F'] if r[1] > th] + [0])   # parts sunk through a cutout
    print(f'board {th:.2f} mm; tallest top {top:.2f}, tallest bottom {bot:.2f}, sink-through below bottom {sink:.2f}')
    print(f'assembled stack = {top:.2f} + {th:.2f} + {max(bot, sink):.2f} = {top + th + max(bot, sink):.2f} mm')
    if unknown:
        print('UNKNOWN heights:', unknown)


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8)
