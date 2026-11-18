"""Small net-oriented description layer on top of sch.py.

A design is a set of sheets; each sheet has groups (functional blocks) of parts. Parts are created with
helpers (R, C, L, ic, ...) that take net names per pin. References are numbered per sheet:
sheet n -> R{n}01, R{n}02, ... (KiCad "sheet number x 100" style), so adding a part on one sheet never
renumbers another sheet.

Every part carries sourcing fields used later for BOM/CPL:
  LCSC (JLCPCB part number or ''), MPN, Manufacturer, Sourcing ('JLC', 'JLC-GS' = Global Sourcing,
  'HAND' = hand-solder / customer-supplied, 'DNP'), Status ('' or 'UNVERIFIED: why').
"""
import json
import os
import re

import sch
import symlib

HERE = os.path.dirname(os.path.abspath(__file__))
PASSIVES_JSON = os.path.join(HERE, 'data', 'passives.json')

FP = {
    'R0201': 'Resistor_SMD:R_0201_0603Metric', 'R0402': 'Resistor_SMD:R_0402_1005Metric',
    'R0603': 'Resistor_SMD:R_0603_1608Metric', 'R0805': 'Resistor_SMD:R_0805_2012Metric',
    'R1206': 'Resistor_SMD:R_1206_3216Metric', 'R2512': 'Resistor_SMD:R_2512_6332Metric',
    'C0201': 'Capacitor_SMD:C_0201_0603Metric', 'C0402': 'Capacitor_SMD:C_0402_1005Metric',
    'C0603': 'Capacitor_SMD:C_0603_1608Metric', 'C0805': 'Capacitor_SMD:C_0805_2012Metric',
    'C1206': 'Capacitor_SMD:C_1206_3216Metric',
    'FB0402': 'Inductor_SMD:L_0402_1005Metric', 'FB0603': 'Inductor_SMD:L_0603_1608Metric',
    'LED0603': 'LED_SMD:LED_0603_1608Metric', 'LED0402': 'LED_SMD:LED_0402_1005Metric',
}


_HV = {'VBUS_C', 'CHG_IN', 'CHG_IN_S', 'CHG_VBUS_F', 'CHG_ACP', 'CHG_ACN', 'USBC_CC1', 'USBC_CC2'}
_5V = {'VCC5V0', 'USBA1_VBUS', 'USBA2_VBUS', 'CAMA_5V', 'VCC5V_KBD', 'VBUS_KBD', 'VUSB'}


def _rail_v(net):
    """Minimum capacitor voltage rating for a net (max operating voltage with margin)."""
    if net in _HV:
        return 25
    if net in ('BL_LEDA',):
        return 50
    if net in ('CHG_REGN', 'CHG_VDDA'):
        return 16
    if net in _5V:
        return 10
    return 6.3


def _load_passives():
    if os.path.exists(PASSIVES_JSON):
        return json.load(open(PASSIVES_JSON))
    return {}


class Design:
    def __init__(self, name, title):
        self.proj = sch.Project(name, title)
        self.sheets = []
        self.passives = _load_passives()
        self.missing_passives = set()
        self.symbols = {}          # lib_id -> Symbol (custom ones, written to project library)
        self.notes = []

    def sheet(self, title, filename, paper='A1'):
        n = len(self.sheets) + 1
        sb = SheetBuilder(self, n, title, filename, paper)
        self.sheets.append(sb)
        self.proj.add_sheet(sb.sheet)
        return sb

    def all_parts(self):
        for sb in self.sheets:
            for p in sb.sheet.parts:
                yield sb, p


class SheetBuilder:
    def __init__(self, design, n, title, filename, paper):
        self.d, self.n = design, n
        self.sheet = sch.Sheet(title, filename, paper)
        self.counters = {}

    def ref(self, prefix):
        c = self.counters.get(prefix, 0) + 1
        self.counters[prefix] = c
        if c > 99:
            raise ValueError(f'sheet {self.n} ran out of {prefix} references')
        return f'{prefix}{self.n}{c:02d}'

    def group(self, title, note=''):
        return Group(self, title, note)


def _sym(lib_id):
    return symlib.load(lib_id)


class Group:
    def __init__(self, sb, title, note):
        self.sb, self.title, self.note = sb, title, note
        self.parts = []
        sb.sheet.group(title if not note else f'{title}\n{note}', self.parts)

    # ------------------------------------------------------------------ generic
    def part(self, prefix, sym, value, nets, footprint='', fields=None, unit=1, dnp=False, ref=None, rot=None,
             auto_hidden=True):
        """nets: {pin_number: net or None}. Hidden no-connect pins and hidden pins duplicating a visible
        pin name are filled automatically (auto_hidden)."""
        nets = dict(nets)
        if auto_hidden:
            vis = {}
            for p in sym.pins_of_unit(unit):
                if not p.hidden and p.number in nets:
                    vis.setdefault(p.name, nets[p.number])
            for p in sym.pins_of_unit(unit):
                if p.number in nets:
                    continue
                if p.hidden and p.etype == 'no_connect':
                    nets[p.number] = None
                elif p.hidden and p.name in vis:
                    nets[p.number] = vis[p.name]
        f = {'LCSC': '', 'MPN': '', 'Manufacturer': '', 'Sourcing': 'JLC', 'Status': ''}
        f.update(fields or {})
        if dnp:
            f['Sourcing'] = 'DNP'
        r = ref or self.sb.ref(prefix)
        # a symbol that is no part to buy (hole, test pad, solder jumper: Sourcing PCB) is kept out of the BOM, as its
        # footprint is
        p = sch.Part(r, sym, value, nets, footprint=footprint, fields=f, unit=unit, dnp=dnp, rot=rot,
                     in_bom=f.get('Sourcing') != 'PCB')
        self.parts.append(p)
        return p

    def _passive_fields(self, kind, value, size, extra):
        key = f'{kind}_{size}_{value}'
        if extra.get('lcsc'):
            return {'LCSC': extra['lcsc'], 'MPN': extra.get('mpn', ''), 'Manufacturer': extra.get('mfr', '')}
        info = self.sb.d.passives.get(key)
        if not info:
            self.sb.d.missing_passives.add(key)
            return {'LCSC': '', 'MPN': '', 'Manufacturer': ''}
        return {'LCSC': info['lcsc'], 'MPN': info['mpn'], 'Manufacturer': info['mfr']}

    # ------------------------------------------------------------------ passives
    def R(self, value, a, b, size='0402', dnp=False, note='', **kw):
        f = self._passive_fields('R', value, size, kw)
        if note:
            f['Note'] = note
        return self.part('R', _sym('Device:R'), value, {'1': a, '2': b}, FP['R' + size], f, dnp=dnp)

    def C(self, value, a, b='GND', size='0402', v='', dnp=False, note='', **kw):
        if value == 'DNP':
            val = 'DNP'
            f = {'LCSC': '', 'MPN': '', 'Manufacturer': ''}
        else:
            need = max(_rail_v(a), _rail_v(b), float(v.rstrip('V')) if v else 0)
            vr = next(r for r in (6.3, 10, 16, 25, 50, 100) if r >= need)
            vs = ('%g' % vr) + 'V'
            val = f'{value} {vs}'
            f = self._passive_fields('C', f'{value}_{vs}', size, kw)
        if note:
            f['Note'] = note
        fp = kw.get('fp') or FP['C' + size]
        return self.part('C', _sym('Device:C'), val, {'1': a, '2': b}, fp, f, dnp=dnp)

    def Cpol(self, value, a, b='GND', fp='', **kw):
        f = {'LCSC': kw.get('lcsc', ''), 'MPN': kw.get('mpn', ''), 'Manufacturer': kw.get('mfr', '')}
        return self.part('C', _sym('Device:C_Polarized'), value, {'1': a, '2': b}, fp, f)

    def L(self, value, a, b, fp, lcsc='', mpn='', mfr='', status=''):
        return self.part('L', _sym('Device:L'), value, {'1': a, '2': b}, fp,
                         {'LCSC': lcsc, 'MPN': mpn, 'Manufacturer': mfr, 'Status': status})

    def FB(self, value, a, b, size='0402', **kw):
        f = self._passive_fields('FB', value, size, kw)
        return self.part('FB', _sym('Device:FerriteBead_Small'), value, {'1': a, '2': b}, FP['FB' + size], f)

    def D(self, sym, value, k, a, fp, lcsc='', mpn='', mfr=''):
        return self.part('D', _sym(sym), value, {'1': k, '2': a}, fp, {'LCSC': lcsc, 'MPN': mpn, 'Manufacturer': mfr})

    def LED(self, value, k, a, size='0603', **kw):
        f = self._passive_fields('LED', value, size, kw)
        return self.part('D', _sym('Device:LED'), value, {'1': k, '2': a}, FP['LED' + size], f)

    def TP(self, net, fp='TestPoint:TestPoint_Pad_D1.0mm', label=''):
        return self.part('TP', _sym('Connector:TestPoint'), label or net, {'1': net}, fp,
                         {'Sourcing': 'PCB', 'Note': 'test pad (no part)'})

    # ------------------------------------------------------------------ ICs / anything else
    def ic(self, sym, value, nets, fp, lcsc='', mpn='', mfr='', prefix='U', sourcing='JLC', status='', note='',
           unit=1, datasheet=''):
        s = sym if isinstance(sym, symlib.Symbol) else _sym(sym)
        f = {'LCSC': lcsc, 'MPN': mpn or value, 'Manufacturer': mfr, 'Sourcing': sourcing, 'Status': status}
        if note:
            f['Note'] = note
        if datasheet:
            f['Datasheet'] = datasheet
        return self.part(prefix, s, value, nets, fp, f, unit=unit)


# ---------------------------------------------------------------------- custom symbol helper
def box(design, name, pins, ref='U', description='', footprint='', datasheet='', sides=None):
    """pins: list of (number, name, etype, side) with side in L/R/T/B, or None entries per side via `sides`.
    Builds `cm5h:<name>` and registers it in the design's project library."""
    if sides is None:
        sides = {'left': [], 'right': [], 'top': [], 'bottom': []}
        for num, nm, et, side in pins:
            key = {'L': 'left', 'R': 'right', 'T': 'top', 'B': 'bottom'}[side]
            sides[key].append((num, nm, et) if num else None)
    s = symlib.make_box_symbol(f'cm5h:{name}', [sides], ref=ref, value=name, description=description,
                               footprint=footprint, datasheet=datasheet)
    design.symbols[s.lib_id] = s
    return s
