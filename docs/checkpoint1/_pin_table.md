| Conn | Pin(s) | Radxa net | SoC function / GPIO | I/O domain | Used as | Connects to | Notes | Source |
|---|---|---|---|---|---|---|---|---|
| A | 77,79,81,83,85,87 | VCC_SYSIN | - | input 3.6-5.2 V | Module supply | CM5_VIN = 4.8 V boost (TPS61088) | Radxa recommends 4 V/3 A; 4.8 V used because a boost from VSYS (max 4.55 V) must output above VSYS. 6 pins x 0.3 A DF40 contact rating (same as Radxa IO board). | PX U13-A; DOC README; IO p15 |
| A | 84,86 | VCC_3V3_S3 | - | output, 600 mA max | 3.3 V for low-power carrier loads | microSD VDD, panel VCI (via load switch), GT911 VDD, I2C pull-ups, level-shifter B side, regulator ENs | Budget <= 300 mA of 600 mA | PX U13-A; CM5 p4 |
| C | 92 | VCC_3V3_S3 | - | output | same rail | same as above |  | PX J1; CM5 p4 (R9241 0R) |
| A | 88,90 | VCC_1V8_S0 | - | output, 600 mA max | 1.8 V for carrier loads | panel IOVCC, AP6275P VDDIO, level-shifter A side, CAM-A I2C pull-ups, PDM mic VDD | Budget <= 100 mA | PX U13-A; CM5 p4 |
| A | 73 | VCCIO_FLASH | = VCC_1V8_S3 | output (1.8 V, S3) | pull-up rail | SDMMC_DET_L 100k pull-up | Module ties VCCIO_FLASH to VCC_1V8_S3 (R4000 0R); IO board pulls SD-detect to VCC_1V8_S3 | CM5 p4; IO p6 |
| A/B/C | all GND pins | GND | - | - | Ground | GND planes L2/L5 |  | PX |
| A | 99 | PWRON_L | RK806 PWRON | PMIC input (internal pull-up) | Power button | Tactile switch to GND, 100R + ESD (as IO board) | RK806 handles press/long-press | PX; CM5 p18; IO p19 |
| A | 92 | RESET_L | NPOR/RK806 RESETB | PMIC | Reset button | Tactile switch to GND, 100R + ESD |  | PX; IO p19 |
| A | 93 | SARADC_VIN0_BOOT | SARADC_IN0 | 1.8 V ADC | Maskrom button | Tactile switch to GND, 100R + ESD | Module also has its own maskrom button (SW9201) | PX; CM5 p13; IO p19 |
| C | 26 | SARADC_VIN1_KEY/RECOVERY | SARADC_IN1 | 1.8 V ADC (10k pull-up on module) | Recovery + Vol+/Vol- (ADC ladder) | Recovery = short to GND; Vol+/Vol- through resistors (values at checkpoint 2) | adc-keys in device tree | PX; CM5 p13; IO p19 |
| C | 28 | SARADC_VIN2_DC | SARADC_IN2 | 1.8 V ADC | VSYS monitor | VSYS / 3 divider (4.55 V max -> 1.52 V) | optional, debug aid | PX; CM5 p13; IO p15 |
| A | 51 | UART2_RX_M0 | GPIO0_B6 | PMUIO2 3.3 V | Debug console RX | 3-pin debug pads/header | 1.5 Mbaud Rockchip default | PX; CM5 p9 |
| A | 55 | UART2_TX_M0 | GPIO0_B5 | PMUIO2 3.3 V | Debug console TX | 3-pin debug pads/header |  | PX; CM5 p9 |
| A | 95 | WIFI_LED | GPIO3_C5 | VCCIO5 3.3 V | Status LED | LED + resistor |  | PX; CM5 p17 |
| C | 4 | GPIO3_C0 | I2C3_SDA_M1 | VCCIO5 3.3 V | SYS_I2C SDA | TPS25751 I2Ct, MAX17055, HT8563 RTC | 2.2k pull-up to VCC_3V3_S3 | PX J1; CM5 p17 |
| C | 6 | GPIO3_B7 | I2C3_SCL_M1 | VCCIO5 3.3 V | SYS_I2C SCL | same |  | PX J1; CM5 p17 |
| C | 96 | CC_INT0_L | GPIO0_C4 | PMUIO2 3.3 V | PD controller IRQ (wake) | TPS25751 I2Ct_IRQ (open drain) | PMU GPIO = can wake from suspend | PX J1; CM5 p9 |
| A | 89 | PWM4_M0 | GPIO0_C5 | PMUIO2 3.3 V | RTC alarm IRQ (wake) | HT8563 INT# (open drain, 10k pull-up) |  | PX; CM5 p9 |
| C | 94 | GPIO0_D3 | GPIO0_D3 | PMUIO2 3.3 V | Fuel-gauge alert (wake) | MAX17055 ALRT# (open drain) | 10k pull-up to VCC_3V3_S3 | PX J1; CM5 p9 |
| B | 103,105 | TYPEC0_OTG_DM/DP | USB20 OTG0 | USB PHY | USB-C data (device default, Maskrom) | USB-C receptacle D-/D+ via 2.2R + CMC + ESD | OTG0 is the Maskrom/download port | PX U13-B; CM5 p12; IO p18 |
| C | 97 | TYPEC0_OTG_VBUSDET | TYPEC0_USB20_VBUSDET | 3.3 V (4.7k pull-up on module) | left at module default | - (option: NMOS pull-down when VBUS absent) | Same as Radxa IO board (pin NC) | PX J1; CM5 p12; IO p17 |
| C | 63,65 | USB20_HOST0_DP/DM | USB2 HOST0 | USB PHY | USB hub upstream | USB2514B upstream port | Same port Radxa uses for its FE1.1s hub | PX J1; IO p12 |
| C | 45,47 | USB20_HOST1_DP/DM | USB2 HOST1 | USB PHY | LTE modem USB 2.0 (direct) | M.2 Key-B pins 7/9 (USB_DP/USB_DM) | USB 2.0 half of the modem USB 3.0 link (same pairing as Radxa IO-board USB 3.0 port) | PX J1; IO p13; EM060K HD V1.1 s.4.1 |
| C | 51,53 | USB30_2_SSTXP/N | USB3 SS TX (combo PHY2) | USB3 PHY | LTE modem USB 3.0 TX | M.2 pins 37/35 (USB_SS_RX_P/M) via 100 nF | decision Q7; host-side AC caps per Quectel Fig. 18 | PX J1; EM060K HD V1.1 Fig. 18 |
| C | 57,59 | USB30_2_SSRXP/N | USB3 SS RX (combo PHY2) | USB3 PHY | LTE modem USB 3.0 RX | M.2 pins 31/29 (USB_SS_TX_P/M), no caps (inside module) | combo PHY2 set to USB3 mode in device tree | PX J1; EM060K HD V1.1 Fig. 18 |
| C | 89 | GPIO4_A6 | GPIO4_A6 | VCCIO6 3.3 V | Hub reset | USB2514B RESET_N (+ RC) |  | PX J1; CM5 p17 |
| A | 56 | GPIO0_C7 | GPIO0_C7 | PMUIO2 3.3 V | LTE rail enable | TPS63020 (3.7 V) EN | PMU GPIO keeps state in suspend | PX; CM5 p9 |
| A | 58 | GPIO0_D0 | GPIO0_D0 | PMUIO2 3.3 V | FULL_CARD_POWER_OFF# | M.2 pin 6 (series 1k) | EM060K: 3.3 V tolerant, >= 1.19 V = on, 100k internal pull-down | PX; EM060K HD V1.1 s.3.6 |
| C | 8 | TYPEC0_SBU1_DC | GPIO3_C4 | VCCIO5 3.3 V | LTE RESET# | M.2 pin 67 via NMOS (open drain) | EM060K: VIH min 1.3 V, internal pull-up; Quectel ref = open-collector | PX J1; EM060K HD V1.1 s.3.8 |
| C | 14 | TYPEC0_SBU2_DC | GPIO3_D4 | VCCIO5 3.3 V | LTE W_DISABLE1# | M.2 pin 8 via NMOS (open drain) | internal pull-up; VIL max 0.4 V | PX J1; EM060K HD V1.1 s.4.4.1 |
| A | 91 | HOST_WAKE_BT_H | GPIO0_C6 | PMUIO2 3.3 V | LTE WAKE_ON_WAN# (wake) | M.2 pin 23 (open drain, 10k pull-up to 3V3_S3) | Module pin is OD, 1.8/3.3 V | PX; EM060K HD V1.1 pin table |
| B | 110,112 | PCIE20_0_REFCLKP/N | PCIe2 lane 0 (combo PHY0) | PCIe | Wi-Fi PCIe refclk | AP6275P PCIE_RCLK_P/N (35/33) | Same lane Radxa routes to its M.2 E-key Wi-Fi | PX U13-B; IO p7 |
| B | 122,124 | PCIE20_0_TXP/N | PCIe2 lane 0 | PCIe | Wi-Fi PCIe TX | AP6275P PCIE_RX_P/N (45/44) via 100 nF |  | PX U13-B; IO p7 |
| B | 116,118 | PCIE20_0_RXP/N | PCIe2 lane 0 | PCIe | Wi-Fi PCIe RX | AP6275P PCIE_TX_P/N (47/46) (AC caps: check AP6275P ref) | UNVERIFIED: whether AP6275P has internal TX caps | PX U13-B; AP6275P DS p15-16 |
| B | 109 | PCIE20X1_2_PERSTN_M0 | GPIO3_D1 | VCCIO5 3.3 V | PCIe PERST# | AP6275P PCIE_PREST_L (12) via 3.3->1.8 V translator | AP6275P VDDIO is 1.8 V only (abs max 2.07 V) | PX U13-B; AP6275P DS |
| B | 102 | PCIE20X1_2_CLKREQN_M0 | GPIO3_C7 | VCCIO5 3.3 V | PCIe CLKREQ# | AP6275P PCIE_CLKREQ_L (37, OD) via translator |  | PX U13-B; AP6275P DS |
| A | 24 | PCIE20X1_2_WAKEN_M0 | GPIO3_D0 | VCCIO5 3.3 V | PCIe WAKE# | AP6275P PCIE_PME_L (24, OD) via translator |  | PX U13-A; AP6275P DS |
| A | 20 | HP_INT | GPIO0_A0 | PMUIO1 1.8 V | WL_HOST_WAKE (wake) | AP6275P WL_HOST_WAKE (16) | 1.8 V PMU GPIO, no translator | PX; CM5 p9; AP6275P DS |
| A | 29 | GSENSOR_INT | GPIO1_A4 | VCCIO4 1.8 V (S3) | WL_REG_ON | AP6275P WL_REG_ON (15) | S3 domain so Wi-Fi can stay up in suspend | PX; CM5 p17; AP6275P DS |
| A | 40 | GPIO1_B1 | GPIO1_B1 | VCCIO4 1.8 V (S3) | BT_REG_ON | AP6275P BT_REG_ON (38) |  | PX; CM5 p17 |
| A | 39 | TP_RST_L | GPIO1_B4 | VCCIO4 1.8 V (S3) | BT_WAKE (host->BT) | AP6275P BT_WAKE (49) | Radxa net name is TP_RST_L; touch uses 3.3 V pins instead | PX; CM5 p17 |
| C | 81 | RTC_INT_L | GPIO0_B0 | PMUIO1 1.8 V | BT_HOST_WAKE (wake) | AP6275P BT_HOST_WAKE (50) | repurposed; RTC IRQ goes to GPIO0_C5 | PX J1; CM5 p9 |
| A | 97 | USB_HOST_PWREN_H | GPIO1_A0 / UART6_RX_M1 | VCCIO4 1.8 V | BT UART RX | AP6275P BT_UART_TXD (40) | UART6_M1 4-wire with RTS/CTS | PX U13-A func list; CM5 p17 |
| A | 27 | WIFI_REG_ON_E | GPIO1_A1 / UART6_TX_M1 | VCCIO4 1.8 V | BT UART TX | AP6275P BT_UART_RXD (41) |  | PX U13-A |
| A | 25 | I2C4_SDA_M3_WIFI | GPIO1_A2 / UART6_RTSN_M1 | VCCIO4 1.8 V | BT UART RTS# | AP6275P BT_UART_CTS_N (43) |  | PX U13-A |
| A | 49 | I2C4_SCL_M3_WIFI | GPIO1_A3 / UART6_CTSN_M1 | VCCIO4 1.8 V | BT UART CTS# | AP6275P BT_UART_RTS_N (42) |  | PX U13-A |
| A | 57,61,62,63,67,69 | SDMMC_CLK/D3/CMD/D0/D1/D2 | GPIO4_D0..D5 | VCCIO_SD (module-switched 3.3/1.8 V) | microSD | microSD socket (22R on CLK, ESD on all lines) | as IO board | PX U13-A; IO p6 |
| C | 74 | SDMMC_DET_L | GPIO0_A4 | PMUIO1 1.8 V | Card detect | socket CD switch to GND, 100k to VCCIO_FLASH | low = card present | PX J1 note; IO p6 |
| A | 75 | SD_PWR_ON | GPIO3_C6 | VCCIO5 3.3 V | SD card power switch | P-FET gate (0R bypass fitted by default, as IO board) |  | PX; IO p6 |
| B | 175,177,181,183,193,195,194,196 | MIPI_DPHY1_TX_D0..D3 N/P | DSI1 data | MIPI D-PHY | Display data lanes 0-3 | Panel FPC pins 7/8,10/11,16/17,19/20 | DSI1 is the 4-lane DSI exposed on CM5 (DSI0 is 2-lane only) | PX U13-B; DOC faq; panel DS s.4.1 |
| B | 187,189 | MIPI_DPHY1_TX_CLKN/P | DSI1 clock | MIPI D-PHY | Display clock lane | Panel FPC pins 13/14 |  | PX U13-B |
| A | 41 | LCD_RESET_L | GPIO1_B0 | VCCIO4 1.8 V | Panel reset | Panel RESET (26); panel IOVCC is 1.8 V | no translator needed | PX; panel DS s.4.1, 6.2 |
| C | 34 | LCD_PWREN_H | GPIO4_A3 | VCCIO6 3.3 V | Panel power enable | Load switch for panel VCI 3.3 V |  | PX J1 |
| A | 21 | PWM15_M1 | GPIO4_B3 | VCCIO6 3.3 V | Backlight PWM / enable | TPS61169 CTRL |  | PX; IO p10 |
| C | 69 | I2C6_SDA_M3 | GPIO4_B0 | VCCIO6 3.3 V | Touch + keyboard I2C SDA | GT911 SDA (CTP FPC pin 5); keyboard FFC pin 8 (RP2040 I2C target 0x1F) | GT911 logic is 3.3 V; free because there is no FUSB302 | PX J1; panel DS s.1.2, 4.2 |
| C | 71 | I2C6_SCL_M3 | GPIO4_B1 | VCCIO6 3.3 V | Touch + keyboard I2C SCL | GT911 SCL (CTP pin 4); keyboard FFC pin 9 |  | PX J1 |
| C | 38 | GPIO4_A4 | GPIO4_A4 | VCCIO6 3.3 V | Touch INT | GT911 INT (pin 6) | bidirectional: also selects GT911 I2C address at reset | PX J1 |
| C | 40 | GPIO4_A5 | GPIO4_A5 | VCCIO6 3.3 V | Touch RESET | GT911 RST (pin 7) |  | PX J1 |
| B | 115,117,121,123,133,135,139,141 | MIPI_DPHY0_RX_D0..D3 N/P | CSI (D/C-PHY0 RX) | MIPI D-PHY | CAM-A data lanes 0-3 | FH35C-31S pins 14/15, 11/12, 5/6, 2/3 | CAM-A = Radxa Camera 4K pinout (IO board Camera 1) | PX U13-B; IO p11 |
| B | 127,129 | MIPI_DPHY0_RX_CLKN/P | CSI clock | MIPI D-PHY | CAM-A clock lane | FH35C-31S pins 17/18 |  | PX U13-B; IO p11 |
| C | 10 | GPIO1_B6_CAM2_CLK | MIPI_CAMERA1_CLK_M0 | VCCIO4 1.8 V | CAM-A MCLK | FH35C-31S pin 20 |  | PX J1; IO p11 |
| A | 47 | MIPI_CAM2_PDN_L | GPIO1_A7 | VCCIO4 1.8 V | CAM-A power-down | FH35C-31S pin 23 |  | PX; IO p11 |
| A | 38 | MIPI_CAM2_RST_L | GPIO1_B3 | VCCIO4 1.8 V | CAM-A reset | FH35C-31S pin 27 |  | PX; IO p11 |
| A | 35,36 | I2C8_SCL/SDA_M2_CAM | GPIO1_D6/D7 | VCCIO4 1.8 V | CAM-A I2C | FH35C-31S pins 24/25; 2.2k pull-ups to 1.8 V | module pull-ups are not fitted (NC) | PX; CM5 p17; IO p11 |
| B | 128,130,134,136 | MIPI_CSI0_RX_D0/D1 N/P | CSI0 2-lane RX | MIPI D-PHY | CAM-B data lanes 0-1 | 15-pin 1.0 mm FPC pins 13/14, 10/11 (Radxa reverse numbering) | CAM-B = Radxa Camera 8M 219 / RPi v2 pinout (IO board Camera 0) | PX U13-B; IO p11; DOC camera_8m |
| B | 140,142 | MIPI_CSI0_RX_CLK0N/P | CSI0 clock | MIPI D-PHY | CAM-B clock lane | 15-pin FPC pins 7/8 |  | PX U13-B; IO p11 |
| A | 80,82 | I2C7_SCL/SDA_M2 | GPIO3_D2/D3 | VCCIO5 3.3 V (2.2k pull-ups on module) | CAM-B I2C | 15-pin FPC pins 3/2 |  | PX; CM5 p17; IO p11 |
| A | 44 | GPIO1_B2_CAM1 | GPIO1_B2 | VCCIO4 1.8 V | CAM-B enable (CAM_IO0) | 15-pin FPC pin 5 (0R) | as IO board | PX; IO p11 |
| A | 45 | GPIO1_A6_CAM1 | GPIO1_A6 | VCCIO4 1.8 V | CAM-B CAM_IO1 | 15-pin FPC pin 4 (0R) | as IO board | PX; IO p11 |
| A | 46 | I2S0_SCLK_TX | GPIO1_C3 | VCCIO1 1.8 V (S0) | I2S BCLK | MAX98357A x2 BCLK | MAX98357A VIH = 1.3 V, so 1.8 V works; no MCLK needed | PX; CM5 p13; MAX98357A DS |
| A | 48 | I2S0_LRCK_TX | GPIO1_C5 | VCCIO1 1.8 V | I2S LRCLK | MAX98357A x2 LRCLK |  | PX; CM5 p13 |
| A | 34 | I2S0_SDO0 | GPIO1_C7 | VCCIO1 1.8 V | I2S data | MAX98357A x2 DIN |  | PX; CM5 p13 |
| C | 98 | BT_REG_ON_H | GPIO0_D4 | PMUIO2 3.3 V | Amp enable / channel select | MAX98357A SD_MODE: left amp via ~2k, right amp via 210k (Table 6) |  | PX J1; MAX98357A DS Table 5/6 |
| C | 75 | GPIO1_C6_S | PDM0_CLK0_M0 | VCCIO1 1.8 V | PDM mic clock | MEMS PDM microphone CLK |  | PX J1 func list |
| C | 77 | GPIO1_D5_S | PDM0_SDI0_M0 | VCCIO1 1.8 V | PDM mic data | MEMS PDM microphone DATA |  | PX J1 func list |
| C | 18 | PWM11_M3 | GPIO3_D5 | VCCIO5 3.3 V | Charger PROCHOT# (throttle request) | BQ25713 PROCHOT# (open drain, 10k pull-up to VCC_3V3_S3) | asserts on battery-discharge current, low VSYS, input over-current: Linux throttles CPU/GPU | PX J1; BQ25713 DS pin 11 |
| C | 93 | GPIO0_C2 | GPIO0_C2 | PMUIO2 3.3 V | 5 V rail enable | TPS61089 EN (100k pull-up to VCC_3V3_S3 = on by default) | lets software drop USB-A/keyboard power in suspend | PX J1; CM5 p9 |
| C | 95 | TYPEC5V_PWREN_H | GPIO0_D5 | PMUIO2 3.3 V | Keyboard INT# (wake) | FFC pin 10 (10k pull-up to 3V3_S3, 1k series) | PMU GPIO so a key press can wake the SoC | PX J1; CM5 p9 |
| C | 87 | GPIO4_A7 | GPIO4_A7 | VCCIO6 3.3 V | Keyboard RESET# | FFC pin 11 -> RP2040 RUN (open drain) |  | PX J1 |
| C | 85 | BT_HOST_WAKE | GPIO4_B5 | VCCIO6 3.3 V | Keyboard BOOT# | FFC pin 12 -> RP2040 QSPI_SS via 1k (open drain) | Radxa net name is BT_HOST_WAKE; repurposed | PX J1 |
