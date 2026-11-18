# Documentation

Where to find what. The project overview is in the [README](../README.md).

## Start here

| Document | What it is |
|---|---|
| [`DECISIONS.md`](DECISIONS.md) | the decision log: every design question and decision (Q1-Q10, C-items, D1-D122) with the alternatives, the reason and the sources |
| [`../REVIEW.md`](../REVIEW.md) | the pre-manufacture review: what is verified, what is assumed, what is still open, what an experienced engineer should check |
| [`board_status.md`](board_status.md) | where the boards and orders stand now, what is waiting on whom, bring-up notes |
| [`BUILDING.md`](BUILDING.md) | how the design is generated, phase by phase, and how to run each step again |

## The design, in the order it was made

| Document | Contents |
|---|---|
| [`checkpoint1/CHECKPOINT1.md`](checkpoint1/CHECKPOINT1.md) | research, block diagram, pin budget, power budget, parts shortlist |
| [`checkpoint2/CHECKPOINT2.md`](checkpoint2/CHECKPOINT2.md) | schematics of both boards, electrical-rule check |
| [`checkpoint3/CHECKPOINT3.md`](checkpoint3/CHECKPOINT3.md) | placement, mechanical fit, 3D renders, component height check |
| [`checkpoint4/CHECKPOINT4.md`](checkpoint4/CHECKPOINT4.md) | routing, stack-up and impedance, length matching, design-rule check |
| [`checkpoint5/CHECKPOINT5.md`](checkpoint5/CHECKPOINT5.md) | manufacturing outputs |
| [`orange_pi_cm5_check.md`](orange_pi_cm5_check.md) | the Orange Pi CM5 checked pin by pin against the carrier, when the Radxa CM5 could not be bought |
| [`opi/OPI_REDESIGN.md`](opi/OPI_REDESIGN.md) | Board A redesigned for the Orange Pi CM5: changes, results, block diagram and power tree |
| [`opi/length_report.md`](opi/length_report.md) | every differential pair's length and skew against its target, with the source of each target |
| [`footprint_audit.md`](footprint_audit.md) | the 24 project footprints checked against their datasheet drawings |

## Manufacturing and verification

| Document | Contents |
|---|---|
| [`../fab/board_a/ORDER.md`](../fab/board_a/ORDER.md), [`../fab/board_b/ORDER.md`](../fab/board_b/ORDER.md) | what to upload, every option on the order page, and the checks run on exactly those files |
| [`../fab/board_a/STACKUP.md`](../fab/board_a/STACKUP.md), [`../fab/board_a/IMPEDANCE.md`](../fab/board_a/IMPEDANCE.md) | Board A's stack-up and controlled-impedance classes |
| [`../tools/jlc_prod_check/README.md`](../tools/jlc_prod_check/README.md) | the manufacturer's production files compared with ours before the order was confirmed |

## Parts, mechanics and software

| Document | Contents |
|---|---|
| [`off_board_parts.md`](off_board_parts.md) | everything that plugs in or screws on: compute module, modem, battery, display, cameras, cables |
| [`shopping_list_eu.md`](shopping_list_eu.md) | where those parts can be bought for delivery in the EU, with prices seen and caveats |
| [`../datasheets/README.md`](../datasheets/README.md) | index of the datasheets, drawings and reference designs, by board |
| [`enclosure/ENCLOSURE.md`](enclosure/ENCLOSURE.md), [`enclosure/mechanical_inputs.md`](enclosure/mechanical_inputs.md) | the enclosure concept and the dimensions it is built from |
| [`../software/README.md`](../software/README.md) | the Linux device tree for Board A on Orange Pi's images (written, not yet tested on hardware) |
| [`../archive/README.md`](../archive/README.md) | the snapshots kept before the project moved to git (not published) |
