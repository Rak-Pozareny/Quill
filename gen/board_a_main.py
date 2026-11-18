"""Board A sheets 3-10: CM5 + system, USB, LTE + SIM, wireless, display + cameras, audio, storage, keyboard IF."""
import json
import os

from parts import part
from board_a_power import P, sot_nmos, sot_pmos
import symbols

HERE = os.path.dirname(os.path.abspath(__file__))
OPI = json.load(open(os.path.join(HERE, 'data', 'opi_cm5_pins.json')))

# Orange Pi CM5 pin -> carrier net (docs/opi/opi_cm5_pin_map.csv, decisions D85-D92). Symbol / footprint letter A = JP1,
# B = JP2, C = JP3. IO voltage per pin: gen/data/opi_cm5_pins.json ('domain'); GPIO_VREF (JP1.78) = 3.3 V here.
CM5_NETS = {
    'A': {21: 'LED_STATUS', 25: 'HUB_RESET_N', 27: 'LTE_RESET_CTL', 28: 'I2C_SYS_SDA', 29: 'TP_INT',
          30: 'I2C_SYS_SCL', 31: 'TP_RST_N', 34: 'LTE_WDIS_CTL', 37: 'DIG_INT_N', 38: 'DIG_RST_N', 39: 'KBD_RESET_N',
          40: 'KBD_BOOT_N', 47: 'LTE_FCPO_N', 48: 'PDM_CLK', 49: 'PDM_DATA', 51: 'DBG_RX_SOC', 55: 'DBG_TX_SOC',
          57: 'SD_CLK_SOC', 61: 'SD_D3', 62: 'SD_CMD', 63: 'SD_D0', 67: 'SD_D1', 69: 'SD_D2', 68: 'BTN_ADC_KEYS',
          76: 'SD_DET_N', 77: 'CM5_VIN', 79: 'CM5_VIN', 81: 'CM5_VIN', 83: 'CM5_VIN', 85: 'CM5_VIN',
          87: 'CM5_VIN', 78: 'VCC_3V3_S3', 80: 'I2C_TP_SCL', 82: 'I2C_TP_SDA', 84: 'VCC_3V3_S3', 86: 'VCC_3V3_S3',
          88: 'VCC_1V8_S3', 90: 'VCC_1V8_S3', 92: 'BTN_RESET_N', 93: 'BTN_MASKROM', 95: 'BL_PWM', 96: 'VSYS_SENSE',
          97: 'LCD_PWREN', 99: 'BTN_PWRON_N'},
    'B': {2: 'I2C_CAMB_SDA', 3: 'USB_OTG_DN', 4: 'I2C_CAMB_SCL', 5: 'USB_OTG_DP', 9: 'AMP_SD_MODE',
          16: 'USB3_LTE_RX_P', 18: 'USB3_LTE_RX_N', 22: 'USB3_LTE_TX_P', 24: 'USB3_LTE_TX_N',
          15: 'CSIA_D0_N', 17: 'CSIA_D0_P', 21: 'CSIA_D1_N', 23: 'CSIA_D1_P', 27: 'CSIA_CLK_N', 29: 'CSIA_CLK_P',
          33: 'CSIA_D2_N', 35: 'CSIA_D2_P', 39: 'CSIA_D3_N', 41: 'CSIA_D3_P',
          28: 'CSIB_D0_N', 30: 'CSIB_D0_P', 34: 'CSIB_D1_N', 36: 'CSIB_D1_P', 40: 'CSIB_CLK_N', 42: 'CSIB_CLK_P',
          75: 'DSI_D0_N', 77: 'DSI_D0_P', 81: 'DSI_D1_N', 83: 'DSI_D1_P', 87: 'DSI_CLK_N', 89: 'DSI_CLK_P',
          93: 'DSI_D2_N', 95: 'DSI_D2_P', 94: 'DSI_D3_N', 96: 'DSI_D3_P'},
    'C': {1: 'USB_LTE_DP', 3: 'USB_LTE_DN', 13: 'USB_HUB_UP_DP', 15: 'USB_HUB_UP_DN', 20: 'CAMA_RST_N',
          22: 'WL_PCIE_CLKREQ_N', 24: 'WL_PCIE_PERST_N', 26: 'BT_UART_TX', 28: 'BT_UART_RTS_N', 30: 'BT_UART_RX',
          34: 'I2C_CAMA_SCL', 36: 'CAMA_PDN', 38: 'CAMB_IO0', 40: 'BT_UART_CTS_N', 42: 'CAMB_IO1',
          43: 'WL_PCIE_PME_N', 46: 'PD_INT_N', 48: 'FG_ALRT_N', 50: 'CHG_PROCHOT_N', 52: 'CAMA_MCLK', 60: 'CAMB_MCLK',
          62: 'LCD_RESET_N', 66: 'RTC_INT_N', 67: 'WL_HOST_WAKE', 69: 'I2S0_LRCK', 70: 'I2S0_SDO', 71: 'I2S0_BCLK',
          72: 'I2C_CAMA_SDA', 76: 'PCIE_REFCLK_P', 77: 'EN_5V', 78: 'PCIE_REFCLK_N', 79: 'BT_REG_ON', 81: 'KBD_INT_N',
          82: 'PCIE_TX_P', 83: 'LTE_PWR_EN', 84: 'PCIE_TX_N', 85: 'LTE_WAKE_N', 88: 'PCIE_RX_N', 89: 'WL_REG_ON',
          90: 'PCIE_RX_P', 94: 'BT_HOST_WAKE', 96: 'WIFI_LPO_32K', 98: 'BT_WAKE'},
}
JP = {'A': 'JP1', 'B': 'JP2', 'C': 'JP3'}


def cm5_net_map(letter):
    nets = {}
    for k in range(1, 101):
        n = OPI[JP[letter]][str(k)]['signal']
        nets[str(k)] = 'GND' if n == 'GND' else CM5_NETS[letter].get(k)
    return nets


def esd4(g, a, b, c, d_):
    """TPD4E05U06 (4 lines to GND). None = unused channel."""
    p = part('TPD4E05U06')
    return g.ic('Power_Protection:TPD4E05U06DQA', 'TPD4E05U06DQAR', {
        '1': a, '2': b, '4': c, '5': d_, '3': 'GND', '8': 'GND', '6': None, '7': None, '9': None, '10': None},
        p['fp'], lcsc=p['lcsc'], mpn=p['mpn'], mfr=p['mfr'], prefix='D')


def conn(g, key, sym, value, pins, note='', sourcing='JLC'):
    return P(g, key, sym, value, pins, prefix='J', note=note, sourcing=sourcing)


def fpc_sym(d, name, n, footprint):
    if name not in d.S:
        d.S[name] = symbols.fpc(d, name, n, name, footprint)
    return d.S[name]


# ============================================================================================ sheet 3
def sheet_cm5(d):
    sb = d.sheet('CM5 module, buttons, RTC, debug', 'cm5.kicad_sch', paper='A3')
    S = d.S
    g = sb.group('Orange Pi CM5 board-to-board connectors JP1-JP3 (3 x Hirose DF40C-100DS-0.4V(51), 1.5 mm stack)',
                 'Pin names = Orange Pi CM5 interface PIN definition V1.1 (2025-07), IO voltage in brackets. Unused and\n'
                 '"Reserved" pins open (JP1.64 / JP1.73: "do not connect"). GPIO_VREF (JP1.78) = VCC_3V3_S3, as both Orange Pi\n'
                 'carriers: GPIO1_A/B/C0/C1/C4/C6/D0-D3/D5 at 3.3 V. GPIO0 and GPIO3 are 1.8 V, GPIO4 3.3 V (base board V1.2 sheet 10).')
    for c in 'ABC':
        g.ic(S['CM5_' + c], f'DF40C-100DS-0.4V(51) (CM5 {JP[c]})', cm5_net_map(c), f'cm5h:OPi_CM5_DF40_{JP[c]}',
             lcsc='C597931', mpn='DF40C-100DS-0.4V(51)', mfr='Hirose', prefix='J')
    g.C('22uF', 'CM5_VIN', size='0805', v='16V', note='VCC_SYSIN decoupling at the connector')
    g.C('22uF', 'CM5_VIN', size='0805', v='16V')
    g.C('100nF', 'CM5_VIN', size='0402', v='16V')
    g.C('10uF', 'VCC_3V3_S3', size='0603', v='10V')
    g.C('10uF', 'VCC_1V8_S3', size='0603', v='10V')
    g.C('1uF', 'VCC_1V8_S3', size='0402', v='10V')
    g.C('100nF', 'VCC_3V3_S3', size='0402', v='10V', note='at GPIO_VREF (JP1.78)')
    for i in range(4):
        pn = part('CM5_NUT')
        g.part('H', d_sym('Mechanical:MountingHole_Pad'), 'M2.5 x 1.5 standoff', {'1': 'GND'}, pn['fp'],
               {'Sourcing': 'JLC', 'LCSC': pn['lcsc'], 'MPN': pn['mpn'], 'Manufacturer': pn['mfr'],
                'Note': 'CM5 module standoff at (+-16.50, +-24.00) mm from the module centre (Orange Pi base board DXF)'})
    for i in range(4):
        g.part('H', d_sym('Mechanical:MountingHole_Pad'), 'M2', {'1': 'GND'},
               'MountingHole:MountingHole_2.2mm_M2_Pad', {'Sourcing': 'PCB', 'Note': 'enclosure mounting (brief: 4 x M2)'})

    g = sb.group('System I2C (I2C4_M3 on JP1.28 / JP1.30, 3.3 V): TPS25751 I2Ct 0x20, MAX17055, BM8563 RTC 0x51',
                 'Pull-ups to VCC_3V3_S3 (bus unpowered when the CM5 is off; the PD controller and gauge run without it).')
    g.R('2.2k', 'I2C_SYS_SDA', 'VCC_3V3_S3')
    g.R('2.2k', 'I2C_SYS_SCL', 'VCC_3V3_S3')

    g = sb.group('RTC + 32.768 kHz clock for the SoC (CLK32K_IN) and the Wi-Fi sleep clock (BM8563, PCF8563-compatible)',
                 'Powered from the always-on 3.3 V. CLKOUT is open-drain (BM8563 pin table) and defaults to 32.768 kHz;\n'
                 'pulled up to VCC_1V8_S3 = AP6275P LPO level (1.8 V +-0.09 V, s.7) and fed to CLK32K_IN/GPIO0_B2 (JP3.96, 1.8 V)\n'
                 'as on the Orange Pi base board (HYM8563 CLKOUT). INT# -> GPIO0_B0 (JP3.66) as there, pulled up to 1.8 V.\n'
                 'Crystal CL 7 pF (BM8563 characterised at 8 pF).')
    px = part('BM8563')
    g.ic('Timer_RTC:PCF8563T', 'BM8563ESA', {'1': 'RTC_OSCI', '2': 'RTC_OSCO', '3': 'RTC_INT_N', '4': 'GND',
                                              '5': 'I2C_SYS_SDA', '6': 'I2C_SYS_SCL', '7': 'WIFI_LPO_32K', '8': 'VCC3V3_AO'},
         px['fp'], lcsc=px['lcsc'], mpn=px['mpn'], mfr=px['mfr'],
         note='register map identical to the PCF8563 (BM8563 DS sec. 6.2): Linux rtc-pcf8563, compatible "nxp,pcf8563"')
    pc = part('XTAL_32K_7PF')
    g.part('Y', d_sym('Device:Crystal'), '32.768 kHz 7 pF', {'1': 'RTC_OSCI', '2': 'RTC_OSCO'}, pc['fp'],
           {'LCSC': pc['lcsc'], 'MPN': pc['mpn'], 'Manufacturer': pc['mfr']})
    g.C('100nF', 'VCC3V3_AO')
    g.R('10k', 'RTC_INT_N', 'VCC_1V8_S3', note='alarm IRQ -> GPIO0_B0 (1.8 V, wake)')
    g.R('10k', 'WIFI_LPO_32K', 'VCC_1V8_S3')

    g = sb.group('Buttons: power / volume on the right edge (side push, next to SD/SIM), reset / maskrom / recovery on board',
                 'Switch to GND, 100 Ohm series, ESD at the SoC side. PWRON_L (JP1.99) is pulled up to VBUS (45k) inside the module.\n'
                 'SARADC_IN1 (JP1.68) ladder (10k pull-up to 1.8 V on the module): Recovery 0 V, Vol+ 2.2k -> 0.32 V, Vol- 6.8k -> 0.73 V.')
    sw_side, sw_top = part('SW_SIDE'), part('SW_TOP')
    for name, net in (('POWER', 'BTN_PWR_SW'), ('VOL+', 'BTN_VOLUP_SW'), ('VOL-', 'BTN_VOLDN_SW')):
        g.ic(S['SW_SIDE'], f'SKRTLAE010 {name}', {'1': net, '2': 'GND', 'MP': 'GND'}, sw_side['fp'],
             lcsc=sw_side['lcsc'], mpn=sw_side['mpn'], mfr=sw_side['mfr'], prefix='SW')
    for name, net in (('RESET', 'BTN_RESET_SW'), ('MASKROM', 'BTN_MASKROM_SW'), ('RECOVERY', 'BTN_RECOVERY_SW')):
        g.ic('Switch:SW_Push', f'TS-1088C {name}', {'1': net, '2': 'GND'}, sw_top['fp'],
             lcsc=sw_top['lcsc'], mpn=sw_top['mpn'], mfr=sw_top['mfr'], prefix='SW')
    g.R('100', 'BTN_PWR_SW', 'BTN_PWRON_N')
    g.R('100', 'BTN_RESET_SW', 'BTN_RESET_N')
    g.R('100', 'BTN_MASKROM_SW', 'BTN_MASKROM')
    g.R('100', 'BTN_RECOVERY_SW', 'BTN_ADC_KEYS')
    g.R('2.2k', 'BTN_VOLUP_SW', 'BTN_ADC_KEYS', note='1 %')
    g.R('6.8k', 'BTN_VOLDN_SW', 'BTN_ADC_KEYS', note='1 %')
    esd4(g, 'BTN_PWRON_N', 'BTN_RESET_N', 'BTN_MASKROM', 'BTN_ADC_KEYS')

    g = sb.group('Debug console (UART2_M0, 1.5 Mbaud), status LED, VSYS monitor',
                 'UART2_M0 is GPIO0_B5 / B6 = 1.8 V on the Orange Pi CM5 (JP1.55 / JP1.51): TXS0104E to 3.3 V debug pads, so a\n'
                 'common 3.3 V USB-serial adapter can be used. VSYS_SENSE (SARADC_IN2, JP1.96) = VSYS x 499k/(1M+499k):\n'
                 '4.5 V -> 1.50 V (SARADC 1.8 V full scale), 3 uA load.')
    for n in ('DBG_UART_TX', 'DBG_UART_RX', 'GND'):
        g.TP(n, fp='TestPoint:TestPoint_Pad_1.5x1.5mm', label=f'DEBUG_{n}')
    pt = part('TXS0104E')
    g.ic('Logic_LevelTranslator:TXS0104EPW', 'TXS0104EPWR', {
        '1': 'VCC_1V8_S3', '14': 'VCC_3V3_S3', '8': 'VCC_1V8_S3', '7': 'GND',
        '2': 'DBG_TX_SOC', '13': 'DBG_UART_TX', '3': 'DBG_RX_SOC', '12': 'DBG_UART_RX',
        '4': None, '11': None, '5': None, '10': None, '6': None, '9': None},
        pt['fp'], lcsc=pt['lcsc'], mpn=pt['mpn'], mfr=pt['mfr'],
        note='A = 1.8 V (SoC), B = 3.3 V (pads); OE tied to VCCA; unused channels open (internal 10k pull-ups)')
    g.C('100nF', 'VCC_1V8_S3')
    g.C('100nF', 'VCC_3V3_S3')
    g.LED('red', 'LED_STATUS_K', 'LED_STATUS_A', size='0603')
    g.R('1k', 'LED_STATUS', 'LED_STATUS_A', note='~1.3 mA (red, Vf ~2 V)')
    g.R('0', 'LED_STATUS_K', 'GND', note='0 Ohm so the LED can be disabled')
    g.R('1M', 'VSYS', 'VSYS_SENSE', note='1 %')
    g.R('499k', 'VSYS_SENSE', 'GND', note='1 %')
    g.C('100nF', 'VSYS_SENSE', size='0402', v='10V')
    for n in ('VCC_3V3_S3', 'VCC_1V8_S3'):
        g.TP(n)
    return sb


def d_sym(lib_id):
    import symlib
    return symlib.load(lib_id)


# ============================================================================================ sheet 4
def sheet_usb(d):
    sb = d.sheet('USB: USB-C data, hub, USB-A ports', 'usb.kicad_sch', paper='A3')
    S = d.S
    g = sb.group('USB-C data -> CM5 OTG0 (device by default; Maskrom download port)',
                 'Common-mode choke + ESD as on the Radxa IO board. CC lines share the ESD array (sink only, VRWM 5.5 V).')
    pc = part('CMC_90R')
    g.ic('Filter:Choke_CommonMode_FerriteCore_1243', 'DLW21SN900SQ2L', {'1': 'USBC_DP', '2': 'USB_OTG_DP',
         '4': 'USBC_DN', '3': 'USB_OTG_DN'}, pc['fp'], lcsc=pc['lcsc'], mpn=pc['mpn'], mfr=pc['mfr'], prefix='L',
         note='Murata equivalent circuit: windings 1-2 and 4-3, phase dots on 1 and 4 (connector side)')
    esd4(g, 'USBC_DP', 'USBC_DN', 'USBC_CC1', 'USBC_CC2')

    g = sb.group('USB 2.0 hub USB2514B on CM5 HOST0: P1/P2 USB-A, P3 keyboard, P4 digitizer (reserved)',
                 'Microchip DS Rev 2.2: CFG_SEL[1:0] = 00 (strap mode, self-powered, individual port power + over-current).\n'
                 'NON_REM = 00, BC_EN = 0 (internal pull-downs). RBIAS 12.0k 1 %. 24 MHz crystal, 1 MOhm + 18 pF (sec. 7.1).\n'
                 'VBUS_DET from VCC_3V3_S3 (permanently attached host). RESET_N: GPIO1_B0 (JP1.25, 3.3 V) open-drain + 10k/100 nF.\n'
                 'Upstream = USB20_HOST0 (JP3.13 / JP3.15).')
    ph = part('USB2514B')
    g.ic('Interface_USB:USB2514B_Bi', 'USB2514B-AEZC-TR', {
        '1': 'USB_P1_DN', '2': 'USB_P1_DP', '3': 'USB_P2_DN', '4': 'USB_P2_DP', '6': 'KBD_DN', '7': 'KBD_DP',
        '8': 'DIG_DN', '9': 'DIG_DP', '5': 'VCC3V3_AUX', '10': 'VCC3V3_AUX', '29': 'VCC3V3_AUX', '36': 'VCC3V3_AUX',
        '15': 'VCC3V3_AUX', '23': 'VCC3V3_AUX', '11': 'GND', '12': 'HUB_PRTPWR1', '13': 'HUB_OCS1_N', '14': 'HUB_CRFILT',
        '16': 'HUB_PRTPWR2', '17': 'HUB_OCS2_N', '18': 'HUB_PRTPWR3', '19': 'HUB_OCS3_N', '20': 'HUB_PRTPWR4',
        '21': None, '22': 'HUB_NONREM1', '24': 'HUB_CFGSEL0', '25': 'HUB_CFGSEL1', '26': 'HUB_RESET_N', '27': 'HUB_VBUS_DET',
        '28': 'HUB_NONREM0', '30': 'USB_HUB_UP_DN', '31': 'USB_HUB_UP_DP', '32': 'HUB_XO', '33': 'HUB_XI',
        '34': 'HUB_PLLFILT', '35': 'HUB_RBIAS', '37': 'GND'}, ph['fp'], lcsc=ph['lcsc'], mpn=ph['mpn'], mfr=ph['mfr'],
        note='OCS_N4 open (internal pull-up): digitizer port has no over-current sense')
    g.C('4.7uF', 'VCC3V3_AUX', size='0603', v='10V')
    for _ in range(6):
        g.C('100nF', 'VCC3V3_AUX')
    g.C('100nF', 'HUB_CRFILT', note='<= 0.1 uF low ESR')
    g.C('100nF', 'HUB_PLLFILT')
    g.R('12k', 'HUB_RBIAS', 'GND', note='12.0k 1 %')
    for n in ('HUB_NONREM1', 'HUB_CFGSEL0', 'HUB_CFGSEL1', 'HUB_NONREM0'):
        g.R('100k', n, 'GND', note='strap low (47-100k, Table 3.4)')
    g.R('10k', 'VCC_3V3_S3', 'HUB_VBUS_DET')
    g.R('10k', 'HUB_RESET_N', 'VCC3V3_AUX')
    g.C('100nF', 'HUB_RESET_N')
    px = part('XTAL_24M')
    g.part('Y', d_sym('Device:Crystal_GND24'), '24 MHz 12 pF', {'1': 'HUB_XI', '3': 'HUB_XO', '2': 'GND', '4': 'GND'},
           px['fp'], {'LCSC': px['lcsc'], 'MPN': px['mpn'], 'Manufacturer': px['mfr']})
    g.R('1M', 'HUB_XI', 'HUB_XO')
    g.C('18pF', 'HUB_XI', size='0402', v='50V')
    g.C('18pF', 'HUB_XO', size='0402', v='50V')

    g = sb.group('USB-A x2 (bottom edge, mid-mount) with current-limited switches',
                 'TPS2553 RILIM 39k: IOS min/nom/max 0.61/0.67/0.74 A (TI eq. 1) - covers 500 mA. EN = hub PRTPWRx (active high),\n'
                 'FAULT# -> OCS_Nx. VBUS bulk 2 x 22 uF per port (USB 2.0 asks 120 uF; reduced for size, accepted at checkpoint 2).\n'
                 'ESD: one TPD4E05U06 per port next to its connector (flow-through, 2 channels used).')
    pu, ps = part('USBA_MID'), part('TPS2553')
    for n in (1, 2):
        g.ic(S['TPS2553'], 'TPS2553DBVR', {'1': 'VCC5V0', '2': 'GND', '3': f'HUB_PRTPWR{n}', '4': f'HUB_OCS{n}_N',
                                           '5': f'USBA{n}_ILIM', '6': f'USBA{n}_VBUS'}, ps['fp'], lcsc=ps['lcsc'],
             mpn=ps['mpn'], mfr=ps['mfr'])
        g.R('39k', f'USBA{n}_ILIM', 'GND', note='1 %')
        g.C('100nF', 'VCC5V0', size='0402', v='16V')
        g.C('22uF', f'USBA{n}_VBUS', size='0805', v='10V')
        g.C('22uF', f'USBA{n}_VBUS', size='0805', v='10V')
        g.R('10k', f'HUB_OCS{n}_N', 'VCC3V3_AUX')
        conn(g, 'USBA_MID', S['USBA_MID'], f'USB-A port {n}', {'1': f'USBA{n}_VBUS', '2': f'USB_P{n}_DN',
                                                               '3': f'USB_P{n}_DP', '4': 'GND', 'SH': 'GND'})
        esd4(g, f'USB_P{n}_DP', f'USB_P{n}_DN', None, None)    # one array per port, at its connector (ports 18 mm apart)
    return sb


# ============================================================================================ sheet 5
def sheet_lte(d):
    sb = d.sheet('LTE modem (M.2 Key-B) and nano-SIM', 'lte.kicad_sch', paper='A3')
    g = sb.group('Quectel EM060K-GL in an M.2 3042 Key-B socket (bottom side, under the CM5)',
                 'Quectel EM060K HD V1.1: USB 2.0 on HOST1 (JP3.1/3 -> pins 7/9) + USB 3.0 on combo PHY2 in USB3 mode (JP2.22/24,\n'
                 'host TX -> 100 nF -> pins 37/35; module TX pins 31/29 -> JP2.16/18, caps inside the module). RESET# (VIH max 2.1 V,\n'
                 'internal PU to 1.8 V) and W_DISABLE1# driven open-drain by 2N7002s from 3.3 V GPIOs. FULL_CARD_POWER_OFF#\n'
                 '(>= 1.19 V = on) from GPIO0_C2 at 1.8 V. Unused pins open (Table 5 note).')
    pm = part('M2_B')
    nets = {str(k): None for k in list(range(1, 12)) + list(range(20, 76))}
    nets.update({'2': 'VCC_LTE', '4': 'VCC_LTE', '70': 'VCC_LTE', '72': 'VCC_LTE', '74': 'VCC_LTE',
                 '3': 'GND', '5': 'GND', '11': 'GND', '27': 'GND', '33': 'GND', '39': 'GND', '45': 'GND', '51': 'GND',
                 '57': 'GND', '71': 'GND', '73': 'GND',
                 '6': 'LTE_FCPO_M2', '7': 'USB_LTE_DP', '8': 'LTE_WDIS_N', '9': 'USB_LTE_DN', '10': 'LTE_LED_N',
                 '23': 'LTE_WAKE_N', '29': 'USB3_LTE_RX_N', '31': 'USB3_LTE_RX_P', '35': 'USB3_LTE_TXC_N',
                 '37': 'USB3_LTE_TXC_P', '30': 'SIM_RST_M2', '32': 'SIM_CLK_M2', '34': 'SIM_IO_M2', '36': 'SIM_VDD',
                 '66': 'SIM_DET', '67': 'LTE_RESET_N'})
    g.ic('Connector:Bus_M.2_Socket_B', 'M.2 Key-B socket (EM060K-GL)', nets, pm['fp'], lcsc=pm['lcsc'], mpn=pm['mpn'],
         mfr=pm['mfr'], prefix='J', note='module: Quectel EM060K-GL (customer-supplied / hand-fitted)')
    pn = part('M2_NUT')
    g.part('H', d_sym('Mechanical:MountingHole_Pad'), 'M.2 3042 standoff', {'1': 'GND'}, pn['fp'],
           {'Sourcing': 'JLC', 'Note': pn['note'], 'MPN': pn['mpn'], 'LCSC': pn['lcsc'], 'Manufacturer': pn['mfr']})
    g.C('100nF', 'USB3_LTE_TX_P', 'USB3_LTE_TXC_P', size='0201', v='16V', note='host TX AC coupling (Quectel Fig. 18)')
    g.C('100nF', 'USB3_LTE_TX_N', 'USB3_LTE_TXC_N', size='0201', v='16V')
    g.TP('USB_LTE_DP', label='LTE_USB_DP')
    g.TP('USB_LTE_DN', label='LTE_USB_DN')
    g.R('1k', 'LTE_FCPO_N', 'LTE_FCPO_M2', note='FULL_CARD_POWER_OFF# (100k pull-down inside the module)')
    sot_nmos(g, 'LTE_RESET_N', 'LTE_RESET_CTL', 'GND')
    g.R('100k', 'LTE_RESET_CTL', 'GND', note='released by default')
    sot_nmos(g, 'LTE_WDIS_N', 'LTE_WDIS_CTL', 'GND')
    g.R('100k', 'LTE_WDIS_CTL', 'GND')
    g.R('10k', 'LTE_WAKE_N', 'VCC_1V8_S3', note='WAKE_ON_WAN# (OD) -> GPIO0_D3 (1.8 V, wake)')
    g.LED('red', 'LTE_LED_N', 'LTE_LED_A', size='0603')
    g.R('1k', 'VCC_LTE', 'LTE_LED_A', note='WWAN_LED# (OD, active low), ~1.8 mA')
    g.TP('LTE_RESET_N')

    g = sb.group('Modem supply decoupling (Quectel Fig. 8: 2 x 220 uF + 2 x (1 uF, 100 nF, 33 pF, 10 pF) + 5.1 V TVS)', '')
    pp = part('POSCAP_220U')
    for _ in range(2):
        g.part('C', d_sym('Device:C_Polarized'), '220uF 6.3V', {'1': 'VCC_LTE', '2': 'GND'}, pp['fp'],
               {'LCSC': pp['lcsc'], 'MPN': pp['mpn'], 'Manufacturer': pp['mfr'], 'Note': pp['note']})
    for _ in range(2):
        g.C('1uF', 'VCC_LTE', size='0402', v='10V')
        g.C('100nF', 'VCC_LTE', size='0402', v='10V')
        g.C('33pF', 'VCC_LTE', size='0402', v='50V')
        g.C('10pF', 'VCC_LTE', size='0402', v='50V')
    pt = part('SMF5V0A')
    g.D('Device:D_TVS', 'SMF5.0A', 'VCC_LTE', 'GND', pt['fp'], pt['lcsc'], pt['mpn'], pt['mfr'])

    g = sb.group('nano-SIM (push-push, right edge) - Quectel Fig. 14/15 + 4.1.7',
                 '22 Ohm series on RST/CLK/DATA, 33 pF to GND, 15k DATA pull-up to USIM_VDD, 100 nF on VCC, TVS array < 10 pF,\n'
                 'all close to the SIM connector. Card detect to USIM1_DET (enable with AT+QSIMDET; polarity set to the connector).')
    sim = part('NANOSIM')
    conn(g, 'NANOSIM', d.S['NANOSIM'], 'nano-SIM', {'C1': 'SIM_VDD', 'C2': 'SIM_RST', 'C3': 'SIM_CLK', 'C7': 'SIM_IO',
                                                     'C6': None, 'C5': 'GND', 'CD': 'SIM_DET', 'SH': 'GND'})
    g.R('22', 'SIM_RST_M2', 'SIM_RST')
    g.R('22', 'SIM_CLK_M2', 'SIM_CLK')
    g.R('22', 'SIM_IO_M2', 'SIM_IO')
    g.R('15k', 'SIM_IO', 'SIM_VDD', note='10-20k (Quectel 4.1.7)')
    for n in ('SIM_RST', 'SIM_CLK', 'SIM_IO'):
        g.C('33pF', n, size='0402', v='50V')
    g.C('100nF', 'SIM_VDD', size='0402', v='10V')
    esd4(g, 'SIM_VDD', 'SIM_RST', 'SIM_CLK', 'SIM_IO')
    return sb


# ============================================================================================ sheet 6
def sheet_wireless(d):
    sb = d.sheet('Wi-Fi 6 / BT 5 (AP6275P)', 'wireless.kicad_sch', paper='A3')
    g = sb.group('AMPAK AP6275P (BCM43752): PCIe Gen1 x1 on combo PHY0 (PCIE20_0, JP3), BT HCI UART9_M2 with RTS/CTS',
                 'Pins: AP6275P datasheet s.5.2. Support circuit after Khadas Edge2 V1.3 p.19 (AP6275P on RK3588S):\n'
                 'CBUCK/ABUCK 2.2 uH (<= 80 mOhm) + 4.7 uF, VBAT 22 uF + 100 nF via 120R bead, VDDIO 4.7 uF + 100 nF via bead,\n'
                 'PCIe 100 nF on both lane directions, 100 pF on REFCLK (as Edge2). VDDIO = VCC_1V8_S3 so Wi-Fi/BT survive suspend.\n'
                 'Control pins as the Orange Pi CM5 tablet board (Wi-Fi/BT on GPIO0, 1.8 V): WL_REG_ON GPIO0_D0, WL_HOST_WAKE GPIO0_A0,\n'
                 'BT_WAKE GPIO0_C6, BT_HOST_WAKE GPIO0_C5, UART9_M2; BT_REG_ON on GPIO0_C7 (tablet: D3, which has a default pull-up).')
    pa = part('AP6275P')
    gnd = ['1', '3', '4', '5', '6', '7', '8', '10', '11', '23', '27', '30', '32', '39']
    nets = {k: 'GND' for k in gnd}
    nets.update({'36': 'WL_VBAT', '34': 'WL_VDDIO', '25': 'WL_CBUCK', '26': 'WL_CSR_VLX', '28': 'WL_ASR_VLX',
                 '29': 'WL_ABUCK', '13': 'WL_XO_P', '14': 'WL_XO_N', '31': 'WIFI_LPO_32K', '15': 'WL_REG_ON',
                 '38': 'BT_REG_ON', '16': 'WL_HOST_WAKE', '49': 'BT_WAKE', '50': 'BT_HOST_WAKE', '2': 'WL_ANT0_M',
                 '9': 'WL_ANT1_M', '12': 'WL_PCIE_PERST_N', '37': 'WL_PCIE_CLKREQ_N', '24': 'WL_PCIE_PME_N',
                 '35': 'WL_REFCLK_P', '33': 'WL_REFCLK_N', '45': 'WL_PCIE_RX_P', '44': 'WL_PCIE_RX_N',
                 '47': 'WL_PCIE_TX_P', '46': 'WL_PCIE_TX_N', '40': 'BT_UART_RX', '41': 'BT_UART_TX',
                 '42': 'BT_UART_CTS_N', '43': 'BT_UART_RTS_N', '19': 'BT_PCM_OUT', '20': 'BT_PCM_IN', '21': 'BT_PCM_SYNC',
                 '22': 'BT_PCM_CLK', '17': None, '18': None, '48': None})
    g.ic(d.S['AP6275P'], 'AP6275P', nets, pa['fp'], lcsc=pa['lcsc'], mpn=pa['mpn'], mfr=pa['mfr'],
         note='software: BCM43752 firmware/NVRAM from the AMPAK / Rockchip BSP (Khadas Edge2 uses the same module)')
    fb2, fb4 = part('FB_120R_2A'), part('FB_120R_0402')
    g.FB('120R', 'VCC3V3_AUX', 'WL_VBAT', size='0603', lcsc=fb2['lcsc'], mpn=fb2['mpn'], mfr=fb2['mfr'])
    g.C('22uF', 'WL_VBAT', size='0603', v='10V')
    g.C('100nF', 'WL_VBAT')
    g.FB('120R', 'VCC_1V8_S3', 'WL_VDDIO', size='0402', lcsc=fb4['lcsc'], mpn=fb4['mpn'], mfr=fb4['mfr'])
    g.C('4.7uF', 'WL_VDDIO', size='0402', v='6.3V')
    g.C('100nF', 'WL_VDDIO')
    pl = part('L_2u2_WIFI')
    g.L('2.2uH', 'WL_CSR_VLX', 'WL_CBUCK', pl['fp'], pl['lcsc'], pl['mpn'], pl['mfr'])
    g.C('4.7uF', 'WL_CBUCK', size='0402', v='6.3V')
    g.L('2.2uH', 'WL_ASR_VLX', 'WL_ABUCK', pl['fp'], pl['lcsc'], pl['mpn'], pl['mfr'])
    g.C('4.7uF', 'WL_ABUCK', size='0402', v='6.3V')
    px = part('XTAL_37M4')
    g.part('Y', d_sym('Device:Crystal_GND24'), '37.4 MHz 16 pF', {'1': 'WL_XO_P', '3': 'WL_XO_N', '2': 'GND', '4': 'GND'},
           px['fp'], {'LCSC': px['lcsc'], 'MPN': px['mpn'], 'Manufacturer': px['mfr'],
                      'Note': 'AP6275P s.7: CL 18 pF, +-10/+-10 ppm, ESR < 60 Ohm'})
    g.C('27pF', 'WL_XO_P', size='0402', v='50V', note='C = 2 x (CL 16 pF) - ~5 pF stray; tune on first board')
    g.C('27pF', 'WL_XO_N', size='0402', v='50V')
    g.R('100k', 'WL_REG_ON', 'GND', note='module off until the SoC drives REG_ON')
    g.R('100k', 'BT_REG_ON', 'GND')
    for n in ('BT_PCM_OUT', 'BT_PCM_IN', 'BT_PCM_SYNC', 'BT_PCM_CLK'):
        g.TP(n)

    g = sb.group('PCIe lane and sidebands', 'Sidebands PCIE20X1_2 *_M0: CLKREQ# GPIO3_C7 (JP3.22), PERST# GPIO3_D1 (JP3.24), WAKE#\n'
                 'GPIO3_D0 (JP3.43) are 1.8 V on the Orange Pi CM5 = AP6275P VDDIO: direct. CLKREQ# / PME# are open-drain: 10k to 1.8 V.')
    for a, b in (('PCIE_TX_P', 'WL_PCIE_RX_P'), ('PCIE_TX_N', 'WL_PCIE_RX_N'), ('WL_PCIE_TX_P', 'PCIE_RX_P'),
                 ('WL_PCIE_TX_N', 'PCIE_RX_N')):
        g.C('100nF', a, b, size='0201', v='16V')
    g.C('100pF', 'PCIE_REFCLK_P', 'WL_REFCLK_P', size='0201', v='50V', note='as Edge2 (C383/C384)')
    g.C('100pF', 'PCIE_REFCLK_N', 'WL_REFCLK_N', size='0201', v='50V')
    gp = g

    g = sb.group('Antenna ports (2 x U.FL, 50 Ohm coplanar)', 'Series 0 Ohm + unfitted shunt pads for a pi match (as Edge2).')
    pu = part('UFL')
    for i in (0, 1):
        g.R('0', f'WL_ANT{i}_M', f'WL_ANT{i}', size='0201', note='match series element')
        g.C('DNP', f'WL_ANT{i}', size='0201', dnp=True, note='match shunt, not fitted')
        g.ic('Connector:Conn_Coaxial', 'U.FL', {'1': f'WL_ANT{i}', '2': 'GND'}, pu['fp'], lcsc=pu['lcsc'],
             mpn=pu['mpn'], mfr=pu['mfr'], prefix='J')
    # (made last so the antenna parts keep their references)
    gp.R('10k', 'WL_PCIE_CLKREQ_N', 'VCC_1V8_S3')
    gp.R('10k', 'WL_PCIE_PME_N', 'VCC_1V8_S3')
    return sb


# ============================================================================================ sheet 7
def sheet_display(d):
    sb = d.sheet('Display, touch, backlight, digitizer, cameras', 'display.kicad_sch', paper='A3')
    S = d.S
    g = sb.group('DisplayModule DMKDI0400S0CA (4.0" 720x720, ST7703, 4-lane DSI) - 30-pin 0.5 mm FPC',
                 'Panel spec V1.0.0 (2025) s.4.1. DSI1 4 lanes (JP2.75-96). RESET at IOVCC 1.8 V (GPIO3_A4, JP3.62). VCI 3.3 V via\n'
                 'TPS22919 on LCD_PWREN (GPIO4_A7, JP1.97). TE unused. Double-sided-contact connector: which face is up is fixed at placement.')
    fp30 = part('FPC30_DS')
    s30 = fpc_sym(d, 'FPC_30P', 30, fp30['fp'])
    # the panel's own pin numbers (spec V1.0.0 s.4.1, confirmed by DisplayModule 2026-11-10: 7 = D0N, 8 = D0P)
    panel = {1: None, 2: 'BL_LEDK', 3: None, 4: 'BL_LEDA', 5: None, 6: 'GND', 7: 'DSI_D0_N', 8: 'DSI_D0_P', 9: 'GND',
             10: 'DSI_D1_N', 11: 'DSI_D1_P', 12: 'GND', 13: 'DSI_CLK_N', 14: 'DSI_CLK_P', 15: 'GND', 16: 'DSI_D2_N',
             17: 'DSI_D2_P', 18: 'GND', 19: 'DSI_D3_N', 20: 'DSI_D3_P', 21: 'GND', 22: 'GND', 23: None, 24: 'GND',
             25: None, 26: 'LCD_RESET_N', 27: 'LCD_IOVCC', 28: 'LCD_VCI', 29: 'GND', 30: 'GND'}
    # D118: the tail arrives mirrored. DisplayModule's CAD drawing (2026-11-10) puts pin 1 at the right with the glass
    # facing you and the tail hanging down; with the FPC edge at the board's right edge that is the -y end, where the
    # footprint has pad 30. Connector pad k = panel pin 31 - k.
    conn(g, 'FPC30_DS', s30, 'Display FPC 30P', {**{str(31 - k): v for k, v in panel.items()}, 'MP': 'GND'})
    pfb = part('FB_120R_0402')
    g.FB('120R', 'VCC_1V8_S3', 'LCD_IOVCC', size='0402', lcsc=pfb['lcsc'], mpn=pfb['mpn'], mfr=pfb['mfr'])
    g.C('1uF', 'LCD_IOVCC', size='0402', v='10V')
    pls = part('TPS22919')
    g.ic('Power_Management:TPS22919DCK', 'TPS22919DCKR', {'1': 'VCC_3V3_S3', '2': 'GND', '3': 'LCD_PWREN', '4': None,
                                                         '5': 'LCD_VCI_QOD', '6': 'LCD_VCI'}, pls['fp'], lcsc=pls['lcsc'],
         mpn=pls['mpn'], mfr=pls['mfr'])
    g.R('100', 'LCD_VCI_QOD', 'LCD_VCI', note='quick output discharge, tFALL ~3.5 ms with 10 uF (TPS22919 DS)')
    g.C('1uF', 'VCC_3V3_S3', size='0402', v='10V')
    g.C('2.2uF', 'LCD_VCI', size='0402', v='10V')
    g.R('100k', 'LCD_PWREN', 'GND')

    g = sb.group('Backlight: TPS61169 LED boost, 12 LEDs 18.6 V / 40 mA (panel spec s.6.3)',
                 'TI SNVSA40B Fig. 7-1: L 4.7 uH, COUT 1 uF 50 V, Schottky 40 V. RSET = 204 mV / 40 mA = 5.1 Ohm. PWM dimming on CTRL\n'
                 '(5-100 kHz, PWM13_M1 = GPIO4_B6, JP1.95). OVP 38 V. Panel B/L circuit: 2 parallel strings of 6 LEDs, 18.6 +-0.3 V,\n'
                 '40 mA total.')
    pb = part('TPS61169')
    g.ic(S['TPS61169'], 'TPS61169DCKR', {'5': 'VSYS', '4': 'BL_PWM', '2': 'GND', '1': 'BL_SW', '3': 'BL_LEDK'},
         pb['fp'], lcsc=pb['lcsc'], mpn=pb['mpn'], mfr=pb['mfr'])
    pl4 = part('L_4u7_1A')
    g.L('4.7uH', 'VSYS', 'BL_SW', pl4['fp'], pl4['lcsc'], pl4['mpn'], pl4['mfr'], status=pl4['note'])
    psd = part('SCHOTTKY_40V_1A')
    g.D('Device:D_Schottky', 'B5819W', 'BL_LEDA', 'BL_SW', psd['fp'], psd['lcsc'], psd['mpn'], psd['mfr'])
    g.C('1uF', 'BL_LEDA', size='0805', v='50V')
    g.C('4.7uF', 'VSYS', size='0603', v='10V')
    g.R('5.1', 'BL_LEDK', 'GND', size='0603', note='1 %, sets 40 mA')
    g.R('100k', 'BL_PWM', 'GND', note='backlight off until the SoC drives PWM')

    g = sb.group('Capacitive touch (GT911 on the panel CTP tail, 8-pin 0.5 mm) on I2C6_M3 (JP1.80 / JP1.82, 3.3 V)',
                 'Panel spec s.4.2. INT also selects the GT911 address at reset (0x5D / 0x14). I2C6 is shared with the\n'
                 'keyboard (0x1F) and the reserved digitizer; pull-ups here.')
    fp8 = part('FPC8')
    s8 = fpc_sym(d, 'FPC_8P', 8, fp8['fp'])
    # the tail's own pin numbers (spec s.4.2); mirrored onto the connector as the display tail (D118): pad k = pin 9 - k
    ctp = {1: 'GND', 2: None, 3: 'VCC_3V3_S3', 4: 'I2C_TP_SCL', 5: 'I2C_TP_SDA', 6: 'TP_INT', 7: 'TP_RST_N', 8: 'GND'}
    conn(g, 'FPC8', s8, 'CTP FPC 8P', {**{str(9 - k): v for k, v in ctp.items()}, 'MP': 'GND'})
    g.C('1uF', 'VCC_3V3_S3', size='0402', v='10V')
    g.R('2.2k', 'I2C_TP_SDA', 'VCC_3V3_S3')
    g.R('2.2k', 'I2C_TP_SCL', 'VCC_3V3_S3')

    g = sb.group('Reserved digitizer port (decision Q1): hub port 4 USB, I2C6, INT, RST, 3.3 V - 12-pin 0.5 mm FFC',
                 'Pinout mirrors the keyboard FFC (USB pair between ground pins). 3.3 V switched by hub PRTPWR4 (TPS22919).')
    f12 = part('FFC12')
    s12 = fpc_sym(d, 'FFC_12P', 12, f12['fp'])
    conn(g, 'FFC12', s12, 'Digitizer FFC 12P', {'1': 'GND', '2': 'DIG_3V3', '3': 'DIG_3V3', '4': 'GND', '5': 'DIG_DN',
                                                 '6': 'DIG_DP', '7': 'GND', '8': 'I2C_TP_SDA', '9': 'I2C_TP_SCL',
                                                 '10': 'DIG_INT_N', '11': 'DIG_RST_N', '12': 'GND', 'MP': 'GND'})
    g.ic('Power_Management:TPS22919DCK', 'TPS22919DCKR', {'1': 'VCC3V3_AUX', '2': 'GND', '3': 'HUB_PRTPWR4', '4': None,
                                                         '5': 'DIG_3V3_QOD', '6': 'DIG_3V3'}, pls['fp'], lcsc=pls['lcsc'],
         mpn=pls['mpn'], mfr=pls['mfr'])
    g.R('100', 'DIG_3V3_QOD', 'DIG_3V3', note='quick output discharge')
    g.C('1uF', 'VCC3V3_AUX', size='0402', v='10V')
    g.C('10uF', 'DIG_3V3', size='0603', v='10V')
    g.R('10k', 'DIG_INT_N', 'VCC_3V3_S3')
    g.R('10k', 'DIG_RST_N', 'VCC_3V3_S3')

    g = sb.group('CAM-A (rear): 4-lane CSI (MIPI_CSI0 D-PHY, JP2 odd pins) - Hirose FH35C-31S, Radxa 31-pin camera standard',
                 'Rear camera: Radxa Camera 13M 214 (Sony IMX214 13 MP, autofocus DW9714, HDR), Radxa 31p 0.3 mm opposite-side cable.\n'
                 'Orange Pi CM5: I2C3_M1 (GPIO3_B7 / C0, JP3.34 / 72), MCLK MIPI_CAMERA1_CLK_M1 (GPIO3_A6, JP3.52), PDN GPIO3_C5,\n'
                 'RST GPIO3_C6, all 1.8 V; device tree needs a custom overlay. I2C 2.2k pull-ups to 1.8 V. 3.3 V via 120R bead, 5 V via 0 Ohm.')
    ph = part('FH35C31')
    s31 = fpc_sym(d, 'FPC_31P', 31, ph['fp'])
    cam = {1: 'GND', 2: 'CSIA_D3_N', 3: 'CSIA_D3_P', 4: 'GND', 5: 'CSIA_D2_N', 6: 'CSIA_D2_P', 7: 'GND', 8: None, 9: None,
           10: 'GND', 11: 'CSIA_D1_N', 12: 'CSIA_D1_P', 13: 'GND', 14: 'CSIA_D0_N', 15: 'CSIA_D0_P', 16: 'GND',
           17: 'CSIA_CLK_N', 18: 'CSIA_CLK_P', 19: 'GND', 20: 'CAMA_MCLK_C', 21: 'GND', 22: None, 23: 'CAMA_PDN_C',
           24: 'I2C_CAMA_SCL', 25: 'I2C_CAMA_SDA', 26: None, 27: 'CAMA_RST_C', 28: 'CAMA_3V3', 29: 'CAMA_3V3',
           30: 'CAMA_5V', 31: 'CAMA_5V'}
    conn(g, 'FH35C31', s31, 'CAM-A FH35C-31S', {**{str(k): v for k, v in cam.items()}, 'MP': 'GND'},
         note='rear camera (Radxa Camera 13M 214), 4 lanes, Radxa 31-pin camera pinout (Radxa CM5 IO board Camera 1)')
    g.R('0', 'CAMA_MCLK', 'CAMA_MCLK_C', note='as IO board R715')
    g.C('DNP', 'CAMA_MCLK_C', size='0402', dnp=True, note='as IO board C750 (NC)')
    g.R('0', 'CAMA_PDN', 'CAMA_PDN_C')
    g.R('0', 'CAMA_RST_N', 'CAMA_RST_C')
    g.R('2.2k', 'I2C_CAMA_SCL', 'VCC_1V8_S3')
    g.R('2.2k', 'I2C_CAMA_SDA', 'VCC_1V8_S3')
    g.FB('120R', 'VCC3V3_AUX', 'CAMA_3V3', size='0402', lcsc=pfb['lcsc'], mpn=pfb['mpn'], mfr=pfb['mfr'])
    g.C('10uF', 'CAMA_3V3', size='0603', v='10V')
    g.C('100nF', 'CAMA_3V3')
    g.R('0', 'VCC5V0', 'CAMA_5V', size='0603')
    g.C('22uF', 'CAMA_5V', size='0805', v='10V')
    g.C('100nF', 'CAMA_5V', size='0402', v='16V')

    g = sb.group('CAM-B (front): 2-lane CSI (MIPI_DPHY0_RX = DC-PHY0 in D-PHY mode, JP2 even pins) - Hirose FH35C-31S',
                 'Front camera: Radxa Camera 8M 219 (Sony IMX219 8 MP) through Radxa 31-pin 0.3 mm -> 15-pin 1.0 mm same-side cable\n'
                 '(as on ROCK 5A/5B/5C). Lanes 0/1 + CLK only; pins 2/3, 5/6, 8/9, 22, 26, 30/31 open. I2C2_M4 (GPIO1_A0 / A1,\n'
                 'JP2.2 / 4) at 3.3 V with 2.2k pull-ups here. PDN0 (23) = GPIO3_C4, RESET (27) = GPIO3_A1, MCLK (20) = GPIO3_A7, 1.8 V.')
    camb = {1: 'GND', 2: None, 3: None, 4: 'GND', 5: None, 6: None, 7: 'GND', 8: None, 9: None, 10: 'GND',
            11: 'CSIB_D1_N', 12: 'CSIB_D1_P', 13: 'GND', 14: 'CSIB_D0_N', 15: 'CSIB_D0_P', 16: 'GND',
            17: 'CSIB_CLK_N', 18: 'CSIB_CLK_P', 19: 'GND', 20: 'CAMB_MCLK_C', 21: 'GND', 22: None, 23: 'CAMB_IO0_C',
            24: 'I2C_CAMB_SCL', 25: 'I2C_CAMB_SDA', 26: None, 27: 'CAMB_IO1_C', 28: 'CAMB_3V3', 29: 'CAMB_3V3',
            30: None, 31: None}
    conn(g, 'FH35C31', s31, 'CAM-B FH35C-31S', {**{str(k): v for k, v in camb.items()}, 'MP': 'GND'},
         note='front camera (Radxa Camera 8M 219 via the Radxa 31p -> 15p cable), 2 lanes on DC-PHY0')
    g.R('0', 'CAMB_IO0', 'CAMB_IO0_C')
    g.R('0', 'CAMB_IO1', 'CAMB_IO1_C')
    g.R('0', 'CAMB_MCLK', 'CAMB_MCLK_C', note='MIPI_CAMERA2_CLK_M1, for modules without an oscillator')
    g.R('2.2k', 'I2C_CAMB_SCL', 'VCC_3V3_S3', note='the Radxa CM5 had these on the module')
    g.R('2.2k', 'I2C_CAMB_SDA', 'VCC_3V3_S3')
    g.FB('120R', 'VCC3V3_AUX', 'CAMB_3V3', size='0402', lcsc=pfb['lcsc'], mpn=pfb['mpn'], mfr=pfb['mfr'])
    g.C('10uF', 'CAMB_3V3', size='0603', v='10V')
    g.C('100nF', 'CAMB_3V3')
    return sb


# ============================================================================================ sheet 8
def sheet_audio(d):
    sb = d.sheet('Audio: 2 x class-D amplifier, speakers, PDM microphone', 'audio.kicad_sch', paper='A3')
    g = sb.group('2 x MAX98357A on I2S0 (JP3.69-71, 1.8 V, VIH 1.3 V), supplied from VSYS',
                 'Maxim MAX98357A/B: SD_MODE high (via 2k) = left channel, 210k (Table 6, 3.3 V) = right, low = shutdown\n'
                 '(100k internal pull-down). One 3.3 V GPIO (GPIO4_A2, JP2.9) controls both. GAIN_SLOT open = 9 dB. No MCLK needed.')
    pa = part('MAX98357A')
    pj = part('JST_SH2')
    for ch, rsd in (('L', '2k'), ('R', '210k')):
        g.ic(d.S['MAX98357A'], f'MAX98357AETE+T ({ch})', {'1': 'I2S0_SDO', '2': None, '3': 'GND', '4': f'AMP_{ch}_SDMODE',
                                                          '7': 'VSYS', '9': f'SPK_{ch}_P', '10': f'SPK_{ch}_N', '14': 'I2S0_LRCK',
                                                          '16': 'I2S0_BCLK', '17': 'GND'},
             pa['fp'], lcsc=pa['lcsc'], mpn=pa['mpn'], mfr=pa['mfr'])
        g.R(rsd, 'AMP_SD_MODE', f'AMP_{ch}_SDMODE', note='1 %')
        g.C('10uF', 'VSYS', size='0603', v='10V')
        g.C('100nF', 'VSYS', size='0402', v='16V')
        g.ic('Connector_Generic_MountingPin:Conn_01x02_MountingPin', f'Speaker {ch}',
             {'1': f'SPK_{ch}_P', '2': f'SPK_{ch}_N', 'MP': 'GND'}, pj['fp'], lcsc=pj['lcsc'], mpn=pj['mpn'],
             mfr=pj['mfr'], prefix='J')

    g = sb.group('PDM MEMS microphone (Knowles SPH0641LU4H-1) on PDM0_M0 (GPIO1_C6 / D5, JP1.48 / 49, GPIO_VREF = 3.3 V)',
                 'Mic VDD 3.3 V (1.62-3.6 V, VIH 0.7 x VDD) to match the clock level. SEL low = data valid on the clock low phase\n'
                 '(channel set in the device tree).')
    pm = part('SPH0641')
    g.ic('Sensor_Audio:SPH0641LU4H-1', 'SPH0641LU4H-1', {'1': 'PDM_DATA', '2': 'GND', '3': 'GND', '4': 'PDM_CLK',
                                                         '5': 'VCC_3V3_S3'}, pm['fp'], lcsc=pm['lcsc'], mpn=pm['mpn'],
         mfr=pm['mfr'])
    g.C('100nF', 'VCC_3V3_S3')
    return sb


# ============================================================================================ sheet 9
def sheet_storage(d):
    sb = d.sheet('microSD', 'storage.kicad_sch', paper='A3')
    g = sb.group('microSD push-push (right edge) on SDMMC (JP1.57-69) - circuit as the Radxa CM5 IO board p.6',
                 '22 Ohm on CLK, ESD on all 7 lines, card detect to GPIO0_A4 (JP1.76, 1.8 V) with 100k to VCC_1V8_S3. VDD from\n'
                 'VCC_3V3_S3 through a 0 Ohm link. JP1.75 (SDMMC_PWREN) is left open: it is GPIO0_A5, the module PMIC\'s SPI2 clock\n'
                 '(SPI2_CLK_M2, rk3588-rk806-single.dtsi), D105.')
    ps = part('MICROSD')
    g.ic('Connector:Micro_SD_Card_Det_Hirose_DM3AT', 'DM3AT-SF-PEJM5', {
        '1': 'SD_D2', '2': 'SD_D3', '3': 'SD_CMD', '4': 'SD_VDD', '5': 'SD_CLK', '6': 'GND', '7': 'SD_D0', '8': 'SD_D1',
        '9': 'GND', '10': 'SD_DET_N', 'SH': 'GND'}, ps['fp'], lcsc=ps['lcsc'], mpn=ps['mpn'], mfr=ps['mfr'], prefix='J',
        note='Hirose DM3AT p.3: detect switch open without a card, closed with a card -> SD_DET_N low = card present')
    g.R('22', 'SD_CLK_SOC', 'SD_CLK')
    g.R('100k', 'SD_DET_N', 'VCC_1V8_S3')
    g.R('0', 'VCC_3V3_S3', 'SD_VDD', size='0603', note='SD card always powered from VCC_3V3_S3')
    g.C('10uF', 'SD_VDD', size='0603', v='10V')
    g.C('100nF', 'SD_VDD')
    esd4(g, 'SD_CLK', 'SD_CMD', 'SD_D0', 'SD_D1')
    esd4(g, 'SD_D2', 'SD_D3', 'SD_DET_N', None)
    return sb


# ============================================================================================ sheet 10
def sheet_keyboard(d):
    sb = d.sheet('Keyboard interface (FFC to Board B)', 'keyboard.kicad_sch', paper='A3')
    g = sb.group('Keyboard FFC, 12-pin 0.5 mm (identical pinout on Board B)',
                 '1 GND, 2-3 +5V_KBD, 4 GND, 5 D-, 6 D+, 7 GND, 8 SDA, 9 SCL, 10 INT#, 11 RESET#, 12 BOOT#.\n'
                 'USB from hub port 3; I2C6 (3.3 V) to the RP2040 (0x1F, i2c_puppet). INT# on GPIO0_D4 (JP3.81, 1.8 V, can wake the\n'
                 'SoC): Board B drives it through a BSS138, so the pull-up here sets the level. RESET# / BOOT# open-drain from 3.3 V GPIOs.\n'
                 '+5V_KBD: TPS2553 on hub PRTPWR3, 0.61-0.74 A limit (2 FFC conductors).')
    f12 = part('FFC12')
    s12 = fpc_sym(d, 'FFC_12P', 12, f12['fp'])
    conn(g, 'FFC12', s12, 'Keyboard FFC 12P', {'1': 'GND', '2': 'VCC5V_KBD', '3': 'VCC5V_KBD', '4': 'GND',
                                                '5': 'KBD_DN', '6': 'KBD_DP', '7': 'GND', '8': 'I2C_TP_SDA',
                                                '9': 'I2C_TP_SCL', '10': 'KBD_INT_FFC', '11': 'KBD_RESET_N',
                                                '12': 'KBD_BOOT_N', 'MP': 'GND'})
    ps = part('TPS2553')
    g.ic(d.S['TPS2553'], 'TPS2553DBVR', {'1': 'VCC5V0', '2': 'GND', '3': 'HUB_PRTPWR3', '4': 'HUB_OCS3_N',
                                         '5': 'KBD_ILIM', '6': 'VCC5V_KBD'}, ps['fp'], lcsc=ps['lcsc'], mpn=ps['mpn'],
         mfr=ps['mfr'])
    g.R('39k', 'KBD_ILIM', 'GND', note='1 %')
    g.R('10k', 'HUB_OCS3_N', 'VCC3V3_AUX')
    g.C('100nF', 'VCC5V0', size='0402', v='16V')
    g.C('10uF', 'VCC5V_KBD', size='0603', v='10V')
    g.R('1k', 'KBD_INT_N', 'KBD_INT_FFC', note='series protection')
    g.R('10k', 'KBD_INT_N', 'VCC_1V8_S3')
    esd4(g, 'KBD_DP', 'KBD_DN', 'KBD_INT_FFC', 'KBD_RESET_N')
    g.TP('VCC5V_KBD')

    g = sb.group('Additional rail test pads', 'Brief: test points on all rails.')
    for n in ('BL_LEDA', 'LCD_VCI', 'LCD_IOVCC', 'DIG_3V3', 'SD_VDD', 'WL_VBAT', 'WL_VDDIO', 'USBA1_VBUS', 'USBA2_VBUS',
              'CAMA_3V3', 'CAMA_5V', 'CAMB_3V3'):
        g.TP(n)
    return sb
