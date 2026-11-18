"""3D models for the README renders (tools/media.py): VRML writer, the Orange Pi CM5 and LTE card models, and EasyEDA
part models fitted onto our footprints.

Only the renders use these: the board files keep their own box models, and the EasyEDA models are not stored in git.

Coordinates while building: millimetres in the footprint's frame, x right, y down (as in the .kicad_pcb), z up from
the board surface. The VRML written for KiCad is in its units (0.1 inch) with y up.

EasyEDA part models: from the JLCEDA / EasyEDA Official Library (https://lceda.cn/, https://easyeda.com), the models
JLCPCB shows for each LCSC part. A part's model is placed in EasyEDA's footprint by its SVGNODE (c_origin = centre of
the model's outline, c_rotation, z = height of the model's lowest point), and EasyEDA's footprint is then fitted onto ours by matching pad centres, so the
model lands on our pads whatever origin or rotation either footprint uses.
"""
import json
import math
import os
import subprocess
import time
import urllib.error
import urllib.request

UNIT = 0.254                      # EasyEDA footprint unit, mm
UA = 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0'


# ----------------------------------------------------------------------------------------------------------- meshes
class Mesh:
    """Faces grouped by material. mat: (diffuse rgb, specular rgb, shininess 0-1, transparency 0-1)."""

    def __init__(self):
        self.mats, self.parts = {}, {}

    def material(self, name, diffuse, specular=(0.2, 0.2, 0.2), shininess=0.2, transparency=0.0):
        self.mats[name] = (diffuse, specular, shininess, transparency)
        self.parts.setdefault(name, ([], []))
        return name

    def face(self, mat, pts):
        v, f = self.parts[mat]
        base = len(v)
        v.extend(pts)
        f.append(list(range(base, base + len(pts))))

    def box(self, mat, x0, y0, z0, x1, y1, z1):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        for q in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.face(mat, [c[i] for i in q])

    def prism(self, mat, poly, z0, z1):
        """Convex polygon (x, y) list extruded from z0 to z1."""
        n = len(poly)
        self.face(mat, [(x, y, z0) for x, y in reversed(poly)])
        self.face(mat, [(x, y, z1) for x, y in poly])
        for i in range(n):
            (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
            self.face(mat, [(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)])

    def cylinder(self, mat, cx, cy, r, z0, z1, n=32):
        self.prism(mat, [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)], z0, z1)

    def ring(self, mat, cx, cy, r0, r1, z0, z1, n=40):
        p = [(math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n)) for k in range(n + 1)]
        for k in range(n):
            (c0, s0), (c1, s1) = p[k], p[k + 1]
            i0, i1 = (cx + r0 * c0, cy + r0 * s0), (cx + r0 * c1, cy + r0 * s1)
            o0, o1 = (cx + r1 * c0, cy + r1 * s0), (cx + r1 * c1, cy + r1 * s1)
            self.face(mat, [(*i0, z1), (*o0, z1), (*o1, z1), (*i1, z1)])
            self.face(mat, [(*i0, z0), (*i1, z0), (*o1, z0), (*o0, z0)])
            self.face(mat, [(*o0, z0), (*o1, z0), (*o1, z1), (*o0, z1)])
            self.face(mat, [(*i1, z0), (*i0, z0), (*i0, z1), (*i1, z1)])

    def rounded_rect(self, mat, x0, y0, x1, y1, r, z0, z1, n=8):
        poly = []
        for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            for k in range(n + 1):
                a = math.radians(a0 + 90 * k / n)
                poly.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        self.prism(mat, poly, z0, z1)

    def text(self, mat, s, x, y, height, z0, z1, font='DejaVu-Sans-Bold', rot=0, anchor='centre'):
        """Text as raised boxes, from the font rasterised by ImageMagick. height: cap-to-baseline height in mm of the
        trimmed bitmap; rot: 0 (reads along +x, tops toward -y) or 90 / 180 / 270 counter-clockwise on the board.
        Text on a bottom-side footprint reads correctly from below as it is (checked on the LTE card)."""
        out = subprocess.run(['magick', '-background', 'black', '-fill', 'white', '-font', font, '-pointsize', '160',
                              'label:' + s, '-trim', '+repage', '-threshold', '50%', 'pbm:-'],
                             capture_output=True, check=True).stdout
        w, h, rows = _pbm(out)
        k = height / h
        runs = {}                                  # (x0, x1) -> list of [row0, row1]
        for r, row in enumerate(rows):
            c = 0
            while c < w:
                if row[c]:
                    c0 = c
                    while c < w and row[c]:
                        c += 1
                    spans = runs.setdefault((c0, c), [])
                    if spans and spans[-1][1] == r:
                        spans[-1][1] = r + 1
                    else:
                        spans.append([r, r + 1])
                else:
                    c += 1
        ox = -w * k / 2 if anchor == 'centre' else 0.0
        oy = -h * k / 2
        a = math.radians(-rot)                     # y down: counter-clockwise on screen is a negative angle
        ca, sa = math.cos(a), math.sin(a)
        for (c0, c1), spans in runs.items():
            for r0, r1 in spans:
                px0, px1, py0, py1 = ox + c0 * k, ox + c1 * k, oy + r0 * k, oy + r1 * k
                if rot % 360 == 0:
                    self.box(mat, x + px0, y + py0, z0, x + px1, y + py1, z1)
                else:
                    pts = [(px0, py0), (px1, py0), (px1, py1), (px0, py1)]
                    t = [(x + ca * u - sa * v, y + sa * u + ca * v) for u, v in pts]
                    xs, ys = [p[0] for p in t], [p[1] for p in t]
                    self.box(mat, min(xs), min(ys), z0, max(xs), max(ys), z1)

    def add(self, other, transform=None):
        for m, (v, f) in other.parts.items():
            name = self.material(m, *other.mats[m])
            vv, ff = self.parts[name]
            base = len(vv)
            vv.extend(transform(p) for p in v) if transform else vv.extend(v)
            ff.extend([[base + i for i in face] for face in f])

    def write_wrl(self, path):
        with open(path, 'w') as out:
            out.write('#VRML V2.0 utf8\n')
            for m, (v, f) in self.parts.items():
                if not f:
                    continue
                d, s, sh, tr = self.mats[m]
                # KiCad's raytracer turns shininess into mirror reflection of the (empty) surroundings: keep it low
                s, sh = tuple(min(c, 0.5) for c in s), min(sh, 0.3)
                pts = ', '.join('%.5f %.5f %.5f' % (x / 2.54, -y / 2.54, z / 2.54) for x, y, z in v)
                # y is negated for KiCad (a mirror), which turns every face inside out: reverse the vertex order so
                # the faces stay outward (KiCad's raytracer lights only the outer side)
                idx = ', '.join(', '.join(map(str, reversed(face))) + ', -1' for face in f)
                out.write('Shape { appearance Appearance { material Material { diffuseColor %.4f %.4f %.4f '
                          'specularColor %.4f %.4f %.4f shininess %.3f transparency %.3f ambientIntensity 0.3 } }\n'
                          '  geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ %s ] } coordIndex [ %s ] } }\n'
                          % (*d, *s, sh, tr, pts, idx))


def _pbm(data):
    """Parse a binary PBM (P4): width, height, rows of 0 / 1."""
    toks, i = [], 0
    while len(toks) < 3:
        while data[i:i + 1].isspace():
            i += 1
        if data[i:i + 1] == b'#':
            while data[i:i + 1] != b'\n':
                i += 1
            continue
        j = i
        while not data[j:j + 1].isspace():
            j += 1
        toks.append(data[i:j]); i = j
    i += 1
    w, h = int(toks[1]), int(toks[2])
    stride = (w + 7) // 8
    rows = []
    for r in range(h):
        b = data[i + r * stride:i + (r + 1) * stride]
        rows.append([1 - ((b[c // 8] >> (7 - c % 8)) & 1) for c in range(w)])
    return w, h, rows


# ------------------------------------------------------------------------------------------------- custom models
def opi_cm5():
    """Orange Pi CM5 (V1.1) on its carrier, in the frame of footprint J301 (module centre at the origin, 40 x 55 mm,
    JP3 toward +y). Part positions measured on a photo of the module (2026-11-18) rectified onto the four holes;
    heights estimated (Orange Pi publishes none): 1.5 mm board-to-board stack, 1.6 mm PCB, parts up to 1.2 mm."""
    m = Mesh()
    pcb = m.material('opi_pcb', (0.07, 0.20, 0.42), (0.35, 0.35, 0.4), 0.45)
    gold = m.material('opi_gold', (0.80, 0.62, 0.28), (0.9, 0.8, 0.5), 0.8)
    hole = m.material('opi_hole', (0.05, 0.05, 0.06))
    chip = m.material('opi_chip', (0.045, 0.045, 0.05), (0.15, 0.15, 0.15), 0.25)
    lid = m.material('opi_lid', (0.025, 0.025, 0.03), (0.5, 0.5, 0.5), 0.7)
    ink = m.material('opi_ink', (0.78, 0.78, 0.76), (0.1, 0.1, 0.1), 0.1)
    silk = m.material('opi_silk', (0.92, 0.92, 0.90))
    ind = m.material('opi_inductor', (0.20, 0.19, 0.18), (0.2, 0.2, 0.2), 0.2)
    metal = m.material('opi_metal', (0.72, 0.72, 0.74), (0.9, 0.9, 0.9), 0.8)
    z0, z1 = 1.5, 3.1
    m.rounded_rect(pcb, -20.0, -27.5, 20.0, 27.5, 1.6, z0, z1)
    for hx in (-16.5, 16.5):
        for hy in (-24.0, 24.0):
            m.ring(gold, hx, hy, 1.35, 2.5, z1, z1 + 0.03)
            m.cylinder(hole, hx, hy, 1.35, z1, z1 + 0.02)
    # SoC 17 x 17 with its darker lid, RAM top and right, eMMC lower left, PMIC lower right
    m.box(chip, -11.25, -15.0, z1, 5.85, 2.1, z1 + 1.2)
    m.box(lid, -8.35, -10.4, z1 + 1.2, 2.5, -2.9, z1 + 1.21)
    m.text(ink, 'Rockchip', -2.9, -8.0, 1.25, z1 + 1.21, z1 + 1.23, font='DejaVu-Sans-Bold-Oblique')
    m.text(ink, 'RK3588S', -2.9, -5.2, 1.05, z1 + 1.21, z1 + 1.23)
    m.box(chip, -10.0, -26.25, z1, 5.4, -15.85, z1 + 1.0)
    m.box(chip, 6.85, -13.35, z1, 17.1, 2.1, z1 + 1.0)
    m.box(chip, -15.4, 8.35, z1, -3.75, 21.65, z1 + 1.0)
    m.box(chip, 3.35, 13.5, z1, 10.65, 20.85, z1 + 0.85)
    for x0, y0, x1, y1, h in ((-1.5, 11.25, 2.5, 15.85, 1.2), (-1.5, 16.25, 1.85, 19.15, 1.0),
                              (4.35, 10.15, 6.5, 12.65, 1.0), (6.85, 10.15, 8.9, 12.65, 1.0), (9.4, 10.4, 11.65, 12.9, 1.0),
                              (12.35, 15.0, 15.0, 17.1, 1.0), (12.35, 17.1, 15.0, 19.0, 1.0), (12.35, 19.15, 15.0, 21.25, 1.0),
                              (14.15, 5.4, 16.65, 7.9, 0.9), (14.15, -17.9, 16.25, -15.85, 0.9), (-16.65, -20.85, -15.0, -18.75, 0.8)):
        m.box(ind, x0, y0, z1, x1, y1, z1 + h)
    m.box(metal, -1.5, 3.75, z1, 0.5, 5.65, z1 + 0.6)                      # crystal
    for y in (-13.6, -9.75, -6.5, -2.65):                                    # GND / 5V / RX / TX pads
        m.cylinder(gold, 18.85, y, 0.5, z1, z1 + 0.02, 20)
    for y in (3.9, 5.15):
        m.cylinder(gold, -16.5, y, 0.45, z1, z1 + 0.02, 20)
    m.text(silk, 'Orange Pi', -15.9, -4.0, 1.9, z1, z1 + 0.012, font='DejaVu-Sans', rot=270)
    m.text(silk, 'OPi CM5 V1.1', -13.3, -4.0, 0.9, z1, z1 + 0.012, font='DejaVu-Sans', rot=270)
    return m


def lte_card():
    """Quectel EM060K-GL M.2 3042 card in the frame of footprint J501 (HOAUC HYCW11B socket): card 30 x 42 from
    y = 3.525, bottom 1.25 mm above the board (gen/footprints.py m2()), PCB 0.8 mm, shield up to 3.55 mm."""
    m = Mesh()
    pcb = m.material('card_pcb', (0.05, 0.28, 0.12), (0.3, 0.3, 0.3), 0.4)
    gold = m.material('card_gold', (0.80, 0.62, 0.28), (0.9, 0.8, 0.5), 0.8)
    shield = m.material('card_shield', (0.66, 0.67, 0.69), (0.85, 0.85, 0.88), 0.6)
    label = m.material('card_label', (0.90, 0.90, 0.88), (0.1, 0.1, 0.1), 0.1)
    ink = m.material('card_ink', (0.08, 0.08, 0.09))
    z0, z1 = 1.25, 2.05
    m.box(pcb, -15.0, 3.525, z0, 15.0, 42.9, z1)
    m.box(pcb, -15.0, 42.9, z0, -2.0, 45.525, z1)
    m.box(pcb, 2.0, 42.9, z0, 15.0, 45.525, z1)
    for k in range(30):
        x = -9.25 + k * 0.5 * (75 / 30)
        m.box(gold, x - 0.15, 3.525, z1, x + 0.15, 6.0, z1 + 0.01)
    m.box(shield, -13.0, 8.0, z1, 13.0, 42.0, 3.55)
    m.box(label, -11.0, 12.0, 3.55, 11.0, 38.0, 3.56)
    m.text(ink, 'Quectel', 0.0, 20.5, 2.2, 3.56, 3.575, font='DejaVu-Sans-Bold')
    m.text(ink, 'EM060K-GL', 0.0, 25.5, 1.8, 3.56, 3.575)
    m.text(ink, 'LTE-A Cat 6', 0.0, 29.5, 1.2, 3.56, 3.575, font='DejaVu-Sans')
    return m


def usb_a():
    """HOAUC HYCW236-USBA04-289B, in the frame of its footprint (gen/footprints.py usba(): x centre, y = 0 at the
    rear of the board cutout, mouth toward +y, 4.33 mm above / 2.89 below the board top). No 3D model exists for it
    in EasyEDA; this one follows HOAUC's drawing: SUS 201 shell, flange 15.30 wide at 9.80, mouth to 11.30, opening
    12.50 x 5.12, black PA46T tongue 11.10 wide carrying the four contacts on its underside."""
    m = Mesh()
    steel = m.material('usba_steel', (0.74, 0.75, 0.77), (0.9, 0.9, 0.92), 0.75)
    dark = m.material('usba_inside', (0.30, 0.30, 0.32), (0.3, 0.3, 0.3), 0.3)
    tongue = m.material('usba_tongue', (0.05, 0.05, 0.06), (0.2, 0.2, 0.2), 0.3)
    gold = m.material('usba_gold', (0.80, 0.62, 0.28), (0.9, 0.8, 0.5), 0.8)
    zb, zt, t = -2.89, 4.33, 0.3
    ox0, ox1, oz0, oz1 = -6.25, 6.25, 0.72 - 2.56, 0.72 + 2.56          # opening
    m.box(steel, -7.2, 0.0, zb, 7.2, 8.92, zb + t)                          # body: bottom, top, sides, back
    m.box(steel, -7.2, 0.0, zt - t, 7.2, 8.92, zt)
    m.box(steel, -7.2, 0.0, zb, -7.2 + t, 8.92, zt)
    m.box(steel, 7.2 - t, 0.0, zb, 7.2, 8.92, zt)
    m.box(steel, -7.2, 0.0, zb, 7.2, t, zt)
    m.box(dark, ox0, t, oz0, ox1, t + 0.01, oz1)                            # back wall seen through the mouth
    for (x0, x1, z0, z1, y0, y1) in ((-7.65, 7.65, zb, oz0, 8.92, 9.80), (-7.65, 7.65, oz1, zt, 8.92, 9.80),
                                     (-7.65, ox0, oz0, oz1, 8.92, 9.80), (ox1, 7.65, oz0, oz1, 8.92, 9.80),
                                     (-6.55, 6.55, -2.5, oz0, 9.80, 11.30), (-6.55, 6.55, oz1, 3.9, 9.80, 11.30),
                                     (-6.55, ox0, oz0, oz1, 9.80, 11.30), (ox1, 6.55, oz0, oz1, 9.80, 11.30)):
        m.box(steel, x0, y0, z0, x1, y1, z1)                                # flange and mouth around the opening
    m.box(tongue, -5.55, t, 1.15, 5.55, 10.4, 3.05)
    for x in (-3.5, -1.0, 1.0, 3.5):
        m.box(gold, x - 0.5, 4.5, 1.12, x + 0.5, 10.0, 1.15)
    return m


def molex_505578():
    """Molex 505578-0971 (Micro-Lock Plus 2.0, right angle, 9 circuits, black housing: the last digit 1), in the frame of
    its footprint (gen/footprints.py molex(): x centre, y = 0 at the signal pad centres, mating face toward +y). Body
    22.0 x 8.45 x 5.9 per Molex drawing 5055780001; not in EasyEDA's library, so built from the drawing."""
    m = Mesh()
    black = m.material('mx_housing', (0.06, 0.06, 0.065), (0.25, 0.25, 0.25), 0.3)
    tin = m.material('mx_tin', (0.72, 0.72, 0.70), (0.85, 0.85, 0.85), 0.7)
    x0, x1, y0, y1, h = -11.0, 11.0, 0.15, 8.6, 5.9
    m.box(black, x0, y0, 0.0, x1, 3.2, h)                                  # rear block
    m.box(black, x0, 3.2, 0.0, x1, y1, 0.9)                                # floor of the shroud
    m.box(black, x0, 3.2, h - 0.8, x1, y1, h)                              # roof
    m.box(black, x0, 3.2, 0.9, x0 + 0.9, y1, h - 0.8)                      # side walls
    m.box(black, x1 - 0.9, 3.2, 0.9, x1, y1, h - 0.8)
    m.box(black, -2.6, y1 - 0.8, h - 1.6, 2.6, y1, h - 0.8)                # latch ramp
    for k in range(9):
        x = -8.0 + 2.0 * k
        m.box(tin, x - 0.32, 3.2, 2.6, x + 0.32, 7.6, 3.24)               # pins in the shroud
        m.box(tin, x - 0.3, -1.1, 0.0, x + 0.3, 0.4, 0.15)                # tails on the pads
        m.box(tin, x - 0.3, 0.0, 0.0, x + 0.3, 0.15, 1.2)
    for sx in (-1, 1):
        m.box(tin, sx * 10.4 - 0.75, 2.4, 0.0, sx * 10.4 + 0.75, 5.9, 0.15)  # nails
        m.box(tin, sx * 11.0 - 0.1 * sx, 2.4, 0.0, sx * 11.0 + 0.05 * sx, 5.9, 2.2)
    return m


# --------------------------------------------------------------------------------------------------------- EasyEDA
def _get(url, path, check):
    """Download once into path (a per-part cache directory); check(data) must accept the content. EasyEDA rate-limits
    with HTTP 403: back off and retry."""
    if os.path.exists(path):
        return path
    for wait in (2, 8, 20, 45, 90):
        time.sleep(wait)
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Referer': 'https://easyeda.com/',
                                                   'Accept': 'application/json, */*'})
        try:
            data = urllib.request.urlopen(req, timeout=60).read()
        except urllib.error.HTTPError as ex:
            if ex.code in (403, 429, 503):
                continue
            raise
        if not check(data):
            raise ValueError(f'unexpected content from {url}')
        open(path, 'wb').write(data)
        return path
    raise ValueError(f'rate-limited: {url}')


def _is_component(data):
    try:
        return 'packageDetail' in json.loads(data)['result']
    except Exception:
        return False


def _is_obj(data):
    head = data[:2000].decode('latin-1')
    return any(line.startswith(('v ', 'newmtl', 'usemtl')) for line in head.splitlines())


def easyeda_fetch(lcsc, cache):
    """Component JSON and OBJ model for an LCSC part, cached in cache/<lcsc>/. Returns (footprint dict, obj path)."""
    d = os.path.join(cache, lcsc)
    os.makedirs(d, exist_ok=True)
    comp = json.load(open(_get(f'https://easyeda.com/api/products/{lcsc}/components?version=6.4.19.5',
                               os.path.join(d, 'component.json'), _is_component)))
    ds = comp['result']['packageDetail']['dataStr']
    ox, oy = ds['head']['x'], ds['head']['y']
    pads, node = [], None
    for s in ds['shape']:
        f = s.split('~')
        if f[0] == 'PAD':
            w, h, rot = float(f[4]) * UNIT, float(f[5]) * UNIT, float(f[11] or 0)
            if round(rot) % 180 == 90:
                w, h = h, w
            pads.append(((float(f[2]) - ox) * UNIT, (float(f[3]) - oy) * UNIT, w, h))
        elif f[0] == 'SVGNODE':
            node = json.loads(s.split('~', 1)[1])
    if node is None:
        return None, None
    a = node['attrs']
    outline = []
    for c in node.get('childNodes', []):
        p = list(map(float, c['attrs'].get('points', '').split()))
        outline += [((x - ox) * UNIT, (y - oy) * UNIT) for x, y in zip(p[0::2], p[1::2])]
    cx, cy = map(float, a['c_origin'].split(','))
    fp = dict(pads=pads, outline=outline, origin=((cx - ox) * UNIT, (cy - oy) * UNIT),
              rot=[float(v) for v in a.get('c_rotation', '0,0,0').split(',')], z=float(a.get('z', 0)) * UNIT,
              uuid=a['uuid'], title=a.get('title', ''))
    obj = _get(f'https://modules.easyeda.com/3dmodel/{fp["uuid"]}', os.path.join(d, 'model.obj'), _is_obj)
    return fp, obj


def load_obj(path):
    """EasyEDA OBJ (mm, materials inline): Mesh in the model's own frame, y up (converted to y down here)."""
    mesh, verts, mats, cur, mat = Mesh(), [], {}, None, None
    for line in open(path, errors='replace'):
        t = line.split()
        if not t:
            continue
        if t[0] == 'newmtl':
            cur = t[1]; mats[cur] = {'Kd': (0.5, 0.5, 0.5), 'Ks': (0.2, 0.2, 0.2), 'd': 0.0}
        elif t[0] in ('Kd', 'Ks') and cur:
            mats[cur][t[0]] = tuple(float(v) for v in t[1:4])
        elif t[0] == 'd' and cur:
            mats[cur]['d'] = float(t[1])
        elif t[0] == 'v':
            verts.append((float(t[1]), -float(t[2]), float(t[3])))
        elif t[0] == 'usemtl':
            k = mats.get(t[1], {'Kd': (0.5, 0.5, 0.5), 'Ks': (0.2, 0.2, 0.2), 'd': 0.0})
            spec = k['Ks']
            mat = mesh.material('ee_' + t[1] + '_%.3f_%.3f_%.3f' % k['Kd'], k['Kd'], spec,
                                0.6 if max(spec) > 0.5 else 0.25, 0.0)      # opaque: 'd' is not used consistently
        elif t[0] == 'f' and mat:
            idx = [int(v.split('/')[0]) for v in t[1:]]
            pts = [verts[i - 1] if i > 0 else verts[i] for i in idx]
            mesh.face(mat, pts[::-1])            # y was negated: reversed so write_wrl's reversal restores it
    return mesh


def _grid(points, cell):
    g = {}
    for p in points:
        g.setdefault((int(math.floor(p[0] / cell)), int(math.floor(p[1] / cell))), []).append(p)
    return g


def _nearest(g, cell, x, y, reach=2):
    i, j, best = int(math.floor(x / cell)), int(math.floor(y / cell)), 1e9
    for di in range(-reach, reach + 1):
        for dj in range(-reach, reach + 1):
            for p in g.get((i + di, j + dj), ()):
                d = (p[0] - x) ** 2 + (p[1] - y) ** 2
                if d < best:
                    best = d
    return math.sqrt(best)


def _rot2(a):
    c, s = round(math.cos(math.radians(a)), 9), round(math.sin(math.radians(a)), 9)
    return lambda x, y: (c * x - s * y, s * x + c * y)


def easyeda_model(fp, obj_path, our_pads):
    """Fit an EasyEDA model onto our footprint. our_pads: [(x, y, w, h)] in our footprint frame (y down).
    Returns (Mesh, report) or (None, reason)."""
    raw = load_obj(obj_path)
    verts = [p for v, _ in raw.parts.values() for p in v]
    if not verts:
        return None, 'empty model'
    sub = verts[::max(1, len(verts) // 3000)]
    rx, ry, rz = fp['rot']
    # 1. model -> EasyEDA footprint: rotation sense chosen by the outline (the model's projection), centre on c_origin
    best = None
    out = fp['outline'][::max(1, len(fp['outline']) // 1500)]
    for sense in (1, -1):
        r = _rot2(-sense * rz)                       # y down
        pts = [r(x, y) for x, y, _ in sub]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        dx = fp['origin'][0] - (min(xs) + max(xs)) / 2
        dy = fp['origin'][1] - (min(ys) + max(ys)) / 2
        if out:
            g = _grid([(x + dx, y + dy) for x, y in pts], 0.25)
            score = sum(min(2.0, _nearest(g, 0.25, x, y)) for x, y in out) / len(out)
        else:
            score = 0.0
        if best is None or score < best[0]:
            best = (score, sense, dx, dy)
    oscore, sense, dx, dy = best
    r = _rot2(-sense * rz)
    zs = [p[2] for p in verts]
    dz = fp['z'] - min(zs)            # EasyEDA puts the model's lowest point at z (checked on five parts)
    tilt = (rx % 360, ry % 360)

    def to_ee(p):
        x, y, z = p
        if tilt != (0, 0):              # rare: models stood up in EasyEDA; rotate about x then y (y down frame)
            a, b = math.radians(rx), math.radians(ry)
            y, z = y * math.cos(a) + z * math.sin(a), -y * math.sin(a) + z * math.cos(a)
            x, z = x * math.cos(b) - z * math.sin(b), x * math.sin(b) + z * math.cos(b)
        x, y = r(x, y)
        return (x + dx, y + dy, z + dz)

    # 2. EasyEDA footprint -> ours: rotation in 90 degree steps and a translation voted from pad pairs
    ee = fp['pads']
    if not ee or not our_pads:
        return None, 'no pads'
    TOL = 0.2
    gour = _grid([(x, y) for x, y, _, _ in our_pads], 0.3)
    anchors = sorted(range(len(ee)), key=lambda i: -ee[i][2] * ee[i][3])[:4]
    best = None
    for rot in (0, 90, 180, 270):
        rr = _rot2(rot)
        e2 = [rr(x, y) for x, y, _, _ in ee]
        for i in anchors:
            for ox, oy, _, _ in our_pads:
                tx, ty = ox - e2[i][0], oy - e2[i][1]
                ds = [_nearest(gour, 0.3, x + tx, y + ty, 1) for x, y in e2]
                hit = [d for d in ds if d < TOL]
                key = (len(hit), -sum(hit) / max(1, len(hit)))
                if best is None or key > best[0]:
                    best = (key, rot, tx, ty, e2)
    (nhit, _), rot, tx, ty, e2 = best
    gx = [(x, y) for x, y, _, _ in our_pads]
    how = f'pads {nhit}/{len(ee)}'
    if nhit >= max(2, 0.5 * min(len(ee), len(our_pads))):
        res = []
        for x, y in e2:
            q = min(gx, key=lambda p: (p[0] - x - tx) ** 2 + (p[1] - y - ty) ** 2)
            if math.hypot(q[0] - x - tx, q[1] - y - ty) < TOL:
                res.append((q[0] - x - tx, q[1] - y - ty))
        tx += sum(a for a, _ in res) / len(res); ty += sum(b for _, b in res) / len(res)
    else:
        # different land patterns (2-pad parts with longer pads, LGA rings): pad centroids together, and the
        # rotation whose pad layout fits best; accepted only if the layouts agree to 0.5 mm on average
        cx, cy = sum(p[0] for p in gx) / len(gx), sum(p[1] for p in gx) / len(gx)
        best = None
        for rot in (0, 90, 180, 270):
            rr = _rot2(rot)
            e2 = [rr(x, y) for x, y, _, _ in ee]
            ex, ey = sum(p[0] for p in e2) / len(e2), sum(p[1] for p in e2) / len(e2)
            g = _grid([(x - ex + cx, y - ey + cy) for x, y in e2], 0.5)
            err = sum(_nearest(g, 0.5, x, y, 4) for x, y in gx) / len(gx)
            if best is None or err < best[0]:
                best = (err, rot, cx - ex, cy - ey)
        err, rot, tx, ty = best
        if err > 0.5:
            return None, f'pads do not match ({nhit} of {len(ee)} EasyEDA / {len(our_pads)} ours, layout {err:.2f} mm)'
        how = f'pad centroid, layout {err:.2f} mm'
    rr = _rot2(rot)

    def to_ours(p):
        x, y, z = to_ee(p)
        x, y = rr(x, y)
        return (x + tx, y + ty, z)

    mesh = Mesh()
    mesh.add(raw, to_ours)
    return mesh, f'{fp["title"]}: outline fit {oscore:.2f} mm, sense {sense:+d}, rot {rot}, {how}'
