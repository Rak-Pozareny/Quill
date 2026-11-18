#!/usr/bin/env python3
"""Checkpoint 5: the ready-to-upload package of one board in fab/<board>/.

usage: package.py a|b

Adds board A's artwork (gen/art_a.py), places the silkscreen references (tools/silk.py) and copies the schematic's
fields and attributes to the footprints (tools/sync_pcb.py), all on hw/<board>/ in place, then runs on those files:
  ERC (kicad-cli sch erc), DRC with the schematic parity check (kicad-cli pcb drc, zones refilled, the by-design
  exclusions in the project file honoured), the fab files (tools/fab.py: Gerber + drill zip, BOM.csv, CPL.csv,
  ROTATIONS.md, not_placed.csv), the live JLCPCB check of every BOM line (tools/bom.py), the schematic PDF, the STEP
  model and the stack-up; then writes ORDER.md with the options to select on JLCPCB's order page and the check results.
Order options and their sources: research/jlc/order_options_2026-10-22.md.
"""
import csv
import json
import os
import re
import subprocess
import sys

import pcbnew

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import fab  # noqa: E402

PCBA_QTY = 2        # boards JLCPCB assembles (the PCBA qty chosen at order time, 2026-10-23); the BOM check is for 5

BOARDS = {
    'a': dict(dir='hw/board_a', name='cm5_carrier', title='Board A, Orange Pi CM5 carrier', fab='fab/board_a',
              layers=6, thickness='1.2 mm', impedance=True, stackup='JLC06121H-3313A',
              copper='1 oz outer, 0.5 oz inner', via='**0.2 mm** hole (the option listed as 0.2 mm with 0.3 / 0.35 mm diameter)',
              remarks=('Re-order of cancelled order 13909286A-Y4, with corrected files. Impedance control on stack-up JLC06121H-3313A: the requirements are in the drawing layer cm5_carrier-Impedance_Drawing.gbr and in your impedance form, filled in as cm5_carrier_impedance_control.xlsx, both inside the zip. Impedance_Drawing.gbr is documentation only, not a copper, mask or silkscreen layer. Vias are 0.2/0.4 mm and some sit in pads (epoxy filled and capped). If a track width or gap must change to meet the impedance targets, please tell me before production. Edge rails: please join them with mouse bites, holes outside the board outline, not V-cut: copper runs 0.25 mm inside the long edge opposite the USB-A ports (tabs on that edge only near the corners) and a row of GND vias 0.3 mm inside every edge.',
                       "Re-order of 13909286A-Y4. U601 (AP6275P): footprint corrected to AMPAK's drawing. J102 (C17389413) is the 9-circuit Molex 505578-0971; its pads follow Molex's 9-circuit drawing. J401/J402 (USB-A) overhang the bottom board edge by up to 3.0 mm, as reviewed on the previous order; please keep the bottom rail clear of them. C615, C616 and C709 are intentionally not fitted. If anything in the placement is unclear, please ask before assembly.",
                       'If the U101 parts are reserved in your JLCPCB parts inventory or pre-ordered, add: "U101 (C30169739): please use the parts reserved in my inventory."'),
              via_why='every via is 0.2 mm hole / 0.4 mm diameter (some in pads): the option goes by the hole; its '
                      '0.3 / 0.35 mm is the smallest diameter allowed with it, and 0.4 is larger, which is fine. Not '
                      'the 0.25 / 0.3 mm options: they would declare larger holes than the board has',
              covering='Epoxy Filled & Capped (JLCPCB\'s default on 6 layers and up; needed: vias sit in pads)',
              finish='ENIG (HASL is not offered on 6 layers and up; flat pads for the 0.4 mm CM5 connectors and the '
                     '0.3 mm FPC connectors)'),
    'b': dict(dir='hw/board_b', name='q20_keyboard', title='Board B, Q20 keyboard', fab='fab/board_b',
              layers=2, thickness='2.0 mm', impedance=False, stackup=None, copper='1 oz',
              via='0.3 mm hole / 0.6 mm diameter', covering='Tented',
              finish='ENIG (flat pads for the 0.4 mm keyboard connector J201)'),
}


def kicad(*args):
    r = subprocess.run(['kicad-cli', *args], capture_output=True, text=True)
    if r.returncode not in (0, 5):          # 5: DRC / ERC ran and found violations (counted from the report)
        sys.exit(f'kicad-cli {" ".join(args)}\n{r.stdout}\n{r.stderr}')
    return r.stdout


def erc(sch, out):
    kicad('sch', 'erc', '--format', 'json', '--severity-all', '-o', out, sch)
    d = json.load(open(out))
    vs = [v for s in d['sheets'] for v in s['violations'] if not v.get('excluded')]
    return sum(v['severity'] == 'error' for v in vs), sum(v['severity'] == 'warning' for v in vs)


def drc(pcb, out):
    kicad('pcb', 'drc', '--format', 'json', '--severity-all', '--schematic-parity', '--refill-zones', '-o', out, pcb)
    d = json.load(open(out))
    live = [v for v in d['violations'] if not v.get('excluded')]
    par = [v for v in d.get('schematic_parity', []) if not v.get('excluded')]
    return dict(errors=sum(v['severity'] == 'error' for v in live), warnings=sum(v['severity'] == 'warning' for v in live),
                excluded=sum(1 for v in d['violations'] if v.get('excluded')), unconnected=len(d['unconnected_items']),
                parity_errors=sum(v['severity'] == 'error' for v in par), parity=len(par),
                types=sorted({v['type'] for v in live if v['severity'] == 'error'}))


def stackup(pcb):
    txt = open(pcb).read()
    blk = txt[txt.index('(stackup'):]
    blk = blk[:blk.index('(copper_finish')]
    rows = []
    for m in re.finditer(r'\(layer "([^"]+)"\s*\(type "([^"]+)"\)(.*?)\n\t\t\t\)', blk, re.S):
        th = re.search(r'\(thickness ([\d.]+)\)', m.group(3))
        mat = re.search(r'\(material "([^"]+)"\)', m.group(3))
        er = re.search(r'\(epsilon_r ([\d.]+)\)', m.group(3))
        rows.append((m.group(1), m.group(2), th.group(1) if th else '', mat.group(1) if mat else '', er.group(1) if er else ''))
    return rows


def main():
    key = sys.argv[1]
    B = BOARDS[key]
    os.chdir(ROOT)
    d, name, out = B['dir'], B['name'], B['fab']
    os.makedirs(out, exist_ok=True)
    pcb, sch = f'{d}/{name}.kicad_pcb', f'{d}/{name}.kicad_sch'
    # board A's artwork (logo, hidden text) before the references, which then keep clear of it
    if key == 'a':
        r = subprocess.run([sys.executable, 'gen/art_a.py', pcb], capture_output=True, text=True)
        if r.returncode:
            sys.exit(f'gen/art_a.py failed\n{r.stderr}')
        print('\n'.join(ln for ln in r.stdout.splitlines() if 'Debug' not in ln))
    # the silkscreen references (in place: the routing scripts leave them where the placement put them)
    r = subprocess.run([sys.executable, 'tools/silk.py', pcb], capture_output=True, text=True)
    print('\n'.join(ln for ln in r.stdout.splitlines() if 'Debug' not in ln))
    # the footprints' fields and attributes as in the schematic (nothing moves)
    r = subprocess.run([sys.executable, 'tools/sync_pcb.py', pcb], capture_output=True, text=True)
    print('\n'.join(ln for ln in r.stdout.splitlines() if 'Debug' not in ln))
    ee, ew = erc(sch, f'{out}/erc.json')
    dr = drc(pcb, f'{out}/drc.json')
    # the pours refilled with the board's own design rules and saved (the scripts above refill with KiCad's Python
    # filler, which leaves the custom rules out: D112, pours 0.30 mm from impedance tracks on the outer layers)
    if key == 'a':
        r = subprocess.run([sys.executable, 'tools/refill_pours.py', pcb], capture_output=True, text=True)
        if r.returncode:
            sys.exit(f'tools/refill_pours.py failed\n{r.stdout}\n{r.stderr}')
        print('\n'.join(ln for ln in r.stdout.splitlines() if 'Debug' not in ln))
    # joints that only touch and duplicate copper: KiCad's DRC passes both, a fab's CAM does not (D110)
    r = subprocess.run([sys.executable, 'tools/close_joints.py', pcb, '--check'], capture_output=True, text=True)
    jl = [ln for ln in r.stdout.splitlines() if 'Debug' not in ln]
    joints_ok = r.returncode == 0
    jcheck = '; '.join(ln for ln in jl if ln.endswith(('width', 'vias')))
    print(f'joints: {jcheck}')
    print(f'ERC: {ee} errors, {ew} warnings; DRC: {dr}')

    sys.argv = ['fab.py', pcb, out, name]
    fab.main()
    # the Gerber zip itself, rebuilt and checked as a fab's CAM builds it (D116: shorts, opens, necks, joint widths).
    # It needs shapely: the interpreter in GERBER_CHECK_PYTHON (a venv with shapely), else this one
    gpy = os.environ.get('GERBER_CHECK_PYTHON', sys.executable)
    r = subprocess.run([gpy, '-I', 'tools/gerber_check.py', f'{out}/{name}_gerber.zip', name, f'{out}/GERBER_CHECK.txt'],
                       capture_output=True, text=True)
    gl = r.stdout.splitlines()
    if r.returncode in (0, 1) and gl and gl[-1].startswith('result'):
        gerber_ok = r.returncode == 0
        gcheck = '; '.join(ln[3:] for ln in gl if re.match(r'^[1-5]\. ', ln)) + f'; {gl[-1]}'
    else:
        gerber_ok = False
        gcheck = 'NOT RUN (needs shapely: set GERBER_CHECK_PYTHON to a Python that has it)'
    print(f'Gerber check: {gcheck}')
    r = subprocess.run([sys.executable, '-I', 'tools/bom.py', d, name, f'{out}/BOM_check.csv'], capture_output=True,
                       text=True)
    print(r.stdout.strip())
    check = list(csv.reader(open(f'{out}/BOM_check.csv')))
    hdr, lines = check[0], check[1:]
    ci = next(i for i, h in enumerate(hdr) if h.startswith('Check'))
    si = hdr.index('Sourcing')
    bad = [ln for ln in lines if ln[si] == 'JLC' and ln[ci] != 'OK']
    # stock short of 5 boards but enough for the boards actually assembled (PCBA_QTY) does not hold the order up
    ki = next(i for i, h in enumerate(hdr) if h.startswith('JLC stock'))
    qi = hdr.index('Qty')
    covers = lambda x: ('LOW STOCK' in x[ci] and x[ki].isdigit() and x[qi].isdigit() and int(x[qi])
                        and int(x[ki]) // int(x[qi]) >= PCBA_QTY)
    short = [x for x in bad if not covers(x)]
    kicad('sch', 'export', 'pdf', '-o', f'{out}/{name}_schematic.pdf', sch)
    # assembly drawings: every reference is on the Fab layers, also those the silkscreen has no room for
    for side, layers, mirror in (('top', 'F.Fab,Edge.Cuts', []), ('bottom', 'B.Fab,Edge.Cuts', ['--mirror'])):
        kicad('pcb', 'export', 'pdf', '--mode-single', '--sketch-pads-on-fab-layers', '--black-and-white', '--scale', '0', '--exclude-value', *mirror,
              '--layers', layers, '-o', f'{out}/{name}_assembly_{side}.pdf', pcb)
    # (kicad-cli 10.0.6 returns 2 from the STEP export even when it writes the file and reports nothing)
    if os.path.exists(f'{out}/{name}.step'):
        os.remove(f'{out}/{name}.step')
    subprocess.run(['kicad-cli', 'pcb', 'export', 'step', '--force', '--subst-models', '-o', f'{out}/{name}.step', pcb],
                   capture_output=True)
    if not os.path.exists(f'{out}/{name}.step'):
        sys.exit('STEP export failed')

    b = pcbnew.LoadBoard(pcb)
    bb = b.GetBoardEdgesBoundingBox()
    w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
    parts, skipped = fab.placed(b)
    top = sum(not f.IsFlipped() for f in parts)
    bot = len(parts) - top
    side = 'Both sides' if top and bot else ('Top side' if top else 'Bottom side')
    groups = len({(fab.field(f, 'LCSC'), str(f.GetFPID().GetLibItemName())) for f in parts})
    rot = sum(1 for ln in open(f'{out}/ROTATIONS.md') if ln.startswith('| ') and not ln.startswith('| Ref'))

    # parts cost (live JLCPCB prices) and assembly fees (research/jlc/order_options_2026-10-22.md), 5 boards
    r = subprocess.run([sys.executable, '-I', 'tools/bom_cost.py', f'{out}/BOM.csv', '--boards', '5'], capture_output=True,
                       text=True)
    open(f'{out}/BOM_cost.csv', 'w').write(r.stdout)
    parts_cost = float(re.search(r'parts for 5 boards: ([\d.]+) USD', r.stderr).group(1))
    joints = sum(1 for f in parts for p in f.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH and p.IsOnCopperLayer())
    two = top and bot
    fees = dict(setup=51.12 if two else 25.56, stencil=16.42 if two else 8.21, feeders=1.53 * groups,
                joints=0.0016 * joints * 5)
    cost = dict(parts=parts_cost, **fees)

    st = stackup(pcb)
    with open(f'{out}/STACKUP.md', 'w') as fh:
        fh.write(f'# {B["title"]}: stack-up\n\n'
                 f'{B["layers"]} layers, {B["thickness"]}' +
                 (f', JLCPCB stack-up **{B["stackup"]}** (impedance control, +-10 %)' if B['stackup'] else '') +
                 ', as entered in the board file (KiCad Board Setup > Physical Stackup).\n\n'
                 '| Layer | Type | Thickness (mm) | Material | Er |\n|---|---|---|---|---|\n')
        for r_ in st:
            fh.write(f'| {r_[0]} | {r_[1]} | {r_[2]} | {r_[3]} | {r_[4]} |\n')
        if B['impedance']:
            fh.write('\nControlled-impedance geometry (JLCPCB impedance calculator for this stack-up, '
                     '`research/jlc/impedance_selected.json`; layer use and the full table in '
                     '`docs/checkpoint4/CHECKPOINT4.md` section 2):\n\n'
                     '| Interface | Target | Outer layer W / S | Inner layer W / S |\n|---|---|---|---|\n'
                     '| USB 2.0 / USB 3 | 90 ohm diff | 0.12 / 0.11 mm | 0.10 / 0.11 mm |\n'
                     '| PCIe | 85 ohm diff | 0.13 / 0.10 mm | 0.11 / 0.10 mm |\n'
                     '| MIPI DSI / CSI, PCIe refclk | 100 ohm diff | 0.11 / 0.155 mm | 0.10 / 0.20 mm |\n'
                     '| SD card, Wi-Fi antenna | 50 ohm | 0.155 mm | 0.125 mm |\n')

    ok = ee == 0 and dr['errors'] == 0 and dr['unconnected'] == 0 and dr['parity_errors'] == 0 and not short and joints_ok \
        and gerber_ok
    o = []
    o.append(f'# {B["title"]}: JLCPCB order\n')
    o.append(('**Not ready: see the checks below.**' if not ok else
              'Ready to upload: ERC, DRC, the joint checks (board and Gerber zip) and the BOM check below are clean.' if not bad else
              f'Ready to upload for **{PCBA_QTY} assembled boards** (PCBA qty {PCBA_QTY}): ERC, DRC and the joint checks are '
              f'clean; {len(bad)} BOM line(s) lack JLCPCB stock for 5 boards (below).') + '\n')
    o.append('## Files to upload\n')
    o.append(f'1. PCB: `{name}_gerber.zip` (Gerbers and drill files; do not unzip).' +
             (f' It also holds `{name}-Impedance_Drawing.gbr`, a drawing layer (Gerber X2 FileFunction OtherDrawing) '
              f'with the impedance requirements for the CAM engineers; the same as `{name}_impedance.pdf` and '
              '`IMPEDANCE.md` here, to attach when JLCPCB asks.' if os.path.exists(f'{out}/IMPEDANCE.md') else '') +
             (f' The zip also holds `{name}_impedance_control.xlsx`, JLCPCB\'s own impedance form filled from the '
              'board (`tools/impedance_form.py`, D112; a copy is here too, to send when they ask for it).'
              if os.path.exists(f'{out}/{name}_impedance_control.xlsx') else ''))
    o.append('2. Assembly: `BOM.csv` (bill of materials) and `CPL.csv` (pick and place).\n')
    o.append('## PCB options\n')
    o.append('| Option | Select | Why |\n|---|---|---|')
    o += [
        '| Base material | FR-4 | |',
        f'| Layers | {B["layers"]} | |',
        f'| Dimensions | {w:.1f} x {h:.1f} mm | from the Gerber outline (JLCPCB fills it in) |',
        '| PCB qty | 5 | the minimum |',
        '| Delivery format | Single PCB | |',
        f'| PCB thickness | {B["thickness"]} | ' + ('JLC06121H-3313A is a 1.2 mm stack-up |' if key == 'a' else
                                                    'the BBQ20KBD reference stack (D19) |'),
        '| PCB color | Green | any colour works; green is the reference for the solder-mask bridge rules used |',
        '| Silkscreen | White | |',
        f'| Surface finish | {B["finish"]} | the brief asks for ENIG |',
        f'| Outer / inner copper weight | {B["copper"]} | the impedance geometry assumes it |' if B['impedance'] else
        f'| Outer copper weight | {B["copper"]} | |',
        f'| Via covering | {B["covering"]} | |',
        f'| Min via hole size / diameter | {B["via"]} | {B.get("via_why", "")} |',
    ]
    if B['impedance']:
        o.append(f'| Impedance control | Yes, stack-up **{B["stackup"]}** | the track widths of the 85 / 90 / 100 ohm '
                 'pairs and 50 ohm lines are calculated for it (STACKUP.md) |')
    else:
        o.append('| Impedance control | No | 2 layers; no controlled-impedance lines |')
    o += ['| Gold fingers, castellated holes, edge plating | No | |',
          '| Mark on PCB (order number) | Remove, or let JLCPCB place it | the boards have no marked spot for it |',
          '| Everything else | default | |\n']
    o.append('## Assembly options (PCB Assembly: on)\n')
    o.append('| Option | Select | Why |\n|---|---|---|')
    o += [
        '| PCBA type | **Standard** | ' + ('parts on both sides; 0201 parts; 0.3-0.4 mm pitch connectors: Economic '
                                         'places one side only and 0402 and up |' if key == 'a' else
                                         'the board is 2.0 mm thick (Economic: 0.8-1.6 mm) and parts sit on both '
                                         'sides |'),
        f'| Assembly side | **{side}** | {top} part{"s" * (top != 1)} on the top, {bot} on the bottom' +
        (' (J201, the keyboard connector, is the only top-side part: solder it by hand to make it Bottom side only, '
         'still Standard for the 2.0 mm board) |' if key == 'b' else ' |'),
        '| PCBA qty | 2 (or 5) | Standard PCBA takes 2 and up |',
        f'| Edge rails / fiducials | Added by JLCPCB | the board is smaller than Standard PCBA\'s 70 x 70 mm and has '
        'no fiducials of its own |',
        '| Tooling holes | Added by JLCPCB | |',
        '| Confirm parts placement | **Yes** | check the parts listed in ROTATIONS.md in the placement preview |\n',
    ]
    if B.get('remarks'):
        o.append('## Order remarks (paste into the order page)\n')
        o.append('**PCB remark:**\n\n> ' + B['remarks'][0] + '\n')
        o.append('**Assembly remark:**\n\n> ' + B['remarks'][1] + '\n')
        o.append(B['remarks'][2] + '\n')
    o.append('## After uploading the BOM and CPL\n')
    o.append(f'- The BOM has {groups} lines, {len(parts)} parts; every line has an LCSC part number, and JLCPCB should '
             'match each line without asking. If it asks about a line, the LCSC number in `BOM.csv` is the one to '
             'keep.')
    o.append(f'- Placement preview: {rot} parts have a pin 1 or a polarity; `ROTATIONS.md` lists them with the '
             'rotation sent and the rule it came from. Check each against pin 1 on the board.')
    if skipped:
        o.append(f'- Not placed by JLCPCB (do not fit): ' + ', '.join(f.GetReference() for f, _ in skipped) +
                 ' (`not_placed.csv`).')
    o.append('- Nothing on this board is hand-soldered or customer-supplied; the parts that plug into it are listed '
             'in REVIEW.md (off-board parts).\n')
    o.append('## Estimated assembly cost, 5 boards (USD)\n')
    o.append('Parts at JLCPCB\'s live prices (`BOM_cost.csv`) and the Standard PCBA fees of JLCPCB\'s price page '
             '(research/jlc/order_options_2026-10-22.md); the PCB itself is priced by JLCPCB\'s quote at upload.\n')
    o.append('| Item | USD |\n|---|---|')
    o.append(f'| Parts ({len(parts)} per board, {groups} types) | {cost["parts"]:.2f} |')
    o.append(f'| Setup ({"double" if two else "single"}-sided) | {cost["setup"]:.2f} |')
    o.append(f'| Stencil | {cost["stencil"]:.2f} |')
    o.append(f'| Feeder loading ({groups} part types x 1.53) | {cost["feeders"]:.2f} |')
    o.append(f'| Solder joints ({joints} per board x 5 x 0.0016) | {cost["joints"]:.2f} |')
    o.append(f'| **Total, without the PCB** | **{sum(cost.values()):.2f}** ({sum(cost.values()) / 5:.2f} per board) |\n')
    o.append('## Checks on these files\n')
    o.append('| Check | Result |\n|---|---|')
    o.append(f'| ERC (`kicad-cli sch erc`, `erc.json`) | {ee} errors, {ew} warnings |')
    o.append(f'| DRC (`kicad-cli pcb drc`, zones refilled, `drc.json`) | {dr["errors"]} errors, {dr["warnings"]} warnings, '
             f'{dr["unconnected"]} unconnected; {dr["excluded"]} by-design findings excluded (reasons: `gen/route_a.py` BY_DESIGN, '
             'in the project file) |')
    o.append(f'| Schematic parity (same run) | {dr["parity_errors"]} errors, {dr["parity"] - dr["parity_errors"]} warnings |')
    o.append(f'| Track and via joints, duplicate copper (`tools/close_joints.py --check`: every track end and every via '
             f'inside same-net copper or joined by at least 95 % of the narrower width; no copper repeated) | {jcheck} |')
    o.append(f'| The Gerber zip as the fab builds it (`tools/gerber_check.py`, `GERBER_CHECK.txt`: copper rebuilt from the '
             f'Gerbers and drill file; shorts, opens, necks under 0.095 mm, same-net joints under 95 % that a net or a '
             f'pour needs, copper held by no pad) | {gcheck} |')
    o.append(f'| BOM lines with an LCSC number found at JLCPCB, MPN matching, stock for 5 boards (`BOM_check.csv`, '
             f'checked live) | {len([x for x in lines if x[si] == "JLC"]) - len(bad)} of '
             f'{len([x for x in lines if x[si] == "JLC"])} |')
    if bad:
        for x in bad:
            note = ''
            if 'LOW STOCK' in x[ci] and x[ki].isdigit() and x[qi].isdigit() and int(x[qi]):
                n = int(x[ki]) // int(x[qi])
                note = (f' JLCPCB has {x[ki]}: enough for {n} board{"s" * (n != 1)}. Assemble {n} or fewer, or wait for '
                        'stock / use JLCPCB parts pre-order (REVIEW.md, at order time)')
            o.append(f'| problem | {x[0]} {x[1]} {x[3]}: {x[ci]}.{note} |')
    o.append('\nAlso here: `' + f'{name}_schematic.pdf' + '`, `' + f'{name}_assembly_top.pdf' + '` / `' +
             f'{name}_assembly_bottom.pdf' + '` (every reference designator; the silkscreen shows those it has room '
             'for), `' + f'{name}.step' + '` (3D model), `STACKUP.md`, `drill_map_*.pdf`.\n')
    open(f'{out}/ORDER.md', 'w').write('\n'.join(o))
    print(f'{out}/ORDER.md: {"ready" if ok else "NOT READY"}')


if __name__ == '__main__':
    main()
