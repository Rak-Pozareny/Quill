#!/usr/bin/env python3
"""Images for the README (docs/media/): 3D renders of both boards and Board A's six copper layers.

    python3 -I tools/media.py            (needs kicad-cli, rsvg-convert, ImageMagick's magick, and the network once)

Renders: each board is copied beside its original (so the 3D model paths resolve) with the solder-mask colour set
(Board A: purple, as ordered from JLCPCB; Board B: green), and on that copy only:
- the box models of the parts are replaced by the parts' real models from the JLCEDA / EasyEDA Official Library
  (https://lceda.cn/, https://easyeda.com), fitted onto our pads (tools/models3d.py); downloads are cached in
  research/dl/easyeda_3d/ (not in git);
- the Orange Pi CM5 box becomes a model of the module (tools/models3d.py opi_cm5), and the LTE card one of the
  EM060K-GL card.
The copy is deleted afterwards; the board files are not changed. board_a_hero.png adds a reflection: the underside,
rendered from the mirror-image camera, below the board as on a glossy surface.

Copper plots: KiCad's own SVG export of each layer with the board outline, as seen from the top.
"""
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import models3d as m3   # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OUT = os.path.join(ROOT, 'docs', 'media')
CACHE = os.path.join(ROOT, 'research', 'dl', 'easyeda_3d')
BOARDS = {'a': ('hw/board_a/cm5_carrier.kicad_pcb', 'fab/board_a/BOM.csv', 'Purple'),
          'b': ('hw/board_b/q20_keyboard.kicad_pcb', 'fab/board_b/BOM.csv', 'Green')}
TOP, BOTTOM = ('top', '-40,0,-30'), ('bottom', '40,0,30')
MIRROR = ('bottom', '40,0,-30', '-flop')       # the underside as a mirror below the board shows it (outline IoU 0.997)
LAYERS = [('F.Cu', 'L1  F.Cu  signal'), ('In1.Cu', 'L2  In1.Cu  ground plane'), ('In2.Cu', 'L3  In2.Cu  signal'),
          ('In3.Cu', 'L4  In3.Cu  signal'), ('In4.Cu', 'L5  In4.Cu  ground plane'), ('B.Cu', 'L6  B.Cu  signal')]
COPPER, BACKGROUND = '#c8963e', '#10151c'
# parts EasyEDA has no model for, shown with a model of a part of the same kind and land pattern:
# HDGC 0520-HX-30PWB (30-pin 0.5 mm flip-lock FPC) as XUNPU FPC-05F-30PH15
STANDIN = {'C3041205': 'C2856824'}


def run(*cmd, env=None):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, env=env)
    if r.returncode:
        raise SystemExit(f'failed ({r.returncode}): {" ".join(cmd)}\n{r.stderr[-2000:]}')


def sexpr_end(t, i):
    """Index just past the s-expression starting at t[i] == '('."""
    depth, q = 0, False
    for k in range(i, len(t)):
        c = t[k]
        if q:
            if c == '\\':
                continue
            if c == '"' and t[k - 1] != '\\':
                q = False
        elif c == '"':
            q = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return k + 1
    raise ValueError('unbalanced')


def footprints(t):
    """[(start, end, ref, layer, angle, pads, model span or None)] for every footprint in a board file."""
    res = []
    for mo in re.finditer(r'\n\t\(footprint ', t):
        s = mo.start() + 2
        e = sexpr_end(t, s)
        b = t[s:e]
        ref = re.search(r'\(property "Reference" "([^"]*)"', b).group(1)
        layer = re.search(r'\(layer "([FB])\.Cu"\)', b).group(1)
        at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', b)
        ang = float(at.group(3) or 0)
        pads = []
        for pm in re.finditer(r'\(pad "[^"]*" (?:smd|thru_hole|np_thru_hole|connect)', b):
            pe = sexpr_end(b, pm.start())
            p = b[pm.start():pe]
            a = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', p)
            sz = re.search(r'\(size ([-\d.]+) ([-\d.]+)\)', p)
            w, h = float(sz.group(1)), float(sz.group(2))
            if round(float(a.group(3) or 0) - ang) % 180 == 90:
                w, h = h, w
            pads.append((float(a.group(1)), float(a.group(2)), w, h))
        mi = b.find('(model ')
        model = (s + mi, s + sexpr_end(b, mi)) if mi >= 0 else None
        res.append((s, e, ref, layer, ang, pads, model))
    return res


def bom(path):
    out = {}
    for row in csv.DictReader(open(path)):
        for r in row['Designator'].split(','):
            out[r.strip()] = row['LCSC Part #']
    return out


def real_models(t, board, bom_path, tmp, log):
    """Board text with the box models replaced, for the render copy only."""
    refs = bom(os.path.join(ROOT, bom_path))
    edits, made = [], {}
    for s, e, ref, layer, ang, pads, model in footprints(t):
        if not model:
            continue
        path = re.search(r'\(model "([^"]+)"', t[model[0]:model[1]]).group(1)
        if 'cm5h.3dshapes' not in path:
            continue                                   # KiCad library model: already a real one
        mesh = None
        if board == 'a' and ref == 'J301':
            mesh, note = m3.opi_cm5(), 'Orange Pi CM5 model'
        elif 'USB_A_HOAUC_HYCW236' in t[s:e]:
            mesh, note = m3.usb_a(), 'USB-A model from the HOAUC drawing'
        elif 'Molex_Micro-Lock_Plus_505578' in t[s:e]:
            mesh, note = m3.molex_505578(), 'Molex 505578 model from the Molex drawing'
        else:
            code = STANDIN.get(refs.get(ref), refs.get(ref))
            key = code
            if key in made:
                mesh, note = made[key]
            elif code:
                try:
                    fp, obj = m3.easyeda_fetch(code, CACHE)
                    mesh, note = m3.easyeda_model(fp, obj, pads) if fp else (None, 'no 3D model in EasyEDA')
                except Exception as ex:                # network or format trouble: keep the box
                    mesh, note = None, f'EasyEDA: {ex}'
                made[key] = (mesh, note)
            else:
                note = 'not in the BOM'
            if board == 'a' and ref == 'J501':
                card = m3.lte_card()
                if mesh:
                    card.add(mesh)
                mesh, note = card, note + ' + EM060K-GL card'
        log.append(f'{board.upper()} {ref:6s} {code if (code := refs.get(ref)) else "":10s} {note if mesh else "kept box: " + note}')
        if mesh:
            wrl = os.path.join(tmp, f'{board}_{ref}.wrl')
            mesh.write_wrl(wrl)
            edits.append((model, f'(model "{wrl}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'))
    for (a, b), new in sorted(edits, reverse=True):
        t = t[:a] + new + t[b:]
    return t


def render_copy(board, tmp, log):
    rel, bom_path, colour = BOARDS[board]
    path = os.path.join(ROOT, rel)
    t = open(path).read()
    for side in ('Top', 'Bottom'):
        t, n = re.subn(r'(\(type "%s Solder Mask"\))' % side, r'\1 (color "%s")' % colour, t, count=1)
        assert n == 1, (path, side)
    t = real_models(t, board, bom_path, tmp, log)
    copy = os.path.join(os.path.dirname(path), '_media_tmp.kicad_pcb')
    open(copy, 'w').write(t)
    return copy


RENDER_ENV = None


def render_env(tmp):
    """A KiCad configuration for the renders: the user's (paths to KiCad's 3D library) with the raytracer set
    explicitly: shadows, reflections, anti-aliasing and post-processing on, no floor (it adds a grey slab)."""
    global RENDER_ENV
    src = os.path.expanduser('~/.config/kicad/10.0')
    if not os.path.isdir(src):
        return None
    cfg = os.path.join(tmp, 'kicad_config')
    shutil.copytree(src, os.path.join(cfg, '10.0'))
    p = os.path.join(cfg, '10.0', '3d_viewer.json')
    d = json.load(open(p))
    d.setdefault('render', {}).update(raytrace_backfloor=False, raytrace_shadows=True, raytrace_reflections=True,
                                      raytrace_anti_aliasing=True, raytrace_post_processing=True,
                                      raytrace_procedural_textures=True)
    json.dump(d, open(p, 'w'), indent=2)
    RENDER_ENV = dict(os.environ, KICAD_CONFIG_HOME=cfg)
    return RENDER_ENV


def render(copy, out, side, rot, w=2400, h=1600, quality='high'):
    if quality == 'high' and RENDER_ENV:
        quality = 'user'
    run('kicad-cli', 'pcb', 'render', '-o', out, '-w', str(w), '-h', str(h), '--side', side, '--rotate', rot,
        '--quality', quality, '--use-board-stackup-colors', '--zoom', '0.95', copy, env=RENDER_ENV)


def trim(png, width=1600):
    run('magick', png, '-trim', '+repage', '-bordercolor', 'none', '-border', '24', '-resize', f'{width}x>', png)


def hero(copy, tmp, out, gap=300, strength=55):
    """Board A from the top with its reflection on a glossy surface below it: the underside, seen by the mirror-image
    camera, is the bottom-side render mirrored left to right (its outline matches the top view's, IoU 0.997);
    it sits gap px below the board and fades out downward from strength % opacity."""
    W, H = 2400, 1600
    top, under = os.path.join(tmp, 'hero_top.png'), os.path.join(tmp, 'hero_under.png')
    render(copy, top, *TOP, w=W, h=H)
    render(copy, under, MIRROR[0], MIRROR[1], w=W, h=H)
    run('magick', under, MIRROR[2], under)
    box = subprocess.run(['magick', under, '-format', '%@', 'info:'], capture_output=True, text=True).stdout
    bw, bh, bx, by = map(int, re.match(r'(\d+)x(\d+)\+(\d+)\+(\d+)', box).groups())
    CH = H + gap + 40
    shifted, grad, refl = (os.path.join(tmp, n) for n in ('hero_shift.png', 'hero_grad.png', 'hero_refl.png'))
    run('magick', '-size', f'{W}x{CH}', 'xc:none', under, '-geometry', f'+0+{gap}', '-composite', shifted)
    gy, gh = by + gap, int(bh * 0.8)
    run('magick', '-size', f'{W}x{CH}', 'xc:black', '(', '-size', f'{W}x{gh}', f'gradient:gray{strength}-black', ')',
        '-geometry', f'+0+{gy}', '-composite', grad)
    run('magick', shifted, '(', '+clone', '-alpha', 'extract', grad, '-compose', 'multiply', '-composite', ')',
        '-alpha', 'off', '-compose', 'copy-opacity', '-composite', '-channel', 'RGBA', '-blur', '0x1.6', refl)
    run('magick', refl, top, '-geometry', '+0+0', '-compose', 'over', '-composite', out)
    trim(out, 1700)


def renders():
    log = []
    with tempfile.TemporaryDirectory() as tmp:
        render_env(tmp)
        for b in BOARDS:
            copy = render_copy(b, tmp, log)
            try:
                for name, (side, rot) in (('top', TOP), ('bottom', BOTTOM)):
                    png = os.path.join(OUT, f'board_{b}_{name}.png')
                    render(copy, png, side, rot)
                    trim(png)
                if b == 'a':
                    hero(copy, tmp, os.path.join(OUT, 'board_a_hero.png'))
            finally:
                for f in (copy, copy[:-len('.kicad_pcb')] + '.kicad_prl'):   # kicad-cli writes a .kicad_prl too
                    if os.path.exists(f):
                        os.remove(f)
    return log


def copper():
    pcb = os.path.join(ROOT, BOARDS['a'][0])
    with tempfile.TemporaryDirectory() as tmp:
        tiles = []
        for layer, label in LAYERS:
            svg, png = os.path.join(tmp, layer + '.svg'), os.path.join(tmp, layer + '.png')
            run('kicad-cli', 'pcb', 'export', 'svg', '--mode-single', '-o', svg, '-l', f'{layer},Edge.Cuts',
                '--black-and-white', '--page-size-mode', '2', '--exclude-drawing-sheet', '--drill-shape-opt', '2', pcb)
            run('rsvg-convert', '-w', '1100', '-b', 'white', svg, '-o', png)
            # black copper on white -> copper colour on the dark background
            run('magick', png, '-colorspace', 'gray', '-negate', '-alpha', 'copy', '-fill', COPPER, '-colorize', '100',
                '-background', BACKGROUND, '-flatten', '-gravity', 'north', '-splice', '0x60', '-fill', '#e6edf3',
                '-font', 'DejaVu-Sans', '-pointsize', '32', '-annotate', '+0+12', label, png)
            tiles.append(png)
        out = os.path.join(OUT, 'board_a_copper_layers.png')
        run('magick', 'montage', *tiles, '-tile', '3x2', '-geometry', '+14+14', '-background', BACKGROUND, out)
        run('magick', out, '-resize', '1800x>', out)


if __name__ == '__main__':
    for tool in ('kicad-cli', 'rsvg-convert', 'magick'):
        if not shutil.which(tool):
            raise SystemExit(f'{tool} not found')
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)
    for line in renders():
        print(line)
    if '--no-copper' not in sys.argv:
        copper()
    for f in sorted(os.listdir(OUT)):
        print(f'docs/media/{f}  {os.path.getsize(os.path.join(OUT, f)) // 1024} KiB')
