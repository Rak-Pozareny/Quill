"""Search KiCad standard footprint libraries by regex on Lib:Name. usage: kifp.py PATTERN..."""
import os, re, sys
D = '/usr/share/kicad/footprints'
for lib in sorted(os.listdir(D)):
    if not lib.endswith('.pretty'):
        continue
    for f in sorted(os.listdir(os.path.join(D, lib))):
        n = f'{lib[:-7]}:{f[:-10]}'
        if all(re.search(p, n, re.I) for p in sys.argv[1:]):
            print(n)
