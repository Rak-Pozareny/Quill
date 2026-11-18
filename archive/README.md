# Archive: snapshots from before git

The project went into git on 2026-11-18. Before that, each milestone was copied here by hand; changes made between
two snapshots were not kept. This folder is not in git (it is large and never changes), apart from this file.

| Folder | State |
|---|---|
| `radxa_cm5_2026-10-22/` | The complete Radxa CM5 version of Board A, before the switch to the Orange Pi CM5 (D85): sources, KiCad project, fab package, docs. |
| `y4_order_2026-11-06/` | Order Y4 (cancelled: U601 AP6275P land pattern wrong, D114): KiCad board, fab package, generators, DECISIONS.md, REVIEW.md, and JLCPCB's production file `cm5_carrier_gerber_Y4_PRODUCTION_FILE.zip`. |
| `pre_d116_2026-11-07/` | After the U601 fix, before the joint / sliver fixes of D116: board and Gerbers. |
| `d116_2026-11-07/` | After D116: board, Gerbers, BOM, CPL, ORDER.md. **Display pin 1 reversed: never upload.** |
| `pre_d118_2026-11-10/` | Same board and Gerbers as `d116_2026-11-07/`, with the full fab folder and generators, kept before the re-route. |
| `d118_d120_2026-11-11/` | The re-order (Y5), identical to `hw/board_a/` and `fab/board_a/` in the first git commit, with JLCPCB's production file `cm5_carrier_gerber_Y5_PRODUCTION_FILE.zip`. |
