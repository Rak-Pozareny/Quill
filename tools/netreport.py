"""Net report / checks on an exported KiCad netlist.
usage: netreport.py <project_dir> <name> [regex ...]   (prints nets matching regexes with pin names)
       netreport.py <project_dir> <name> --pairs       (diff-pair polarity check)"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gen'))
from sexpr import parse, find, find_all
d, name = sys.argv[1], sys.argv[2]
root = parse(open(os.path.join(d, name + '.net')).read())[0]
nets = {}
for n in find_all(find(root, 'nets'), 'net'):
    nm = str(find(n, 'name')[1]).lstrip('/')
    nodes = []
    for nd in find_all(n, 'node'):
        pf = find(nd, 'pinfunction')
        nodes.append((str(find(nd, 'ref')[1]), str(find(nd, 'pin')[1]), str(pf[1]) if pf else ''))
    nets[nm] = nodes
vals = {str(find(c, 'ref')[1]): str(find(c, 'value')[1]) for c in find_all(find(root, 'components'), 'comp')}


def pol(s):
    s = s.upper()
    s = re.sub(r'^\d+:', '', s)
    s = re.sub(r'_\d+$', '', s).replace('DPHY', 'X').replace('CPHY', 'X')
    if re.search(r'(D\+|DP|_P$|P$|\+$|_P_|TXP|RXP|CLKP|RCLK_P|TX_P|RX_P|TDP|RDP|DP_|D[0-3]P|CLKAP)', s):
        return '+'
    if re.search(r'(D-|DM|DN|_N$|N$|-$|_N_|TXN|RXN|CLKN|RCLK_N|TX_N|RX_N|TDN|RDN|DM_|D[0-3]N|CLKAN)', s):
        return '-'
    return None


if '--pairs' in sys.argv:
    bad = 0
    for nm, nodes in sorted(nets.items()):
        npol = '+' if re.search(r'(_P|_DP)$', nm) else '-' if re.search(r'(_N|_DN)$', nm) else None
        if npol is None or nm.endswith('_RESET_N') or nm.endswith('INT_N'):
            continue
        for ref, pin, pf in nodes:
            v = vals.get(ref, '')
            if ref[0] in 'RC' or ref.startswith('TP') or 'TPD4E' in v:
                continue
            p = pol(pf)
            if p is None and ref[0] == 'J' and 'FPC' in v or 'FFC' in v or 'FH35C' in v:
                continue
            if p and p != npol:
                bad += 1
                print(f'POLARITY? {nm}: {ref}.{pin} ({pf}) [{v}]')
    print('pairs checked, suspicious:', bad)
else:
    pats = sys.argv[3:]
    for nm, nodes in sorted(nets.items()):
        if any(re.search(p, nm) for p in pats):
            print(nm + ': ' + ', '.join(f'{r}.{p}({f})' for r, p, f in nodes))
