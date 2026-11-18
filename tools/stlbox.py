"""Bounding box and height profile of an STL (binary or ASCII).
usage: stlbox.py file.stl [--zslices]"""
import struct, sys
fn = sys.argv[1]
data = open(fn, 'rb').read()
tris = []
if data[:5] == b'solid' and b'facet' in data[:2000]:
    pts = []
    for line in data.decode(errors='ignore').splitlines():
        line = line.strip()
        if line.startswith('vertex'):
            pts.append(tuple(map(float, line.split()[1:4])))
    tris = [pts[i:i + 3] for i in range(0, len(pts), 3)]
else:
    n = struct.unpack('<I', data[80:84])[0]
    off = 84
    for i in range(n):
        v = struct.unpack('<12f', data[off:off + 48])
        tris.append([v[3:6], v[6:9], v[9:12]])
        off += 50
xs = [p[0] for t in tris for p in t]; ys = [p[1] for t in tris for p in t]; zs = [p[2] for t in tris for p in t]
print(f'triangles {len(tris)}')
print(f'x {min(xs):.3f} .. {max(xs):.3f}  ({max(xs)-min(xs):.3f})')
print(f'y {min(ys):.3f} .. {max(ys):.3f}  ({max(ys)-min(ys):.3f})')
print(f'z {min(zs):.3f} .. {max(zs):.3f}  ({max(zs)-min(zs):.3f})')
if '--zslices' in sys.argv:
    # histogram of max z over a 1 mm xy grid
    import math
    grid = {}
    for t in tris:
        for p in t:
            k = (math.floor(p[0]), math.floor(p[1]))
            grid[k] = max(grid.get(k, -1e9), p[2])
    hs = sorted(grid.values())
    for q in (0.5, 0.9, 0.99, 1.0):
        print(f'height percentile {q}: {hs[min(len(hs)-1, int(q*len(hs)))]:.3f}')
