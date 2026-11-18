#!/usr/bin/env python3
"""Check the compiled board device tree against the board.

usage: check_dtb.py [DTB]   (default software/build/rk3588s-orangepi-cm5-handheld.dtb)

1. Pin conflicts: every pin claimed by an enabled node, through its pinctrl states or a GPIO property, by more than one
   node (or by one node with two functions).
2. GPIOs against the board: every GPIO the tree uses on a connector pin is compared with docs/opi/opi_cm5_pin_map.csv
   (the net on that pin); pins the module uses internally are listed separately.
3. Graph endpoints: every remote-endpoint points back.
"""
import csv
import os
import re
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DTB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'software', 'build', 'rk3588s-orangepi-cm5-handheld.dtb')
BANK = 'ABCD'


def parse(text):
    """minimal DTS parser for dtc's own output: {path: {prop: raw value}}"""
    nodes, stack = {}, []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('/dts-v1/'):
            continue
        m = re.match(r"^(?:[\w-]+:\s*)*([\w,@.+-]+|/)\s*\{$", line)
        if m:
            stack.append(m.group(1))
            path = '/' + '/'.join(stack[1:]) if len(stack) > 1 else '/'
            nodes[path] = {}
            continue
        if line == '};':
            stack.pop()
            continue
        path = '/' + '/'.join(stack[1:]) if len(stack) > 1 else '/'
        m = re.match(r'^([\w,#.+-]+)(?:\s*=\s*(.*))?;$', line)
        if m:
            nodes[path][m.group(1)] = m.group(2) or ''
    return nodes


def cells(v):
    return [int(x, 0) for x in re.findall(r'0x[0-9a-f]+|\b\d+\b', ' '.join(re.findall(r'<([^>]*)>', v)))]


def main():
    text = subprocess.run(['dtc', '-I', 'dtb', '-O', 'dts', DTB], capture_output=True, text=True).stdout
    nodes = parse(text)
    ph = {int(p['phandle'].strip('<>'), 0): path for path, p in nodes.items() if 'phandle' in p}

    def enabled(path):
        parts = path.split('/')
        for k in range(2, len(parts) + 1):
            st = nodes.get('/'.join(parts[:k]) or '/', {}).get('status', '"okay"')
            if st.strip('"') not in ('okay', 'ok'):
                return False
        return True

    gpio_ctrl = {}
    for path, p in nodes.items():
        m = re.search(r'/gpio@([0-9a-f]+)$', path)
        if m and 'gpio-controller' in p:
            gpio_ctrl[int(p['phandle'].strip('<>'), 0)] = path
    # bank number of each gpio controller from its alias
    aliases = nodes.get('/aliases', {})
    bank_of = {}
    for k, v in aliases.items():
        m = re.fullmatch(r'gpio(\d)', k)
        if m:
            bank_of[v.strip('"')] = int(m.group(1))

    claims = {}       # (bank, pin) -> [(consumer, how)]
    for path, p in nodes.items():
        if path.startswith('/pinctrl/') or not enabled(path):
            continue
        for prop, v in p.items():
            if re.fullmatch(r'pinctrl-\d+', prop):
                for h in cells(v):
                    grp = nodes.get(ph.get(h, ''), {})
                    c = cells(grp.get('rockchip,pins', ''))
                    for i in range(0, len(c), 4):
                        claims.setdefault((c[i], c[i + 1]), []).append((path, f'{prop} func {c[i + 2]}'))
            elif re.search(r'gpios?$|_gpio$|_gpios$|gpio$', prop, re.I) and prop != 'gpio-controller':
                c = cells(v)
                i = 0
                while i + 2 < len(c) + 1 and i < len(c):
                    if c[i] in gpio_ctrl:
                        bank = bank_of.get(gpio_ctrl[c[i]])
                        claims.setdefault((bank, c[i + 1]), []).append((path, prop))
                        i += 3
                    else:
                        i += 1
    name = lambda bp: f'GPIO{bp[0]}_{BANK[bp[1] // 8]}{bp[1] % 8}'

    print('== 1. pins claimed by more than one node (a pinctrl GPIO state plus a GPIO property of the same node is fine)')
    bad = 0
    for bp, cl in sorted(claims.items()):
        owners = {c[0] for c in cl}
        funcs = {c[1].split('func ')[1] for c in cl if 'func' in c[1]}
        gp = any('func' not in c[1] for c in cl)
        conflict = len(owners) > 1 or len(funcs) > 1 or (gp and funcs - {'0'})
        if conflict:
            bad += 1
            print(f'  {name(bp)}: ' + '; '.join(f'{o} ({h})' for o, h in cl))
    print(f'  {bad} conflicts')

    pinmap = {}
    for r in csv.DictReader(open(os.path.join(ROOT, 'docs', 'opi', 'opi_cm5_pin_map.csv'))):
        if r['gpio']:
            pinmap[r['gpio']] = (f"{r['connector']}.{r['pin']}", r['carrier_net'], r['function_used'])
    print('== 2. GPIOs / pins used, against the board pin map')
    for bp, cl in sorted(claims.items()):
        g = name(bp)
        where = pinmap.get(g)
        users = '; '.join(sorted({f"{o.split('/')[-1]} ({h})" for o, h in cl}))
        if where:
            print(f'  {g:10s} {where[0]:8s} {where[1]:18s} <- {users}')
        else:
            print(f'  {g:10s} {"module":8s} {"(not on a connector)":18s} <- {users}')
    unused = [f'{g} {w[0]} {w[1]}' for g, w in sorted(pinmap.items()) if w[1] not in ('NC', '')
              and not any(name(bp) == g for bp in claims)]
    print('  board GPIOs with a net that the tree does not touch (left as inputs):')
    for u in unused:
        print('    ', u)

    print('== 3. graph endpoints')
    eps = {path: p for path, p in nodes.items() if 'remote-endpoint' in p and enabled(path)}
    broken = 0
    for path, p in eps.items():
        other = ph.get(cells(p['remote-endpoint'])[0])
        back = nodes.get(other, {}).get('remote-endpoint')
        if not back or ph.get(cells(back)[0]) != path:
            broken += 1
            print(f'  {path} -> {other} does not point back')
        elif not enabled(other):
            broken += 1
            print(f'  {path} -> {other} is disabled')
    print(f'  {len(eps)} endpoints, {broken} broken')


if __name__ == '__main__':
    main()
