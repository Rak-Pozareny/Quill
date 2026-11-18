#!/usr/bin/env python3
"""Find words on a PDF page and print their fractional positions. usage: pdfwords.py PDF PAGE REGEX"""
import sys, subprocess, re, html
pdf, page, rx = sys.argv[1], int(sys.argv[2]), re.compile(sys.argv[3])
out = subprocess.run(['pdftotext', '-f', str(page), '-l', str(page), '-bbox', pdf, '-'], capture_output=True, text=True).stdout
m = re.search(r'<page width="([\d.]+)" height="([\d.]+)"', out)
W, H = float(m.group(1)), float(m.group(2))
for w in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', out):
    t = html.unescape(w.group(5))
    if rx.search(t):
        x0, y0 = float(w.group(1)) / W, float(w.group(2)) / H
        print(f'{t}\t{x0:.3f}\t{y0:.3f}')
