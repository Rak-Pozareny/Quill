"""Read a KiCad S-expression netlist (kicad-cli sch export netlist) into plain dicts.

components: {ref: {'value', 'footprint', 'fields': {name: value}}}
nets:       {net_name: [(ref, pin), ...]}
pin_net:    {(ref, pin): net_name}
"""
from sexpr import parse


def _kids(node, tag):
    return [x for x in node[1:] if isinstance(x, list) and x and x[0] == tag]


def _kid(node, tag):
    k = _kids(node, tag)
    return k[0] if k else None


def _val(node, tag, default=''):
    k = _kid(node, tag)
    return str(k[1]) if k is not None and len(k) > 1 else default


def read(path):
    root = parse(open(path).read())
    root = root[0] if root and isinstance(root[0], list) and root[0][0] == 'export' else root
    comps, nets, pin_net = {}, {}, {}
    for c in _kids(_kid(root, 'components'), 'comp'):
        fields = {}
        fs = _kid(c, 'fields')
        if fs is not None:
            for f in _kids(fs, 'field'):
                name = _val(f, 'name')
                fields[name] = str(f[2]) if len(f) > 2 and not isinstance(f[2], list) else ''
        comps[_val(c, 'ref')] = dict(value=_val(c, 'value'), footprint=_val(c, 'footprint'), fields=fields)
    for n in _kids(_kid(root, 'nets'), 'net'):
        name = _val(n, 'name')
        nodes = [(_val(x, 'ref'), _val(x, 'pin')) for x in _kids(n, 'node')]
        nets[name] = nodes
        for rp in nodes:
            pin_net[rp] = name
    return comps, nets, pin_net
