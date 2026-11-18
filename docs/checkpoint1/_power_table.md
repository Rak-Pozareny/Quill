| Load | Rail | Worst W | Heavy W | Light W | Converter (η) | Worst from VSYS | Heavy from VSYS | Light from VSYS | Basis |
|---|---|---|---|---|---|---|---|---|---|
| CM5 module (SoC, RAM, eMMC, PMIC) | CM5_VIN 4.8 V | 12.00 | 8.00 | 3.00 | TPS61088 boost (0.92) | 13.04 | 8.70 | 3.26 | Radxa: typ 2 A @ 4 V (8 W), recommended supply 4 V/3 A (12 W) [DOC README] |
| CM5 3V3_S3 / 1V8_S0 carrier loads (SD card 0.66 W, panel logic 0.18 W, touch 0.07 W, pull-ups) | via CM5 regulators | 1.10 | 0.40 | 0.20 | TPS61088 + on-module regulators (0.83) | 1.33 | 0.48 | 0.24 | SD 200 mA peak (estimate), panel IDD 56 mA max [panel DS 6.2] |
| LTE EM060K-GL | VCC_LTE 3.7 V | 3.96 | 2.00 | 0.08 | TPS63020 buck-boost (0.90) | 4.40 | 2.22 | 0.09 | Max listed data-transfer current 1.07 A @ 23 dBm (LTE B30); idle 21 mA [EM060K HD V1.1 Table 45]. Quectel PSU guideline is 3 A cont./4 A peak. |
| Wi-Fi/BT AP6275P | VCC3V3_AUX 3.3 V | 3.96 | 0.50 | 0.30 | TPS63020 buck-boost (0.90) | 4.40 | 0.56 | 0.33 | VBAT peak 1200 mA @ 3.3 V [AP6275P DS] |
| USB hub USB2514B + CAM-B 3.3 V | VCC3V3_AUX 3.3 V | 0.60 | 0.35 | 0.30 | TPS63020 buck-boost (0.90) | 0.67 | 0.39 | 0.33 | estimate; UNVERIFIED until hub/camera datasheets read |
| USB-A x2 at 500 mA each | VCC5V0 5.1 V | 5.10 | 0.00 | 0.00 | TPS61089 boost (0.90) | 5.67 | 0.00 | 0.00 | USB 2.0 port limit 500 mA (hard-limited by switches) |
| Keyboard board (RP2040, trackpad, key backlight) | VCC5V0 5.1 V | 0.50 | 0.30 | 0.20 | TPS61089 boost (0.90) | 0.56 | 0.33 | 0.22 | estimate (BBQ20KBD-class), UNVERIFIED |
| CAM-A (4K camera, 5 V + 3.3 V pins) | VCC5V0 / 3V3 | 0.60 | 0.00 | 0.00 | TPS61089 boost (0.90) | 0.67 | 0.00 | 0.00 | estimate, UNVERIFIED (Radxa Camera 4K power not published) |
| Display backlight (12 LED, 18.6 V x 40 mA) | LED boost | 0.74 | 0.56 | 0.37 | TPS61169 LED boost (0.85) | 0.88 | 0.66 | 0.44 | panel DS 6.3 (100 % / 75 % / 50 %) |
| Speakers 2 x MAX98357A | VSYS | 1.60 | 0.40 | 0.10 | class-D (0.85) | 1.88 | 0.47 | 0.12 | about 0.8 W per channel into 8 ohm at 3.7 V (estimate, depends on speaker) |
| PD/charger/fuel gauge/RTC/LEDs/misc | various | 0.15 | 0.10 | 0.05 | - (1.00) | 0.15 | 0.10 | 0.05 | TPS25751, BQ25713 IQ, MAX17055, LEDs (estimate) |
| **Total** | | **30.3** | **12.6** | **4.6** | | **33.6** | **13.9** | **5.1** | |
