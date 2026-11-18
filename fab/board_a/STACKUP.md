# Board A, Orange Pi CM5 carrier: stack-up

6 layers, 1.2 mm, JLCPCB stack-up **JLC06121H-3313A** (impedance control, +-10 %), as entered in the board file (KiCad Board Setup > Physical Stackup).

| Layer | Type | Thickness (mm) | Material | Er |
|---|---|---|---|---|
| F.SilkS | Top Silk Screen |  |  |  |
| F.Paste | Top Solder Paste |  |  |  |
| F.Mask | Top Solder Mask | 0.01 |  |  |
| F.Cu | copper | 0.035 |  |  |
| dielectric 1 | prepreg | 0.0994 | 3313 | 4.1 |
| In1.Cu | copper | 0.0152 |  |  |
| dielectric 2 | core | 0.1 | NP-155F | 4.36 |
| In2.Cu | copper | 0.0152 |  |  |
| dielectric 3 | prepreg | 0.639 | 3 x 7628 | 4.4 |
| In3.Cu | copper | 0.0152 |  |  |
| dielectric 4 | core | 0.1 | NP-155F | 4.36 |
| In4.Cu | copper | 0.0152 |  |  |
| dielectric 5 | prepreg | 0.0994 | 3313 | 4.1 |
| B.Cu | copper | 0.035 |  |  |
| B.Mask | Bottom Solder Mask | 0.01 |  |  |
| B.Paste | Bottom Solder Paste |  |  |  |
| B.SilkS | Bottom Silk Screen |  |  |  |

Controlled-impedance geometry (JLCPCB impedance calculator for this stack-up, `research/jlc/impedance_selected.json`; layer use and the full table in `docs/checkpoint4/CHECKPOINT4.md` section 2):

| Interface | Target | Outer layer W / S | Inner layer W / S |
|---|---|---|---|
| USB 2.0 / USB 3 | 90 ohm diff | 0.12 / 0.11 mm | 0.10 / 0.11 mm |
| PCIe | 85 ohm diff | 0.13 / 0.10 mm | 0.11 / 0.10 mm |
| MIPI DSI / CSI, PCIe refclk | 100 ohm diff | 0.11 / 0.155 mm | 0.10 / 0.20 mm |
| SD card, Wi-Fi antenna | 50 ohm | 0.155 mm | 0.125 mm |
