# Shopping list: parts bought separately, delivery to the EU

Everything the two boards need that JLCPCB does not assemble (the full list with what each part plugs into is
`docs/off_board_parts.md`). Searched 2026-10-22; prices and stock change, so check before ordering. "EU" below means
a shop that ships from inside the EU (no customs); for orders from outside the EU, VAT is charged at checkout up to
150 EUR (IOSS) and by customs above that.

Quantities are per device.

## 1. Modules

| # | Part | Exact type | Qty | Where (EU first) | Price seen | Notes |
|---|---|---|---|---|---|---|
| 1 | Compute module | **Orange Pi CM5** (RK3588S). Board A was redesigned for it on 2026-10-22 (D85); the Radxa CM5 no longer fits. Any RAM / eMMC size; the board you picked (16 GB / 32 GB eMMC, V1.1) is fine, V1.5 has the same connectors and holes | 1 | Amazon, the listing you found (4 GB 174.99 USD, 8 GB 226.99 USD, 16 GB 400.99 USD in your screenshot); [Tinytronics](https://www.tinytronics.nl/en/development-boards/single-board-computers/orange-pi-cm5-compute-module-5-rk3588s-16gb-32gb-emmc) (NL): 16 GB / 32 GB 174.25 EUR, [8 GB / 32 GB](https://www.tinytronics.nl/en/development-boards/single-board-computers/orange-pi-cm5-compute-module-5-rk3588s-8gb-32gb-emmc) 134.25 EUR incl. VAT, both **not in stock** on 2026-10-22 | see left | The module has **no Wi-Fi / Bluetooth** (Orange Pi user manual): Board A's AP6275P provides them. Tinytronics is much cheaper than Amazon: worth asking them for a restock date. |
| 2 | LTE modem | **Quectel EM060K-GL** (M.2 3042 key B; the global variant, not -NA / -EA) | 1 | [Amazon.de](https://www.amazon.de/Quectel-EM060K-GL-M-2-Formfaktor-Multi-Band-Positionierung/dp/B0CF8BJS8M) (in stock when searched); [Wivia](https://www.wivia.com/p/productid-638/quectel-em060k-gl) (price on request); [soyter.pl](https://soyter.pl/en/products/quectel-em060k-gl-lte-module-4605.html) (PL, sold out) | 127.67 EUR (Amazon.de) | |
| 3 | Display | **DisplayModule DMKDI0400S0CA**, 4.0" 720 x 720, ST7703, **with the capacitive touch panel (GT911)** | 1 | [DisplayModule](https://www.displaymodule.com/products/products-4inch-720x720-tft-lcd-dmkdi0400s0ca) | 59 USD; factory lead time ~3 weeks | Their pages disagree on touch: the English page lists none, the [French page](https://www.displaymodule.com/fr/products/products-4inch-720x720-tft-lcd-dmkdi0400s0ca) lists GT911. Order the touch version explicitly, and ask for the full outline drawing and the init code (open items in REVIEW.md). |
| 4 | Rear camera | **Radxa Camera 13M 214** (IMX214, 31-pin 0.3 mm FPC) with Radxa's 31-pin 0.3 mm cable | 1 | Radxa partners ([product page](https://radxa.com/products/accessories/camera-13m-214)); no EU shop found; outside the EU [Evelta](https://evelta.com/13m-imx214-auto-focus-camera-module-with-ffc-cable-radxa/) (India, "with FFC cable") | 1,239 INR (Evelta) | The design expects a 31p-to-31p, opposite-side, ~150 mm cable; confirm it is the one in the box. |
| 5 | Front camera | **Radxa Camera 8M 219** (IMX219) | 1 | [Tinytronics](https://www.tinytronics.nl/nl/sensoren/optisch/camera's-en-scanners/radxa-camera-8m-219-imx219) (NL, in stock when searched) | 17.50 EUR | Its own cable is 15p-to-15p; you need the next line. |
| 6 | Front camera cable | Radxa **31-pin 0.3 mm to 15-pin 1.0 mm, same side** (sold for the ROCK 5) | 1 | [Tinytronics](https://www.tinytronics.nl/nl/kabels-en-connectoren/kabels-en-adapters/ffc/radxa-camera-fpc-kabel-voor-camera-8m-219-met-rock-5) (NL) | 2.00 EUR excl. VAT; 2-4 weeks | Board A's CAM-B connector is the 31-pin one (D23). |
| 7 | Keyboard | **BlackBerry Classic (Q20, SQC100) keyboard assembly with its flex** (the flex ends in the 40-pin board-to-board plug), white number keys | 1 | Phone-parts sellers: [eBay](https://www.ebay.com/itm/227022540733) ("keypad keyboard buttons with flex cable"), [AliExpress search](https://www.aliexpress.com/w/wholesale-blackberry-classic-q20.html) | a few EUR to ~20 USD | Not a bare "keyboard flex cable": that is the ribbon alone. Solder Party's ready board (BBQ20KBD) is sold out everywhere. Check the photos for the trackpad and the 40-pin plug. |

## 2. Antennas

| # | Part | Exact type | Qty | Where | Price seen | Notes |
|---|---|---|---|---|---|---|
| 8 | LTE antennas | Flexible LTE antenna with an **MHF4 (IPEX4) plug**, covering 698-2700 MHz or wider | 2 (main + diversity/GNSS) | [Sixfab: Quectel 5G/LTE ultra-wideband FPC, MHF4, 200 mm](https://sixfab.com/product/5glte-ultra-wideband-fpc-antenna-mhf4-plug-200mm/) (~600-6000 MHz, lists the EM060K-GL) | 8 USD each | The EM060K-GL's two antenna sockets are 2 x 2 mm M.2 RF receptacles (Quectel HD 5.4), the MHF4 size; U.FL (MHF1) plugs do **not** fit. Avoid kits that start at 824 MHz, e.g. the [Seeed 4G kit](https://openelab.io/de/products/seeed-studio-4g-antenna-kit-m2-mhf4) (EU shop): they miss Europe's 700 / 800 MHz bands (B28, B20). |
| 9 | Wi-Fi / BT antennas | 2.4 / 5 GHz flexible antenna with a **U.FL (MHF1)** plug, e.g. **Molex 1461530100** (100 mm cable) | 2 | Mouser EU ([Molex balanced flex antennas](https://www.mouser.it/molex-flex-pcb-antennas)) | | Stick-on, inside a non-metal case, away from the battery and the display frame. |

## 3. Power

| # | Part | Exact type | Qty | Where | Notes |
|---|---|---|---|---|---|
| 10 | Battery pack | **Custom 1S Li-ion / LiPo pack**: 3.7 V, 4.20 V charge, 5000 mAh, about 8 x 65 x 85 mm; protection circuit **>= 12 A continuous** (trip >= 15 A), over-discharge cut-off >= 2.8 V; **10 kOhm NTC, B 3435** on the cells; leads <= 80 mm ending in a **Molex 505570-0901** plug wired pins 1-4 BAT+, 5-8 BAT-, 9 NTC (decision C2-1) | 1 | Custom-pack makers that ship internationally: [lipolbattery.com](https://www.lipolbattery.com/LiPo-Battery-5000mAh+.html), [DNK Power](https://www.dnkpower.com/products/3-7v-5000mah-lipo-battery/), [VTC Batt](https://vtcbatt.com/3-7v-5000mah-lipo-battery/), [lipobatteries.net](https://www.lipobatteries.net/lipo-batteries-5000mah/) | No shop stocks this exact pack: off-the-shelf 5000 mAh packs have 2-6 A protection, too little for the 9.8 A worst case. Ask for IEC 62133 / UN38.3 papers; lithium shipping to the EU is slower (no plain air mail). Send them this row. **For bring-up (2026-11-03):** a plain 105080 cell (3.7 V, 5000 mAh, 10 x 50 x 80 mm) from [accessoires-energie.com](https://accessoires-energie.com/en/products/batterie-105080-li-po-3-7v-5000mah) (Nice, France, EUR 27.90; C rating not stated, may be 1C), with the 15 A protection board, the NTC and the Molex lead; bring-up draws about 1-3 A, so no full-load tests on it. The 3C Keepbatt 105080 (batteryzone) would not check out for our delivery address; Amazon B0DP4JSFDF was out of stock; the final pack: quote from lithium-polymer-akkus.de (LP954896 class). |
| 11 | Battery lead (if the pack maker does not fit the plug) | Molex **505570-0901** housing (Micro-Lock Plus 2.00 mm, 9 circuits) + 9 **Micro-Lock Plus 2.0 pre-crimped leads**, 24 AWG, 75 mm, tin, socket on one end: 4 x red **2175012111** (pins 1-4 BAT+), 5 x black **2175011111** (pins 5-8 BAT-, pin 9 NTC: mark it). No crimp tool needed (Molex 2002180800 is about EUR 451). UNVERIFIED: the Digi-Key pages give only the series, not the terminal number; check that the drawing says 505572 / mates with 505570. | 2 housings + 5 red + 6 black | [Digi-Key](https://www.digikey.gr/en/products/result?keywords=2175011111) | EUR 0.36 / 0.95 / 0.95 on 2026-11-03 |
| 12 | USB-C charger | USB PD charger whose label lists **12 V 3 A** | 1 | any | The board asks for 5 / 9 / 12 V. Without a 12 V profile it charges at 9 V (27 W) instead of 36 W. Most chargers list 5 / 9 / 15 / 20 V only. |

## 4. Cables and small parts

| # | Part | Exact type | Qty | Where | Notes |
|---|---|---|---|---|---|
| 13 | Board A to Board B cable | FFC, **12 contacts, 0.5 mm pitch, ~50 mm, contacts on opposite sides**, e.g. **Molex 0151200120** (Premo-Flex, 50.8 mm) | 2 (one spare) | [Digi-Key](https://www.digikey.ch/en/products/detail/molex/0151200120/22512032) (EU sites) | Molex 15166-0119 ([Distrelec](https://www.distrelec.nl/en/molex-premo-flex-series-ffc-ribbon-cable-12-way-5mm-pitch-50mm-length-molex-15166-0119/p/30494215)) is the same-side version: not this one. |
| 14 | Speakers | **Ole Wolff OWS-091630W50A-8**: 16 x 9 x 3 mm, 8 ohm, 1.0 W nom / 1.2 W max, F0 950 Hz in a 1 cc cavity; red/black twisted leads 50 +/- 5 mm, ends stripped 1.0 mm (datasheet dated 02-08-2024) | 2 (+1 spare) | [Digi-Key 3949-OWS-091630W50A-8-ND](https://www.digikey.gr/en/products/result?keywords=OWS-091630W50A-8) | EUR 1.88 on 2026-11-03, **0 in stock, 7 weeks lead time**. The amplifiers give about 0.8 W per channel into 8 ohm, inside its 1.0 W rating. Each needs about 1 cc of sealed volume behind it in the enclosure. Wire-ended: see 17a. |
| 15 | Screws | M2.5 x 3-5 mm (4, CM5 onto its standoffs; length = the module's PCB thickness (about 1.6 mm) + up to 1.5 mm, measure it); M2 x 3 mm (1, LTE card); M2 (4, Board A) and M2.5 (2, Board B) for the enclosure | as listed | an M2 / M2.5 assortment box (Amazon.de, any hardware shop) | |
| 16 | Heat spreader | thermal pad (1-1.5 mm, to suit the enclosure) + aluminium plate from the CM5 to the display frame | 1 | Amazon.de / hardware shop | For bench testing, any small heatsink with a thermal pad on the RK3588S works. |
| 17 | microSD card, nano-SIM | your own | 1 + 1 | | |
| 17a | Speaker leads | 2 x **JST SHR-02V-S** housing + 2 x **JST ASSHSSH28K152** (one 28 AWG wire, 152 mm, an SH socket crimped on each end), per device. Cut each lead in half: two 76 mm pigtails, each with a socket. Push both into one housing, then solder and heat-shrink the bare ends to the speaker wires: red to pin 1 (SPK_x_P), black to pin 2 (SPK_x_N). The pigtails are all black, so mark pin 1 before splicing. | 2 + 2 (buy 5 + 4) | [Digi-Key SHR-02V-S](https://www.digikey.gr/en/products/result?keywords=SHR-02V-S), [Digi-Key ASSHSSH28K152](https://www.digikey.gr/en/products/result?keywords=ASSHSSH28K) | EUR 0.10 / 0.46 on 2026-11-03. J801 / J802 open to the board edge (D108). No crimp tool needed. |
| 17b | Stylus (optional) | a capacitive stylus: disc-tip (works on any capacitive screen) or a "universal active" fine-tip pen (likely, untested on this panel); no pressure | 1 | any | a pressure (EMR) pen needs a digitizer on J703 later: open question, see REVIEW / Q1 |
| 17c | Headphones (optional) | USB-A to 3.5 mm USB audio adapter, or Bluetooth headphones | 1 | any | the board has no headphone jack (a v2 idea) |

## 5. Tools for the first power-up

| # | Part | Why |
|---|---|---|
| 18 | 3.3 V USB-to-I2C adapter: the **CH341T USB-to-I2C/UART module** you picked (2-pack, jumpers on 3.3 V and I2C), or an FT232H board + probe clips / pogo pins / thin wires | to write the TPS25751 configuration into the M24512 EEPROM through its programming pads TP101 SDA (top), TP102 SCL, TP105 GND, TP103 write-protect to GND (REVIEW.md, at order time item 6) |
| 19 | 3.3 V USB-to-serial adapter that does 1.5 Mbaud: the second CH341T of the pack in UART mode (up to 2 Mbit/s), or a CP2102N / FT232R | the CM5's debug console on the debug UART pads TP301 / TP302 / TP303 (the module's UART is 1.8 V; Board A translates it to 3.3 V at the pads, D90) |
| 20 | Current-limited bench power supply | first power-up without the battery |

Not on this list because JLCPCB fits them: every part in `fab/board_a/BOM.csv` and `fab/board_b/BOM.csv`, including the
CM5 connectors, the M.2 socket, the battery and FPC connectors and the standoffs.
