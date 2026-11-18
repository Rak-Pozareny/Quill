#!/usr/bin/env python3
"""Parts cost of a board's JLCPCB BOM, live prices.
usage: bom_cost.py fab/<board>/BOM.csv [--boards N]

For every BOM line: the JLCPCB unit price at the quantity bought for N boards (JLCPCB sells at least the part's
minimum order quantity; the cost counted here is what that purchase costs), library type (basic / extended: JLCPCB
charges a feeder fee per extended part type and order). Prints a table and the totals per board and per order."""
import csv
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlc_search import search, price_at, lib  # noqa: E402


def main():
    path = sys.argv[1]
    boards = int(sys.argv[sys.argv.index('--boards') + 1]) if '--boards' in sys.argv else 5
    rows = list(csv.DictReader(open(path)))
    total, ext, out = 0.0, 0, []
    for r in rows:
        lcsc, qty = r['LCSC Part #'], len(r['Designator'].split(','))
        try:
            n, lst = search(lcsc, 5)
            c = next((x for x in lst if x.get('componentCode') == lcsc), None)
        except Exception:
            c = None
        time.sleep(0.6)
        if c is None:
            out.append((r['Comment'], lcsc, qty, '?', '', '', 'NOT FOUND'))
            continue
        need = qty * boards
        moq = c.get('minPurchaseNum') or c.get('minImage') or 1
        buy = max(need, int(moq) if str(moq).isdigit() else 1)
        unit = price_at(c.get('componentPrices'), buy) or 0.0
        cost = unit * buy
        total += cost
        lb = lib(c)
        ext += lb != 'BASIC'
        out.append((r['Comment'], lcsc, qty, lb, f'{unit:.4f}', f'{cost:.2f}', ''))
    w = csv.writer(sys.stdout)
    w.writerow(['Comment', 'LCSC', 'Qty per board', 'Library', 'Unit price (USD)', f'Cost for {boards} boards (USD)',
                'Note'])
    w.writerows(out)
    print(f'# parts for {boards} boards: {total:.2f} USD ({total / boards:.2f} per board); {len(rows)} part types, '
          f'{ext} not in the basic library', file=sys.stderr)


if __name__ == '__main__':
    main()
