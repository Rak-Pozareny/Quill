# Orange Pi CM5 in the CM5 carrier: pin check (2026-10-22)

Every CM5 pin Board A uses (docs/checkpoint2/cm5_pin_map.csv, Radxa CM5 v2.21 pinout) against the Orange Pi CM5
IO description (orangepi-cm5-pinmap.pdf, mirrored at raspipcb.com/wp-content/uploads/2025/01/; orangepi.org refused
the connection). JP1 = connector A, JP2 = B (pins 101-200 here), JP3 = C. 'same' = the same SoC signal on that pin;
'DIFF' = a different one; '??' = not read from the PDF (wrapped text). Names in the 'opi' column can be cut off where
the PDF wraps. Result: **not compatible** (connector A: 37 of 73 used pins differ; connector C: almost all differ).

```
same A  1  radxa=GND                               opi=GND                carrier=GND
same A  2  radxa=GND                               opi=GND                carrier=GND
same A  7  radxa=GND                               opi=GND                carrier=GND
same A  8  radxa=GND                               opi=GND                carrier=GND
same A 13  radxa=GND                               opi=GND                carrier=GND
same A 14  radxa=GND                               opi=GND                carrier=GND
DIFF A 20  radxa=HP_INT                 GPIO0_A0   opi=Reserved           carrier=WL_HOST_WAKE
DIFF A 21  radxa=PWM15_M1               GPIO4_B3   opi=GPIO4_A4           carrier=BL_PWM
same A 22  radxa=GND                               opi=GND                carrier=GND
same A 23  radxa=GND                               opi=GND                carrier=GND
DIFF A 24  radxa=PCIE20X1_2_WAKEN_M0    GPIO3_D0   opi=GPIO1_C0           carrier=PCIE_WAKE_N_3V3
DIFF A 25  radxa=I2C4_SDA_M3_WIFI       GPIO1_A2   opi=GPIO1_B0           carrier=BT_UART_RTS_N
DIFF A 27  radxa=WIFI_REG_ON_E          GPIO1_A1   opi=GPIO1_B1           carrier=BT_UART_TX
DIFF A 28  radxa=SPIO_MOSI_M1           GPIO4_A1   opi=GPIO1_A2           carrier=DIG_INT_N
DIFF A 29  radxa=GSENSOR_INT            GPIO1_A4   opi=GPIO1_B2           carrier=WL_REG_ON
DIFF A 30  radxa=SPIO_CLK_M1            GPIO4_A2   opi=GPIO1_A3           carrier=DIG_RST_N
same A 32  radxa=GND                               opi=GND                carrier=GND
same A 33  radxa=GND                               opi=GND                carrier=GND
DIFF A 34  radxa=I2S0_SDO0              GPIO1_C7   opi=GPIO1_A4           carrier=I2S0_SDO
same A 35  radxa=I2C8_SCL_M2_CAM        GPIO1_D6   opi=GPIO1_D6           carrier=I2C_CAMA_SCL
same A 36  radxa=I2C8_SDA_M2_CAM        GPIO1_D7   opi=GPIO1_D7           carrier=I2C_CAMA_SDA
DIFF A 38  radxa=MIPI_CAM2_RST_L        GPIO1_B3   opi=GPIO1_A5           carrier=CAMA_RST_N
DIFF A 39  radxa=TP_RST_L               GPIO1_B4   opi=GPIO1_B5           carrier=BT_WAKE
DIFF A 40  radxa=GPIO1_B1               GPIO1_B1   opi=GPIO1_A6           carrier=BT_REG_ON
DIFF A 41  radxa=LCD_RESET_L            GPIO1_B0   opi=GPIO1_B6           carrier=LCD_RESET_N
same A 42  radxa=GND                               opi=GND                carrier=GND
same A 43  radxa=GND                               opi=GND                carrier=GND
DIFF A 44  radxa=GPIO1_B2_CAM1          GPIO1_B2   opi=GPIO1_A7           carrier=CAMB_IO0
DIFF A 45  radxa=GPIO1_A6_CAM1          GPIO1_A6   opi=GPIO1_B7           carrier=CAMB_IO1
DIFF A 46  radxa=I2S0_SCLK_TX           GPIO1_C3   opi=GPIO1_C4           carrier=I2S0_BCLK
DIFF A 47  radxa=MIPI_CAM2_PDN_L        GPIO1_A7   opi=GPIO0_C2           carrier=CAMA_PDN
DIFF A 48  radxa=I2S0_LRCK_TX           GPIO1_C5   opi=GPIO1_C6           carrier=I2S0_LRCK
DIFF A 49  radxa=I2C4_SCL_M3_WIFI       GPIO1_A3   opi=GPIO1_D5           carrier=BT_UART_CTS_N
DIFF A 51  radxa=UART2_RX_M0            GPIO0_B6   opi=UART2_RX           carrier=DBG_UART_RX
same A 52  radxa=GND                               opi=GND                carrier=GND
same A 53  radxa=GND                               opi=GND                carrier=GND
DIFF A 55  radxa=UART2_TX_M0            GPIO0_B5   opi=UART2_TX           carrier=DBG_UART_TX
DIFF A 56  radxa=GPIO0_C7               GPIO0_C7   opi=GPIO1_D2           carrier=LTE_PWR_EN
same A 57  radxa=SDMMC_CLK              GPIO4_D5   opi=SDMMC_CLK          carrier=SD_CLK_SOC
DIFF A 58  radxa=GPIO0_D0               GPIO0_D0   opi=GPIO1_D3           carrier=LTE_FCPO_N
same A 59  radxa=GND                               opi=GND                carrier=GND
same A 60  radxa=GND                               opi=GND                carrier=GND
same A 61  radxa=SDMMC_D3               GPIO4_D3   opi=SDMMC_D3           carrier=SD_D3
same A 62  radxa=SDMMC_CMD              GPIO4_D4   opi=SDMMC_CMD          carrier=SD_CMD
??   A 63  radxa=SDMMC_D0               GPIO4_D0   opi=None               carrier=SD_D0
same A 65  radxa=GND                               opi=GND                carrier=GND
same A 66  radxa=GND                               opi=GND                carrier=GND
same A 67  radxa=SDMMC_D1               GPIO4_D1   opi=SDMMC_D1           carrier=SD_D1
??   A 69  radxa=SDMMC_D2               GPIO4_D2   opi=None               carrier=SD_D2
same A 71  radxa=GND                               opi=GND                carrier=GND
DIFF A 73  radxa=VCCIO_FLASH                       opi=Reserved           carrier=VCC_1V8_S3
same A 74  radxa=GND                               opi=GND                carrier=GND
DIFF A 75  radxa=SD_PWR_ON              GPIO3_C6   opi=SDMMC_PWREN        carrier=SD_PWR_ON
DIFF A 77  radxa=VCC_SYSIN                         opi=VBUS               carrier=CM5_VIN
DIFF A 79  radxa=VCC_SYSIN                         opi=VBUS               carrier=CM5_VIN
DIFF A 80  radxa=I2C7_SCL_M2            GPIO3_D2   opi=I2C6_SCL_M3        carrier=I2C_CAMB_SCL
DIFF A 81  radxa=VCC_SYSIN                         opi=VBUS               carrier=CM5_VIN
DIFF A 82  radxa=I2C7_SDA_M2            GPIO3_D3   opi=I2C6_SDA_M3        carrier=I2C_CAMB_SDA
DIFF A 83  radxa=VCC_SYSIN                         opi=VBUS               carrier=CM5_VIN
same A 84  radxa=VCC_3V3_S3                        opi=VCC_3V3_S3         carrier=VCC_3V3_S3
DIFF A 85  radxa=VCC_SYSIN                         opi=VBUS               carrier=CM5_VIN
same A 86  radxa=VCC_3V3_S3                        opi=VCC_3V3_S3         carrier=VCC_3V3_S3
DIFF A 87  radxa=VCC_SYSIN                         opi=VBUS               carrier=CM5_VIN
DIFF A 88  radxa=VCC_1V8_S0                        opi=VCC_1V8_S3         carrier=VCC_1V8_S0
??   A 89  radxa=PWM4_M0                GPIO0_C5   opi=None               carrier=RTC_INT_N
??   A 90  radxa=VCC_1V8_S0                        opi=None               carrier=VCC_1V8_S0
??   A 91  radxa=HOST_WAKE_BT_H         GPIO0_C6   opi=None               carrier=LTE_WAKE_N
??   A 92  radxa=RESET_L                           opi=None               carrier=BTN_RESET_N
DIFF A 93  radxa=SARADC_VIN0_BOOT                  opi=SARADC_IN0         carrier=BTN_MASKROM
DIFF A 95  radxa=WIFI_LED               GPIO3_C5   opi=GPIO4_B6           carrier=LED_STATUS
DIFF A 97  radxa=USB_HOST_PWREN_H       GPIO1_A0   opi=GPIO4_A7           carrier=BT_UART_RX
same A 98  radxa=GND                               opi=GND                carrier=GND
same A 99  radxa=PWRON_L                           opi=PWRON_L            carrier=BTN_PWRON_N
??   B102  radxa=PCIE20X1_2_CLKREQN_M0  GPIO3_C7   opi=None               carrier=PCIE_CLKREQ_N_3V3
??   B103  radxa=TYPEC0_OTG_DM                     opi=None               carrier=USB_OTG_DN
??   B105  radxa=TYPEC0_OTG_DP                     opi=None               carrier=USB_OTG_DP
??   B107  radxa=GND                               opi=None               carrier=GND
??   B108  radxa=GND                               opi=None               carrier=GND
??   B109  radxa=PCIE20X1_2_PERSTN_M0   GPIO3_D1   opi=None               carrier=PCIE_PERST_N_3V3
??   B110  radxa=PCIE20_0_REFCLKP                  opi=None               carrier=PCIE_REFCLK_P
??   B112  radxa=PCIE20_0_REFCLKN                  opi=None               carrier=PCIE_REFCLK_N
??   B113  radxa=GND                               opi=None               carrier=GND
??   B114  radxa=GND                               opi=None               carrier=GND
??   B115  radxa=MIPI_DPHY0_RX_D0N                 opi=None               carrier=CSIA_D0_N
??   B116  radxa=PCIE20_0_RXP                      opi=None               carrier=PCIE_RX_P
??   B117  radxa=MIPI_DPHY0_RX_D0P                 opi=None               carrier=CSIA_D0_P
??   B118  radxa=PCIE20_0_RXN                      opi=None               carrier=PCIE_RX_N
??   B119  radxa=GND                               opi=None               carrier=GND
??   B120  radxa=GND                               opi=None               carrier=GND
??   B121  radxa=MIPI_DPHY0_RX_D1N                 opi=None               carrier=CSIA_D1_N
??   B122  radxa=PCIE20_0_TXP                      opi=None               carrier=PCIE_TX_P
??   B123  radxa=MIPI_DPHY0_RX_D1P                 opi=None               carrier=CSIA_D1_P
??   B124  radxa=PCIE20_0_TXN                      opi=None               carrier=PCIE_TX_N
??   B125  radxa=GND                               opi=None               carrier=GND
??   B126  radxa=GND                               opi=None               carrier=GND
??   B127  radxa=MIPI_DPHY0_RX_CLKN                opi=None               carrier=CSIA_CLK_N
??   B128  radxa=MIPI_CSI0_RX_D0N                  opi=None               carrier=CSIB_D0_N
??   B129  radxa=MIPI_DPHY0_RX_CLKP                opi=None               carrier=CSIA_CLK_P
??   B130  radxa=MIPI_CSI0_RX_D0P                  opi=None               carrier=CSIB_D0_P
??   B131  radxa=GND                               opi=None               carrier=GND
??   B132  radxa=GND                               opi=None               carrier=GND
??   B133  radxa=MIPI_DPHY0_RX_D2N                 opi=None               carrier=CSIA_D2_N
??   B134  radxa=MIPI_CSI0_RX_D1N                  opi=None               carrier=CSIB_D1_N
??   B135  radxa=MIPI_DPHY0_RX_D2P                 opi=None               carrier=CSIA_D2_P
??   B136  radxa=MIPI_CSI0_RX_D1P                  opi=None               carrier=CSIB_D1_P
??   B137  radxa=GND                               opi=None               carrier=GND
??   B138  radxa=GND                               opi=None               carrier=GND
??   B139  radxa=MIPI_DPHY0_RX_D3N                 opi=None               carrier=CSIA_D3_N
??   B140  radxa=MIPI_CSI0_RX_CLK0N                opi=None               carrier=CSIB_CLK_N
??   B141  radxa=MIPI_DPHY0_RX_D3P                 opi=None               carrier=CSIA_D3_P
??   B142  radxa=MIPI_CSI0_RX_CLK0P                opi=None               carrier=CSIB_CLK_P
??   B144  radxa=GND                               opi=None               carrier=GND
??   B150  radxa=GND                               opi=None               carrier=GND
??   B155  radxa=GND                               opi=None               carrier=GND
??   B156  radxa=GND                               opi=None               carrier=GND
??   B161  radxa=GND                               opi=None               carrier=GND
??   B162  radxa=GND                               opi=None               carrier=GND
??   B167  radxa=GND                               opi=None               carrier=GND
??   B168  radxa=GND                               opi=None               carrier=GND
??   B173  radxa=GND                               opi=None               carrier=GND
??   B174  radxa=GND                               opi=None               carrier=GND
??   B175  radxa=MIPI_DPHY1_TX_D0N                 opi=None               carrier=DSI_D0_N
??   B177  radxa=MIPI_DPHY1_TX_D0P                 opi=None               carrier=DSI_D0_P
??   B179  radxa=GND                               opi=None               carrier=GND
??   B180  radxa=GND                               opi=None               carrier=GND
??   B181  radxa=MIPI_DPHY1_TX_D1N                 opi=None               carrier=DSI_D1_N
??   B183  radxa=MIPI_DPHY1_TX_D1P                 opi=None               carrier=DSI_D1_P
??   B185  radxa=GND                               opi=None               carrier=GND
??   B186  radxa=GND                               opi=None               carrier=GND
??   B187  radxa=MIPI_DPHY1_TX_CLKN                opi=None               carrier=DSI_CLK_N
??   B189  radxa=MIPI_DPHY1_TX_CLKP                opi=None               carrier=DSI_CLK_P
??   B191  radxa=GND                               opi=None               carrier=GND
??   B192  radxa=GND                               opi=None               carrier=GND
??   B193  radxa=MIPI_DPHY1_TX_D2N                 opi=None               carrier=DSI_D2_N
??   B194  radxa=MIPI_DPHY1_TX_D3N                 opi=None               carrier=DSI_D3_N
??   B195  radxa=MIPI_DPHY1_TX_D2P                 opi=None               carrier=DSI_D2_P
??   B196  radxa=MIPI_DPHY1_TX_D3P                 opi=None               carrier=DSI_D3_P
??   B197  radxa=GND                               opi=None               carrier=GND
??   B198  radxa=GND                               opi=None               carrier=GND
DIFF C  1  radxa=GND                               opi=USB20_HOST1_DP     carrier=GND
DIFF C  2  radxa=GND                               opi=TYPEC0_SSTX2P      carrier=GND
DIFF C  4  radxa=GPIO3_C0               GPIO3_C0   opi=TYPEC0_SSTX2N      carrier=I2C_SYS_SDA
DIFF C  6  radxa=GPIO3_B7               GPIO3_B7   opi=GND                carrier=I2C_SYS_SCL
DIFF C  7  radxa=GND                               opi=TYPEC0_SBU1        carrier=GND
DIFF C  8  radxa=TYPEC0_SBU1_DC         GPIO3_C4   opi=TYPEC0_SSRX2P      carrier=LTE_RESET_CTL
DIFF C 10  radxa=GPIO1_B6_CAM2_CLK      GPIO1_B6   opi=TYPEC0_SSRX2N      carrier=CAMA_MCLK
DIFF C 12  radxa=GPIO1_B7               GPIO1_B7   opi=GND                carrier=CAMB_MCLK
??   C 13  radxa=GND                               opi=None               carrier=GND
??   C 14  radxa=TYPEC0_SBU2_DC         GPIO3_D4   opi=None               carrier=LTE_WDIS_CTL
DIFF C 18  radxa=PWM11_M3               GPIO3_D5   opi=GND                carrier=CHG_PROCHOT_N
DIFF C 19  radxa=GND                               opi=TYPEC0_SSRX1P      carrier=GND
DIFF C 22  radxa=GND                               opi=GPIO3_C7           carrier=GND
??   C 25  radxa=GND                               opi=None               carrier=GND
??   C 26  radxa=SARADC_VIN1_KEY/RECOVE            opi=None               carrier=BTN_ADC_KEYS
??   C 28  radxa=SARADC_VIN2_DC                    opi=None               carrier=VSYS_SENSE
DIFF C 31  radxa=GND                               opi=MIPI_DPHY1_RX_D1P  carrier=GND
same C 32  radxa=GND                               opi=GND                carrier=GND
??   C 34  radxa=LCD_PWREN_H            GPIO4_A3   opi=None               carrier=LCD_PWREN
??   C 37  radxa=GND                               opi=None               carrier=GND
??   C 38  radxa=GPIO4_A4               GPIO4_A4   opi=None               carrier=TP_INT
??   C 40  radxa=GPIO4_A5               GPIO4_A5   opi=None               carrier=TP_RST_N
??   C 42  radxa=GND                               opi=None               carrier=GND
??   C 43  radxa=GND                               opi=None               carrier=GND
??   C 45  radxa=USB20_HOST1_DP                    opi=None               carrier=USB_LTE_DP
DIFF C 47  radxa=USB20_HOST1_DM                    opi=_M4/PWM10_M0/SPI4_ carrier=USB_LTE_DN
DIFF C 48  radxa=GND                               opi=_B2_d              carrier=GND
??   C 49  radxa=GND                               opi=None               carrier=GND
DIFF C 51  radxa=USB30_2_SSTXP                     opi=M12_M0/GPIO3_B5_u  carrier=USB3_LTE_TX_P
??   C 53  radxa=USB30_2_SSTXN                     opi=None               carrier=USB3_LTE_TX_N
??   C 55  radxa=GND                               opi=None               carrier=GND
??   C 56  radxa=GND                               opi=None               carrier=GND
DIFF C 57  radxa=USB30_2_SSRXP                     opi=M1/PWM13_M0/GPIO3_ carrier=USB3_LTE_RX_P
DIFF C 59  radxa=USB30_2_SSRXN                     opi=WM2_M1/GPIO3_B1_d  carrier=USB3_LTE_RX_N
DIFF C 61  radxa=GND                               opi=M2/UART8_TX_M1/SPI carrier=GND
DIFF C 62  radxa=GND                               opi=TSN_M1/SPI4_CS1_M1 carrier=GND
??   C 63  radxa=USB20_HOST0_DP                    opi=None               carrier=USB_HUB_UP_DP
DIFF C 65  radxa=USB20_HOST0_DM                    opi=GND                carrier=USB_HUB_UP_DN
??   C 67  radxa=GND                               opi=None               carrier=GND
??   C 68  radxa=GND                               opi=None               carrier=GND
DIFF C 69  radxa=I2C6_SDA_M3            GPIO4_B0   opi=K_M0/GPIO1_C2_d    carrier=I2C_TP_SDA
DIFF C 71  radxa=I2C6_SCL_M3            GPIO4_B1   opi=1.8V               carrier=I2C_TP_SCL
DIFF C 72  radxa=GND                               opi=GPIO3_C0_d         carrier=GND
??   C 73  radxa=GND                               opi=None               carrier=GND
??   C 74  radxa=SDMMC_DET_L            GPIO0_A4   opi=None               carrier=SD_DET_N
DIFF C 75  radxa=GPIO1_C6_S             GPIO1_C6   opi=GND                carrier=PDM_CLK
DIFF C 76  radxa=GND                               opi=PCIE20_0_REFCLKP   carrier=GND
??   C 77  radxa=GPIO1_D5_S             GPIO1_D5   opi=None               carrier=PDM_DATA
??   C 81  radxa=RTC_INT_L                         opi=None               carrier=BT_HOST_WAKE
DIFF C 85  radxa=BT_HOST_WAKE           GPIO4_B5   opi=GPIO0_D3           carrier=KBD_BOOT_N
DIFF C 87  radxa=GPIO4_A7               GPIO4_A7   opi=GND                carrier=KBD_RESET_N
??   C 89  radxa=GPIO4_A6               GPIO4_A6   opi=None               carrier=HUB_RESET_N
??   C 92  radxa=VCC_3V3_S3                        opi=None               carrier=VCC_3V3_S3
DIFF C 93  radxa=GPIO0_C2               GPIO0_C2   opi=0_TX_M2/GPIO4_A3_d carrier=EN_5V
DIFF C 94  radxa=GPIO0_D3               GPIO0_D3   opi=0/GPIO0_C5_u       carrier=FG_ALRT_N
??   C 95  radxa=TYPEC5V_PWREN_H        GPIO0_D5   opi=None               carrier=KBD_INT_N
??   C 96  radxa=CC_INT0_L              GPIO0_C4   opi=None               carrier=PD_INT_N
??   C 98  radxa=BT_REG_ON_H            GPIO0_D4   opi=None               carrier=AMP_SD_MODE
same C 99  radxa=GND                               opi=GND                carrier=GND
same C100  radxa=GND                               opi=GND                carrier=GND
```
