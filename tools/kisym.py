"""Search KiCad standard symbol libraries; print pins of matches.
usage: kisym.py [-p] PATTERN...   (-p prints pin tables)"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gen'))
import symlib
D = symlib.KICAD_SYM_DIR
show = '-p' in sys.argv
pats = [a for a in sys.argv[1:] if a != '-p']
for f in sorted(os.listdir(D)):
    if not f.endswith('.kicad_sym'):
        continue
    txt = open(os.path.join(D, f), encoding='utf-8').read()
    names = re.findall(r'^\t\(symbol "([^"]+)"', txt, re.M)
    for n in names:
        if any(re.search(p, n, re.I) for p in pats):
            lib = f[:-10]
            line = f'{lib}:{n}'
            if show:
                s = symlib.load(line)
                fp = [x for x in s.node if isinstance(x, list) and x[0] == 'property' and x[1] == 'Footprint']
                print(line, '| fp:', fp[0][2] if fp else '')
                for p in sorted(s.pins, key=lambda p: (p.unit, int(re.sub(r'\D', '', p.number) or 0))):
                    print(f'   u{p.unit} {p.number:>16} {p.name:<20} {p.etype}{" (hidden)" if p.hidden else ""}')
            else:
                print(line)
