"""KiCad symbol handling: load library symbols (flattening `extends`), compute pins,
and build custom box symbols from datasheet pin tables."""
import copy
import os
import re
from sexpr import parse, find, find_all, Q

KICAD_SYM_DIR = '/usr/share/kicad/symbols'
_lib_cache = {}


def _load_lib(path):
    if path not in _lib_cache:
        root = parse(open(path, encoding='utf-8').read())[0]
        syms = {}
        for node in find_all(root, 'symbol'):
            syms[str(node[1])] = node
        _lib_cache[path] = syms
    return _lib_cache[path]


class Pin:
    __slots__ = ('number', 'name', 'etype', 'x', 'y', 'angle', 'length', 'unit', 'hidden')

    def __init__(self, number, name, etype, x, y, angle, length, unit, hidden):
        self.number, self.name, self.etype = number, name, etype
        self.x, self.y, self.angle, self.length = x, y, angle, length
        self.unit, self.hidden = unit, hidden

    def __repr__(self):
        return f'Pin({self.number},{self.name},{self.etype},u{self.unit},({self.x},{self.y})@{self.angle})'


class Symbol:
    """A flattened symbol ready to embed in a schematic as lib_id `lib:name`."""

    def __init__(self, lib_id, node):
        self.lib_id = lib_id
        self.node = node  # (symbol "lib:name" ...)
        self.pins = []
        self.units = set()
        for sub in find_all(node, 'symbol'):
            m = re.match(r'.*_(\d+)_(\d+)$', str(sub[1]))
            unit, style = int(m.group(1)), int(m.group(2))
            if style not in (0, 1):
                continue
            if unit:
                self.units.add(unit)
            for p in find_all(sub, 'pin'):
                at = find(p, 'at')
                ln = find(p, 'length')
                name = str(find(p, 'name')[1])
                num = str(find(p, 'number')[1])
                hidden = any(isinstance(x, list) and x[0] == 'hide' and x[1] == 'yes' for x in p) or 'hide' in p
                self.pins.append(Pin(num, name, str(p[1]), float(at[1]), float(at[2]),
                                     float(at[3]) if len(at) > 3 else 0.0, float(ln[1]), unit, hidden))
        if not self.units:
            self.units = {1}
        self.is_power = find(node, 'power') is not None

    def pins_of_unit(self, unit):
        return [p for p in self.pins if p.unit in (0, unit)]

    def bbox(self, unit=1):
        """Rough body bbox (library coords) from graphics + pin ends."""
        xs, ys = [], []
        for sub in find_all(self.node, 'symbol'):
            m = re.match(r'.*_(\d+)_(\d+)$', str(sub[1]))
            u, st = int(m.group(1)), int(m.group(2))
            if u not in (0, unit) or st not in (0, 1):
                continue
            for g in sub:
                if not isinstance(g, list):
                    continue
                if g[0] == 'rectangle':
                    s, e = find(g, 'start'), find(g, 'end')
                    xs += [float(s[1]), float(e[1])]
                    ys += [float(s[2]), float(e[2])]
                elif g[0] in ('polyline', 'bezier'):
                    for xy in find_all(find(g, 'pts'), 'xy'):
                        xs.append(float(xy[1])); ys.append(float(xy[2]))
                elif g[0] == 'circle':
                    c, r = find(g, 'center'), float(find(g, 'radius')[1])
                    xs += [float(c[1]) - r, float(c[1]) + r]
                    ys += [float(c[2]) - r, float(c[2]) + r]
                elif g[0] == 'arc':
                    for k in ('start', 'mid', 'end'):
                        q = find(g, k)
                        if q:
                            xs.append(float(q[1])); ys.append(float(q[2]))
        for p in self.pins_of_unit(unit):
            xs.append(p.x); ys.append(p.y)
        if not xs:
            return (-2.54, -2.54, 2.54, 2.54)
        return (min(xs), min(ys), max(xs), max(ys))


def load(lib_id):
    """Load `Lib:Name` from the KiCad standard library, flattening `extends`."""
    lib, name = lib_id.split(':', 1)
    syms = _load_lib(os.path.join(KICAD_SYM_DIR, lib + '.kicad_sym'))
    node = copy.deepcopy(syms[name])
    ext = find(node, 'extends')
    if ext is not None:
        parent = load(lib + ':' + str(ext[1])).node
        pname = str(parent[1]).split(':', 1)[1]
        node = [x for x in node if not (isinstance(x, list) and x[0] == 'extends')]
        # take parent's flags/units, child's properties
        child_props = {str(p[1]): p for p in find_all(node, 'property')}
        merged = ['symbol', Q(name)]
        for x in parent[2:]:
            if isinstance(x, list) and x[0] == 'property':
                merged.append(child_props.pop(str(x[1]), x))
            elif isinstance(x, list) and x[0] == 'symbol':
                sub = copy.deepcopy(x)
                sub[1] = Q(str(sub[1]).replace(pname, name, 1))
                merged.append(sub)
            else:
                merged.append(copy.deepcopy(x))
        for p in child_props.values():
            merged.insert(2, p)
        node = merged
    node[1] = Q(lib_id)
    return Symbol(lib_id, node)


# ----------------------------------------------------------------------------- custom symbols
def _prop(key, val, x, y, hide=False):
    p = ['property', Q(key), Q(val), ['at', x, y, 0], ['show_name', 'no'], ['do_not_autoplace', 'no']]
    if hide:
        p.append(['hide', 'yes'])
    p.append(['effects', ['font', ['size', 1.27, 1.27]]])
    return p


def _pin(etype, x, y, ang, length, name, num, hidden=False):
    p = ['pin', etype, 'line', ['at', x, y, ang], ['length', length]]
    if hidden:
        p.append(['hide', 'yes'])
    p += [['name', Q(name), ['effects', ['font', ['size', 1.27, 1.27]]]],
          ['number', Q(num), ['effects', ['font', ['size', 1.27, 1.27]]]]]
    return p


def make_box_symbol(lib_id, units, ref='U', value='', description='', footprint='', datasheet='',
                    pin_len=2.54, pitch=2.54, min_width=10.16, extra_props=None, hide_pin_numbers=False):
    """Build a box symbol.

    units: list of dicts {'left': [...], 'right': [...], 'top': [...], 'bottom': [...]}; each entry is
    (number, name, etype) or None for a spacer.
    etype: input output bidirectional tri_state passive free unspecified power_in power_out
    open_collector open_emitter no_connect
    """
    name = lib_id.split(':', 1)[1]
    node = ['symbol', Q(lib_id)]
    if hide_pin_numbers:
        node.append(['pin_numbers', ['hide', 'yes']])
    node += [['pin_names', ['offset', 0.762]], ['exclude_from_sim', 'no'], ['in_bom', 'yes'], ['on_board', 'yes'],
             ['in_pos_files', 'yes'], ['duplicate_pin_numbers_are_jumpers', 'no']]
    props_at = []
    for ui, sides in enumerate(units, start=1):
        L, R = sides.get('left', []), sides.get('right', [])
        T, B = sides.get('top', []), sides.get('bottom', [])
        rows = max(len(L), len(R), 1)
        cols = max(len(T), len(B), 0)

        def maxlen(lst):
            return max([len(e[1]) for e in lst if e] + [0])
        char_w = 1.0  # mm per char at 1.27 mm font (approx)
        width = max(min_width, (maxlen(L) + maxlen(R)) * char_w + 5.08, (cols + 1) * pitch)
        width = round(width / pitch + 0.4999) * pitch
        height = (rows + 1) * pitch
        if T or B:
            height += 2 * pitch + max(maxlen(T), maxlen(B)) * char_w
        height = round(height / pitch + 0.4999) * pitch
        x0, x1 = -width / 2, width / 2
        y1, y0 = height / 2, -height / 2
        # snap edges to grid
        x0 = -round(width / 2 / pitch) * pitch
        x1 = x0 + width
        y1 = round(height / 2 / pitch) * pitch
        y0 = y1 - height
        g = ['symbol', Q(f'{name}_{ui}_1'),
             ['rectangle', ['start', x0, y1], ['end', x1, y0],
              ['stroke', ['width', 0.254], ['type', 'default']], ['fill', ['type', 'background']]]]
        ytop = y1 - pitch
        if T or B:
            ytop -= pitch + 0  # leave room below top pins
        for i, e in enumerate(L):
            if e:
                g.append(_pin(e[2], x0 - pin_len, ytop - i * pitch, 0, pin_len, e[1], e[0]))
        for i, e in enumerate(R):
            if e:
                g.append(_pin(e[2], x1 + pin_len, ytop - i * pitch, 180, pin_len, e[1], e[0]))
        for i, e in enumerate(T):
            if e:
                g.append(_pin(e[2], x0 + (i + 1) * pitch, y1 + pin_len, 270, pin_len, e[1], e[0]))
        for i, e in enumerate(B):
            if e:
                g.append(_pin(e[2], x0 + (i + 1) * pitch, y0 - pin_len, 90, pin_len, e[1], e[0]))
        node.append(g)
        props_at.append((x0, y1, y0))
    x0, y1, y0 = props_at[0]
    node[2:2] = []
    props = [_prop('Reference', ref, x0, y1 + 1.27), _prop('Value', value or name, x0, y0 - 1.27),
             _prop('Footprint', footprint, 0, 0, True), _prop('Datasheet', datasheet, 0, 0, True),
             _prop('Description', description, 0, 0, True)]
    for k, v in (extra_props or {}).items():
        props.append(_prop(k, v, 0, 0, True))
    # properties go after the flag nodes, before unit sub-symbols
    insert_at = next(i for i, x in enumerate(node) if isinstance(x, list) and x[0] == 'symbol')
    node[insert_at:insert_at] = props
    node.append(['embedded_fonts', 'no'])
    return Symbol(lib_id, node)


def make_power_symbol(lib_id, net_name):
    """Global power symbol whose net name is `net_name` (hidden power_in pin, like KiCad's power lib)."""
    name = lib_id.split(':', 1)[1]
    node = ['symbol', Q(lib_id), ['power', 'global'], ['pin_numbers', ['hide', 'yes']],
            ['pin_names', ['offset', 0], ['hide', 'yes']], ['exclude_from_sim', 'no'], ['in_bom', 'no'],
            ['on_board', 'yes'], ['in_pos_files', 'yes'], ['duplicate_pin_numbers_are_jumpers', 'no'],
            _prop('Reference', '#PWR', 0, -3.81, True), _prop('Value', net_name, 0, 3.556),
            _prop('Footprint', '', 0, 0, True), _prop('Datasheet', '', 0, 0, True),
            _prop('Description', f'Power symbol for net {net_name}', 0, 0, True),
            ['symbol', Q(f'{name}_0_1'),
             ['polyline', ['pts', ['xy', -0.762, 1.27], ['xy', 0, 2.54]], ['stroke', ['width', 0], ['type', 'default']], ['fill', ['type', 'none']]],
             ['polyline', ['pts', ['xy', 0, 0], ['xy', 0, 2.54]], ['stroke', ['width', 0], ['type', 'default']], ['fill', ['type', 'none']]],
             ['polyline', ['pts', ['xy', 0, 2.54], ['xy', 0.762, 1.27]], ['stroke', ['width', 0], ['type', 'default']], ['fill', ['type', 'none']]]],
            ['symbol', Q(f'{name}_1_1'), _pin('power_in', 0, 0, 90, 0, net_name, '1', hidden=True)],
            ['embedded_fonts', 'no']]
    return Symbol(lib_id, node)
