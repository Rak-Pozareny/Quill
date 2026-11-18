#!/usr/bin/env python3
"""Minimal stdlib-only xlsx dumper: prints every sheet as TSV (shared strings resolved, merged cells ignored)."""
import sys, zipfile, re
import xml.etree.ElementTree as ET
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def col2num(c):
    n = 0
    for ch in c:
        n = n * 26 + (ord(ch) - 64)
    return n
def main(path):
    z = zipfile.ZipFile(path)
    ss = []
    if 'xl/sharedStrings.xml' in z.namelist():
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in root.findall('m:si', NS):
            ss.append(''.join(t.text or '' for t in si.iter('{%s}t' % NS['m'])))
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    relmap = {r.get('Id'): r.get('Target') for r in rels}
    for sh in wb.find('m:sheets', NS):
        name = sh.get('name'); rid = sh.get('{%s}id' % NS['r'])
        target = relmap[rid].lstrip('/')
        if not target.startswith('xl/'): target = 'xl/' + target
        root = ET.fromstring(z.read(target))
        print(f'#### SHEET: {name}')
        for row in root.iter('{%s}row' % NS['m']):
            cells = {}
            for c in row.findall('m:c', NS):
                ref = c.get('r'); col = col2num(re.match(r'[A-Z]+', ref).group())
                t = c.get('t'); v = c.find('m:v', NS)
                if t == 's' and v is not None: val = ss[int(v.text)]
                elif t == 'inlineStr':
                    val = ''.join(x.text or '' for x in c.iter('{%s}t' % NS['m']))
                else: val = v.text if v is not None else ''
                cells[col] = (val or '').replace('\n', ' ').replace('\t', ' ')
            if cells:
                mx = max(cells)
                print(f"r{row.get('r')}\t" + '\t'.join(cells.get(i, '') for i in range(1, mx + 1)))
if __name__ == '__main__':
    main(sys.argv[1])
