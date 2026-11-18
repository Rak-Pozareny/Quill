"""Specific (non-generic) parts: JLCPCB/LCSC number, MPN, manufacturer, footprint.
Stock figures are from the JLCPCB parts API on the date in the comment; footprints marked cm5h: are
project footprints drawn from the cited datasheet at checkpoint 3."""

# key: (lcsc, mpn, manufacturer, footprint, note)
PARTS = {
    # ---- power input / charger (JLC stock 2026-10-15)
    'USBC': ('C165948', 'TYPE-C-31-M-12', 'Korean Hroparts', 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12', ''),
    'TPS25751D': ('C30169739', 'TPS25751DREFR', 'TI', 'Package_DFN_QFN:Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4', ''),
    # D113: ElecSuper's second source (pin-for-pin, same DFN2020-6L land); TI's C523793 had 4 in stock on 2026-10-31
    'TVS2200': ('C42400188', 'ESTVS2200DRVR', 'ElecSuper', 'Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm', ''),
    'M24512': ('C79991', 'M24512-RMN6TP', 'STMicroelectronics', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', ''),
    'BQ25713': ('C2878935', 'BQ25713RSNR', 'TI', 'Package_DFN_QFN:Texas_RSN_WQFN-32-1EP_4x4mm_P0.4mm_EP2.8x2.8mm', ''),
    'CSD17577Q3A': ('C201632', 'CSD17577Q3A', 'TI', 'cm5h:TI_VSONP-8_3.3x3.3mm_CSD17577Q3A', ''),
    'CSD25404Q3': ('C2865523', 'CSD25404Q3', 'TI', 'cm5h:TI_VSON-CLIP-8_3.3x3.3mm_CSD25404Q3', ''),
    'L_2u2_14A': ('C1329579', 'SRP7028A-2R2M', 'Bourns', 'Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm', 'Isat 14 A, Irms 8 A, 18 mOhm, 2.8 mm'),
    'R_10m_2512': ('C5375464', 'HoYLR2512-3W-10mR-1%', 'Milliohm', 'Resistor_SMD:R_2512_6332Metric', '3 W'),
    'R_4m_2512': ('C2904236', 'HoJLR2512-3W-4mR-1%', 'Milliohm', 'Resistor_SMD:R_2512_6332Metric', '3 W'),
    'MAX17055': ('C2976422', 'MAX17055ETB+T', 'Analog Devices (Maxim)', 'cm5h:Maxim_TDFN-10-1EP_2x2.5mm_P0.4mm_EP1.4x1.3mm', 'land per Maxim 90-100007'),
    'BATT_CONN': ('C17389413', '5055780971', 'Molex', 'cm5h:Molex_Micro-Lock_Plus_505578-0971_1x09_P2.00mm_Horizontal',
                  'right angle SMT, 5.9 mm high, mates 505570-0901; JLC stock 50 (2026-10-17)'),
    'TLV7042': ('C2760466', 'TLV7042DGKR', 'TI', 'Package_SO:VSSOP-8_3x3mm_P0.65mm', ''),
    'XC6206_33': ('C5446', 'XC6206P332MR-G', 'Torex', 'Package_TO_SOT_SMD:SOT-23-3', ''),
    '2N7002': ('C8545', '2N7002', 'Changjiang', 'Package_TO_SOT_SMD:SOT-23', 'JLC basic; verify at BOM step'),
    'PMOS_SOT23': ('C15127', 'AO3401A', 'Alpha & Omega', 'Package_TO_SOT_SMD:SOT-23', 'JLC basic; verify at BOM step'),
    # ---- rails
    'TPS61088': ('C87357', 'TPS61088RHLR', 'TI', 'cm5h:Texas_RHL0020A_VQFN-20-1EP_3.5x4.5mm_P0.5mm', ''),
    'TPS61089': ('C165129', 'TPS61089RNRR', 'TI', 'Package_DFN_QFN:Texas_VQFN-RNR0011A-11', ''),
    'TPS63020': ('C15483', 'TPS63020DSJR', 'TI', 'cm5h:Texas_DSJ0014A_VSON-14-1EP_3x4mm_P0.5mm', ''),
    'TPS61169': ('C71045', 'TPS61169DCKR', 'TI', 'Package_TO_SOT_SMD:SOT-353_SC-70-5', ''),
    'TPS2553': ('C55266', 'TPS2553DBVR', 'TI', 'Package_TO_SOT_SMD:SOT-23-6', ''),
    'TPS22919': ('C2149796', 'TPS22919DCKR', 'TI', 'Package_TO_SOT_SMD:SOT-363_SC-70-6', ''),
    'L_1u5_7A': ('C98360', 'WPN4020H1R5MT', 'Sunlord', 'cm5h:L_Sunlord_WPN4020', 'Isat 7.7 A, Irms 5.2 A, 36 mOhm max, 4x4x2 mm'),
    'L_4u7_1A': ('C19398', 'SWPA3015S4R7MT', 'Sunlord', 'Inductor_SMD:L_Sunlord_SWPA3015S', 'Isat 1.4 A, Irms 1.09 A (JLC attributes; datasheet is image-only)'),
    'SCHOTTKY_40V_1A': ('C64885', 'B5819W', 'MDD', 'Diode_SMD:D_SOD-123', '40 V 1 A'),
    'TPD4E05U06': ('C138714', 'TPD4E05U06DQAR', 'TI', 'Package_SON:USON-10_2.5x1.0mm_P0.5mm', '4-ch ESD, 0.5 pF'),
    'CMC_90R': ('C97856', 'DLW21SN900SQ2L', 'Murata', 'cm5h:L_CMC_Murata_DLW21SN',
                '90 Ohm @100 MHz, 330 mA; windings 1-2 / 4-3 per Murata JEFL243C-0003V-01'),
    'USB2514B': ('C16251', 'USB2514B-AEZC-TR', 'Microchip', 'Package_DFN_QFN:QFN-36-1EP_6x6mm_P0.5mm_EP3.7x3.7mm', ''),
    'USBA_MID': ('C3034183', 'HYCW236-USBA04-289B', 'HOAUC', 'cm5h:USB_A_HOAUC_HYCW236-USBA04-289B', 'mid-mount for 1.2 mm PCB, 4.33 mm above board'),
    'M2_B': ('C41430834', 'HYCW11B-05NGFF-320B', 'HOAUC', 'cm5h:M.2_Key-B_HOAUC_HYCW11B', 'M.2 Key-B socket H3.2, module bottom 1.25 mm'),
    'M2_NUT': ('C2916319', 'SMTSO2010CTJ', 'Sinhoo', 'cm5h:M.2_SMT_Standoff_M2',
               'M2 x 1.0 mm SMT nut (no 1.25 mm part stocked; module end sits 0.25 mm low, screw preloads it)'),
    'CM5_NUT': ('C5221850', 'SMTSOM2.515BTR', 'YIYUAN', 'cm5h:CM5_Standoff_SMT_M2.5_L1.5',
                'M2.5 x 1.5 mm SMT standoff (= DF40 1.5 mm stack), CM5 fixing screws from the module top'),
    'NANOSIM': ('C3032925', 'SIM8066-6-1-14-01-A', 'GCT', 'cm5h:GCT_SIM8066-6-1-14-01-A', 'push-push, card detect'),
    'SMF5V0A': ('C193402', 'SMF5.0A', 'MDD', 'Diode_SMD:D_SOD-123F', 'VRWM 5.0 V, VBR 6.4 V, 200 W (Quectel: 5.1 V TVS >= 0.5 W)'),
    'POSCAP_220U': ('C129173', '6TPE220MI', 'Panasonic', 'Capacitor_Tantalum_SMD:CP_EIA-7343-15_Kemet-W', '220 uF 6.3 V 18 mOhm; footprint/height checked at checkpoint 3'),
    'AP6275P': ('C2984107', 'AP6275P', 'AMPAK', 'cm5h:AMPAK_AP6275P', ''),
    'L_2u2_WIFI': ('C279858', 'WPN252012H2R2MTY01', 'Sunlord', 'cm5h:L_Sunlord_WPN252012H', '2.2 uH 85 mOhm 2.1 A (Edge2 ref: 2.2 uH 2 A <= 80 mOhm)'),
    'FB_120R_2A': ('C14709', 'BLM18PG121SN1D', 'Murata', 'Inductor_SMD:L_0603_1608Metric', '120 Ohm @100 MHz, 2 A'),
    'FB_120R_0402': ('C85812', 'BLM15AG121SN1D', 'Murata', 'Inductor_SMD:L_0402_1005Metric', '120 Ohm @100 MHz, 550 mA'),
    'TXS0104E': ('C44955', 'TXS0104EPWR', 'TI', 'Package_SO:TSSOP-14_4.4x5mm_P0.65mm', ''),
    'UFL': ('C434808', 'U.FL-R-SMT(10)', 'Hirose', 'Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical', ''),
    'FPC30_DS': ('C3041205', '0520-HX-30PWB', 'HDGC', 'cm5h:FPC_0.5mm_30P_HDGC_0520-HX-30PWB', 'double-sided contacts, flip lock'),
    'FPC8': ('C2856815', 'FPC-05F-8PH15', 'XUNPU', 'cm5h:FPC_0.5mm_8P_XUNPU_FPC-05F-8PH15', ''),
    'FFC12': ('C23398836', 'FC-05A12P11H20', 'BXCONN', 'cm5h:FPC_0.5mm_12P_BXCONN_FC-05A12P11H20', 'bottom contact, flip lock'),
    'FH35C31': ('C424662', 'FH35C-31S-0.3SHW(50)', 'Hirose', 'cm5h:Hirose_FH35C-31S-0.3SHW', 'Radxa 31-pin camera connector (ROCK 5B J5002 pinout)'),
    'MAX98357A': ('C910544', 'MAX98357AETE+T', 'Analog Devices (Maxim)', 'Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm', ''),
    'JST_SH2': ('C160402', 'SM02B-SRSS-TB(LF)(SN)', 'JST', 'Connector_JST:JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal', ''),
    'SPH0641': ('C2879853', 'SPH0641LU4H-1', 'Knowles', 'Sensor_Audio:Knowles_LGA-5_3.5x2.65mm', 'PDM, bottom port'),
    'MICROSD': ('C114218', 'DM3AT-SF-PEJM5', 'Hirose', 'Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5', 'push-push, card detect'),
    'SW_SIDE': ('C110293', 'SKRTLAE010', 'Alps Alpine', 'cm5h:SW_Alps_SKRTLAE010_JLC', 'side push'),
    'SW_TOP': ('C455278', 'TS-1088C-02026', 'XUNPU', 'Button_Switch_SMD:SW_SPST_TS-1088-xR020', 'top push 3.9x3x2 mm'),
    # ---- clocks
    'XTAL_32K_7PF': ('C48615', 'Q13FC13500002', 'Epson', 'Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm', 'CL 7 pF (BM8563 characterised at 8 pF)'),
    'XTAL_24M': ('C70590', 'X322524MOB4SI', 'YXC', 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm', 'CL 12 pF'),
    'XTAL_37M4': ('C2687892', 'E3SB37E0X0004E', 'Hosonic', 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm', 'CL 16 pF, +-10/+-10 ppm'),
    'BM8563': ('C269877', 'BM8563ESA', 'GATEMODE', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 'PCF8563-compatible'),
}


def part(key):
    lcsc, mpn, mfr, fp, note = PARTS[key]
    return dict(lcsc=lcsc, mpn=mpn, mfr=mfr, fp=fp, note=note)
