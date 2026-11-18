# D118 / D119: display connectors mirrored, J702 moved; CSI-A clock fix

**What was used in the end (2026-11-11):** not the local procedure below. It left J701's new GND pads and six signals
open, so Board A was routed again in full with `gen/route_a.py` from the new placement (D118), and, at the user's
request, with the CSI-A layer plan of D119 in `gen/route_pairs.py` / `gen/route_tune.py`. The local procedure is kept
for the record and for the router findings at the end.

The installed board is the fourth full route (2026-11-11), with D120's additions in `gen/` (USB-C D+ / D- as a pair,
J302.20's GND via placed before the pairs, the GND stub's via checked on every layer). One connection the router left
open, KBD_BOOT_N, was then routed on the finished board with `route_one.py` (below), joints closed with
`tools/close_joints.py`, DRC run, the board copied into `hw/board_a`, `tools/refill_pours.py`, `tools/package.py a`.

Scripts used for D119 (on copies of a pair-stage board, `route_a.py --stop-after pairs`):

- `csia_try.py IN OUT NAME[,NAME...]`: the named pairs' copper removed and routed again in that order, with options
  changed per pair from `PAIR_OPTS` (JSON); then the CSI-A lanes matched as `route_a.tune` does, lengths printed.
- `s8_rip_nets.py IN OUT NET[,NET...]`: every track and via of the named nets removed.

Scripts used on the finished routes (D120):

- `route_one.py IN OUT NET REF.PAD REF.PAD [CLR] [MARGIN]`: one open connection as a single 0.1 mm trace, every other
  net at its net class clearance, pours as hulls; `START_VIA=x,y` puts a via at a chosen spot next to / in the start
  pad first. Used for KBD_BOOT_N (`START_VIA=149.8,106.4 ... KBD_BOOT_N J1001.12 J301.40 0.005 6`).
- `reach.py BOARD NET REF.PAD [CLR] [R]`: flood fill from a pad over the four routing layers with vias: which layers
  and how far a trace of that net can get (found J1001.12 boxed in on the top layer).
- `via_search.py BOARD X Y SPAN STEP NET`: spots around (X, Y) where a 0.4 / 0.2 via of NET clears every other net at
  its net class clearance, the via keepouts (footprint rule areas too) and hole-to-hole; nearest first.
- `net_topology.py BOARD NET`: a net's copper as a graph (T joints and via / pad overlaps included): pad-to-pad
  distances, to tell a signal path from its stubs (the USB-C D+ / D- figures in D120). Its loop count is not
  meaningful (each via and pad joins the track ends inside it to each other).
- `gnd_probe.py BOARD REF.PAD ...`: map of where a GND via fits around a pad, as the router sees it.


DisplayModule's CAD drawing (2026-11-10, `research/dl/panel/DMKDI0400S0CA_drawing_2026-11-10.dwg`) puts pin 1 of both
panel tails at the right, glass facing you, tail hanging down. The board had them at the left, and J702 15.5 mm from
J701 where the tails are 20.85 mm apart. The schematic maps the tails mirrored (`gen/board_a_main.py`, pad k = panel
pin 31 - k / 9 - k) and these scripts carried that onto the routed board without a full re-route. Run with KiCad's
system Python (`python3`, pcbnew), on a copy of `hw/board_a` (they save in place).

Order used (2026-11-10), each on the output of the previous:

1. `python3 -I gen/build_a.py`: schematics, ERC, netlist with the mirrored pins.
2. `s1_connectors.py BOARD NETFILE`: J701 / J702 pad nets from the netlist; J702 to (55.0, 43.85), SW304 to
   (57.2, 36.25), TP305 to (54.75, 49.75); the CHG_IN 1.2 mm run re-laid past J702 (below its pad column, then on a
   45-degree line between pad 1 and the lower mounting tab); every DSI, backlight, LCD supply / reset and touch INT /
   RST net ripped except the DSI fan-out at J302; J701's old GND fan-out vias in front of the new lane pads removed;
   old stubs on renamed pads removed; copper that DRC finds too close to the moved / renamed pads or the new CHG_IN
   run removed; then dangling copper.
3. `s2_restore_fanout.py ORIG BOARD`: the DSI fan-out at J302 (west of x 19.6) copied back from the board before
   D118 (the dangling clean-up takes a via with one stub). The Wi-Fi module's bottom breakouts were routed round
   those vias at 0.14-0.18 mm, closer than the pair router would place them again.
4. `s3_clear_zone.py BOARD 50.0 17.0 54.45 26.6 CM5_VIN,VSYS,CHG_IN`: everything but locked power copper cleared in
   front of J701's lane pads (the lanes' landing area; the router puts the rest back).
5. `s4_clear_corridor.py BOARD BOARD 19.6 17.0 50.0 30.0 WIFI_LPO_32K`: unlocked single-ended copper on L3 / L4 along
   the DSI corridor removed (re-routed in step 8). Then step 3 again (`s2_restore_fanout.py`).
6. `DSI_OPTS_ONLY=DSI_D0 DSI_OPTS='{"thru": [false, true], "layers": ["In2", "In3", "F"], "allow_vias": true,
   "layer_cost": {"In2": 1.0, "In3": 1.3, "F": 1.6}}' s5_route_dsi.py IN OUT -1 8000000
   DSI_D3,DSI_D0,DSI_D1,DSI_CLK,DSI_D2`: the five pairs with `gen/route_pairs`, starting from the existing J302
   fan-out vias, with only switch-node pours as obstacles (the finished pours are refilled round new copper). D0 leaves
   J701 on the top layer (bottom parts under its pads). Order D3 first gave the shortest D3. Then remove the dangling
   DSI stubs DRC reports (old D3 pieces west of x 19.6).
7. `s6_tune_dsi.py BOARD`: P / N skew of each pair, then the lanes matched to the group as far as room allows.
8. `python3 gen/route_a.py --out BOARD --finish`: everything still open, the joint / skew clean-up, DRC exclusions.
9. `tools/refill_pours.py`, then install into `hw/board_a` and `tools/package.py a`.

`via_probe.py` and `plot_region.py` are the diagnostics used on the way (where a via fits in front of each lane; a
region of the board on chosen layers with chosen nets highlighted).

Router behaviour found on the way (not changed in `gen/`):
- `proute.Obstacles` with `zones=True` treats every pour outline as solid, so on a finished board (GND pours on both
  outer layers) no via fits anywhere; `s5_route_dsi.py` uses `zones='hull'`.
- `PairRouter.route_on`'s `_straighten` can move a layer change away from the cell the search checked: in one trial
  D0's via pair landed on C302 / C304's GND pads. Check every routed pair with DRC.
