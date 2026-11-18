| Function | Part | LCSC | JLC stock (14 Oct 2026) | Note |
|---|---|---|---|---|
| CM5 B2B receptacle x3 | Hirose DF40C-100DS-0.4V(51) | C597931 | 33535 | 1.5 mm mated height with the CM5 DF40C-100DP plugs; same part as Radxa IO board |
| USB-C PD sink controller | TI TPS25751DREFR | C30169739 | 5713 | D variant (WQFN-38); TI-listed integrated control of BQ25713; boots from >= 36 KB EEPROM at 0x50 |
| PD config EEPROM (>= 36 KB) | 24C512-class 64 KB (part TBD at checkpoint 2) | - | - | TPS25751 DS: EEPROM at least 36 kB at 7-bit 0x50; programming pads (decision Q12) |
| NVDC buck-boost charge controller | TI BQ25713RSNR | C2878935 | 3254 | external FETs: 4 x N-ch switching + P-ch BATFET (sized >= 12 A), RSR/RAC sense resistors; PROCHOT# output |
| Fuel gauge (current sensing) | ADI MAX17055ETB+T | C2976422 | 6107 | TDFN-10; mainline max17042_battery; datasheet not yet obtained (UNVERIFIED pin-out/sense resistor) |
| CM5 supply 4.8 V boost | TI TPS61088RHLR | C87357 | 9348 | 10 A switch; VOUT 4.5-12.6 V; standalone (no I2C) |
| 5 V USB/keyboard boost | TI TPS61089RNRR | C165129 | 11137 | 7 A switch, 2 x 2.5 mm |
| LTE 3.7 V and AUX 3.3 V buck-boost (x2) | TI TPS63020DSJR | C15483 | 26202 | 4 A switch; about 2 A in boost mode |
| Backlight LED boost | TI TPS61169DCKR | C71045 | 23247 | 38 V OVP, PWM dimming on CTRL |
| USB-A VBUS current-limited switch x2 (+1 keyboard) | TI TPS2553DBVR-1 / Silergy SY6280AAC | C111738 / C55136 | 11974 | adjustable current limit, set to about 0.6 A |
| USB 2.0 hub, 4 port | Microchip USB2514B-AEZC-TR | C16251 | 15399 | MTT, per-port power control; alt: Terminus FE1.1S-BQFN24B C6776948 (Radxa uses it) |
| Wi-Fi 6 / BT 5 module | AMPAK AP6275P | C2984107 | 494 | PCIe Wi-Fi (BCM43752) + UART BT; VDDIO 1.8 V only; needs 37.4 MHz crystal, 32.768 kHz LPO |
| 37.4 MHz crystal (AP6275P) | HELE X3S037400BA1H-Z | C254335 | 2731 | check load capacitance against AP6275P DS |
| RTC + 32.768 kHz clock out | HTCSEMI HT8563ARZ (PCF8563-class) | C2834465 | 1024 | HYM8563 (Radxa part) is out of stock |
| Class-D amp x2 | ADI MAX98357AETE+T | C910544 | 30911 | I2S, no MCLK, VIH 1.3 V |
| 3.3<->1.8 V translator (PCIe sideband) | Union UM3204H / TI TXS0104E | C620004 / C154926 | 3419 | Radxa uses UM3204 |
| M.2 Key-B socket (3042) | HOAUC HYCW11B-05NGFF-320B (3.05 mm) or lower variant | C41430834 | 854 | final height choice at checkpoint 3 |
| nano-SIM push-push socket | JXTCONN NANO SIM 7P 1.37H PUSH | C53207808 | 448 | no combo SIM+microSD tray stocked at JLCPCB |
| microSD push-push socket | SHOU HAN MICRO SD4.0 9P H1.4 PUSH | C53223918 | 983 | needs card-detect pin check |
| CAM-A FPC 31-pin 0.3 mm | Hirose FH35C-31S-0.3SHW(50) | C424662 | 4309 | same as Radxa IO board Camera 1; back-flip, 0.88 mm tall |
| Display FPC 30-pin 0.5 mm (flip-lock) | HanElectricity 05A15L30P (1.5 mm H) | C22459560 | 1858 | contact side must match panel FPC (UNVERIFIED) |
| Touch FPC 8-pin 0.5 mm | XUNPU FPC-05F-8PH15 | C2856815 | 22943 |  |
| Keyboard FFC 12-pin 0.5 mm (both boards) | BXCONN FC-05A12P11H20 (bottom contact, flip) | C23398836 | 3670 |  |
| Q20 keyboard connector (Board B) | Hirose BM20B(0.8)-40DS-0.4V(51) | C424543 | 8819 | same as BBQ20KBD |
| Keyboard MCU (Board B) | Raspberry Pi RP2040 | C2040 | 54524 |  |
| u.FL receptacle (Wi-Fi x2) | Hirose U.FL-R-SMT(10) | C434808 | 16958 |  |
| Battery connector (decision Q3) | Molex Micro-Lock Plus 2.0 mm 505575-0971 (9-pin: 4 BAT+, 4 GND, NTC) | C17385595 | 0 | 12 A at 3.0 A/contact (distributor rating; Molex PS 5055700001 not read); Global Sourcing |
