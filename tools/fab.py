#!/usr/bin/env python3
"""JLCPCB manufacturing files for one board.

usage: fab.py BOARD.kicad_pcb OUTDIR NAME

Writes into OUTDIR:
  NAME_gerber.zip    Gerbers (every copper layer, paste, silkscreen, mask, Edge.Cuts) and Excellon drill files, the
                     settings of JLCPCB's KiCad guide ("How to generate Gerber and drill files in KiCad 8"): Protel
                     extensions, soldermask subtracted from silkscreen, zones checked; drill origin absolute,
                     millimetres, decimal zeros, alternate oval-hole mode. Gerbers and drill share the absolute origin.
  drill_map_*.pdf    drill maps (outside the zip: JLCPCB reads every file in it as a layer)
  NAME_impedance.pdf, IMPEDANCE.md   impedance requirements (tools/impedance_drawing.py); the same on a drawing-layer
                     Gerber (X2 FileFunction OtherDrawing) inside the zip, NAME-Impedance_Drawing.gbr
  NAME_impedance_control.xlsx   JLCPCB's impedance form (tools/impedance_form.py, run separately: it needs openpyxl);
                     an existing one is copied into the zip as well
  BOM.csv            the parts JLCPCB places, grouped: Comment, Designator, Footprint, LCSC Part # (the minimum fields
                     of JLCPCB's "How to generate the BOM and centroid file from KiCad")
  CPL.csv            Designator, Val, Package, Mid X, Mid Y, Rotation, Layer for the same parts (mm; JLCPCB's columns
                     Designator, Mid X, Mid Y, Rotation, Layer, plus value and package as kicad-jlcpcb-tools writes them)
  not_placed.csv     the parts JLCPCB does not place (do-not-fit), with the reason

Parts placed by JLCPCB: footprints with Sourcing JLC (fields copied from the schematic). Sourcing PCB (holes, test pads,
solder jumpers: no part) and DNP are left out.

CPL position and rotation follow Bouni's kicad-jlcpcb-tools (MIT, fabrication.py): the position is the centre of the
bounding box of the footprint's soldered pads, Y negated; the rotation is KiCad's orientation, mirrored for the bottom
side as (180 - angle), plus a correction where JLCPCB's library footprint is drawn turned against KiCad's. The
corrections are those of matthewlai's JLCKicadTools rotation table (jlc_kicad_tools/cpl_rotations_db.csv, GPL-3: the
values only, for the footprints these boards use). They are rules of thumb: every part with a pin 1 or a polarity is
listed in ROTATIONS.md to be checked in JLCPCB's placement preview.
"""
import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

import pcbnew

# (footprint name pattern, degrees), first match wins. First the ones read off JLCPCB's placement preview of board A
# (2026-10-23: each library model's pink pin-1 dot against our pin 1, connector bodies against their pads; the same
# turn on both sides), then JLCKicadTools' cpl_rotations_db.csv
CORRECTIONS = [
    (r'^SOT-23(-\d)?$', 180),                           # Q501, U106 top; Q106-Q108, Q502, U1001 bottom (was -90)
    (r'^TI_VSONP-8_', 270), (r'^QFN-36-', 270),          # Q101-Q104; U401
    (r'^TQFN-16-', 270), (r'^WSON-6-', 270),             # U801, U802; D101
    (r'^U\.FL_Hirose_U\.FL-R-SMT-1', 90),                # J601, J602
    (r'^USB_C_Receptacle_HRO_TYPE-C-31-M-12', 0),        # J101: with JLCKicadTools' 180 the opening faced inward
    (r'^FPC_0\.5mm_12P_BXCONN_FC-05A12P11H20', 180),     # J703, J1001: the cable entry faced into the board
    (r'^SOT-223', 180), (r'^SOT-23', -90), (r'^SOT-89', 180), (r'^TSOT-23', 180), (r'^SOT-353', 180),
    (r'^SOT-363', 180), (r'^LQFP-', 270), (r'^TQFP-', 270), (r'^SOP-4_', 0), (r'^SOP-(?!18_)', 270),
    (r'^TSSOP-', 270), (r'^SSOP-', 270), (r'^DFN-', 270), (r'^SOIC-', 270), (r'^VSSOP-8_3.0x3.0mm_P0.65mm', 270),
    (r'^VSSOP-8_', 180), (r'^VSSOP-10_', 270), (r'^VSON-8_', 270), (r'^USON-10', 270), (r'^CP_EIA-', 180),
    (r'^(.*?_|V)?QFN-(16|20|24|28|40)(-|_|$)', 270), (r'^USB_C_Receptacle_HRO_TYPE-C-31-M-12', 180),
    (r'^HTSSOP-', 270), (r'^SC-74-6', 180), (r'^SOT-143', 180),
    # our own footprints, seen in JLCPCB's placement preview (2026-10-23): the CM5 connectors JP1 / JP2 run up the
    # board, JLCPCB's DF40C-100DS-0.4V(51) model lies across it. Not polarized (Hirose DF40 catalogue, note 4), so 90
    # and 270 place it alike; JP3 lies across the board like the model
    (r'^OPi_CM5_DF40_JP[12]$', 90),
]
# two-terminal parts without a polarity: any rotation by 180 degrees places them the same
NON_POLAR = re.compile(r'^(R|C|L|FB)_\d{4}_|^R_2512|^L_Sunlord|^L_Bourns|^L_0')


def field(fp, name):
    return {k: str(v) for k, v in fp.GetFieldsText().items()}.get(name, '')


def natural(ref):
    m = re.match(r'([A-Z]+)(\d+)', ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def correction(name):
    for pat, deg in CORRECTIONS:
        if re.match(pat, name):
            return pat, deg
    return None, 0


def centre(fp):
    pads = [p for p in fp.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH and p.IsOnCopperLayer()]
    if not pads:
        return fp.GetPosition()
    bb = pads[0].GetBoundingBox()
    for p in pads[1:]:
        bb.Merge(p.GetBoundingBox())
    return bb.GetCenter()


def placed(b):
    out, skipped = [], []
    for fp in b.GetFootprints():
        src = field(fp, 'Sourcing') or 'JLC'
        if src == 'PCB':
            continue
        if src != 'JLC' or fp.IsDNP():
            skipped.append((fp, 'do not fit' if src == 'DNP' or fp.IsDNP() else f'Sourcing {src}'))
            continue
        out.append(fp)
    return out, skipped


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f'{" ".join(cmd)}\n{r.stdout}\n{r.stderr}')
    return r.stdout


def gerbers(board, out, name, layers):
    with tempfile.TemporaryDirectory() as tmp:
        run(['kicad-cli', 'pcb', 'export', 'gerbers', '-o', tmp, '--layers', ','.join(layers), '--subtract-soldermask',
             '--check-zones', board])
        run(['kicad-cli', 'pcb', 'export', 'drill', '-o', tmp, '--format', 'excellon', '--drill-origin', 'absolute',
             '--excellon-units', 'mm', '--excellon-zeros-format', 'decimal', '--excellon-oval-format', 'alternate',
             '--excellon-separate-th', '--generate-map', '--map-format', 'pdf', board])
        files = sorted(os.listdir(tmp))
        zpath = os.path.join(out, f'{name}_gerber.zip')
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
            for f in files:
                if f.endswith('.pdf'):
                    shutil.copy(os.path.join(tmp, f), os.path.join(out, 'drill_map_' + f.split('-')[-1]))
                elif not f.endswith('.gbrjob'):
                    z.write(os.path.join(tmp, f), f)
        return zpath, [f for f in files if not f.endswith(('.pdf', '.gbrjob'))]


def main():
    board, out, name = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    b = pcbnew.LoadBoard(board)
    n = b.GetCopperLayerCount()
    cu = ['F.Cu'] + [f'In{k}.Cu' for k in range(1, n - 1)] + ['B.Cu']
    layers = cu + ['F.Paste', 'B.Paste', 'F.Silkscreen', 'B.Silkscreen', 'F.Mask', 'B.Mask', 'Edge.Cuts']
    zpath, files = gerbers(board, out, name, layers)
    # impedance requirements for the CAM engineers (boards with controlled-impedance classes): a drawing-layer Gerber in
    # the zip, its colour PDF and a text version beside it (tools/impedance_drawing.py, D110)
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'impedance_drawing.py'),
                        board, out, name], capture_output=True, text=True)
    drawing = os.path.join(out, f'{name}-Impedance_Drawing.gbr')
    if os.path.exists(drawing):
        with zipfile.ZipFile(zpath, 'a', zipfile.ZIP_DEFLATED) as z:
            z.write(drawing, os.path.basename(drawing))
        os.remove(drawing)
        files.append(os.path.basename(drawing))
    form = os.path.join(out, f'{name}_impedance_control.xlsx')
    if os.path.exists(form):
        with zipfile.ZipFile(zpath, 'a', zipfile.ZIP_DEFLATED) as z:
            z.write(form, os.path.basename(form))
        files.append(os.path.basename(form))

    parts, skipped = placed(b)
    groups = {}                          # one line per LCSC part and footprint (JLCPCB matches lines by part)
    for fp in parts:
        g = groups.setdefault((field(fp, 'LCSC'), str(fp.GetFPID().GetLibItemName())), ([], []))
        g[0].append(fp.GetReference())
        if fp.GetValue() not in g[1]:
            g[1].append(fp.GetValue())
    with open(os.path.join(out, 'BOM.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
        for (lcsc, fpn), (refs, vals) in sorted(groups.items(), key=lambda kv: natural(sorted(kv[1][0], key=natural)[0])):
            w.writerow([' / '.join(vals), ','.join(sorted(refs, key=natural)), fpn, lcsc])
    rot_rows = []
    with open(os.path.join(out, 'CPL.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['Designator', 'Val', 'Package', 'Mid X', 'Mid Y', 'Rotation', 'Layer'])
        for fp in sorted(parts, key=lambda f: natural(f.GetReference())):
            fpn = str(fp.GetFPID().GetLibItemName())
            c = centre(fp)
            bottom = fp.IsFlipped()
            kicad = fp.GetOrientation().AsDegrees()
            rot = (180 - kicad) % 360 if bottom else kicad % 360
            pat, deg = correction(fpn)
            rot = (rot + deg) % 360
            w.writerow([fp.GetReference(), fp.GetValue(), fpn, f'{pcbnew.ToMM(c.x):.4f}', f'{-pcbnew.ToMM(c.y):.4f}',
                        f'{rot:g}', 'bottom' if bottom else 'top'])
            if not NON_POLAR.match(fpn):
                rot_rows.append((fp.GetReference(), fp.GetValue(), fpn, field(fp, 'LCSC'), 'bottom' if bottom else 'top',
                                 kicad, deg, pat or '', rot))
    with open(os.path.join(out, 'not_placed.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['Designator', 'Value', 'Footprint', 'LCSC', 'Reason'])
        for fp, why in sorted(skipped, key=lambda s: natural(s[0].GetReference())):
            w.writerow([fp.GetReference(), fp.GetValue(), str(fp.GetFPID().GetLibItemName()), field(fp, 'LCSC'), why])
    with open(os.path.join(out, 'ROTATIONS.md'), 'w') as fh:
        fh.write(f'# {name}: parts to check in JLCPCB\'s placement preview\n\n'
                 'Every placed part with a pin 1 or a polarity (all but plain resistors, capacitors and inductors). '
                 'The CPL rotation is KiCad\'s angle (bottom side: 180 - angle) plus the correction of the JLCKicadTools '
                 'rule that matches the footprint name; a part without a rule is taken as drawn alike in both libraries. '
                 'In the preview, pin 1 (or the polarity mark) of JLCPCB\'s footprint must sit on the pad marked pin 1 '
                 'on the board; if it does not, turn the part there (or tell me the angle).\n\n'
                 '| Ref | Value | Footprint | LCSC | Side | KiCad angle | Correction | Rule | CPL rotation |\n'
                 '|---|---|---|---|---|---|---|---|---|\n')
        for r in rot_rows:
            fh.write(f'| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]:g} | {r[6]:+d} | '
                     f'{("`" + r[7] + "`") if r[7] else "none"} | {r[8]:g} |\n')
    print(f'{zpath}: {len(files)} files; BOM {len(groups)} lines, {len(parts)} parts; '
          f'CPL {len(parts)} rows ({sum(f.IsFlipped() for f in parts)} bottom); not placed {len(skipped)}; '
          f'{len(rot_rows)} to check in the preview, {sum(1 for r in rot_rows if r[6])} with a correction')


if __name__ == '__main__':
    main()
