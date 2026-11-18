"""Board A design rules: JLCPCB 6-layer limits, net classes and impedance geometry.

Sources:
- JLCPCB capabilities page, fetched 2026-10-17 (research/jlc/capabilities_2026-10-17.md).
- Trace geometry from JLCPCB's own impedance solver for stack-up JLC06121H-3313A
  (tools/jlc_impedance.py -> research/jlc/impedance_selected.json).

KiCad keeps net classes and the board rules in the .kicad_pro file and custom rules in the .kicad_dru file next to the
board; kicad-cli DRC reads both. This module writes both.
"""
import json
import re

# ---------------------------------------------------------------------------------------------------- JLC limits (mm)
JLC = dict(track=0.09, clearance=0.09, via_hole=0.15, via_dia=0.25, annular=0.05, hole_to_hole=0.2,
           via_hole_to_track=0.2, pth_to_track=0.28, npth_to_track=0.2, inner_pth_to_copper=0.3, edge=0.2,
           pad_hole_to_hole=0.45, mask_bridge=0.1)

# impedance geometry (JLC solver results, ohms in comments): width / gap per layer group
GEOM = {
    #            outer (L1/L6, microstrip)          inner (L3/L4, offset stripline)
    'USB90':  dict(out=(0.12, 0.11),  inn=(0.10, 0.11)),     # 89.6 / 90.1 ohm differential
    'PCIE85': dict(out=(0.13, 0.10),  inn=(0.11, 0.10)),     # 84.9 / 85.1
    'MIPI100': dict(out=(0.11, 0.155), inn=(0.10, 0.20)),    # 100.1 / 100.3
    'SE50':   dict(out=(0.155, None), inn=(0.125, None)),    # 50.3 / 50.5 single-ended
}

# net classes: name -> (clearance, track, via_dia, via_drill)
CLASSES = {
    # clearances: <= 20 V everywhere, so pad-level fine pitch decides (0.125 mm inside the TPS25751 / 0.15 at FH35C)
    'Default': (0.10, 0.10, 0.40, 0.20),
    # power nets carry their current in pours and trunks laid down before the autorouter (gen/route_power.py);
    # the class width is what the autorouter uses for the remaining short connections, so it fits 0.4 mm-pitch pins
    'PWR':     (0.10, 0.20, 0.40, 0.20),
    'PWR_HI':  (0.12, 0.25, 0.40, 0.20),
    'USB90':   (0.12, 0.12, 0.40, 0.20),
    'PCIE85':  (0.12, 0.13, 0.40, 0.20),
    'MIPI100': (0.12, 0.11, 0.40, 0.20),
    'SE50':    (0.12, 0.155, 0.40, 0.20),
}

PWR_HI = r'^(VSYS|BAT_P|BAT_N|BAT_SRP|CHG_IN|CHG_IN_S|CHG_SW1|CHG_SW2|CM5_VIN|VCC5V0|VBUS_C|BST_CM5_SW|BST_5V_SW|' \
         r'BB_LTE_L1|BB_LTE_L2|BB_AUX_L1|BB_AUX_L2|VCC_LTE|USBA1_VBUS|USBA2_VBUS)$'
PWR = r'^(VCC3V3_AUX|VCC_3V3_S3|VCC_1V8_S0|VCC_1V8_S3|VCC3V3_AO|PD_LDO_3V3|PD_LDO_1V5|SD_VDD|SIM_VDD|CAMA_3V3|' \
      r'CAMA_5V|CAMB_3V3|DIG_3V3|LCD_VCI|LCD_IOVCC|WL_VBAT|WL_VDDIO|WL_CBUCK|WL_ABUCK|WL_CSR_VLX|WL_ASR_VLX|BL_SW|' \
      r'BL_LEDA|BL_LEDK|VBUS_KBD|VCC5V_KBD|SPK_[LR]_[PN]|BB_\w+_VINA|PD_DRAIN|CHG_REGN|CHG_VBUS_F)$'
DIFF = [('USB90', r'^(USBC_D[PN]|USB_\w+_D[PN]|KBD_D[PN]|DIG_D[PN]|PD_BC_D[PN]|USB3_LTE_\w+_[PN])$'),
        ('PCIE85', r'^(PCIE_(TX|RX)_[PN]|WL_PCIE_(TX|RX)_[PN])$'),
        ('MIPI100', r'^(DSI_\w+_[PN]|CSI[AB]_\w+_[PN]|PCIE_REFCLK_[PN]|WL_REFCLK_[PN])$'),
        ('SE50', r'^(WL_ANT\d(_M)?|SD_CLK|SD_CLK_SOC|SD_CMD|SD_D[0-3])$')]


def classify(short):
    for cls, rx in DIFF:
        if re.match(rx, short):
            return cls
    if re.match(PWR_HI, short):
        return 'PWR_HI'
    if re.match(PWR, short):
        return 'PWR'
    return None


def _class_json(name, clearance, track, via_d, via_h):
    g = GEOM.get(name, {}).get('out')
    return {'bus_width': 12, 'clearance': clearance, 'diff_pair_gap': (g[1] if g and g[1] else 0.1),
            'diff_pair_via_gap': 0.25, 'diff_pair_width': (g[0] if g else track), 'line_style': 0,
            'microvia_diameter': 0.3, 'microvia_drill': 0.1, 'name': name, 'pcb_color': 'rgba(0, 0, 0, 0.000)',
            'priority': 2147483647 if name == 'Default' else list(CLASSES).index(name),
            'schematic_color': 'rgba(0, 0, 0, 0.000)', 'track_width': track, 'tuning_profile': '',
            'via_diameter': via_d, 'via_drill': via_h, 'wire_width': 6}


def write_project(pro_path, net_names, exclusions=None):
    """net classes, explicit net -> class assignments, JLC minimums, rule severities"""
    p = json.load(open(pro_path))
    ns = p['net_settings']
    ns['classes'] = [_class_json(n, *v) for n, v in CLASSES.items()]
    ns['netclass_patterns'] = []
    ns['netclass_assignments'] = {n: [classify(n.split('/')[-1])] for n in sorted(net_names)
                                  if classify(n.split('/')[-1])}
    ds = p['board']['design_settings']
    r = ds['rules']
    r.update(min_clearance=JLC['clearance'], min_track_width=JLC['track'], min_via_diameter=JLC['via_dia'],
             min_via_annular_width=JLC['annular'], min_through_hole_diameter=JLC['via_hole'],
             min_hole_clearance=JLC['via_hole_to_track'], min_hole_to_hole=JLC['hole_to_hole'],
             min_copper_edge_clearance=JLC['edge'], min_microvia_diameter=0.2, min_microvia_drill=0.1,
             min_text_height=0.8, min_text_thickness=0.12, min_silk_clearance=0.0)
    ds['track_widths'] = [0.0, 0.1, 0.15, 0.2, 0.3, 0.5, 0.8, 1.2]
    ds['via_dimensions'] = [{'diameter': 0.0, 'drill': 0.0}, {'diameter': 0.4, 'drill': 0.2},
                            {'diameter': 0.6, 'drill': 0.3}]
    ds['diff_pair_dimensions'] = [{'gap': 0.0, 'via_gap': 0.0, 'width': 0.0}] + \
        [{'gap': g[k][1], 'via_gap': 0.25, 'width': g[k][0]} for g in GEOM.values() for k in ('out', 'inn') if g[k][1]]
    sev = ds['rule_severities']
    # intra-pair skew (a signal-integrity target, not a fabrication limit) is reported as a warning: every pair's
    # result against its target is listed in the length report (docs/checkpoint4/length_report.md)
    sev.update(hole_to_hole='error', track_dangling='error', via_dangling='error', isolated_copper='warning',
               skew_out_of_range='warning', lib_footprint_issues='ignore', lib_footprint_mismatch='ignore')
    if exclusions is not None:
        ds['drc_exclusions'] = exclusions
    json.dump(p, open(pro_path, 'w'), indent=2)


def mm(v):
    return f'{v:g}mm'


def write_dru(path):
    """custom rules: JLC hole rules, impedance widths per layer, diff-pair coupling, skew"""
    R = ['(version 1)']
    R.append(f'(rule "PTH pad hole to copper (JLC 0.28)" (condition "A.Type == \'Pad\' && A.Pad_Type == \'Through-hole\'")'
             f' (constraint hole_clearance (min {mm(JLC["pth_to_track"])})))')
    R.append(f'(rule "PTH pad hole to inner copper (JLC 0.3)" (layer inner) '
             f'(condition "A.Type == \'Pad\' && A.Pad_Type == \'Through-hole\'") (constraint hole_clearance (min {mm(JLC["inner_pth_to_copper"])})))')
    R.append(f'(rule "NPTH to copper (JLC 0.2)" (condition "A.Pad_Type == \'NPTH, mechanical\'")'
             f' (constraint hole_clearance (min {mm(JLC["npth_to_track"])})))')
    R.append(f'(rule "pad holes (JLC 0.45)" (condition "A.Type == \'Pad\' && B.Type == \'Pad\'")'
             f' (constraint hole_to_hole (min {mm(JLC["pad_hole_to_hole"])})))')
    for cls, g in GEOM.items():
        for layers, key in (('outer', 'out'), ('inner', 'inn')):
            w, s = g[key]
            body = f'(constraint track_width (min {mm(w - 0.005)}) (opt {mm(w)}) (max {mm(w + 0.005)}))'
            if s:      # min = the 0.09 mm pair clearance, no max: KiCad also counts the breakouts at the pads (0.4-0.5 mm
                # pitch) as coupled; the coupled sections are drawn at the impedance gap (opt) by the pair router
                body += f' (constraint diff_pair_gap (min 0.09mm) (opt {mm(s)}))'
            R.append(f'(rule "{cls} {layers}" (layer {layers}) (condition "A.NetClass == \'{cls}\'") {body})')
    # FH35C camera connectors (two staggered rows): a rear-row pin's trace leaves straight between two front-row pads
    # (0.30 mm gap), the way the connector is drawn; 0.095 mm each side there, JLC's minimum is 0.09
    R.append('(rule "FH35C pass-through (JLC 0.09)" '
             '(condition "A.intersectsCourtyard(\'J704\') || A.intersectsCourtyard(\'J705\')") '
             '(constraint clearance (min 0.09mm)))')
    # PCIe AC capacitors (0201) in the 1.25 mm strip between the Wi-Fi module's pads and the M.2 card outline (D96, D114):
    # their courtyards overlap the neighbours' margins; the bodies are 0.7 mm from the module body and outside the card
    caps = ('C609', 'C610', 'C611', 'C612')
    cond = ' || '.join(f"{x}.Reference == '{c}'" for x in 'AB' for c in caps)
    R.append(f'(rule "PCIe AC capacitors beside the Wi-Fi module (D96)" (condition "{cond}") '
             '(constraint courtyard_clearance (min -1mm)))')
    # TP204 is a bare test pad on the CM5_VIN pour between C303 and C205 (D114): nothing is placed there, and the pad
    # itself keeps 0.5 mm from both parts' pads
    R.append('(rule "CM5_VIN test pad on its pour (D114)" (condition "A.Reference == \'TP204\' || B.Reference == \'TP204\'") '
             '(constraint courtyard_clearance (min -1mm)))')
    # the two traces of a pair sit at the impedance gap (0.10-0.20 mm), which may be below the class clearance
    R.append('(rule "differential pair internal gap" (condition "A.isCoupledDiffPair()") '
             '(constraint clearance (min 0.09mm)))')
    # P / N skew, the targets of the length report (tools/length_report.py intra_target; a later rule wins): USB 2.0
    # 1.27 mm and MIPI 0.15 mm, PCIe, USB 3 and the PCIe reference clocks 0.127 mm
    for name, cond, lim in (('USB 2.0', "A.NetClass == 'USB90'", 1.27), ('MIPI', "A.NetClass == 'MIPI100'", 0.15),
                            ('PCIe', "A.NetClass == 'PCIE85'", 0.127), ('USB 3', "A.NetName == '*USB3_*'", 0.127),
                            ('PCIe reference clock', "A.NetName == '*REFCLK*'", 0.127)):
        R.append(f'(rule "{name} skew" (condition "{cond} && A.inDiffPair(\'*\')")'
                 f' (constraint skew (max {mm(lim)}) (within_diff_pairs)))')
    # controlled-impedance tracks on the outer layers: the pours keep 3x the 0.0994 mm prepreg away (0.30 mm), so the
    # traces stay the plain (coated) microstrip their widths were calculated for; at the pours' own 0.09 mm they were
    # coplanar, well under their target impedance (D112). Inner layers carry no pour beside them. Last in the file: a later rule wins, and the FH35C rule
    # above matches the pours too (they cross J704 / J705)
    R.append('(rule "impedance tracks: pour 0.30 mm away on the outer layers (D112)" (layer outer) '
             '(condition "A.Type == \'Track\' && B.Type == \'Zone\' && (A.NetClass == \'MIPI100\' || '
             'A.NetClass == \'USB90\' || A.NetClass == \'PCIE85\' || A.NetClass == \'SE50\')") '
             '(constraint clearance (min 0.3mm)))')
    open(path, 'w').write('\n'.join(R) + '\n')
