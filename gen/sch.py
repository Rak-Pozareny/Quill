"""Schematic generation for KiCad 10 (format 20260306).

Design is described as Parts with pin->net maps. Each pin gets a short wire stub ending in a
label (local or global), a GND power symbol, or a no-connect flag. Parts are packed on the page.
"""
import math
import uuid as _uuid
from sexpr import Q, dump
import symlib

SCH_VERSION = 20260306
GRID = 1.27
STUB = 2.54
FONT = ['effects', ['font', ['size', 1.27, 1.27]]]


def uid(seed=None):
    if seed is None:
        return str(_uuid.uuid4())
    return str(_uuid.uuid5(_uuid.NAMESPACE_URL, 'cm5h:' + seed))


def snap(v):
    return round(round(v / GRID) * GRID, 4)


class Part:
    def __init__(self, ref, sym, value, nets, footprint='', fields=None, unit=1, rot=None, dnp=False,
                 in_bom=True, on_board=True):
        self.ref, self.sym, self.value = ref, sym, value
        self.nets = dict(nets)  # pin number (str) -> net name or None (no-connect)
        self.footprint, self.fields, self.unit = footprint, dict(fields or {}), unit
        self.rot, self.dnp, self.in_bom, self.on_board = rot, dnp, in_bom, on_board
        pins = {p.number for p in sym.pins_of_unit(unit)}
        missing = pins - set(self.nets)
        extra = set(self.nets) - pins
        if missing or extra:
            raise ValueError(f'{ref} ({sym.lib_id} u{unit}): pins missing from net map {sorted(missing)}; '
                             f'unknown pins {sorted(extra)}')


def _rot(x, y, deg):
    r = math.radians(deg)
    c, s = round(math.cos(r)), round(math.sin(r))
    return x * c - y * s, x * s + y * c


class Placed:
    def __init__(self, part, X, Y, rot):
        self.part, self.X, self.Y, self.rot = part, X, Y, rot

    def pin_xy(self, pin):
        x, y = _rot(pin.x, pin.y, self.rot)
        return snap(self.X + x), snap(self.Y - y)

    def pin_out(self, pin):
        """Unit vector (schematic coords) pointing away from the body at the pin end."""
        a = (pin.angle + 180 + self.rot) % 360
        dx, dy = round(math.cos(math.radians(a))), -round(math.sin(math.radians(a)))
        return dx, dy


class Sheet:
    def __init__(self, title, filename, paper='A2'):
        self.title, self.filename, self.paper = title, filename, paper
        self.groups = []     # (title, [Part]); the part lists may keep growing after group() is called
        self.extra_items = []
        self.uuid = uid('sheet:' + filename)

    @property
    def parts(self):
        return [p for _, ps in self.groups for p in ps]

    def group(self, title, parts):
        self.groups.append((title, parts))
        return parts


class Project:
    def __init__(self, name, root_title):
        self.name, self.root_title = name, root_title
        self.sheets = []
        self.root_uuid = uid('root:' + name)
        self.global_nets = set()
        self.flag_sheet = None

    def add_sheet(self, sheet):
        self.sheets.append(sheet)
        return sheet

    # ------------------------------------------------------------------ connectivity bookkeeping
    def net_usage(self):
        use = {}
        for sh in self.sheets:
            for p in sh.parts:
                for pin, net in p.nets.items():
                    if net is None:
                        continue
                    use.setdefault(net, set()).add(sh.filename)
        return use

    def expected_netlist(self):
        nets = {}
        for sh in self.sheets:
            for p in sh.parts:
                for pin, net in p.nets.items():
                    if net is not None:
                        nets.setdefault(net, set()).add((p.ref, pin))
        return nets

    # ------------------------------------------------------------------ writing
    def write(self, outdir):
        import os
        os.makedirs(outdir, exist_ok=True)
        use = self.net_usage()
        is_global = {n: (len(s) > 1 or n in self.global_nets) for n, s in use.items()}
        # power-flag analysis: nets with power_in pins and no power_out pins
        drivers, pwr_in = {}, {}
        for sh in self.sheets:
            for p in sh.parts:
                pmap = {pp.number: pp for pp in p.sym.pins_of_unit(p.unit)}
                for pin, net in p.nets.items():
                    if net is None:
                        continue
                    et = pmap[pin].etype
                    if et == 'power_out':
                        drivers[net] = drivers.get(net, 0) + 1
                    if et == 'power_in':
                        pwr_in[net] = True
        flag_nets = sorted(n for n in pwr_in if not drivers.get(n))
        if 'GND' in use and 'GND' not in flag_nets and not drivers.get('GND'):
            flag_nets.append('GND')
        per_sheet = {sh.filename: [] for sh in self.sheets}
        for n in flag_nets:
            home = next(sh for sh in self.sheets if n in {net for p in sh.parts for net in p.nets.values()})
            per_sheet[home.filename].append(n)
        for sh in self.sheets:
            self._write_sheet(sh, outdir, is_global, per_sheet[sh.filename])
        self._write_root(outdir)
        return flag_nets

    def _write_root(self, outdir):
        items = []
        x, y = 25.4, 30.48
        for i, sh in enumerate(self.sheets, start=2):
            w, h = 50.8, 12.7
            items.append(['sheet', ['at', x, y], ['size', w, h], ['exclude_from_sim', 'no'], ['in_bom', 'yes'],
                          ['on_board', 'yes'], ['dnp', 'no'], ['fields_autoplaced', 'yes'],
                          ['stroke', ['width', 0.1524], ['type', 'solid']], ['fill', ['color', 0, 0, 0, 0.0]],
                          ['uuid', Q(sh.uuid)],
                          ['property', Q('Sheetname'), Q(sh.title), ['at', x, y - 0.7116, 0], ['show_name', 'no'],
                           ['do_not_autoplace', 'no'], ['effects', ['font', ['size', 1.27, 1.27]], ['justify', 'left', 'bottom']]],
                          ['property', Q('Sheetfile'), Q(sh.filename), ['at', x, y + h + 0.5846, 0], ['show_name', 'no'],
                           ['do_not_autoplace', 'no'], ['effects', ['font', ['size', 1.27, 1.27]], ['justify', 'left', 'top']]],
                          ['instances', ['project', Q(self.name), ['path', Q('/' + self.root_uuid), ['page', Q(str(i))]]]]])
            x += 66.04
            if x > 380:
                x = 25.4
                y += 25.4
        doc = ['kicad_sch', ['version', SCH_VERSION], ['generator', Q('eeschema')], ['generator_version', Q('10.0')],
               ['uuid', Q(self.root_uuid)], ['paper', Q('A3')],
               ['title_block', ['title', Q(self.root_title)], ['date', Q('2026-10-14')], ['rev', Q('0.1')],
                ['comment', 1, Q('Generated by gen/ scripts - do not edit by hand')]],
               ['lib_symbols']] + items + [['sheet_instances', ['path', Q('/'), ['page', Q('1')]]], ['embedded_fonts', 'no']]
        open(f'{outdir}/{self.name}.kicad_sch', 'w').write(dump(doc) + '\n')

    def _write_sheet(self, sh, outdir, is_global, flag_nets):
        libsyms = {}
        items = []
        pwr_counter = [0]
        gnd = symlib.load('power:GND')
        flag = symlib.load('power:PWR_FLAG')
        page_w = {'A4': 297, 'A3': 420, 'A2': 594, 'A1': 841, 'A0': 1189}[sh.paper]
        margin = 20.32
        cur_x, cur_y, row_h = margin, margin + 10.16, 0.0
        sheet_path = f'/{self.root_uuid}/{sh.uuid}'

        def label_len(name):
            return len(name) * 1.05 + 4.0

        def add_text(x, y, text, size=2.0, bold=True):
            font = ['font', ['size', size, size]] + ([['bold', 'yes']] if bold else [])
            items.append(['text', Q(text), ['exclude_from_sim', 'no'], ['at', x, y, 0],
                          ['effects', font, ['justify', 'left', 'top']],
                          ['uuid', Q(uid())]])

        def place_gnd(x, y, out):
            dx, dy = out
            rot = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}[(dx, dy)]
            pwr_counter[0] += 1
            libsyms[gnd.lib_id] = gnd
            items.append(_symbol_instance(gnd, f'#PWR{sh.uuid[:4]}{pwr_counter[0]:04d}', 'GND', x, y, rot, 1, '',
                                          {}, self.name, sheet_path, in_bom=False, on_board=True,
                                          hide_value=dx != 0))

        def place_label(net, x, y, out):
            dx, dy = out
            ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[(dx, dy)]
            just = 'left' if ang in (0, 90) else 'right'
            if is_global.get(net, False):
                items.append(['global_label', Q(net), ['shape', 'bidirectional'], ['at', x, y, ang],
                              ['fields_autoplaced', 'yes'],
                              ['effects', ['font', ['size', 1.27, 1.27]], ['justify', just]],
                              ['uuid', Q(uid())],
                              ['property', Q('Intersheetrefs'), Q('${INTERSHEET_REFS}'), ['at', x, y, ang],
                               ['show_name', 'no'], ['do_not_autoplace', 'no'],
                               ['effects', ['font', ['size', 1.27, 1.27]], ['justify', just], ['hide', 'yes']]]])
            else:
                items.append(['label', Q(net), ['at', x, y, ang],
                              ['effects', ['font', ['size', 1.27, 1.27]], ['justify', just, 'bottom']],
                              ['uuid', Q(uid())]])

        def measure(p):
            sym = p.sym
            rot = p.rot
            if rot is None:
                rot = 90 if len(sym.pins_of_unit(p.unit)) == 2 and not sym.is_power else 0
            bx0, by0, bx1, by1 = sym.bbox(p.unit)
            pts = [_rot(bx0, by0, rot), _rot(bx1, by1, rot), _rot(bx0, by1, rot), _rot(bx1, by0, rot)]
            rx0, rx1 = min(q[0] for q in pts), max(q[0] for q in pts)
            ry0, ry1 = min(q[1] for q in pts), max(q[1] for q in pts)
            placed_tmp = Placed(p, 0, 0, rot)
            ext = {'l': 0, 'r': 0, 'u': 0, 'd': 0}
            for pin in sym.pins_of_unit(p.unit):
                net = p.nets[pin.number]
                o = placed_tmp.pin_out(pin)
                L = STUB + (label_len(net) if (net and net != 'GND') else 5.08)
                key = {(1, 0): 'r', (-1, 0): 'l', (0, -1): 'u', (0, 1): 'd'}[o]
                ext[key] = max(ext[key], L)
            small = len(sym.pins_of_unit(p.unit)) <= 4
            pad = 5.08 if small else 7.62
            w = (rx1 - rx0) + ext['l'] + ext['r'] + pad
            h = (ry1 - ry0) + ext['u'] + ext['d'] + pad + (2.54 if small else 0)
            return dict(rot=rot, rx0=rx0, ry1=ry1, ext=ext, w=w, h=h, small=small)

        def layout_group(gtitle, parts, max_w):
            """Lay out one group in a block of width <= max_w. Coordinates relative to block origin."""
            pl_out, tx_out = [], []
            y = 0.0
            lines = gtitle.split('\n')
            tx_out.append((0, y, lines[0], 2.5, True))
            y += 5.08
            if len(lines) > 1:
                tx_out.append((0, y, '\n'.join(lines[1:]), 1.5, False))
                y += 2.6 * (len(lines) - 1) + 2.54
            y = snap(y + 2.54)
            text_w = max(len(lines[0]) * 2.2, max([len(t) for t in lines[1:]] + [0]) * 1.3)
            ms = [(p, measure(p)) for p in parts]
            big = [(p, m) for p, m in ms if not m['small']]
            sml = [(p, m) for p, m in ms if m['small']]
            band_y, x, band_h = y, 0.0, 0.0
            used_w = 0.0

            def put(p, m, px, py):
                X = snap(px + m['ext']['l'] - m['rx0'] + 1.27)
                Y = snap(py + m['ext']['u'] + m['ry1'] + 2.54)
                pl_out.append((p, X, Y, m['rot']))
            for p, m in big:
                if x + m['w'] > max_w and x > 0:
                    band_y, x, band_h = band_y + band_h, 0.0, 0.0
                put(p, m, x, band_y)
                x += m['w']
                used_w = max(used_w, x)
                band_h = max(band_h, m['h'])
            col_limit = max(band_h, 50.8)
            col_x, col_y, col_w = x, band_y, 0.0
            for p, m in sml:
                if col_y + m['h'] > band_y + col_limit and col_y > band_y:
                    col_x, col_y, col_w = col_x + col_w, band_y, 0.0
                if col_x + m['w'] > max_w and col_x > 0:
                    band_y = band_y + max(band_h, col_limit)
                    band_h, col_limit = 0.0, 50.8
                    col_x, col_y, col_w = 0.0, band_y, 0.0
                put(p, m, col_x, col_y)
                col_y += m['h']
                col_w = max(col_w, m['w'])
                used_w = max(used_w, col_x + col_w)
                band_h = max(band_h, col_y - band_y)
            return pl_out, tx_out, max(used_w, min(text_w, max_w)), band_y + band_h

        def layout(page_w):
            """Shelf-pack group blocks. Returns placements, texts, used height."""
            max_w = min(page_w - 2 * margin, 400.0)
            blocks = [layout_group(t, ps, max_w) for t, ps in sh.groups]
            pl_out, tx_out = [], []
            x, y, shelf_h = margin, margin + 5.08, 0.0
            for pls, txs, bw, bh in blocks:
                if x + bw > page_w - margin and x > margin:
                    x, y, shelf_h = margin, y + shelf_h + 7.62, 0.0
                ox, oy = snap(x), snap(y)
                pl_out += [(p, snap(X + ox), snap(Y + oy), r) for p, X, Y, r in pls]
                tx_out += [(tx + ox, ty + oy, t, sz, b) for tx, ty, t, sz, b in txs]
                x += bw + 12.7
                shelf_h = max(shelf_h, bh)
            return pl_out, tx_out, y + shelf_h + 7.62

        papers = [('A4', 297, 210), ('A3', 420, 297), ('A2', 594, 420), ('A1', 841, 594), ('A0', 1189, 841)]
        start = [i for i, pp in enumerate(papers) if pp[0] == sh.paper][0]
        nflag = len(flag_nets)
        for name_, pw, ph in papers[start:]:
            placements, texts, used_h = layout(pw)
            need = used_h + (40.0 if nflag else 0) + 30.0
            if need <= ph:
                break
        sh.paper, page_w = name_, pw
        for (x, y, t, sz, bold) in texts:
            add_text(x, y, t, sz, bold)
        cur_x, cur_y, row_h = margin, used_h, 0.0
        for p, X, Y, rot in placements:
            sym = p.sym
            pl = Placed(p, X, Y, rot)
            libsyms[sym.lib_id] = sym
            fields = dict(p.fields)
            items.append(_symbol_instance(sym, p.ref, p.value, X, Y, rot, p.unit, p.footprint, fields,
                                          self.name, sheet_path, dnp=p.dnp, in_bom=p.in_bom, on_board=p.on_board))
            for pin in sym.pins_of_unit(p.unit):
                net = p.nets[pin.number]
                px, py = pl.pin_xy(pin)
                if net is None:
                    items.append(['no_connect', ['at', px, py], ['uuid', Q(uid())]])
                    continue
                o = pl.pin_out(pin)
                ex, ey = snap(px + o[0] * STUB), snap(py + o[1] * STUB)
                items.append(['wire', ['pts', ['xy', px, py], ['xy', ex, ey]],
                              ['stroke', ['width', 0], ['type', 'default']], ['uuid', Q(uid())]])
                if net == 'GND':
                    place_gnd(ex, ey, o)
                else:
                    place_label(net, ex, ey, o)
        # power flags
        if flag_nets:
            cur_x, cur_y, row_h = margin, cur_y + 7.62, 0.0
            add_text(margin, cur_y - 5.08, 'Power flags (ERC: nets fed by connectors / passive parts)', 2.0)
            cur_y += 10.16
            libsyms[flag.lib_id] = flag
            for i, net in enumerate(flag_nets):
                x = snap(cur_x + 10.16)
                y = snap(cur_y + 5.08)
                items.append(_symbol_instance(flag, f'#FLG{i + 1:03d}', 'PWR_FLAG', x, y, 0, 1, '', {}, self.name,
                                              sheet_path, in_bom=False, on_board=True))
                ex, ey = x, snap(y + STUB)
                items.append(['wire', ['pts', ['xy', x, y], ['xy', ex, ey]], ['stroke', ['width', 0], ['type', 'default']],
                              ['uuid', Q(uid())]])
                if net == 'GND':
                    place_gnd(ex, ey, (0, 1))
                else:
                    place_label(net, ex, ey, (0, 1))
                cur_x += max(30.48, label_len(net) + 10.16)
                if cur_x > page_w - 60:
                    cur_x, cur_y = margin, cur_y + 30.48
        doc = ['kicad_sch', ['version', SCH_VERSION], ['generator', Q('eeschema')], ['generator_version', Q('10.0')],
               ['uuid', Q(sh.uuid)], ['paper', Q(sh.paper)],
               ['title_block', ['title', Q(sh.title)], ['date', Q('2026-10-14')], ['rev', Q('0.1')],
                ['comment', 1, Q('Generated by gen/ scripts - do not edit by hand')]],
               ['lib_symbols'] + [s.node for s in libsyms.values()]] + items + [['embedded_fonts', 'no']]
        open(f'{outdir}/{sh.filename}', 'w').write(dump(doc) + '\n')


def _symbol_instance(sym, ref, value, X, Y, rot, unit, footprint, fields, project, sheet_path,
                     dnp=False, in_bom=True, on_board=True, hide_value=False):
    u = uid(f'{sheet_path}:{ref}:{unit}')
    node = ['symbol', ['lib_id', Q(sym.lib_id)], ['at', X, Y, rot], ['unit', unit], ['body_style', 1],
            ['exclude_from_sim', 'no'], ['in_bom', 'yes' if in_bom else 'no'], ['on_board', 'yes' if on_board else 'no'],
            ['in_pos_files', 'yes' if on_board else 'no'], ['dnp', 'yes' if dnp else 'no'], ['uuid', Q(u)]]
    hidden_ref = ref.startswith('#')

    def prop(k, v, dx, dy, hide=False):
        pr = ['property', Q(k), Q(v), ['at', snap(X + dx), snap(Y + dy), rot % 180]]
        if hide:
            pr.append(['hide', 'yes'])
        pr += [['show_name', 'no'], ['do_not_autoplace', 'no'], FONT]
        return pr
    bx0, by0, bx1, by1 = sym.bbox(unit)
    pts = [_rot(bx0, by0, rot), _rot(bx1, by1, rot)]
    top = -max(q[1] for q in pts + [_rot(bx0, by1, rot), _rot(bx1, by0, rot)])
    bot = -min(q[1] for q in pts + [_rot(bx0, by1, rot), _rot(bx1, by0, rot)])
    node.append(prop('Reference', ref, 0, top - 1.27, hide=hidden_ref))
    node.append(prop('Value', value, 0, bot + 1.27, hide=(sym.is_power and ref.startswith('#FLG')) or hide_value))
    node.append(prop('Footprint', footprint, 0, 0, hide=True))
    node.append(prop('Datasheet', fields.pop('Datasheet', ''), 0, 0, hide=True))
    node.append(prop('Description', fields.pop('Description', ''), 0, 0, hide=True))
    for k, v in fields.items():
        node.append(prop(k, v, 0, 0, hide=True))
    for p in sym.pins_of_unit(unit):
        node.append(['pin', Q(p.number), ['uuid', Q(uid(f'{u}:{p.number}'))]])
    node.append(['instances', ['project', Q(project), ['path', Q(sheet_path), ['reference', Q(ref)], ['unit', unit]]]])
    return node
