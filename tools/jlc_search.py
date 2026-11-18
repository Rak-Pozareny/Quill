#!/usr/bin/env python3
"""Query JLCPCB's parts library (same endpoint the jlcpcb.com/parts page uses).
usage: jlc_search.py [-n N] KEYWORD [KEYWORD ...]
Prints LCSC code | MPN | brand | package | library (basic/preferred/extended) | JLC stock | unit price @1 / @100 | description."""
import sys, json, time, urllib.request
URL = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'
def search(kw, n=6):
    body = json.dumps({"currentPage": 1, "pageSize": n, "keyword": kw, "searchSource": "search"}).encode()
    req = urllib.request.Request(URL, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=40) as r:
        d = json.load(r)
    info = (d.get('data') or {}).get('componentPageInfo') or {}
    return info.get('total', 0), info.get('list') or []
def price_at(prices, q):
    best = None
    for p in prices or []:
        if p['startNumber'] <= q and (p['endNumber'] == -1 or q <= p['endNumber']):
            best = p['productPrice']
    return best
def lib(c):
    t = c.get('componentLibraryType')
    if t == 'base': return 'BASIC'
    if c.get('preferredComponentFlag'): return 'PREF-EXT'
    return 'EXT' if t == 'expand' else str(t)
if __name__ == '__main__':
    args = sys.argv[1:]; n = 6
    if args and args[0] == '-n': n = int(args[1]); args = args[2:]
    for kw in args:
        try:
            total, lst = search(kw, n)
        except Exception as e:
            print(f'## {kw}: ERROR {e}'); continue
        print(f'## {kw}  (total {total})')
        for c in lst:
            p1 = price_at(c.get('componentPrices'), 1); p100 = price_at(c.get('componentPrices'), 100)
            print(f"  {c.get('componentCode')} | {c.get('componentModelEn')} | {c.get('componentBrandEn')} | {c.get('componentSpecificationEn')} | {lib(c)} | stock {c.get('stockCount')} | ${p1} / ${p100} | {(c.get('describe') or '')[:110]}")
        time.sleep(1.2)
