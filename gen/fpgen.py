"""Footprint writer for project footprints (KiCad 10 .kicad_mod) + simple VRML box models for 3D/height checks.

Every footprint carries its source (datasheet / drawing) in the description. Coordinates are in mm, KiCad
convention (y down), origin as stated per footprint. Pads are rect/roundrect SMD, plated or NPTH holes.
"""
import os
from sexpr import Q, dump

FONT = ['effects', ['font', ['size', 1, 1], ['thickness', 0.15]]]
FONT_S = ['effects', ['font', ['size', 0.6, 0.6], ['thickness', 0.1]]]


class Footprint:
    def __init__(self, name, descr, tags='', attr='smd'):
        self.name, self.descr, self.tags, self.attr = name, descr, tags, attr
        self.pads, self.graphics, self.models, self.zones = [], [], [], []
        self.courtyard_extra = []   # extra (x0, y0, x1, y1) boxes the courtyard must enclose
        self.courtyard_holes = []   # (x0, y0, x1, y1) openings inside the courtyard outline (drawn as inner outlines)
        self.body = None        # (x0, y0, x1, y1) fab outline
        self.height = None      # mm above board (for the height check)

    # ------------------------------------------------------------------ pads
    def smd(self, num, x, y, w, h, shape='roundrect', rratio=0.15, angle=0, layers=('F.Cu', 'F.Mask', 'F.Paste'),
            paste_ratio=None):
        p = ['pad', Q(str(num)), 'smd', shape, ['at', round(x, 4), round(y, 4)] + ([angle] if angle else []),
             ['size', round(w, 4), round(h, 4)], ['layers'] + [Q(l) for l in layers]]
        if shape == 'roundrect':
            p.append(['roundrect_rratio', rratio])
        if paste_ratio is not None:
            p.append(['solder_paste_margin_ratio', paste_ratio])
        self.pads.append(p)

    def th(self, num, x, y, drill, pad, shape='circle', plated=True, slot=None, extra_layers=(), inner=None, back=None):
        """plated or NPTH hole. slot=(w,h) for oval drill. inner / back: other (round) pad diameters on the inner
        layers / B.Cu than the front pad (KiCad front-inner-back padstack)."""
        if plated:
            d = ['drill', 'oval', slot[0], slot[1]] if slot else ['drill', drill]
            sz = [pad, pad] if not isinstance(pad, (list, tuple)) else list(pad)
            p = ['pad', Q(str(num)), 'thru_hole', shape, ['at', round(x, 4), round(y, 4)],
                 ['size'] + sz, d, ['layers', Q('*.Cu'), Q('*.Mask')] + [Q(l) for l in extra_layers]]
            if inner is not None or back is not None:
                p.append(['padstack', ['mode', 'front_inner_back']] +
                         [['layer', Q(lay), ['shape', 'circle'], ['size', dia, dia]]
                          for lay, dia in (('Inner', inner if inner is not None else pad),
                                           ('B.Cu', back if back is not None else pad))])
            self.pads.append(p)
        else:
            d = ['drill', 'oval', slot[0], slot[1]] if slot else ['drill', drill]
            sz = list(slot) if slot else [drill, drill]
            self.pads.append(['pad', Q(''), 'np_thru_hole', 'oval' if slot else 'circle', ['at', round(x, 4), round(y, 4)],
                              ['size'] + sz, d, ['layers', Q('*.Cu'), Q('*.Mask')]])

    # ------------------------------------------------------------------ graphics
    def line(self, x0, y0, x1, y1, layer, w):
        self.graphics.append(['fp_line', ['start', round(x0, 4), round(y0, 4)], ['end', round(x1, 4), round(y1, 4)],
                              ['stroke', ['width', w], ['type', 'solid']], ['layer', Q(layer)]])

    def rect(self, x0, y0, x1, y1, layer, w):
        self.graphics.append(['fp_rect', ['start', round(x0, 4), round(y0, 4)], ['end', round(x1, 4), round(y1, 4)],
                              ['stroke', ['width', w], ['type', 'solid']], ['fill', 'no'], ['layer', Q(layer)]])

    def circle(self, x, y, r, layer, w, fill=False):
        self.graphics.append(['fp_circle', ['center', round(x, 4), round(y, 4)], ['end', round(x + r, 4), round(y, 4)],
                              ['stroke', ['width', w], ['type', 'solid']], ['fill', 'yes' if fill else 'no'],
                              ['layer', Q(layer)]])

    def text(self, s, x, y, layer='F.Fab'):
        self.graphics.append(['fp_text', 'user', Q(s), ['at', x, y], ['layer', Q(layer)], FONT_S])

    def keepout(self, pts, layers=('F.Cu',), name='keep-out'):
        """copper keep-out rule area (no tracks, vias or pours; pads allowed), polygon in footprint coordinates"""
        self.zones.append(['zone', ['net', 0], ['net_name', Q('')], ['layers'] + [Q(l) for l in layers],
                           ['name', Q(name)], ['hatch', 'edge', 0.5], ['connect_pads', ['clearance', 0]],
                           ['min_thickness', 0.25], ['filled_areas_thickness', 'no'],
                           ['keepout', ['tracks', 'not_allowed'], ['vias', 'not_allowed'], ['pads', 'allowed'],
                            ['copperpour', 'not_allowed'], ['footprints', 'allowed']],
                           ['fill', ['thermal_gap', 0.5], ['thermal_bridge_width', 0.5]],
                           ['polygon', ['pts'] + [['xy', round(x, 4), round(y, 4)] for x, y in pts]]])

    def set_body(self, x0, y0, x1, y1, height):
        self.body = (x0, y0, x1, y1)
        self.height = height

    def model(self, path, offset=(0, 0, 0), rotate=(0, 0, 0), scale=(1, 1, 1)):
        self.models.append(['model', Q(path), ['offset', ['xyz'] + list(offset)], ['scale', ['xyz'] + list(scale)],
                            ['rotate', ['xyz'] + list(rotate)]])

    # ------------------------------------------------------------------ output
    def _pad_boxes(self):
        out = []
        for p in self.pads:
            at = next(x for x in p if isinstance(x, list) and x[0] == 'at')
            sz = next(x for x in p if isinstance(x, list) and x[0] == 'size')
            ang = at[3] if len(at) > 3 else 0
            w, h = (sz[2], sz[1]) if ang in (90, 270, -90) else (sz[1], sz[2])
            out.append((at[1] - w / 2, at[2] - h / 2, at[1] + w / 2, at[2] + h / 2))
        return out

    def _pad_extent(self):
        bx = self._pad_boxes()
        return min(b[0] for b in bx), min(b[1] for b in bx), max(b[2] for b in bx), max(b[3] for b in bx)

    def _silk_segments(self, x0, y0, x1, y1, clear=0.2, minlen=0.2):
        """the four edges of a rectangle, with the parts closer than `clear` to any pad removed"""
        boxes = [(a - clear, b - clear, c + clear, d + clear) for a, b, c, d in self._pad_boxes()]
        segs = []
        for (ax, ay, bx_, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
            horiz = ay == by
            lo, hi = (min(ax, bx_), max(ax, bx_)) if horiz else (min(ay, by), max(ay, by))
            fixed = ay if horiz else ax
            cuts = []
            for (p0, q0, p1, q1) in boxes:
                if horiz and q0 <= fixed <= q1:
                    cuts.append((p0, p1))
                elif not horiz and p0 <= fixed <= p1:
                    cuts.append((q0, q1))
            parts = [(lo, hi)]
            for c0, c1 in cuts:
                nxt = []
                for s0, s1 in parts:
                    if c1 <= s0 or c0 >= s1:
                        nxt.append((s0, s1))
                        continue
                    if c0 > s0:
                        nxt.append((s0, c0))
                    if c1 < s1:
                        nxt.append((c1, s1))
                parts = nxt
            for s0, s1 in parts:
                if s1 - s0 >= minlen:
                    segs.append((s0, fixed, s1, fixed) if horiz else (fixed, s0, fixed, s1))
        return segs

    def build(self, pin1=None, courtyard_margin=0.25, silk=True, courtyard=True):
        node = ['footprint', Q(self.name), ['version', 20260206], ['generator', Q('cm5h_fpgen')], ['layer', Q('F.Cu')],
                ['descr', Q(self.descr)], ['tags', Q(self.tags)]]
        ex = self._pad_extent() if self.pads else (0, 0, 0, 0)
        b = self.body or ex
        boxes = [ex, b] + list(self.courtyard_extra)
        x0, y0 = min(q[0] for q in boxes), min(q[1] for q in boxes)
        x1, y1 = max(q[2] for q in boxes), max(q[3] for q in boxes)
        node.append(['property', Q('Reference'), Q('REF**'), ['at', 0, round(y0 - 1.0, 3), 0], ['layer', Q('F.SilkS')], FONT])
        node.append(['property', Q('Value'), Q(self.name), ['at', 0, round(y1 + 1.0, 3), 0], ['layer', Q('F.Fab')], FONT])
        node.append(['attr'] + ([self.attr] if self.attr else []))
        node.append(['duplicate_pad_numbers_are_jumpers', 'no'])
        g = list(self.graphics)
        if self.body:
            g.append(['fp_rect', ['start', b[0], b[1]], ['end', b[2], b[3]], ['stroke', ['width', 0.1], ['type', 'solid']],
                      ['fill', 'no'], ['layer', Q('F.Fab')]])
            if silk:
                m = 0.11
                for (sx0, sy0, sx1, sy1) in self._silk_segments(b[0] - m, b[1] - m, b[2] + m, b[3] + m):
                    g.append(['fp_line', ['start', round(sx0, 3), round(sy0, 3)], ['end', round(sx1, 3), round(sy1, 3)],
                              ['stroke', ['width', 0.12], ['type', 'solid']], ['layer', Q('F.SilkS')]])
        c = courtyard_margin
        if courtyard:
            base = (min(ex[0], b[0]) - c, min(ex[1], b[1]) - c, max(ex[2], b[2]) + c, max(ex[3], b[3]) + c)
            outline = None
            if len(self.courtyard_extra) == 1:
                e = self.courtyard_extra[0]
                e = (e[0] - c, e[1] - c, e[2] + c, e[3] + c)
                # extra box wider than the base and hanging off its bottom edge (M.2 socket + module): T outline
                if e[0] < base[0] and e[2] > base[2] and base[1] < e[1] < base[3] < e[3]:
                    outline = [(base[0], base[1]), (base[2], base[1]), (base[2], e[1]), (e[2], e[1]),
                               (e[2], e[3]), (e[0], e[3]), (e[0], e[1]), (base[0], e[1])]
            if outline:
                g.append(['fp_poly', ['pts'] + [['xy', round(px, 3), round(py, 3)] for px, py in outline],
                          ['stroke', ['width', 0.05], ['type', 'solid']], ['fill', 'no'], ['layer', Q('F.CrtYd')]])
            else:
                g.append(['fp_rect', ['start', round(x0 - c, 3), round(y0 - c, 3)],
                          ['end', round(x1 + c, 3), round(y1 + c, 3)],
                          ['stroke', ['width', 0.05], ['type', 'solid']], ['fill', 'no'], ['layer', Q('F.CrtYd')]])
            for (hx0, hy0, hx1, hy1) in self.courtyard_holes:
                g.append(['fp_rect', ['start', hx0, hy0], ['end', hx1, hy1], ['stroke', ['width', 0.05], ['type', 'solid']],
                          ['fill', 'no'], ['layer', Q('F.CrtYd')]])
        if pin1 is not None:
            g.append(['fp_circle', ['center', pin1[0], pin1[1]], ['end', pin1[0] + 0.1, pin1[1]],
                      ['stroke', ['width', 0.2], ['type', 'solid']], ['fill', 'yes'], ['layer', Q('F.SilkS')]])
        node += g
        node += self.pads
        node += self.zones
        node.append(['embedded_fonts', 'no'])
        node += self.models
        return node

    def write(self, libdir, **kw):
        os.makedirs(libdir, exist_ok=True)
        open(os.path.join(libdir, self.name + '.kicad_mod'), 'w').write(dump(self.build(**kw)) + '\n')


def vrml_box(path, boxes, color=(0.2, 0.2, 0.2)):
    """Write a VRML 2.0 file with axis-aligned boxes [(x0,y0,z0,x1,y1,z1), ...] in mm (KiCad VRML unit = 0.1 inch,
    so coordinates are divided by 2.54). y is model space (up = -y in the PCB)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = ['#VRML V2.0 utf8']
    for (x0, y0, z0, x1, y1, z1) in boxes:
        cx, cy, cz = (x0 + x1) / 2 / 2.54, (y0 + y1) / 2 / 2.54, (z0 + z1) / 2 / 2.54
        sx, sy, sz = abs(x1 - x0) / 2.54, abs(y1 - y0) / 2.54, abs(z1 - z0) / 2.54
        out.append('Transform { translation %.5f %.5f %.5f children [ Shape { appearance Appearance { material Material '
                   '{ diffuseColor %.2f %.2f %.2f } } geometry Box { size %.5f %.5f %.5f } } ] }'
                   % (cx, cy, cz, color[0], color[1], color[2], sx, sy, sz))
    open(path, 'w').write('\n'.join(out) + '\n')
