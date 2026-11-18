#!/usr/bin/env python3
"""Orange Pi CM5 pin map of Board A: every connector pin with its Orange Pi signal, GPIO, IO voltage, the function the
carrier uses, the carrier net and what it connects to. Reads gen/data/opi_cm5_pins.json, gen/board_a_main.CM5_NETS and
hw/board_a/cm5_carrier.net; writes docs/opi/opi_cm5_pin_map.csv.

usage: opi_pinmap.py
"""
import csv
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'gen'))
import board_a_main  # noqa: E402
from sexpr import parse, find, find_all  # noqa: E402

# the pin function each used pin needs, read off the PIN definition V1.1 pages (pin-name column); plain GPIOs and
# fixed-function pins (USB, PCIe, MIPI, SDMMC, power, ADC) are not listed
FUNC = {
    ('JP1', 28): 'I2C4_SDA_M3', ('JP1', 30): 'I2C4_SCL_M3', ('JP1', 48): 'PDM0_CLK0_M0', ('JP1', 49): 'PDM0_SDI0_M0',
    ('JP1', 51): 'UART2_RX_M0', ('JP1', 55): 'UART2_TX_M0', ('JP1', 80): 'I2C6_SCL_M3', ('JP1', 82): 'I2C6_SDA_M3',
    ('JP1', 95): 'PWM13_M1', ('JP1', 76): 'SDMMC_DET',
    ('JP2', 2): 'GPIO (software I2C SDA; I2C2 is the module\'s, D104)',
    ('JP2', 4): 'GPIO (software I2C SCL; I2C2 is the module\'s, D104)', ('JP2', 16): 'USB30_2 SSRXP (combo PHY2, USB3 mode)',
    ('JP2', 18): 'USB30_2 SSRXN (combo PHY2, USB3 mode)', ('JP2', 22): 'USB30_2 SSTXP (combo PHY2, USB3 mode)',
    ('JP2', 24): 'USB30_2 SSTXN (combo PHY2, USB3 mode)',
    ('JP3', 22): 'PCIE20X1_2_CLKREQN_M0', ('JP3', 24): 'PCIE20X1_2_PERSTN_M0', ('JP3', 43): 'PCIE20X1_2_WAKEN_M0',
    ('JP3', 26): 'UART9_TX_M2', ('JP3', 28): 'UART9_RTSN_M2', ('JP3', 30): 'UART9_RX_M2', ('JP3', 40): 'UART9_CTSN_M2',
    ('JP3', 34): 'I2C3_SCL_M1', ('JP3', 72): 'I2C3_SDA_M1', ('JP3', 52): 'MIPI_CAMERA1_CLK_M1',
    ('JP3', 60): 'MIPI_CAMERA2_CLK_M1', ('JP3', 69): 'I2S0_LRCK', ('JP3', 70): 'I2S0_SDO0', ('JP3', 71): 'I2S0_SCLK',
    ('JP3', 96): 'CLK32K_IN',
}
JP = {'A': 'JP1', 'B': 'JP2', 'C': 'JP3'}
REF = {'JP1': 'J301', 'JP2': 'J302', 'JP3': 'J303'}


def main():
    root = parse(open(os.path.join(ROOT, 'hw', 'board_a', 'cm5_carrier.net')).read())[0]
    nodes = {}
    for n in find_all(find(root, 'nets'), 'net'):
        name = str(find(n, 'name')[1]).split('/')[-1]
        nodes[name] = sorted(f'{find(x, "ref")[1]}.{find(x, "pin")[1]}' for x in find_all(n, 'node'))
    out = os.path.join(ROOT, 'docs', 'opi', 'opi_cm5_pin_map.csv')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['connector', 'pin', 'opi_signal', 'gpio', 'io_voltage', 'function_used', 'carrier_net',
                    'connected_to'])
        for letter, jp in JP.items():
            for k in range(1, 101):
                e = board_a_main.OPI[jp][str(k)]
                net = 'GND' if e['signal'] == 'GND' else board_a_main.CM5_NETS[letter].get(k) or 'NC'
                vol = {'GPIO_VREF': '3.3V (GPIO_VREF)', 'UNVERIFIED': 'UNVERIFIED'}.get(e['domain'], e['domain'] or '')
                other = [x for x in nodes.get(net, []) if not x.startswith(REF[jp] + '.')] if net not in ('NC', 'GND') else []
                w.writerow([jp, k, e['signal'], e['gpio'] or '', vol, FUNC.get((jp, k), ''), net,
                            ', '.join(other[:12]) + (' ...' if len(other) > 12 else '')])
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
