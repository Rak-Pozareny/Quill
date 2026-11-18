# Linux device tree for the Orange Pi CM5 on Board A

For Orange Pi's own images for the CM5 with the **Linux 6.1** kernel (Debian 12 Bookworm or Ubuntu 22.04 Jammy, Orange
Pi CM5 user manual section 3.1), kernel branch `orange-pi-6.1-rk35xx` of
[orangepi-xunlong/linux-orangepi](https://github.com/orangepi-xunlong/linux-orangepi).

| File | What |
|---|---|
| `dts/rk3588s-orangepi-cm5-handheld.dts` | the board: everything on the carrier |
| `dts/rk3588s-orangepi-cm5-module.dtsi` | the module itself (CPU / GPU / NPU supplies, eMMC, video blocks), copied unchanged from Orange Pi's `rk3588s-orangepi-cm5.dts` |
| `kernel/cm5-handheld.config` | six kernel options Orange Pi's 6.1 config leaves out and this board needs |
| `build_dtb.sh` | compiles the tree against Orange Pi's kernel tree (`build/rk3588s-orangepi-cm5-handheld.dtb`) |
| `check_dtb.py` | checks the compiled tree: no pin claimed twice, every GPIO on the net `docs/opi/opi_cm5_pin_map.csv` gives it, camera links consistent |

## Sources

- **Orange Pi's 6.1 tree** (commit `f6eedab0cbe9`, sparse copy in `research/dl/linux-orangepi/src`):
  - `rk3588s-orangepi-cm5.dts` / `-tablet.dts`: the module part, the Bluetooth / Wi-Fi control pins and the GPIO0_C2 PMIC override.
  - `rk3588s-orangepi-cm5-camera*.dtsi`: the camera chains.
  - `rk3588s-orangepi-5.dtsi`: an AP6275P on the same PCIe controller with the same GPIOs.
  - `rk3588-evb.dtsi`: the DSI panel node.
- **Radxa's overlays for the same cameras** (`research/dl/cameras/overlays/`): sensor addresses, clocks, pin polarities, focus motor values.
- **The drivers in Orange Pi's 6.1 kernel** (`research/dl/linux-orangepi/drivers/`): every property name used is one the driver reads.
- **Orange Pi's kernel config** `linux-rockchip-rk3588-current.config` (orangepi-build) for what is built.

## Build and install

1. **Kernel.** Orange Pi's stock 6.1 kernel lacks six drivers this board uses: the IMX214 rear camera and its DW9714 focus motor, the MAX98357A amplifiers, the PDM microphone codec, the MAX17055 gauge, and software I2C for the front camera. To add them:
   - Build the kernel with [orangepi-build](https://github.com/orangepi-xunlong/orangepi-build) (`./build.sh`, board orangepicm5, kernel "current").
   - Add the lines of `kernel/cm5-handheld.config` to `external/config/kernel/linux-rockchip-rk3588-current.config` (or set them in the kernel configuration menu the build offers).
   - Install the resulting `linux-image` / `linux-dtb` packages.
   - Without them the board still boots; the parts above just have no driver.
2. **Device tree.** On a PC: `sh software/build_dtb.sh` (needs `cpp` and `dtc`, and the kernel tree in `research/dl/linux-orangepi/src`, or pass another tree's path). Or copy the two `.dts*` files into the kernel tree's `arch/arm64/boot/dts/rockchip/` and add the `.dtb` to its Makefile before step 1.
3. **On the board:**
   1. Copy `build/rk3588s-orangepi-cm5-handheld.dtb` to `/boot/dtb/rockchip/`.
   2. In `/boot/orangepiEnv.txt` set `fdtfile=rockchip/rk3588s-orangepi-cm5-handheld.dtb`. Orange Pi's RK3588 boot script loads `/boot/dtb/${fdtfile}` (orangepi-build `boot-rk3588.cmd`).
   3. Reboot.
4. **First boot:** have the 3.3 V USB-serial adapter on the debug pads (1 500 000 baud, as Orange Pi's images). If the new tree does not boot, put back the old `fdtfile` line from another computer.

## What it sets up

| Function | How |
|---|---|
| **Supplies** | module VBUS (fixed), 5 V boost (EN_5V GPIO0_D5, on), AUX 3.3 V (hardware), LTE supply (GPIO0_C4) then the modem's FULL_CARD_POWER_OFF# (GPIO0_C2) as a two-step regulator chain, panel VCI (GPIO4_A7, switched with the panel) |
| **Wi-Fi / Bluetooth** | AP6275P on PCIe (`pcie2x1l2`, combo PHY0, PERST# GPIO3_D1), `wlan-platdata` (REG_ON GPIO0_D0, host wake GPIO0_A0) and `bluetooth-platdata` on UART9_M2 (REG_ON GPIO0_C7, wake GPIO0_C6, host wake GPIO0_C5), sleep clock from the RTC, as Orange Pi 5 |
| **USB** | USB-C on OTG0 as a USB 2.0 device (Maskrom / gadget); HOST0 to the USB2514B hub (USB-A x2, keyboard, digitizer); HOST1 + combo PHY2 in USB 3.0 mode to the LTE modem |
| **Storage** | eMMC (module), microSD with card detect |
| **RTC** | BM8563 on I2C4_M3 with Orange Pi's HYM8563 driver (same PCF8563 register set), alarm on GPIO0_B0 (wake) |
| **Fuel gauge** | MAX17055 on I2C4_M3, 4 mOhm shunt, alert on GPIO3_B2 |
| **Touch** | GT911 on I2C6_M3 (INT GPIO1_B2, RST GPIO1_B3), 720 x 720 |
| **Keyboard** | enumerates as a USB keyboard on hub port 3; its I2C side (0x1F on I2C6) needs an out-of-tree driver and is not described |
| **Buttons** | power through the PMIC (Orange Pi's tree); Vol+ / Vol- / Recovery as ADC keys on SARADC_IN1; modem WAKE# as a wake-up key |
| **Status LED** | GPIO4_A4, heartbeat |
| **Speakers** | sound card "speakers": I2S0 to the two MAX98357A, shutdown on GPIO4_A2 |
| **Microphone** | sound card "microphone": PDM0_M0 |
| **Rear camera** | IMX214 + DW9714 on I2C3_M1, 4 lanes on MIPI_CSI0 (csi2_dphy0) -> CSI host 2 -> CIF 2 -> ISP0 |
| **Front camera** | IMX219 on the bit-banged bus (GPIO1_A0 / A1), 2 lanes on DC-PHY0 -> CSI host 0 -> CIF -> ISP1; PDN (CAMB_IO0, GPIO3_C4) held high and the module's own 24 MHz oscillator, as Radxa's overlay; CAMB_MCLK not driven |
| **Backlight** | PWM13_M1 at 25 kHz |
| **Display** | DSI1, 4 lanes: **written but disabled** (below) |

## Not done / UNVERIFIED

- **Display.** DisplayModule's documents give neither the panel's video timings nor its ST7703 initialisation sequence.
  - The panel node has everything else and is `disabled`, with the timings at 0 and only the two standard DCS commands (sleep out, display on) in the init sequence.
  - With DisplayModule's init code and timings: fill `panel-init-sequence` and `timing0`, then set `&dsi1`, its panel, `&dsi1_in_vp3` and `&route_dsi1` to `"okay"`.
- **Camera tuning.** Rockchip's camera engine needs a tuning file per camera module, named after `rockchip,camera-module-name` / `-lens-name` (`RADXA-CAMERA-13M` / `DEFAULT`, `RADXA-CAMERA-8M` / `default`). Radxa ships them in its images, Orange Pi does not: copy them from Radxa's `camera_engine_rkaiq` package. Raw capture through the CIF works without them.
- **MAX17055 address 0x36:** from the Linux binding example; the datasheet text is silent. Check with `i2cdetect -y 4`.
- **AP6275P firmware:** the Orange Pi 5 supports this module, so its images are expected to carry the firmware (`bcmdhd`, AP6XXX build); check `dmesg` on the first boot.
- **TPS25751:** no driver in this kernel; it runs from its EEPROM.
- **PROCHOT#** (GPIO3_C1) and the PD controller's IRQ (GPIO3_B3) have no consumer.
- **Not used as GPIO lines** by any driver: keyboard INT# / RESET# / BOOT#, digitizer INT / RST, modem RESET / W_DISABLE (2N7002 gates, pulled down), CAM-B CAM_IO1. They stay inputs with the board's pulls and can be driven from user space (`gpioset`).
- **The front camera's I2C is software I2C** (GPIO1_A0 / A1 only offer I2C2, which the module's NPU regulator uses: D104). About 100 kHz, plenty for the sensor's register set-up.
