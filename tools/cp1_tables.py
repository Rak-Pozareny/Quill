#!/usr/bin/env python3
"""Checkpoint-1 data: CM5 pin budget, power budget, parts shortlist.
Writes CSV + Markdown tables into docs/checkpoint1/. Re-run after edits: python3 -I tools/cp1_tables.py"""
import csv, os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'checkpoint1')

# Source tags (full list in docs/checkpoint1/CHECKPOINT1.md, section "Sources")
#  PX   = radxa_cm5_v2210_pinout.xlsx (sheet U13-A / U13-B / J1), row = pin
#  CM5  = radxa_cm5_v2210_schematic.pdf page n   IO = radxa_cm5_io_v2200_schematic.pdf page n
#  DOC  = docs.radxa.com CM5 README / hw-interface / faq (radxa-docs repo, i18n/en/.../som/cm/cm5)

# Domains (CM5 schematic): PMUIO1=1.8V(S3) GPIO0_A0..B3 [CM5 p9]; PMUIO2=3.3V(VCC_3V3_S3) GPIO0_B5..D6 [CM5 p9];
# VCCIO1=1.8V only, S0 rail, GPIO1_C0..D5 [CM5 p13]; VCCIO4=1.8V (VCC_1V8_S3) GPIO1_A0..B7,D6,D7 [CM5 p17];
# VCCIO5=3.3V (VCC_3V3_S0=VCC_3V3_S3 via R95036 0R) GPIO3_B..D5 [CM5 p17, p6]; VCCIO6=GPIO_VREF=VCC_3V3_S3 (R95031 0R) GPIO4_A0..C1 [CM5 p4, p17]

P = []  # (conn, pin(s), radxa net, soc/gpio, domain, use, connects_to, notes, source)
def add(*row): P.append(row)

# ---------------- Power / ground ----------------
add('A', '77,79,81,83,85,87', 'VCC_SYSIN', '-', 'input 3.6-5.2 V', 'Module supply', 'CM5_VIN = 4.8 V boost (TPS61088)', 'Radxa recommends 4 V/3 A; 4.8 V used because a boost from VSYS (max 4.55 V) must output above VSYS. 6 pins x 0.3 A DF40 contact rating (same as Radxa IO board).', 'PX U13-A; DOC README; IO p15')
add('A', '84,86', 'VCC_3V3_S3', '-', 'output, 600 mA max', '3.3 V for low-power carrier loads', 'microSD VDD, panel VCI (via load switch), GT911 VDD, I2C pull-ups, level-shifter B side, regulator ENs', 'Budget <= 300 mA of 600 mA', 'PX U13-A; CM5 p4')
add('C', '92', 'VCC_3V3_S3', '-', 'output', 'same rail', 'same as above', '', 'PX J1; CM5 p4 (R9241 0R)')
add('A', '88,90', 'VCC_1V8_S0', '-', 'output, 600 mA max', '1.8 V for carrier loads', 'panel IOVCC, AP6275P VDDIO, level-shifter A side, CAM-A I2C pull-ups, PDM mic VDD', 'Budget <= 100 mA', 'PX U13-A; CM5 p4')
add('A', '73', 'VCCIO_FLASH', '= VCC_1V8_S3', 'output (1.8 V, S3)', 'pull-up rail', 'SDMMC_DET_L 100k pull-up', 'Module ties VCCIO_FLASH to VCC_1V8_S3 (R4000 0R); IO board pulls SD-detect to VCC_1V8_S3', 'CM5 p4; IO p6')
add('A/B/C', 'all GND pins', 'GND', '-', '-', 'Ground', 'GND planes L2/L5', '', 'PX')

# ---------------- Power control / buttons / debug ----------------
add('A', '99', 'PWRON_L', 'RK806 PWRON', 'PMIC input (internal pull-up)', 'Power button', 'Tactile switch to GND, 100R + ESD (as IO board)', 'RK806 handles press/long-press', 'PX; CM5 p18; IO p19')
add('A', '92', 'RESET_L', 'NPOR/RK806 RESETB', 'PMIC', 'Reset button', 'Tactile switch to GND, 100R + ESD', '', 'PX; IO p19')
add('A', '93', 'SARADC_VIN0_BOOT', 'SARADC_IN0', '1.8 V ADC', 'Maskrom button', 'Tactile switch to GND, 100R + ESD', 'Module also has its own maskrom button (SW9201)', 'PX; CM5 p13; IO p19')
add('C', '26', 'SARADC_VIN1_KEY/RECOVERY', 'SARADC_IN1', '1.8 V ADC (10k pull-up on module)', 'Recovery + Vol+/Vol- (ADC ladder)', 'Recovery = short to GND; Vol+/Vol- through resistors (values at checkpoint 2)', 'adc-keys in device tree', 'PX; CM5 p13; IO p19')
add('C', '28', 'SARADC_VIN2_DC', 'SARADC_IN2', '1.8 V ADC', 'VSYS monitor', 'VSYS / 3 divider (4.55 V max -> 1.52 V)', 'optional, debug aid', 'PX; CM5 p13; IO p15')
add('A', '51', 'UART2_RX_M0', 'GPIO0_B6', 'PMUIO2 3.3 V', 'Debug console RX', '3-pin debug pads/header', '1.5 Mbaud Rockchip default', 'PX; CM5 p9')
add('A', '55', 'UART2_TX_M0', 'GPIO0_B5', 'PMUIO2 3.3 V', 'Debug console TX', '3-pin debug pads/header', '', 'PX; CM5 p9')
add('A', '95', 'WIFI_LED', 'GPIO3_C5', 'VCCIO5 3.3 V', 'Status LED', 'LED + resistor', '', 'PX; CM5 p17')

# ---------------- System I2C (PD, fuel gauge, RTC) ----------------
add('C', '4', 'GPIO3_C0', 'I2C3_SDA_M1', 'VCCIO5 3.3 V', 'SYS_I2C SDA', 'TPS25751 I2Ct, MAX17055, HT8563 RTC', '2.2k pull-up to VCC_3V3_S3', 'PX J1; CM5 p17')
add('C', '6', 'GPIO3_B7', 'I2C3_SCL_M1', 'VCCIO5 3.3 V', 'SYS_I2C SCL', 'same', '', 'PX J1; CM5 p17')
add('C', '96', 'CC_INT0_L', 'GPIO0_C4', 'PMUIO2 3.3 V', 'PD controller IRQ (wake)', 'TPS25751 I2Ct_IRQ (open drain)', 'PMU GPIO = can wake from suspend', 'PX J1; CM5 p9')
add('A', '89', 'PWM4_M0', 'GPIO0_C5', 'PMUIO2 3.3 V', 'RTC alarm IRQ (wake)', 'HT8563 INT# (open drain, 10k pull-up)', '', 'PX; CM5 p9')
add('C', '94', 'GPIO0_D3', 'GPIO0_D3', 'PMUIO2 3.3 V', 'Fuel-gauge alert (wake)', 'MAX17055 ALRT# (open drain)', '10k pull-up to VCC_3V3_S3', 'PX J1; CM5 p9')

# ---------------- USB ----------------
add('B', '103,105', 'TYPEC0_OTG_DM/DP', 'USB20 OTG0', 'USB PHY', 'USB-C data (device default, Maskrom)', 'USB-C receptacle D-/D+ via 2.2R + CMC + ESD', 'OTG0 is the Maskrom/download port', 'PX U13-B; CM5 p12; IO p18')
add('C', '97', 'TYPEC0_OTG_VBUSDET', 'TYPEC0_USB20_VBUSDET', '3.3 V (4.7k pull-up on module)', 'left at module default', '- (option: NMOS pull-down when VBUS absent)', 'Same as Radxa IO board (pin NC)', 'PX J1; CM5 p12; IO p17')
add('C', '63,65', 'USB20_HOST0_DP/DM', 'USB2 HOST0', 'USB PHY', 'USB hub upstream', 'USB2514B upstream port', 'Same port Radxa uses for its FE1.1s hub', 'PX J1; IO p12')
add('C', '45,47', 'USB20_HOST1_DP/DM', 'USB2 HOST1', 'USB PHY', 'LTE modem USB 2.0 (direct)', 'M.2 Key-B pins 7/9 (USB_DP/USB_DM)', 'USB 2.0 half of the modem USB 3.0 link (same pairing as Radxa IO-board USB 3.0 port)', 'PX J1; IO p13; EM060K HD V1.1 s.4.1')
add('C', '51,53', 'USB30_2_SSTXP/N', 'USB3 SS TX (combo PHY2)', 'USB3 PHY', 'LTE modem USB 3.0 TX', 'M.2 pins 37/35 (USB_SS_RX_P/M) via 100 nF', 'decision Q7; host-side AC caps per Quectel Fig. 18', 'PX J1; EM060K HD V1.1 Fig. 18')
add('C', '57,59', 'USB30_2_SSRXP/N', 'USB3 SS RX (combo PHY2)', 'USB3 PHY', 'LTE modem USB 3.0 RX', 'M.2 pins 31/29 (USB_SS_TX_P/M), no caps (inside module)', 'combo PHY2 set to USB3 mode in device tree', 'PX J1; EM060K HD V1.1 Fig. 18')
add('C', '89', 'GPIO4_A6', 'GPIO4_A6', 'VCCIO6 3.3 V', 'Hub reset', 'USB2514B RESET_N (+ RC)', '', 'PX J1; CM5 p17')

# ---------------- LTE (M.2 Key-B) ----------------
add('A', '56', 'GPIO0_C7', 'GPIO0_C7', 'PMUIO2 3.3 V', 'LTE rail enable', 'TPS63020 (3.7 V) EN', 'PMU GPIO keeps state in suspend', 'PX; CM5 p9')
add('A', '58', 'GPIO0_D0', 'GPIO0_D0', 'PMUIO2 3.3 V', 'FULL_CARD_POWER_OFF#', 'M.2 pin 6 (series 1k)', 'EM060K: 3.3 V tolerant, >= 1.19 V = on, 100k internal pull-down', 'PX; EM060K HD V1.1 s.3.6')
add('C', '8', 'TYPEC0_SBU1_DC', 'GPIO3_C4', 'VCCIO5 3.3 V', 'LTE RESET#', 'M.2 pin 67 via NMOS (open drain)', 'EM060K: VIH min 1.3 V, internal pull-up; Quectel ref = open-collector', 'PX J1; EM060K HD V1.1 s.3.8')
add('C', '14', 'TYPEC0_SBU2_DC', 'GPIO3_D4', 'VCCIO5 3.3 V', 'LTE W_DISABLE1#', 'M.2 pin 8 via NMOS (open drain)', 'internal pull-up; VIL max 0.4 V', 'PX J1; EM060K HD V1.1 s.4.4.1')
add('A', '91', 'HOST_WAKE_BT_H', 'GPIO0_C6', 'PMUIO2 3.3 V', 'LTE WAKE_ON_WAN# (wake)', 'M.2 pin 23 (open drain, 10k pull-up to 3V3_S3)', 'Module pin is OD, 1.8/3.3 V', 'PX; EM060K HD V1.1 pin table')

# ---------------- Wi-Fi / BT (AP6275P) ----------------
add('B', '110,112', 'PCIE20_0_REFCLKP/N', 'PCIe2 lane 0 (combo PHY0)', 'PCIe', 'Wi-Fi PCIe refclk', 'AP6275P PCIE_RCLK_P/N (35/33)', 'Same lane Radxa routes to its M.2 E-key Wi-Fi', 'PX U13-B; IO p7')
add('B', '122,124', 'PCIE20_0_TXP/N', 'PCIe2 lane 0', 'PCIe', 'Wi-Fi PCIe TX', 'AP6275P PCIE_RX_P/N (45/44) via 100 nF', '', 'PX U13-B; IO p7')
add('B', '116,118', 'PCIE20_0_RXP/N', 'PCIe2 lane 0', 'PCIe', 'Wi-Fi PCIe RX', 'AP6275P PCIE_TX_P/N (47/46) (AC caps: check AP6275P ref)', 'UNVERIFIED: whether AP6275P has internal TX caps', 'PX U13-B; AP6275P DS p15-16')
add('B', '109', 'PCIE20X1_2_PERSTN_M0', 'GPIO3_D1', 'VCCIO5 3.3 V', 'PCIe PERST#', 'AP6275P PCIE_PREST_L (12) via 3.3->1.8 V translator', 'AP6275P VDDIO is 1.8 V only (abs max 2.07 V)', 'PX U13-B; AP6275P DS')
add('B', '102', 'PCIE20X1_2_CLKREQN_M0', 'GPIO3_C7', 'VCCIO5 3.3 V', 'PCIe CLKREQ#', 'AP6275P PCIE_CLKREQ_L (37, OD) via translator', '', 'PX U13-B; AP6275P DS')
add('A', '24', 'PCIE20X1_2_WAKEN_M0', 'GPIO3_D0', 'VCCIO5 3.3 V', 'PCIe WAKE#', 'AP6275P PCIE_PME_L (24, OD) via translator', '', 'PX U13-A; AP6275P DS')
add('A', '20', 'HP_INT', 'GPIO0_A0', 'PMUIO1 1.8 V', 'WL_HOST_WAKE (wake)', 'AP6275P WL_HOST_WAKE (16)', '1.8 V PMU GPIO, no translator', 'PX; CM5 p9; AP6275P DS')
add('A', '29', 'GSENSOR_INT', 'GPIO1_A4', 'VCCIO4 1.8 V (S3)', 'WL_REG_ON', 'AP6275P WL_REG_ON (15)', 'S3 domain so Wi-Fi can stay up in suspend', 'PX; CM5 p17; AP6275P DS')
add('A', '40', 'GPIO1_B1', 'GPIO1_B1', 'VCCIO4 1.8 V (S3)', 'BT_REG_ON', 'AP6275P BT_REG_ON (38)', '', 'PX; CM5 p17')
add('A', '39', 'TP_RST_L', 'GPIO1_B4', 'VCCIO4 1.8 V (S3)', 'BT_WAKE (host->BT)', 'AP6275P BT_WAKE (49)', 'Radxa net name is TP_RST_L; touch uses 3.3 V pins instead', 'PX; CM5 p17')
add('C', '81', 'RTC_INT_L', 'GPIO0_B0', 'PMUIO1 1.8 V', 'BT_HOST_WAKE (wake)', 'AP6275P BT_HOST_WAKE (50)', 'repurposed; RTC IRQ goes to GPIO0_C5', 'PX J1; CM5 p9')
add('A', '97', 'USB_HOST_PWREN_H', 'GPIO1_A0 / UART6_RX_M1', 'VCCIO4 1.8 V', 'BT UART RX', 'AP6275P BT_UART_TXD (40)', 'UART6_M1 4-wire with RTS/CTS', 'PX U13-A func list; CM5 p17')
add('A', '27', 'WIFI_REG_ON_E', 'GPIO1_A1 / UART6_TX_M1', 'VCCIO4 1.8 V', 'BT UART TX', 'AP6275P BT_UART_RXD (41)', '', 'PX U13-A')
add('A', '25', 'I2C4_SDA_M3_WIFI', 'GPIO1_A2 / UART6_RTSN_M1', 'VCCIO4 1.8 V', 'BT UART RTS#', 'AP6275P BT_UART_CTS_N (43)', '', 'PX U13-A')
add('A', '49', 'I2C4_SCL_M3_WIFI', 'GPIO1_A3 / UART6_CTSN_M1', 'VCCIO4 1.8 V', 'BT UART CTS#', 'AP6275P BT_UART_RTS_N (42)', '', 'PX U13-A')

# ---------------- microSD ----------------
add('A', '57,61,62,63,67,69', 'SDMMC_CLK/D3/CMD/D0/D1/D2', 'GPIO4_D0..D5', 'VCCIO_SD (module-switched 3.3/1.8 V)', 'microSD', 'microSD socket (22R on CLK, ESD on all lines)', 'as IO board', 'PX U13-A; IO p6')
add('C', '74', 'SDMMC_DET_L', 'GPIO0_A4', 'PMUIO1 1.8 V', 'Card detect', 'socket CD switch to GND, 100k to VCCIO_FLASH', 'low = card present', 'PX J1 note; IO p6')
add('A', '75', 'SD_PWR_ON', 'GPIO3_C6', 'VCCIO5 3.3 V', 'SD card power switch', 'P-FET gate (0R bypass fitted by default, as IO board)', '', 'PX; IO p6')

# ---------------- Display (DSI1 4-lane) + touch + backlight ----------------
add('B', '175,177,181,183,193,195,194,196', 'MIPI_DPHY1_TX_D0..D3 N/P', 'DSI1 data', 'MIPI D-PHY', 'Display data lanes 0-3', 'Panel FPC pins 7/8,10/11,16/17,19/20', 'DSI1 is the 4-lane DSI exposed on CM5 (DSI0 is 2-lane only)', 'PX U13-B; DOC faq; panel DS s.4.1')
add('B', '187,189', 'MIPI_DPHY1_TX_CLKN/P', 'DSI1 clock', 'MIPI D-PHY', 'Display clock lane', 'Panel FPC pins 13/14', '', 'PX U13-B')
add('A', '41', 'LCD_RESET_L', 'GPIO1_B0', 'VCCIO4 1.8 V', 'Panel reset', 'Panel RESET (26); panel IOVCC is 1.8 V', 'no translator needed', 'PX; panel DS s.4.1, 6.2')
add('C', '34', 'LCD_PWREN_H', 'GPIO4_A3', 'VCCIO6 3.3 V', 'Panel power enable', 'Load switch for panel VCI 3.3 V', '', 'PX J1')
add('A', '21', 'PWM15_M1', 'GPIO4_B3', 'VCCIO6 3.3 V', 'Backlight PWM / enable', 'TPS61169 CTRL', '', 'PX; IO p10')
add('C', '69', 'I2C6_SDA_M3', 'GPIO4_B0', 'VCCIO6 3.3 V', 'Touch + keyboard I2C SDA', 'GT911 SDA (CTP FPC pin 5); keyboard FFC pin 8 (RP2040 I2C target 0x1F)', 'GT911 logic is 3.3 V; free because there is no FUSB302', 'PX J1; panel DS s.1.2, 4.2')
add('C', '71', 'I2C6_SCL_M3', 'GPIO4_B1', 'VCCIO6 3.3 V', 'Touch + keyboard I2C SCL', 'GT911 SCL (CTP pin 4); keyboard FFC pin 9', '', 'PX J1')
add('C', '38', 'GPIO4_A4', 'GPIO4_A4', 'VCCIO6 3.3 V', 'Touch INT', 'GT911 INT (pin 6)', 'bidirectional: also selects GT911 I2C address at reset', 'PX J1')
add('C', '40', 'GPIO4_A5', 'GPIO4_A5', 'VCCIO6 3.3 V', 'Touch RESET', 'GT911 RST (pin 7)', '', 'PX J1')

# ---------------- Cameras ----------------
add('B', '115,117,121,123,133,135,139,141', 'MIPI_DPHY0_RX_D0..D3 N/P', 'CSI (D/C-PHY0 RX)', 'MIPI D-PHY', 'CAM-A data lanes 0-3', 'FH35C-31S pins 14/15, 11/12, 5/6, 2/3', 'CAM-A = Radxa Camera 4K pinout (IO board Camera 1)', 'PX U13-B; IO p11')
add('B', '127,129', 'MIPI_DPHY0_RX_CLKN/P', 'CSI clock', 'MIPI D-PHY', 'CAM-A clock lane', 'FH35C-31S pins 17/18', '', 'PX U13-B; IO p11')
add('C', '10', 'GPIO1_B6_CAM2_CLK', 'MIPI_CAMERA1_CLK_M0', 'VCCIO4 1.8 V', 'CAM-A MCLK', 'FH35C-31S pin 20', '', 'PX J1; IO p11')
add('A', '47', 'MIPI_CAM2_PDN_L', 'GPIO1_A7', 'VCCIO4 1.8 V', 'CAM-A power-down', 'FH35C-31S pin 23', '', 'PX; IO p11')
add('A', '38', 'MIPI_CAM2_RST_L', 'GPIO1_B3', 'VCCIO4 1.8 V', 'CAM-A reset', 'FH35C-31S pin 27', '', 'PX; IO p11')
add('A', '35,36', 'I2C8_SCL/SDA_M2_CAM', 'GPIO1_D6/D7', 'VCCIO4 1.8 V', 'CAM-A I2C', 'FH35C-31S pins 24/25; 2.2k pull-ups to 1.8 V', 'module pull-ups are not fitted (NC)', 'PX; CM5 p17; IO p11')
add('B', '128,130,134,136', 'MIPI_CSI0_RX_D0/D1 N/P', 'CSI0 2-lane RX', 'MIPI D-PHY', 'CAM-B data lanes 0-1', '15-pin 1.0 mm FPC pins 13/14, 10/11 (Radxa reverse numbering)', 'CAM-B = Radxa Camera 8M 219 / RPi v2 pinout (IO board Camera 0)', 'PX U13-B; IO p11; DOC camera_8m')
add('B', '140,142', 'MIPI_CSI0_RX_CLK0N/P', 'CSI0 clock', 'MIPI D-PHY', 'CAM-B clock lane', '15-pin FPC pins 7/8', '', 'PX U13-B; IO p11')
add('A', '80,82', 'I2C7_SCL/SDA_M2', 'GPIO3_D2/D3', 'VCCIO5 3.3 V (2.2k pull-ups on module)', 'CAM-B I2C', '15-pin FPC pins 3/2', '', 'PX; CM5 p17; IO p11')
add('A', '44', 'GPIO1_B2_CAM1', 'GPIO1_B2', 'VCCIO4 1.8 V', 'CAM-B enable (CAM_IO0)', '15-pin FPC pin 5 (0R)', 'as IO board', 'PX; IO p11')
add('A', '45', 'GPIO1_A6_CAM1', 'GPIO1_A6', 'VCCIO4 1.8 V', 'CAM-B CAM_IO1', '15-pin FPC pin 4 (0R)', 'as IO board', 'PX; IO p11')

# ---------------- Audio ----------------
add('A', '46', 'I2S0_SCLK_TX', 'GPIO1_C3', 'VCCIO1 1.8 V (S0)', 'I2S BCLK', 'MAX98357A x2 BCLK', 'MAX98357A VIH = 1.3 V, so 1.8 V works; no MCLK needed', 'PX; CM5 p13; MAX98357A DS')
add('A', '48', 'I2S0_LRCK_TX', 'GPIO1_C5', 'VCCIO1 1.8 V', 'I2S LRCLK', 'MAX98357A x2 LRCLK', '', 'PX; CM5 p13')
add('A', '34', 'I2S0_SDO0', 'GPIO1_C7', 'VCCIO1 1.8 V', 'I2S data', 'MAX98357A x2 DIN', '', 'PX; CM5 p13')
add('C', '98', 'BT_REG_ON_H', 'GPIO0_D4', 'PMUIO2 3.3 V', 'Amp enable / channel select', 'MAX98357A SD_MODE: left amp via ~2k, right amp via 210k (Table 6)', '', 'PX J1; MAX98357A DS Table 5/6')
add('C', '75', 'GPIO1_C6_S', 'PDM0_CLK0_M0', 'VCCIO1 1.8 V', 'PDM mic clock', 'MEMS PDM microphone CLK', '', 'PX J1 func list')
add('C', '77', 'GPIO1_D5_S', 'PDM0_SDI0_M0', 'VCCIO1 1.8 V', 'PDM mic data', 'MEMS PDM microphone DATA', '', 'PX J1 func list')

add('C', '18', 'PWM11_M3', 'GPIO3_D5', 'VCCIO5 3.3 V', 'Charger PROCHOT# (throttle request)', 'BQ25713 PROCHOT# (open drain, 10k pull-up to VCC_3V3_S3)', 'asserts on battery-discharge current, low VSYS, input over-current: Linux throttles CPU/GPU', 'PX J1; BQ25713 DS pin 11')

# ---------------- Keyboard board interface ----------------
add('C', '93', 'GPIO0_C2', 'GPIO0_C2', 'PMUIO2 3.3 V', '5 V rail enable', 'TPS61089 EN (100k pull-up to VCC_3V3_S3 = on by default)', 'lets software drop USB-A/keyboard power in suspend', 'PX J1; CM5 p9')
add('C', '95', 'TYPEC5V_PWREN_H', 'GPIO0_D5', 'PMUIO2 3.3 V', 'Keyboard INT# (wake)', 'FFC pin 10 (10k pull-up to 3V3_S3, 1k series)', 'PMU GPIO so a key press can wake the SoC', 'PX J1; CM5 p9')
add('C', '87', 'GPIO4_A7', 'GPIO4_A7', 'VCCIO6 3.3 V', 'Keyboard RESET#', 'FFC pin 11 -> RP2040 RUN (open drain)', '', 'PX J1')
add('C', '85', 'BT_HOST_WAKE', 'GPIO4_B5', 'VCCIO6 3.3 V', 'Keyboard BOOT#', 'FFC pin 12 -> RP2040 QSPI_SS via 1k (open drain)', 'Radxa net name is BT_HOST_WAKE; repurposed', 'PX J1')

# ---------------- Deliberately unconnected (notable) ----------------
NC = [
 ('A', '78', 'GPIO_VREF', 'Module already ties it to VCC_3V3_S3 (R95031 0R), which sets VCCIO6 = 3.3 V. Radxa IO board leaves it NC.', 'CM5 p4, p17; IO p17'),
 ('B', '106', '5V_HDMI', 'Only feeds the on-module HDMI DDC level shifter (diode-OR with VCC_SYSIN). No HDMI on this board.', 'PX note; CM5 p4'),
 ('B', '157,159,163,165,169,171', 'MIPI_DPHY0_TX (DSI0, 2-lane)', 'Unused; panel uses 4-lane DSI1.', 'PX U13-B'),
 ('B', '145,147,151,153,170,172,176,178,182,184,188,190,199,200', 'HDMI0 TX/SBD/CEC/HPD/DDC', 'No HDMI.', 'PX U13-B'),
 ('C', '3,5,9,11,15,17,21,23,27,29', 'TYPEC0 SBU/SSTX/SSRX (USB3 + DP alt-mode lanes)', 'No DP alt-mode (your choice), USB-C is USB 2.0 only.', 'PX J1'),
 ('C', '39,41', 'PCIE20_2_REFCLKP/N', 'Combo PHY2 is used as USB 3.0 for the modem, so its PCIe refclk is unused.', 'PX J1'),
 ('A', '3,4,5,6,9,10,11,12,15,17,19', 'PHY1_MDI0-3, PHY1 LEDs', 'No Ethernet.', 'PX U13-A'),
 ('A', '28,30,31,100', 'SPI0_M1', 'Spare (3.3 V).', 'PX U13-A'),
 ('C', '24', 'WIFI_PWR_EN (GPIO1_D3)', 'Spare. VCCIO1 is an S0 rail, so it is unsuitable for WL_REG_ON if Wi-Fi must survive suspend.', 'CM5 p13'),
 ('C', '12,20,36,46,79,83', 'GPIO1_B7, GPIO1_C1, HP_DET_L, GPIO1_D1, GPIO1_C4_S, GPIO1_D2', 'Spare 1.8 V GPIOs.', 'PX J1'),
 ('A', '37', 'TP_INT_L (GPIO1_B5)', 'Spare 1.8 V S3 GPIO.', 'PX'),
  ('A/C', '50,54 / 30 / 96', 'I2S0_MCLK, I2S0_SDI0 / SARADC_VIN3 / SARADC_VIN4', 'Unused (no codec, no headphone jack).', 'PX'),
 ('C', '90', 'RTC_32K_SOC', 'Module-side 32 kHz input/output whose direction is UNVERIFIED (pinout says "already in use"). Left NC.', 'CM5 p4; PX J1 note'),
 ('B', '101', 'TYPEC0_USB20_OTG_ID', 'NC; role is set in software.', 'PX U13-B'),
]

# ---------------- Power budget ----------------
# load, rail, worst-case W at load, realistic-heavy W, light-use W, converter, eta, source of number
PB = [
 ('CM5 module (SoC, RAM, eMMC, PMIC)', 'CM5_VIN 4.8 V', 12.0, 8.0, 3.0, 'TPS61088 boost', 0.92, 'Radxa: typ 2 A @ 4 V (8 W), recommended supply 4 V/3 A (12 W) [DOC README]'),
 ('CM5 3V3_S3 / 1V8_S0 carrier loads (SD card 0.66 W, panel logic 0.18 W, touch 0.07 W, pull-ups)', 'via CM5 regulators', 1.1, 0.4, 0.2, 'TPS61088 + on-module regulators', 0.83, 'SD 200 mA peak (estimate), panel IDD 56 mA max [panel DS 6.2]'),
 ('LTE EM060K-GL', 'VCC_LTE 3.7 V', 3.96, 2.0, 0.08, 'TPS63020 buck-boost', 0.90, 'Max listed data-transfer current 1.07 A @ 23 dBm (LTE B30); idle 21 mA [EM060K HD V1.1 Table 45]. Quectel PSU guideline is 3 A cont./4 A peak.'),
 ('Wi-Fi/BT AP6275P', 'VCC3V3_AUX 3.3 V', 3.96, 0.5, 0.3, 'TPS63020 buck-boost', 0.90, 'VBAT peak 1200 mA @ 3.3 V [AP6275P DS]'),
 ('USB hub USB2514B + CAM-B 3.3 V', 'VCC3V3_AUX 3.3 V', 0.6, 0.35, 0.3, 'TPS63020 buck-boost', 0.90, 'estimate; UNVERIFIED until hub/camera datasheets read'),
 ('USB-A x2 at 500 mA each', 'VCC5V0 5.1 V', 5.1, 0.0, 0.0, 'TPS61089 boost', 0.90, 'USB 2.0 port limit 500 mA (hard-limited by switches)'),
 ('Keyboard board (RP2040, trackpad, key backlight)', 'VCC5V0 5.1 V', 0.5, 0.3, 0.2, 'TPS61089 boost', 0.90, 'estimate (BBQ20KBD-class), UNVERIFIED'),
 ('CAM-A (4K camera, 5 V + 3.3 V pins)', 'VCC5V0 / 3V3', 0.6, 0.0, 0.0, 'TPS61089 boost', 0.90, 'estimate, UNVERIFIED (Radxa Camera 4K power not published)'),
 ('Display backlight (12 LED, 18.6 V x 40 mA)', 'LED boost', 0.744, 0.56, 0.37, 'TPS61169 LED boost', 0.85, 'panel DS 6.3 (100 % / 75 % / 50 %)'),
 ('Speakers 2 x MAX98357A', 'VSYS', 1.6, 0.4, 0.1, 'class-D', 0.85, 'about 0.8 W per channel into 8 ohm at 3.7 V (estimate, depends on speaker)'),
 ('PD/charger/fuel gauge/RTC/LEDs/misc', 'various', 0.15, 0.1, 0.05, '-', 1.0, 'TPS25751, BQ25713 IQ, MAX17055, LEDs (estimate)'),
]

# ---------------- Parts shortlist (stock = JLCPCB stock at query time) ----------------
PARTS = [
 ('CM5 B2B receptacle x3', 'Hirose DF40C-100DS-0.4V(51)', 'C597931', 33535, 'EXT', '1.5 mm mated height with the CM5 DF40C-100DP plugs; same part as Radxa IO board'),
 ('USB-C PD sink controller', 'TI TPS25751DREFR', 'C30169739', 5713, 'EXT', 'D variant (WQFN-38); TI-listed integrated control of BQ25713; boots from >= 36 KB EEPROM at 0x50'),
 ('PD config EEPROM (>= 36 KB)', '24C512-class 64 KB (part TBD at checkpoint 2)', '-', None, '-', 'TPS25751 DS: EEPROM at least 36 kB at 7-bit 0x50; programming pads (decision Q12)'),
 ('NVDC buck-boost charge controller', 'TI BQ25713RSNR', 'C2878935', 3254, 'EXT', 'external FETs: 4 x N-ch switching + P-ch BATFET (sized >= 12 A), RSR/RAC sense resistors; PROCHOT# output'),
 ('Fuel gauge (current sensing)', 'ADI MAX17055ETB+T', 'C2976422', 6107, 'EXT', 'TDFN-10; mainline max17042_battery; datasheet not yet obtained (UNVERIFIED pin-out/sense resistor)'),
 ('CM5 supply 4.8 V boost', 'TI TPS61088RHLR', 'C87357', 9348, 'EXT', '10 A switch; VOUT 4.5-12.6 V; standalone (no I2C)'),
 ('5 V USB/keyboard boost', 'TI TPS61089RNRR', 'C165129', 11137, 'EXT', '7 A switch, 2 x 2.5 mm'),
 ('LTE 3.7 V and AUX 3.3 V buck-boost (x2)', 'TI TPS63020DSJR', 'C15483', 26202, 'EXT', '4 A switch; about 2 A in boost mode'),
 ('Backlight LED boost', 'TI TPS61169DCKR', 'C71045', 23247, 'EXT', '38 V OVP, PWM dimming on CTRL'),
 ('USB-A VBUS current-limited switch x2 (+1 keyboard)', 'TI TPS2553DBVR-1 / Silergy SY6280AAC', 'C111738 / C55136', 11974, 'EXT', 'adjustable current limit, set to about 0.6 A'),
 ('USB 2.0 hub, 4 port', 'Microchip USB2514B-AEZC-TR', 'C16251', 15399, 'EXT', 'MTT, per-port power control; alt: Terminus FE1.1S-BQFN24B C6776948 (Radxa uses it)'),
 ('Wi-Fi 6 / BT 5 module', 'AMPAK AP6275P', 'C2984107', 494, 'EXT', 'PCIe Wi-Fi (BCM43752) + UART BT; VDDIO 1.8 V only; needs 37.4 MHz crystal, 32.768 kHz LPO'),
 ('37.4 MHz crystal (AP6275P)', 'HELE X3S037400BA1H-Z', 'C254335', 2731, 'EXT', 'check load capacitance against AP6275P DS'),
 ('RTC + 32.768 kHz clock out', 'HTCSEMI HT8563ARZ (PCF8563-class)', 'C2834465', 1024, 'EXT', 'HYM8563 (Radxa part) is out of stock'),
 ('Class-D amp x2', 'ADI MAX98357AETE+T', 'C910544', 30911, 'EXT', 'I2S, no MCLK, VIH 1.3 V'),
 ('3.3<->1.8 V translator (PCIe sideband)', 'Union UM3204H / TI TXS0104E', 'C620004 / C154926', 3419, 'EXT', 'Radxa uses UM3204'),
 ('M.2 Key-B socket (3042)', 'HOAUC HYCW11B-05NGFF-320B (3.05 mm) or lower variant', 'C41430834', 854, 'EXT', 'final height choice at checkpoint 3'),
 ('nano-SIM push-push socket', 'JXTCONN NANO SIM 7P 1.37H PUSH', 'C53207808', 448, 'EXT', 'no combo SIM+microSD tray stocked at JLCPCB'),
 ('microSD push-push socket', 'SHOU HAN MICRO SD4.0 9P H1.4 PUSH', 'C53223918', 983, 'EXT', 'needs card-detect pin check'),
 ('CAM-A FPC 31-pin 0.3 mm', 'Hirose FH35C-31S-0.3SHW(50)', 'C424662', 4309, 'EXT', 'same as Radxa IO board Camera 1; back-flip, 0.88 mm tall'),
 ('Display FPC 30-pin 0.5 mm (flip-lock)', 'HanElectricity 05A15L30P (1.5 mm H)', 'C22459560', 1858, 'EXT', 'contact side must match panel FPC (UNVERIFIED)'),
 ('Touch FPC 8-pin 0.5 mm', 'XUNPU FPC-05F-8PH15', 'C2856815', 22943, 'EXT', ''),
 ('Keyboard FFC 12-pin 0.5 mm (both boards)', 'BXCONN FC-05A12P11H20 (bottom contact, flip)', 'C23398836', 3670, 'EXT', ''),
 ('Q20 keyboard connector (Board B)', 'Hirose BM20B(0.8)-40DS-0.4V(51)', 'C424543', 8819, 'EXT', 'same as BBQ20KBD'),
 ('Keyboard MCU (Board B)', 'Raspberry Pi RP2040', 'C2040', 54524, 'EXT', ''),
 ('u.FL receptacle (Wi-Fi x2)', 'Hirose U.FL-R-SMT(10)', 'C434808', 16958, 'EXT', ''),
 ('Battery connector (decision Q3)', 'Molex Micro-Lock Plus 2.0 mm 505575-0971 (9-pin: 4 BAT+, 4 GND, NTC)', 'C17385595', 0, 'EXT', '12 A at 3.0 A/contact (distributor rating; Molex PS 5055700001 not read); Global Sourcing'),
]

def write():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'pin_budget.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['conn', 'pins', 'radxa_net', 'soc_function_gpio', 'io_domain', 'use', 'connects_to', 'notes', 'source'])
        w.writerows(P)
    with open(os.path.join(OUT, 'pin_budget_nc.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['conn', 'pins', 'radxa_net', 'reason', 'source']); w.writerows(NC)
    md = ['| Conn | Pin(s) | Radxa net | SoC function / GPIO | I/O domain | Used as | Connects to | Notes | Source |', '|---|---|---|---|---|---|---|---|---|']
    for r in P: md.append('| ' + ' | '.join(str(x).replace('|', '/') for x in r) + ' |')
    md2 = ['| Conn | Pin(s) | Radxa net | Why unconnected | Source |', '|---|---|---|---|---|']
    for r in NC: md2.append('| ' + ' | '.join(str(x).replace('|', '/') for x in r) + ' |')
    open(os.path.join(OUT, '_pin_table.md'), 'w').write('\n'.join(md) + '\n')
    open(os.path.join(OUT, '_pin_nc_table.md'), 'w').write('\n'.join(md2) + '\n')
    # power budget
    rows = []; tot = [0, 0, 0]; tot_in = [0, 0, 0]
    for name, rail, wc, heavy, light, conv, eta, src in PB:
        ins = [wc / eta, heavy / eta, light / eta]
        for i in range(3): tot[i] += (wc, heavy, light)[i]; tot_in[i] += ins[i]
        rows.append((name, rail, f'{wc:.2f}', f'{heavy:.2f}', f'{light:.2f}', conv, f'{eta:.2f}', f'{ins[0]:.2f}', f'{ins[1]:.2f}', f'{ins[2]:.2f}', src))
    with open(os.path.join(OUT, 'power_budget.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['load', 'rail', 'worst_W', 'heavy_W', 'light_W', 'converter', 'eta', 'worst_from_VSYS_W', 'heavy_from_VSYS_W', 'light_from_VSYS_W', 'source']); w.writerows(rows)
    md = ['| Load | Rail | Worst W | Heavy W | Light W | Converter (η) | Worst from VSYS | Heavy from VSYS | Light from VSYS | Basis |', '|---|---|---|---|---|---|---|---|---|---|']
    for r in rows: md.append(f'| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} ({r[6]}) | {r[7]} | {r[8]} | {r[9]} | {r[10]} |')
    md.append(f'| **Total** | | **{tot[0]:.1f}** | **{tot[1]:.1f}** | **{tot[2]:.1f}** | | **{tot_in[0]:.1f}** | **{tot_in[1]:.1f}** | **{tot_in[2]:.1f}** | |')
    open(os.path.join(OUT, '_power_table.md'), 'w').write('\n'.join(md) + '\n')
    # battery current table
    bat = ['| Case | Power from VSYS | I_bat @ 4.2 V | I_bat @ 3.7 V | I_bat @ 3.5 V |', '|---|---|---|---|---|']
    for label, pw in (('Worst case, all loads at max', tot_in[0]), ('Realistic heavy use', tot_in[1]), ('Light use', tot_in[2])):
        pw2 = pw * 1.02  # +2 % BATFET/connector/trace loss
        bat.append(f'| {label} | {pw:.1f} W | {pw2/4.2:.2f} A | {pw2/3.7:.2f} A | {pw2/3.5:.2f} A |')
    open(os.path.join(OUT, '_battery_table.md'), 'w').write('\n'.join(bat) + '\n')
    # parts
    with open(os.path.join(OUT, 'parts_shortlist.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['function', 'part', 'lcsc', 'jlc_stock_2026_10_14', 'library', 'note']); w.writerows(PARTS)
    md = ['| Function | Part | LCSC | JLC stock (14 Oct 2026) | Note |', '|---|---|---|---|---|']
    for r in PARTS: md.append(f'| {r[0]} | {r[1]} | {r[2]} | {r[3] if r[3] is not None else "-"} | {r[5]} |')
    open(os.path.join(OUT, '_parts_table.md'), 'w').write('\n'.join(md) + '\n')
    print('pins used rows:', len(P), ' NC rows:', len(NC), ' totals W (worst/heavy/light at loads):', [round(x, 1) for x in tot], ' from VSYS:', [round(x, 1) for x in tot_in])

if __name__ == '__main__':
    write()
