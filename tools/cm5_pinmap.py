"""As-built CM5 pin map from the Board A netlist -> docs/checkpoint2/cm5_pin_map.csv
Columns: connector, CM5 pin, Radxa net name, SoC GPIO, carrier net, connected to (ref.pin(function))."""
import csv, json, os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'gen'))
from sexpr import parse, find, find_all
pins = json.load(open(os.path.join(ROOT, 'gen', 'data', 'cm5_pins.json')))
root = parse(open(os.path.join(ROOT, 'hw', 'board_a', 'cm5_carrier.net')).read())[0]
vals = {str(find(c, 'ref')[1]): str(find(c, 'value')[1]) for c in find_all(find(root, 'components'), 'comp')}
by_node, members = {}, {}
for n in find_all(find(root, 'nets'), 'net'):
    nm = str(find(n, 'name')[1]).split('/')[-1]
    nodes = [(str(find(x, 'ref')[1]), str(find(x, 'pin')[1]), str(find(x, 'pinfunction')[1]) if find(x, 'pinfunction') else '')
             for x in find_all(n, 'node')]
    members[nm] = nodes
    for r, p, f in nodes:
        by_node[(r, p)] = nm
conn = {'A': 'J301', 'B': 'J302', 'C': 'J303'}
rows = []
used = 0
for letter in 'ABC':
    for k in range(1, 101):
        cm5pin = k + (100 if letter == 'B' else 0)
        info = pins[letter][str(cm5pin)]
        net = by_node.get((conn[letter], str(k)), '')
        if net.startswith('unconnected'):
            net = ''
        other = '' if net in ('', 'GND') else ', '.join(f'{r}.{p}' for r, p, f in members[net] if r != conn[letter])
        if net and net != 'GND':
            used += 1
        rows.append([letter, cm5pin, info['net'], info['gpio'], net or 'NC', other])
out = os.path.join(ROOT, 'docs', 'checkpoint2', 'cm5_pin_map.csv')
with open(out, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['connector', 'cm5_pin', 'radxa_net', 'soc_gpio', 'carrier_net', 'connected_to'])
    w.writerows(rows)
print(out, 'signal/power pins used (excl. GND):', used)
