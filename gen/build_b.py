#!/usr/bin/env python3
"""Generate Board B (BlackBerry Q20 keyboard board) schematics, run ERC and check the netlist.
Derived from Solder Party BBQ20KBD (CERN-OHL v1.2): same RP2040 GPIO map, so the i2c_puppet firmware
(board 'bbq20kbd_breakout') runs unchanged. Changes: USB-C/Stemma/PMOD replaced by the 12-pin FFC to the
carrier; host I2C isolated with BSS138 so an unpowered keyboard board does not clamp the carrier's shared I2C6 bus
(touch panel on the same bus); INT# through an open-drain buffer with power-off isolation, since the carrier pulls it
up to 1.8 V (D109).
usage: python3 -I gen/build_b.py"""
import json
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dsl
import libwriter
import symbols
import verify
from parts import PARTS

OUT = os.path.join(HERE, '..', 'hw', 'board_b')
NAME = 'q20_keyboard'

PARTS.update({
    'RP2040': ('C2040', 'RP2040', 'Raspberry Pi', 'Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm', ''),
    'W25Q16': ('C131025', 'W25Q16JVSSIQ', 'Winbond', 'Package_SO:SOIC-8_5.3x5.3mm_P1.27mm', ''),
    'XTAL_12M': ('C20625731', 'ABM8-272-T3', 'Abracon', 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm', 'CL 10 pF'),
    'AP2112K33': ('C51118', 'AP2112K-3.3TRG1', 'Diodes Inc', 'Package_TO_SOT_SMD:SOT-23-5', ''),
    'ME6212_18': ('C236669', 'ME6212C18M5G', 'Microne', 'Package_TO_SOT_SMD:SOT-23-5', 'pinout = AP2112K (ME6212 DS)'),
    'ME6212_28': ('C427596', 'ME6212C28M5G', 'Microne', 'Package_TO_SOT_SMD:SOT-23-5', 'pinout = AP2112K (ME6212 DS)'),
    'BSS138': ('C40912', 'BSS138-7-F', 'Diodes Inc', 'Package_TO_SOT_SMD:SOT-23', ''),
    'LVC1G07': ('C7829', 'SN74LVC1G07DBVR', 'Texas Instruments', 'Package_TO_SOT_SMD:SOT-23-5',
                'TI SCES296 pin functions, DBV: 1 NC, 2 A, 3 GND, 4 Y (open drain), 5 VCC; Ioff'),
    'BM20B': ('C424543', 'BM20B(0.8)-40DS-0.4V(51)', 'Hirose', 'cm5h:Hirose_BM20B_0.8_-40DS-0.4V',
              'BBQ20KBD footprint (40 contacts + 4 hold-down pads)'),
})
from parts import part


def P(g, key, sym, value, nets, prefix='U', note='', status=''):
    p = part(key)
    return g.ic(sym, value, nets, p['fp'], lcsc=p['lcsc'], mpn=p['mpn'], mfr=p['mfr'], prefix=prefix,
                note=note or p['note'], status=status)


def bss138(g, d_, gate, s_, note=''):
    return P(g, 'BSS138', 'Transistor_FET:BSS138', 'BSS138', {'1': gate, '2': s_, '3': d_}, prefix='Q', note=note)


def build():
    d = dsl.Design(NAME, 'Q20 keyboard board (Board B)')
    S = d.S = {}
    # ------------------------------------------------------------------ sheet 1
    sb = d.sheet('RP2040, power, carrier FFC', 'mcu.kicad_sch', paper='A3')
    g = sb.group('Carrier FFC, 12-pin 0.5 mm (pinout identical to Board A J1001)',
                 '1 GND, 2-3 +5V, 4 GND, 5 D-, 6 D+, 7 GND, 8 SDA, 9 SCL, 10 INT#, 11 RESET#, 12 BOOT#.\n'
                 'Cable type (same-side / opposite-side contacts) chosen at checkpoint 3 so that pin n meets pin n.')
    f12 = part('FFC12')
    S['FFC_12P'] = symbols.fpc(d, 'FFC_12P', 12, 'FFC_12P', f12['fp'])
    g.ic(S['FFC_12P'], 'Carrier FFC 12P', {'1': 'GND', '2': 'VBUS_KBD', '3': 'VBUS_KBD', '4': 'GND', '5': 'USB_DN',
                                          '6': 'USB_DP', '7': 'GND', '8': 'HOST_SDA', '9': 'HOST_SCL', '10': 'HOST_INT_N',
                                          '11': 'HOST_RESET_N', '12': 'HOST_BOOT_N', 'MP': 'GND'},
         f12['fp'], lcsc=f12['lcsc'], mpn=f12['mpn'], mfr=f12['mfr'], prefix='J')

    g = sb.group('3.3 V LDO (as BBQ20KBD)', 'AP2112K-3.3, 600 mA, from the carrier 5 V (current-limited there to 0.61-0.74 A).')
    P(g, 'AP2112K33', 'Regulator_Linear:AP2112K-3.3', 'AP2112K-3.3', {'1': 'VBUS_KBD', '2': 'GND', '3': 'VBUS_KBD',
                                                                     '4': None, '5': '+3V3'})
    g.C('10uF', 'VBUS_KBD', size='0603', v='10V')
    g.C('10uF', '+3V3', size='0603')

    g = sb.group('RP2040 + 16 Mbit QSPI flash + 12 MHz crystal',
                 'As BBQ20KBD: IOVDD 5 x 100 nF + 1 uF, DVDD 2 x 100 nF + 1 uF, RUN 10k pull-up, QSPI_SS 10k pull-up,\n'
                 'USB 27 Ohm series, XOUT 1k series. Crystal ABM8-272-T3 CL 10 pF: C = 2 x (10 - ~3 pF stray) = 15 pF.\n'
                 'Firmware: i2c_puppet (MIT), board bbq20kbd_breakout - host I2C target 0x1F on GPIO28/29.')
    pin = {'1': '+3V3', '43': '+3V3', '44': '+3V3', '48': '+3V3', '23': 'DVDD', '45': 'DVDD', '57': 'GND', '19': 'GND',
           '2': 'KB_INT', '3': 'ROW1', '4': 'ROW2', '5': 'ROW3', '6': 'ROW4', '7': 'ROW5', '8': 'ROW6', '9': 'ROW7',
           '11': 'COL1', '12': 'COL2', '17': 'COL3', '16': 'COL4', '15': 'COL5', '14': 'COL6', '13': 'BOOTSEL_COL7',
           '18': None, '27': 'TP_RESET', '28': None, '29': 'TP_SDA', '30': None, '31': 'DBG_TX', '32': None,
           '34': 'TP_MOTION', '35': 'TP_SCL', '36': 'TP_SHUTDOWN', '37': 'BACKLIGHT', '38': None, '39': 'MIC',
           '40': 'KB_SDA', '41': 'KB_SCL', '20': 'XIN', '21': 'XOUT', '24': 'SWCLK', '25': 'SWDIO', '26': 'RUN',
           '46': 'USB_DN_MCU', '47': 'USB_DP_MCU', '51': 'QSPI_SD3', '52': 'QSPI_SCLK', '53': 'QSPI_SD0',
           '54': 'QSPI_SD2', '55': 'QSPI_SD1', '56': 'QSPI_SS'}
    P(g, 'RP2040', 'MCU_RaspberryPi:RP2040', 'RP2040', pin, note='GPIO map identical to BBQ20KBD (i2c_puppet)')
    for _ in range(5):
        g.C('100nF', '+3V3')
    g.C('1uF', '+3V3')
    g.C('100nF', 'DVDD')
    g.C('100nF', 'DVDD')
    g.C('1uF', 'DVDD')
    P(g, 'W25Q16', 'Memory_Flash:W25Q16JVSS', 'W25Q16JVSSIQ', {'1': 'QSPI_SS', '2': 'QSPI_SD1', '3': 'QSPI_SD2',
                                                              '4': 'GND', '5': 'QSPI_SD0', '6': 'QSPI_SCLK',
                                                              '7': 'QSPI_SD3', '8': '+3V3'})
    g.C('100nF', '+3V3')
    g.R('10k', 'QSPI_SS', '+3V3')
    g.R('1k', 'QSPI_SS', 'BOOTSEL_COL7', note='as BBQ20KBD R3: BOOTSEL test pad / COL7 key')
    g.R('1k', 'QSPI_SS', 'BOOT_ISO', note='keeps the isolator capacitance off the flash chip-select')
    g.R('10k', 'RUN', '+3V3')
    g.R('27', 'USB_DN_MCU', 'USB_DN')
    g.R('27', 'USB_DP_MCU', 'USB_DP')
    px = part('XTAL_12M')
    g.part('Y', symlib_load('Device:Crystal_GND24'), '12 MHz 10 pF', {'1': 'XIN', '3': 'XOUT_X', '2': 'GND', '4': 'GND'},
           px['fp'], {'LCSC': px['lcsc'], 'MPN': px['mpn'], 'Manufacturer': px['mfr']})
    g.R('1k', 'XOUT', 'XOUT_X')
    g.C('15pF', 'XIN', size='0402', v='50V')
    g.C('15pF', 'XOUT_X', size='0402', v='50V')
    for n, lab in (('SWCLK', 'SWCLK'), ('SWDIO', 'SWDIO'), ('RUN', 'RUN'), ('BOOTSEL_COL7', 'BOOTSEL'),
                   ('DBG_TX', 'UART_TX'), ('GND', 'GND'), ('+3V3', '3V3')):
        g.TP(n, fp='TestPoint:TestPoint_Pad_D1.5mm', label=f'TP_{lab}')

    g = sb.group('Host I2C / INT / RESET / BOOT isolation (BSS138, gate on the local 3.3 V; INT# open-drain buffer)',
                 'When Board B is unpowered the FETs are off and their body diodes reverse-biased, so the carrier I2C6 bus\n'
                 '(touch panel) is not clamped and the RP2040 is not back-powered. Carrier side pull-ups are on Board A.\n'
                 'INT#: the carrier pulls it up to 1.8 V (wake pin GPIO0_D4), below this side\'s 3.3 V, where a BSS138\'s body\n'
                 'diode would conduct into it; the open-drain buffer only pulls low and is high-impedance unpowered (D109).')
    for host, local in (('HOST_SDA', 'KB_SDA'), ('HOST_SCL', 'KB_SCL'), ('HOST_INT_N', 'KB_INT')):
        if host == 'HOST_INT_N':
            P(g, 'LVC1G07', '74xGxx:74LVC1G07', 'SN74LVC1G07DBVR',
              {'1': None, '2': local, '3': 'GND', '4': host, '5': '+3V3'})
            g.C('100nF', '+3V3', size='0402', v='16V')
        else:
            bss138(g, host, '+3V3', local)
        g.R('10k', local, '+3V3')
    bss138(g, 'HOST_RESET_N', '+3V3', 'RUN', note='carrier RESET# pulls RUN low; isolated when unpowered')
    bss138(g, 'HOST_BOOT_N', '+3V3', 'BOOT_ISO', note='carrier BOOT# pulls QSPI_SS low via 1k (BOOTSEL)')
    for i in (1, 2):
        g.part('H', symlib_load('Mechanical:MountingHole'), f'M2.5 hole {i}', {}, 'MountingHole:MountingHole_2.7mm_M2.5',
               {'Sourcing': 'PCB', 'Note': 'positions as BBQ20KBD'})

    # ------------------------------------------------------------------ sheet 2
    sb = d.sheet('Q20 keyboard connector, trackpad level shifters, backlight', 'keyboard.kicad_sch', paper='A3')
    g = sb.group('BlackBerry Q20 keyboard flex - Hirose BM20B(0.8)-40DS-0.4V(51) (pinout from BBQ20KBD netlist)',
                 'Trackpad I2C (0x3B) and control at 1.8 V; key backlight LEDs between LEDA (3.3 V) and LEDK (BSS138 low side, PWM).\n'
                 'MIC_VDD through an open solder jumper (microphone unused, as BBQ20KBD).')
    S['BM20B'] = dsl.box(d, 'Hirose_BM20B_40P', [(str(i), str(i), 'passive', 'L' if i <= 20 else 'R') for i in range(1, 41)],
                         ref='J', description='Hirose BM20B(0.8)-40DS-0.4V(51) receptacle for the BlackBerry Q20 keyboard flex')
    pb = part('BM20B')
    kb = {1: 'GND', 2: 'TP_SHUTDOWN_1V8', 3: 'TP_SCL_1V8', 4: 'TP_MOTION_1V8', 5: 'TP_SDA_1V8', 6: 'TP_RESET_1V8',
          7: 'GND', 8: '+2V8', 9: 'GND', 10: '+1V8', 11: 'GND', 12: 'COL1', 13: 'COL2', 14: 'COL3', 15: 'COL4',
          16: 'COL5', 17: 'COL6', 18: 'BOOTSEL_COL7', 19: 'GND', 20: 'GND', 21: 'GND', 22: 'GND', 23: 'MIC',
          24: 'MIC_VDD', 25: 'GND', 26: 'ROW7', 27: 'ROW6', 28: 'ROW5', 29: 'ROW4', 30: 'ROW3', 31: 'ROW2', 32: 'ROW1',
          33: 'LEDK', 34: '+3V3', 35: 'LEDK', 36: '+3V3', 37: 'LEDK', 38: None, 39: None, 40: 'GND'}
    g.ic(S['BM20B'], 'BM20B(0.8)-40DS-0.4V(51)', {str(k): v for k, v in kb.items()}, pb['fp'], lcsc=pb['lcsc'],
         mpn=pb['mpn'], mfr=pb['mfr'], prefix='J')
    g.part('JP', symlib_load('Jumper:SolderJumper_2_Open'), 'MIC_VDD', {'1': '+3V3', '2': 'MIC_VDD'},
           'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', {'Sourcing': 'PCB', 'Note': 'open'})

    g = sb.group('Trackpad level shifters 3.3 V <-> 1.8 V (BSS138, as BBQ20KBD)', '10k pull-ups on both sides, gate on +1V8.')
    for sig in ('TP_SHUTDOWN', 'TP_SCL', 'TP_MOTION', 'TP_SDA', 'TP_RESET'):
        bss138(g, sig, '+1V8', f'{sig}_1V8')
        g.R('10k', sig, '+3V3')
        g.R('10k', f'{sig}_1V8', '+1V8')

    g = sb.group('Keyboard flex supplies 1.8 V / 2.8 V and backlight switch', 'ME6212 (SOT-23-5, pinout = AP2112K). 1 uF in/out.')
    P(g, 'ME6212_18', 'Regulator_Linear:AP2112K-3.3', 'ME6212C18M5G', {'1': '+3V3', '2': 'GND', '3': '+3V3', '4': None,
                                                                     '5': '+1V8'})
    g.C('1uF', '+1V8')
    P(g, 'ME6212_28', 'Regulator_Linear:AP2112K-3.3', 'ME6212C28M5G', {'1': '+3V3', '2': 'GND', '3': '+3V3', '4': None,
                                                                     '5': '+2V8'})
    g.C('1uF', '+2V8')
    g.C('1uF', '+3V3')
    bss138(g, 'LEDK', 'BACKLIGHT', 'GND', note='backlight PWM (GPIO25)')
    g.R('10k', 'BACKLIGHT', 'GND')
    return d


def symlib_load(lib_id):
    import symlib
    return symlib.load(lib_id)


def main():
    d = build()
    os.makedirs(OUT, exist_ok=True)
    flags = d.proj.write(OUT)
    libwriter.write_project_libs(OUT, d.symbols)
    verify.write_project_file(OUT, NAME)
    viol = verify.run_erc(OUT, NAME)
    errs = [v for v in viol if v[0] == 'error']
    print(f'ERC: {len(errs)} errors, {len(viol) - len(errs)} warnings; PWR_FLAG nets: {flags}')
    for v in viol:
        print('  ', v[0], v[1], '|', v[2], '|', v[3], '|', '; '.join(v[4])[:200])
    # schematic group of every part (the PCB placer anchors passives to an IC of their own group)
    groups = {p.ref: t.split('\n')[0] for sb in d.sheets for t, ps in sb.sheet.groups for p in ps}
    json.dump(groups, open(os.path.join(OUT, 'groups.json'), 'w'), indent=0, sort_keys=True)
    nets, comps = verify.export_netlist(OUT, NAME)
    probs = verify.compare(d.proj.expected_netlist(), nets)
    print(f'netlist: {len(nets)} nets, {len(comps)} components, {len(probs)} mismatches')
    for p in probs[:50]:
        print('  ', p)
    open(os.path.join(OUT, 'missing_passives.txt'), 'w').write('\n'.join(sorted(d.missing_passives)) + '\n')
    print('passives without LCSC mapping:', sorted(d.missing_passives))
    return d


if __name__ == '__main__':
    main()
