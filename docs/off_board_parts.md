# Off-board parts (not assembled by JLCPCB)

Everything the two boards need that is plugged in, screwed on or hand-fitted. The PCBA BOMs are in the checkpoint folders.

| Item | Part | Connects to | Source / decision |
|---|---|---|---|
| Compute module | **Orange Pi CM5** (RK3588S; the user's 16 GB / 32 GB eMMC unit, V1.1 board; V1.5 has the same connector and hole positions). It has no Wi-Fi / BT: the carrier's AP6275P provides them | J301-J303 = JP1-JP3 (3 x DF40C-100DS) | D85 |
| CM5 screws | 4 x M2.5 (module holes 2.7 mm), into the SMT standoffs H301-H304 (1.5 mm) | Board A | D13, D86 |
| CM5 heat spreader | thermal pad + aluminium plate to the display frame, over the 40 x 55 mm zone on User.2 (module top about 4.6 mm above the board: UNVERIFIED, no Orange Pi 3D model) | CM5 top | brief; D86 |
| LTE modem | Quectel EM060K-GL, M.2 3042 key B | J501 + M2 screw into H501 | checkpoint 1 decision |
| LTE antennas | per Quectel EM060K HD ch. 5, on the module's own antenna connectors | EM060K-GL | to choose with the enclosure |
| Wi-Fi / BT antennas | 2 x dual-band 2.4 / 5 GHz antennas with u.FL (MHF1) plugs | J601 (WL_ANT0), J602 (WL_ANT1) | to choose with the enclosure |
| Battery pack | 1S Li-ion/LiPo 3.7 V, 5000 mAh, about 8 x 65 x 85 mm, PCM >= 12 A, 10 kOhm B3435 NTC | J102 | C2-1 |
| Battery harness | Molex **505570-0901** housing (Micro-Lock Plus 2.00 mm, 9 circuits) + 9 x **505572-1000** crimp terminals (matte tin, 22-26 AWG, 3.0 A; Molex hand tool 2002180800), **24 AWG** (22 at most), <= 80 mm; pins 1-4 BAT+, 5-8 BAT-, 9 NTC | J102 (Molex 505578-0971: "mate with 505570 series", tin) | C2-1, D11, D111 |
| Display | DisplayModule DMKDI0400S0CA (720 x 720), FPC edge toward the device's left side | J701 (30P 0.5 mm) | Q5, C3-2 |
| Touch panel | the panel's capacitive touch (GT911) | J702 (8P 0.5 mm) | Q1 |
| Rear camera | Radxa Camera 13M 214 + Radxa 31p 0.3 mm FPC, opposite-side contacts, 150 mm | J704 (FH35C-31S) | D21 |
| Front camera | Radxa Camera 8M 219 + Radxa 31p 0.3 mm -> 15p 1.0 mm FPC, same side | J705 (FH35C-31S) | D22, D23 |
| Speakers | 2 x 4-8 Ohm micro-speakers with JST SHR-02V-S plugs | J801, J802 (JST SM02B-SRSS-TB) | to choose with the enclosure |
| Keyboard | BlackBerry Q20 keyboard (flex with the BM20B mate) | Board B J201 | brief |
| Board A <-> Board B cable | 12-pin 0.5 mm FFC, type B (contacts on opposite sides), about 50 mm | Board A J1001, Board B J101 | CHECKPOINT3.md §3 |
| Digitizer (later) | EMR digitizer, 12P 0.5 mm FFC | J703 (reserved) | Q1 |
| Board fixing | Board A 4 x M2 (H305-H308); Board B 2 x M2.5 (H101, H102) | enclosure | checkpoint 3 |
