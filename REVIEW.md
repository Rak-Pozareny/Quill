# Review report: CM5 carrier (Board A, Orange Pi CM5) and Q20 keyboard board (Board B)

Status, 2026-11-11.
- **New Board A files, 2026-11-11 (D118-D120).** DisplayModule's drawing (2026-11-10) puts pin 1 of both panel tails at the other end from the board's assumption, so J701 / J702 are now mapped mirrored, J702 moved to the tails' 20.85 mm spacing (SW304 / TP305 moved with it), and the board was routed again in full. With that re-route:
  - the rear camera's clock fix you asked for (D119): its data lanes are now 0.14-2.82 mm (1-20 ps) short of the clock, against 4.65-6.30 mm (33-44 ps);
  - three things the re-route turned up, fixed in the generator (D120): the USB-C D+ / D- path (now 0.6 mm apart from the connector to the choke), two GND vias (one pin was left unconnected, one via sat too close to the Wi-Fi U.FL pad), and one boxed-in signal routed by hand on the finished board.
  - All checks pass on the new files in `fab/board_a/`. The D116 files have pin 1 the wrong way round: they are in `archive/d116_2026-11-07/` and must not be uploaded.
- **Board A** was redesigned for the **Orange Pi CM5**, because the Radxa CM5 could not be ordered (`docs/opi/OPI_REDESIGN.md`, decisions D85-D116). Its package is complete and passes every check on the final files, but it is **not ready to order** until the points in section 6 are settled with JLCPCB.
- **JLCPCB's SMT review stopped order Y4 (2026-11-06, D114):**
  - **U601 was my error.** The AP6275P's 14.375 / 12.375 mm dimensions run between pad centres; I had read them as outer edges, so all 50 pads sat 0.5625 mm too far in. Corrected, and the board routed again: the module moved 0.5625 mm north, 19 of 432 parts moved in all. `fab/board_a/` is therefore a new order; the files of order Y4 are in `archive/y4_order_2026-11-06/`.
  - **J102 is not changed.** Its pads follow Molex's drawing for 9 circuits; JLCPCB's library model measures as the 8-circuit part and has to be corrected by JLCPCB.
- **The first order's failure, checked again on the new files (2026-11-07, D116):** the Gerber zip was rebuilt as copper and every joint measured, the way a fab's CAM sees it. No joint only touched between tracks, but 45 track joints on 33 signal nets still had two ends up to half a width apart with nothing between them (down to 0.083 mm on 0.1 mm tracks): what D110's fix left, and what the board check then let through. One CHG_IN via only touched U101's pin 20, and four GND pour slivers (0.04-0.11 mm) remained. All closed: 131 short bridges, no track or via moved, and four small pour keep-outs. The board check now measures these joints properly and checks vias, and the package build runs the new Gerber check on the zip it writes (`fab/board_a/GERBER_CHECK.txt`: 0 shorts, 0 opens, no copper under 0.095 mm joining anything, 0 joints under 95 % that anything needs).
- **Device tree:** written for Orange Pi's Debian 12 / Ubuntu 22.04 images (Linux 6.1), in `software/` with build and install steps. The display stays disabled until DisplayModule supplies the panel's timings and init code (section 1).
- **Two pin errors found while writing it, both fixed on the board** (D104, D105):
  - The front camera's I2C pins belong to an I2C controller the module already uses. They are now driven as software I2C, so no board change.
  - JP1.75 is the module PMIC's SPI clock. The SD power-switch option that hung on it is removed.
- **JLCPCB's CAM stopped the first Board A order (2026-10-30):** track segments whose round ends only touched, on the inner layers and the top, with no real copper between them. KiCad counts touching copper as connected, so DRC had passed. Fixed (D110): 395 duplicate tracks removed and 153 such joints bridged at full width, the pairs' skew tuned again on the true lengths, and a new check in the package build that refuses any such joint or duplicate (made stricter, with a check of the Gerber zip itself, in D116). The Gerber zip now also holds an impedance drawing for the CAM engineers (`cm5_carrier-Impedance_Drawing.gbr`; the same as `cm5_carrier_impedance.pdf` and `IMPEDANCE.md` in `fab/board_a/`).
- **Outer-layer impedance fixed (2026-10-31, D112):** the GND pour on the top and bottom ran 0.09 mm from the controlled traces, which turns them into coplanar lines with a lower impedance than their widths were calculated for. The pour now keeps 0.30 mm from every controlled trace on the outer layers, so the Gerber zip of 2026-10-31 must be the one uploaded (BOM.csv / CPL.csv unchanged). JLCPCB's own impedance form is filled in `fab/board_a/cm5_carrier_impedance_control.xlsx` (15 rows: layer, reference layers, model, width / gap, target, a picture of where).
- **Stock (2026-11-07):** U101 (TPS25751DREFR) has **2** at JLCPCB (0 on 2026-11-06, 4 on 2026-10-31): exactly enough for the 2 assembled boards, so `ORDER.md` now reads "ready" on its own checks. That covers the files only; the points in section 6 still hold the order, and the 2 can go before the re-order (section 6). D101 is now ElecSuper's pin-compatible ESTVS2200DRVR (C42400188, 2871 in stock) in place of TI's TVS2200 (4 in stock) (D113); check its rotation in the placement preview.
- **Board B** is ready to upload. One change from the logic check of 2026-10-23: the keyboard's interrupt line to the CM5 now goes through an open-drain buffer (U104), because the CM5 end is a 1.8 V pin and the old BSS138 shifter would have pushed 3.3 V into it (D109).
- **Not right yet**, listed here and not hidden:
  - points with JLCPCB before the re-order: U101's stock and J102's library model (section 6; the USB-A rail is settled);
  - the display and touch FPC pin direction now comes from DisplayModule's drawing (D118), not from a panel: a meter check when one is in hand (section 6);
  - length matching on the rear camera link: much improved (D119), but two of its four lanes are still outside my +-1.0 mm allowance (section 3);
  - the module's mechanical heights, which Orange Pi does not publish (section 1);
  - the items an experienced engineer should review before money is spent.
- **The finished Radxa version** is in `archive/radxa_cm5_2026-10-22/`, should a Radxa CM5 become available.

What to upload is in `fab/board_a/` and `fab/board_b/`; each folder's `ORDER.md` lists the files, every option to
select on JLCPCB's order page, and the checks run on exactly those files. Every decision with its reason is in
`docs/DECISIONS.md`.

| | Board A, Orange Pi CM5 carrier | Board B, Q20 keyboard |
|---|---|---|
| Board | 6 layers, 1.2 mm, JLC06121H-3313A, impedance control, ENIG, epoxy-filled vias | 2 layers, 2.0 mm, ENIG |
| Size | 95.0 x 65.0 mm | 74.0 x 53.1 mm |
| ERC | 0 errors, 0 warnings | 0 errors, 0 warnings |
| DRC (zones refilled) | 0 errors, 0 unconnected; 3 skew warnings (USB3_LTE_TXC, PD_BC, USBC; section 3); 7 by-design findings excluded; track joints, via joints and duplicate copper 0 / 0 / 0; Gerber check of the zip: pass (D116, D118-D120) | 0 errors, 0 warnings, 0 unconnected |
| Schematic / board parity | 0 errors, 0 warnings | 0 errors, 0 warnings |
| BOM | 130 lines, 379 parts placed (3 do-not-fit); every LCSC number found, MPN matching, stock for 5 boards on every line (checked 2026-10-23) | 17 lines, 58 parts, every LCSC number found, MPN matching, in stock for 5 boards (checked 2026-10-23) |
| Assembly | Standard PCBA, both sides | Standard PCBA, both sides (one part on the top) |

---

## 1. UNVERIFIED items

No footprint, pin or part number in the design is guessed:
- Every footprint and pin was checked against its datasheet or reference design.
- The Orange Pi CM5's pins and connector positions come from Orange Pi's own files: the interface PIN definition V1.1 (2025), the base-board schematics, the base-board and module DXFs (`research/dl/orangepi/`).

What is left are values that only a datasheet we could not get, the vendor, or the first board can settle.

| Item | Where | What is assumed | Settled by |
|---|---|---|---|
| **Orange Pi CM5 part heights** | Board A, mechanics | the module's underside parts over the M.2 standoff H501 are 0402 / 0603 (module DXF): 0.27 mm left if they are <= 0.9 mm tall; module top about 4.6 mm above the board (box model) | Orange Pi, or measuring a module |
| CLK32K_IN on the module | Board A, RTC | the RTC's 32.768 kHz goes to CLK32K_IN as on Orange Pi's base board; whether the module needs it is not documented | Orange Pi |
| Combo PHY2 in USB 3.0 mode for the modem | software | the RK3588S's combo PHY2 is PCIe / SATA / USB 3.0; Orange Pi's table names only PCIe / SATA for those pins; the device tree sets USB 3.0 mode (`combphy2_psu`, `usbhost3_0`) | first board |
| Device tree: untested | software | `software/` compiles against Orange Pi's 6.1 tree, and every GPIO matches the board's pin map (`software/check_dtb.py`); nothing has run on hardware | first board |
| Camera tuning files | software | Rockchip's camera engine needs a tuning file per camera; Radxa's images have them for these two cameras, Orange Pi's do not | copy from Radxa's `camera_engine_rkaiq` |
| CM5 module's own lane-to-lane skew (MIPI) | Board A, DSI / CSI | not published by Orange Pi; the board allowance of +-1.0 mm is my own (section 3) | Orange Pi, or a measurement |
| TPS25751 configuration tool: whether it exposes the BQ25713 charge current (2.5 A), charge voltage (4.2 V), VSYSMIN and input limits, and services the charger watchdog | Board A, power | the configuration is built in TI's tool and written to the EEPROM through the programming pads | TI's tool, before programming |
| TPS25751 Linux driver | software | Orange Pi's 6.1 `tipd` knows only the TPS6598x (mainline adds ti,tps25750, not the TPS25751), so the device tree leaves it undescribed; the hardware does not depend on it (dead-battery boot from EEPROM) | software |
| MAX17055 I2C address | Board A, fuel gauge | 0x36 (Linux binding example; the datasheet text is silent) | bring-up (`i2cdetect`) |
| BM8563 RTC with Linux's HYM8563 driver | software | register map matches the PCF8563 / HYM8563 table; Orange Pi's kernel builds `rtc-hym8563`, not `rtc-pcf8563` | bring-up |
| Battery pack NTC | Board A, NTC window comparator | 10 kOhm, B3435; the 0-45 degC thresholds scale with B | your pack's datasheet |
| Display panel LED string, init code and video timings | Board A, backlight / software | only the total 18.6 V / 40 mA is published. DisplayModule's documents give neither the ST7703 init sequence nor the timings, so the panel node in `software/` is written but disabled | DisplayModule |
| Display FPC tail length | mechanics | scaled from the drawing, +-10 % | DisplayModule's full outline or a sample |
| Display and touch FPC pin direction | Board A, J701 / J702 | the panel drawing does not mark pin 1 on either tail; the board assumes pin 1 at the left with the glass facing you and the tail down. **UNVERIFIED** | a meter check on the panel (`docs/footprint_audit.md`) or DisplayModule, before ordering |
| AP6275P crystal load capacitors | Board A, Wi-Fi | 27 pF from CL 16 pF and ~5 pF stray | first board (frequency check) |
| Sunlord SWPA3015S4R7MT saturation current | Board A, BB_AUX | 1.4 A from JLCPCB's attributes (the datasheet is an image) | low risk: peak ~0.5 A |
| AP6275P firmware | software | Orange Pi 5 has the same module on the same controller, so Orange Pi's images are expected to carry its `bcmdhd` firmware | first boot (`dmesg`) |
| JLCPCB's CPL rotations | both boards | rules of thumb from JLCKicadTools' table; every part with a pin 1 is listed in `fab/*/ROTATIONS.md` | JLCPCB's placement preview, at order time |
| 0.3 mm pitch camera connectors (FH35C) at JLCPCB | Board A, J704 / J705 | JLCPCB states 0.35 mm minimum IC pin spacing for Standard PCBA; the FH35C's two staggered rows have 0.6 mm pad pitch each, 0.3 mm between rows | JLCPCB's engineering review of the order (they flag what they cannot place) |

## 2. Assumptions

- **Compute module:** Orange Pi CM5 (your 16 GB / 32 GB eMMC unit; V1.1 and V1.5 have the same connectors and holes).
  - GPIO_VREF is tied to 3.3 V as on Orange Pi's own carriers.
  - The module has no Wi-Fi / Bluetooth: the carrier's AP6275P provides them.
- **Battery:** 1S Li-ion/LiPo, 5000 mAh, about 8 x 65 x 85 mm beside the board, PCM >= 12 A, 10 kOhm B3435 NTC, wired to the 9-pin Micro-Lock Plus as pins 1-4 BAT+, 5-8 BAT-, 9 NTC (you confirmed the pin-out at checkpoint 2).
- **Display:** DisplayModule DMKDI0400S0CA (4.0", 720 x 720, ST7703, 4-lane DSI, GT911 touch), FPC toward the device's left side (you confirmed).
- **LTE:** Quectel EM060K-GL on the M.2 Key-B socket, USB 2.0 + USB 3.0 to the CM5 (your choice).
- **Cameras:** Radxa Camera 13M 214 at the rear (4-lane), Radxa Camera 8M 219 at the front (2-lane), Radxa's FPCs; on the Orange Pi CM5 they need a device tree of our own.
- **CM5 supply:** a 5.03 V boost (TPS61088) from VSYS, inside the Orange Pi CM5's 4.75-5.25 V VBUS range (D91).
- **Worst-case battery current:** 9.8 A at 3.5 V; the battery path is sized for 12 A.
- **Enclosure:** none designed. Heights (~9 mm), antenna choice and the CM5 heat spreader to the display frame depend on it.
- **Quantities:** the BOM stock check and the cost estimate assume 5 boards.

## 3. What an experienced engineer should review before ordering

**Orange Pi CM5 interface** (`docs/opi/OPI_REDESIGN.md`, `docs/opi/opi_cm5_pin_map.csv`):
- **Every low-speed pin was assigned again** to suit the module's IO banks (GPIO0 / GPIO3 at 1.8 V, GPIO4 at 3.3 V, GPIO1 at GPIO_VREF = 3.3 V; D87, D88). A second pair of eyes on the pin map, especially the voltage of every line against what it drives, is the most useful check:
  - Open-drain interrupts are pulled up to 1.8 V.
  - The 2N7002 gates and the keyboard RESET# / BOOT# are on 3.3 V pins.
  - The debug UART goes through a TXS0104E to 3.3 V pads.
  - The PCIe sidebands run straight at 1.8 V.
- **Wake from suspend relies on GPIO0** (all 12 used), as on Orange Pi's tablet board. Whether the Orange Pi firmware wakes on the pins chosen is a software question.
- **Mechanics:** the M.2 standoff's shank under the module (section 1), and the module height for the enclosure.

**Power-up sequencing and power path** (Board A, `power_in`, `power_rails` sheets):
- Dead-battery and no-battery start: the TPS25751 loads its configuration from the EEPROM with the SoC off; the BQ25713 then runs the system from the adapter. The EEPROM content is built in TI's tool (section 1), which has not been run.
- The CM5's 5.03 V boost (TPS61088) and the order in which VBUS, the module's 3.3 V / 1.8 V outputs, the LTE supply (TPS63020 buck-boost) and the 5 V USB rail come up.
- CM5 supply current per DF40 contact: at the Orange Pi CM5's 1.8 A maximum, 0.3 A per VBUS contact, the DF40's rating.
- LTE supply: about 2 A in boost mode against Quectel's generic 3-4 A guideline (module maximum listed 1.07 A), with 2 x 220 uF for the bursts.
- USB-A bulk capacitance: 2 x 22 uF per port instead of 120 uF (you accepted it); hot-plug droop on the other port is not verified.
- Battery path at 9.8 A: RSR 10 mOhm 1 W, gauge shunt, BATFET, connector, and the copper (pours on several layers, VSYS on L4).

**High-speed routing** (`docs/opi/length_report.md`):
- **Impedance and P / N skew:**
  - Every pair is routed at the impedance geometry JLCPCB's calculator gives for the stack-up, over a GND plane 0.1 mm away.
  - P / N skew is tuned to the sourced targets (TI SPRAAR7J, the CM4 datasheet), lengths counted the way KiCad does, on the copper as made: before D110, gaps the touching joints spanned were not counted and duplicate tracks were counted twice, which hid up to 0.6 mm of real skew; the pairs were tuned again after the repair.
- **Rear camera (CSI-A), fixed in the D118 re-route (D119):** the data lanes are now **0.14-2.82 mm (1-20 ps) shorter than their clock** (clock 26.07 mm; D0 -0.14, D1 -0.79, D2 -1.78, D3 -2.82). On the D116 files they were 4.63-6.50 mm (32-46 ps) short.
  - The cause (D117): the clock sits between D2 and D1 on connector B but last on the camera connector, so it must cross D1 and D0. Now D3, D2 and the clock run on L3 in connector B's order and D1 / D0 pass under the clock on L4; every lane has one via pair.
  - D0 and D1 are within my +-1.0 mm allowance, D2 and D3 are not: no straight coupled stretch was left for a tuning accordion.
  - Whether the link works at its full lane rate, with this skew plus the module's own unpublished skew, is still the main high-speed question for bring-up, now with about half the skew.
- **Front camera (CSI-B):** clock 2.8-2.9 mm short of its lanes. Its clock runs as two separate traces (17 mm), as on the Radxa version.
- **Over the 0.127 mm P / N target:**
  - USB3_LTE_TXC 0.297 mm, as before (no room for a bump).
  - USB3_LTE_RX is now 0.000 mm (was 0.248, D103).
- **PCIe to the Wi-Fi module:** TX / RX / REFCLK all coupled; skew 0.000 / 0.000 / 0.000 mm (PCIe target 0.127). On the Radxa version PCIE_RX was two traces and PCIE_REFCLK 0.128 mm out.
- **DSI to the display:** matched, lanes 55.08-55.22 mm against the clock's 55.12 (D118: longer than before, as the pins are now mirrored).
- **Reference planes (checked 2026-11-06):** L2 (In1.Cu) and L5 (In4.Cu) are each one continuous GND piece, no splits. About 5 % of the controlled-trace length (107 of 2318 mm) runs over via clearance holes in its reference plane. Measured on the route of order Y4, not on the D118 re-route (the places named here are Y4's): 664 holes up to 1.2 mm, 99 of 1.2-2.5 mm (merged clearances of neighbouring vias); controlled traces cross the larger ones in 33 places on L2 and 26 on L5, at most 2.25 mm (about 15 ps), many at the pair's own layer change. Short local bumps, usually acceptable at these rates; a reviewer may want the worst moved (SD_CLK and CSIA_D3_N near (176.6, 130.7) / (119.6, 135.8), USB_P1 / USB_P2 / KBD / DIG near the hub, PCIE_REFCLK_N near (135.4, 159.6)).
- **KiCad's skew warnings:** KiCad counts each net's whole length, stubs included.
  - PD_BC measures the USB-C data net with its BC1.2 detection branch to the PD controller (a DC detection stub), not a signal path.
  - USBC (4.0 mm) is the same kind: D+ / D- from the USB-C connector to the common-mode choke L401 are 3.44 / 2.82 mm, 0.62 mm apart (D120; about 5 mm on the D116 files); the rest is the stubs, mainly the ESD array D401's branch, 7.6 mm on D+ and 2.7 mm on D- (as on D116). A reviewer may want D401 closer to the connector's path.
  - USB3_LTE_TXC is the 0.297 mm above.
  - The PCIE_REFCLK / WL_REFCLK warnings of the D116 files are gone with the re-route.
- **microSD bus** (50 ohm, 0.12 mm clearance): it crosses the power section; it is routed first and was not matched (no sourced target for an SD bus at the speeds used).

**RF:**
- **Wi-Fi / BT:** AP6275P with its two 50 ohm lines to the u.FL connectors J601 / J602, routed straight on the outer layer over the L2 GND plane (D62).
  - The antenna matching shunts C615 / C616 are not fitted.
  - Antenna choice, cable length and the enclosure decide the match: a VNA check on the first board.
- **LTE:** the antennas connect to the EM060K's own connectors; nothing RF on Board A apart from its supply and SIM.
- **Board B** has no RF.

**Thermal:**
- **CM5:** the heat spreader to the display frame over the 40 x 55 mm keep-out is part of the enclosure, not designed.
- **Power stages:** the charger stage (BQ25713, 2 phases), the CM5 boost and the battery path at 9.8 A worst case. Copper is pours on several layers; no thermal simulation was done.
- **AP6275P and EM060K** under the CM5 / in the M.2 socket: no airflow; the enclosure should give the LTE module a thermal path.

**Other:**
- **Script-generated routing:** Board A's routing comes from `gen/route_a.py` and is not hand-routed.
  - It passes KiCad's DRC against JLCPCB's rules.
  - A human look at the copper plots (`docs/opi/img/`) is worth it before spending money: return paths over splits, long stubs, awkward GND connections.
  - One DRC warning, a copper sliver in a B.Cu pour, has no position in the command-line report: look it up in KiCad's DRC window.
- **Artwork (D106):** the check-on-a-cube logo in white silkscreen on the top, beside the camera connectors, and a line of text in bottom copper under the solder mask, at the right edge (`docs/opi/img/art_*.png`).
- **3D:** the STEP model has the library 3D models and box models for the parts without one, the Orange Pi CM5 among them (no Orange Pi model). Clearance to the enclosure is not checked.

## 4. Estimated cost (5 boards, USD)

- **Prices:** parts at JLCPCB's live prices (2026-10-23 for both boards); Standard PCBA fees from JLCPCB's price page (`research/jlc/order_options_2026-10-22.md`).
- **Not included:** the bare PCBs (priced by JLCPCB's quote at upload), shipping, duties and the off-board parts of section 5.

| | Board A | Board B |
|---|---|---|
| Parts | 329.74 (65.95 per board) | 21.10 (4.22 per board) |
| Assembly fees (setup, stencil, feeders, joints) | 280.48 | 95.59 |
| **Total without the PCB** | **610.22** (122.04 per board) | **116.69** (23.34 per board) |

Details per board: `fab/*/BOM_cost.csv` and the cost table in `fab/*/ORDER.md`.

## 5. Off-board parts to buy

From `docs/off_board_parts.md` (where to buy, delivered to the EU: `docs/shopping_list_eu.md`):

| Item | Part | Connects to | Source / decision |
|---|---|---|---|
| Compute module | **Orange Pi CM5** (no Wi-Fi / BT on the module) | J301-J303 = JP1-JP3 (3 x DF40C-100DS) | D85 |
| CM5 screws | 4 x M2.5 (module holes 2.7 mm), into the SMT standoffs H301-H304 (1.5 mm) | Board A | D13, D86 |
| CM5 heat spreader | thermal pad + aluminium plate to the display frame, over the 40 x 55 mm zone on User.2 | CM5 top | brief; D86 |
| LTE modem | Quectel EM060K-GL, M.2 3042 key B | J501 + M2 screw into H501 | checkpoint 1 decision |
| LTE antennas | per Quectel EM060K HD ch. 5, on the module's own antenna connectors | EM060K-GL | to choose with the enclosure |
| Wi-Fi / BT antennas | 2 x dual-band 2.4 / 5 GHz antennas with u.FL (MHF1) plugs | J601 (WL_ANT0), J602 (WL_ANT1) | to choose with the enclosure |
| Battery pack | 1S Li-ion/LiPo 3.7 V, 5000 mAh, about 8 x 65 x 85 mm, PCM >= 12 A, 10 kOhm B3435 NTC | J102 | C2-1 |
| Battery harness | Molex 505570-0901 housing + 9 x 505572-1000 crimps (2.00 mm, tin, 22-26 AWG), 24 AWG, <= 80 mm; pins 1-4 BAT+, 5-8 BAT-, 9 NTC | J102 (Molex 505578-0971) | C2-1, D11, D111 |
| Display | DisplayModule DMKDI0400S0CA (720 x 720), FPC edge toward the device's left side | J701 (30P 0.5 mm) | Q5, C3-2 |
| Touch panel | the panel's capacitive touch (GT911) | J702 (8P 0.5 mm) | Q1 |
| Rear camera | Radxa Camera 13M 214 + Radxa 31p 0.3 mm FPC, opposite-side contacts, 150 mm | J704 (FH35C-31S) | D21 |
| Front camera | Radxa Camera 8M 219 + Radxa 31p 0.3 mm -> 15p 1.0 mm FPC, same side | J705 (FH35C-31S) | D22, D23 |
| Speakers | 2 x 4-8 Ohm micro-speakers with JST SHR-02V-S plugs | J801, J802 (JST SM02B-SRSS-TB) | to choose with the enclosure |
| Keyboard | BlackBerry Q20 keyboard (flex with the BM20B mate) | Board B J201 | brief |
| Board A <-> Board B cable | 12-pin 0.5 mm FFC, type B (contacts on opposite sides), about 50 mm | Board A J1001, Board B J101 | CHECKPOINT3.md §3 |
| Digitizer (later) | EMR digitizer, 12P 0.5 mm FFC | J703 (reserved) | Q1 |
| Board fixing | Board A 4 x M2 (H305-H308); Board B 2 x M2.5 (H101, H102) | enclosure | checkpoint 3 |

## 6. At order time

1. **U101 (TPS25751DREFR, C30169739) stock:** one per board. JLCPCB had 25 on 2026-10-22, 3 early on 2026-10-23, 23 at the last rebuild that day, 4 on 2026-10-31, **0 on 2026-11-06** and **2 on 2026-11-07** (enough for PCBA qty 2). Order Y4 may hold 2 of them (unknown), so ask before cancelling it. Then pick one:
   - Keep the 2 pieces for the new order, if JLCPCB can.
   - Wait for stock, or use JLCPCB's parts pre-order for this one line.
   - Or switch to TPS25751ADREFR (C55162188; 7 in stock earlier, 0 on 2026-10-31), the PD 3.2 version. It has the same REF0038A package and the same pin names on all 38 pins, so no layout change. But its datasheet does not list the BQ25713 among the chargers it controls (the TPS25751D's does): **UNVERIFIED**. Do not switch without TI confirming that, and the configuration would then be built for the TPS25751A in TI's tool.
2. **J102 (C17389413):** JLCPCB's library model has the 8-circuit geometry (8 pins, 14 mm span, nails 18.5 mm apart, outline 20 mm); the part and these pads have 9 circuits (16 mm, 20.53 mm, 22 mm). JLCPCB has to correct it, or the new order stops at the same point. If it will not, leave J102 off and solder it by hand.
3. **J401 / J402 against the bottom rail:** in the production file of order Y4 the rail comes to 1.0 mm from the board edge at the cutouts, 14.4 mm wide, and the connectors' 15.3 mm flange reaches 1.5 mm past the edge. Settled: JLCPCB checked it and said it is not a concern (reported by the user, 2026-11-11; picture: `fab/board_a/jlc_query_usba_vs_rail.png`).
4. **Display and touch FPC pin direction:** settled from DisplayModule's drawing and laid out to it (D118). When a panel is in hand, the meter check in `docs/footprint_audit.md` confirms it before the first power-up with the display connected.
5. Upload `fab/board_a/cm5_carrier_gerber.zip`, select the options in `fab/board_a/ORDER.md`, then `BOM.csv` and `CPL.csv`.
6. In the placement preview, check every part in `fab/board_a/ROTATIONS.md` (pin 1 against the board's pin 1 mark), and that U601's model pads now lie on its pads.
7. The same for Board B with `fab/board_b/`.
5. **After JLCPCB's engineering review:** they may ask about the 0.3 mm FH35C connectors (section 1) and any part they want to substitute. Keep the LCSC numbers of `BOM.csv` unless they cannot.
6. **Before the first power-up:**
   - Build the TPS25751 configuration in TI's tool and program the EEPROM through its pads (section 3). Until then the PD controller has no configuration of ours, and what it and the charger do in that state is part of the power-up review.
   - So first power the board from a current-limited bench supply.
   - Then install the device tree and the extra kernel options (`software/README.md`), with the serial console connected.
