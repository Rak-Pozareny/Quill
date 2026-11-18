# cm5_carrier: parts to check in JLCPCB's placement preview

Every placed part with a pin 1 or a polarity (all but plain resistors, capacitors and inductors). The CPL rotation is KiCad's angle (bottom side: 180 - angle) plus the correction of the JLCKicadTools rule that matches the footprint name; a part without a rule is taken as drawn alike in both libraries. In the preview, pin 1 (or the polarity mark) of JLCPCB's footprint must sit on the pad marked pin 1 on the board; if it does not, turn the part there (or tell me the angle).

| Ref | Value | Footprint | LCSC | Side | KiCad angle | Correction | Rule | CPL rotation |
|---|---|---|---|---|---|---|---|---|
| C503 | 220uF 6.3V | CP_EIA-7343-15_Kemet-W | C129173 | bottom | 180 | +180 | `^CP_EIA-` | 180 |
| C504 | 220uF 6.3V | CP_EIA-7343-15_Kemet-W | C129173 | bottom | 180 | +180 | `^CP_EIA-` | 180 |
| D101 | TVS2200 | WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm | C42400188 | top | 90 | +270 | `^WSON-6-` | 0 |
| D301 | TPD4E05U06DQAR | USON-10_2.5x1.0mm_P0.5mm | C138714 | bottom | 180 | +270 | `^USON-10` | 270 |
| D302 | red | LED_0603_1608Metric | C2286 | top | 90 | +0 | none | 90 |
| D401 | TPD4E05U06DQAR | USON-10_2.5x1.0mm_P0.5mm | C138714 | bottom | 180 | +270 | `^USON-10` | 270 |
| D402 | TPD4E05U06DQAR | USON-10_2.5x1.0mm_P0.5mm | C138714 | bottom | -90 | +270 | `^USON-10` | 180 |
| D403 | TPD4E05U06DQAR | USON-10_2.5x1.0mm_P0.5mm | C138714 | bottom | -90 | +270 | `^USON-10` | 180 |
| D501 | red | LED_0603_1608Metric | C2286 | top | 90 | +0 | none | 90 |
| D502 | SMF5.0A | D_SOD-123F | C193402 | bottom | 90 | +0 | none | 90 |
| D503 | TPD4E05U06DQAR | USON-10_2.5x1.0mm_P0.5mm | C138714 | top | 90 | +270 | `^USON-10` | 0 |
| D701 | B5819W | D_SOD-123 | C64885 | top | 0 | +0 | none | 0 |
| D901 | TPD4E05U06DQAR | USON-10_2.5x1.0mm_P0.5mm | C138714 | bottom | 180 | +270 | `^USON-10` | 270 |
| D902 | TPD4E05U06DQAR | USON-10_2.5x1.0mm_P0.5mm | C138714 | top | 0 | +270 | `^USON-10` | 270 |
| D1001 | TPD4E05U06DQAR | USON-10_2.5x1.0mm_P0.5mm | C138714 | bottom | -90 | +270 | `^USON-10` | 180 |
| H301 | M2.5 x 1.5 standoff | CM5_Standoff_SMT_M2.5_L1.5 | C5221850 | top | 0 | +0 | none | 0 |
| H302 | M2.5 x 1.5 standoff | CM5_Standoff_SMT_M2.5_L1.5 | C5221850 | top | 0 | +0 | none | 0 |
| H303 | M2.5 x 1.5 standoff | CM5_Standoff_SMT_M2.5_L1.5 | C5221850 | top | 0 | +0 | none | 0 |
| H304 | M2.5 x 1.5 standoff | CM5_Standoff_SMT_M2.5_L1.5 | C5221850 | top | 0 | +0 | none | 0 |
| H501 | M.2 3042 standoff | M.2_SMT_Standoff_M2 | C2916319 | bottom | 180 | +0 | none | 0 |
| J101 | USB-C (USB 2.0, PD sink) | USB_C_Receptacle_HRO_TYPE-C-31-M-12 | C165948 | top | -90 | +0 | `^USB_C_Receptacle_HRO_TYPE-C-31-M-12` | 270 |
| J102 | Molex 505578-0971 | Molex_Micro-Lock_Plus_505578-0971_1x09_P2.00mm_Horizontal | C17389413 | top | 180 | +0 | none | 180 |
| J301 | DF40C-100DS-0.4V(51) (CM5 JP1) | OPi_CM5_DF40_JP1 | C597931 | top | 0 | +90 | `^OPi_CM5_DF40_JP[12]$` | 90 |
| J302 | DF40C-100DS-0.4V(51) (CM5 JP2) | OPi_CM5_DF40_JP2 | C597931 | top | 0 | +90 | `^OPi_CM5_DF40_JP[12]$` | 90 |
| J303 | DF40C-100DS-0.4V(51) (CM5 JP3) | OPi_CM5_DF40_JP3 | C597931 | top | 0 | +0 | none | 0 |
| J401 | USB-A port 1 | USB_A_HOAUC_HYCW236-USBA04-289B | C3034183 | top | 0 | +0 | none | 0 |
| J402 | USB-A port 2 | USB_A_HOAUC_HYCW236-USBA04-289B | C3034183 | top | 0 | +0 | none | 0 |
| J501 | M.2 Key-B socket (EM060K-GL) | M.2_Key-B_HOAUC_HYCW11B | C41430834 | bottom | 180 | +0 | none | 0 |
| J502 | nano-SIM | GCT_SIM8066-6-1-14-01-A | C3032925 | top | 90 | +0 | none | 90 |
| J601 | U.FL | U.FL_Hirose_U.FL-R-SMT-1_Vertical | C434808 | bottom | 180 | +90 | `^U\.FL_Hirose_U\.FL-R-SMT-1` | 90 |
| J602 | U.FL | U.FL_Hirose_U.FL-R-SMT-1_Vertical | C434808 | bottom | 180 | +90 | `^U\.FL_Hirose_U\.FL-R-SMT-1` | 90 |
| J701 | Display FPC 30P | FPC_0.5mm_30P_HDGC_0520-HX-30PWB | C3041205 | top | 90 | +0 | none | 90 |
| J702 | CTP FPC 8P | FPC_0.5mm_8P_XUNPU_FPC-05F-8PH15 | C2856815 | top | 90 | +0 | none | 90 |
| J703 | Digitizer FFC 12P | FPC_0.5mm_12P_BXCONN_FC-05A12P11H20 | C23398836 | top | 0 | +180 | `^FPC_0\.5mm_12P_BXCONN_FC-05A12P11H20` | 180 |
| J704 | CAM-A FH35C-31S | Hirose_FH35C-31S-0.3SHW | C424662 | top | -90 | +0 | none | 270 |
| J705 | CAM-B FH35C-31S | Hirose_FH35C-31S-0.3SHW | C424662 | top | -90 | +0 | none | 270 |
| J801 | Speaker L | JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal | C160402 | bottom | 90 | +0 | none | 90 |
| J802 | Speaker R | JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal | C160402 | bottom | 90 | +0 | none | 90 |
| J901 | DM3AT-SF-PEJM5 | microSD_HC_Hirose_DM3AT-SF-PEJM5 | C114218 | top | 90 | +0 | none | 90 |
| J1001 | Keyboard FFC 12P | FPC_0.5mm_12P_BXCONN_FC-05A12P11H20 | C23398836 | top | 0 | +180 | `^FPC_0\.5mm_12P_BXCONN_FC-05A12P11H20` | 180 |
| L401 | DLW21SN900SQ2L | L_CMC_Murata_DLW21SN | C97856 | bottom | -90 | +0 | none | 270 |
| Q101 | CSD17577Q3A (Q1 buck HS) | TI_VSONP-8_3.3x3.3mm_CSD17577Q3A | C201632 | bottom | 180 | +270 | `^TI_VSONP-8_` | 270 |
| Q102 | CSD17577Q3A (Q2 buck LS) | TI_VSONP-8_3.3x3.3mm_CSD17577Q3A | C201632 | bottom | 0 | +270 | `^TI_VSONP-8_` | 90 |
| Q103 | CSD17577Q3A (Q3 boost LS) | TI_VSONP-8_3.3x3.3mm_CSD17577Q3A | C201632 | bottom | 180 | +270 | `^TI_VSONP-8_` | 270 |
| Q104 | CSD17577Q3A (Q4 boost HS) | TI_VSONP-8_3.3x3.3mm_CSD17577Q3A | C201632 | bottom | 0 | +270 | `^TI_VSONP-8_` | 90 |
| Q105 | CSD25404Q3 (BATFET) | TI_VSON-CLIP-8_3.3x3.3mm_CSD25404Q3 | C2865523 | bottom | 0 | +0 | none | 180 |
| Q106 | 2N7002 | SOT-23 | C8545 | bottom | -90 | +180 | `^SOT-23(-\d)?$` | 90 |
| Q107 | AO3401A | SOT-23 | C15127 | bottom | 180 | +180 | `^SOT-23(-\d)?$` | 180 |
| Q108 | 2N7002 (Q_a) | SOT-23 | C8545 | bottom | 180 | +180 | `^SOT-23(-\d)?$` | 180 |
| Q501 | 2N7002 | SOT-23 | C8545 | top | 0 | +180 | `^SOT-23(-\d)?$` | 180 |
| Q502 | 2N7002 | SOT-23 | C8545 | bottom | -90 | +180 | `^SOT-23(-\d)?$` | 90 |
| SW301 | SKRTLAE010 POWER | SW_Alps_SKRTLAE010_JLC | C110293 | top | 90 | +0 | none | 90 |
| SW302 | SKRTLAE010 VOL+ | SW_Alps_SKRTLAE010_JLC | C110293 | top | 90 | +0 | none | 90 |
| SW303 | SKRTLAE010 VOL- | SW_Alps_SKRTLAE010_JLC | C110293 | top | 90 | +0 | none | 90 |
| SW304 | TS-1088C RESET | SW_SPST_TS-1088-xR020 | C455278 | top | 0 | +0 | none | 0 |
| SW305 | TS-1088C MASKROM | SW_SPST_TS-1088-xR020 | C455278 | top | 0 | +0 | none | 0 |
| SW306 | TS-1088C RECOVERY | SW_SPST_TS-1088-xR020 | C455278 | top | 0 | +0 | none | 0 |
| U101 | TPS25751DREFR | Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4 | C30169739 | bottom | 180 | +0 | none | 0 |
| U102 | M24512-RMN6TP | SOIC-8_3.9x4.9mm_P1.27mm | C79991 | bottom | 180 | +270 | `^SOIC-` | 270 |
| U103 | BQ25713RSNR | Texas_RSN_WQFN-32-1EP_4x4mm_P0.4mm_EP2.8x2.8mm | C2878935 | bottom | 0 | +0 | none | 180 |
| U104 | MAX17055ETB+T | Maxim_TDFN-10-1EP_2x2.5mm_P0.4mm_EP1.4x1.3mm | C2976422 | bottom | 180 | +0 | none | 0 |
| U105 | TLV7042DGKR | VSSOP-8_3x3mm_P0.65mm | C2760466 | bottom | 180 | +180 | `^VSSOP-8_` | 180 |
| U106 | XC6206P332MR | SOT-23-3 | C5446 | top | 90 | +180 | `^SOT-23(-\d)?$` | 270 |
| U201 | TPS61088RHLR | Texas_RHL0020A_VQFN-20-1EP_3.5x4.5mm_P0.5mm | C87357 | bottom | -90 | +0 | none | 270 |
| U202 | TPS61089RNRR | Texas_VQFN-RNR0011A-11 | C165129 | top | 0 | +0 | none | 0 |
| U203 | TPS63020DSJR | Texas_DSJ0014A_VSON-14-1EP_3x4mm_P0.5mm | C15483 | bottom | -90 | +0 | none | 270 |
| U204 | TPS63020DSJR | Texas_DSJ0014A_VSON-14-1EP_3x4mm_P0.5mm | C15483 | bottom | -90 | +0 | none | 270 |
| U301 | BM8563ESA | SOIC-8_3.9x4.9mm_P1.27mm | C269877 | top | 90 | +270 | `^SOIC-` | 0 |
| U302 | TXS0104EPWR | TSSOP-14_4.4x5mm_P0.65mm | C44955 | bottom | 180 | +270 | `^TSSOP-` | 270 |
| U401 | USB2514B-AEZC-TR | QFN-36-1EP_6x6mm_P0.5mm_EP3.7x3.7mm | C16251 | bottom | 180 | +270 | `^QFN-36-` | 270 |
| U402 | TPS2553DBVR | SOT-23-6 | C55266 | top | 0 | +180 | `^SOT-23(-\d)?$` | 180 |
| U403 | TPS2553DBVR | SOT-23-6 | C55266 | top | 0 | +180 | `^SOT-23(-\d)?$` | 180 |
| U601 | AP6275P | AMPAK_AP6275P | C2984107 | bottom | 90 | +0 | none | 90 |
| U701 | TPS22919DCKR | SOT-363_SC-70-6 | C2149796 | bottom | 180 | +180 | `^SOT-363` | 180 |
| U702 | TPS61169DCKR | SOT-353_SC-70-5 | C71045 | top | 0 | +180 | `^SOT-353` | 180 |
| U703 | TPS22919DCKR | SOT-363_SC-70-6 | C2149796 | bottom | 180 | +180 | `^SOT-363` | 180 |
| U801 | MAX98357AETE+T (L) | TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm | C910544 | bottom | 180 | +270 | `^TQFN-16-` | 270 |
| U802 | MAX98357AETE+T (R) | TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm | C910544 | bottom | 180 | +270 | `^TQFN-16-` | 270 |
| U803 | SPH0641LU4H-1 | Knowles_LGA-5_3.5x2.65mm | C2879853 | top | 0 | +0 | none | 0 |
| U1001 | TPS2553DBVR | SOT-23-6 | C55266 | bottom | -90 | +180 | `^SOT-23(-\d)?$` | 90 |
| Y301 | 32.768 kHz 7 pF | Crystal_SMD_3215-2Pin_3.2x1.5mm | C48615 | top | 90 | +0 | none | 90 |
| Y401 | 24 MHz 12 pF | Crystal_SMD_3225-4Pin_3.2x2.5mm | C70590 | bottom | -90 | +0 | none | 270 |
| Y601 | 37.4 MHz 16 pF | Crystal_SMD_3225-4Pin_3.2x2.5mm | C2687892 | bottom | -90 | +0 | none | 270 |
