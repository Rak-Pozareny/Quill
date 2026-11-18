# Length-matching targets: sources (fetched 2026-10-20)

Files in `research/dl/length_targets/` are the downloaded originals.

## TI SPRAAR7J, "High-Speed Interface Layout Guidelines" (Nov 2018, revised Feb 2023)
`dl/length_targets/spraar7j.pdf`, from https://www.ti.com/lit/pdf/spraar7 (resolved to spraar7j.pdf).
Appendix A, device layout tables (Table A-2, AM57xx/DRA7xx; the same rows recur for the other device families):
- "Skew within any USB3/SATA/PCIe/HDMI differential pair": max 5 mils (0.127 mm)
- "Skew within any USB2.0 differential pair": max 50 mils (1.27 mm) (also Table A-1, AM335x/AM437x)
- "Skew between all PCIe RX pairs (Total)" / TX: 550 mils
The document lists CSI among its critical signals but gives no MIPI skew figure.

## Raspberry Pi Compute Module 4 datasheet (Release 4, build date 30/06/2026)
`dl/length_targets/cm4_datasheet.pdf`, from
https://pip-assets.raspberrypi.com/categories/634-raspberry-pi-compute-module-4/documents/RP-008168-DS-4-cm4-datasheet.pdf
(a carrier-board design guide for a compute module, the closest published analogue to this board):
- PCIe (2.3): "only the signals within a Pair need to be length matched ideally to better than 0.1mm"
- USB 2.0 (2.4): "The length of the P/N signals should ideally be matched to better than 0.15mm"
- CSI-2 (2.7) and DSI (2.8): "Each signal within a pair should ideally be matched to better than 0.15mm"
- 4.1: "It is recommended that P/N signals within a pair are matched to better than 0.15mm. Often, matching between
  pairs is not so critical"; 4.1.1: "It is recommended that pairs are also matched on the interface board"
  (no figure for MIPI lane-to-lane).

## AMD UG863, Versal Adaptive SoC PCB Design User Guide, rev 1.12 (2026-06-16), "MIPI D-PHY"
https://docs.amd.com/r/en-US/ug863-versal-pcb-design/MIPI-D-PHY (JavaScript page: read with a web reader, no file
saved). Table 1, "MIPI D-PHY PCB Trace and Skew Guidelines":
- intra-pair skew (P/N): +-2 ps
- clock-to-data skew and data-to-data skew: 0.075 UI (Table 2); footnote: skew calculations include the package
  delays
- 100 ohm +-10 % differential, stripline
Table 2, "Skew values per line rate" (0.075 UI): 0.4 Gbps +-187.5 ps; 1.0 Gbps +-75 ps; 1.5 Gbps +-50 ps;
2.5 Gbps +-30 ps; 4.5 Gbps +-16.67 ps.

## Not usable (could not be read)
- Intel Agilex 5 / Agilex 3 PCB design guidelines, "MIPI Interface Layout Design Guidelines"
  (intel.com/content/www/us/en/docs/programmable/821801/... and .../853726/...): HTTP 403 to a download, redirect
  to a 404 page to a web reader. Its data-to-clock figure (+-40 mil, seen only in a search-result summary) is not
  used.
- Cadence blog "MIPI PCB Design Guidelines for High-Speed Interfaces": the page has no article text (landing page).

## Propagation delay used to convert lengths to time
Not taken from a source: t = sqrt(Er) / c. Stripline (L3 / L4) in the 3 x 7628 prepreg, Er 4.4 (JLC06121H-3313A,
`research/jlc/`): sqrt(4.4) / 299.8 mm/ns = 7.0 ps/mm. Outer-layer microstrip is faster (effective Er below 4.1).
