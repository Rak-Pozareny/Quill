# Checking JLCPCB's production files against ours (2026-11-18, order 13909286A-Y5)

JLCPCB's "confirm production file" zip has their CAM output in `ok/` (jlccam Gerber, inches, arcs, clear polarity:
`tl l2 l3 l4 l5 bl` copper, `ts bs` mask, `to bo` silkscreen, `drl` holes, `ko` outline with the panel, `sk` plugged
vias, `qrt qrb` QR codes) and our upload in `YG/`. Extract it into its own directory and run these with
`python3 -I` from a Python that has shapely (they read our Gerbers from `fab/board_a/cm5_carrier_gerber.zip`, extracted).
Panel coordinates map to ours as x = 25.4 X + 100, y_gerber = 25.4 Y - 172 (`DX`, `DY` in `jlc_vs_ours.py`; Y5 panel:
5 mm rails top and bottom, 2 mm gap, board at panel y 7-72 mm). Check the offsets on a new panel first (outline in `ko`).

- `jlc_vs_ours.py JLC_LAYER OUR_GERBER OUR_EDGE_CUTS OUT`: copper inside the board, theirs only / ours only beyond
  compensation; round pieces counted by size (inner-layer pads they removed show as 'round 0.40').
- `widths.py JLC_LAYER OUR_GERBER`: every track of ours matched by centreline to theirs; width before -> after.
- `added_nets.py TOOLS_DIR JLC_LAYER OUR_GERBER OUR_EDGE_CUTS`: copper they added and the nets each piece touches
  (two nets = a short, unless at a net tie).
- `drills.py TOOLS_DIR JLC_OK_DIR OUR_GERBER_DIR`: hole counts by size, ours vs theirs; mouse-bite holes.

Result for Y5 (D122 follow-up, `docs/board_status.md`): every track present at its place; widths +0.0254 mm on the
outer layers, +0.020-0.035 mm inner (etch compensation, the 0.125 mm SD lines the most); unused inner via / pad
rings removed (1079 on each GND plane = every non-GND via); added copper only same-net slivers (four at NT101,
FG_CSN / GND, by design); holes 1:1 (drill sizes compensated), plus slot pre-drills, notch-corner reliefs and the
notch arcs drilled; silkscreen kept (text block identical), mask webs all kept, mask cleared 0.05 mm at the edge and
0.1 mm round non-plated holes; mouse-bite tabs within 10 mm of each corner, holes 0.45 mm reaching 0.09 mm into
the board, nearest copper GND at 0.21 mm.
