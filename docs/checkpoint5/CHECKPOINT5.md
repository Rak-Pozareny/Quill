# Checkpoint 5: fabrication outputs

> **Board A was redesigned for the Orange Pi CM5 on 2026-10-22/23** (the Radxa CM5 cannot be ordered). This report describes the Radxa CM5 version, kept in `archive/radxa_cm5_2026-10-22/`; the current Board A, its routing results and checks are in `docs/opi/OPI_REDESIGN.md`. Board B is unchanged.

Status, 2026-10-22: **done.** Both packages are in `fab/` and pass every check on the final files: ERC 0, DRC 0 errors and 0 unconnected, schematic parity 0, and every BOM line found at JLCPCB with stock for 5 boards. Board A has 4 skew warnings (section 6 of CHECKPOINT4.md) and its 7 by-design exclusions.

| | Board A, CM5 carrier | Board B, Q20 keyboard |
|---|---|---|
| Package | `fab/board_a/` | `fab/board_b/` |
| Order sheet | `fab/board_a/ORDER.md` | `fab/board_b/ORDER.md` |
| ERC | 0 errors, 0 warnings | 0 errors, 0 warnings |
| DRC, zones refilled, with schematic parity | 0 errors, 4 skew warnings, 0 unconnected, parity 0; 7 by-design findings excluded | 0 errors, 0 warnings, 0 unconnected, parity 0 |
| BOM lines checked live at JLCPCB | 131 of 131 (LCSC number found, MPN matching, stock for 5 boards) | 16 of 16 (same) |
| Parts placed by JLCPCB | 374 (130 top, 244 bottom); 6 do-not-fit | 57 (1 top, 56 bottom) |
| Parts to check in the placement preview | 83 (27 with a rotation correction) | 19 (15) |

The final report is `REVIEW.md` in the project root.

## 1. What each package contains

| File | What | How |
|---|---|---|
| `<name>_gerber.zip` | the upload for the PCB: every copper layer, paste, silkscreen, mask, Edge.Cuts, and the plated / non-plated Excellon drill files | `tools/fab.py`, with the settings of JLCPCB's KiCad guide (section 2) |
| `BOM.csv` | the upload for assembly: Comment, Designator, Footprint, LCSC Part #, one line per LCSC part and footprint | from the board's footprints; Sourcing JLC only (holes, test pads and jumpers have no part; do-not-fit parts in `not_placed.csv`) |
| `CPL.csv` | the upload for assembly: Designator, Val, Package, Mid X, Mid Y, Rotation, Layer (mm) | pad-centre position and JLCPCB rotation (section 3) |
| `ORDER.md` | every option to select on the order page, why, the cost estimate, and the checks run on these files | `tools/package.py` |
| `ROTATIONS.md` | every placed part with a pin 1 or a polarity: the rotation sent and the rule it came from | `tools/fab.py` |
| `BOM_check.csv` | every BOM line checked live at JLCPCB: library, stock, MPN match | `tools/bom.py` |
| `BOM_cost.csv` | every BOM line priced live at JLCPCB for 5 boards | `tools/bom_cost.py` |
| `<name>_schematic.pdf` | the schematics | `kicad-cli sch export pdf` |
| `<name>_assembly_top.pdf`, `_bottom.pdf` | assembly drawings: part outlines and every reference designator (the silkscreen shows only those it has room for) | `kicad-cli pcb export pdf`, Fab layers |
| `<name>.step` | 3D model of the assembled board | `kicad-cli pcb export step` |
| `STACKUP.md` | the stack-up as entered in the board file; for Board A the impedance geometry | from the board file |
| `erc.json`, `drc.json` | the ERC and DRC reports of these exact files | `kicad-cli` |
| `drill_map_*.pdf` | drill maps (kept out of the zip: JLCPCB reads every file in it as a layer) | `kicad-cli pcb export drill` |

## 2. Sources for the formats and order options

`research/jlc/order_options_2026-10-22.md` quotes each:
- Gerber and drill settings: JLCPCB, "How to generate Gerber and drill files in KiCad 8" (layers, Protel extensions,
  soldermask subtracted from silkscreen; drill origin absolute, millimetres, decimal, alternate oval-hole mode).
- BOM and CPL columns: JLCPCB, "How to generate the BOM and centroid file from KiCad".
- Board options (thickness, ENIG, epoxy-filled vias, copper weights, impedance control): JLCPCB's PCB capabilities
  page. HASL is not offered on 6 layers and up, so Board A is ENIG anyway; Board B is ENIG for its 0.4 mm connector.
- Assembly type: JLCPCB's assembly capabilities page. Both boards need **Standard PCBA**: Board A has parts on both
  sides and 0201 parts; Board B is 2.0 mm thick (Economic: 0.8-1.6 mm) and its keyboard connector is on the other side
  from the rest. Standard PCBA needs edge rails and fiducials and a board of at least 70 x 70 mm: both boards are
  smaller, so the order asks JLCPCB to add the rails.
- Assembly fees: JLCPCB's PCBA price page (setup, stencil, feeder loading, joints).

I could not load JLCPCB's order page itself (it is an application, not a page). The option names in `ORDER.md` are the
ones the help and capability pages use; where a label on the order page differs, the option with that meaning is meant.

## 3. CPL rotations

KiCad's footprints and JLCPCB's library footprints are not always drawn the same way round. JLCPCB does not publish its
footprints' orientation in a form that can be read (the EasyEDA API refuses requests), so:
- Position: the centre of the footprint's soldered pads, Y negated, absolute coordinates like the Gerbers.
- Rotation: KiCad's angle; on the bottom side mirrored as (180 - angle); plus a correction where the footprint matches
  a rule of JLCKicadTools' rotation table (for example SOT-23 -90, SOIC 270, SOT-353 / SOT-363 180, USON-10 270). The
  method is Bouni's kicad-jlcpcb-tools (MIT); the table is matthewlai's JLCKicadTools (GPL-3: only the values for the
  footprints used here are in `tools/fab.py`, the file is not copied).
- Every placed part with a pin 1 or a polarity is in `ROTATIONS.md`, to be checked in JLCPCB's placement preview at
  order time. Plain resistors, capacitors and inductors look the same either way round and are left out.

The table's rules are what other KiCad users found for JLCPCB's library; they are not checked against JLCPCB's own
footprints here, so the preview check is not optional.

## 4. Silkscreen

Checkpoint 4 left silkscreen warnings on both boards (Board A 434 or more: KiCad lists at most 199 of a kind; Board B 166), nearly all reference
designators sitting on pads, on each other or at the board edge. `tools/silk.py` moves each reference to a free spot
around its part (0.15 mm from pads, JLCPCB's minimum; clear of other silkscreen; 0.3 mm inside the edge) and hides it
where there is none; KiCad's DRC then confirms. Where two parts' own outlines overlap, the smaller part's line goes;
where an edge-mounted part's outline runs to the board edge, those lines go.

| | Board A | Board B |
|---|---|---|
| References shown | 128 | 39 |
| References hidden (no room; on the assembly drawing) | 303 | 28 |
| Outline lines removed | 12 (USB-C, USB-A and side-button outlines at the edge) | 1 (R101 against the RP2040's pin-1 mark) |
| Silkscreen findings left | 0 | 0 |

Text stays 1.0 mm high with a 0.15 mm line, JLCPCB's minimum. Copper is not touched.

## 5. Checks on the final files

`tools/package.py` runs the checks on exactly the files that are zipped and uploaded:
- ERC on the schematics (`kicad-cli sch erc`).
- DRC with the zones refilled and the schematic parity check (`kicad-cli pcb drc --schematic-parity
  --refill-zones`); Board A's by-design findings are excluded in the project file with their reason (CHECKPOINT4.md
  section 7).
- Every BOM line looked up at JLCPCB: the LCSC number exists, its MPN matches the schematic's, and the stock covers 5
  boards.

Also synced before the checks (`tools/sync_pcb.py`, KiCad's "Update PCB from Schematic" for fields and attributes
only): the footprints now carry every schematic field (the 'Status' field was missing on all of them), the six
do-not-fit parts carry KiCad's do-not-populate attribute, and the schematic marks the holes, test pads and solder
jumpers as not in the BOM, as their footprints are. KiCad's schematic parity check found 256 or more warnings on Board A (at most 199 of a kind are listed) and
77 on Board B before; none now.

One thing went wrong on the way and is fixed: re-generating the schematics (for the BOM flags) rewrote both projects'
`.kicad_pro` with the schematic template, which dropped the net classes, DRC severities and Board A's by-design
exclusions that the routing scripts keep there. Both files were restored from the copies the routing produced, and
`gen/verify.py` now keeps an existing project file's board sections when it writes the schematic ones.

## 6. Re-generating

```
python3 tools/package.py a
python3 tools/package.py b
```
