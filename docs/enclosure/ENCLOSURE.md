# Enclosure (shell) design

Started 2026-11-09. This file holds the shell discussion: decisions, open questions and notes. Dimensions from the
boards and parts are in `mechanical_inputs.md` beside it. The electronics and the JLCPCB order are tracked separately
in `docs/board_status.md`.

Shell decisions are numbered **E1, E2, ...** so they don't mix with the board decisions (D1-D117 in
`docs/DECISIONS.md`).

## Fixed by the boards

The boards are about to be ordered, so the shell has to fit these unless we decide a board change is worth it (each
would delay the order):

- Board A 95 x 65 x 1.2 mm with its edge connectors where they are: USB-A x 2 at the device top, USB-C and the
  camera cables on the right, SIM, microSD and the three buttons on the left, battery and keyboard cable toward
  the keyboard.
- Board B 74 x 53.1 x 2.0 mm, the BBQ20KBD outline, under the Q20 keyboard.
- Component stack 10.65 mm on Board A (9.35 without the battery connector).

## Assumed so far, open to change without touching the boards

These come from checkpoints 1-3 and were never designed as a shell:

- Layout: display above the keyboard on the front; Board A behind the display, battery behind the keyboard, both
  in one shell, about 95 x 150 x 15 mm (rough estimate).
- Display FPC toward the device's left side (the board's J701 position requires the tail to come over the board's
  right edge).
- CM5 cooled by a heat spreader to the display frame.
- Cameras placed by the shell, on 150 mm cables from the device's right side.
- Board-to-board FFC about 50 mm.

## Open questions

1. ~~Overall form~~: decided, a FLIPOUT-style swivel (E1); thickness about 37 mm (E2, E4); pivot on the right (E5).
   Still open: the hinge hardware.
2. **Screen size:** the 4.0" panel's module is 84 mm wide and the board makes the device about 98 mm wide anyway, so
   there are about 11 mm of width a bigger panel could use without widening the device. A different panel means a
   board change (J701, display routing) before the re-order.
3. ~~How it's made~~: decided, 3D printing (E6). Still open: the home printer type and the service and material for
   the final shell.
4. **Opening and service:** how the back comes off; battery access; reaching the debug pads, the RESET / MASKROM /
   RECOVERY buttons (under the display), SIM and microSD.
5. **Display mounting:** frame, adhesive or bezel; how the FPC tails fold behind the panel.
6. **Keyboard mounting:** how the Q20 keyboard and Board B are held; the BBQ20KBD reference has its own approach.
7. **Thermal:** CM5 heat path (spreader to the display frame, or to the back / a metal part), LTE modem thermal pad.
8. **Antennas:** Wi-Fi x 2 and LTE x 2-3; where they sit, non-metal windows, spacing from the battery and the boards.
9. **Cameras:** rear decided (E3, E5); still open: the front camera's position (its size is not known yet), the lens
   windows, and what to do with the rear camera's 150 mm cable.
10. **Buttons and lights:** caps for the three side switches, light pipes for the two LEDs.
11. **Speakers and microphone:** speaker size, acoustic chambers and grilles. The board's microphone listens through
    a 0.5 mm hole to the back face of Board A (near the device's left side, about 17 mm below the board's USB-A edge).
    The back shell needs a sealed sound path there.
12. **Ports:** USB-A x 2 on the top edge (mouths 3.0 mm past the board edge), USB-C on the right.

## Decisions

| # | Decision | Reason |
|---|---|---|
| E1 | **Form: a swivel like the Motorola FLIPOUT.** Two halves of the same size. The screen half turns 90 degrees about a pivot near one corner to uncover the keyboard below the screen. (2026-11-09) | The user's choice. The square 720 x 720 panel loses nothing when the picture rotates 90 degrees. |
| E2 | **Internals unchanged, including the 85 x 65 x 8 mm 5000 mAh battery under Board B in the keyboard half; closed thickness about 34 mm accepted** ("3 cm feels appropriate"). (2026-11-09) | The user's choice: keep the boards and the battery as they are. Thinner options (5 mm or a narrow cell beside Board B, 27-31 mm) were set aside for now. |
| E3 | **Rear camera in the screen half, on its back: usable only with the device open.** (2026-11-09) | The user's choice: having to swivel the device open before taking a photo feels tactile. When closed the lens faces into the keyboard half and is protected. |
| E4 | **Keyboard half about 3 mm thicker (about 20.5 mm); closed thickness about 37 mm** (replaces the 34 mm of E2). (2026-11-09) | The user's choice of fix (a). The camera's closed position overlaps the battery's top edge by 3 mm in plan, and the channel needs 10.8 mm of depth there. With 20.5 mm the channel floor ends 9.7 mm above the back face, 0.5 mm above the battery (9.2). |
| E5 | **Pivot on the right (seen from the front), set in 22.5 mm from both edges; rear camera at the screen half's top-right, behind Board A next to J704; when closed it sits in a curved channel in the keyboard half's top-left corner.** (2026-11-09) | Recommended with the camera study and accepted with E4 ("yeah"). On the left, the camera would sit over the charger's power stage and the microphone port. Cost: battery harness about 120-150 mm (24 AWG keeps the 25 mV budget to 120 mm) and a longer FFC. |
| E6 | **Made by 3D printing:** mock-ups and test prints at home first, the final shell from a printing service. (2026-11-09) | The user's plan. Design rules for both: walls of at least 1.6 mm (four 0.4 mm FDM perimeters), 0.3-0.5 mm clearance on moving fits, heat-set brass inserts for screws, and a metal pivot rather than a printed one. Check the service's own rules once it is chosen. |

## Notes

### 2026-11-09: Motorola FLIPOUT-style swivel (proposed by the user; adopted as E1 / E2)

The FLIPOUT (2010) is a 67 x 67 x 17 mm square phone, 120 g, 1170 mAh (Wikipedia, GSMArena, Smartprix). Its screen
half swivels 90 degrees about a corner to uncover a QWERTY keyboard below the screen.

- **Fits well:** the 720 x 720 panel is square, so the picture rotates with no loss when the screen half turns
  90 degrees. The open device puts the display above the keyboard, as the slab layout does.
- **Size of each half:** about 98 x 90 mm, set by Board A (95 mm) and the display module (84 x 86).
- **Thickness, rough:**
  - Screen half: display 3.76 + 6.1 to the board (CM5 4.6 UNVERIFIED + spreader) + board 1.2 + 3.55 underneath
    + back wall about 1.2 = about **16 mm**.
  - Keyboard half: keyboard (height not measured, about 3 assumed) + Board B 4.96 + battery 8 + back wall about
    1.2 = about **17 mm**.
  - Closed: about **33 mm**, roughly twice the FLIPOUT and twice a slab built from the same parts (about 16-17).
    A 5 mm battery of the same outline saves 3 mm, at roughly 3000 mAh instead of 5000 (estimate).
- **Closed thickness by battery option** (estimate; capacities scaled by volume from 5000 mAh for 85 x 65 x 8):

  | Battery | Where | Keyboard half | Closed |
  |---|---|---|---|
  | 85 x 65 x 8 (5000 mAh) | under Board B | about 17.5 | **about 34 mm** |
  | 85 x 65 x 5 (about 3000 mAh) | under Board B | about 14.5 | about 31 mm |
  | 85 x 33 x 8 (about 2500 mAh) | beside Board B, in the 37 mm of the keyboard half the screen half covers when open | about 10-11 | about 27-28 mm |

  Screen half about 16, gap about 0.5. The keyboard's own height (3 mm assumed) and the CM5 height are not
  measured. A smaller cell must still deliver the board's worst case (9.8 A, about 4C for 2500 mAh) or the load must
  be limited.
- **The battery cannot go in the screen half:** Board A (65 mm) + battery (65 mm) is longer than the half.
- **Through the pivot:**
  - the 12P board-to-board FFC, as a loop or spiral;
  - the battery harness: 9 x 24 AWG wires, up to about 10 A worst case.
  - A 90-degree swing with a slack loop and fine-stranded silicone wire is mild, but fatigue and strain relief need
    care.
- **Rear camera:** when closed, the back of the screen half is covered. So the camera goes either in the keyboard
  half, with its FPC through the pivot, or on the screen half, where it works only when open. The rear module is
  32 x 32 x 9.5 mm: no 32 mm strip is left beside the battery (90 - 65 = 25) or beside Board A (86 - 65 = 21)
  unless a half grows.
- **Front camera:** the display leaves about 2 mm above / below it in a 90 mm half; the module size is not known
  yet.
- **Geometry of a corner swivel** (worked out 2026-11-09):
  - **The halves must be square** for their outlines to line up both closed and open, because the screen half is
    turned 90 degrees between the two states. Board A's 95 mm gives about **98 x 98 mm**. In the screen half that
    leaves about 12 mm beyond the 86 mm display in one direction (a candidate place for the front camera, whose
    size is not known yet).
  - A pivot set in by a from both edges makes the open halves overlap by 2a. With 98 mm halves and the keyboard's
    53 mm left uncovered, 2a = 45, so a is about 22.5 mm.
  - Open, Board A's cable edge (J102, J1001) faces the keyboard. Both connectors sit left of the device centre seen
    from the front (x' 19-48), so a pivot on the left would keep the battery harness and the FFC shortest. The
    camera (below) argues for the right instead.
- **Hinge:** a metal pivot (shaft, washers, detents at 0 and 90 degrees) set into the printed or machined halves;
  the screen half (display, Board A, CM5, modem) is the heavy one.

### 2026-11-09: rear camera in the screen half (E3), consequences worked out

Front-view coordinates, open, typing orientation: keyboard half x 0-98.5, y 0-98.5 (y down); pivot set in by
a = 22.5; the screen half open covers y -53.5 to 45.

- **Only the top band of the screen half is uncovered when open.** The halves overlap by 45 mm, so only the top
  53 mm of the screen half's back is free when open, and Board A fills that band across its full width. The camera
  must therefore sit **behind Board A**.
- **That makes a bump on the screen half's back of about 8-9 mm**, about 34 x 34 mm. The stack from the outside is
  a window of about 1 + lens 6.38 + camera PCB 1.6 + its parts 1.5 + 0.3 clearance + Board A's bottom parts under
  it (up to 3.55 over the modem), against 5.05 for the normal back.
- **The bump is housed in the keyboard half.** Closed, it sits in a recess in the keyboard half. While swivelling,
  it travels in an arc-shaped channel cut about 10 mm into the keyboard half's top band, the part the screen half
  covers when open, so the channel is never visible. Open, the bump sits in the step above the keyboard half and
  stays within the device's back plane (16 + 9 < 34).
  - For the channel to stay in the key-free band, **the camera must be on the same side as the pivot**. Its closed
    y equals its open x'.
  - The battery must then start at y >= about 31.5: 65 mm tall, y 31.5-96.5, which just fits.
- **Pivot side:**
  - **Left:** the camera would sit over the charger's power stage (Q101-Q104, L101; heat next to the sensor) and
    the microphone port at (82.5, 47.8).
  - **Right (recommended, not decided):** the camera sits at the screen half's top-right corner seen from the front.
    That is board x about 0-30, y about 33-65, right behind its own connector J704 (3.0, 46.5), over the Wi-Fi /
    audio corner. Bottom parts there: speaker sockets 2.96, u.FL J601 / J602 (their cables leave sideways), the
    modem's edge 3.55 at x >= 19.
- **Cost of a right-hand pivot:** the battery harness and the keyboard FFC run about 35-55 mm to the pivot instead
  of about 20-45. The harness grows from <= 80 mm (C2-1, a 25 mV drop budget at 10 A on 26 AWG) to roughly
  120-150 mm.
  - On 24 AWG (D111, 4 wires per polarity), 120 mm stays within that 25 mV budget.
  - 22 AWG (the terminal takes 22-26) allows about 190 mm but is stiffer in the pivot.
- **Camera module (Radxa drawing):**
  - Board 32 x 32 x 1.6 mm with four mounting holes 28 x 28 apart and two holes 20 mm apart beside the lens.
  - Lens block 8.5 x 8.5 x 6.38 mm at the centre.
  - The 31P cable connector is on the **lens side** at one edge, so the cable leaves on the outward face.
  - Parts under 1.5 mm on the back.
  - The standard cable is 150 mm, far longer than needed here, so the excess has to be folded or a shorter cable
    found.

### 2026-11-09: the camera channel checked (`tools/enclosure_swivel.py`, picture `img/camera_channel.png`)

The user asked whether the camera can slide into and out of a cut-out in the keyboard half, making the device
thicker if needed. Yes: that is the channel described above. Computed with the pivot on the right at (76, 22.5),
the camera (34 x 34 with margin) at the screen half's top-right when open:

- **Closed,** the camera lands in the keyboard half's **top-left** corner (x 2-36, y 1-35). The channel it sweeps
  while turning is about 42 x 35 mm in that corner and opens through the keyboard half's top edge. It touches no
  key and stays 40 mm from the pivot; the screen half hides it when open.
- **One clash:** the closed camera reaches y 35, and the battery's top edge is at y 32. Over that 3 mm strip the
  channel (bump 9.3 + 0.5 clearance + 1.0 floor = 10.8 deep) would reach 2.5 mm into the battery's 8 mm.
  The camera's closed y is the half's size minus its open x, so moving the pivot does not help.
- **Fixes:**
  - (a) the keyboard half about 3 mm thicker (closed about 37 mm);
  - (b) both halves about 102 x 102 mm instead of 98.5, thickness unchanged;
  - (c) a battery of at most 61.5 mm instead of 65 (conflicts with E2).

### 2026-11-09: block model v1 and the first printable mock-up

**Files**
- `model/enclosure_open.step`, `model/enclosure_closed.step`: open in any CAD program (FreeCAD, Fusion,
  Onshape). They hold both halves, the boards as part envelopes, the battery, display, keyboard placeholder, rear
  camera and pivot.
- `model/mockup_screen_half.stl` and `model/mockup_keyboard_half.stl`: for printing.
- `img/view_*.png`: pictures.
- To rebuild, first export the board envelopes with KiCad's Python: `python3 tools/board_envelopes.py
  hw/board_a/cm5_carrier.kicad_pcb docs/enclosure/model/board_a_envelope.json`, and the same for board_b. Then run
  `tools/enclosure_model.py OUT_DIR` (needs build123d, shapely, numpy, pillow). All parameters are at the top of
  that script.

**What the model checks**
- **Size:** open 98.5 x 152 x 37.1 mm; closed 98.5 x 98.5 x 37.1 mm.
- **Clearances (all zero overlap):**
  - closed, the camera bump is clear of the keyboard half;
  - the camera is clear of Board A's parts;
  - the display is clear of Board A's parts. The tallest, J102 at 5.9 mm, ends 0.19 mm below the display's back.
    That is tight, and the CM5 height under the heat spreader is UNVERIFIED.

**What it is not**
- The halves are solid blocks: no walls, bosses, clips, cable paths or antenna windows yet.
- The keyboard is a 74 x 53.1 x 3 placeholder (not measured), and the CM5 is a 4.6 mm box (UNVERIFIED).
- There is no front camera.
- The display sits flush with the front; no bezel lip is designed.
- The pivot is an M4 through-bolt. That is for the mock-up only: the real pivot must stay blind on the screen side,
  because the display covers that spot.
- **Known point to rework:** closed, the part of the channel the bump does not fill is open at the top edge, a
  notch of about 8 x 10 mm.

**Printing the mock-up**
- **Orientation:** the files are already oriented. The screen half prints front face down, the keyboard half back
  face down. No supports needed.
- **Settings:** about 0.2 mm layers, 3-4 walls, 10-20 % infill, PLA or PETG.
- **Hardware:** an M4 x 30 socket-head bolt from the back of the keyboard half (7.2 mm counterbore), an M4 nut in the
  hex pocket on the screen half's front, and one M4 washer between the halves. The washer makes the gap about 0.8 mm
  instead of 0.5; the bump keeps 1.3 mm of depth clearance.
- **What to try:**
  - how it feels in the hand and how thick it is;
  - the swivel, and the bump running through its channel;
  - typing reach over the grooved keyboard area;
  - where the ports and buttons fall: recesses on the sides (USB-A x 2 on top; USB-C right; SIM, microSD, POWER,
    VOL+, VOL- left; open positions).

