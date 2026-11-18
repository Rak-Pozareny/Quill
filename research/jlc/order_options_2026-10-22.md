# JLCPCB order options used for ORDER.md (fetched 2026-10-22)

## PCB (https://jlcpcb.com/capabilities/pcb-capabilities)

- Board thickness, FR-4: "Thickness for FR4 are: 0.4/0.6/0.8/1.0/1.2/1.6/2.0 mm." (1.2 mm for Board A, 2.0 mm for
  Board B.)
- Surface finish: "HASL (leaded / lead-free), ENIG, OSP". HASL is not available for "FR-4/HDI boards with 6 or more
  layers": Board A must be ENIG; Board B is ENIG by choice (0.4 mm keyboard connector).
- Via covering, epoxy filled and capped: "Vias are filled with epoxy resin or copper paste and then plated over to
  achieve an opaque and smooth finish." "This process is the default for 6-layer and above multilayer boards."
  "Compatible with via diameters from 0.15 to 0.55 mm." (Board A's vias are 0.4 mm, some in pads.)
- Copper: outer "Multi-layer: 1 oz / 2 oz"; inner "0.5 oz / 1 oz / 2 oz", 0.5 oz default; 2-layer outer from 1 oz.
- Impedance control: "4/6/8/10/12/14/16/18/20/.../32 layers", "Impedance Tolerance ±10%" (±5 % on request).
- Solder mask: "Green, Purple, Red, Yellow, Blue, White, and Black" (the page does not say which go with ENIG).

## Assembly (https://jlcpcb.com/capabilities/pcb-assembly-capabilities)

| | Economic PCBA | Standard PCBA |
|---|---|---|
| Assembly type | "Single sided placement (SMT/Thru-hole)" | "Single & double sided placement (SMT/Thru-hole)" |
| Board thickness | "0.8mm - 1.6mm" | "No limit" |
| Single PCB size | "10x10mm - 470x500mm" | "70x70mm - 460x500mm" |
| Edge rails / fiducials | "Not necessary" | "Necessary" |
| Minimum package | "0402" | "01005" |
| Minimum IC pin spacing | "0.4mm" | "0.35mm" |
| Layer stackup | "Standard stack-up only" | "All stack-up" |

Both boards need Standard PCBA: Board A is assembled on both sides and has 0201 parts; Board B is 2.0 mm thick and has
its keyboard connector on the other side from the rest. Both are smaller than 70 x 70 mm, so the edge rails (and
fiducials on them) are added by JLCPCB on the order page.

## File formats

- Gerber / drill: https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-8 (layers, Protel
  extensions, subtract soldermask from silkscreen; drill origin absolute, mm, decimal, alternate oval-hole mode).
- BOM / CPL: https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad (BOM: Comment,
  Designator, Footprint, JLCPCB / LCSC part #; CPL: "Designator, Mid X, Mid Y, Rotation and Layer", millimetres).
- CPL position and bottom-side rotation: Bouni/kicad-jlcpcb-tools, fabrication.py (MIT). Rotation corrections:
  matthewlai/JLCKicadTools, jlc_kicad_tools/cpl_rotations_db.csv (GPL-3; values used, file not copied).

## Assembly fees (https://jlcpcb.com/help/article/pcb-assembly-price, fetched 2026-10-22)

| Fee | Economic PCBA | Standard PCBA |
|---|---|---|
| Setup / engineering | "$8.18" | "$25.56/Single-side", "$51.12/Double-side" |
| Stencil | "$1.53" | "$8.21/Single-side assembly", "$16.42/Double-side assembly" |
| Feeder loading | "$3.07 Extend." | "$1.53 Basic/Extend." (the page does not say per part type; counted per part type here) |
| SMT joints | "1–100,000 joints: $0.0016/joint" | "1–50,000 joints: $0.0016/joint" |
| Hand soldering | "$3.58 per order", manual assembly "$0.0164/joint" | same |

The PCB fabrication price itself (6 layers, impedance control, ENIG, epoxy-filled vias) comes from JLCPCB's quote at
upload; it is not estimated here.
