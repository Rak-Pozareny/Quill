# q20_keyboard: parts to check in JLCPCB's placement preview

Every placed part with a pin 1 or a polarity (all but plain resistors, capacitors and inductors). The CPL rotation is KiCad's angle (bottom side: 180 - angle) plus the correction of the JLCKicadTools rule that matches the footprint name; a part without a rule is taken as drawn alike in both libraries. In the preview, pin 1 (or the polarity mark) of JLCPCB's footprint must sit on the pad marked pin 1 on the board; if it does not, turn the part there (or tell me the angle).

| Ref | Value | Footprint | LCSC | Side | KiCad angle | Correction | Rule | CPL rotation |
|---|---|---|---|---|---|---|---|---|
| J101 | Carrier FFC 12P | FPC_0.5mm_12P_BXCONN_FC-05A12P11H20 | C23398836 | bottom | 180 | +180 | `^FPC_0\.5mm_12P_BXCONN_FC-05A12P11H20` | 180 |
| J201 | BM20B(0.8)-40DS-0.4V(51) | Hirose_BM20B_0.8_-40DS-0.4V | C424543 | top | 90 | +0 | none | 90 |
| Q101 | BSS138 | SOT-23 | C40912 | bottom | -90 | +180 | `^SOT-23(-\d)?$` | 90 |
| Q102 | BSS138 | SOT-23 | C40912 | bottom | -90 | +180 | `^SOT-23(-\d)?$` | 90 |
| Q103 | BSS138 | SOT-23 | C40912 | bottom | 180 | +180 | `^SOT-23(-\d)?$` | 180 |
| Q104 | BSS138 | SOT-23 | C40912 | bottom | 180 | +180 | `^SOT-23(-\d)?$` | 180 |
| Q201 | BSS138 | SOT-23 | C40912 | bottom | 0 | +180 | `^SOT-23(-\d)?$` | 0 |
| Q202 | BSS138 | SOT-23 | C40912 | bottom | 0 | +180 | `^SOT-23(-\d)?$` | 0 |
| Q203 | BSS138 | SOT-23 | C40912 | bottom | 0 | +180 | `^SOT-23(-\d)?$` | 0 |
| Q204 | BSS138 | SOT-23 | C40912 | bottom | 0 | +180 | `^SOT-23(-\d)?$` | 0 |
| Q205 | BSS138 | SOT-23 | C40912 | bottom | 0 | +180 | `^SOT-23(-\d)?$` | 0 |
| Q206 | BSS138 | SOT-23 | C40912 | bottom | 0 | +180 | `^SOT-23(-\d)?$` | 0 |
| U101 | AP2112K-3.3 | SOT-23-5 | C51118 | bottom | 180 | +180 | `^SOT-23(-\d)?$` | 180 |
| U102 | RP2040 | QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm | C2040 | bottom | 180 | +0 | none | 0 |
| U103 | W25Q16JVSSIQ | SOIC-8_5.3x5.3mm_P1.27mm | C131025 | bottom | 180 | +270 | `^SOIC-` | 270 |
| U104 | SN74LVC1G07DBVR | SOT-23-5 | C7829 | bottom | 180 | +180 | `^SOT-23(-\d)?$` | 180 |
| U201 | ME6212C18M5G | SOT-23-5 | C236669 | bottom | 180 | +180 | `^SOT-23(-\d)?$` | 180 |
| U202 | ME6212C28M5G | SOT-23-5 | C427596 | bottom | 180 | +180 | `^SOT-23(-\d)?$` | 180 |
| Y101 | 12 MHz 10 pF | Crystal_SMD_3225-4Pin_3.2x2.5mm | C20625731 | bottom | 0 | +0 | none | 180 |
