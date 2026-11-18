# Boards and order: where things stand

Status 2026-11-11. This file covers the electronics and the JLCPCB order only. The enclosure (shell) is discussed
separately in `docs/enclosure/`. The full detail stays where it was: `REVIEW.md` (review report),
`docs/DECISIONS.md` (every decision with its reason), `fab/board_a/ORDER.md` and `fab/board_b/ORDER.md` (what to
upload and the options to select).

## Order

- **Board A, order 13909286A-Y4: cancelled by JLCPCB** (reported 2026-11-09). To be re-ordered with the new files.
- **New files, 2026-11-11 (D118-D120), ready to upload:** `fab/board_a/cm5_carrier_gerber.zip` (with the impedance
  form and drawing inside), `BOM.csv`, `CPL.csv`. The display / touch connectors now follow DisplayModule's drawing
  (pins mirrored, J702 moved), and the board was routed again in full, with the rear-camera clock fix (D119) and the
  clean-ups found on the way (D120). Checks on these files: ERC 0, DRC 0 errors / 0 unconnected, parity 0, joints
  0 / 0 / 0, Gerber check pass (`GERBER_CHECK.txt`); 3 skew warnings, all explained (below). Copy:
  `archive/d118_d120_2026-11-11/`. The D116 files (pin 1 wrong) are in `archive/d116_2026-11-07/`: do not upload
  those.
- **Re-order placed (2026-11-11). JLCPCB's CAM question (2026-11-15): traces too close to the outline for a V-cut
  rail joint (they need 0.4 mm).** Answer A (mouse bites), D122: four signal traces run 0.255 mm inside the long edge
  opposite the USB-A ports and a GND via row 0.30 mm inside every edge; the board was laid out to the routed-edge
  rule (0.2 mm). Ask for the holes outside the outline and the tabs on that edge near the corners. On delivery: cut
  the tabs, file the nubs flush with the outline, not past it. JLCPCB asked (2026-11-17) whether point 2 meant a file change: no, proceed with the existing files; the tab placement is shown in `fab/board_a/jlc_reply_mouse_bite_tabs.png`.
- **Production file (Y5), 2026-11-18: checked against ours, fine to confirm** (`tools/jlc_prod_check/`): copper, holes, silkscreen and mask as ours apart from standard CAM changes (etch compensation, unused inner pads removed); mouse-bite tabs within 10 mm of each corner, nearest copper GND at 0.21 mm. Order data: **purple** solder mask (ORDER.md said green; JLCPCB's bridge minimum is the same 0.10 mm for purple). **SW304 / SW305 / SW306 (RESET / MASKROM / RECOVERY, C455278) are not assembled** in the placement preview (JLCPCB's part page showed 0 remaining): hand-solder them after delivery (C455278 from LCSC, or C&K PTS820J20MSMTR-LFS from DigiKey, CKN10505CT-ND: same 3.9 x 2.9 x 2.0 mm body, its two J terminals (4.4 mm tip to tip, 1.0 wide) land inside our 1.05 x 2.0 mm pads at 4.45 mm, checked against C&K's drawing 2026-11-18; not a 'P' version, those have pegs and the board has no holes for them); until then shorting a switch's pads with tweezers does the same.
- **Board B:** ready to upload (`fab/board_b/`).

## Waiting on

- **DisplayModule answered on 2026-11-10** (all points now handled on the board; the init sequence is software) (reply and attachments in `research/dl/panel/`:
  `displaymodule_reply_2026-11-10.md`, `DMKDI0400S0CA_drawing_2026-11-10.dwg`,
  `DMKDI0400S0CA_ST7703_init_4lane_V1.1.txt`). Against the board:
  1. **pin 1 on both tails: the board has it the wrong way round (read 2026-11-10).** The DWG (read with LibreDWG
     0.13.3 from the AUR, installed by the user, then ezdxf) labels the contacts in the front view, glass facing you,
     tails hanging down: 30P "30" at the left end, "1" at the right; 8P "8" left, "1" right. The rear view shows the
     mirror image. Renders: `research/dl/panel/DMKDI0400S0CA_drawing_tails_front.png` / `_rear.png`. The board
     assumed pin 1 at the left (`docs/footprint_audit.md`): J701 pad 1 at board y 30.25, pad 30 at y 15.75; with the
     FPC edge at the board's right edge, the panel's right side is the board's -y side, so the tail brings pin 1 to
     the small-y end. Both connectors are mirrored relative to the tails. Not fixable in software: the pin field is
     not symmetric (the clock pair, power and GND would land on other pins).
     **Also from the drawing:** tail centrelines are 20.85 mm apart (30P centred on the 84.0 glass, 8P centre 21.15 mm
     from the glass's left edge as seen from the front); J701 and J702 are 15.5 mm apart. 30P tail 41.30 +- 0.5 mm and
     8P 55.90 +- 0.5 mm past the panel edge (estimate was 43-47 / 58-63). With the panel centred in the shell model
     (FPC edge 4.75 mm in from the board edge) the 30P needs about 4.7 fold + 31.5 run + 3 in the connector = 39-40
     mm: fits, 1-2 mm spare. With the FPC edge at the board edge it would not.
     **Done 2026-11-11 (D118):** J701 / J702 mapped mirrored (pad k = panel pin 31 - k / 9 - k), J702 moved to the
     drawing's spacing (y 38.5 -> 43.85), SW304 and TP305 moved, Board A routed again in full; DSI lanes matched
     within 0.10 mm. Not checked against a real panel (none in hand): the fallback meter check below still applies
     when one arrives.
  2. pin 7 = MIPI_D0N, pin 8 = MIPI_D0P: **matches the board** (`gen/board_a_main.py`, panel map).
  3. full outline with tail lengths, widths, bend position: in the DWG (not read yet; also feeds `docs/enclosure/`).
  4. init sequence (4 lanes, VCC 3.3 V, IOVCC 1.8 V: matches LCD_VCI / LCD_IOVCC); timings HS 4 / HBP 40 / HFP 10,
     VS 4 / VBP 20 / VFP 8, about 35 MHz pixel clock, 224 Mbit/s per lane, 60 Hz. Reset: low >= 10 us, >= 15 ms
     before the first command, no Sleep Out (0x11) within 120 ms of the release (their file waits 120 ms before
     the first command). Software only (GPIO3_A4); goes into the device tree.
  5. backlight 40 mA for the whole module (two strings of six in parallel), "40 mA or below": **matches** the
     TPS61169 setting (5.1 ohm, 204 mV typ = 40 mA). Spread: VREF 188-220 mV (TI SNVSA40B) and 1 % resistor give
     36.5-43.6 mA at 100 % PWM; the spec's lifetime note says above 40 mA shortens LED life. Option: cap the PWM
     at 90 % in the device tree (no hardware change), or 5.6 ohm (36.4 mA typ, at most 39.7 mA; BOM change only).
- Fallback for 1 if the panel is in hand: the meter check in `docs/footprint_audit.md`.

## Before the re-order

- **U101 (TPS25751DREFR, C30169739):** JLCPCB had 2 on 2026-11-07, exactly the 2 boards. Secure them (JLC parts
  inventory / pre-order) rather than wait.
- **J102:** settled on JLCPCB's side. It was taken off the could-not-place list before the cancellation, leaving only
  U601, which D114 fixed. Still look at J102 and U601 in the new order's placement preview.
- **USB-A against the bottom rail:** settled. The user reports (2026-11-11) that JLCPCB checked the J401 / J402
  overhang against their rail and said it is not a concern; their reply is not on file here. J401 / J402 and the
  board edge are unchanged in the new files, so the same answer applies (picture: `fab/board_a/jlc_query_usba_vs_rail.png`).
- In the placement preview: every part in `fab/board_a/ROTATIONS.md`, D101's rotation (ElecSuper part, D113).
- JLCPCB's impedance and CAM reviews run again on the new order.

## Recent decisions

- **D118 (2026-11-11):** display / touch connectors mirrored to the panel's tails, J702 moved 5.35 mm (tail
  spacing 20.85 mm), SW304 / TP305 moved, Board A routed again in full. DSI lanes 55.08-55.22 mm.
- **D119 (2026-11-11):** rear camera (CSI-A) clock fix, asked for with the re-route: the clock on L3 in connector B's
  order, D1 / D0 on L4 under it. Lanes now 0.14-2.82 mm (1-20 ps) short of the clock, was 4.65-6.30 mm (33-44 ps);
  D0 / D1 within the +-1.0 mm allowance, D2 / D3 not. Still test the rear camera at full lane rate at bring-up.
  Supersedes D117. The front camera (CSI-B) is unchanged: its clock was already two separate traces on D116.
- **D120 (2026-11-11):** found in the re-route and fixed in `gen/`: USB-C D+ / D- in the pair table (they had
  wandered to 17.8 / 9.1 mm; now 3.4 / 2.8 mm from the connector to the choke, 0.6 mm apart, D116 about 5 mm);
  J302.20 and J704.4's GND vias placed before the pairs (one was left unconnected, one sat 0.085 mm from the Wi-Fi
  U.FL pad); KBD_BOOT_N, left open by the router, routed on the finished board. KiCad's 3 skew warnings:
  USB3_LTE_TXC 0.297 mm (as since D103), PD_BC (the BC1.2 detection branch, as before), USBC (counted with its
  ESD / BC1.2 stubs, 4.0 mm; the signal path is 0.6 mm).

- **D116 (2026-11-07):** the first order's failure (track joints that only touched) checked again on the Gerbers
  themselves; 45 half-width gaps, one via that only touched and four pour slivers closed; `tools/gerber_check.py`
  now runs in every package build.
- **D117 (2026-11-07):** CSI-A (rear camera) clock skew: a re-route was tried and not adopted. The best full route
  found gains about 14 ps (lanes 3.6-4.6 mm short of the clock instead of 4.6-6.5 mm) at the cost of a full
  re-route. Test the rear camera at full lane rate at bring-up; a later revision needs room for two pairs to cross
  the clock beside J704.

## Open questions raised in conversation

- **Screen size (2026-11-09):** the user is worried the 4.0" panel is too small. Facts: 71.9 mm square active area,
  254 ppi, larger than the BlackBerry Classic's 3.5" with the same 720 x 720. Software scaling of about 1.4-1.5 gives
  desktop-size text at handheld distance (480 x 480 logical); room for content is the limit, not legibility.
  Offered, not started: a true-size printable test sheet (web pages and a terminal at scales 1.25 / 1.5 / 2). A
  different panel would mean a new connector, pin map and display routing, so it would have to be decided before
  the re-order. The mechanical side of this is in `docs/enclosure/`.

## Work offered, not started

- Display device tree from DisplayModule's init file (`research/dl/panel/DMKDI0400S0CA_ST7703_init_4lane_V1.1.txt`):
  the panel driver's init sequence and timings in `software/`, with the PWM capped at 90 % (40 mA backlight).

- TPS25751 configuration (TI's tool) and the EEPROM programming plan (CH341T, TP101-TP105). **Decided 2026-11-11:
  the user programs U102 (M24512) themselves after delivery**, not JLCPCB: JLCPCB only programs after assembly through
  an on-board interface (Standard PCBA, Advanced Options -> Function test, about $8 + $8 / hour), which would need the
  configuration finished before ordering, and our pads are on both sides with the board powered from J102. So no
  programming option on the order; the configuration and script can be done while the boards are made.
- A bring-up checklist: carrier powered without the module first, from a current-limited bench supply.
- `REVIEW.md` status refresh (Y4 cancelled, J102 settled).
- Keyboard firmware additions (asked about 2026-11-09). The stock i2c_puppet, read from its source, already gives
  pointer, click on press, right-click on press-and-hold, and Alt + swipe for arrow keys. The additions would be a
  scroll mode and a mapping for the four top buttons. Software only; flashed through BOOTSEL, which the CM5 can drive
  over BOOT# / RESET#.

## Bring-up notes kept from earlier

- EEPROM programming at 3.3 V: TP101 SDA (top), TP102 SCL (bottom), TP103 WP to GND (top), TP105 GND (bottom);
  board on its battery connector.
- Debug console: TP301 TX / TP302 RX / TP303 GND (bottom), 1.5 Mbaud.
- **Orange Pi CM5 received 2026-11-18:** label "OPi CM5 16G32G", RK3588S. Top silkscreen "OPi CM5 V1.?": the last
  digit is unreadable in the photos (looks like 1); V1.1 and V1.5 are the revisions checked (same plugs and holes),
  any other number to be checked. The DF40 pair is rated 30 mating cycles (Hirose): fit it once for bring-up, do not
  swap it around. The module's own TX / RX / 5V / GND pads on top: level not documented (UART2_M0 is 1.8 V on JP1),
  so no 3.3 V USB-serial on them; use TP301-303 on the carrier.
- Rear camera: test at full lane rate (D117, D119: skew now 1-20 ps). Wi-Fi crystal: frequency check. MAX17055 address: `i2cdetect`.
