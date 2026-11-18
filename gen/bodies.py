"""Body heights of KiCad library footprints that ship without a 3D model (or whose model is not installed), from the
part datasheets, and box models for them so the 3D renders show the part.

Used by tools/heights.py (height check) and gen/pcbgen.py (renders). The box footprint is the F.Fab body outline of
the library footprint; the height is the datasheet maximum.
"""
import os

from fpgen import vrml_box
from sexpr import parse

BODY = {
    'SW_Push_1P1T-MP_NO_Horizontal_Alps_SKRTLAE010': (3.3, 'Alps SKRTLAE010 drawing (C110293)'),
    'USB_C_Receptacle_HRO_TYPE-C-31-M-12': (3.26, 'HRO TYPE-C-31-M-12 drawing (C165948)'),
    'L_Bourns_SRP7028A_7.3x6.6mm': (3.0, 'Bourns SRP7028A, 2.8 +-0.2 (C1329579 datasheet)'),
    'microSD_HC_Hirose_DM3AT-SF-PEJM5': (1.68, 'Hirose DM3AT drawing (C114218 datasheet p.3)'),
    'Knowles_LGA-5_3.5x2.65mm': (1.08, 'Knowles SPH0641LU4H-1, 0.98 +-0.10 (C2879853 datasheet)'),
    'Texas_RSN_WQFN-32-1EP_4x4mm_P0.4mm_EP2.8x2.8mm': (0.8, 'WQFN package class (<= 0.8 mm)'),
    'Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4': (0.8, 'WQFN package class (<= 0.8 mm)'),
    'Texas_VQFN-RNR0011A-11': (1.0, 'VQFN package class (<= 1.0 mm)'),
    'TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm': (0.8, 'TQFN package class (<= 0.8 mm)'),
}
COLOR = {'L_Bourns_SRP7028A_7.3x6.6mm': (0.25, 0.25, 0.28), 'USB_C_Receptacle_HRO_TYPE-C-31-M-12': (0.75, 0.75, 0.78),
         'SW_Push_1P1T-MP_NO_Horizontal_Alps_SKRTLAE010': (0.7, 0.7, 0.72)}


def _points(node):
    for x in node[1:]:
        if isinstance(x, list) and x and x[0] in ('start', 'end', 'mid', 'center', 'xy'):
            yield float(x[1]), float(x[2])
        elif isinstance(x, list):
            yield from _points(x)


def fab_bbox(mod_path):
    """bounding box of the F.Fab drawing of a .kicad_mod file"""
    root = parse(open(mod_path).read())[0]
    pts = []
    for g in root[1:]:
        if isinstance(g, list) and g and str(g[0]).startswith('fp_'):
            layer = [str(x[1]) for x in g if isinstance(x, list) and x and x[0] == 'layer']
            if layer == ['F.Fab']:
                pts += list(_points(g))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def box_model(name, mod_path, out_dir):
    """write <out_dir>/body_<name>.wrl (if needed) and return its path"""
    path = os.path.join(out_dir, 'body_' + name + '.wrl')
    if not os.path.exists(path) or os.path.getmtime(path) < os.path.getmtime(__file__):
        x0, y0, x1, y1 = fab_bbox(mod_path)
        h = BODY[name][0]
        vrml_box(path, [(x0, -y1, 0.0, x1, -y0, h)], COLOR.get(name, (0.12, 0.12, 0.12)))
    return path
