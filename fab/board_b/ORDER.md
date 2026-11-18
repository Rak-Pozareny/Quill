# Board B, Q20 keyboard: JLCPCB order

Ready to upload: ERC, DRC, the track joints and the BOM check below are clean.

## Files to upload

1. PCB: `q20_keyboard_gerber.zip` (Gerbers and drill files; do not unzip).
2. Assembly: `BOM.csv` (bill of materials) and `CPL.csv` (pick and place).

## PCB options

| Option | Select | Why |
|---|---|---|
| Base material | FR-4 | |
| Layers | 2 | |
| Dimensions | 74.0 x 53.1 mm | from the Gerber outline (JLCPCB fills it in) |
| PCB qty | 5 | the minimum |
| Delivery format | Single PCB | |
| PCB thickness | 2.0 mm | the BBQ20KBD reference stack (D19) |
| PCB color | Green | any colour works; green is the reference for the solder-mask bridge rules used |
| Silkscreen | White | |
| Surface finish | ENIG (flat pads for the 0.4 mm keyboard connector J201) | the brief asks for ENIG |
| Outer copper weight | 1 oz | |
| Via covering | Tented | |
| Min via hole size / diameter | 0.3 mm hole / 0.6 mm diameter | |
| Impedance control | No | 2 layers; no controlled-impedance lines |
| Gold fingers, castellated holes, edge plating | No | |
| Mark on PCB (order number) | Remove, or let JLCPCB place it | the boards have no marked spot for it |
| Everything else | default | |

## Assembly options (PCB Assembly: on)

| Option | Select | Why |
|---|---|---|
| PCBA type | **Standard** | the board is 2.0 mm thick (Economic: 0.8-1.6 mm) and parts sit on both sides |
| Assembly side | **Both sides** | 1 part on the top, 57 on the bottom (J201, the keyboard connector, is the only top-side part: solder it by hand to make it Bottom side only, still Standard for the 2.0 mm board) |
| PCBA qty | 2 (or 5) | Standard PCBA takes 2 and up |
| Edge rails / fiducials | Added by JLCPCB | the board is smaller than Standard PCBA's 70 x 70 mm and has no fiducials of its own |
| Tooling holes | Added by JLCPCB | |
| Confirm parts placement | **Yes** | check the parts listed in ROTATIONS.md in the placement preview |

## After uploading the BOM and CPL

- The BOM has 17 lines, 58 parts; every line has an LCSC part number, and JLCPCB should match each line without asking. If it asks about a line, the LCSC number in `BOM.csv` is the one to keep.
- Placement preview: 19 parts have a pin 1 or a polarity; `ROTATIONS.md` lists them with the rotation sent and the rule it came from. Check each against pin 1 on the board.
- Nothing on this board is hand-soldered or customer-supplied; the parts that plug into it are listed in REVIEW.md (off-board parts).

## Estimated assembly cost, 5 boards (USD)

Parts at JLCPCB's live prices (`BOM_cost.csv`) and the Standard PCBA fees of JLCPCB's price page (research/jlc/order_options_2026-10-22.md); the PCB itself is priced by JLCPCB's quote at upload.

| Item | USD |
|---|---|
| Parts (58 per board, 17 types) | 27.19 |
| Setup (double-sided) | 51.12 |
| Stencil | 16.42 |
| Feeder loading (17 part types x 1.53) | 26.01 |
| Solder joints (255 per board x 5 x 0.0016) | 2.04 |
| **Total, without the PCB** | **122.78** (24.56 per board) |

## Checks on these files

| Check | Result |
|---|---|
| ERC (`kicad-cli sch erc`, `erc.json`) | 0 errors, 0 warnings |
| DRC (`kicad-cli pcb drc`, zones refilled, `drc.json`) | 0 errors, 0 warnings, 0 unconnected; 0 by-design findings excluded (reasons: `gen/route_a.py` BY_DESIGN, in the project file) |
| Schematic parity (same run) | 0 errors, 0 warnings |
| Track joints and duplicate copper (`tools/close_joints.py --check`: every track end inside same-net copper or joined by at least 95 % of its width; no copper repeated) | 0 duplicate tracks / vias; 0 track joints with a neck under 95% of the track width |
| BOM lines with an LCSC number found at JLCPCB, MPN matching, stock for 5 boards (`BOM_check.csv`, checked live) | 19 of 19 |

Also here: `q20_keyboard_schematic.pdf`, `q20_keyboard_assembly_top.pdf` / `q20_keyboard_assembly_bottom.pdf` (every reference designator; the silkscreen shows those it has room for), `q20_keyboard.step` (3D model), `STACKUP.md`, `drill_map_*.pdf`.
