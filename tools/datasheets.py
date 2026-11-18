#!/usr/bin/env python3
"""Collect the documents the boards were designed from into datasheets/ (tracked in git), and write its README.

    python3 -I tools/datasheets.py

research/dl/ keeps the raw downloads (not in git: large, and code clones). This copies the ones the design rests on
under readable names, writes datasheets/README.md (file, part, references, LCSC code, origin), and checks both BOMs:
every part that is not a plain resistor / capacitor must have a datasheet here, or it is listed as missing.
Re-run after a BOM change or after adding an entry below.
"""
import csv
import filecmp
import os
import shutil
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SRC = os.path.join(ROOT, 'research', 'dl')
OUT = os.path.join(ROOT, 'datasheets')

# (folder, file name, source under research/dl, LCSC codes, part / note, origin)
J, M, U = 'JLCPCB / LCSC', 'manufacturer', 'supplied by you'
DOCS = [
    # ---- Board A: carrier
    ('board_a', 'TPS25751.pdf', 'ds/tps25751.pdf', 'C30169739', 'TPS25751DREFR USB-C PD controller', M),
    ('board_a', 'M24512-RMN6TP.pdf', 'jlc/C79991_M24512-RMN6TP.pdf', 'C79991', 'M24512 EEPROM (TPS25751 configuration)', J),
    ('board_a', 'BQ25713.pdf', 'ds/bq25713.pdf', 'C2878935', 'BQ25713 buck-boost charger', M),
    ('board_a', 'MAX17055.pdf', 'ds/MAX17055.pdf', 'C2976422', 'MAX17055 fuel gauge', M),
    ('board_a', 'MAX17055_package_21-100013.pdf', 'maxim/21-100013.pdf', '', 'MAX17055 TDFN-10 package outline, rev C', U),
    ('board_a', 'MAX17055_land_pattern_90-100007.pdf', 'maxim/90-100007.pdf', '', 'MAX17055 TDFN-10 land pattern, rev B', U),
    ('board_a', 'TLV7042.pdf', 'jlc/C2760466_TLV7042DGKR.pdf', 'C2760466', 'TLV7042 dual comparator', J),
    ('board_a', 'XC6206.pdf', 'jlc/C5446_XC6206P332MR-G.pdf', 'C5446', 'XC6206 3.3 V LDO', J),
    ('board_a', 'TPS61088.pdf', 'ds/tps61088.pdf', 'C87357', 'TPS61088 boost', M),
    ('board_a', 'TPS61089.pdf', 'ds2/tps61089.pdf', 'C165129', 'TPS61089 boost', M),
    ('board_a', 'TPS63020.pdf', 'ds/tps63020.pdf', 'C15483', 'TPS63020 buck-boost', M),
    ('board_a', 'BM8563.pdf', 'jlc/C269877_BM8563ESA.pdf', 'C269877', 'BM8563 RTC', J),
    ('board_a', 'TXS0104E.pdf', 'ds2/txs0104e.pdf', 'C44955', 'TXS0104E level shifter', M),
    ('board_a', 'USB2514B.pdf', 'ds/usb2514b.pdf', 'C16251', 'USB2514B USB 2.0 hub', M),
    ('board_a', 'TPS2553.pdf', 'ds2/tps2553.pdf', 'C55266', 'TPS2553 current-limited switch', M),
    ('board_a', 'AP6275P.pdf', 'ds/ap6275p.pdf', 'C2984107', 'AMPAK AP6275P Wi-Fi 6 / BT module', M),
    ('board_a', 'TPS22919.pdf', 'ds2/tps22919.pdf', 'C2149796', 'TPS22919 load switch', M),
    ('board_a', 'TPS61169.pdf', 'ds/tps61169.pdf', 'C71045', 'TPS61169 backlight boost', M),
    ('board_a', 'MAX98357A.pdf', 'ds/MAX98357A-MAX98357B.pdf', 'C910544', 'MAX98357A I2S amplifier', M),
    ('board_a', 'SPH0641LU4H-1.pdf', 'jlc/C2879853_SPH0641LU4H-1.pdf', 'C2879853', 'SPH0641LU4H-1 PDM microphone', J),
    ('board_a', 'TVS2200.pdf', 'ds2/tvs2200.pdf', '', 'TVS2200 (TI original)', M),
    ('board_a', 'ESTVS2200DRVR.pdf', 'jlc/C42400188_ESTVS2200DRVR.pdf', 'C42400188', 'ESTVS2200DRVR, the TVS2200 part JLCPCB places', J),
    ('board_a', 'TPD4E05U06.pdf', 'ds2/tpd4e05u06.pdf', 'C138714', 'TPD4E05U06 ESD array', M),
    ('board_a', 'KT-0603R.pdf', 'jlc_2026-11-18/C2286_KT-0603R.pdf', 'C2286', 'red LED 0603', J),
    ('board_a', 'SMF5.0A.pdf', 'jlc_2026-11-18/C193402_SMF5.0A.pdf', 'C193402', 'SMF5.0A TVS', J),
    ('board_a', 'B5819W.pdf', 'jlc_2026-11-18/C64885_B5819W.pdf', 'C64885', 'B5819W Schottky', J),
    ('board_a', 'BLM18PG121SN1D.pdf', 'jlc_2026-11-18/C14709_BLM18PG121SN1D.pdf', 'C14709', 'ferrite bead 120R', J),
    ('board_a', 'BLM15AG121SN1D.pdf', 'jlc_2026-11-18/C85812_BLM15AG121SN1D.pdf', 'C85812', 'ferrite bead 120R 0402', J),
    ('board_a', 'CSD17577Q3A.pdf', 'ds2/csd17577q3a.pdf', 'C201632', 'CSD17577Q3A N-MOSFET', M),
    ('board_a', 'CSD25404Q3.pdf', 'ds2/csd25404q3.pdf', 'C2865523', 'CSD25404Q3 P-MOSFET (BATFET)', M),
    ('board_a', '2N7002.pdf', 'jlc_2026-11-18/C8545_2N7002.pdf', 'C8545', '2N7002 N-MOSFET', J),
    ('board_a', 'AO3401A.pdf', 'jlc_2026-11-18/C15127_AO3401A.pdf', 'C15127', 'AO3401A P-MOSFET', J),
    ('board_a', 'SRP7028A-2R2M.pdf', 'jlc/C1329579_SRP7028A-2R2M.pdf', 'C1329579', 'inductor 2.2 uH', J),
    ('board_a', 'WPN4020H1R5MT.pdf', 'jlc/C98360_WPN4020H1R5MT.pdf', 'C98360', 'inductor 1.5 uH', J),
    ('board_a', 'WPN252012H2R2MTY01.pdf', 'jlc_2026-11-18/C279858_WPN252012H2R2MTY01.pdf', 'C279858', 'inductor 2.2 uH (Wi-Fi module)', J),
    ('board_a', 'SWPA3015S4R7MT.pdf', 'jlc/C19398_SWPA3015S4R7MT.pdf', 'C19398', 'inductor 4.7 uH (backlight)', J),
    ('board_a', 'DLW21SN900SQ2L.pdf', 'jlc/C97856_DLW21SN900SQ2L.pdf', 'C97856', 'common-mode choke', J),
    ('board_a', '6TPE220MI.pdf', 'jlc/C129173_6TPE220MI.pdf', 'C129173', 'polymer capacitor 220 uF 6.3 V', J),
    ('board_a', 'Q13FC13500002.pdf', 'jlc_2026-11-18/C48615_Q13FC13500002.pdf', 'C48615', 'crystal 32.768 kHz', J),
    ('board_a', 'X322524MOB4SI.pdf', 'jlc/C70590_X322524MOB4SI.pdf', 'C70590', 'crystal 24 MHz', J),
    ('board_a', 'E3SB37E0X0004E.pdf', 'jlc_2026-11-18/C2687892_E3SB37E0X0004E.pdf', 'C2687892', 'crystal 37.4 MHz', J),
    ('board_a', 'TYPE-C-31-M-12.pdf', 'jlc/C165948_TYPE-C-31-M-12.pdf', 'C165948', 'USB-C receptacle', J),
    ('board_a', 'Molex_505578-0971.pdf', 'lcsc/C17389413_5055780971.pdf', 'C17389413', 'battery connector', J),
    ('board_a', 'Hirose_DF40.pdf', 'ds/df40.pdf', 'C597931', 'DF40C-100DS-0.4V(51) CM5 connectors', M),
    ('board_a', 'HYCW236-USBA04-289B.pdf', 'jlc/C3034183_HYCW236-USBA04-289B.pdf', 'C3034183', 'USB-A receptacle', J),
    ('board_a', 'HYCW11B-05NGFF-320B.pdf', 'jlc/C41430834_HYCW11B-05NGFF-320B.pdf', 'C41430834', 'M.2 Key-B socket', J),
    ('board_a', 'SIM8066-6-1-14-01-A.pdf', 'jlc/C3032925_SIM8066-6-1-14-01-A.pdf', 'C3032925', 'nano-SIM holder', J),
    ('board_a', 'U.FL-R-SMT.pdf', 'jlc/C434808_U.FL-R-SMT_10_.pdf', 'C434808', 'U.FL antenna connector', J),
    ('board_a', '0520-HX-30PWB.pdf', 'jlc/C3041205_0520-HX-30PWB.pdf', 'C3041205', 'display FPC 30P', J),
    ('board_a', 'FPC-05F-8PH15.pdf', 'jlc/C2856815_FPC-05F-8PH15.pdf', 'C2856815', 'touch FPC 8P', J),
    ('board_a', 'FC-05A12P11H20.pdf', 'jlc/C23398836_FC-05A12P11H20.pdf', 'C23398836', 'FFC 12P (keyboard, digitizer; Board B too)', J),
    ('board_a', 'FH35C-31S-0.3SHW.pdf', 'jlc/C424662_FH35C-31S-0.3SHW_50_.pdf', 'C424662', 'camera FPC 31P', J),
    ('board_a', 'SM02B-SRSS-TB.pdf', 'jlc/C160402_SM02B-SRSS-TB_LF__SN_.pdf', 'C160402', 'speaker connector', J),
    ('board_a', 'DM3AT-SF-PEJM5.pdf', 'jlc/C114218_DM3AT-SF-PEJM5.pdf', 'C114218', 'microSD socket', J),
    ('board_a', 'SKRTLAE010.pdf', 'jlc/C110293_SKRTLAE010.pdf', 'C110293', 'side buttons (power, volume)', J),
    ('board_a', 'TS-1088C-02026.pdf', 'jlc/C455278_TS-1088C-02026.pdf', 'C455278', 'RESET / MASKROM / RECOVERY buttons', J),
    ('board_a', 'CK_PTS820_substitute_SW304-306.pdf', 'ck_pts820/PTS820.pdf', '', 'C&K PTS820J20MSMTR-LFS, hand-soldered substitute for SW304-306', M),
    ('board_a', 'SMTSOM2.515BTR.pdf', 'jlc_2026-11-18/C5221850_SMTSOM2.515BTR.pdf', 'C5221850', 'M2.5 standoff (CM5)', J),
    ('board_a', 'SMTSO2010CTJ.pdf', 'jlc/C2916319_SMTSO2010CTJ.pdf', 'C2916319', 'M.2 standoff', J),
    # ---- Board B: keyboard
    ('board_b', 'RP2040.pdf', 'jlc_2026-11-18/C2040_RP2040.pdf', 'C2040', 'RP2040 microcontroller', J),
    ('board_b', 'W25Q16JV.pdf', 'jlc_2026-11-18/C131025_W25Q16JVSSIQ.pdf', 'C131025', 'W25Q16JV flash', J),
    ('board_b', 'AP2112K.pdf', 'jlc_2026-11-18/C51118_AP2112K-3.3TRG1.pdf', 'C51118', 'AP2112K-3.3 LDO', J),
    ('board_b', 'ME6212C18M5G.pdf', 'jlc/C236669_ME6212C18M5G.pdf', 'C236669', 'ME6212 1.8 V LDO', J),
    ('board_b', 'ME6212C28M5G.pdf', 'jlc_2026-11-18/C427596_ME6212C28M5G.pdf', 'C427596', 'ME6212 2.8 V LDO', J),
    ('board_b', 'SN74LVC1G07.pdf', 'ds_sn74lvc1g07/sn74lvc1g07.pdf', 'C7829', 'SN74LVC1G07 open-drain buffer', M),
    ('board_b', 'BSS138.pdf', 'jlc_2026-11-18/C40912_BSS138-7-F.pdf', 'C40912', 'BSS138 N-MOSFET', J),
    ('board_b', 'ABM8-272-T3.pdf', 'jlc/C20625731_ABM8-272-T3.pdf', 'C20625731', 'crystal 12 MHz', J),
    ('board_b', 'BM20B-40DS-0.4V.pdf', 'jlc/C424543_BM20B_0.8_-40DS-0.4V_51_.pdf', 'C424543', 'Q20 keyboard connector', J),
    ('board_b', 'FC-05A12P11H20.pdf', 'jlc/C23398836_FC-05A12P11H20.pdf', 'C23398836', 'FFC 12P to the carrier', J),
    # ---- Modules and parts that plug in
    ('modules/orange_pi_cm5', 'pin_definition_v1.1_2025-07.pdf', 'orangepi/opi_cm5_pin_definition_v1.1_2025-07.pdf', '', 'Orange Pi CM5 interface pin definition V1.1', U),
    ('modules/orange_pi_cm5', 'module_v1.1_bottom.dxf', 'orangepi/opi_cm5_v1.1_bot.dxf', '', 'module V1.1 bottom drawing', U),
    ('modules/orange_pi_cm5', 'module_v1.5_bottom.dxf', 'orangepi/opi_cm5_v1.5_bot.dxf', '', 'module V1.5 bottom drawing', U),
    ('modules/orange_pi_cm5', 'module_v1.5_drawing.pdf', 'orangepi/opi_cm5_v1.5_dxf.pdf', '', 'module V1.5 drawing (PDF)', U),
    ('modules/display_DMKDI0400S0CA', 'datasheet.pdf', 'panel/DMKDI0400S0CA_Datasheet.pdf', '', 'DisplayModule 4.0" panel datasheet', M),
    ('modules/display_DMKDI0400S0CA', 'spec_v1.0.0_2025.pdf', 'panel/DMKDI0400S0CA_Spec_V1.0.0_2025.pdf', '', 'panel specification V1.0.0', M),
    ('modules/display_DMKDI0400S0CA', 'drawing_2026-11-10.dwg', 'panel/DMKDI0400S0CA_drawing_2026-11-10.dwg', '', 'CAD drawing (pin 1 direction, tails), D118', 'DisplayModule, email 2026-11-10'),
    ('modules/display_DMKDI0400S0CA', 'drawing_render.png', 'panel/DMKDI0400S0CA_drawing_render.png', '', 'render of the drawing', 'made from the DWG'),
    ('modules/display_DMKDI0400S0CA', 'drawing_tails_front.png', 'panel/DMKDI0400S0CA_drawing_tails_front.png', '', 'tails, front view', 'made from the DWG'),
    ('modules/display_DMKDI0400S0CA', 'drawing_tails_rear.png', 'panel/DMKDI0400S0CA_drawing_tails_rear.png', '', 'tails, rear view', 'made from the DWG'),
    ('modules/display_DMKDI0400S0CA', 'ST7703_init_4lane_V1.1.txt', 'panel/DMKDI0400S0CA_ST7703_init_4lane_V1.1.txt', '', 'ST7703 init sequence, 4 lanes', 'DisplayModule'),
    ('modules/display_DMKDI0400S0CA', 'reply_2026-11-10.md', 'panel/displaymodule_reply_2026-11-10.md', '', 'DisplayModule\'s answers (pinout, voltages, backlight)', 'DisplayModule, email 2026-11-10'),
    ('modules/lte_EM060K', 'EM060K_hardware_design_v1.1.pdf', 'lte/EM060K_HD_V1.1.pdf', '', 'Quectel EM060K hardware design V1.1', M),
    ('modules/camera', 'radxa_camera_13m_214_product_brief.pdf', 'cameras/radxa_camera_13m_214_product_brief.pdf', '', 'Radxa Camera 13M 214', M),
    ('modules/keyboard_bbq20kbd', 'schematics.pdf', 'kbd/bbq20kbd_hw/schematics.pdf', '', 'Solder Party BBQ20KBD schematic (Board B is derived from it)', M),
    ('modules/keyboard_bbq20kbd', 'bbq20_keyboard.kicad_pcb', 'kbd/bbq20kbd_hw/bbq20_keyboard.kicad_pcb', '', 'BBQ20KBD board: Board B outline and positions (gen/pcb_b.py)', M),
    ('modules/keyboard_bbq20kbd', 'bbq20_keyboard_case.step', 'kbd/bbq20kbd_hw/bbq20_keyboard_case.step', '', 'BBQ20KBD case model', M),
    ('modules/keyboard_bbq20kbd', 'bbq20_keyboard_full.step', 'kbd/bbq20kbd_hw/bbq20_keyboard_full.step', '', 'BBQ20KBD with the Q20 keyboard, model', M),
    ('modules/keyboard_bbq20kbd', 'LICENSE.md', 'kbd/bbq20kbd_hw/LICENSE.md', '', 'BBQ20KBD licence (CERN-OHL v1.2)', M),
    # ---- Reference designs and layout guides
    ('reference/orange_pi_cm5_base', 'base_v1.2_schematic.pdf', 'orangepi/opi_cm5_base_v1.2_schematic.pdf', '', 'Orange Pi CM5 base board V1.2 schematic', U),
    ('reference/orange_pi_cm5_base', 'base_v1.2_drawing.pdf', 'orangepi/opi_cm5_base_v1.2_drawing.pdf', '', 'base board V1.2 drawing', U),
    ('reference/orange_pi_cm5_base', 'base_v1.2_top.dxf', 'orangepi/opi_cm5_base_v1.2_top.dxf', '', 'base board V1.2 top DXF (connector positions, gen/footprints.py)', U),
    ('reference/orange_pi_cm5_base', 'tablet_base_v1.1_schematic.pdf', 'orangepi/opi_cm5_base_tablet_v1.1_schematic.pdf', '', 'tablet base board V1.1 schematic', U),
    ('reference/radxa_cm5', 'cm5_v2210_schematic.pdf', 'radxa/radxa_cm5_v2210_schematic.pdf', '', 'Radxa CM5 V2.21 schematic (first design, archive/radxa_cm5_2026-10-22)', M),
    ('reference/radxa_cm5', 'cm5_v2210_pinout.xlsx', 'radxa/radxa_cm5_v2210_pinout.xlsx', '', 'Radxa CM5 pinout', M),
    ('reference/radxa_cm5', 'cm5_v2210_placement_map.pdf', 'radxa/radxa_cm5_v2210_components_placement_map.pdf', '', 'Radxa CM5 placement map', M),
    ('reference/radxa_cm5', 'io_board_v2200_schematic.pdf', 'radxa/radxa_cm5_io_v2200_schematic.pdf', '', 'Radxa CM5 IO board schematic', M),
    ('reference/radxa_cm5', 'io_board_v2200_BOM.xlsx', 'radxa-cm-projects/cm5/radxa-cm5-io-board/radxa_cm5_io_board_v2200_BOM.xlsx', '', 'Radxa CM5 IO board BOM', M),
    ('reference/radxa_cm5', 'rock_5b_v1450_schematic.pdf', 'radxa/rock5b/radxa_rock_5b_v1450_schematic.pdf', '', 'Radxa ROCK 5B schematic', M),
    ('reference/khadas_edge2', 'edge2_schematic_v13.pdf', 'khadas/edge2-sch-v13.pdf', '', 'Khadas Edge2 (RK3588S) schematic', M),
    ('reference/layout', 'raspberry_pi_cm4_datasheet.pdf', 'length_targets/cm4_datasheet.pdf', '', 'CM4 datasheet: high-speed length / skew targets', M),
    ('reference/layout', 'TI_spraar7j_high_speed_layout.pdf', 'length_targets/spraar7j.pdf', '', 'TI SPRAAR7J high-speed interface layout guidelines', M),
    # ---- Compared, not used (the reasons are in docs/DECISIONS.md)
    ('considered', 'BQ25731.pdf', 'ds/bq25731.pdf', '', 'charger', M),
    ('considered', 'BQ25792.pdf', 'ds/bq25792.pdf', '', 'charger', M),
    ('considered', 'TPS25750.pdf', 'ds/tps25750.pdf', '', 'PD controller', M),
    ('considered', 'TPS25751A.pdf', 'ds3/tps25751a.pdf', '', 'PD 3.2 version of U101 (REVIEW.md)', M),
    ('considered', 'TPS55288.pdf', 'ds/tps55288.pdf', '', 'buck-boost', M),
    ('considered', 'MAX77596.pdf', 'jlc/C2072689_MAX77596ETBA_T.pdf', '', 'buck', J),
    ('considered', 'MAX17048-MAX17049.pdf', 'ds/MAX17048-MAX17049.pdf', '', 'fuel gauge', M),
    ('considered', 'MAX17048-MAX17049_rev2016.pdf', 'ds/MAX17048-MAX17049_rev2016.pdf', '', 'fuel gauge, older revision', M),
    ('considered', 'LMV393.pdf', 'ds2/lmv393.pdf', '', 'comparator', M),
    ('considered', 'TPD2E2U06.pdf', 'ds2/tpd2e2u06.pdf', '', 'ESD', M),
    ('considered', 'HT8563.pdf', 'jlc/C2834465_HT8563ARZ.pdf', '', 'RTC', J),
    ('considered', 'Molex_505575.pdf', 'ds/molex_505575.pdf', '', 'battery connector, vertical (D11)', M),
    ('considered', 'Molex_505575-0971.pdf', 'jlc/C17385595_5055750971.pdf', '', 'battery connector, vertical (D11)', J),
    ('considered', 'SPM6550T-2R2M.pdf', 'jlc/C138677_SPM6550T-2R2M.pdf', '', 'inductor', J),
    ('considered', 'SDCW2012-2-900TF.pdf', 'jlc/C54888_SDCW2012-2-900TF.pdf', '', 'common-mode choke', J),
    ('considered', 'Q13FC13500004.pdf', 'jlc/C32346_Q13FC13500004.pdf', '', 'crystal 32.768 kHz', J),
    ('considered', 'X3S037400BA1H-Z.pdf', 'jlc/C254335_X3S037400BA1H-Z.pdf', '', 'crystal 37.4 MHz', J),
    ('considered', 'HYCW10B-05NGFF-180B.pdf', 'jlc/C41430831_HYCW10B-05NGFF-180B.pdf', '', 'M.2 socket', J),
    ('considered', 'HYC63-SIM07-137.pdf', 'jlc/C645507_HYC63-SIM07-137.pdf', '', 'SIM holder', J),
    ('considered', 'SIM8060-6-0-14-00-A.pdf', 'jlc/C6296715_SIM8060-6-0-14-00-A.pdf', '', 'SIM holder', J),
    ('considered', 'NANO_SIM_7P_H1.37.pdf', 'jlc/C7529384_NANO_SIM_7P_H1.37.pdf', '', 'SIM holder', J),
    ('considered', 'USB-A-S-F-B-SM2.pdf', 'jlc/C6906824_USB-A-S-F-B-SM2.pdf', '', 'USB-A receptacle', J),
    ('considered', 'USB-A_C42621.pdf', 'jlc/C42621_AF90Degree_Sinking_Board_Short_Bent_Leg_No_Curled_Edge_Iron_ShellLCPNatural_Color_Short_Terminal.pdf', '', 'USB-A receptacle, sinking', J),
    ('considered', 'USB-ZD-134DIP.pdf', 'jlc/C5273995_USB-ZD-134DIP.pdf', '', 'USB-A receptacle', J),
    ('considered', '05A15L30P.pdf', 'jlc/C22459560_05A15L30P.pdf', '', 'FPC connector', J),
    ('considered', 'FC-10A15P11H20.pdf', 'jlc/C23397372_FC-10A15P11H20.pdf', '', 'FFC connector', J),
    ('considered', '9774010151R.pdf', 'jlc/C25592730_9774010151R.pdf', '', 'standoff', J),
    ('considered', 'SMTSOM215BTR.pdf', 'jlc/C5301777_SMTSOM215BTR.pdf', '', 'standoff', J),
]
GENERIC = ('C_', 'R_')          # plain resistors and capacitors: no datasheet needed
# Kept on this computer only (listed in .gitignore, not published): a vendor's private email and its attachments, and
# documents whose public source is not recorded.
LOCAL_ONLY = {
    ('modules/display_DMKDI0400S0CA', 'spec_v1.0.0_2025.pdf'),
    ('modules/display_DMKDI0400S0CA', 'drawing_2026-11-10.dwg'),
    ('modules/display_DMKDI0400S0CA', 'drawing_render.png'),
    ('modules/display_DMKDI0400S0CA', 'drawing_tails_front.png'),
    ('modules/display_DMKDI0400S0CA', 'drawing_tails_rear.png'),
    ('modules/display_DMKDI0400S0CA', 'ST7703_init_4lane_V1.1.txt'),
    ('modules/display_DMKDI0400S0CA', 'reply_2026-11-10.md'),
}


def main():
    missing_src = [d[2] for d in DOCS if not os.path.isfile(os.path.join(SRC, d[2]))]
    if missing_src:
        sys.exit('not in research/dl: ' + ', '.join(missing_src))
    names = {(d[0], d[1]) for d in DOCS}
    if len(names) != len(DOCS):
        sys.exit('two entries share a folder and file name')
    copied = 0
    for folder, name, src, *_ in DOCS:
        s, t = os.path.join(SRC, src), os.path.join(OUT, folder, name)
        os.makedirs(os.path.dirname(t), exist_ok=True)
        if not (os.path.exists(t) and filecmp.cmp(s, t, shallow=False)):
            shutil.copy2(s, t); copied += 1
    listed = {os.path.join(d[0], d[1]) for d in DOCS} | {'README.md'}
    extra = sorted(os.path.relpath(os.path.join(dp, f), OUT) for dp, _, fs in os.walk(OUT) for f in fs)
    extra = [e for e in extra if e not in listed]

    # BOM coverage
    have = {c for d in DOCS for c in d[3].split(',') if c}
    refs, gaps = {}, []
    for board in ('board_a', 'board_b'):
        for row in csv.DictReader(open(os.path.join(ROOT, 'fab', board, 'BOM.csv'))):
            code = row['LCSC Part #']
            refs.setdefault(code, []).append(row['Designator'].replace(',', ', '))
            if code not in have and not row['Footprint'].startswith(GENERIC):
                gaps.append(f"{board}: {row['Designator']} {row['Comment']} ({code})")

    w = ['# Datasheets and drawings', '',
         'The documents Board A and Board B were designed from, copied from the raw downloads in `research/dl/` '
         '(which is not in git) by `tools/datasheets.py`. Do not edit this file by hand: add an entry to the list in '
         'that script and run `python3 -I tools/datasheets.py`.', '',
         'Plain resistors and capacitors have no datasheet here. Origin "JLCPCB / LCSC" means the copy JLCPCB hosts for '
         'that LCSC part; "manufacturer" means the maker\'s own copy.', '',
         'Files marked *local only* are not published: a supplier\'s private correspondence and its attachments, and '
         'documents whose public source is not recorded. They stay in `research/dl/` on the design computer.', '']
    titles = {'board_a': 'Board A (carrier): parts', 'board_b': 'Board B (keyboard): parts',
              'modules': 'Modules and parts that plug in', 'reference': 'Reference designs and layout guides',
              'considered': 'Compared, not used (reasons in docs/DECISIONS.md)'}
    for top, title in titles.items():
        rows = [d for d in DOCS if d[0].split('/')[0] == top]
        w += [f'## {title}', '', '| File | Part / content | References | LCSC | Origin |', '|---|---|---|---|---|']
        for folder, name, src, codes, note, origin in rows:
            r = '; '.join(x for c in codes.split(',') if c for x in refs.get(c, [])) if top.startswith('board') else ''
            f = f'`{folder}/{name}` (*local only*)' if (folder, name) in LOCAL_ONLY else f'[`{folder}/{name}`]({folder}/{name})'
            w.append(f'| {f} | {note} | {r} | {codes} | {origin} |')
        w.append('')
    w += ['## BOM parts without a datasheet here', '']
    w += [f'- {g}' for g in gaps] or ['None: every part on both BOMs that is not a plain resistor or capacitor has one.']
    w.append('')
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'README.md'), 'w').write('\n'.join(w))
    print(f'{len(DOCS)} documents, {copied} copied; BOM parts without a datasheet: {len(gaps)}')
    for g in gaps: print('  ', g)
    if extra: print('files in datasheets/ that are not listed:', ', '.join(extra))


if __name__ == '__main__':
    main()
