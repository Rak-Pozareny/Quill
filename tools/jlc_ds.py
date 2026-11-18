#!/usr/bin/env python3
"""Download the datasheet JLCPCB hosts for an LCSC part (via its file-access id) and convert it to text.
usage: jlc_ds.py C138677 [C...]   -> research/dl/jlc/<code>_<mpn>.pdf (+ .txt), prints key attributes."""
import json, os, re, subprocess, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlc_search import search
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'research', 'dl', 'jlc')
os.makedirs(OUT, exist_ok=True)
for code in sys.argv[1:]:
    total, lst = search(code, 5)
    c = next((x for x in lst if x.get('componentCode') == code), None)
    if not c:
        print(f'{code}: not found'); continue
    mpn = re.sub(r'[^A-Za-z0-9._-]', '_', c.get('componentModelEn') or '')
    attrs = '; '.join(f"{a['attribute_name_en']}={a['attribute_value_name']}" for a in c.get('attributes') or [])
    print(f"{code} | {c.get('componentModelEn')} | {c.get('componentBrandEn')} | {c.get('componentSpecificationEn')} | stock {c.get('stockCount')}")
    print(f'   {attrs[:400]}')
    fid = c.get('dataManualFileAccessId')
    # JLCPCB's search now returns a signed download link (2026-11) instead of the file id
    url = c.get('dataManualFileAccessIdUrl') or (f'https://jlcpcb.com/api/file/downloadByFileSystemAccessId/{fid}' if fid else None)
    if not url:
        print('   no datasheet link'); continue
    path = os.path.join(OUT, f'{code}_{mpn}.pdf')
    if not os.path.exists(path):
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = urllib.request.urlopen(req, timeout=60).read()
        if not data.startswith(b'%PDF'):
            print('   download is not a PDF'); continue
        open(path, 'wb').write(data)
        subprocess.run(['pdftotext', '-layout', path, path[:-4] + '.txt'])
    print(f'   -> {os.path.relpath(path)}')
    time.sleep(1.0)
