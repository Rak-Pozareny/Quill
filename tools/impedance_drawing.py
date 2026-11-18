#!/usr/bin/env python3
"""Impedance requirements for the fab's CAM engineers, from the board itself: the stack-up and reference planes, the
target, model and width / gap of every controlled class per layer (JLCPCB's own impedance calculator for stack-up
JLC06121H-3313A, research/jlc/impedance_selected.json; gen/route_rules.GEOM), the nets of each class, and one map per
signal layer of where those traces run.

usage: impedance_drawing.py BOARD.kicad_pcb OUTDIR NAME

Writes into OUTDIR:
  NAME-Impedance_Drawing.gbr   the tables and maps on a drawing layer (Gerber X2 FileFunction Other,Drawing), below
                               the board outline in the board's own coordinates; tools/fab.py puts it into the Gerber
                               zip, where JLCPCB reads every file as a layer: it is a drawing, nothing on it is made
  NAME_impedance.pdf           the same, in colour, to send to the fab with the order
  IMPEDANCE.md                 the tables as text
"""
import json
import math
import os
import shutil
import sys
import tempfile

import pcbnew
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'gen'))
import route_rules  # noqa: E402

STACKUP = 'JLC06121H-3313A'
# layer: (file, role, model, reference) - the calculator's own model names and heights (tools/jlc_impedance.py)
LAYERS = [
    ('F.Cu', 'L1', 'gtl', 'signal', 'coated microstrip', 'L2 GND plane, 3313 prepreg 0.0994 mm (Er 4.1), solder mask over'),
    ('In1.Cu', 'L2', 'g1', 'GND plane', '', 'reference for L1 and L3'),
    ('In2.Cu', 'L3', 'g2', 'signal', 'offset stripline',
     'near: L2 GND, core 0.10 mm (Er 4.36); far: L5 GND, 0.754 mm (7628 x3 + L4 + core)'),
    ('In3.Cu', 'L4', 'g3', 'signal', 'offset stripline',
     'near: L5 GND, core 0.10 mm (Er 4.36); far: L2 GND, 0.754 mm'),
    ('In4.Cu', 'L5', 'g4', 'GND plane', '', 'reference for L4 and L6'),
    ('B.Cu', 'L6', 'gbl', 'signal', 'coated microstrip', 'L5 GND plane, 3313 prepreg 0.0994 mm (Er 4.1), solder mask over'),
]
TARGET = {'MIPI100': ('100 ohm differential', 'MIPI DSI / CSI lanes, PCIe reference clocks'),
          'USB90': ('90 ohm differential', 'USB 2.0 pairs, USB 3.0 to the LTE modem'),
          'PCIE85': ('85 ohm differential', 'PCIe 2.0 to the Wi-Fi module'),
          'SE50': ('50 ohm single-ended', 'Wi-Fi antenna feeds, microSD clock / command / data')}
COLOUR = {'MIPI100': (31, 119, 180), 'USB90': (44, 160, 44), 'PCIE85': (255, 127, 14), 'SE50': (148, 103, 189)}
SIGNAL = ['F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu']


def mm(v):
    return pcbnew.ToMM(v)


def nm(v):
    return pcbnew.FromMM(v)


def solver():
    """(class, 'out'/'inn') -> ohms, from the calculator results the geometry was chosen with"""
    res = json.load(open(os.path.join(ROOT, 'research', 'jlc', 'impedance_selected.json')))
    z = {}
    for cls, g in route_rules.GEOM.items():
        for side in ('out', 'inn'):
            w, s = g[side]
            for r in res.values():
                outer = 'Microstrip' in r['model']
                if outer == (side == 'out') and abs(r['W_mm'] - w) < 1e-6 and \
                        ((s is None and r['S_mm'] is None) or (s is not None and r['S_mm'] is not None and abs(r['S_mm'] - s) < 1e-6)):
                    z[(cls, side)] = r['Z']
    return z


def collect(b):
    """class -> {layer: [(start, end, width)]}, class -> sorted net names, class -> vias"""
    tracks, nets, vias = {}, {}, {}
    for t in b.GetTracks():
        short = t.GetNetname().split('/')[-1]
        cls = route_rules.classify(short)
        if cls not in TARGET:
            continue
        nets.setdefault(cls, set()).add(short)
        if t.Type() == pcbnew.PCB_VIA_T:
            vias.setdefault(cls, []).append((mm(t.GetPosition().x), mm(t.GetPosition().y)))
        elif t.Type() == pcbnew.PCB_TRACE_T:
            tracks.setdefault(cls, {}).setdefault(b.GetLayerName(t.GetLayer()), []).append(
                ((mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y)), mm(t.GetWidth())))
    return tracks, {k: sorted(v) for k, v in nets.items()}, vias


def rows(z, nets):
    """the class table as rows of strings"""
    out = [('Class', 'Target', 'L1 / L6 width / gap (mm)', 'L3 / L4 width / gap (mm)', 'Calculated', 'Used for')]
    for cls, (tgt, use) in TARGET.items():
        g = route_rules.GEOM[cls]
        f = lambda wg: f'{wg[0]:.3f}' + (f' / {wg[1]:.3f}' if wg[1] else ' (single)')
        out.append((cls, tgt, f(g['out']), f(g['inn']),
                    f'{z.get((cls, "out"), 0):.1f} / {z.get((cls, "inn"), 0):.1f} ohm', use))
    return out


def notes(b):
    t = b.GetDesignSettings()
    return [
        f'Stack-up {STACKUP} (JLCPCB template; 6 layers, 1.2 mm, NP-155F, 1 oz outer / 0.5 oz inner). '
        'Impedance tolerance +-10 % (+-5 ohm at 50 ohm and below).',
        'Widths and gaps are from JLCPCB\'s impedance calculator for this stack-up (Polar Si9000 models: coated '
        'microstrip outside, offset stripline inside, etch factor and mask as the calculator\'s defaults).',
        'Outer layers: the copper pour keeps at least 0.30 mm from every controlled trace, so these are plain '
        '(non-coplanar) microstrips; the inner signal layers carry no pour beside them.',
        'Only the traces of the classes below are controlled. Please adjust their width within tolerance if your '
        'process needs it; keep the gaps of each pair as drawn, and do not change other traces.',
        'This file is a drawing: nothing on it is to be made.',
    ]


def gerber(path, b, out, name, tracks, nets, vias, z):
    eb = b.GetBoardEdgesBoundingBox()
    X0, Y0, X1, Y1 = mm(eb.GetX()), mm(eb.GetY()), mm(eb.GetRight()), mm(eb.GetBottom())
    W, H = X1 - X0, Y1 - Y0
    # drawn on a second, unsaved copy of the board (a new empty BOARD has no project, and KiCad aborts freeing it);
    # what the copy already has on the drawing layer (some footprints draw there) moves to User.9 first
    d = pcbnew.LoadBoard(path)
    L = pcbnew.Dwgs_User
    for fp in d.GetFootprints():
        for gi in fp.GraphicalItems():
            if gi.GetLayer() == L:
                gi.SetLayer(pcbnew.User_9)
    for e in d.GetDrawings():
        if e.GetLayer() == L:
            e.SetLayer(pcbnew.User_9)
    tmp = tempfile.mkdtemp()

    def text(s, x, y, size=1.2, bold=False):
        t = pcbnew.PCB_TEXT(d)
        t.SetText(s)
        t.SetLayer(L)
        t.SetTextSize(pcbnew.VECTOR2I(nm(size), nm(size)))
        t.SetTextThickness(nm(size * (0.2 if bold else 0.13)))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_TOP)
        t.SetPosition(pcbnew.VECTOR2I(nm(x), nm(y)))
        d.Add(t)

    def seg(a, c, w):
        s = pcbnew.PCB_SHAPE(d, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(nm(a[0]), nm(a[1])))
        s.SetEnd(pcbnew.VECTOR2I(nm(c[0]), nm(c[1])))
        s.SetWidth(nm(w))
        s.SetLayer(L)
        d.Add(s)

    def outline(dx, dy):
        for e in b.GetDrawings():
            if e.GetLayer() != pcbnew.Edge_Cuts or not isinstance(e, pcbnew.PCB_SHAPE):
                continue
            sh = e.GetShape()
            mv = lambda p: pcbnew.VECTOR2I(p.x + nm(dx), p.y + nm(dy))
            n = pcbnew.PCB_SHAPE(d, sh)
            if sh == pcbnew.SHAPE_T_ARC:
                n.SetArcGeometry(mv(e.GetStart()), mv(e.GetArcMid()), mv(e.GetEnd()))
            elif sh == pcbnew.SHAPE_T_CIRCLE:
                n.SetCenter(mv(e.GetCenter()))
                n.SetEnd(mv(e.GetEnd()))
            else:
                n.SetStart(mv(e.GetStart()))
                n.SetEnd(mv(e.GetEnd()))
            n.SetWidth(nm(0.15))
            n.SetLayer(L)
            d.Add(n)

    # tables below the board
    x, y = X0, Y1 + 10
    text(f'IMPEDANCE CONTROL - {name} - DRAWING ONLY, NOT A FABRICATION LAYER', x, y, 2.0, True)
    y += 4
    for line in notes(b):
        text(line, x, y, 1.0)
        y += 1.8
    y += 2
    text('Layer stack and reference planes', x, y, 1.4, True)
    y += 2.6
    cols = (0, 18, 32, 55, 80)
    for c, s in zip(cols, ('Layer', 'Gerber', 'Use', 'Model', 'Reference')):
        text(s, x + c, y, 1.1, True)
    y += 2
    for lay, ln, ext, role, model, ref in LAYERS:
        for c, s in zip(cols, (f'{ln} {lay}', f'.{ext}', role, model, ref)):
            text(s, x + c, y, 1.0)
        y += 1.8
    y += 2
    text('Controlled-impedance classes', x, y, 1.4, True)
    y += 2.6
    cols = (0, 18, 50, 85, 120, 150)
    for k, r in enumerate(rows(z, nets)):
        for c, s in zip(cols, r):
            text(s, x + c, y, 1.1 if k == 0 else 1.0, k == 0)
        y += 2.0
    y += 2
    text('Nets per class', x, y, 1.4, True)
    y += 2.6
    for cls in TARGET:
        ns = nets.get(cls, [])
        line, lines = '', []
        for n in ns:
            if len(line) + len(n) > 150:
                lines.append(line)
                line = ''
            line += n + '  '
        lines.append(line)
        text(f'{cls}:', x, y, 1.0, True)
        for ln_ in lines:
            text(ln_, x + 18, y, 1.0)
            y += 1.8
        y += 0.6
    # one map per signal layer, 2 x 2, each with the board outline and that layer's controlled traces
    y += 6
    for k, lay in enumerate(SIGNAL):
        dx = (k % 2) * (W + 20)
        dy = y - Y0 + (k // 2) * (H + 18)
        ln = next(l for l in LAYERS if l[0] == lay)
        text(f'{ln[1]} {lay} ({ln[4]}): controlled traces; width / gap per the table', X0 + dx, Y0 + dy - 4, 1.3, True)
        outline(dx, dy)
        for cls in TARGET:
            for a, c, w in tracks.get(cls, {}).get(lay, []):
                seg((a[0] + dx, a[1] + dy), (c[0] + dx, c[1] + dy), w)
    pc = pcbnew.PLOT_CONTROLLER(d)
    po = pc.GetPlotOptions()
    po.SetOutputDirectory(tmp)
    po.SetUseGerberProtelExtensions(False)
    po.SetUseGerberX2format(True)
    po.SetIncludeGerberNetlistInfo(False)
    po.SetCreateGerberJobFile(False)
    pc.SetLayer(L)
    pc.OpenPlotfile('Impedance_Drawing', pcbnew.PLOT_FORMAT_GERBER, 'Impedance drawing')
    pc.PlotLayer()
    pc.ClosePlot()
    src = [f for f in os.listdir(tmp) if f.endswith('.gbr')][0]
    dst = os.path.join(out, f'{name}-Impedance_Drawing.gbr')
    shutil.copy(os.path.join(tmp, src), dst)
    shutil.rmtree(tmp)
    return dst


def pdf(b, out, name, tracks, nets, z):
    font = lambda s, bold=False: ImageFont.truetype(
        '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/TTF/DejaVuSans.ttf', s)
    PW, PH = 3508, 2480                       # A4 landscape, 300 dpi
    pages = []
    p = Image.new('RGB', (PW, PH), 'white')
    g = ImageDraw.Draw(p)
    y = 120
    g.text((120, y), f'Impedance control - {name}', fill='black', font=font(64, True))
    y += 110
    for line in notes(b):
        g.text((120, y), line, fill='black', font=font(34))
        y += 52
    y += 40
    g.text((120, y), 'Layer stack and reference planes', fill='black', font=font(44, True))
    y += 70
    cols = (120, 520, 720, 1060, 1480)
    for c, s in zip(cols, ('Layer', 'Gerber', 'Use', 'Model', 'Reference')):
        g.text((c, y), s, fill='black', font=font(34, True))
    y += 54
    for lay, ln, ext, role, model, ref in LAYERS:
        for c, s in zip(cols, (f'{ln} {lay}', f'.{ext}', role, model, ref)):
            g.text((c, y), s, fill='black', font=font(32))
        y += 48
    y += 40
    g.text((120, y), 'Controlled-impedance classes', fill='black', font=font(44, True))
    y += 70
    cols = (120, 500, 1000, 1500, 2000, 2440)
    for k, r in enumerate(rows(z, nets)):
        if k:
            g.rectangle((80, y + 8, 104, y + 32), fill=COLOUR[r[0]])
        for c, s in zip(cols, r):
            g.text((c, y), s, fill='black', font=font(32, k == 0))
        y += 52
    pages.append(p)
    p = Image.new('RGB', (PW, PH), 'white')
    g = ImageDraw.Draw(p)
    y = 120
    g.text((120, y), 'Nets per class', fill='black', font=font(44, True))
    y += 80
    for cls in TARGET:
        g.rectangle((120, y + 8, 150, y + 38), fill=COLOUR[cls])
        g.text((170, y), f'{cls} ({TARGET[cls][0]})', fill='black', font=font(36, True))
        y += 56
        line = ''
        for n in nets.get(cls, []) + ['']:
            if not n or len(line) + len(n) > 150:
                g.text((170, y), line, fill='black', font=font(30))
                y += 44
                line = ''
            line += n + '   '
        y += 30
    pages.append(p)
    eb = b.GetBoardEdgesBoundingBox()
    X0, Y0, W, H = mm(eb.GetX()), mm(eb.GetY()), mm(eb.GetWidth()), mm(eb.GetHeight())
    s = min((PW - 240) / W, (PH - 400) / H)
    for lay in SIGNAL:
        p = Image.new('RGB', (PW, PH), 'white')
        g = ImageDraw.Draw(p)
        ln = next(l for l in LAYERS if l[0] == lay)
        g.text((120, 80), f'{ln[1]} {lay}: {ln[4]}, {ln[5]}', fill='black', font=font(44, True))
        ox, oy = 120, 220
        P = lambda q: (ox + (q[0] - X0) * s, oy + (q[1] - Y0) * s)
        for t in b.GetTracks():                      # all copper of the layer, light, for orientation
            if t.Type() == pcbnew.PCB_TRACE_T and b.GetLayerName(t.GetLayer()) == lay:
                g.line([P((mm(t.GetStart().x), mm(t.GetStart().y))), P((mm(t.GetEnd().x), mm(t.GetEnd().y)))],
                       fill=(215, 215, 215), width=max(1, int(mm(t.GetWidth()) * s)))
        for e in b.GetDrawings():
            if e.GetLayer() == pcbnew.Edge_Cuts and isinstance(e, pcbnew.PCB_SHAPE) and e.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                g.line([P((mm(e.GetStart().x), mm(e.GetStart().y))), P((mm(e.GetEnd().x), mm(e.GetEnd().y)))],
                       fill='black', width=4)
        for cls in TARGET:
            for a, c, w in tracks.get(cls, {}).get(lay, []):
                g.line([P(a), P(c)], fill=COLOUR[cls], width=max(3, int(w * s)))
        x = 120
        for cls in TARGET:
            g.rectangle((x, PH - 120, x + 40, PH - 80), fill=COLOUR[cls])
            gw = route_rules.GEOM[cls]['out' if lay in ('F.Cu', 'B.Cu') else 'inn']
            lab = f'{cls}  {gw[0]:.3f}' + (f' / {gw[1]:.3f} mm' if gw[1] else ' mm')
            g.text((x + 60, PH - 124), lab, fill='black', font=font(34))
            x += 820
        pages.append(p)
    dst = os.path.join(out, f'{name}_impedance.pdf')
    pages[0].save(dst, save_all=True, append_images=pages[1:], resolution=300)
    return dst


def markdown(b, out, name, nets, z):
    o = [f'# {name}: impedance control\n']
    o += [f'- {line}' for line in notes(b)]
    o.append('\n## Layer stack and reference planes\n\n| Layer | Gerber | Use | Model | Reference |\n|---|---|---|---|---|')
    for lay, ln, ext, role, model, ref in LAYERS:
        o.append(f'| {ln} {lay} | .{ext} | {role} | {model} | {ref} |')
    r = rows(z, nets)
    o.append('\n## Controlled-impedance classes\n\n| ' + ' | '.join(r[0]) + ' |\n|' + '---|' * len(r[0]))
    o += ['| ' + ' | '.join(x) + ' |' for x in r[1:]]
    o.append('\n## Nets per class\n')
    for cls in TARGET:
        o.append(f'- **{cls}**: ' + ', '.join(nets.get(cls, [])))
    dst = os.path.join(out, 'IMPEDANCE.md')
    open(dst, 'w').write('\n'.join(o) + '\n')
    return dst


def main():
    board, out, name = sys.argv[1], sys.argv[2], sys.argv[3]
    b = pcbnew.LoadBoard(board)
    tracks, nets, vias = collect(b)
    if not tracks:
        print('no controlled-impedance traces: nothing written')
        return
    z = solver()
    for f in (gerber(board, b, out, name, tracks, nets, vias, z), pdf(b, out, name, tracks, nets, z),
              markdown(b, out, name, nets, z)):
        print(f'wrote {f}')


if __name__ == '__main__':
    main()
