#!/usr/bin/env python3
"""JLCPCB's impedance form ("Required_impedance_control.xlsx", the blank as JLCPCB sent it, kept in
research/jlc/) filled from the board: one row per signal layer x impedance class in use, with the reference layers,
the model (all non-coplanar: D112 keeps the outer-layer pour 0.30 mm away, the inner layers have no pour beside the
traces), width / gap in mil (gen/route_rules.GEOM, JLCPCB's calculator for JLC06121H-3313A) and the target. The
Position column holds a close-up of the Gerber copper around one trace of the class, boxed in yellow; the cell's
comment gives the Gerber coordinates and the class's nets.

usage: impedance_form.py TEMPLATE.xlsx BOARD.kicad_pcb OUT.xlsx [GERBER.zip]

With GERBER.zip the form also goes into the zip (an earlier copy there is replaced), as tools/fab.py puts it there.

Needs openpyxl (not part of KiCad's Python: run it from a venv made with --system-site-packages, so that pcbnew and
Pillow stay visible). Run it again whenever the board's controlled traces change.
"""
import collections
import copy
import os
import subprocess
import sys
import tempfile
import zipfile

import pcbnew
from openpyxl import load_workbook
from openpyxl.comments import Comment
from openpyxl.drawing.image import Image as XLImage
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'gen'))
import route_rules  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
MIL = 0.0254
PX = 40                                       # layer plot, pixels per mm
LAYERS = [('F.Cu', 'L1', 'L2', 'out'), ('In2.Cu', 'L3', 'L2 (near, 0.10 mm), L5 (far)', 'inn'),
          ('In3.Cu', 'L4', 'L5 (near, 0.10 mm), L2 (far)', 'inn'), ('B.Cu', 'L6', 'L5', 'out')]
TARGET = {'MIPI100': 100, 'USB90': 90, 'PCIE85': 85, 'SE50': 50}
USE = {'MIPI100': 'MIPI DSI/CSI, PCIe ref. clock', 'USB90': 'USB 2.0 / USB 3.0', 'PCIE85': 'PCIe (Wi-Fi)',
       'SE50': 'Wi-Fi antenna, microSD'}


def layer_pictures(board, eb, tmp):
    """KiCad's own plot of each signal layer (what the Gerber holds), black copper on white"""
    pics = {}
    for L, *_ in LAYERS:
        svg = os.path.join(tmp, L.replace('.', '_') + '.svg')
        png = svg[:-4] + '.png'
        subprocess.run(['kicad-cli', 'pcb', 'export', 'svg', '--layers', L, '--mode-single', '--page-size-mode', '2',
                        '--exclude-drawing-sheet', '--black-and-white', '-o', svg, board],
                       capture_output=True, check=True)
        subprocess.run(['rsvg-convert', '-w', str(int(pcbnew.ToMM(eb.GetWidth()) * PX)), '-b', 'white', svg,
                        '-o', png], check=True)
        pics[L] = Image.open(png).convert('L')
    return pics


def close_up(pic, eb, L, t, cls):
    """a CAM-style close-up (red copper on black) 3.2 mm square around the middle of track t, the trace or pair
    boxed in yellow; returns it with the centre in board mm"""
    mm = pcbnew.ToMM
    k = pic.width / mm(eb.GetWidth())
    x0, y0 = mm(eb.GetX()), mm(eb.GetY())
    a, c = t.GetStart(), t.GetEnd()
    mx, my = (mm(a.x) + mm(c.x)) / 2, (mm(a.y) + mm(c.y)) / 2
    half = 1.6
    g = pic.crop((int((mx - half - x0) * k), int((my - half - y0) * k),
                  int((mx + half - x0) * k), int((my + half - y0) * k)))
    img = Image.new('RGB', g.size, (0, 0, 0))
    img.paste((210, 20, 20), (0, 0), g.point(lambda v: 255 if v < 128 else 0))
    w, s = route_rules.GEOM[cls]['out' if L in ('F.Cu', 'B.Cu') else 'inn']
    r = (w + s / 2 if s else w / 2) + 0.12
    d = ImageDraw.Draw(img)
    d.rectangle(((half - r) * k, (half - r) * k, (half + r) * k, (half + r) * k), outline=(255, 230, 0), width=3)
    return img.resize((170, 170), Image.LANCZOS), mx, my


def into_zip(zpath, f):
    """f into the zip, replacing a member of that name (zipfile cannot overwrite one in place)"""
    arc = os.path.basename(f)
    tmp = zpath + '.tmp'
    with zipfile.ZipFile(zpath) as zi, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
        for m in zi.infolist():
            if m.filename != arc:
                zo.writestr(m, zi.read(m))
        zo.write(f, arc)
    os.replace(tmp, zpath)


def main():
    template, board, out = sys.argv[1:4]
    name = os.path.splitext(os.path.basename(board))[0]
    b = pcbnew.LoadBoard(board)
    segs, nets = collections.defaultdict(list), collections.defaultdict(set)
    for t in b.GetTracks():
        if t.Type() != pcbnew.PCB_TRACE_T:
            continue
        net = t.GetNetname().split('/')[-1]
        cls = route_rules.classify(net)
        if cls in TARGET:
            L = b.GetLayerName(t.GetLayer())
            segs[(L, cls)].append(t)
            nets[(L, cls)].add(net)
    rows = []
    for L, ln, ref, side in LAYERS:
        for cls in TARGET:
            if (L, cls) in segs:
                w, s = route_rules.GEOM[cls][side]
                rows.append((L, ln, ref, cls, w, s, max(segs[(L, cls)], key=lambda t: t.GetLength())))

    wb = load_workbook(template)
    ws = wb.active
    style = {col: copy.copy(ws[f'{col}2']._style) for col in 'ABCDEFGH'}
    opts = ws['C2'].comment                   # JLCPCB's list of impedance types
    ws._images = []                           # their example picture, anchored at H2, would cover row 2's
    eb = b.GetBoardEdgesBoundingBox()
    with tempfile.TemporaryDirectory() as tmp:
        pics = layer_pictures(board, eb, tmp)
        for i, (L, ln, ref, cls, w, s, t) in enumerate(rows):
            r = 2 + i
            if r > 2:
                ws.merge_cells(f'D{r}:E{r}')      # as the template's row 2
            for col in 'ABCDEFGH':
                ws[f'{col}{r}']._style = copy.copy(style[col])
            ws[f'A{r}'] = ln
            ws[f'B{r}'] = ref
            ws[f'C{r}'] = 'Differential Pair (Non coplanar)' if s else 'Single Ended (Non coplanar)'
            ws[f'D{r}'] = round(w / MIL, 2)
            ws[f'F{r}'] = round(s / MIL, 2) if s else '-'
            ws[f'G{r}'] = TARGET[cls]
            ws.row_dimensions[r].height = 128     # the 160 px picture is 120 pt
            img, mx, my = close_up(pics[L], eb, L, t, cls)
            p = os.path.join(tmp, f'pos_{ln}_{cls}.png')
            img.save(p, dpi=(96, 96))
            xi = XLImage(p)
            xi.width = xi.height = 160
            xi.anchor = f'H{r}'
            ws.add_image(xi)
            txt = (f'{cls} ({USE[cls]}) on {ln} {L}: {w:.3f} mm' + (f' / gap {s:.3f} mm' if s else '') +
                   f'. Picture centre: Gerber X {mx:.2f} mm, Y {-my:.2f} mm (absolute origin). Nets: ' +
                   ', '.join(sorted(nets[(L, cls)])))
            ws[f'H{r}'].comment = Comment(txt, name)
            ws[f'H{r}'].comment.width, ws[f'H{r}'].comment.height = 420, 220
        if opts is not None:
            ws['C2'].comment = opts
        ws[f'A{len(rows) + 3}'] = (
            "Stack-up JLC06121H-3313A. Widths / gaps from JLCPCB's impedance calculator for it. Outer layers: copper "
            f'pour >= 0.30 mm from every controlled trace (non-coplanar). Full drawing: {name}-Impedance_Drawing.gbr '
            'in the Gerber zip (drawing only).')
        wb.save(out)                          # the pictures are read from tmp here
    print(f'{len(rows)} rows -> {out}')
    if len(sys.argv) > 4:
        into_zip(sys.argv[4], out)
        print(f'  and into {sys.argv[4]}')
    for L, ln, ref, cls, w, s, t in rows:
        print(f'  {ln} ref {ref:30s} {cls:8s} W {w / MIL:.2f} mil' + (f' S {s / MIL:.2f} mil' if s else '') +
              f'  {TARGET[cls]} ohm')


if __name__ == '__main__':
    main()
