#!/usr/bin/env python3
"""Generate checkpoint-1 block diagram and power tree as SVG (no external deps). python3 -I tools/make_diagrams.py"""
import os
from xml.sax.saxutils import escape as E
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'opi')   # checkpoint 1 kept its own
CSS = """
<style>
 .t{font:13px sans-serif;fill:#1b1b1b}.s{font:11px sans-serif;fill:#444}.h{font:bold 14px sans-serif;fill:#1b1b1b}
 .ti{font:bold 18px sans-serif;fill:#1b1b1b}.l{font:11px sans-serif;fill:#1d4e89}
 .bx{stroke:#333;stroke-width:1.2;rx:6}.ln{stroke:#555;stroke-width:1.4;fill:none}
 .hs{stroke:#b5172d;stroke-width:2.2;fill:none}.pw{stroke:#c26a00;stroke-width:2.4;fill:none}
</style>
<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#555"/></marker>
<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#b5172d"/></marker>
<marker id="ap" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#c26a00"/></marker></defs>
"""
FILL = {'soc': '#dfe9f7', 'conn': '#f4f4f4', 'ic': '#e7f4e4', 'pwr': '#fdebd3', 'off': '#f6e3ef', 'kb': '#efe7fb'}
class S:
    def __init__(s, w, h, title):
        s.w, s.h = w, h; s.o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">', CSS,
                                f'<rect width="{w}" height="{h}" fill="#ffffff"/>', f'<text class="ti" x="16" y="28">{E(title)}</text>']
    def box(s, x, y, w, h, title, lines=(), kind='ic'):
        s.o.append(f'<rect class="bx" x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{FILL[kind]}"/>')
        s.o.append(f'<text class="h" x="{x+8}" y="{y+18}">{E(title)}</text>')
        for i, l in enumerate(lines): s.o.append(f'<text class="s" x="{x+8}" y="{y+34+i*14}">{E(l)}</text>')
    def line(s, pts, label=None, cls='ln', lpos=None, arrow=True, both=False):
        d = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        mk = {'ln': 'a', 'hs': 'ar', 'pw': 'ap'}[cls]
        m = f' marker-end="url(#{mk})"' if arrow else ''
        if both: m += f' marker-start="url(#{mk})"'
        s.o.append(f'<path class="{cls}" d="{d}"{m}/>')
        if label:
            lx, ly = lpos if lpos else ((pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2 - 5)
            s.o.append(f'<text class="l" x="{lx}" y="{ly}">{E(label)}</text>')
    def text(s, x, y, t, cls='s'): s.o.append(f'<text class="{cls}" x="{x}" y="{y}">{E(t)}</text>')
    def save(s, name):
        s.o.append('</svg>'); open(os.path.join(OUT, name), 'w').write('\n'.join(s.o)); print('wrote', name)

def block():
    s = S(1500, 1010, 'CM5 handheld: block diagram (Orange Pi CM5 redesign). Red = high-speed, grey = control/low-speed')
    # CM5 centre
    s.box(560, 330, 330, 330, 'Orange Pi CM5 (RK3588S)', ['3 x Hirose DF40 100-pin JP1-JP3 (1.5 mm stack)', 'VBUS 4.75-5.25 V (fed 5.03 V), 1.8 A max', 'outputs: VCC_3V3_S3 600 mA,', '         VCC_1V8_S3 600 mA', 'no on-module Wi-Fi/BT', 'eMMC + LPDDR4X on module', 'GPIO0/3 1.8 V, GPIO4 3.3 V, GPIO1 = VREF 3.3 V', 'USB: OTG0, HOST0, HOST1 (USB 2.0) + USB3 (PHY2)', 'PCIe 2.0 x1 (PHY0), DSI1 4-lane', 'CSI 4-lane + 2-lane, SDMMC, I2S0, PDM0', 'UART2/9, I2C2/3/4/6'], 'soc')
    # left: USB
    s.box(40, 70, 220, 80, 'USB-C receptacle (16-pin)', ['charging + USB 2.0 data', 'left short edge'], 'conn')
    s.box(40, 180, 220, 90, 'TPS25751 PD sink', ['dead-battery boot from EEPROM', 'controls BQ25713 over I2C', 'IRQ -> GPIO3_B3 (1.8 V)'], 'pwr')
    s.box(300, 180, 200, 70, 'BQ25713 charger', ['NVDC, ext. BATFET >= 12 A', 'PROCHOT# -> GPIO3_C1'], 'pwr')
    s.line([(260, 110), (530, 110), (530, 345), (560, 345)], 'OTG0 D+/D- (Maskrom, gadget)', 'hs', (300, 104))
    s.box(40, 300, 220, 110, 'USB2514B hub', ['upstream = HOST0', 'P1/P2 -> USB-A 1/2', 'P3 -> keyboard FFC', 'P4 -> digitizer FPC (reserved)'], 'ic')
    s.line([(560, 400), (260, 350)], 'HOST0', 'hs', (390, 360))
    s.box(40, 440, 220, 70, '2 x USB-A 2.0 (mid-mount)', ['bottom long edge', 'TPS2553 0.6 A limit each'], 'conn')
    s.line([(150, 410), (150, 440)], None, 'hs')
    s.box(40, 540, 220, 90, 'Keyboard FFC (12-pin 0.5 mm)', ['USB D+/D-, 5 V, I2C, INT#,', 'RESET#, BOOT#', '-> Board B (RP2040 + Q20)'], 'kb')
    s.line([(260, 395), (280, 395), (280, 585), (260, 585)], None, 'hs')
    # LTE
    s.box(40, 680, 250, 120, 'M.2 Key-B 3042 socket', ['Quectel EM060K-GL (Cat-6, global)', 'USB 2.0 (HOST1) + USB 3.0 (PHY2)', 'FULL_CARD_POWER_OFF#, RESET#,', 'W_DISABLE1#, WAKE_ON_WAN#', 'antennas on module (MHF4)'], 'ic')
    s.line([(560, 600), (290, 720)], 'HOST1 USB2 + USB3 SS', 'hs', (330, 650))
    s.box(40, 830, 250, 70, 'nano-SIM push-push', ['ESD + series R; SIM_DETECT -> M.2 pin 66', 'right short edge'], 'conn')
    s.line([(165, 800), (165, 830)], None, both=True)
    # Wi-Fi
    s.box(330, 830, 260, 110, 'AMPAK AP6275P', ['Wi-Fi 6 2x2 over PCIe (combo PHY0)', 'BT 5.0 over UART9 (RTS/CTS), 1.8 V', '37.4 MHz XTAL, 32.768 kHz LPO from RTC', '2 x u.FL (50 ohm)'], 'ic')
    s.line([(640, 660), (500, 830)], 'PCIe 2.0 x1', 'hs', (585, 760))
    s.line([(690, 660), (560, 830)], None)
    s.text(612, 800, 'UART9 + REG_ON/WAKE (GPIO0)', 'l')
    s.box(620, 880, 210, 60, 'BM8563 RTC', ['always-on; CLKOUT 32 kHz -> LPO', '+ SoC CLK32K_IN'], 'ic')
    s.line([(620, 920), (590, 920)], None)
    s.line([(830, 910), (1000, 905)], 'I2C4, INT', 'ln', (850, 900))
    # right side: display, cameras
    s.box(1000, 70, 290, 110, 'Display FPC 30-pin (top face)', ['DMKDI0400S0CA 4.0" 720x720, ST7703', '4-lane DSI1, RESET 1.8 V', 'backlight LEDA/K <- TPS61169', 'pinout from panel DS s.4.1'], 'conn')
    s.line([(890, 360), (1000, 140)], 'DSI1 4 lanes', 'hs', (900, 230))
    s.box(1000, 200, 290, 70, 'Touch FPC 8-pin (top face)', ['GT911, I2C6 3.3 V, INT/RST GPIO1_B2/B3', 'active stylus; EMR digitizer FPC reserved'], 'conn')
    s.line([(890, 390), (1000, 245)], None)
    s.box(1000, 300, 290, 90, 'CAM-A FPC FH35C-31S (top face)', ['Radxa 31-pin camera pinout', '4-lane CSI (MIPI_CSI0 D-PHY)', 'MCLK, PDN, RST, I2C3 (1.8 V)'], 'conn')
    s.line([(890, 420), (1000, 345)], 'CSI 4-lane', 'hs', (930, 372))
    s.box(1000, 410, 290, 90, 'CAM-B FPC 15-pin 1.0 mm (top)', ['Radxa Camera 8M 219 / RPi v2', '2-lane CSI (DC-PHY0)', 'I2C2 (3.3 V), CAM_IO0/1'], 'conn')
    s.line([(890, 470), (1000, 455)], 'CSI 2-lane', 'hs', (905, 455))
    s.box(1000, 520, 290, 90, 'Audio', ['2 x MAX98357A on I2S0 (L / R)', '2 x 2-pin speaker connectors', 'PDM MEMS mic on PDM0'], 'ic')
    s.line([(890, 560), (1000, 565)], 'I2S0 / PDM0', 'ln', (905, 557))
    s.box(1000, 630, 290, 70, 'microSD push-push', ['SDMMC 4-bit, CD -> GPIO0_A4', 'right short edge'], 'conn')
    s.line([(890, 610), (1000, 665)], 'SDMMC', 'ln', (920, 640))
    s.box(1000, 720, 290, 110, 'Buttons, debug, status', ['Power (PWRON_L), Reset (RESET_L)', 'Maskrom (SARADC_IN0)', 'Recovery/Vol+/Vol- (SARADC_IN1 ladder)', 'UART2 debug (3.3 V pads via TXS0104E), LED'], 'ic')
    s.line([(890, 640), (1000, 770)], None)
    s.box(1000, 850, 290, 80, 'System I2C4 (3.3 V)', ['TPS25751 (0x20-23), MAX17055', 'BM8563 RTC (0x51)'], 'ic')
    s.line([(860, 660), (1000, 890)], None)
    s.box(560, 90, 330, 160, 'Power (see power_tree.svg)', ['Battery 1S 5000 mAh (beside board)', 'BQ25713 NVDC -> VSYS 3.0-4.5 V', 'TPS61088 -> 5.03 V CM5', 'TPS61089 -> 5.1 V USB-A/keyboard/cam', '2 x TPS63020 -> 3.7 V LTE, 3.3 V AUX', 'TPS61169 -> backlight', 'MAX17055 fuel gauge (current sense)'], 'pwr')
    s.line([(500, 215), (560, 190)], None, 'pw')
    s.line([(150, 150), (150, 180)], 'VBUS', 'pw', (156, 170))
    s.line([(260, 215), (300, 215)], None, 'pw')
    s.line([(725, 250), (725, 330)], 'CM5_VIN 5.03 V', 'pw', (732, 300))
    s.save('block_diagram.svg')

def power():
    s = S(1500, 900, 'CM5 handheld: power tree (Orange Pi CM5 redesign). Numbers: worst-case load at the rail')
    s.box(30, 80, 220, 90, 'USB-C VBUS 5-20 V', ['PD sink, max 7 A path', 'TPS25751 negotiates 5/9/12 V'], 'conn')
    s.box(30, 210, 220, 110, 'TPS25751D', ['VIN_3V3 <- always-on LDO', 'boots from >= 36 KB EEPROM (0x50)', 'I2C controller -> BQ25713 + EEPROM', 'I2C target -> SoC I2C3'], 'pwr')
    s.line([(140, 170), (140, 210)], None, 'pw')
    s.box(300, 160, 250, 140, 'BQ25713 (1S NVDC controller)', ['VBUS 3.5-24 V in, 4 ext. N-FETs', 'ICHG 2.5 A, VREG 4.2 V (PD config)', 'VSYSMIN 3.584 V (1S default)', 'ext. P-ch BATFET sized >= 12 A', 'no TS pin: NTC window comp -> HIZ'], 'pwr')
    s.line([(250, 265), (300, 230)], 'PPHV', 'pw', (255, 240))
    s.box(300, 360, 250, 110, 'Battery 1S Li-ion 5000 mAh', ['PCM >= 12 A (decision Q4)', '9-pin: 4 x BAT+, 4 x GND, NTC (12 A)', 'MAX17055 + sense resistor'], 'conn')
    s.line([(425, 360), (425, 300)], 'BAT', 'pw', (432, 335), both=True)
    s.box(620, 400, 200, 60, 'VSYS 3.0-4.5 V', ['NVDC; >= 3.584 V on adapter'], 'pwr')
    s.line([(550, 230), (720, 230), (720, 400)], None, 'pw')
    rails = [
        (900, 60, 'TPS61088 boost', ['5.03 V CM5_VIN', 'CM5: 9 W max (1.8 A)', 'EN: always (module PMIC does on/off)'], 'CM5 VBUS x6 pins'),
        (900, 175, 'TPS61089 boost', ['5.1 V VCC5V0', 'USB-A 2 x 0.5 A, keyboard, CAM-A 5 V', 'EN: VCC_3V3_S3 (on with CM5)'], 'TPS2553 x2 -> USB-A; switch -> KBD FFC'),
        (900, 290, 'TPS63020 buck-boost', ['3.7 V VCC_LTE', 'EM060K-GL: 1.07 A max listed', '2 x 220 uF low-ESR + MLCC array', 'EN: GPIO0_C4 (1.8 V)'], 'M.2 Key-B VCC pins 2,4,70,72,74'),
        (900, 420, 'TPS63020 buck-boost', ['3.3 V VCC3V3_AUX', 'AP6275P VBAT 1.2 A peak, hub, CAM-B', 'EN: VCC_3V3_S3'], 'AP6275P, USB2514B, cameras'),
        (900, 535, 'TPS61169 LED boost', ['18.6 V / 40 mA backlight', 'CTRL <- PWM13_M1'], 'panel LEDA/LEDK'),
        (900, 635, '2 x MAX98357A', ['from VSYS directly', '~0.8 W/ch into 8 ohm'], 'speakers'),
        (900, 735, 'Always-on LDO 3.3 V (XC6206)', ['TPS25751 VIN_3V3, BM8563 RTC', 'Iq ~1 uA'], ''),
    ]
    for x, y, t, l, dest in rails:
        h = 30 + 14 * len(l)
        s.box(x, y, 300, h, t, l, 'pwr')
        s.line([(820, 430), (860, 430), (860, y + 22), (x, y + 22)], None, 'pw')
        if dest: s.text(x + 310, y + 26, '-> ' + dest, 'l')
    s.box(300, 540, 250, 165, 'CM5 on-module outputs', ['VCC_3V3_S3 (600 mA max):', '  microSD VDD, panel VCI (load sw), GPIO_VREF,', '  GT911, PDM mic, pull-ups, shifter B-side', 'VCC_1V8_S3 (600 mA max):', '  panel IOVCC, AP6275P VDDIO,', '  1.8 V pull-ups, shifter A-side', '(fed from CM5_VIN by the module PMIC)'], 'soc')
    s.text(30, 760, 'Budget at the battery (all loads at max at once): 33.6 W from VSYS = 9.3 A @ 3.7 V, 9.8 A @ 3.5 V.', 'h')
    s.text(30, 784, 'Battery path (connector 12 A, PCM >= 12 A, external BATFET, sense resistors) is sized for the full worst case; PROCHOT# warns Linux.', 't')
    s.text(30, 806, 'Realistic heavy use 13.9 W (3.8 A @ 3.7 V); light use 5.1 W (1.4 A).', 't')
    s.save('power_tree.svg')

if __name__ == '__main__':
    block(); power()
