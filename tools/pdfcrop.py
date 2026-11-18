#!/usr/bin/env python3
"""Render one PDF page at high DPI (pdftoppm) and save crops given as fractional boxes.
usage: pdfcrop.py PDF PAGE DPI OUTPREFIX x0,y0,x1,y1 [x0,y0,x1,y1 ...]   (fractions 0..1 of page)"""
import sys, subprocess, os, tempfile
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
pdf, page, dpi, outp = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
boxes = sys.argv[5:]
with tempfile.TemporaryDirectory() as td:
    base = os.path.join(td, 'p')
    subprocess.run(['pdftoppm', '-r', str(dpi), '-f', str(page), '-l', str(page), '-png', pdf, base], check=True)
    fn = [f for f in os.listdir(td) if f.endswith('.png')][0]
    im = Image.open(os.path.join(td, fn))
    W, H = im.size
    for i, b in enumerate(boxes):
        x0, y0, x1, y1 = [float(v) for v in b.split(',')]
        c = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
        out = f'{outp}_{i}.png'
        c.save(out)
        print(out, c.size)
