# Board A for the Orange Pi CM5

2026-10-22. The Radxa CM5 cannot be ordered, so Board A now takes the **Orange Pi CM5** (RK3588S). Board B is unchanged.
The finished Radxa design (sources, board, fab package, docs) is kept in `archive/radxa_cm5_2026-10-22/`.
Decisions D85-D116 in `docs/DECISIONS.md` give each change with its reason.

## 1. Sources

All are Orange Pi files the user supplied; copies with checksums are in `research/dl/orangepi/` (`SHA256SUMS`).

| File | Used for |
|---|---|
| `opi_cm5_pin_definition_v1.1_2025-07.pdf` (OPi CM5 core board interface PIN definition V1.1, July 2025) | every pin's signal name, GPIO, function list and notes; parsed into `gen/data/opi_cm5_pins.json` by `tools/opi_pins.py` |
| `opi_cm5_base_v1.2_schematic.pdf` (Orange Pi CM5 base board V1.2) | IO voltage per GPIO bank (sheet 10 note), GPIO_VREF = 3.3 V, RTC CLKOUT to CLK32K_IN, RTC INT on GPIO0_B0 |
| `opi_cm5_base_tablet_v1.1_schematic.pdf` (Orange Pi CM5 tablet base board V1.1) | Wi-Fi / BT control pins on GPIO0, UART9_M2 for Bluetooth, PCIE20X1_2 *_M0 sidebands |
| `opi_cm5_base_v1.2_top.dxf` | positions of the three DF40 receptacles (land rows, pin-number silkscreen) and of the four M2.5 holes |
| `opi_cm5_v1.1_bot.dxf`, `opi_cm5_v1.5_bot.dxf`, `opi_cm5_v1.5_dxf.pdf` | module outline (55 x 40 mm), plug positions (agree with the base board to 0.02 mm; V1.1 and V1.5 identical), parts on the module's underside |

The newer pin definition (2025) settles what the older mirror left open: JP3.69 is I2S0_LRCK (GPIO1_C5) and JP3.71
I2S0_SCLK (GPIO1_C3).

## 2. Mechanical

- **Connectors:**
  - JP1 / JP2 sit where the Radxa connectors A / B were. JP2's pads are exactly on the old ones (D95); JP1's are 0.06 mm west.
  - JP3 is on the other short edge of the module: the bottom of the board, rows at y 60.57 / 63.65, about 1 mm from the board edge.
  - The footprints keep the Hirose DF40C-100DS recommended land, on Orange Pi's row centres.
- **Holes:** 48.0 x 33.0 mm, the same SMT M2.5 standoffs (H301-H304), within 0.02 mm of the old positions.
- **M.2 standoff H501 (bottom), under JP3 (D86):**
  - Its ring on the top and inner layers is now 4.3 mm, 0.8 mm from JP3's inner pads. The 6.2 mm solder pad stays on the bottom.
  - Its shank stands 0.33 mm proud of the top surface, under 0402 / 0603 parts on the module's underside. That leaves about 0.27 mm, assuming those parts are at most 0.9 mm tall.
  - **UNVERIFIED:** Orange Pi publishes no part heights or 3D model.
- **Module height:** a box model (1.5 mm stack + 1.6 mm PCB + 1.5 mm parts = 4.6 mm). **UNVERIFIED**, for the same reason.

## 3. Power

- **Module supply:** VBUS (JP1.77-87, 4.75-5.25 V, 1.8 A max) from the TPS61088 boost, now set to 5.03 V (feedback 178k / 56k, D91).
- **Module outputs:** VCC_3V3_S3 (JP1.84 / 86) and VCC_1V8_S3 (JP1.88 / 90), 600 mA each (300 mA per pin).
  - The Radxa design's second 1.8 V rail (VCC_1V8_S0) is gone. Its loads (panel IOVCC, CAM-A I2C pull-ups) are on VCC_1V8_S3.
  - JP1.73 (Radxa VCCIO_FLASH) is open: Orange Pi says "do not connect" (D94).
- **GPIO_VREF:** JP1.78 = VCC_3V3_S3 (D87), with 100 nF at the pin.
- **PWRON_L** (JP1.99) is pulled up to VBUS (45k) inside the module. The button, its 100 ohm resistor and the ESD array (VRWM 5.5 V) work at 5 V.

## 4. IO voltages and the pin plan

From the base board V1.2 schematic note, with GPIO_VREF at 3.3 V:

| Bank | Voltage |
|---|---|
| GPIO0 (PMU, wakes the SoC) | 1.8 V |
| GPIO1_A*, B*, C0, C1, C4, C6, D0-D3, D5 | GPIO_VREF = 3.3 V |
| I2S0 (GPIO1_C2, C3, C5, C7, D4) | 1.8 V |
| GPIO1_D6, D7 | not in the note: not used |
| GPIO3 (incl. the GMAC pins) | 1.8 V |
| GPIO4 | 3.3 V |

Every pin, the function it is used for and what it connects to: `docs/opi/opi_cm5_pin_map.csv`
(`tools/opi_pinmap.py`). In short:

| Function | Orange Pi pins | Level |
|---|---|---|
| Module supply, rails, buttons, ADC keys, VSYS monitor | JP1.77-99, JP1.68 (recovery / volume ladder), JP1.96 | - |
| microSD | JP1.57-69 (SDMMC), detect JP1.76 (GPIO0_A4); JP1.75 left open: it is the module PMIC's SPI clock (D105) | as before |
| Debug console UART2_M0 | JP1.51 / 55 -> TXS0104E -> 3.3 V pads (D90) | 1.8 V |
| System I2C (PD controller, gauge, RTC) | I2C4_M3, JP1.28 / 30 | 3.3 V |
| Touch / keyboard / digitizer I2C | I2C6_M3, JP1.80 / 82 (the bus number of the Radxa design) | 3.3 V |
| Touch INT / RST, digitizer INT / RST, keyboard RESET# / BOOT#, hub reset, LTE RESET / W_DISABLE gates | GPIO1_A/B on JP1 | 3.3 V |
| Backlight PWM | PWM13_M1, JP1.95 | 3.3 V |
| Panel power, status LED | GPIO4_A7 (JP1.97), GPIO4_A4 (JP1.21) | 3.3 V |
| PDM microphone | PDM0_M0, JP1.48 / 49 (microphone now at 3.3 V, D94) | 3.3 V |
| CAM-B I2C | GPIO1_A0 / A1, JP2.2 / 4, as software I2C: I2C2 is the module's (D104); 2.2k pull-ups added | 3.3 V |
| Amplifier enable / channel | GPIO4_A2, JP2.9 | 3.3 V |
| USB OTG (USB-C), CSI 4-lane + 2-lane, DSI 4-lane | JP2, same pins as the Radxa B connector | - |
| LTE USB 3.0 | combo PHY2, JP2.16-24, USB3 mode (D89) | - |
| LTE USB 2.0, hub uplink | USB20_HOST1 JP3.1 / 3, USB20_HOST0 JP3.13 / 15 | - |
| Wi-Fi PCIe + REFCLK | combo PHY0, JP3.76-90; sidebands PCIE20X1_2 *_M0 JP3.22 / 24 / 43, direct (D89) | 1.8 V |
| Bluetooth UART with RTS / CTS | UART9_M2, JP3.26 / 28 / 30 / 40 | 1.8 V |
| Wi-Fi / BT REG_ON and wake lines | GPIO0 on JP3, as the Orange Pi tablet board (D88) | 1.8 V |
| Wake / hold pins: RTC, modem wake, keyboard INT#, 5 V enable, LTE power, modem power-off | GPIO0 on JP3 / JP1.47 (D88) | 1.8 V |
| PD controller IRQ, gauge alert, charger PROCHOT# | GPIO3 on JP3 (open drain, pulled up to 1.8 V) | 1.8 V |
| CAM-A I2C, MCLK, PDN, RST; CAM-B MCLK, PDN, RESET; panel RESET | I2C3_M1, MIPI_CAMERA1/2_CLK_M1, GPIO3 (D93) | 1.8 V |
| I2S to the amplifiers | I2S0 SCLK / LRCK / SDO0, JP3.71 / 69 / 70 | 1.8 V |
| 32.768 kHz to the SoC | CLK32K_IN, JP3.96, from the RTC's CLKOUT (D92) | 1.8 V |

All 12 GPIO0 pins on the connectors are used.

## 5. Circuit changes against the Radxa design

| Change | Parts |
|---|---|
| Connector symbols and footprints: Orange Pi pin names (with IO voltage), positions | J301-J303 |
| TXS0104E moved from the PCIe sidebands (now direct at 1.8 V) to the debug UART | U602 -> U302 |
| 10k pull-ups to 1.8 V on the AP6275P's open-drain CLKREQ# and PME# | R605, R606 (new) |
| 2.2k pull-ups to 3.3 V on CAM-B's I2C (on the Radxa module before) | R719, R720 (new) |
| 100 nF at GPIO_VREF | C307 (new) |
| Pull-ups of RTC INT#, modem WAKE#, keyboard INT#, PD IRQ, gauge ALRT#, PROCHOT#, EN_5V moved to VCC_1V8_S3 | R303, R504, R1004, R103, R127, R124, R207 |
| CM5 boost feedback 169k -> 178k (5.03 V) | R205 |
| PDM microphone supply and its capacitor to VCC_3V3_S3 | U803, C805 |
| Panel IOVCC bead and CAM-A I2C pull-ups from VCC_1V8_S3 (one 1.8 V rail) | FB701, R713, R714 |
| RTC CLKOUT also to CLK32K_IN | (net WIFI_LPO_32K) |
| VCC_1V8_S0 test pad removed (rail gone) | - |

Some parts have new reference designators because the schematic order changed: the RTC capacitor is C308 (was C307), the
CM5 sheet's capacitors C305-C311, test pads TP304-TP305, and the Wi-Fi antenna shunt pads C615 / C616 (were C617 /
C618). `fab/board_a/BOM.csv` and `CPL.csv` are generated from the board, so they agree.

## 6. Layout changes

- **Placement:** `gen/pcb_a.py`.
  - The module centre is 0.04 mm off the old one (D95), the holes at Orange Pi's positions.
  - The RTC group is fixed where checkpoint 3 had it.
  - The PCIe AC capacitors (C609-C612) are now beside the Wi-Fi module's PCIe pins (D96).
  - The REFCLK capacitors (C613 / C614) are north-west of the module's REFCLK pins (D98).
  - The rest is placed by the same rules as before.
- **Differential pairs:** `gen/route_pairs.py`.
  - PCIe and its REFCLK now start at JP3.
  - LTE USB 3.0 starts at JP2, leaving east between the pin rows (D97), then north on L4 only (D99).
  - The USB 2.0 uplinks start at JP3.
  - CSI, DSI and OTG are unchanged.
- **Camera lane matching:**
  - Each camera lane's P / N skew is now tuned right after the lane is routed, so the next lanes route around its bumps (D100).
  - A pair round that leaves a lane with more than 0.5 mm of skew counts that lane as failed (D101).
  - Without these, CSIA_D1 kept 4.3 mm of P / N skew in every run: on this board the router laid the next lane 0.55 mm beside it, no room to tune.
- Decisions D95-D103 record every routing change and the runs that led to it.
- The routing flow (`gen/route_a.py`) is the one of checkpoint 4. A full run now also starts with no DRC exclusions (the old board's would point at items that no longer exist).

## 7. Software (device tree)

Written: `software/` (build, install and what is left: `software/README.md`), for Orange Pi's Debian 12 / Ubuntu 22.04
images on Linux 6.1. It starts from Orange Pi's own CM5 trees, and writing it against them found two pin errors on this
board, both fixed:
- **CAM-B I2C (JP2.2 / 4):** Orange Pi's table offers I2C2_M4 there, but the module runs I2C2 on its M0 pins for the NPU
  regulator. The same pins are now a software I2C bus (D104).
- **JP1.75 (SDMMC_PWREN):** it is GPIO0_A5, the module PMIC's SPI2 clock. Now left open, and the SD power-switch option
  that hung on it is removed (D105).

Changes from the plan that was here:
- The BM8563 RTC uses the `haoyu,hym8563` driver Orange Pi's kernel builds.
- CAM-B's PDN (CAMB_IO0, GPIO3_C4) is held high as an always-on supply switch, as in Radxa's overlay for the 8M camera.
  CAMB_IO1 is unused, and the module's own 24 MHz oscillator replaces MCLK.
- Six drivers are missing from Orange Pi's kernel config; `software/kernel/cm5-handheld.config` adds them.

## 8. Results (installed board: run o35, `gen/route_a.py --iters 60`, 2.5 h; then the SD power switch taken out without re-routing, D105)

| Check | Result |
|---|---|
| ERC | 0 errors, 0 warnings |
| Netlist against the generator's intended nets | 0 mismatches (531 nets, 432 parts, after D105) |
| DRC, zones refilled, with schematic parity | 0 errors, 0 unconnected, parity 0; 7 by-design findings excluded (the five standoffs and the M.2 socket's locating holes inside the module courtyard, as before); 5 warnings: 4 skew (below) and 1 copper sliver on B.Cu (a pour artefact; KiCad's command-line report gives no position: look it up in KiCad's DRC window) |
| Fab package | `fab/board_a/`: 130 BOM lines, 379 parts placed (131 top, 248 bottom), 3 do-not-fit; every BOM line found at JLCPCB with the MPN matching and stock for 5 boards (2026-10-23; U101 had dipped to 3 earlier that day, REVIEW.md section 6) |
| Parts + assembly for 5 boards, without the PCB | 610.22 USD (Radxa version: 622.07) |

Length matching (`docs/opi/length_report.md`, lengths as KiCad counts them):

| | Orange Pi version | Radxa version |
|---|---|---|
| DSI, 5 lanes | all 45.77 mm, matched | all 45.75 mm, matched |
| CSI-A (rear camera) lanes against the clock | clock 29.21 mm, lanes 22.77-24.53 mm: **-4.67 to -6.44 mm** (33-45 ps) | -3.55 to +3.55 mm |
| CSI-B (front camera) lanes against the clock | clock 16.93 mm, lanes +2.79 / +2.86 mm (clock as two traces) | +2.29 / +2.76 mm (same) |
| P / N skew over target | USB3_LTE_TXC -0.297 mm, USB3_LTE_RX +0.248 mm (D103), PD_BC -3.19 mm (BC1.2 detection stub) | USB3_LTE_TXC -0.297, PCIE_REFCLK -0.128, USBC -1.95, PD_BC +3.14 mm |
| PCIe to the Wi-Fi module | TX 40.07 / RX 44.34 / REFCLK 63.19 mm, all coupled, skew 0.000 | PCIE_RX as two traces |

KiCad's skew rule also flags USBC (-1.90 mm): it measures the whole net, including the BC1.2 branch to the PD controller;
the length report's pad-to-pad measure gives +0.79 mm (in target).

Copper plots and 3D renders: `docs/opi/img/`.

## 9. Open items from the redesign

| Item | Status |
|---|---|
| Module part heights (H501 shank clearance, module height for the enclosure) | UNVERIFIED: no Orange Pi 3D model; ask Orange Pi or measure a module |
| Whether the module needs the 32.768 kHz on CLK32K_IN | not documented; supplied as on Orange Pi's own carrier |
| Combo PHY2 in USB 3.0 mode | the SoC supports it (RK3588S combo PHY2 = PCIe / SATA / USB 3.0); Orange Pi's table names only PCIe / SATA. The device tree sets USB 3.0 mode: confirm on the first board |
| Device tree for this carrier | written (`software/`); untested on hardware; display disabled until DisplayModule's timings and init code |
| CSI-A lanes 4.7-6.4 mm shorter than their clock | worse than the Radxa version (+-3.55 mm); review item (REVIEW.md section 3) |
| U101 TPS25751DREFR stock at JLCPCB | 23 at the last rebuild, after 3 earlier the same day: check again when ordering (REVIEW.md section 6, step 1) |
