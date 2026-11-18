#!/usr/bin/env python3
"""Grouped BOM from a generated project's netlist + live JLCPCB check of every LCSC number.
usage: bom.py <project_dir> <name> <out.csv> [--boards N] [--no-check]
Columns: Comment, Designator, Footprint, LCSC, MPN, Manufacturer, Qty, Sourcing, JLC lib, JLC stock, Check, Status/Note"""
import csv, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gen'))
from sexpr import parse, find, find_all
from jlc_search import search, lib

d, name, out = sys.argv[1], sys.argv[2], sys.argv[3]
boards = int(sys.argv[sys.argv.index('--boards') + 1]) if '--boards' in sys.argv else 5
check = '--no-check' not in sys.argv
root = parse(open(os.path.join(d, name + '.net')).read())[0]
groups = {}
for c in find_all(find(root, 'components'), 'comp'):
    ref = str(find(c, 'ref')[1])
    f = {}
    for x in find_all(find(c, 'fields') or [], 'field'):
        nm = find(x, 'name')
        f[str(nm[1])] = str(x[2]) if len(x) > 2 else ''
    val = str(find(c, 'value')[1])
    fp = str(find(c, 'footprint')[1]) if find(c, 'footprint') else ''
    src = f.get('Sourcing', 'JLC')
    if src == 'PCB' or ref.startswith('#'):
        continue
    dnp = 'dnp' in [str(x[0]) for x in c if isinstance(x, list)] or src == 'DNP'
    key = (val, fp, f.get('LCSC', ''), 'DNP' if dnp else src)
    g = groups.setdefault(key, {'refs': [], 'f': f})
    g['refs'].append(ref)
rows = []
cache = {}
for (val, fp, lcsc, src), g in sorted(groups.items(), key=lambda kv: (kv[0][3] != 'JLC', kv[0][2], kv[0][0])):
    f = g['f']
    jl, stock, chk = '', '', ''
    if lcsc and check and src != 'DNP':
        if lcsc not in cache:
            try:
                total, lst = search(lcsc, 5)
                cache[lcsc] = next((x for x in lst if x.get('componentCode') == lcsc), None)
            except Exception as e:
                cache[lcsc] = None
            time.sleep(0.6)
        c = cache[lcsc]
        if c is None:
            chk = 'NOT FOUND'
        else:
            jl, stock = lib(c), c.get('stockCount')
            mpn_ok = re.sub(r'[^A-Z0-9]', '', (f.get('MPN') or '').upper())[:8] in re.sub(r'[^A-Z0-9]', '', c['componentModelEn'].upper())
            need = len(g['refs']) * boards
            chk = ('OK' if mpn_ok else f"MPN MISMATCH: JLC={c['componentModelEn']}") + \
                  ('' if (stock or 0) >= need else f' LOW STOCK (need {need})')
    elif src == 'DNP':
        chk = 'not fitted'
    elif not lcsc:
        chk = 'no LCSC (see Sourcing)'
    refs = sorted(g['refs'], key=lambda r: (re.sub(r'\d', '', r), int(re.sub(r'\D', '', r) or 0)))
    rows.append([val, ','.join(refs), fp.split(':')[-1], lcsc, f.get('MPN', ''), f.get('Manufacturer', ''), len(refs),
                 src, jl, stock, chk, '; '.join(x for x in (f.get('Status', ''), f.get('Note', '')) if x)])
with open(out, 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC', 'MPN', 'Manufacturer', 'Qty', 'Sourcing', 'JLC lib',
                f'JLC stock {time.strftime("%Y-%m-%d")}', f'Check ({boards} boards)', 'Status / note'])
    w.writerows(rows)
bad = [r for r in rows if r[10] not in ('OK', 'not fitted', '') and not r[10].startswith('no LCSC')]
print(f'{len(rows)} BOM lines, {sum(r[6] for r in rows)} parts; problems: {len(bad)}')
for r in bad:
    print('  ', r[0], r[1][:40], r[3], r[4], '->', r[10])
nolcsc = [r for r in rows if r[10].startswith('no LCSC')]
for r in nolcsc:
    print('   no LCSC:', r[0], r[1][:40], r[7])
