# Board A, Orange Pi CM5 carrier: JLCPCB order

Ready to upload for **2 assembled boards** (PCBA qty 2): ERC, DRC and the joint checks are clean; 1 BOM line(s) lack JLCPCB stock for 5 boards (below).

## Files to upload

1. PCB: `cm5_carrier_gerber.zip` (Gerbers and drill files; do not unzip). It also holds `cm5_carrier-Impedance_Drawing.gbr`, a drawing layer (Gerber X2 FileFunction OtherDrawing) with the impedance requirements for the CAM engineers; the same as `cm5_carrier_impedance.pdf` and `IMPEDANCE.md` here, to attach when JLCPCB asks. The zip also holds `cm5_carrier_impedance_control.xlsx`, JLCPCB's own impedance form filled from the board (`tools/impedance_form.py`, D112; a copy is here too, to send when they ask for it).
2. Assembly: `BOM.csv` (bill of materials) and `CPL.csv` (pick and place).

## PCB options

| Option | Select | Why |
|---|---|---|
| Base material | FR-4 | |
| Layers | 6 | |
| Dimensions | 95.0 x 65.0 mm | from the Gerber outline (JLCPCB fills it in) |
| PCB qty | 5 | the minimum |
| Delivery format | Single PCB | |
| PCB thickness | 1.2 mm | JLC06121H-3313A is a 1.2 mm stack-up |
| PCB color | Green | any colour works; green is the reference for the solder-mask bridge rules used |
| Silkscreen | White | |
| Surface finish | ENIG (HASL is not offered on 6 layers and up; flat pads for the 0.4 mm CM5 connectors and the 0.3 mm FPC connectors) | the brief asks for ENIG |
| Outer / inner copper weight | 1 oz outer, 0.5 oz inner | the impedance geometry assumes it |
| Via covering | Epoxy Filled & Capped (JLCPCB's default on 6 layers and up; needed: vias sit in pads) | |
| Min via hole size / diameter | **0.2 mm** hole (the option listed as 0.2 mm with 0.3 / 0.35 mm diameter) | every via is 0.2 mm hole / 0.4 mm diameter (some in pads): the option goes by the hole; its 0.3 / 0.35 mm is the smallest diameter allowed with it, and 0.4 is larger, which is fine. Not the 0.25 / 0.3 mm options: they would declare larger holes than the board has |
| Impedance control | Yes, stack-up **JLC06121H-3313A** | the track widths of the 85 / 90 / 100 ohm pairs and 50 ohm lines are calculated for it (STACKUP.md) |
| Gold fingers, castellated holes, edge plating | No | |
| Mark on PCB (order number) | Remove, or let JLCPCB place it | the boards have no marked spot for it |
| Everything else | default | |

## Assembly options (PCB Assembly: on)

| Option | Select | Why |
|---|---|---|
| PCBA type | **Standard** | parts on both sides; 0201 parts; 0.3-0.4 mm pitch connectors: Economic places one side only and 0402 and up |
| Assembly side | **Both sides** | 131 parts on the top, 248 on the bottom |
| PCBA qty | 2 (or 5) | Standard PCBA takes 2 and up |
| Edge rails / fiducials | Added by JLCPCB | the board is smaller than Standard PCBA's 70 x 70 mm and has no fiducials of its own |
| Tooling holes | Added by JLCPCB | |
| Confirm parts placement | **Yes** | check the parts listed in ROTATIONS.md in the placement preview |

## Order remarks (paste into the order page)

**PCB remark:**

> Re-order of cancelled order 13909286A-Y4, with corrected files. Impedance control on stack-up JLC06121H-3313A: the requirements are in the drawing layer cm5_carrier-Impedance_Drawing.gbr and in your impedance form, filled in as cm5_carrier_impedance_control.xlsx, both inside the zip. Impedance_Drawing.gbr is documentation only, not a copper, mask or silkscreen layer. Vias are 0.2/0.4 mm and some sit in pads (epoxy filled and capped). If a track width or gap must change to meet the impedance targets, please tell me before production.

**Assembly remark:**

> Re-order of 13909286A-Y4. U601 (AP6275P): footprint corrected to AMPAK's drawing. J102 (C17389413) is the 9-circuit Molex 505578-0971; its pads follow Molex's 9-circuit drawing. J401/J402 (USB-A) overhang the bottom board edge by up to 3.0 mm, as reviewed on the previous order; please keep the bottom rail clear of them. C615, C616 and C709 are intentionally not fitted. If anything in the placement is unclear, please ask before assembly.

If the U101 parts are reserved in your JLCPCB parts inventory or pre-ordered, add: "U101 (C30169739): please use the parts reserved in my inventory."

## After uploading the BOM and CPL

- The BOM has 130 lines, 379 parts; every line has an LCSC part number, and JLCPCB should match each line without asking. If it asks about a line, the LCSC number in `BOM.csv` is the one to keep.
- Placement preview: 83 parts have a pin 1 or a polarity; `ROTATIONS.md` lists them with the rotation sent and the rule it came from. Check each against pin 1 on the board.
- Not placed by JLCPCB (do not fit): C709, C615, C616 (`not_placed.csv`).
- Nothing on this board is hand-soldered or customer-supplied; the parts that plug into it are listed in REVIEW.md (off-board parts).

## Estimated assembly cost, 5 boards (USD)

Parts at JLCPCB's live prices (`BOM_cost.csv`) and the Standard PCBA fees of JLCPCB's price page (research/jlc/order_options_2026-10-22.md); the PCB itself is priced by JLCPCB's quote at upload.

| Item | USD |
|---|---|
| Parts (379 per board, 130 types) | 312.04 |
| Setup (double-sided) | 51.12 |
| Stencil | 16.42 |
| Feeder loading (130 part types x 1.53) | 198.90 |
| Solder joints (1755 per board x 5 x 0.0016) | 14.04 |
| **Total, without the PCB** | **592.52** (118.50 per board) |

## Checks on these files

| Check | Result |
|---|---|
| ERC (`kicad-cli sch erc`, `erc.json`) | 0 errors, 0 warnings |
| DRC (`kicad-cli pcb drc`, zones refilled, `drc.json`) | 0 errors, 3 warnings, 0 unconnected; 7 by-design findings excluded (reasons: `gen/route_a.py` BY_DESIGN, in the project file) |
| Schematic parity (same run) | 0 errors, 0 warnings |
| Track and via joints, duplicate copper (`tools/close_joints.py --check`: every track end and every via inside same-net copper or joined by at least 95 % of the narrower width; no copper repeated) | 0 duplicate tracks / vias; 0 track joints with a neck under 95% of the narrower width; 0 via joints with a neck under 95% of the narrower width |
| The Gerber zip as the fab builds it (`tools/gerber_check.py`, `GERBER_CHECK.txt`: copper rebuilt from the Gerbers and drill file; shorts, opens, necks under 0.095 mm, same-net joints under 95 % that a net or a pour needs, copper held by no pad) | islands with two nets: 1 (1 at a net tie); shorts: 0; nets with pads: 308; opens: 0; copper narrower than 0.095 mm joining two parts of an island: 0; same-net joints under 95% of the narrower object: 114 (NEEDED 0, isolates 0, pour 0, redundant 114); copper with a net but no pad in its piece: 0; result: pass (0 findings) |
| BOM lines with an LCSC number found at JLCPCB, MPN matching, stock for 5 boards (`BOM_check.csv`, checked live) | 149 of 150 |
| problem | TPS25751DREFR U101 C30169739: OK LOW STOCK (need 5). JLCPCB has 2: enough for 2 boards. Assemble 2 or fewer, or wait for stock / use JLCPCB parts pre-order (REVIEW.md, at order time) |

Also here: `cm5_carrier_schematic.pdf`, `cm5_carrier_assembly_top.pdf` / `cm5_carrier_assembly_bottom.pdf` (every reference designator; the silkscreen shows those it has room for), `cm5_carrier.step` (3D model), `STACKUP.md`, `drill_map_*.pdf`.
