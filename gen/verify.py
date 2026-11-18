"""Run KiCad ERC and netlist export on a generated project and compare against intended nets."""
import json
import os
import subprocess
import sys
from sexpr import parse, find, find_all

PRO_TEMPLATE = {
    "meta": {"filename": "", "version": 3},
    "schematic": {"drawing": {"default_line_thickness": 6.0}},
    "erc": {"erc_exclusions": [], "meta": {"version": 0}},
    "net_settings": {"classes": [{"name": "Default", "clearance": 0.1, "track_width": 0.15,
                                  "via_diameter": 0.45, "via_drill": 0.2,
                                  "diff_pair_width": 0.1, "diff_pair_gap": 0.15}], "meta": {"version": 4}},
    "pcbnew": {"last_paths": {}},
    "sheets": [],
    "text_variables": {}
}


def write_project_file(outdir, name, sheets=None, net_classes=None):
    """the project file for the schematics. An existing one keeps its board sections (net classes, DRC rules,
    severities and exclusions that the routing scripts write there); only the schematic sections are reset"""
    path = os.path.join(outdir, name + ".kicad_pro")
    pro = json.loads(json.dumps(PRO_TEMPLATE))
    if os.path.exists(path):
        old = json.load(open(path))
        for k in ("schematic", "erc", "sheets", "text_variables"):
            old[k] = pro[k]
        pro = old
    pro["meta"]["filename"] = name + ".kicad_pro"
    if net_classes:
        pro["net_settings"]["classes"] += net_classes
    with open(path, 'w') as f:
        json.dump(pro, f, indent=2)
    return path


def run_erc(outdir, name):
    rpt = os.path.join(outdir, f'{name}-erc.json')
    r = subprocess.run(['kicad-cli', 'sch', 'erc', '--format', 'json', '--severity-all', '-o', rpt,
                        os.path.join(outdir, name + '.kicad_sch')], capture_output=True, text=True)
    if not os.path.exists(rpt):
        print(r.stdout, r.stderr)
        raise RuntimeError('ERC failed to run')
    data = json.load(open(rpt))
    viol = []
    for sheet in data.get('sheets', []):
        for v in sheet.get('violations', []):
            viol.append((v.get('severity'), v.get('type'), v.get('description'), sheet.get('path'),
                         [i.get('description') for i in v.get('items', [])]))
    return viol


def export_netlist(outdir, name):
    net = os.path.join(outdir, f'{name}.net')
    r = subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', net,
                        os.path.join(outdir, name + '.kicad_sch')], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        raise RuntimeError('netlist export failed')
    root = parse(open(net).read())[0]
    nets = {}
    for n in find_all(find(root, 'nets'), 'net'):
        nm = str(find(n, 'name')[1])
        nodes = set()
        for nd in find_all(n, 'node'):
            nodes.add((str(find(nd, 'ref')[1]), str(find(nd, 'pin')[1])))
        nets[nm] = nodes
    comps = {}
    for c in find_all(find(root, 'components'), 'comp'):
        ref = str(find(c, 'ref')[1])
        comps[ref] = {'value': str(find(c, 'value')[1]),
                      'footprint': str(find(c, 'footprint')[1]) if find(c, 'footprint') else ''}
    return nets, comps


def expand_pin(pin):
    """KiCad stacked pin numbers: '[11,12,14]' or '[4-7]' -> ['11','12','14'] / ['4','5','6','7']."""
    if not (pin.startswith('[') and pin.endswith(']')):
        return [pin]
    out = []
    for part in pin[1:-1].split(','):
        if '-' in part:
            a, b = part.split('-')
            out += [str(i) for i in range(int(a), int(b) + 1)]
        else:
            out.append(part)
    return out


def compare(expected, actual):
    """expected: name -> set((ref,pin)); actual: exported name -> set. Returns list of problems."""
    expected = {nm: {(r, q) for r, p in nodes for q in expand_pin(p)} for nm, nodes in expected.items()}
    probs = []
    by_node = {}
    for nm, nodes in actual.items():
        for nd in nodes:
            by_node[nd] = nm
    for nm, nodes in expected.items():
        names = {by_node.get(nd) for nd in nodes}
        if None in names:
            probs.append(f'net {nm}: nodes missing from netlist {[nd for nd in nodes if nd not in by_node]}')
            continue
        if len(names) > 1:
            probs.append(f'net {nm}: split across {sorted(names)}')
            continue
        got = actual[names.pop()]
        extra = {nd for nd in got if not nd[0].startswith('#')} - nodes
        if extra:
            probs.append(f'net {nm}: unexpected extra nodes {sorted(extra)}')
    return probs
