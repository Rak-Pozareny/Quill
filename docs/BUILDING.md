# Building and regenerating the hardware

How the design is produced from code, phase by phase, and how to run each step again. The project overview is in the
[README](../README.md); the documentation index is in [docs/README.md](README.md). Commands run from the repository root.

## Status

| Phase | State |
|---|---|
| 1. Research summary, block diagram, pin budget, power | **done**, see `docs/checkpoint1/CHECKPOINT1.md`; all questions answered (`docs/DECISIONS.md`) |
| 2. Schematics (Board A hierarchical, Board B separate) + ERC | **done**: `docs/checkpoint2/CHECKPOINT2.md`; ERC 0 errors on both boards |
| 3. Placement, mechanical, 3D renders, height check | **done, reviewed; revised after the review** (cameras, power-stage layout): `docs/checkpoint3/CHECKPOINT3.md` |
| 4. Routing + DRC + length matching | **done**: `docs/checkpoint4/CHECKPOINT4.md`; DRC 0 errors, 0 unconnected on both boards; length results and open points in sections 6-7 |
| 5. Fab outputs (Gerbers, BOM, CPL, ORDER.md) + REVIEW.md | **done**: `fab/board_a/`, `fab/board_b/` (each with `ORDER.md`), `docs/checkpoint5/CHECKPOINT5.md`, `REVIEW.md` |
| 6. Board A redesigned for the Orange Pi CM5 (the Radxa CM5 cannot be ordered) | **done**: `docs/opi/OPI_REDESIGN.md`, decisions D85-D116, package rebuilt in `fab/board_a/` on 2026-11-07 (D114: JLCPCB's SMT review found the AP6275P land pattern wrong; D116: the joints checked again on the Gerbers) (ERC 0, DRC 0 errors / 0 unconnected, parity 0, Gerber check pass; **not ready to order until JLCPCB has answered on J102's library model and the USB-A rail and the display pin direction is checked, `REVIEW.md` section 6**; U101: 2 in JLCPCB stock on 2026-11-07, enough for the 2 boards). The finished Radxa design: `archive/radxa_cm5_2026-10-22/` |
| 7. Linux device tree for Orange Pi's 6.1 images | **written**, untested on hardware: `software/README.md`. Display disabled until DisplayModule's panel data |

## Layout

```
docs/checkpoint1/     checkpoint 1 report, pin budget, power budget, parts shortlist, diagrams (SVG)
docs/checkpoint2/     checkpoint 2 report, schematic PDFs, BOM drafts (live JLC check), as-built CM5 pin map
docs/checkpoint3/     checkpoint 3 report, schematic PDFs, BOMs, placement reports, renders and plots (img/)
docs/checkpoint4/     checkpoint 4 report, DRC reports, length report, copper plots and renders (img/)
docs/opi/             Orange Pi CM5 redesign of Board A: OPI_REDESIGN.md, pin map (CSV), block diagram, power tree
docs/off_board_parts.md   everything plugged in or screwed on (CM5, modem, battery, display, cameras, cables)
docs/shopping_list_eu.md  where to buy those, delivered to the EU (sources, prices seen, caveats)
fab/board_a/, fab/board_b/   the JLCPCB order packages: Gerber zip, BOM.csv, CPL.csv, ORDER.md, PDFs, STEP, stack-up
REVIEW.md             final report: UNVERIFIED items, assumptions, what to review before ordering, cost, parts to buy
hw/board_a/           Board A KiCad project (generated - do not edit by hand)
hw/board_b/           Board B KiCad project (generated)
gen/                  generators: schematics, footprints, placement, routing (route_*.py, groute.c), tuning
tools/                scripts that produce everything in docs/ (re-runnable)
software/             Linux device tree for Board A on Orange Pi's 6.1 images, kernel options, build / check scripts
datasheets/           the datasheets, drawings and reference designs the boards rest on, by board; index in datasheets/README.md
                      (copied from research/dl by tools/datasheets.py, which also checks every BOM part has one)
research/             extracted text, image crops; dl/ holds the raw downloads (not in git: large, and code clones)
archive/              snapshots from before git (not in git, listed in archive/README.md);
                      archive/radxa_cm5_2026-10-22/ is the complete Radxa CM5 version of Board A
```

Version history: git, from 2026-11-18 (the state of the Y5 order). Earlier states are the snapshots in `archive/`.

## Re-generating the Orange Pi CM5 version of Board A

```
python3 -I tools/opi_pins.py         # Orange Pi pin definition PDF -> gen/data/opi_cm5_pins.json
python3 gen/footprints.py            # footprints, incl. the Orange Pi DF40 positions
python3 -I gen/build_a.py            # schematics + ERC + netlist check
python3 -I tools/opi_pinmap.py       # docs/opi/opi_cm5_pin_map.csv
python3 -I tools/make_diagrams.py    # docs/opi/block_diagram.svg, power_tree.svg
python3 gen/pcb_a.py                 # placement
python3 gen/route_a.py --out X       # routing (about 6 hours), then install X into hw/board_a and run tools/package.py a
python3 gen/art_a.py hw/board_a/cm5_carrier.kicad_pcb   # logo + hidden text (D106); tools/package.py a runs it too
GERBER_CHECK_PYTHON=VENV/bin/python python3 tools/package.py a   # VENV: a venv with shapely, for tools/gerber_check.py (D116)
python3 tools/pour_cuts.py hw/board_a/cm5_carrier.kicad_pcb LAYER:X:Y ...   # only if the Gerber check reports a pour sliver;
                                     # then tools/refill_pours.py and tools/package.py a again
```

The checkpoint 1-5 sections below describe the Radxa phase; their tools still run, on the Radxa data where they read it
(`tools/cp1_tables.py`, `tools/cm5_pinmap.py`).

## Re-generating checkpoint 1

```
python3 -I tools/cp1_tables.py      # pin budget, power budget, parts tables (CSV + markdown)
python3 -I tools/make_diagrams.py   # block_diagram.svg, power_tree.svg
python3 -I tools/cp1_build.py       # assembles docs/checkpoint1/CHECKPOINT1.md
python3 -I tools/jlc_search.py TPS25750 BQ25792     # live JLCPCB stock lookup
python3 -I tools/jlc_stackups.py 6 1.2 0.5 1        # JLCPCB 6-layer 1.2 mm stack-up templates
```

## Re-generating checkpoint 2

```
python3 -I gen/build_a.py            # Board A schematics -> hw/board_a, runs ERC + netlist comparison
python3 -I gen/build_b.py            # Board B schematics -> hw/board_b
python3 -I tools/passives.py -f hw/board_a/missing_passives.txt   # pick JLC parts for new passive values
python3 -I tools/bom.py hw/board_a cm5_carrier docs/checkpoint2/bom_board_a.csv   # BOM + live JLC check
python3 -I tools/cm5_pinmap.py       # as-built CM5 pin map
python3 -I tools/netreport.py hw/board_a cm5_carrier --pairs      # diff-pair polarity check
```

## Re-generating checkpoint 3

```
python3 gen/footprints.py            # project footprints (lib cm5h), 3D boxes, gen/data/fp_meta.json
python3 tools/fpcheck.py hw/board_a hw/board_a/cm5_carrier.net    # every pin has a pad and vice versa
python3 gen/pcb_a.py                 # Board A PCB: outline, stack-up, footprints + nets, placement (power stages: gen/stages.py)
python3 gen/pcb_b.py                 # Board B PCB
python3 tools/heights.py hw/board_a/cm5_carrier.kicad_pcb         # height check (tallest parts, stack)
python3 tools/placement_check.py hw/board_a/cm5_carrier.kicad_pcb # decoupling / switch-node / sensitive-net distances
python3 tools/placement_plot.py hw/board_a/cm5_carrier.kicad_pcb B out.png   # placement plot with references
sh tools/renders.sh docs/checkpoint3/img                            # 3D renders of both boards
```

## Re-generating checkpoint 4

The routing scripts start from the placed boards above (they remove any earlier routing) and write the routed board
in place. Board A's placement changed after checkpoint 3 (D59): run `gen/pcb_a.py` first. The grid router's C core is
compiled on first use (gcc) into `build/libgroute-<hash of gen/groute.c>.so`. Board A takes about 2.5-3 hours (most
of it the 0.025 mm local passes and the rip-up passes at the end), Board B about 8 minutes. Board A's result is not
bit-identical from run to run: everything before the grid router is, but two full runs of the same code
part ways in the grid router's second stage, so a re-run (or the two-step path below) gives a slightly different
routing, with a different handful of connections left for the rip-up passes. The likely cause is order: new tracks get
random IDs, KiCad stores and saves them in ID order, and the negotiation depends a little on the order it meets them in
(not tracked down further).

```
python3 gen/route_a.py               # Board A: rules, pours, pairs, tuning, trunks, GND fan-out, grid router, GND pours
python3 gen/route_a.py --out X --stop-after fanout   # ... or in two steps: everything before the grid router (~10 min)
python3 gen/route_a.py --out X --resume              #     then the grid router and the GND pours
python3 gen/route_a.py --finish      # a run that ended with connections open: the rip-up and clean-up stage again
                                     # (not every run reaches zero, even with it: see CHECKPOINT4.md section 5)
python3 gen/route_b.py               # Board B: GND fan-out, grid router, GND pours
kicad-cli pcb drc --format json -o docs/checkpoint4/drc_board_a.json hw/board_a/cm5_carrier.kicad_pcb
kicad-cli pcb drc --format json -o docs/checkpoint4/drc_board_b.json hw/board_b/q20_keyboard.kicad_pcb
python3 tools/length_report.py hw/board_a/cm5_carrier.kicad_pcb docs/checkpoint4/length_report.md
sh tools/copper_plots.sh hw/board_a/cm5_carrier.kicad_pcb docs/checkpoint4/img board_a
sh tools/copper_plots.sh hw/board_b/q20_keyboard.kicad_pcb docs/checkpoint4/img board_b F.Cu,B.Cu
sh tools/renders.sh docs/checkpoint4/img                            # 3D renders of the routed boards
```

## Re-generating checkpoint 5 (the order packages)

`tools/package.py` places the silkscreen references (`tools/silk.py`) and copies the schematic's fields and attributes to the footprints (`tools/sync_pcb.py`), both in place, then runs ERC, DRC with the schematic parity check, the fab files, the live JLCPCB check and price of every
BOM line, the schematic PDF, the STEP model and the stack-up on the files in `hw/`, and writes `fab/<board>/ORDER.md`
with the order options and the check results (a few minutes per board, most of it the live JLCPCB queries).

```
python3 tools/package.py a           # fab/board_a/: cm5_carrier_gerber.zip, BOM.csv, CPL.csv, ORDER.md, ...
python3 tools/package.py b           # fab/board_b/
python3 tools/fab.py BOARD.kicad_pcb OUTDIR NAME     # only the Gerber / drill zip, BOM.csv, CPL.csv, ROTATIONS.md
python3 -I tools/bom_cost.py fab/board_a/BOM.csv     # parts cost at live JLCPCB prices
```

## README images

```
python3 -I tools/media.py            # docs/media/: 3D renders of both boards, Board A's six copper layers
python3 -I tools/datasheets.py       # datasheets/ and its index, with the BOM coverage check
```
