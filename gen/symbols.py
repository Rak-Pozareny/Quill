"""Custom schematic symbols (project library `cm5h`), built from datasheet pin tables.

Every entry cites the table it was taken from. Pin types are chosen for ERC: one pin per supply net
is power_out/power_in, duplicates are passive, analog/power-stage pins are passive.
"""
import json
import os

from dsl import box

HERE = os.path.dirname(os.path.abspath(__file__))
P, I, O, B, OC, PI, PO, NC = 'passive', 'input', 'output', 'bidirectional', 'open_collector', 'power_in', 'power_out', 'no_connect'


def make_all(d):
    S = {}

    # BQ25713 -- TI SLUSD83C Table 7-1 (RSN WQFN-32, thermal pad = PGND)
    S['BQ25713'] = box(d, 'BQ25713', [
        ('1', 'VBUS', PI, 'L'), ('3', 'ACP', P, 'L'), ('2', 'ACN', P, 'L'), ('7', 'VDDA', P, 'L'),
        ('6', 'ILIM_HIZ', I, 'L'), ('18', 'CELL_BATPRESZ', I, 'L'), ('5', 'OTG/VAP', I, 'L'), ('14', 'CMPIN', I, 'L'),
        ('12', 'SDA', B, 'L'), ('13', 'SCL', I, 'L'), ('4', 'CHRG_OK', OC, 'L'), ('11', '~{PROCHOT}', OC, 'L'),
        ('15', 'CMPOUT', OC, 'L'), ('8', 'IADPT', P, 'L'), ('9', 'IBAT', P, 'L'), ('10', 'PSYS', P, 'L'),
        ('16', 'COMP1', P, 'L'), ('17', 'COMP2', P, 'L'),
        ('31', 'HIDRV1', O, 'R'), ('32', 'SW1', P, 'R'), ('30', 'BTST1', P, 'R'), ('29', 'LODRV1', O, 'R'),
        ('24', 'HIDRV2', O, 'R'), ('23', 'SW2', P, 'R'), ('25', 'BTST2', P, 'R'), ('26', 'LODRV2', O, 'R'),
        ('28', 'REGN', PO, 'R'), ('22', 'VSYS', P, 'R'), ('21', 'BATDRV', O, 'R'), ('20', 'SRP', P, 'R'),
        ('19', 'SRN', P, 'R'), ('27', 'PGND', PI, 'R'), ('33', 'EP(PGND)', P, 'R')],
        description='NVDC buck-boost charge controller, I2C 0x6B (TI SLUSD83C)',
        footprint='Package_DFN_QFN:Texas_RSN0032A_WQFN-32-1EP_4x4mm_P0.4mm', datasheet='https://www.ti.com/lit/ds/symlink/bq25713.pdf')

    # MAX17055 -- Maxim 19-8708 Rev 0 pin description (TDFN-10, EP -> CSP)
    S['MAX17055'] = box(d, 'MAX17055', [
        ('10', 'BATT', PI, 'L'), ('2', 'AIN', P, 'L'), ('9', 'THRM', P, 'L'), ('3', 'SCL', I, 'L'), ('4', 'SDA', B, 'L'),
        ('8', '~{ALRT}', OC, 'L'), ('1', 'NC', NC, 'L'),
        ('7', 'REG', P, 'R'), ('5', 'CSN', P, 'R'), ('6', 'CSP', PI, 'R'), ('11', 'EP(CSP)', P, 'R')],
        description='1-cell fuel gauge, ModelGauge m5 EZ (Maxim MAX17055 Rev 0)',
        footprint='Package_DFN_QFN:TDFN-10-1EP_2x2.5mm_P0.5mm', datasheet='MAX17055 Rev 0 (research/dl/ds/MAX17055.pdf)')

    # TPS61088 -- TI ZHCSDP8A pin functions (RHL VQFN-20, pin 21 = PGND thermal pad)
    S['TPS61088'] = box(d, 'TPS61088', [
        ('9', 'VIN', PI, 'L'), ('2', 'EN', I, 'L'), ('13', 'MODE', I, 'L'), ('10', 'SS', P, 'L'), ('19', 'ILIM', P, 'L'),
        ('18', 'COMP', P, 'L'), ('1', 'VCC', P, 'L'), ('11', 'NC', P, 'L'), ('12', 'NC', P, 'L'),
        ('4', 'SW', P, 'R'), ('5', 'SW', P, 'R'), ('6', 'SW', P, 'R'), ('7', 'SW', P, 'R'), ('8', 'BOOT', P, 'R'),
        ('3', 'FSW', P, 'R'), ('14', 'VOUT', PO, 'R'), ('15', 'VOUT', P, 'R'), ('16', 'VOUT', P, 'R'), ('17', 'FB', I, 'R'),
        ('20', 'AGND', PI, 'R'), ('21', 'PGND', P, 'R')],
        description='10 A synchronous boost, 4.5-12.6 V out (TI TPS61088)', footprint='cm5h:Texas_RHL0020A_VQFN-20-1EP_3.5x4.5mm_P0.5mm')

    # TPS61089 -- TI SLVSD38C Table 6-1 (RNR VQFN-HR 11)
    S['TPS61089'] = box(d, 'TPS61089', [
        ('9', 'VIN', PI, 'L'), ('7', 'EN', I, 'L'), ('8', 'ILIM', P, 'L'), ('4', 'COMP', P, 'L'), ('2', 'VCC', P, 'L'),
        ('5', 'GND', PI, 'L'),
        ('11', 'SW', P, 'R'), ('10', 'BOOT', P, 'R'), ('1', 'FSW', P, 'R'), ('6', 'VOUT', PO, 'R'), ('3', 'FB', I, 'R')],
        description='7 A synchronous boost (TI TPS61089)', footprint='cm5h:Texas_RNR0011A_VQFN-HR-11_2x2.5mm')

    # TPS63020 -- TI SLVS916I pin functions (DSJ VSON-14, pad 15 = PGND)
    S['TPS63020'] = box(d, 'TPS63020', [
        ('10', 'VIN', PI, 'L'), ('11', 'VIN', P, 'L'), ('1', 'VINA', P, 'L'), ('12', 'EN', I, 'L'), ('13', 'PS/SYNC', I, 'L'),
        ('2', 'GND', PI, 'L'), ('15', 'PGND(EP)', P, 'L'),
        ('8', 'L1', P, 'R'), ('9', 'L1', P, 'R'), ('6', 'L2', P, 'R'), ('7', 'L2', P, 'R'), ('4', 'VOUT', PO, 'R'),
        ('5', 'VOUT', P, 'R'), ('3', 'FB', I, 'R'), ('14', 'PG', OC, 'R')],
        description='4 A switch buck-boost (TI TPS63020)', footprint='Package_SON:Texas_DSJ0014A_VSON-14-1EP_3x4mm_P0.5mm')

    # TPS61169 -- TI SNVSA40B Table 4-1 (DCK SC70-5)
    S['TPS61169'] = box(d, 'TPS61169', [
        ('5', 'VIN', PI, 'L'), ('4', 'CTRL', I, 'L'), ('2', 'GND', PI, 'L'), ('1', 'SW', P, 'R'), ('3', 'FB', P, 'R')],
        description='38 V LED boost driver, PWM dimming (TI TPS61169)', footprint='Package_TO_SOT_SMD:SOT-353_SC-70-5')

    # TPS2553 -- TI SLVS841 pin functions (DBV SOT-23-6)
    S['TPS2553'] = box(d, 'TPS2553', [
        ('1', 'IN', PI, 'L'), ('3', 'EN', I, 'L'), ('2', 'GND', PI, 'L'), ('6', 'OUT', P, 'R'), ('4', '~{FAULT}', OC, 'R'),
        ('5', 'ILIM', P, 'R')],
        description='Adjustable current-limited power switch, active-high EN (TI TPS2553)', footprint='Package_TO_SOT_SMD:SOT-23-6')

    # TLV7042 -- TI ZHCSGV4H Pin Functions TLV7032/42 (DGK VSSOP-8)
    S['TLV7042'] = box(d, 'TLV7042', [
        ('3', 'INA+', I, 'L'), ('2', 'INA-', I, 'L'), ('5', 'INB+', I, 'L'), ('6', 'INB-', I, 'L'),
        ('8', 'VCC', PI, 'R'), ('1', 'OUTA', OC, 'R'), ('7', 'OUTB', OC, 'R'), ('4', 'VEE', PI, 'R')],
        description='Dual nanopower comparator, open-drain (TI TLV7042)', footprint='Package_SO:VSSOP-8_3x3mm_P0.65mm')

    # CSD17577Q3A -- TI pin drawing (S 1-3, G 4, D 5-8 + pad)
    S['NMOS_SON8'] = box(d, 'NMOS_SON8_CSD17577Q3A', [
        ('4', 'G', I, 'L'), ('1', 'S', P, 'B'), ('2', 'S', P, 'B'), ('3', 'S', P, 'B'),
        ('5', 'D', P, 'T'), ('6', 'D', P, 'T'), ('7', 'D', P, 'T'), ('8', 'D', P, 'T'), ('9', 'D(pad)', P, 'T')],
        ref='Q', description='30 V N-ch NexFET, SON 3.3x3.3 (TI CSD17577Q3A)', footprint='cm5h:TI_VSONP-8_3.3x3.3mm_CSD17577Q3A')
    # CSD25404Q3 -- TI SLPS570 top view (D 1-3, G 4, S 5-8 + pad)
    S['PMOS_SON8'] = box(d, 'PMOS_SON8_CSD25404Q3', [
        ('4', 'G', I, 'L'), ('1', 'D', P, 'B'), ('2', 'D', P, 'B'), ('3', 'D', P, 'B'),
        ('5', 'S', P, 'T'), ('6', 'S', P, 'T'), ('7', 'S', P, 'T'), ('8', 'S', P, 'T'), ('9', 'S(pad)', P, 'T')],
        ref='Q', description='-20 V P-ch NexFET, SON 3.3x3.3 (TI CSD25404Q3)', footprint='cm5h:TI_VSON-CLIP-8_3.3x3.3mm_CSD25404Q3')

    # AP6275P -- AMPAK AP6275P datasheet s.5.2 Pin Assignment (50 pads)
    gnd = ['1', '3', '4', '5', '6', '7', '8', '10', '11', '23', '27', '30', '32', '39']
    pins = [('36', 'VBAT', PI, 'L'), ('34', 'VDDIO', PI, 'L'), ('25', 'CBUCK_0P9', P, 'L'), ('26', 'CSR_VLX', P, 'L'),
            ('28', 'ASR_VLX', P, 'L'), ('29', 'ABUCK_1P12', P, 'L'), ('13', 'XTAL_XOP', I, 'L'), ('14', 'XTAL_XON', O, 'L'),
            ('31', 'LPO_IN', I, 'L'), ('15', 'WL_REG_ON', I, 'L'), ('38', 'BT_REG_ON', I, 'L'), ('16', 'WL_HOST_WAKE', O, 'L'),
            ('49', 'BT_WAKE', I, 'L'), ('50', 'BT_HOST_WAKE', O, 'L'), ('2', 'WL_ANT0', P, 'L'), ('9', 'WL_ANT1', P, 'L'),
            ('12', 'PCIE_PERST_L', I, 'R'), ('37', 'PCIE_CLKREQ_L', OC, 'R'), ('24', 'PCIE_PME_L', OC, 'R'),
            ('35', 'PCIE_RCLK_P', I, 'R'), ('33', 'PCIE_RCLK_N', I, 'R'), ('45', 'PCIE_RX_P', I, 'R'), ('44', 'PCIE_RX_N', I, 'R'),
            ('47', 'PCIE_TX_P', O, 'R'), ('46', 'PCIE_TX_N', O, 'R'), ('40', 'BT_UART_TXD', O, 'R'), ('41', 'BT_UART_RXD', I, 'R'),
            ('42', 'BT_UART_RTS_N', O, 'R'), ('43', 'BT_UART_CTS_N', I, 'R'), ('19', 'BT_PCM_OUT', O, 'R'),
            ('20', 'BT_PCM_IN', I, 'R'), ('21', 'BT_PCM_SYNC', B, 'R'), ('22', 'BT_PCM_CLK', I, 'R'),
            ('17', 'NC', NC, 'R'), ('18', 'NC', NC, 'R'), ('48', 'NC', NC, 'R')]
    pins += [(g, 'GND', PI if i == 0 else P, 'B') for i, g in enumerate(gnd)]
    S['AP6275P'] = box(d, 'AP6275P', pins, ref='U', description='Wi-Fi 6 2x2 (PCIe) + BT 5.0 (UART/PCM) module, AMPAK',
                       footprint='cm5h:AMPAK_AP6275P')

    # Molex Micro-Lock Plus 505578-0971 (right angle): 9 circuits + 2 nails (MP). Pin use = decision Q3.
    S['BATT_CONN'] = box(d, 'Molex_505578-0971', [
        ('1', 'BAT+', P, 'L'), ('2', 'BAT+', P, 'L'), ('3', 'BAT+', P, 'L'), ('4', 'BAT+', P, 'L'),
        ('5', 'BAT-', P, 'L'), ('6', 'BAT-', P, 'L'), ('7', 'BAT-', P, 'L'), ('8', 'BAT-', P, 'L'), ('9', 'NTC', P, 'L'),
        ('MP', 'MP', P, 'R')], ref='J', description='Molex Micro-Lock Plus 2.0 mm, 9 pos, right angle SMT',
        footprint='cm5h:Molex_Micro-Lock_Plus_505578-0971_1x09_P2.00mm_Horizontal')

    # GCT SIM8066-6-1-14-01-A nano-SIM push-push (contacts C1..C7 + card detect + shell)
    S['NANOSIM'] = box(d, 'NanoSIM_GCT_SIM8066', [
        ('C1', 'VCC', P, 'L'), ('C2', 'RST', P, 'L'), ('C3', 'CLK', P, 'L'), ('C7', 'I/O', P, 'L'), ('C6', 'VPP', P, 'L'),
        ('C5', 'GND', P, 'R'), ('CD', 'CD', P, 'R'), ('SH', 'SHIELD', P, 'R')], ref='J',
        description='Nano-SIM push-push with card detect (GCT SIM8066)', footprint='cm5h:GCT_SIM8066-6-1-14-01-A')

    # Alps SKRTLAE010 side-push switch: KiCad footprint pads 1, 2, MP
    S['SW_SIDE'] = box(d, 'SW_Push_MP', [('1', '1', P, 'L'), ('2', '2', P, 'R'), ('MP', 'MP', P, 'B')], ref='SW',
                       description='Push button with mounting pads')

    # HOAUC HYCW236-USBA04-289B mid-mount USB-A (drawing: 1 VBUS 2 D- 3 D+ 4 GND, 4 shell tabs)
    S['USBA_MID'] = box(d, 'USB_A_MidMount_HYCW236', [
        ('1', 'VBUS', P, 'L'), ('2', 'D-', P, 'L'), ('3', 'D+', P, 'L'), ('4', 'GND', P, 'L'), ('SH', 'SHIELD', P, 'R')],
        ref='J', description='USB 2.0 Type-A receptacle, mid-mount SMT for 1.2 mm PCB (HOAUC HYCW236-USBA04-289B)',
        footprint='cm5h:USB_A_HOAUC_HYCW236-USBA04-289B')
    # TPS25751D: copy of KiCad Interface_USB:TPS25751D (pins verified against TI SLVSH93A Table 5-1) with the
    # unused GPIOs typed passive - this design ties them to GND as Table 5-1 instructs.
    import copy, symlib
    from sexpr import Q, find_all
    base = symlib.load('Interface_USB:TPS25751D')
    node = copy.deepcopy(base.node)
    node[1] = Q('cm5h:TPS25751D')
    for sub in find_all(node, 'symbol'):
        sub[1] = Q(str(sub[1]).replace('TPS25751D', 'TPS25751D', 1))
        for pin in find_all(sub, 'pin'):
            name = str([x for x in pin if isinstance(x, list) and x[0] == 'name'][0][1])
            if name in ('GPIO0', 'GPIO1', 'GPIO2', 'GPIO3', 'GPIO6', 'GPIO7', 'GPIO11'):
                pin[1] = 'passive'
            if name == '~{I2Ct_IRQ}':
                pin[1] = 'open_collector'
    s = symlib.Symbol('cm5h:TPS25751D', node)
    d.symbols[s.lib_id] = s
    S['TPS25751D'] = s
    # MAX98357A: KiCad symbol's exposed pad is 'unspecified'; it is ground (datasheet), typed passive here
    S['MAX98357A'] = derived(d, 'Audio:MAX98357A', 'MAX98357A', {'PAD': 'passive'})
    return S


def fpc(d, name, n, description, footprint):
    """Generic N-pin FPC/FFC/board connector with one mounting-pad pin MP."""
    pins = [(str(i), str(i), P, 'L') for i in range(1, n + 1)] + [('MP', 'MP', P, 'R')]
    return box(d, name, pins, ref='J', description=description, footprint=footprint)


def cm5_connector(d, letter):
    """CM5 board-to-board connector (Hirose DF40C-100DS-0.4V(51) on the carrier). Pin names = Radxa CM5 v2.21
    pinout net names (gen/data/cm5_pins.json from radxa_cm5_v2210_pinout.xlsx). Connector A = U13-A
    (CM5 pins 1-100), B = U13-B (101-200, DF40 pad n = CM5 pin 100+n), C = J1."""
    pins = json.load(open(os.path.join(HERE, 'data', 'cm5_pins.json')))[letter]
    if not hasattr(d, '_cm5_seen_pwr'):
        d._cm5_seen_pwr = set()
    seen_pwr = d._cm5_seen_pwr
    left, right = [], []
    for k in range(1, 101):
        cm5pin = str(k + (100 if letter == 'B' else 0))
        info = pins[cm5pin]
        net = info['net'] or 'NC'
        gpio = info['gpio']
        name = net if (not gpio or gpio in net) else f'{net}/{gpio}'
        et = P
        if net == 'GND':
            et = PI if 'GND' not in seen_pwr else P
            seen_pwr.add('GND')
        elif net in ('VCC_3V3_S3', 'VCC_1V8_S0', 'VCCIO_FLASH'):
            et = PO if net not in seen_pwr else P
            seen_pwr.add(net)
        elif net == 'VCC_SYSIN':
            et = PI if net not in seen_pwr else P
            seen_pwr.add(net)
        entry = (str(k), f'{cm5pin}:{name}' if letter == 'B' else name, et)
        (left if k % 2 else right).append(entry)
    from symlib import make_box_symbol
    s = make_box_symbol(f'cm5h:CM5_DF40_{letter}', [{'left': left, 'right': right}], ref='J',
                        value=f'CM5 connector {letter}', description=f'Radxa CM5 B2B connector {letter} '
                        f'(carrier part Hirose DF40C-100DS-0.4V(51)); pin names from Radxa CM5 v2.21 pinout',
                        footprint=f'cm5h:Radxa_CM5_DF40_{letter}', min_width=60.96)
    d.symbols[s.lib_id] = s
    return s


def opi_connector(d, jp):
    """Orange Pi CM5 board-to-board connector JP1 / JP2 / JP3 (Hirose DF40C-100DS-0.4V(51) on the carrier). Pin
    names = Orange Pi CM5 'interface PIN definition' V1.1 (gen/data/opi_cm5_pins.json, tools/opi_pins.py): the
    pin's signal name, plus its GPIO where the name is a function, plus its IO voltage."""
    pins = json.load(open(os.path.join(HERE, 'data', 'opi_cm5_pins.json')))[jp]
    if not hasattr(d, '_cm5_seen_pwr'):
        d._cm5_seen_pwr = set()
    seen_pwr = d._cm5_seen_pwr
    left, right = [], []
    for k in range(1, 101):
        info = pins[str(k)]
        net = info['signal'] or 'NC'
        gpio = info['gpio']
        name = net if (not gpio or gpio in net) else f'{net}/{gpio}'
        dom = {'1.8V': '1V8', '3.3V': '3V3', 'GPIO_VREF': 'VREF', 'UNVERIFIED': 'IO ?'}.get(info['domain'])
        if dom:
            name += f' ({dom})'
        et = P
        if net == 'GND':
            et = PI if 'GND' not in seen_pwr else P
            seen_pwr.add('GND')
        elif net in ('VCC_3V3_S3', 'VCC_1V8_S3'):
            et = PO if net not in seen_pwr else P
            seen_pwr.add(net)
        elif net in ('VBUS', 'GPIO_VREF'):
            et = PI if net not in seen_pwr else P
            seen_pwr.add(net)
        (left if k % 2 else right).append((str(k), name, et))
    from symlib import make_box_symbol
    s = make_box_symbol(f'cm5h:OPI_CM5_{jp}', [{'left': left, 'right': right}], ref='J', value=f'CM5 {jp}',
                        description=f'Orange Pi CM5 B2B connector {jp} (carrier part Hirose DF40C-100DS-0.4V(51)); '
                        'pin names from the Orange Pi CM5 interface PIN definition V1.1',
                        footprint=f'cm5h:OPi_CM5_DF40_{jp}', min_width=60.96)
    d.symbols[s.lib_id] = s
    return s


def derived(d, lib_id, new_name, retype):
    """Copy of a KiCad library symbol into cm5h with some pin types changed (retype: pin name -> type)."""
    import copy, symlib
    from sexpr import Q, find_all
    base = symlib.load(lib_id)
    node = copy.deepcopy(base.node)
    node[1] = Q('cm5h:' + new_name)
    old = lib_id.split(':', 1)[1]
    for sub in find_all(node, 'symbol'):
        sub[1] = Q(str(sub[1]).replace(old, new_name, 1))
        for pin in find_all(sub, 'pin'):
            name = str([x for x in pin if isinstance(x, list) and x[0] == 'name'][0][1])
            if name in retype:
                pin[1] = retype[name]
    s = symlib.Symbol('cm5h:' + new_name, node)
    d.symbols[s.lib_id] = s
    return s
