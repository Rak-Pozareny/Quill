#!/usr/bin/env python3
"""Images for the README (docs/media/): 3D renders of both boards and Board A's six copper layers.

    python3 -I tools/media.py            (needs kicad-cli, rsvg-convert and ImageMagick's magick)

The renders use a temporary copy of each board with the solder-mask colour set (Board A: purple, as ordered from
JLCPCB; Board B: green), placed beside the original so the 3D models resolve; the copy is deleted afterwards and the
board files are not changed. The copper plots are KiCad's own SVG export of each layer with the board outline, as
seen from the top.
"""
import os
import re
import shutil
import subprocess
import tempfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OUT = os.path.join(ROOT, 'docs', 'media')
BOARDS = {'a': ('hw/board_a/cm5_carrier.kicad_pcb', 'Purple'), 'b': ('hw/board_b/q20_keyboard.kicad_pcb', 'Green')}
VIEWS = {'top': ('top', '-40,0,-30'), 'bottom': ('bottom', '40,0,30')}
LAYERS = [('F.Cu', 'L1  F.Cu  signal'), ('In1.Cu', 'L2  In1.Cu  ground plane'), ('In2.Cu', 'L3  In2.Cu  signal'),
          ('In3.Cu', 'L4  In3.Cu  signal'), ('In4.Cu', 'L5  In4.Cu  ground plane'), ('B.Cu', 'L6  B.Cu  signal')]
COPPER, BACKGROUND = '#c8963e', '#10151c'


def run(*cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        raise SystemExit(f'failed ({r.returncode}): {" ".join(cmd)}\n{r.stderr[-2000:]}')


def coloured_copy(path, colour):
    """A copy of the board beside it with the solder-mask colour set in the stack-up."""
    t = open(path).read()
    for side in ('Top', 'Bottom'):
        t, n = re.subn(r'(\(type "%s Solder Mask"\))' % side, r'\1 (color "%s")' % colour, t, count=1)
        assert n == 1, (path, side)
    tmp = os.path.join(os.path.dirname(path), '_media_tmp.kicad_pcb')
    open(tmp, 'w').write(t)
    return tmp


def renders():
    for b, (rel, colour) in BOARDS.items():
        tmp = coloured_copy(os.path.join(ROOT, rel), colour)
        try:
            for name, (side, rot) in VIEWS.items():
                png = os.path.join(OUT, f'board_{b}_{name}.png')
                run('kicad-cli', 'pcb', 'render', '-o', png, '-w', '2400', '-h', '1600', '--side', side, '--rotate', rot,
                    '--quality', 'high', '--use-board-stackup-colors', '--zoom', '0.95', tmp)
                run('magick', png, '-trim', '+repage', '-bordercolor', 'none', '-border', '24', '-resize', '1600x>', png)
        finally:
            for f in (tmp, tmp[:-len('.kicad_pcb')] + '.kicad_prl'):     # kicad-cli writes a .kicad_prl beside it
                if os.path.exists(f):
                    os.remove(f)


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
    renders()
    copper()
    for f in sorted(os.listdir(OUT)):
        print(f'docs/media/{f}  {os.path.getsize(os.path.join(OUT, f)) // 1024} KiB')
