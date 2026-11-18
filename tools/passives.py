#!/usr/bin/env python3
"""Pick JLCPCB parts for generic passives and store them in gen/data/passives.json.
usage: passives.py KEY [KEY ...] | -f missing_passives.txt
KEY = R_<size>_<value> | C_<size>_<value>_<V>V | LED_<size>_<colour>
Rules: JLC Basic library first, then Preferred-Extended, then highest stock. Resistors 1 % (0 Ohm any).
Capacitors: exact value, rated voltage >= required, C0G/NP0 for <= 1 nF, X5R/X7R otherwise."""
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlc_search import search, lib
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gen', 'data', 'passives.json')


def attrs(c):
    return {a['attribute_name_en']: a['attribute_value_name'] for a in (c.get('attributes') or [])}


def rank(c):
    return (0 if lib(c) == 'BASIC' else 1 if lib(c) == 'PREF-EXT' else 2, -(c.get('stockCount') or 0))


def cap_farads(s):
    m = re.fullmatch(r'([\d.]+)\s*(pF|nF|uF|µF)', s)
    if not m:
        return None
    return float(m.group(1)) * {'pF': 1e-12, 'nF': 1e-9, 'uF': 1e-6, 'µF': 1e-6}[m.group(2)]


def pick(key):
    kind, size, rest = key.split('_', 2)
    cands = {}
    if kind == 'R':
        want = rest + 'Ω'
        for kw in (f'{size} {want}', f'{want} {size} 1%'):
            for c in search(kw, 50)[1]:
                cands[c['componentCode']] = c
            time.sleep(0.8)
        ok = [c for c in cands.values() if c.get('componentSpecificationEn') == size
              and attrs(c).get('Resistance') == want and (c.get('stockCount') or 0) > 1000
              and (rest == '0' or attrs(c).get('Tolerance') in ('±1%', '±0.5%', '±0.1%'))]
    elif kind == 'C':
        val, v = rest.rsplit('_', 1)
        need_v = float(v.rstrip('V'))
        f = cap_farads(val)
        for kw in (f'{size} {val}', f'{size} {val} {v}'):
            for c in search(kw, 50)[1]:
                cands[c['componentCode']] = c
            time.sleep(0.8)

        def good(c):
            a = attrs(c)
            if c.get('componentSpecificationEn') != size or (c.get('stockCount') or 0) < 1000:
                return False
            cf = cap_farads(a.get('Capacitance', '').replace('μ', 'u'))
            if cf is None or abs(cf - f) / f > 0.01:
                return False
            try:
                if float(a.get('Voltage Rating', '0V').rstrip('V')) < need_v:
                    return False
            except ValueError:
                return False
            tc = a.get('Temperature Coefficient', '')
            return tc in ('C0G', 'NP0') if f <= 1e-9 + 1e-15 and f < 1.5e-9 else tc in ('X5R', 'X7R', 'X6S', 'X7S', 'C0G', 'NP0')
        ok = [c for c in cands.values() if good(c)]
    elif kind == 'LED':
        for c in search(f'{size} {rest} LED', 50)[1]:
            cands[c['componentCode']] = c
        ok = [c for c in cands.values() if c.get('componentSpecificationEn') == size and rest.lower() in
              (c.get('describe') or '').lower() and (c.get('stockCount') or 0) > 1000]
    else:
        return None
    if not ok:
        return None
    c = sorted(ok, key=rank)[0]
    return {'lcsc': c['componentCode'], 'mpn': c['componentModelEn'], 'mfr': c['componentBrandEn'],
            'lib': lib(c), 'stock': c.get('stockCount'), 'desc': (c.get('describe') or '')[:120]}


if __name__ == '__main__':
    keys = sys.argv[1:]
    if keys and keys[0] == '-f':
        keys = [k.strip() for k in open(keys[1]) if k.strip()]
    db = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for k in keys:
        if k in db:
            continue
        try:
            r = pick(k)
        except Exception as e:
            print(k, 'ERROR', e); continue
        if r:
            db[k] = r
            print(f"{k:28s} {r['lcsc']:10s} {r['lib']:8s} {r['mpn']:28s} {r['mfr'][:20]:20s} {r['stock']}")
        else:
            print(f'{k:28s} NOT FOUND')
        json.dump(db, open(OUT, 'w'), indent=1, sort_keys=True)
