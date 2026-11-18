# JLCPCB rigid PCB capabilities used for the design rules (fetched 2026-10-17)

Source: https://jlcpcb.com/capabilities/pcb-capabilities (multilayer values; 1 oz outer copper).

| Parameter | Value | Note |
|---|---|---|
| Min. trace width / spacing | 0.09 / 0.09 mm (3.5 / 3.5 mil) | "3 mil is acceptable in BGA fan-outs" |
| Min. via hole / diameter | 0.15 / 0.25 mm | preferred min. hole 0.2 mm; via >= hole + 0.1 (0.15 preferred) |
| Via-in-pad (filled, capped) | via 0.15-0.55 mm | default on 6 layers and above |
| Hole to hole, via | 0.2 mm | |
| Hole to hole, pad | 0.45 mm | |
| Via hole to track | 0.2 mm | |
| Pad to track | 0.1 mm | 0.09 mm locally at BGA pads |
| PTH to track | 0.28 mm min (0.35 recommended) | |
| NPTH to track | 0.2 mm | |
| Inner layer: via hole to copper / PTH hole to copper | 0.2 / 0.3 mm | |
| Copper to routed edge | >= 0.2 mm | V-cut 0.4 mm |
| PTH annular ring (1 oz) | >= 0.15 mm (0.2 recommended) | |
| Solder mask bridge | 0.10 mm (green, red, yellow, blue, purple); 0.13 mm (black, white) | colours re-checked 2026-10-23 |
| Solder mask expansion | 1:1 | keep >= 0.09 mm from opening to traces |
| Silkscreen line / text height / to pad | 0.15 mm / 1.0 mm / 0.15 mm | |
| Plated slot min. width | 0.35 mm (length >= 2 x width) | non-plated 1.0 mm |
| Impedance tolerance | +-10 % (+-5 % on request), 4 layers and up | |

## 2-layer values (Board B), same page

| Parameter | Value | Note |
|---|---|---|
| Min. trace width / spacing (1 oz) | 0.10 / 0.10 mm | 1-2 layers |
| Min. via hole / diameter | 0.15 / 0.25 mm | 0.1 / 0.2 only for <= 1 mm thickness |
| PTH annular ring (1 oz) | >= 0.25 mm recommended, 0.18 mm absolute minimum | re-checked 2026-10-18: the page labels this row "PTH annular ring"; vias have their own row ("Via diameter should be 0.1mm(0.15mm preferred) larger than Via hole size") |
| Hole to hole (via / pad), via to track, pad to track, PTH to track, NPTH to track, copper to edge | 0.2 / 0.45, 0.2, 0.1, 0.28, 0.2, 0.2 mm | as multilayer |
| Min. drill | 0.15 mm | |
