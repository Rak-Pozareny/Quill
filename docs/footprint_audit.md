# Footprint audit, 2026-11-06

The 24 footprints `gen/footprints.py` generates, each compared with its source drawing, read again for this audit, after
JLCPCB's SMT review found the AP6275P land pattern wrong (D114). The check covers pad positions and sizes, which edge or
centre each dimension's extension lines point to, pin 1 and pin order, and the body outline. Changes: D115.

It does not cover the KiCad library footprints (resistors, capacitors, SOT-23, and so on), which are not generated here.

| Footprint | Parts | Source | Result |
|---|---|---|---|
| AMPAK_AP6275P | U601 | AP6275P datasheet sec. 6.1, 6.2 | **Was wrong, corrected (D114).** Now 14.375 x 12.375 between pad centres, 11.70 / 9.00 spans |
| GCT_SIM8066-6-1-14-01-A | J502 | GCT drawing, Recommended PCB Layout | **Small error, corrected.** The GND tabs were 12.05 apart (drawing 12.00) and the pegs 0.04 mm off. Contacts, peg x, keep-outs correct |
| SW_Alps_SKRTLAE010_JLC | SW301-303 | Alps C110293 p. 2-3 | Pads correct, with the documented changes for the 0.2 mm NPTH rule. **Keep-out and body outline corrected:** both were 0.15 mm off. A sliver of GND pour under SW303 lay in Alps's prohibited area |
| USB_A_HOAUC_HYCW236-USBA04-289B | J401, J402 | HOAUC drawing | Copper correct, with the documented 0.3 mm pad pull-back at the cutout. **3D model and notes corrected:** the mouth front is 3.02 mm past the board edge, not 2.4 |
| FPC_0.5mm_12P_BXCONN_FC-05A12P11H20 | J703, J1001 (A), J101 (B) | BXCONN drawing | Copper correct. **Body outline corrected:** 5.99 mm deep, drawn 5.38. The drawing does not number the pins (below) |
| FPC_0.5mm_30P_HDGC_0520-HX-30PWB | J701 | HDGC drawing, A = 14.50 for 30 pins | Correct. The drawing does not number the pins (below) |
| FPC_0.5mm_8P_XUNPU_FPC-05F-8PH15 | J702 | XUNPU drawing | Correct, pin 1 as marked on the drawing |
| Hirose_FH35C-31S-0.3SHW | J704, J705 | Hirose FH35C catalogue p. 3-4, Radxa CM5 IO board decal | Correct. Rows 2.875 apart, B 8.4, C 9, fitting pads at +-5.2. Pin 1 and the rows as on Radxa's board, relative to the cable side |
| OPi_CM5_DF40_JP1, JP2, JP3 | J301-J303 | Hirose DF40 catalogue p. 4; Orange Pi base board V1.2 top DXF; module V1.1 and V1.5 bottom DXF | Correct. 3.78 / 2.38 are land edges, B 19.6. Pins 1, 2, 99, 100 of all three land on Orange Pi's silkscreen labels; rows agree with the module's plugs to 0.006 mm |
| CM5_Standoff_SMT_M2.5_L1.5 | H301-H304 | YIYUAN SMTSO family table, M2.5 row | Correct. Hole 4.22, pad 6.2, positions within 0.001 mm of the DXF. The table is the family's: the file is C5301777's, not C5221850's own |
| M.2_SMT_Standoff_M2 | H501 | Sinhoo SMTSO2010CTJ drawing, YIYUAN table, M2 row | Correct. Hole 3.73, pad 6.2 |
| M.2_Key-B_HOAUC_HYCW11B | J501 | HOAUC drawing, Recommended PCB Layout | Correct. Rows 7.55 apart, holes 1.10 / 1.60, pin order as drawn. The support pads' y is not dimensioned: measured about 0.13 mm from the row's end, 0.155 in the footprint |
| Molex_Micro-Lock_Plus_505578-0971 | J102 | Molex 5055780001 rev C, 9-circuit row | Correct (A 22, B 16, C 20.53). JLCPCB's library model has the 8-circuit values |
| Texas_RHL0020A_VQFN-20 | U201 | TI TPS61088 datasheet, land pattern page | Correct. 5.3 / 4.3 are outer edges |
| Texas_DSJ0014A_VSON-14 | U203, U204 | TI TPS63020 datasheet, land pattern page | Correct. 2.8 is between pad centres |
| TI_VSON-CLIP-8 (CSD25404Q3) | Q105 | TI SLPS570 sec. 7.2 | Correct. 0.41 + 1.90 + 0.56 + 0.63 = 3.50 |
| TI_VSONP-8 (CSD17577Q3A) | Q101-Q104 | TI SLPS515A sec. 7.2 | Correct |
| Maxim_TDFN-10 | U104 | Maxim 90-100007 rev B, 21-100013 rev C | Correct. 2.45 is between pad centres |
| L_Sunlord_WPN4020 | L203, L204 | Sunlord WPN catalogue, land table | Correct (a 1.9, b 1.1, c 3.7) |
| L_Sunlord_WPN252012H | L601, L602 | Sunlord WPN catalogue, land table | Correct (a 0.8, b 0.85, c 2.0) |
| L_CMC_Murata_DLW21SN | L401 | Murata JEFL243C-0003V-01 sec. 16.7 | Correct (2.6, 0.8, 1.2) |
| Hirose_BM20B_0.8_-40DS-0.4V | J201 (B) | Hirose BM20 catalogue p. 3-4, BBQ20KBD layout | Copper correct. 2.6 / 1.76 / 1.1 are edges. All 40 pads within 0.032 mm of the reference board, same nets. Body outline 3.0 wide, the part is 2.3: a larger courtyard only, left as it is so Board B's files stay untouched |

## Not settled by these drawings

**Update 2026-11-10: settled by DisplayModule's CAD drawing, and the assumption below is WRONG for both tails.**
The DWG (`research/dl/panel/DMKDI0400S0CA_drawing_2026-11-10.dwg`, front view, glass facing you, tails hanging down)
labels 30P "30" at the left and "1" at the right, and 8P "8" at the left and "1" at the right. See
`docs/board_status.md` for the consequences and the fix.
**Update 2026-11-11 (D118): the board now follows the drawing.** The footprints are unchanged; the schematic maps the
connectors mirrored, J701 pad k = panel pin 31 - k, J702 pad k = panel pin 9 - k, so panel pin 1 is at J701's pad 30
(155.0, 115.75) and J702's pad 8 (155.0, 142.1; J702 moved to y 43.85 for the tails' 20.85 mm spacing). The meter
check below still applies when a panel is in hand, with the expected readings the right way round now: on the 30P
the two leftmost contacts (pins 30 / 29, GND) beep together; on the 8P the second from the right (pin 2, NC) reads
open and the second from the left (pin 7, RST) a diode drop. The original text follows for the record.

**Display and touch FPC pin direction: UNVERIFIED.** The panel's outline drawing (spec V1.0.0, sec. 3) lists the pins but does
not mark which end of either tail is pin 1, and its raster is too coarse to show a number if there is one. What the
drawing does show: the conductors are on the tail's front side. After the tail folds behind the panel they face the
board, as the bottom-contact XUNPU connector needs (the HDGC one has contacts on both sides).

The board assumes that, with the glass facing you and the tail hanging down, **pin 1 is at the left**:

- J701: pad 1 at (155.0, 130.25), pad 30 at (155.0, 115.75).
- J702: pad 1 at (155.0, 140.25), pad 8 at (155.0, 136.75).

A fold around the panel edge keeps each conductor's position along the edge, so the assumption is the whole of it. If it
is wrong, the pins reverse and the layout must change, so it should be settled before ordering.

Check on the unpowered panel with a meter, on the tail's contacts:

- **30P:** pins 29 and 30 are both GND and pins 1 and 2 are NC and LEDK. With the glass facing you and the tail down, the
  two rightmost contacts should beep together and the two leftmost should not. If it is the other way round, the
  assumption is wrong.
- **8P:** pins 1 and 8 are both GND, so that does not tell the ends apart. Pin 2 is NC and pin 7 is RST: on diode test
  against GND, the second contact from the left should read open and the second from the right should read a diode drop.

Or ask DisplayModule for a drawing that marks pin 1.

**BXCONN and HDGC pin numbers:** their drawings do not number the pins, so pin 1 is a convention of the footprint, which
matters only against what the cable connects to. J1001 to Board B J101 was worked out in CHECKPOINT3.md section 3. J703
is reserved for a digitizer not yet chosen.
