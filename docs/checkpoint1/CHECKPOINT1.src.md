# Checkpoint 1: research summary, block diagram, pin budget, power

Project: Radxa CM5 handheld carrier (Board A) + BlackBerry Q20 keyboard board (Board B)
Date: 2026-10-14 · Status: **checkpoint 1 complete; all questions answered (section 11, `docs/DECISIONS.md`); ready for checkpoint 2 (schematics)**

Revised after your answers: the charger is now a **BQ25713** controlled by a **TPS25751**, the fuel gauge is a **MAX17055**, the battery path is sized for **12 A** (9-pin connector, ≥12 A PCM), the modem also gets **USB 3.0**, and the stylus approach is fixed.

Everything below is traceable to a downloaded document (section 12). Anything I could not confirm from a source is marked **UNVERIFIED** and collected in section 10.

---

## 0. Summary

**Settled by the research:**
- **CM5:** RK3588S2 on 3 × Hirose DF40C-100DP-0.4V plugs. Carrier side is 3 × DF40C-100DS-0.4V(51) (1.5 mm mated height), the same part Radxa's IO board uses. LCSC C597931, 33.5 k in stock.
- **CM5 supply:** VCC_SYSIN is **3.6–5.2 V** (Radxa recommends a 4 V / 3 A supply).
- **No Wi-Fi/BT on the CM5.** That needs an on-board module; AP6275P is proposed.
- **USB:** the CM5 exposes only **two USB 2.0 host ports** plus OTG0, so a hub is needed. HOST0 goes to the hub (2 × USB-A, keyboard, spare); HOST1 goes directly to the LTE modem.
- **Display/cameras:** DSI1 is the only 4-lane DSI. CSI is 4-lane + 2-lane, so the cameras are one 4-lane (Radxa Camera 4K pinout) and one 2-lane (Radxa Camera 8M / RPi v2 pinout), exactly as on Radxa's IO board.
- **Keyboard:** the Q20 flex carries the key matrix, the 4 top buttons, the optical trackpad (1.8 V I2C), the key backlight LEDs and a microphone. Board B can support all of it with the BBQ20KBD pin map, so the i2c_puppet firmware (MIT) runs unmodified.

**Changes forced by the research (I deviated from the brief):**
1. **CM5 supply rail.** A direct VSYS feed would brown out the CM5 below about 3.6 V. The candidate 4.0 V buck-boost (TPS55288) powers up with its output *disabled* until an I2C write, so nothing could turn it on before the CM5 boots. No standalone buck-boost of 5 A or more is stocked. Plan: a **TPS61088 boost to 4.8 V**. VSYS never exceeds 4.55 V, so it always regulates, and 4.8 V sits inside the CM5's 3.6–5.2 V range. The trade-off is that it's above Radxa's preferred 4 V (section 5.1).
2. **Worst-case battery current is 9.3 A at 3.7 V (9.8 A at 3.5 V), not about 5 A.** The original BQ25792 charger can pass only 6 A RMS from the battery. Per your answer (Q2) it is replaced by a **BQ25713** controller with an external battery FET, and the whole battery path is sized for 12 A.
5. **The BQ25713 has no battery-thermistor (TS) input**, so your brief's "NTC to the charger's TS pin" can't be done literally. Replacement: a hardware window comparator on the pack NTC forces the charger into its no-charge state outside 0–45 °C. It works with the SoC off.
3. **Wi-Fi/BT module lines need a 1.8 V bank.** The AP6275P's I/O rail is 1.8 V only. Its BT UART and enables use the CM5's 1.8 V S3 banks; the PCIe sideband signals go through a 3.3 ↔ 1.8 V translator.
4. **No nano-SIM + microSD combo tray is stocked at JLCPCB.** I'll use two push-push sockets on the right edge, which is your stated fallback.

**Decisions:** all 13 questions plus two follow-ups are answered; see section 11 and `docs/DECISIONS.md`.

---

## 1. Your answers and how I applied them

| Question | Your answer | Applied as |
|---|---|---|
| Display | Default 4″ 720×720 + "high quality stylus" | Default panel proposed: **DisplayModule DMKDI0400S0CA** (4.0″ 720×720, ST7703, 4-lane DSI, GT911 capacitive touch). A *high-quality* stylus isn't something capacitive touch provides, so the stylus is open question **Q1** with four options. |
| Battery | 8×65×85 mm, **beside** the board | Board bottom side is free for components (the M.2 LTE module goes under the CM5). Enclosure impact in section 5.12. |
| LTE | "Implement it on the board itself, not through a connector such as USB-A; use **EM060K-GL**" | EM060K-GL exists only as an M.2 3042 card, so it can't be soldered down. Plan: M.2 Key-B socket **on the carrier**, wired straight to its own SoC USB port (HOST1, no hub, no USB-A). For a soldered-down module, see **Q6**. |
| Fab / USB-C | Keep defaults | JLCPCB 6-layer, impedance-controlled, 1.2 mm (section 5.10). USB-C is a 16-pin USB 2.0 receptacle with no DP alt-mode. |

The second round of answers (Q1–Q13) is in section 11.

---

## 2. Reference material status

| Source | Status |
|---|---|
| Radxa CM5 docs (docs.radxa.com renders only with JavaScript, so I used the docs' GitHub source `radxa-docs/docs`) | ✅ README, hardware interface, revisions, downloads, FAQ, accessories |
| Radxa CM5 V2.21 pinout (xlsx), V2.21 schematic, 2D DXF, 3D STEP, placement map | ✅ downloaded and parsed |
| Radxa CM5 IO board V2.2 schematic, BOM, 2D DXF, PADS/Altium layout (`radxa/radxa-cm-projects`) | ✅ schematic + BOM + DXF parsed; layout files fetched for checkpoint 2 |
| Solder Party BBQ20KBD hardware (`solderparty/bbq20kbd_hw`, KiCad) + i2c_puppet firmware | ✅ cloned, schematic and PCB parsed |
| TI TPS25750, TPS25751, BQ25792, BQ25713, BQ25731, TPS55288, TPS61088, TPS63020, TPS61169 datasheets | ✅ |
| Quectel EM060K Series & EM120K-GL Hardware Design V1.1 (from quectel.com) | ✅ |
| DisplayModule DMKDI0400S0CA specification V1.0 | ✅ (outline drawing is a low-resolution image, so the FPC pitch is UNVERIFIED) |
| AMPAK AP6275P datasheet | ✅ |
| MAX98357A datasheet (analog.com unreachable from this machine; Adafruit mirror used) | ✅ |
| MAX17048/MAX17049 datasheet, Rev 1 (4/12), copy you supplied (alldatasheet.com mirror) | ✅ (MAX17048 since replaced by MAX17055, decision Q13) |
| **MAX17055 datasheet** | ❌ analog.com times out and both LCSC copies are "temporarily unavailable". Needed before the schematic. |
| Molex Micro-Lock Plus 505575 drawing (LCSC) | ✅ (electrical ratings are in a separate product spec, 5055700001-PS, not obtained) |
| USB2514B, DF40 datasheets | ✅ downloaded, to be read at checkpoint 2 |
| JLCPCB capabilities + 6-layer stack-ups (via JLCPCB's impedance-calculator API) | ✅ |
| LCSC/JLCPCB stock (via JLCPCB's parts API, 14 Oct 2026) | ✅ |

---

## 3. Radxa CM5: verified facts

| Item | Value | Source |
|---|---|---|
| SoC | RK3588S2 | DOC README |
| Module outline | **41.0 × 56.0 mm in Radxa's DXF**, with R4 corners concentric with the holes. Docs say "55 × 40 mm". I'll use the DXF size as the keep-out. **UNVERIFIED which is right.** | CM5 2D DXF (BOARD_OUTLINE layer); DOC README |
| Mounting holes | 4 × Ø2.6 mm drill (Ø3.0 mm pad), on a **33.0 × 47.95 mm** rectangle (same spacing as RPi CM4), 4.0 mm from the DXF edges | CM5 DXF (TOOL_BOT), IO board DXF |
| B2B connectors | 3 × 100-pin Hirose DF40, 0.4 mm. Module: DF40C-100DP-0.4V. Carrier: **DF40C-100DS-0.4V(51)**, mated height **1.5 mm**, rated 0.3 A per contact | CM5 sch p4; IO BOM; LCSC C597931 |
| Connector positions (from module centre = hole-pattern centre, carrier top view) | A (pins 1–100): (+17.03, +2.49) mm, vertical. B (101–200): (−17.03, +2.49) mm, vertical. C/"J1" (1–100): (+0.07, +24.0) mm, horizontal. Module and IO-board DXFs agree within 0.06 mm. | CM5 + IO DXF pad clusters |
| Supply | VCC_SYSIN on 6 pins (A77–A87), **3.6–5.2 V**, "maximum efficiency achieved at 4V. Supplying 5V or above may cause audible humming from the voltage regulating circuit." Typical 2 A; recommended supply 4 V / 3 A. The IO board makes 4.04 V with an MP8759 buck. | DOC README; IO sch p15 |
| Outputs for the carrier | VCC_3V3_S3 (A84, A86, C92), **600 mA max**. VCC_1V8_S0 (A88, A90), **600 mA max**. VCCIO_FLASH (A73) = VCC_1V8_S3. | Pinout xlsx; CM5 sch p4 |
| 5V_HDMI (B106) | Must be 5 V only if HDMI is used and VCC_SYSIN < 5 V; it feeds the HDMI DDC level shifter. No HDMI here, so NC. | Pinout xlsx note; CM5 sch p4 |
| GPIO_VREF (A78) | Tied on-module to VCC_3V3_S3 (sets VCCIO6 = 3.3 V); the IO board leaves it NC | CM5 sch p4, p17 |
| I/O voltage banks | PMUIO1 1.8 V; PMUIO2 3.3 V; VCCIO1 **1.8 V only** (S0 rail, off in suspend); VCCIO4 1.8 V (S3); VCCIO5 3.3 V; VCCIO6 3.3 V | CM5 sch p9, p13, p17 |
| Power-on | PWRON_L → RK806 PWRON (button to GND). RK806 auto-boots when VCC_SYSIN appears (VDC divider). | CM5 sch p18 |
| Reset / Maskrom / Recovery | RESET_L (A92) → NPOR; SARADC_IN0 (A93) to GND = Maskrom (the module also has its own button); SARADC_IN1 (C26) to GND = Recovery | CM5 sch p13; IO sch p19 |
| USB exposed | OTG0 USB2 (B101–105) + OTG0 USB3/DP lanes (C3–C29); **USB2 HOST0** (C63/65); **USB2 HOST1** (C45/47); USB3 SuperSpeed on combo PHY2 (C51–59, shared with PCIe/SATA) | Pinout xlsx |
| PCIe | PCIe 2.0 x1 lane 0 (B110–124) with PCIE20X1_2 sidebands; lane 2 on combo PHY2 (C39–59) | Pinout xlsx; IO sch p7 |
| MIPI | DSI0 2-lane (B157–171), **DSI1 4-lane** (B175–196), CSI D/C-PHY0 RX 4-lane (B115–141), CSI0 2-lane (B128–142) | Pinout xlsx; DOC FAQ |
| SDMMC | 4-bit on A57–A69, detect C74, SD_PWR_ON A75 | Pinout xlsx; IO sch p6 |
| Audio | I2S0 pins (1.8 V); no on-module codec ("external codec needed") | Pinout xlsx; DOC FAQ |
| Wireless | **None on the module** ("there is no on-board WiFi/BT module, external module is required") | DOC accessories/wifi_bt_access |
| Ethernet | On-module GbE PHY, MDI on A3–A12 (unused here) | Pinout xlsx |

---

## 4. BBQ20KBD (Board B reference): verified facts

| Item | Value | Source |
|---|---|---|
| License | **CERN-OHL v1.2** (hardware); firmware i2c_puppet **MIT** | repo LICENSE files |
| Keyboard mating connector | **Hirose BM20B(0.8)-40DS-0.4V(51)**, 40 pins, 0.4 mm, 0.8 mm stack. LCSC C424543, 8.8 k in stock. | bbq20_keyboard.kicad_pcb (footprint + LCSC field) |
| Keyboard pinout | 1 GND, 2 TP_SHUTDOWN, 3 TP_SCL, 4 TP_MOTION, 5 TP_SDA, 6 TP_RESET, 7/9/11 GND, 8 +2V8, 10 +1V8, 12–18 COL1–COL7, 19–22 GND/AGND, 23 MIC, 24 MIC_VDD, 25 GND, 26–32 ROW7–ROW1, 33/35/37 LEDK, 34/36 LEDA, 38/39 NC, 40 GND | same (pad nets) |
| Matrix | 7 rows × 6 columns on GPIO1–7 / GPIO8,9,14,13,12,11; trackpad click and BTN_LEFT1/LEFT2/RIGHT1 in the matrix; **BTN_RIGHT2 on COL7 (GPIO10, doubles as BOOTSEL)**. All 4 top buttons + trackpad are supported. | schematics.pdf; i2c_puppet boards/bbq20kbd_breakout.h, app/keyboard.c |
| Trackpad | Optical, on the keyboard flex, I2C at 1.8 V (address 0x3B), needs +1V8 and +2V8; BSS138 level shifters to the 3.3 V RP2040 | schematics.pdf p2; i2c_puppet app/touchpad.c |
| Backlight | LEDs are on the keyboard flex (LEDA = 3.3 V, LEDK switched by a BSS138 driven from RP2040 GPIO25 = PWM4B), so it is PWM-dimmable | schematics.pdf |
| MCU | RP2040 + 16 Mbit QSPI flash, 12 MHz crystal, AP2112K-3.3 from 5 V | schematics.pdf p1 |
| Board size | 74.0 × 53.1 mm (Edge.Cuts), including USB-C, PMOD and Qwiic, which Board B won't need | kicad_pcb |

---

## 5. Architecture decisions

### 5.1 Power

See `power_tree.svg` and section 7.

- **USB-C PD sink: TPS25751D** (WQFN-38, integrated sink path). LCSC C30169739, 5.7 k in stock.
  - **Why the TPS25751 instead of the TPS25750:** its datasheet explicitly lists integrated I2C control of the BQ25713 (along with BQ25731, BQ25792 and others). The TPS25750 datasheet names no supported chargers, and its BQ25713 support rests only on a TI forum reply. It is also USB-IF PD 3.1 certified.
  - **EEPROM boot:** patch + configuration come from an I2C **EEPROM of at least 36 KB at 0x50** on its controller bus, so PD and charging work with a dead battery and the SoC off. It is programmed through on-board pads (decision Q12).
  - **Dead-battery strap:** SafeMode (no sink path until the configuration is loaded).
  - **SoC link:** the SoC talks only to the TPS25751 (I2C target at 0x20–0x23 via ADCIN straps, IRQ → GPIO0_C4).
  - **Linux:** mainline `tipd` lists only `ti,tps25750`, so TPS25751 support is **UNVERIFIED**. It isn't needed for charging.
  - **VIN_3V3:** from an always-on 1 µA-Iq LDO.
- **Charger: BQ25713** (NVDC buck-boost charge controller, I2C 0x6B). LCSC C2878935, 3.3 k in stock.
  - **Range:** 3.5–24 V input, 1–4 cells, set to 1S by the CELL_BATPRESZ divider. 1S defaults: VREG 4.2 V, VSYSMIN 3.584 V, SYSOVP 5 V.
  - **Battery-less operation:** "Instant-on with no battery or depleted battery" (datasheet), so the system runs with no battery fitted, as your brief requires.
  - **External parts:** 4 N-channel switching MOSFETs, a P-channel battery FET, input and battery current-sense resistors, and the inductor. The battery FET runs in linear mode at VSYSMIN when the battery is flat, as an ideal diode in supplement mode, and fully on otherwise.
  - **Battery FET sizing:** ≥12 A. Constraint: BATDRV drives at most 5 nF of gate capacitance (1–3 nF recommended), which limits the FET choice (checkpoint 2).
  - **Charge settings:** 2.5 A / 4.2 V and the input limits are written by the TPS25751 configuration. Which fields TI's web tool exposes is **UNVERIFIED**.
  - **VSYS max:** battery + 160 mV (±3 %), about 4.36–4.5 V, so the 4.8 V CM5 boost below still always regulates.
  - **No battery-thermistor input.** A window comparator on the pack NTC (trips below 0 °C or above 45 °C) pulls ILIM_HIZ low, which puts the charger in HIZ: no charging, system on battery. It works with the SoC off. Thresholds are set at checkpoint 2, once the pack's NTC type is known.
  - **PROCHOT#** (open drain) → GPIO3_D5. It asserts on battery-discharge current above a programmable threshold, low VSYS and input over-current, so Linux can throttle the CPU/GPU before the battery path is stressed.
- **Battery path, sized for 12 A** (decisions Q3/Q4):
  - 9-pin Molex Micro-Lock Plus 2.0 mm (4 × BAT+, 4 × GND, NTC; 12 A at 3.0 A per contact).
  - Pack PCM ≥12 A.
  - Battery FET, both current-sense resistors and copper all rated for 12 A.
- **CM5 rail: TPS61088 boost → 4.8 V**, always on whenever VSYS exists; the RK806 handles on/off via the power button. Why not the brief's options:
  - **Direct VSYS:** on battery, VSYS follows VBAT (3.0–4.2 V minus I·R), so the CM5 (min 3.6 V) would brown out with 10–40 % charge left, depending on load.
  - **4.0 V buck-boost:** TPS55288 needs I2C to enable its output (OE bit resets to 0). Other parts are too small: TPS63020 has a 4 A switch, about 2 A out in boost mode, below the 3 A the CM5 wants. No ≥5 A standalone buck-boost is in JLCPCB stock.
  - **Boost:** VSYS max is about 4.5 V (BQ25713: battery + 160 mV ±3 %), so a 4.8 V output always regulates and stays 0.4 V below the CM5's 5.2 V max.
  - **Cost:** slightly lower RK806 efficiency than at 4 V (my estimate: 2–3 %), and Radxa's "≥5 V may hum" note sits 0.2 V above our rail.
- **5 V rail: TPS61089 boost → 5.1 V** for 2 × USB-A, the keyboard board and CAM-A's 5 V pins.
  - Enabled by GPIO0_C2 with a default-on pull-up.
  - Per-port TPS2553 current limits (~0.6 A) are switched by the USB2514B port-power pins.
- **LTE rail: TPS63020 buck-boost → 3.7 V** (EM060K-GL range is 3.135–4.4 V; a direct VSYS feed could exceed 4.4 V when charging is done).
  - Datasheet max data-transfer draw is 1.07 A. **Quectel's generic PSU guideline is 3 A continuous / 4 A peak; the TPS63020 meets that only in buck mode.** In boost mode it gives about 2 A plus 2 × 220 µF bulk capacitance. Listed as a risk, not hidden.
- **AUX 3.3 V: second TPS63020** for the AP6275P (1.2 A peak), USB hub and cameras.
- **Backlight: TPS61169** LED boost (18.6 V × 40 mA, PWM on CTRL).
- **Fuel gauge: MAX17055** (TDFN-10; decision Q13). LCSC C2976422 (MAX17055ETB+T), 6.1 k in stock.
  - It uses a current-sense resistor in the battery path. The mainline `max17042_battery` driver reports battery current, average current and a charge counter from it (checked in the driver source).
  - **Datasheet not obtained yet**, so its pin-out, sense-resistor value and placement, I2C address and thermistor options are **UNVERIFIED**. If you can drop it in your home directory like the MAX17048, I'll fold it in before the schematic.
  - ALRT# → GPIO0_D3 (wake-capable).
- **CM5 outputs are kept light:** VCC_3V3_S3 ≤ 300 mA of its 600 mA (SD card, panel VCI, touch, pull-ups); VCC_1V8_S0 ≤ 100 mA.

### 5.2 USB topology

The CM5 has OTG0 + HOST0 + HOST1 (USB 2.0). The devices needing a host port are USB-A ×2, the keyboard and LTE, which is more than two, so **a hub is required**.

- **OTG0 → USB-C:** device by default; this is the Maskrom/download port. 2.2 Ω series, common-mode choke and ESD, as on the IO board.
- **HOST1 → M.2 LTE directly:** this is the USB 2.0 half of the modem's USB 3.0 link (section 5.3). Full bandwidth, and the modem's power management isn't tied to the hub.
- **HOST0 → USB2514B:** P1/P2 USB-A, P3 keyboard FFC, P4 reserved digitizer FPC (decision Q1).
- **Why USB2514B over Radxa's FE1.1S:** multi-TT and per-port power control. Both are stocked.

### 5.3 LTE

- **Socket and USB:** M.2 Key-B 3042 socket on the board's **bottom side under the CM5**.
  - **USB 2.0 + USB 3.0** (decision Q7): USB 2.0 from HOST1 → M.2 pins 7/9. SuperSpeed from combo PHY2: host TX (J1-51/53) → 100 nF → M.2 pins 37/35; module TX (M.2 pins 31/29) → host RX (J1-57/59) with no caps, since those are inside the module (Quectel Fig. 18).
  - This is the same pairing Radxa's IO board uses for its USB 3.0 port. The M.2 PCIe pins stay unconnected.
- **Control signals** (levels from the EM060K Hardware Design V1.1):
  - FULL_CARD_POWER_OFF# is 3.3 V tolerant (on above 1.19 V), so it's driven directly from GPIO0_D0.
  - RESET# and W_DISABLE1# have internal pull-ups, so they're driven open-drain through NMOS (Quectel reference).
  - WAKE_ON_WAN# (OD) → GPIO0_C6.
- **SIM:** nano-SIM push-push socket with ESD and series parts per Quectel's reference (values at checkpoint 2); SIM_DETECT → USIM1_DET (M.2 pin 66).
- **Antennas:** main and diversity/GNSS go to the module's own connectors.
- **eSIM:** possible (an MFF2 eSIM in parallel with the socket is a common design), but Quectel's dual-SIM/eSIM wiring isn't verified yet; I'd treat it as a footprint option at checkpoint 2.

### 5.4 Wi-Fi / Bluetooth

**AMPAK AP6275P** (BCM43752, Wi-Fi 6 2×2 over PCIe 2.0 lane 0, BT 5.0 over UART + PCM), LCSC C2984107, 494 in stock.

- **Why this module:** the CM5 exposes no SDIO, so SDIO modules are out, and a PCIe module needs no hub port. Radxa's IO board uses the same PCIe lane for its Wi-Fi.
- **BT UART:** UART6_M1 with RTS/CTS on the four pins Radxa labels "…_WIFI" (1.8 V).
- **Enables and wakes:** WL_REG_ON / BT_REG_ON / BT_WAKE on VCCIO4 (1.8 V S3, so the radio survives suspend); WL/BT_HOST_WAKE on PMU GPIO0_A0 / GPIO0_B0.
- **PCIe sidebands:** PERST#, CLKREQ#, PME# through a 4-channel translator (Radxa uses UM3204).
- **Supporting parts:** 37.4 MHz crystal; 32.768 kHz LPO from an always-on HT8563 RTC (the same approach as the IO board, which also gives the device a battery-backed clock); 2 × u.FL on 50 Ω coplanar lines.
- **Driver support:** mainline `brcmfmac` supports BCM43752 over PCIe (checked in the 7.3-rc7 source; needs firmware `brcmfmac43752-pcie`). **Radxa BSP support is UNVERIFIED:** Radxa ships a `broadcom-wifibt-firmware` package, but I haven't confirmed it covers the AP6275P.
- **BT audio:** BT PCM is routed to test pads only, because SCO over HCI needs no I2S.

### 5.5 Display, touch, stylus

- **Panel (proposed): DMKDI0400S0CA.** 30-pin display FPC:
  - 4-lane DSI on pins 7–20.
  - RESET (26) at IOVCC = 1.8 V, driven by LCD_RESET_L (1.8 V) directly.
  - IOVCC 1.8 V from VCC_1V8_S0; VCI 3.3 V through a load switch on LCD_PWREN_H.
  - TE (25) left NC.
  - Backlight: 12 LEDs at 18.6 V / 40 mA via TPS61169.
- **Touch:** a separate 8-pin CTP tail (GT911, I2C at 3.3 V on I2C6, INT/RST on 3.3 V GPIOs, so no translator). This is a **second FPC connector** beyond the one the brief listed.
- **Linux:** needs a panel entry for `panel-sitronix-st7703` with this panel's init sequence, which must come from the vendor (software risk).
- **Stylus (decision Q1):** capacitive touch with a universal active stylus now. A reserved "digitizer" FPC (USB from hub port 4, I2C, INT, RST, 3.3 V, GND) leaves room for an EMR pen digitizer later without a respin.

### 5.6 Cameras

Same as Radxa's IO board, so the official camera modules plug in.

- **CAM-A:** 4-lane CSI (D/C-PHY0 RX) on a Hirose FH35C-31S-0.3SHW(50) (Radxa Camera 4K, IMX415 pinout). MCLK GPIO1_B6, PDN, RST and I2C8 at 1.8 V, plus 3.3 V and 5 V.
- **CAM-B:** 2-lane CSI0 on a 15-pin 1.0 mm FPC (Radxa Camera 8M 219 / RPi v2 pinout, Radxa's "reverse" pin order). I2C7 at 3.3 V and CAM_IO0/1.
- **Lane split 4 + 2:** CAM-B is limited to 2 lanes, which is still enough for 8 MP @ 30 fps on an IMX219.
- **Low-profile requirement:** I still need a horizontal flip-lock 15-pin 1.0 mm connector; the IO board's part is vertical (3 mm), and JLCPCB search found no stocked horizontal one yet. This goes to checkpoint 2.

### 5.7 Audio

- **Amps:** 2 × MAX98357A on I2S0 (1.8 V; VIH 1.3 V so compatible; no MCLK), powered from VSYS. One 3.3 V GPIO drives both SD_MODE pins: left amp through ~2 kΩ, right amp through 210 kΩ (datasheet Table 6).
- **Speakers:** 2 × 2-pin JST-SH.
- **Microphone:** a PDM MEMS mic on PDM0_M0 (1.8 V). The keyboard flex also has a mic; it stays unused, as on BBQ20KBD.

### 5.8 Storage

microSD push-push socket on SDMMC: 22 Ω on CLK, ESD on all lines, card-detect to GPIO0_A4 with a 100 kΩ pull-up to VCCIO_FLASH, and an optional SD power P-FET on SD_PWR_ON with a 0 Ω bypass (as on the IO board).

### 5.9 Keyboard interface (draft FFC, identical on both boards)

| FFC pin | Signal | Carrier side | Board B side |
|---|---|---|---|
| 1 | GND | | |
| 2 | +5V_KBD | VCC5V0 via switch | AP2112K-3.3 input |
| 3 | +5V_KBD | | |
| 4 | GND | (guard next to D−) | |
| 5 | USB_D− | hub P3 | RP2040 USB_DM (27 Ω) |
| 6 | USB_D+ | hub P3 | RP2040 USB_DP (27 Ω) |
| 7 | GND | (guard next to D+) | |
| 8 | KBD_SDA | I2C6 (3.3 V) | RP2040 GPIO28 |
| 9 | KBD_SCL | I2C6 | RP2040 GPIO29 |
| 10 | KBD_INT# | GPIO0_D5 (PMU domain, can wake the SoC) | RP2040 GPIO0 (OD) |
| 11 | KBD_RESET# | GPIO4_A7 (OD) | RP2040 RUN (10 kΩ pull-up) |
| 12 | KBD_BOOT# | GPIO4_B5 (OD) | RP2040 QSPI_SS via 1 kΩ (BOOTSEL) |

- **Cable and connectors:** 0.5 mm pitch, 12 conductors. Connector: BXCONN FC-05A12P11H20 (bottom contact, flip-lock, C23398836) on both boards. Cable length and same-side vs opposite-side contacts are decided at checkpoint 3 from the placement.
- **Firmware:** i2c_puppet, board `bbq20kbd_breakout`. It can be flashed from Linux by holding BOOT# during RESET# (the RP2040 then appears as a USB drive). SWD pads on Board B as a fallback.
- **Voltage levels:** the RK3588S lines used are all on 3.3 V banks, so no translation is needed.

### 5.10 PCB stack-up and fab rules

- **Stack-up: JLCPCB JLC06121H-3313A**, 6 layers, **1.2 mm**, NP-155F, 1 oz outer / 0.5 oz inner (template data from JLCPCB's impedance-calculator API):
  `L1 Cu 35 µm | PP 3313 99.4 µm εr 4.1 | L2 | core 100 µm εr 4.36 | L3 | 3 × PP 7628 ≈ 639 µm εr 4.4 | L4 | core 100 µm | L5 | PP 3313 99.4 µm | L6`
- **Layer use:** SIG / GND / SIG / SIG / GND / SIG. Every routing layer is about 0.1 mm from a solid ground plane, and the two inner signal layers are 0.64 mm apart (low crosstalk).
- **Impedances** (90 Ω USB, 100 Ω MIPI, 85/100 Ω PCIe, 50 Ω RF) will be computed with JLCPCB's own calculator at checkpoint 2 and turned into KiCad net classes.
- **JLCPCB 6-layer rules** (capabilities page):
  - Track/space 0.09/0.09 mm (1 oz).
  - Via 0.15 mm drill / 0.25 mm pad (0.2 mm drill preferred).
  - Via-in-pad, plated over filled, is free and the default on 6-layer.
  - No HASL on 6-layer; ENIG is available.
  - Impedance tolerance ±10 %.
  - Board thickness 0.4–2.0 mm for FR-4.

### 5.11 Linux driver check (mainline 7.3-rc7 source)

| Device | Mainline driver | Status |
|---|---|---|
| TPS25751 PD controller | `drivers/usb/typec/tipd/core.c` | only `ti,tps25750` is listed; TPS25751 **UNVERIFIED** (not needed for charging) |
| MAX17055 fuel gauge | `max17042_battery.c` | present (current, average current, charge counter) |
| ST7703 panel | `panel-sitronix-st7703.c` | present; **this panel needs a new init descriptor** |
| GT911 touch | `goodix.c` | present |
| MAX98357A amp | `max98357a.c` | present |
| HT8563 RTC (PCF8563-class) | `rtc-pcf8563.c` | present; HT8563 register compatibility **UNVERIFIED** |
| AP6275P (BCM43752 PCIe) | `brcmfmac` | present |
| USB2514B hub | `usb251xb.c` (optional, only for SMBus config) | present |
| BQ25713 charger | none needed (owned by the TPS25751) | n/a |

### 5.12 Early mechanical feasibility (preliminary, refined at checkpoint 3)

- **Area:** estimated component area is about 6,100 mm² across both sides, against 2 × 6,175 mm² at 95 × 65 mm. That looks feasible with double-sided assembly. Routing density around the 300 DF40 contacts is the limiting factor.
- **Height:** the CM5 stack is 1.5 mm plus module PCB and components (module height **UNVERIFIED**, to be measured from Radxa's STEP), so probably about 4 mm above the board. Under the board, the M.2 module plus socket adds about 3–4.5 mm depending on socket height. Expect **about 8.5–9.5 mm** assembled; you accepted about 9 mm (Q11).
- **Enclosure with the battery beside the board:** board (95 × 65) and battery (85 × 65) stacked along the device length gives roughly 95 × 135 mm behind the display (84 × 86 mm module) plus keyboard. The front face is about 95 × 150 mm and the depth about 15 mm (board ~9 + display 3.8 + walls). With the battery *under* the board instead, the footprint shrinks to about 95 × 110 mm but the depth grows to about 23 mm.

---

## 6. Block diagram

![Block diagram](block_diagram.svg)

## 7. Power tree, power budget, worst-case current, runtime

![Power tree](power_tree.svg)

<!--POWER_TABLE-->

**Battery current** (includes 2 % for BATFET, connector and trace losses):

<!--BATTERY_TABLE-->

**Worst case is about 9.3 A at 3.7 V (9.8 A at 3.5 V), not about 5 A.** It counts every load at its maximum at once: CPU+GPU+NPU at 12 W, both USB-A at 500 mA, LTE at 23 dBm, Wi-Fi peak TX, both speakers flat-out, backlight 100 %. With the bigger charger (Q2) nothing caps it any more, so the battery path is sized for it:

- **Connector:** 9-pin Micro-Lock Plus, 4 contacts per polarity = 12 A at 3.0 A per contact (decision Q3).
- **Pack PCM:** ≥12 A (decision Q4).
- **Battery FET, sense resistors, copper:** 12 A. IPC-2221 gives about 9.3 mm of 1 oz outer copper for 12 A at a 10 °C rise, so this will be pours on several layers (sized at checkpoint 4).
- **Path loss (estimate; part values come at checkpoint 2):** connector, battery FET and the two sense resistors add up to roughly 25–35 mΩ. That's about 0.4–0.6 W at a realistic 4 A, and 3.5–5 W only during a 12 A peak.
- **PROCHOT#** from the BQ25713 still lets Linux shed load if battery current stays high, but it's no longer what keeps the hardware safe.

**Runtime** (18.5 Wh nominal, ~17.6 Wh usable):

| Use | Power from VSYS | Runtime |
|---|---|---|
| Idle desktop / terminal, Wi-Fi associated, LTE idle, display 50 % | ≈ 3.6–4.4 W (estimate) | **≈ 4–5 h** |
| Light use (light column) | 5.1 W | **≈ 3.4 h** |
| Realistic heavy (heavy column) | 13.9 W | **≈ 1.3 h** |
| Suspend to RAM (RK3588 deep sleep, LTE in DRX sleep 3.3 mA, Wi-Fi off) | ≈ 0.15–0.4 W (**UNVERIFIED**, no Radxa figure) | **≈ 2–5 days** |

**Suspend notes:**
- The keyboard RP2040 draws about 30 mA unless the firmware uses dormant mode. i2c_puppet doesn't today; this is a firmware task.
- USB-A VBUS and the 5 V boost can be dropped in suspend through GPIO0_C2, but then the keyboard can't wake the device.
- **Storage:** the BQ25713 has no ship mode. The pack's PCM, or unplugging the battery, covers long-term storage.

---

## 8. CM5 pin budget

Every CM5 pin used, what it connects to, its I/O voltage, and the source. Machine-readable copy: `pin_budget.csv`.
Source tags: **PX** = Radxa CM5 V2.21 pinout xlsx (sheet U13-A / U13-B / J1). **CM5 pN** / **IO pN** = Radxa CM5 V2.21 / IO V2.2 schematic page. **DOC** = Radxa docs. Other datasheets are named.

<!--PIN_TABLE-->

**Deliberately unconnected pins** (`pin_budget_nc.csv`):

<!--PIN_NC_TABLE-->

---

## 9. Key parts shortlist (LCSC / JLCPCB, stock checked 14 Oct 2026)

All are extended-library parts; nothing here is in the basic library. Full list in `parts_shortlist.csv`.

<!--PARTS_TABLE-->

---

## 10. UNVERIFIED items so far

1. **CM5 outline:** 41 × 56 mm (DXF) vs 40 × 55 mm (docs). The larger one is used as the keep-out.
2. **CM5 assembled height** (module PCB + top components). To be measured from Radxa's STEP at checkpoint 3.
3. **DF40 pin-1 orientation** of each of the three receptacles. To be taken from Radxa's IO-board layout (Altium/PADS files) before the footprint is placed.
4. **J1-90 RTC_32K_SOC:** direction and purpose (left NC).
5. **Panel FPC:** pitch (0.5 mm assumed; drawing illegible), contact side and FPC thickness. The ST7703 init sequence for this exact panel must also come from the vendor.
6. **AP6275P:** firmware/driver in Radxa's CM5 BSP; whether PCIe AC capacitors are inside the module; the exact supporting passives (to be taken from the Ampak reference schematic).
7. **TPS25751 web tool:** whether it exposes the BQ25713 charge current (2.5 A), charge voltage (4.2 V), VSYSMIN and input limits, and whether it services the charger watchdog. The Linux patch-load fallback is verified only for the TPS25750.
8. **Micro-Lock Plus 2.0 mm** contact rating: 3.0 A per distributors, 3.4 A per LCSC. The Molex product spec 5055700001-PS wasn't obtained, so 3.0 A is used.
9. **Power estimates:** Radxa camera power, keyboard board power, SD card peak, CM5 suspend power.
10. **MAX17055:** datasheet not obtained (pin-out, sense resistor, I2C address, thermistor input).
11. **Unread datasheets:** M.2 socket heights (HOAUC), microSD/SIM socket footprints and card-detect polarity.
12. **EM060K:** USIM reference values and the complete M.2 pin map are in the downloaded doc but not yet extracted (checkpoint 2).
13. **BQ25713 battery FET:** a P-channel FET good for ≥12 A with gate capacitance under 5 nF is still to be found. The battery sense-resistor options (value vs. dissipation) also need checking.
14. **NTC window-comparator thresholds:** these depend on the pack's NTC (type and beta), which is unknown until you choose the battery.
15. **TPS25751 in Linux:** not listed in mainline `tipd`.

---

## 11. Decisions (answered 2026-10-14)

Also recorded in `docs/DECISIONS.md`.

| # | Topic | Decision |
|---|---|---|
| Q1 | Stylus | Capacitive touch + universal active stylus now; digitizer FPC reserved (USB hub P4, I2C, INT, RST, 3.3 V) |
| Q2 | Battery current | **Bigger charger:** BQ25713 + external battery FET (with TPS25751 as PD controller) |
| Q3 | Battery connector | **9-pin** Micro-Lock Plus 505575-0971 (4 × BAT+, 4 × GND, NTC = 12 A); first answer was 7-pin, revised after Q2 |
| Q4 | Pack PCM | **≥12 A** (first answer ≥10 A, revised after Q2) |
| Q5 | Display | DisplayModule DMKDI0400S0CA; you'll request the full drawing + init code |
| Q6 | LTE mounting | M.2 Key-B socket on the carrier, under the CM5 |
| Q7 | LTE link | **USB 2.0 + USB 3.0** |
| Q8 | Wi-Fi/BT | AMPAK AP6275P |
| Q9 | Sourcing | JLCPCB Global Sourcing allowed |
| Q10 | Board B licence | CERN-OHL-1.2 accepted |
| Q11 | Height | ~9 mm accepted |
| Q12 | PD EEPROM | Programming pads on the PD controller's I2C bus |
| Q13 | Fuel gauge | MAX17055 |

---

## 12. Sources

Local copies are under `research/dl/`; extracted text and crops are under `research/`.

- Radxa CM5 docs (source repo): https://github.com/radxa-docs/docs, `i18n/en/docusaurus-plugin-content-docs/current/som/cm/cm5/` (README.md, hardware/hw-interface.md, hardware/revisions.md, download.md, faq.md, accessories/*.md)
- Radxa CM5 V2.21 pinout: https://dl.radxa.com/cm5/v2210/radxa_cm5_v2210_pinout.xlsx
- Radxa CM5 V2.21 schematic: https://dl.radxa.com/cm5/v2210/radxa_cm5_v2210_schematic.pdf
- Radxa CM5 IO V2.2 schematic: https://dl.radxa.com/cm5/v2200/radxa_cm5_io_v2200_schematic.pdf
- Radxa CM5 2D DXF: https://dl.radxa.com/cm5/v2200/radxa_cm5_v2200_2d_dxf.zip · IO board 2D DXF: https://dl.radxa.com/cm5/v2200/radxa_cm5_io_board_v2200_2d_dxf.zip · CM5 3D: https://dl.radxa.com/cm5/radxa_cm5_pcba_3d.stp.zip
- Radxa CM5 IO board design files + BOM: https://github.com/radxa/radxa-cm-projects/tree/main/cm5/radxa-cm5-io-board
- BBQ20KBD hardware: https://github.com/solderparty/bbq20kbd_hw · i2c_puppet firmware: https://github.com/solderparty/i2c_puppet
- TI datasheets: https://www.ti.com/lit/ds/symlink/tps25750.pdf, tps25751.pdf, bq25713.pdf, bq25731.pdf, tps55288.pdf, tps63020.pdf, tps61169.pdf; BQ25792 / TPS61088 via LCSC's file server
- TPS25750 charger pairing: TI reference design TIDT295 (TPS25750 + BQ25731), TPS25750 product page (BQ25792 ≤45 W, BQ25731 above), via web search 2026-10-14
- Quectel EM060K Series & EM120K-GL Hardware Design V1.1: https://quectel.com/content/uploads/2024/02/Quectel_EM060K_SeriesEM120K-GL_Hardware_Design_V1.1.pdf
- DisplayModule DMKDI0400S0CA: https://www.displaymodule.com/products/products-4inch-720x720-tft-lcd-dmkdi0400s0ca (datasheet via the page's Shopify CDN link)
- AMPAK AP6275P datasheet (LCSC C2984107 file)
- MAX17048/MAX17049 datasheet Rev 1 (4/12): copy you supplied (`~/MAX17048.pdf`, alldatasheet.com mirror), kept as `research/dl/ds/MAX17048-MAX17049.pdf`
- MAX98357A datasheet (Adafruit mirror): https://cdn-shop.adafruit.com/product-files/3006/MAX98357A-MAX98357B.pdf
- JLCPCB capabilities: https://jlcpcb.com/capabilities/pcb-capabilities · stack-ups: JLCPCB impedance calculator (https://jlcpcb.com/pcb-impedance-calculator), template API `jlcTools/impedance/selectPageImpedanceDefaultTemplate`
- JLCPCB/LCSC stock: JLCPCB parts search API (`tools/jlc_search.py`)
- Molex Micro-Lock Plus ratings (distributors): element14 505575-0571 / -0671, RS 505575-0771 listings; LCSC lists 3.4 A for 505575-0771; drawing for 505575 via LCSC (C17385595)
