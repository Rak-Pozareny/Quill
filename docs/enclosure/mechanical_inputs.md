# Enclosure inputs: dimensions from the boards and parts

Reference data for the shell design, taken 2026-11-09 from the current board files (`hw/board_a`, `hw/board_b`,
the state ordered in `fab/`), the height check (`tools/heights.py`) and the part documents in the project. Nothing here
is a shell decision; those go in `ENCLOSURE.md`. Values marked **UNVERIFIED** are not published by the maker and must
be measured or asked for.

3D models: `fab/board_a/cm5_carrier.step` and `fab/board_b/q20_keyboard.step` (library models, plus datasheet-size
boxes for parts without one; the Orange Pi CM5 is a box model).

## Coordinates

- **Board coordinates:** mm, origin at the board's top-left corner as drawn, x to the right, y down, seen from the top
  face. (KiCad's own coordinates are these + 100.)
- **How Board A sits in the device** (as placed at checkpoint 3; can still be discussed): behind the display, top face
  (CM5 side) toward the display, turned 180 degrees, so the board's **bottom edge (USB-A) is the device's top**.
  Seen from the front:
  - board bottom edge (y 65) = device **top**
  - board left edge (x 0) = device **right** side
  - board right edge (x 95) = device **left** side
  - board top edge (y 0) = toward the **keyboard** (battery, keyboard cable)
  - device position from the board's top-left corner as seen from the front: x' = 95 - x, y' = 65 - y.

## Board A (CM5 carrier)

- **Outline:** 95.0 x 65.0 mm, corners R 1.0, **1.2 mm** thick (6 layers).
- **Two USB-A cutouts** in the bottom edge: x 54.85-69.75 and 73.05-87.95 (14.9 mm wide, 2.5 mm deep, then 14.4 mm
  wide to the edge, 8.28 mm deep from the edge in all).
- **Fixing holes:** 4 x M2, 2.2 mm plated, 4.4 mm pad, at (3.5, 3.5), (3.5, 61.5), (91.5, 3.5), (92.0, 61.5).
- **CM5 module:** 40 x 55 mm, centred at (32.5, 36.8) on the top face (x 12.5-52.5, y 9.3-64.3), held by 4 x M2.5
  screws into SMT standoffs at (16.0, 12.8), (49.0, 12.8), (16.0, 60.8), (49.0, 60.8). Its top is about **4.6 mm**
  above the board: **UNVERIFIED** (no Orange Pi 3D model; box model 1.5 stack + 1.6 PCB + 1.5 parts). Heat-spreader
  zone over it on User.2.
- **LTE modem (bottom face):** M.2 3042 socket J501 under the CM5, the 30 x 42 mm EM060K-GL runs toward the bottom
  edge, screwed into the standoff H501 at (34.5, 57.2). Its antenna connectors are on the module itself.

### Features at the edges

| Board edge (device side) | Part | Board position | Device position (from the front) | Note |
|---|---|---|---|---|
| bottom (device **top**) | USB-A J401 | centre x 62.3 | x' 32.7 | mouth front **3.0 mm past the edge**, flange 1.5 mm past it (HOAUC drawing); wall goes there |
| bottom (device top) | USB-A J402 | centre x 80.5 | x' 14.5 | as J401 |
| left (device **right**) | USB-C J101 | y 8.0-17.0 | y' 48.0-57.0 | shell front 0.46 mm past the edge; 3.26 mm tall |
| left (device right) | front-camera connector J705 | y 30.0 | y' 35.0 | cable leaves the edge; camera placed by the shell |
| left (device right) | rear-camera connector J704 | y 46.5 | y' 18.5 | as J705 |
| left (device right), bottom face | speaker sockets J801 / J802 | y 48.0 / 55.0 | y' 17.0 / 10.0 | JST-SH, cable to the speakers |
| right (device **left**) | nano-SIM J502 | y 8.6-20.9 | y' 44.1-56.4 | card slot 0.6 mm inside the edge |
| right (device left) | microSD J901 | y 23.1-36.9 | y' 28.1-41.9 | body front 0.4 mm inside the edge |
| right (device left) | POWER SW301 | y 41.5 | y' 23.5 | Alps SKRTLAE010 side-push, actuator at the edge, 3.3 mm tall |
| right (device left) | VOL+ SW302 | y 48.0 | y' 17.0 | as SW301 |
| right (device left) | VOL- SW303 | y 54.5 | y' 10.5 | as SW301. From the device top: VOL-, VOL+, POWER (key codes can be swapped in software) |
| top (toward the **keyboard**) | battery J102 | x 54-76 | x' 19-41 | mating face 0.4 mm inside the edge, 5.9 mm tall |
| top (toward the keyboard) | keyboard FFC J1001 | x 47.0 | x' 48.0 | 12P 0.5 mm FFC to Board B |
| top (toward the keyboard) | digitizer FFC J703 (reserved) | x 33.0 | x' 62.0 | future EMR digitizer |
| top face, inboard | display FPC J701 / touch FPC J702 | (55.0, 23.0) / (55.0, 43.85) | | tails enter from the board's right edge (device left), about 31.5 mm run over SIM / microSD. J702 moved from y 38.5 on 2026-11-10 (D118, board thread): the tails' centrelines are 20.85 mm apart on DisplayModule's CAD drawing |
| bottom face | Wi-Fi u.FL J601 / J602 | (13.6, 42.3) / (7.3, 42.3) | | antenna cables to the shell's antennas |

### Inside, needing light or access

| Part | Board position | Side | Note |
|---|---|---|---|
| status LED D302, LTE LED D501 | (89.0, 40.0), (87.0, 40.0) | top | beside the power button; a light pipe to the device's left side or front |
| RESET / MASKROM / RECOVERY SW304-306 (TS-1088, top push) | SW304 (57.2, 36.25) between the two display tails (D118); SW305 / SW306 (68.0 / 75.0, 47.0) | top | under the display: reachable only with the display off, or through a hole |
| EEPROM programming pads TP101-TP104 | around (75.8-79.5, 2.1-5.9) | top and bottom | one-time programming |
| debug console TP301 / TP302 / TP303 | (56.2, 45.0) / (53.4, 46.2) / (51.3, 49.0) | bottom | 1.5 Mbaud console; useful to reach with the back open |
| **microphone sound port** (U803 Knowles SPH0641LU4H-1, bottom-port, on the top face, D18) | hole 0.50 mm at (82.50, 47.77) | opens on the **bottom face** | seen from the front: x' 12.5, y' 17.2 (near the device's left side, by the power button). The back shell needs a sound hole or channel here, best sealed to the board with a small gasket. Charger FET Q103's body is 0.6 mm from the hole (pad 1.8 mm), so the gasket must be small (about 2 mm outside) or shaped round it |

### Heights (above the top face / below the bottom face)

| Top face | mm | Bottom face | mm |
|---|---|---|---|
| J102 battery connector | 5.90 | M.2 socket + EM060K-GL | 3.55 |
| CM5 module (UNVERIFIED) | 4.60 | SRP7028A inductors L101 / L201 | 3.00 |
| USB-A J401 / J402 | 4.33 (sinks 1.69 below the bottom face in the cutout) | JST-SH speaker sockets | 2.96 |
| side buttons SW301-303 | 3.30 | L203 / L204 | 2.00 |
| USB-C J101 | 3.26 | C504 220 uF | 1.90 |
| everything else | <= 2.0 | | |

Stack: 5.90 + 1.20 + 3.55 = **10.65 mm**; 9.35 mm without J102.

## Board B (Q20 keyboard)

- **Outline:** 74.0 x 53.1 mm, **2.0 mm** thick. Top corners R 3.1; bottom corners R 14 (copied from BBQ20KBD).
- **Holes:** 2 x M2.5, 2.7 mm unplated, at (70.9, 3.1) and (11.4, 49.3).
- **Cut-outs (from BBQ20KBD):** slot x 5.5-9.2, y 14.7-29.4; slot x 5.8-17.0, y 7.5-11.5; round 2.0 mm at
  (20.2, 48.1).
- **Keyboard connector J201** (Hirose BM20B, front face, the only front part) at (12.0, 22.2). Carrier FFC J101 on the
  back face at (37.0, 6.4), cable leaving the top edge.
- **Heights:** front 0.80 mm (J201); back 2.16 mm (SOIC-8 flash), FFC connector 2.0. Stack 4.96 mm.
- **The Q20 keyboard itself:** outline and height not in the project files. **Measure it** (or take it from a Q20 /
  BlackBerry Classic teardown drawing).

## Parts that are not on the boards

| Part | Size | Source | Note |
|---|---|---|---|
| Display DMKDI0400S0CA | module **84.0 x 85.99 x 3.76 mm** (lens O.D.; module O.D. 77.0 x 80.0); active area **71.93 x 71.93 mm** (720 x 0.0999 mm pixel pitch), 254 ppi; 50 g | DisplayModule spec V1.0.0; CAD drawing received 2026-11-10 (`research/dl/panel/DMKDI0400S0CA_drawing_2026-11-10.dwg`) | FPC edge toward the device's left side (board right edge). From the CAD drawing, measured from the lens edge with the tail stretched: **30P tail 41.30 +- 0.5 mm**, centred on the lens (15.50 wide at the end, T-bar 12.40 deep next to the panel, 28.91 stem); **8P touch tail 55.90 +- 0.5 mm**, 4.5 wide, its centreline 21.15 mm from the lens's left edge (front view), i.e. 20.85 mm from the 30P centreline. Bend: not within 1.0 mm of the panel edge; the folded T-bar lies on the back up to the drawn positioning line. Pin 1 of both tails is at the right with the glass facing you and the tail hanging down |
| Battery | about **8 x 65 x 85 mm**, 1S 5000 mAh | your choice at checkpoint 1 / 2 | assumed beside Board A beyond its top edge (85 along the board's width), 3 mm gap; harness <= 80 mm, 24 AWG |
| Rear camera (Radxa Camera 13M 214) | **32 x 32 mm board, 9.5 mm deep** (lens block 8.5 x 8.5 x 6.38 at the centre + 1.6 board + parts < 1.5 on the back); 4 holes 28 x 28 apart; 31P connector on the **lens side** at one edge | Radxa product brief RAD-DOC-0142 p. 4 | placement: ENCLOSURE.md (E3, behind Board A). Cable 150 mm, 31P 0.3 mm. FOV 66.2 x 51.6 degrees (78.4 diagonal) |
| Front camera (Radxa Camera 8M 219) | **not in the project files** | | measure, or find Radxa's drawing. Cable 31P 0.3 mm to 15P 1.0 mm, 150 mm |
| Speakers | to choose (2 x 4-8 ohm micro-speakers, JST SHR-02V-S plug) | | size and acoustic volume set by the shell |
| Wi-Fi / BT antennas | to choose: 2 x dual-band 2.4 / 5 GHz, u.FL (MHF1) | | need a non-metal window in the shell |
| LTE antennas | to choose, on the EM060K-GL's own connectors (Quectel EM060K HD ch. 5) | | main + diversity (+ GNSS); need a non-metal window, spaced from the Wi-Fi ones |
| CM5 heat spreader | thermal pad + aluminium plate from the module top to the display frame, over 40 x 55 mm | brief | a typical 0.5 mm pad + 1.0 mm plate puts the display back about 6.1 mm above the board, above J102 (5.9) |
| Board A to Board B cable | 12P 0.5 mm FFC, type B (contacts on opposite sides), about 50 mm | CHECKPOINT3 section 3 | length to be fixed from the shell; type A if folded back on itself |

## Size estimates made earlier (checkpoint 1, section 5.12)

Not a design, only the rough numbers the board was planned against:
- front face about **95 x 150 mm**: display (86) above the keyboard; Board A (65) + 3 mm gap + battery (65) behind,
  about 133 mm long;
- depth about **15 mm**: display 3.76 + about 6.1 to the board top (CM5 + spreader) + board 1.2 + bottom parts 3.55
  + back wall;
- the board (95 mm plus about 3 mm of USB-A and walls) sets the width; the display module is 84 mm wide.

## To measure or ask for

- Orange Pi CM5 part heights (module top, parts over the M.2 standoff H501): Orange Pi, or measure a module.
- Display: full outline drawing: received 2026-11-10 (CAD, see the display row).
- Q20 keyboard outline and height.
- Front camera module size.
- Speakers, antennas: to be chosen with the shell.
