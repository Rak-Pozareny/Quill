# cm5_carrier: impedance control

- Stack-up JLC06121H-3313A (JLCPCB template; 6 layers, 1.2 mm, NP-155F, 1 oz outer / 0.5 oz inner). Impedance tolerance +-10 % (+-5 ohm at 50 ohm and below).
- Widths and gaps are from JLCPCB's impedance calculator for this stack-up (Polar Si9000 models: coated microstrip outside, offset stripline inside, etch factor and mask as the calculator's defaults).
- Outer layers: the copper pour keeps at least 0.30 mm from every controlled trace, so these are plain (non-coplanar) microstrips; the inner signal layers carry no pour beside them.
- Only the traces of the classes below are controlled. Please adjust their width within tolerance if your process needs it; keep the gaps of each pair as drawn, and do not change other traces.
- This file is a drawing: nothing on it is to be made.

## Layer stack and reference planes

| Layer | Gerber | Use | Model | Reference |
|---|---|---|---|---|
| L1 F.Cu | .gtl | signal | coated microstrip | L2 GND plane, 3313 prepreg 0.0994 mm (Er 4.1), solder mask over |
| L2 In1.Cu | .g1 | GND plane |  | reference for L1 and L3 |
| L3 In2.Cu | .g2 | signal | offset stripline | near: L2 GND, core 0.10 mm (Er 4.36); far: L5 GND, 0.754 mm (7628 x3 + L4 + core) |
| L4 In3.Cu | .g3 | signal | offset stripline | near: L5 GND, core 0.10 mm (Er 4.36); far: L2 GND, 0.754 mm |
| L5 In4.Cu | .g4 | GND plane |  | reference for L4 and L6 |
| L6 B.Cu | .gbl | signal | coated microstrip | L5 GND plane, 3313 prepreg 0.0994 mm (Er 4.1), solder mask over |

## Controlled-impedance classes

| Class | Target | L1 / L6 width / gap (mm) | L3 / L4 width / gap (mm) | Calculated | Used for |
|---|---|---|---|---|---|
| MIPI100 | 100 ohm differential | 0.110 / 0.155 | 0.100 / 0.200 | 100.1 / 100.3 ohm | MIPI DSI / CSI lanes, PCIe reference clocks |
| USB90 | 90 ohm differential | 0.120 / 0.110 | 0.100 / 0.110 | 89.6 / 90.1 ohm | USB 2.0 pairs, USB 3.0 to the LTE modem |
| PCIE85 | 85 ohm differential | 0.130 / 0.100 | 0.110 / 0.100 | 84.9 / 85.1 ohm | PCIe 2.0 to the Wi-Fi module |
| SE50 | 50 ohm single-ended | 0.155 (single) | 0.125 (single) | 50.3 / 50.5 ohm | Wi-Fi antenna feeds, microSD clock / command / data |

## Nets per class

- **MIPI100**: CSIA_CLK_N, CSIA_CLK_P, CSIA_D0_N, CSIA_D0_P, CSIA_D1_N, CSIA_D1_P, CSIA_D2_N, CSIA_D2_P, CSIA_D3_N, CSIA_D3_P, CSIB_CLK_N, CSIB_CLK_P, CSIB_D0_N, CSIB_D0_P, CSIB_D1_N, CSIB_D1_P, DSI_CLK_N, DSI_CLK_P, DSI_D0_N, DSI_D0_P, DSI_D1_N, DSI_D1_P, DSI_D2_N, DSI_D2_P, DSI_D3_N, DSI_D3_P, PCIE_REFCLK_N, PCIE_REFCLK_P, WL_REFCLK_N, WL_REFCLK_P
- **USB90**: DIG_DN, DIG_DP, KBD_DN, KBD_DP, PD_BC_DN, PD_BC_DP, USB3_LTE_RX_N, USB3_LTE_RX_P, USB3_LTE_TXC_N, USB3_LTE_TXC_P, USB3_LTE_TX_N, USB3_LTE_TX_P, USBC_DN, USBC_DP, USB_HUB_UP_DN, USB_HUB_UP_DP, USB_LTE_DN, USB_LTE_DP, USB_OTG_DN, USB_OTG_DP, USB_P1_DN, USB_P1_DP, USB_P2_DN, USB_P2_DP
- **PCIE85**: PCIE_RX_N, PCIE_RX_P, PCIE_TX_N, PCIE_TX_P, WL_PCIE_RX_N, WL_PCIE_RX_P, WL_PCIE_TX_N, WL_PCIE_TX_P
- **SE50**: SD_CLK, SD_CLK_SOC, SD_CMD, SD_D0, SD_D1, SD_D2, SD_D3, WL_ANT0, WL_ANT0_M, WL_ANT1, WL_ANT1_M
