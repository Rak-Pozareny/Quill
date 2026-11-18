"""Board A sheets 1-2: power input/battery and power rails."""
from parts import part
import symbols


def P(g, key, sym, value, nets, prefix='U', status='', note='', sourcing='JLC'):
    p = part(key)
    return g.ic(sym, value, nets, p['fp'], lcsc=p['lcsc'], mpn=p['mpn'], mfr=p['mfr'], prefix=prefix,
                status=status, note=(note or p['note']), sourcing=sourcing)


def nmos(g, key, d, gte, s, value):
    S = g.sb.d.S
    return P(g, key, S['NMOS_SON8'], value, {'1': s, '2': s, '3': s, '4': gte, '5': d, '6': d, '7': d, '8': d, '9': d},
             prefix='Q')


def sot_nmos(g, d, gte, s, value='2N7002'):
    return P(g, '2N7002', 'Transistor_FET:2N7002', value, {'1': gte, '2': s, '3': d}, prefix='Q')


def sot_pmos(g, d, gte, s, value='AO3401A'):
    # AO3401A SOT-23: 1 G, 2 S, 3 D (same pin order as KiCad Transistor_FET:AO3401A)
    return P(g, 'PMOS_SOT23', 'Transistor_FET:AO3401A', value, {'1': gte, '2': s, '3': d}, prefix='Q')


# ============================================================================================ sheet 1
def sheet_power_in(d):
    sb = d.sheet('Power input, charger, battery', 'power_in.kicad_sch', paper='A3')
    S = d.S

    # ------------------------------------------------------------ USB-C receptacle + PD controller
    g = sb.group('USB-C receptacle and PD sink controller (TPS25751D)',
                 'Ref: TI SLVSH93A sec. 6.4 (recommended capacitance), 8.4.1 (ADCIN straps), Fig. 9-26 (application).\n'
                 'ADCIN1 = LDO_3V3 (decoded 7), ADCIN2 = GND (0) -> SafeMode dead-battery behaviour, I2C target index #1 = 0x20.\n'
                 'Patch + configuration load from the EEPROM at 0x50 on I2Cc. Source role disabled in the configuration (sink only).')
    P(g, 'USBC', 'Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C (USB 2.0, PD sink)',
      {'A1': 'GND', 'B1': 'GND', 'A12': 'GND', 'B12': 'GND', 'A4': 'VBUS_C', 'B4': 'VBUS_C', 'A9': 'VBUS_C', 'B9': 'VBUS_C',
       'A5': 'USBC_CC1', 'B5': 'USBC_CC2', 'A6': 'USBC_DP', 'B6': 'USBC_DP', 'A7': 'USBC_DN', 'B7': 'USBC_DN',
       'A8': None, 'B8': None, 'SH': 'GND'}, prefix='J')
    P(g, 'TVS2200', 'Power_Protection:TVS2200DRV', 'TVS2200', {'1': 'GND', '2': 'GND', '3': 'GND', '7': 'GND',
                                                               '4': 'VBUS_C', '5': 'VBUS_C', '6': 'VBUS_C'}, prefix='D')
    g.C('4.7uF', 'VBUS_C', size='0805', v='25V', note='CVBUS 1-10 uF (SLVSH93A 6.4)')
    g.C('10nF', 'VBUS_C', size='0402', v='50V')
    g.C('330pF', 'USBC_CC1', size='0402', v='50V', note='CCCy 200-480 pF')
    g.C('330pF', 'USBC_CC2', size='0402', v='50V')
    P(g, 'TPS25751D', S['TPS25751D'], 'TPS25751DREFR', {
        '1': 'PD_LDO_3V3', '2': 'PD_LDO_3V3', '3': 'GND', '4': 'PD_LDO_1V5',
        '5': 'GND', '6': 'GND', '7': 'GND', '19': 'GND', '13': 'GND', '36': 'GND', '37': 'GND',
        '8': 'I2C_SYS_SDA', '9': 'I2C_SYS_SCL', '10': 'PD_INT_N',
        '16': 'I2C_PD_SDA', '17': 'I2C_PD_SCL', '18': 'PD_I2CC_IRQ_N',
        '20': 'CHG_IN', '23': 'VBUS_C', '32': 'VBUS_C', '34': 'VCC5V0', '38': 'VCC3V3_AO',
        '26': 'PD_BC_DP', '27': 'PD_BC_DN', '28': 'USBC_CC1', '29': 'USBC_CC2',
        '40': 'PD_DRAIN', '[15,30]': 'PD_DRAIN', '[11,12,14,31,39]': 'GND'},
      note='GPIOs unused -> GND (pin table). PP5V on VCC5V0 only for an optional source role; sink-only in config.')
    g.R('0', 'PD_BC_DP', 'USBC_DP', note='BC1.2 detection (GPIO4 = D+), remove to isolate')
    g.R('0', 'PD_BC_DN', 'USBC_DN', note='BC1.2 detection (GPIO5 = D-)')
    g.C('10uF', 'VCC3V3_AO', size='0603', v='10V', note='CVIN_3V3')
    g.C('10uF', 'PD_LDO_3V3', size='0603', v='10V', note='CLDO_3V3')
    g.C('10uF', 'PD_LDO_1V5', size='0603', v='10V', note='CLDO_1V5 4.5-12 uF')
    g.C('10uF', 'VCC5V0', size='0603', v='10V', note='>=10 uF directly at PP5V')
    g.R('10k', 'PD_INT_N', 'VCC_1V8_S3', note='I2Ct_IRQ pull-up (SoC domain) -> GPIO3_B3 (JP3.46, 1.8 V)')
    g.R('10k', 'PD_I2CC_IRQ_N', 'PD_LDO_3V3', note='I2Cc_IRQ must not be grounded')

    g = sb.group('PD configuration EEPROM (64 KB, 0x50) + programming pads',
                 'TPS25751 needs >= 36 KB at 7-bit 0x50 on I2Cc. WC high = write-protected; pull EE_WP low at the pad to program.\n'
                 'Program with the board on battery (TPS25751 waits for a host when the EEPROM is blank).')
    P(g, 'M24512', 'Memory_EEPROM:24LC512', 'M24512-RMN6TP',
      {'1': 'GND', '2': 'GND', '3': 'GND', '4': 'GND', '5': 'I2C_PD_SDA', '6': 'I2C_PD_SCL', '7': 'PD_EE_WP',
       '8': 'PD_LDO_3V3'})
    g.C('100nF', 'PD_LDO_3V3')
    g.R('10k', 'PD_EE_WP', 'PD_LDO_3V3')
    g.R('2.2k', 'I2C_PD_SDA', 'PD_LDO_3V3')
    g.R('2.2k', 'I2C_PD_SCL', 'PD_LDO_3V3')
    for n in ('I2C_PD_SDA', 'I2C_PD_SCL', 'PD_EE_WP', 'PD_LDO_3V3', 'GND'):
        g.TP(n, label=f'PROG_{n}')

    # ------------------------------------------------------------ charger power stage
    g = sb.group('NVDC buck-boost charger (BQ25713) - power stage',
                 'Ref: TI SLUSD83C Fig. 10-1 / 10-2. RAC = RSR = 10 mOhm. fsw default 800 kHz. Q1..Q4 CSD17577Q3A (30 V, 6.4 mOhm @4.5 V),\n'
                 'L = 2.2 uH Isat 14 A. BATFET CSD25404Q3 (-20 V, 5.5 mOhm @ -4.5 V, Ciss 1.63 nF < 5 nF limit). '
                 'Battery path sized for 12 A (decision Q3/Q4).')
    p = part('R_10m_2512')
    g.R('10m', 'CHG_IN', 'CHG_IN_S', size='2512', lcsc=p['lcsc'], mpn=p['mpn'], mfr=p['mfr'], note='RAC input current sense')
    for _ in range(4):
        g.C('10uF', 'CHG_IN', size='0805', v='25V', note='input caps before RAC (Table 10-1)')
    g.C('22uF', 'CHG_IN', size='0805', v='25V', note='CPPHV 47 uF nominal total (SLVSH93A 6.4)')
    g.C('100nF', 'CHG_IN', size='0402', v='25V')
    g.C('10nF', 'CHG_IN_S', size='0402', v='50V', note='max 10 nF + 1 nF after RAC')
    g.C('1nF', 'CHG_IN_S', size='0402', v='50V')
    nmos(g, 'CSD17577Q3A', 'CHG_IN_S', 'CHG_HIDRV1', 'CHG_SW1', 'CSD17577Q3A (Q1 buck HS)')
    nmos(g, 'CSD17577Q3A', 'CHG_SW1', 'CHG_LODRV1', 'GND', 'CSD17577Q3A (Q2 buck LS)')
    pl = part('L_2u2_14A')
    g.L('2.2uH', 'CHG_SW1', 'CHG_SW2', pl['fp'], pl['lcsc'], pl['mpn'], pl['mfr'])
    nmos(g, 'CSD17577Q3A', 'CHG_SW2', 'CHG_LODRV2', 'GND', 'CSD17577Q3A (Q3 boost LS)')
    nmos(g, 'CSD17577Q3A', 'VSYS', 'CHG_HIDRV2', 'CHG_SW2', 'CSD17577Q3A (Q4 boost HS)')
    g.C('47nF', 'CHG_BTST1', 'CHG_SW1', size='0402', v='25V')
    g.C('47nF', 'CHG_BTST2', 'CHG_SW2', size='0402', v='25V')
    for _ in range(7):
        g.C('10uF', 'VSYS', size='0603', v='16V', note='7 x 10 uF at Q3/Q4 (sec. 10.2.2.4)')
    g.C('100nF', 'VSYS', size='0402', v='16V')
    P(g, 'CSD25404Q3', S['PMOS_SON8'], 'CSD25404Q3 (BATFET)',
      {'1': 'BAT_SRP', '2': 'BAT_SRP', '3': 'BAT_SRP', '4': 'CHG_BATDRV',
       '5': 'VSYS', '6': 'VSYS', '7': 'VSYS', '8': 'VSYS', '9': 'VSYS'}, prefix='Q',
      note='source on VSYS, gate from BATDRV (shorted to VSYS = off)')
    g.R('10m', 'BAT_SRP', 'BAT_P', size='2512', lcsc=p['lcsc'], mpn=p['mpn'], mfr=p['mfr'], note='RSR charge current sense')
    g.C('10uF', 'BAT_P', size='0603', v='16V', note='>= 20 uF after RSR')
    g.C('10uF', 'BAT_P', size='0603', v='16V')

    g = sb.group('NVDC charger (BQ25713) - controller',
                 'I2C 0x6B on I2Cc, configured by the TPS25751 (charge 2.5 A / 4.2 V set in the PD configuration).\n'
                 'ILIM_HIZ 383k/220k from VDDA = 2.19 V -> 2.97 A hardware input limit. CELL_BATPRESZ 300k/100k = 25 % of VDDA -> 1S.\n'
                 'COMP/IADPT/IBAT/PSYS values from Fig. 10-1 (IADPT 137k = 2.2 uH).')
    P(g, 'BQ25713', S['BQ25713'], 'BQ25713RSNR', {
        '1': 'CHG_VBUS_F', '2': 'CHG_ACN', '3': 'CHG_ACP', '4': 'CHRG_OK', '5': 'GND', '6': 'CHG_ILIM', '7': 'CHG_VDDA',
        '8': 'CHG_IADPT', '9': 'CHG_IBAT', '10': 'CHG_PSYS', '11': 'CHG_PROCHOT_N', '12': 'I2C_PD_SDA', '13': 'I2C_PD_SCL',
        '14': 'GND', '15': None, '16': 'CHG_COMP1', '17': 'CHG_COMP2', '18': 'CHG_CELL', '19': 'CHG_SRN', '20': 'CHG_SRP',
        '21': 'CHG_BATDRV', '22': 'VSYS', '23': 'CHG_SW2', '24': 'CHG_HIDRV2', '25': 'CHG_BTST2', '26': 'CHG_LODRV2',
        '27': 'GND', '28': 'CHG_REGN', '29': 'CHG_LODRV1', '30': 'CHG_BTST1', '31': 'CHG_HIDRV1', '32': 'CHG_SW1', '33': 'GND'})
    g.R('1', 'CHG_IN', 'CHG_VBUS_F', size='0603', note='VBUS pin filter 1 Ohm + 0.47 uF')
    g.C('470nF', 'CHG_VBUS_F', size='0402', v='25V')
    g.R('4.99', 'CHG_IN', 'CHG_ACP', note='ACP filter (Fig. 10-2)')
    g.C('33nF', 'CHG_ACP', size='0402', v='25V')
    g.R('4.99', 'CHG_IN_S', 'CHG_ACN')
    g.C('33nF', 'CHG_ACN', size='0402', v='25V')
    g.C('2.2uF', 'CHG_REGN', size='0603', v='16V', note='REGN 2.2-3.3 uF')
    g.R('10', 'CHG_REGN', 'CHG_VDDA')
    g.C('1uF', 'CHG_VDDA', size='0402', v='16V')
    g.R('383k', 'CHG_VDDA', 'CHG_ILIM')
    g.R('220k', 'CHG_ILIM', 'GND')
    g.R('300k', 'CHG_VDDA', 'CHG_CELL', note='no capacitor allowed on CELL_BATPRESZ')
    g.R('100k', 'CHG_CELL', 'GND')
    g.R('137k', 'CHG_IADPT', 'GND', note='2.2 uH inductor code')
    g.C('100pF', 'CHG_IADPT', size='0402', v='50V')
    g.C('100pF', 'CHG_IBAT', size='0402', v='50V')
    g.R('30k', 'CHG_PSYS', 'GND')
    g.C('33pF', 'CHG_COMP1', size='0402', v='50V')
    g.R('40.2k', 'CHG_COMP1', 'CHG_COMP1_RC')
    g.C('1.8nF', 'CHG_COMP1_RC', size='0402', v='50V')
    g.C('15pF', 'CHG_COMP2', size='0402', v='50V')
    g.R('10k', 'CHG_COMP2', 'CHG_COMP2_RC')
    g.C('680pF', 'CHG_COMP2_RC', size='0402', v='50V')
    g.R('10', 'BAT_SRP', 'CHG_SRP', note='SRP/SRN 10 Ohm + 0.1 uF differential; route as Kelvin from RSR pads')
    g.R('10', 'BAT_P', 'CHG_SRN')
    g.C('100nF', 'CHG_SRP', 'CHG_SRN', size='0402', v='16V')
    g.R('10k', 'CHG_PROCHOT_N', 'VCC_1V8_S3', note='PROCHOT# (open drain) -> GPIO3_C1 (JP3.50, 1.8 V; CPU/GPU throttling)')
    g.R('1M', 'CHRG_OK', 'VCC3V3_AO', note='CHRG_OK high = adapter present; gates the NTC cutoff')
    g.TP('CHRG_OK')
    g.TP('CHG_PSYS')

    # ------------------------------------------------------------ battery connector, fuel gauge
    g = sb.group('Battery connector (1S, 5000 mAh, PCM >= 12 A) and fuel gauge (MAX17055)',
                 'Molex 505578-0971 (right angle): pins 1-4 BAT+, 5-8 BAT-, 9 NTC (4 x 3.0 A per side = 12 A). Pack PCM >= 12 A (decision Q4).\n'
                 'MAX17055: low-side sense 4 mOhm (+-51.2 mV / 4 mOhm = +-12.8 A); CSP = IC ground (battery side), CSN Kelvin to load side.\n'
                 'Internal temperature mode (AIN tied to CSP, THRM open) - the pack NTC drives the charge cutoff comparator.')
    P(g, 'BATT_CONN', S['BATT_CONN'], 'Molex 505578-0971',
      {'1': 'BAT_P', '2': 'BAT_P', '3': 'BAT_P', '4': 'BAT_P', '5': 'BAT_N', '6': 'BAT_N', '7': 'BAT_N', '8': 'BAT_N',
       '9': 'BAT_NTC', 'MP': 'GND'}, prefix='J')
    p4 = part('R_4m_2512')
    g.R('4m', 'BAT_N', 'GND', size='2512', lcsc=p4['lcsc'], mpn=p4['mpn'], mfr=p4['mfr'], note='fuel-gauge sense, 0.4 W at 10 A')
    g.part('NT', d_sym('Device:NetTie_2'), 'NetTie', {'1': 'FG_CSN', '2': 'GND'}, 'NetTie:NetTie-2_SMD_Pad0.5mm',
           {'Sourcing': 'PCB', 'Note': 'Kelvin tap at the load-side pad of the 4 mOhm sense resistor'})
    P(g, 'MAX17055', S['MAX17055'], 'MAX17055ETB+T', {
        '10': 'BAT_P', '2': 'BAT_N', '9': None, '3': 'I2C_SYS_SCL', '4': 'I2C_SYS_SDA', '8': 'FG_ALRT_N', '1': None,
        '7': 'FG_REG', '5': 'FG_CSN', '6': 'BAT_N', '11': 'BAT_N'},
      note='I2C 0x36 (Linux max17042 binding); no strap, and nothing else on this bus near it (0x20, 0x51)')
    g.C('100nF', 'BAT_P', 'BAT_N', size='0402', v='16V', note='BATT bypass to CSP')
    g.C('470nF', 'FG_REG', 'BAT_N', size='0402', v='10V', note='REG bypass to CSP')
    g.R('10k', 'FG_ALRT_N', 'VCC_1V8_S3', note='ALRT# (open drain) -> GPIO3_B2 (JP3.48, 1.8 V)')

    # ------------------------------------------------------------ NTC charge-temperature window
    g = sb.group('Battery temperature charge window 0-45 C (pack NTC 10 kOhm B3435, battery spec C2-1)',
                 'Only active while an adapter is present (CHRG_OK high switches VNTC on and enables Q_a), so a hot/cold battery\n'
                 'can still power the system. Out of window -> CELL_BATPRESZ pulled low -> BQ25713 disables charging.\n'
                 'Thresholds (ratiometric, VNTC): cold 0.738*VNTC (~0 C, 28.7k), hot 0.320*VNTC (~46 C, 4.7k). '
                 'Missing NTC reads as cold -> no charging.')
    sot_nmos(g, 'NTC_PG', 'CHRG_OK', 'GND', '2N7002')
    sot_pmos(g, 'VNTC', 'NTC_PG', 'VCC3V3_AO', 'AO3401A')
    g.R('1M', 'NTC_PG', 'VCC3V3_AO')
    g.C('100nF', 'VNTC')
    g.R('10k', 'VNTC', 'BAT_NTC', size='0402', note='NTC bias, 0.1 %/C class (1 %)')
    g.C('100nF', 'BAT_NTC')
    g.R('270k', 'VNTC', 'NTC_VCOLD')
    g.R('430k', 'NTC_VCOLD', 'NTC_VHOT')
    g.R('330k', 'NTC_VHOT', 'GND')
    P(g, 'TLV7042', S['TLV7042'], 'TLV7042DGKR', {
        '3': 'NTC_VCOLD', '2': 'BAT_NTC', '5': 'BAT_NTC', '6': 'NTC_VHOT', '8': 'VNTC', '4': 'GND',
        '1': 'NTC_FAULT_N', '7': 'NTC_FAULT_N'},
      note='A: NTC > Vcold (too cold / open) -> OUTA low; B: NTC < Vhot (too hot / short) -> OUTB low. '
           'No pull-up on the OD outputs: the CELL_BATPRESZ divider biases the node through Q_a')
    sot_nmos(g, 'CHG_CELL', 'CHRG_OK', 'NTC_FAULT_N', '2N7002 (Q_a)')

    # ------------------------------------------------------------ always-on 3.3 V
    g = sb.group('Always-on 3.3 V (from VSYS)', 'XC6206: Iq 1 uA, 200 mA, Vin max 6 V (VSYS <= 4.5 V). Loads: TPS25751 VIN_3V3, RTC, NTC window.')
    P(g, 'XC6206_33', 'Regulator_Linear:XC6206PxxxMR', 'XC6206P332MR', {'1': 'GND', '2': 'VCC3V3_AO', '3': 'VSYS'})
    g.C('1uF', 'VSYS', size='0402', v='16V')
    g.C('1uF', 'VCC3V3_AO', size='0402', v='10V')
    for n in ('VBUS_C', 'CHG_IN', 'VSYS', 'BAT_P', 'VCC3V3_AO', 'PD_LDO_3V3'):
        g.TP(n)
    return sb


def d_sym(lib_id):
    import symlib
    return symlib.load(lib_id)


# ============================================================================================ sheet 2
def sheet_power_rails(d):
    sb = d.sheet('Power rails', 'power_rails.kicad_sch', paper='A3')
    S = d.S
    pl = part('L_2u2_14A')
    pl15 = part('L_1u5_7A')

    g = sb.group('CM5 supply: TPS61088 boost VSYS -> 5.03 V (always on while VSYS exists; the module PMIC does on/off)',
                 'Ref: TI ZHCSDP8A sec. 9.2. fsw 600 kHz: RFREQ = 4(1/fsw - 89 ns*Vout/Vin)/23 pF = 270k (Vin 3.7 V).\n'
                 'ILIM = 1.19e6/140k = 8.5 A (min 7.2 A) > peak 6.1 A at Vin 3.0 V, 3 A out (Orange Pi CM5: 1.8 A max).\n'
                 'VOUT = 1.204*(1+178k/56k) = 5.03 V: Orange Pi CM5 VBUS 4.75-5.25 V (PIN definition V1.1, JP1.77-87).\n'
                 'Compensation (eq. 18-20, fc 9 kHz, Co 50 uF): R5 7.5k, C5 5.6 nF, C8 open. Soft start 47 nF = 11 ms. MODE open = PFM.')
    P(g, 'TPS61088', S['TPS61088'], 'TPS61088RHLR', {
        '9': 'VSYS', '2': 'BST_CM5_EN', '13': None, '10': 'BST_CM5_SS', '19': 'BST_CM5_ILIM', '18': 'BST_CM5_COMP',
        '1': 'BST_CM5_VCC', '11': 'GND', '12': 'GND', '4': 'BST_CM5_SW', '5': 'BST_CM5_SW', '6': 'BST_CM5_SW',
        '7': 'BST_CM5_SW', '8': 'BST_CM5_BOOT', '3': 'BST_CM5_FSW', '14': 'CM5_VIN', '15': 'CM5_VIN', '16': 'CM5_VIN',
        '17': 'BST_CM5_FB', '20': 'GND', '21': 'GND'}, note='NC pins 11/12 to ground plane (pin table)')
    g.L('2.2uH', 'VSYS', 'BST_CM5_SW', pl['fp'], pl['lcsc'], pl['mpn'], pl['mfr'])
    g.R('10k', 'BST_CM5_EN', 'VSYS', note='always enabled; TP to force off for bring-up')
    g.TP('BST_CM5_EN')
    g.C('10uF', 'VSYS', size='0805', v='16V')
    g.C('100nF', 'VSYS', size='0402', v='16V')
    g.C('2.2uF', 'BST_CM5_VCC', size='0402', v='10V')
    g.C('100nF', 'BST_CM5_BOOT', 'BST_CM5_SW', size='0402', v='16V')
    g.R('270k', 'BST_CM5_FSW', 'BST_CM5_SW')
    g.R('140k', 'BST_CM5_ILIM', 'GND')
    g.C('47nF', 'BST_CM5_SS', size='0402', v='16V')
    g.R('7.5k', 'BST_CM5_COMP', 'BST_CM5_COMP_RC')
    g.C('5.6nF', 'BST_CM5_COMP_RC', size='0402', v='16V')
    g.R('178k', 'CM5_VIN', 'BST_CM5_FB', note='1 %')
    g.R('56k', 'BST_CM5_FB', 'GND', note='1 %')
    g.C('1uF', 'CM5_VIN', size='0402', v='16V')
    for _ in range(3):
        g.C('22uF', 'CM5_VIN', size='0805', v='16V')

    g = sb.group('5 V rail: TPS61089 boost VSYS -> 5.14 V (USB-A x2, keyboard, CAM-A, PD PP5V)',
                 'Ref: TI SLVSD38C sec. 9.2. fsw ~575 kHz (RFREQ 270k, CFREQ 24 pF, tDELAY 86 ns). ILIM = 1.03e6/158k = 6.5 A (min 5.7 A)\n'
                 '> peak 4.5 A at Vin 3.0 V / 2 A out. VOUT = 1.212*(1+324k/100k) = 5.14 V. Compensation fc 10 kHz: 8.2k + 6.8 nF.\n'
                 'EN (VEN_H 1.2 V) = GPIO0_D5 (JP3.77, 1.8 V, default pull-up) with 100k pull-up to VCC_1V8_S3: on whenever the\n'
                 'CM5 is on, software can cut it in suspend.')
    P(g, 'TPS61089', S['TPS61089'], 'TPS61089RNRR', {
        '9': 'VSYS', '7': 'EN_5V', '8': 'BST_5V_ILIM', '4': 'BST_5V_COMP', '2': 'BST_5V_VCC', '5': 'GND',
        '11': 'BST_5V_SW', '10': 'BST_5V_BOOT', '1': 'BST_5V_FSW', '6': 'VCC5V0', '3': 'BST_5V_FB'})
    g.L('2.2uH', 'VSYS', 'BST_5V_SW', pl['fp'], pl['lcsc'], pl['mpn'], pl['mfr'])
    g.R('100k', 'EN_5V', 'VCC_1V8_S3')
    g.C('10uF', 'VSYS', size='0805', v='16V')
    g.C('100nF', 'VSYS', size='0402', v='16V')
    g.C('2.2uF', 'BST_5V_VCC', size='0402', v='10V')
    g.C('100nF', 'BST_5V_BOOT', 'BST_5V_SW', size='0402', v='16V')
    g.R('270k', 'BST_5V_FSW', 'BST_5V_SW')
    g.R('158k', 'BST_5V_ILIM', 'GND')
    g.R('8.2k', 'BST_5V_COMP', 'BST_5V_COMP_RC')
    g.C('6.8nF', 'BST_5V_COMP_RC', size='0402', v='16V')
    g.R('324k', 'VCC5V0', 'BST_5V_FB', note='1 %')
    g.R('100k', 'BST_5V_FB', 'GND', note='1 %')
    g.C('1uF', 'VCC5V0', size='0402', v='16V')
    for _ in range(3):
        g.C('22uF', 'VCC5V0', size='0805', v='16V')

    for name, net, en, r2, ps, note in (
            ('LTE modem supply: TPS63020 buck-boost VSYS -> 3.75 V', 'VCC_LTE', 'LTE_PWR_EN', '154k', 'VSYS',
             'Ref: TI SLVS916I sec. 8.2: L 1.5 uH, 3 x 22 uF out. VOUT = 0.5*(1+1M/154k) = 3.75 V (EM060K 3.135-4.4 V).\n'
             'EN (VIH 1.2 V) = GPIO0_C4 (JP3.83, 1.8 V; 100k pull-down: off until software enables). PS/SYNC high = forced PWM.\n'
             'Quectel asks 3 A cont./4 A peak; TPS63020 gives ~2 A in boost mode - 2 x 220 uF bulk on the M.2 sheet carry the bursts.'),
            ('AUX 3.3 V: TPS63020 buck-boost VSYS -> 3.31 V (AP6275P, USB hub, cameras)', 'VCC3V3_AUX', 'VCC_3V3_S3', '178k', 'GND',
             'VOUT = 0.5*(1+1M/178k) = 3.31 V. EN follows VCC_3V3_S3 (on in S0/S3, like the CM5 3.3 V rail). PS/SYNC low = power save.')):
        g = sb.group(name, note)
        tag = 'LTE' if net == 'VCC_LTE' else 'AUX'
        en_net = en if tag == 'LTE' else f'BB_{tag}_EN'
        P(g, 'TPS63020', S['TPS63020'], 'TPS63020DSJR', {
            '10': 'VSYS', '11': 'VSYS', '1': f'BB_{tag}_VINA', '12': en_net, '13': ps if ps != 'VSYS' else f'BB_{tag}_VINA',
            '2': 'GND', '15': 'GND', '8': f'BB_{tag}_L1', '9': f'BB_{tag}_L1', '6': f'BB_{tag}_L2', '7': f'BB_{tag}_L2',
            '4': net, '5': net, '3': f'BB_{tag}_FB', '14': f'BB_{tag}_PG'})
        g.L('1.5uH', f'BB_{tag}_L1', f'BB_{tag}_L2', pl15['fp'], pl15['lcsc'], pl15['mpn'], pl15['mfr'])
        g.R('10', 'VSYS', f'BB_{tag}_VINA', note='VINA filter')
        g.C('100nF', f'BB_{tag}_VINA', size='0402', v='16V')
        g.C('10uF', 'VSYS', size='0603', v='16V')
        g.C('10uF', 'VSYS', size='0603', v='16V')
        g.R('1M', net, f'BB_{tag}_FB', note='1 %')
        g.R(r2, f'BB_{tag}_FB', 'GND', note='1 %')
        for _ in range(3):
            g.C('22uF', net, size='0805', v='10V')
        if tag == 'LTE':
            g.R('100k', 'LTE_PWR_EN', 'GND')
        else:
            g.R('10k', 'VCC_3V3_S3', en_net)
            g.R('1M', en_net, 'GND')
        g.R('100k', f'BB_{tag}_PG', net)
        g.TP(f'BB_{tag}_PG')
    g = sb.group('Rail test points', 'One test pad per rail (brief: test points on all rails).')
    for n in ('CM5_VIN', 'VCC5V0', 'VCC_LTE', 'VCC3V3_AUX'):
        g.TP(n)
    return sb
