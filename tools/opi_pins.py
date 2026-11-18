#!/usr/bin/env python3
"""Parse the Orange Pi CM5 'core board interface PIN definition' V1.1 (2025-07,
research/dl/orangepi/opi_cm5_pin_definition_v1.1_2025-07.pdf) into gen/data/opi_cm5_pins.json:

    {"JP1": {"1": {"signal": "GND", "gpio": null, "domain": null, "desc": "Ground (0V)"}, ...}, "JP2": ..., "JP3": ...}

usage: opi_pins.py [PDF]

The tables are read by word position (pdftotext -bbox): each pin pair is a row band around its pin numbers. Only the
'Signal' / 'Pin Net' column (the pin's name) and the description are kept; the long function lists wrap across rows
and are not parsed (the functions the design uses are quoted per pin in docs/opi/opi_cm5_pin_map.csv, read off the
PDF pages).

IO domain per GPIO, from the Orange Pi CM5 base board V1.2 schematic, sheet 10 (CON_JP3) note:
GPIO0 1.8 V; GPIO1_A*, B*, C0, C1, C4, C6, D0-D3, D5 = GPIO_VREF (JP1.78); GPIO3 1.8 V; GPIO4 3.3 V; I2S0 1.8 V
(GPIO1_C2, C3, C5, C7, D4). GPIO1_D6 / D7 are not in the note: 'UNVERIFIED'.
"""
import html
import json
import os
import re
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PDF = os.path.join(ROOT, 'research', 'dl', 'orangepi', 'opi_cm5_pin_definition_v1.1_2025-07.pdf')
OUT = os.path.join(ROOT, 'gen', 'data', 'opi_cm5_pins.json')

COLS = [('desc_l', 0.0, 0.226), ('name_l', 0.226, 0.429), ('net_l', 0.429, 0.489), ('odd', 0.489, 0.508),
        ('even', 0.508, 0.524), ('sig_r', 0.524, 0.615), ('name_r', 0.615, 0.803), ('desc_r', 0.803, 1.0)]

# pins whose 'Signal' column is a function name: the GPIO behind it, from the pin-name column of the same PDF
GPIO_OF = {
    ('JP1', 51): 'GPIO0_B6', ('JP1', 55): 'GPIO0_B5', ('JP1', 57): 'GPIO4_D5', ('JP1', 61): 'GPIO4_D3',
    ('JP1', 62): 'GPIO4_D4', ('JP1', 63): 'GPIO4_D0', ('JP1', 67): 'GPIO4_D1', ('JP1', 69): 'GPIO4_D2',
    ('JP1', 75): 'GPIO0_A5', ('JP1', 80): 'GPIO4_B1', ('JP1', 82): 'GPIO4_B0',
    ('JP2', 51): 'GPIO4_C1', ('JP2', 99): 'GPIO4_C0', ('JP2', 100): 'GPIO4_B7',
    ('JP3', 68): 'GPIO1_C2', ('JP3', 69): 'GPIO1_C5', ('JP3', 70): 'GPIO1_C7', ('JP3', 71): 'GPIO1_C3',
    ('JP3', 73): 'GPIO1_D4',
}
# signal names the word-position parse splits across two rows (checked on the PDF page)
SIGNAL_FIX = {('JP2', 24): 'PCIE20_2_TXN/SATA30_2_TXN'}
VREF = {'C0', 'C1', 'C4', 'C6', 'D0', 'D1', 'D2', 'D3', 'D5'}


def domain(gpio):
    if not gpio:
        return None
    bank, pin = gpio[4], gpio[6:8]
    if bank == '0' or bank == '3':
        return '1.8V'
    if bank == '4':
        return '3.3V'
    if pin[0] in 'AB' or pin in VREF:
        return 'GPIO_VREF'
    if pin in ('C2', 'C3', 'C5', 'C7', 'D4'):
        return '1.8V'
    return 'UNVERIFIED'


def rows(pdf):
    out, conn, last = [], 0, 999
    for page in range(1, 5):
        txt = subprocess.run(['pdftotext', '-f', str(page), '-l', str(page), '-bbox', pdf, '-'],
                             capture_output=True, text=True, check=True).stdout
        m = re.search(r'<page width="([\d.]+)" height="([\d.]+)"', txt)
        W, H = float(m.group(1)), float(m.group(2))
        words = []
        for w in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>',
                             txt):
            x0, y0, x1, y1 = (float(w.group(i)) for i in range(1, 5))
            words.append((html.unescape(w.group(5)), x0 / W, (y0 + y1) / 2 / H))
        pins = sorted((y, int(t)) for t, x, y in words if t.isdigit() and 0.489 <= x < 0.508)
        heads = [y for t, x, y in words if t.startswith('OPi_CM5_CORE')]
        for i, (y, n) in enumerate(pins):
            if n < last:
                conn += 1
            last = n
            ylo = (pins[i - 1][0] + y) / 2 if i else y - 0.012
            yhi = (pins[i + 1][0] + y) / 2 if i + 1 < len(pins) else y + 0.012
            for hy in heads:                   # a table title between two rows ends the band
                if i and pins[i - 1][0] < hy < y:
                    ylo = max(ylo, hy + 0.008)
                if i + 1 < len(pins) and y < hy < pins[i + 1][0]:
                    yhi = min(yhi, hy - 0.008)
            r = {'conn': f'JP{conn}', 'pin': n}
            for name, a, b in COLS:
                ws = sorted((wy, wx, t) for t, wx, wy in words if a <= wx < b and ylo <= wy < yhi)
                r[name] = ' '.join(t for _, _, t in ws if not re.fullmatch(r'[一-鿿]+', t))
            out.append(r)
    return out


def clean(sig):
    sig = re.sub(r'^(Signal|PIN|NO\.)\s*', '', sig).strip()
    return sig.replace('/ ', '/').split(' ')[0] if sig else sig


def main():
    pdf = sys.argv[1] if len(sys.argv) > 1 else PDF
    data = {'JP1': {}, 'JP2': {}, 'JP3': {}}
    for r in rows(pdf):
        for n, sig, desc in ((r['pin'], r['net_l'], r['desc_l']), (r['pin'] + 1, r['sig_r'], r['desc_r'])):
            sig = SIGNAL_FIX.get((r['conn'], n)) or clean(sig)
            g = re.fullmatch(r'GPIO\d_[A-D]\d', sig)
            gpio = sig if g else GPIO_OF.get((r['conn'], n))
            data[r['conn']][str(n)] = {'signal': sig, 'gpio': gpio, 'domain': domain(gpio),
                                       'desc': re.sub(r'^Description\s*', '', desc).strip()}
    for c in data:
        assert sorted(map(int, data[c])) == list(range(1, 101)), c
    json.dump(data, open(OUT, 'w'), indent=1, ensure_ascii=False)
    print(f'wrote {OUT}')


if __name__ == '__main__':
    main()
