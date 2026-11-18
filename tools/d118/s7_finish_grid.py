#!/usr/bin/env python3
"""finish a routed board whose open connections are many: the negotiated grid router first, then rip-up for the rest and gen/route_a.finish (as gen/route_a.route after its first stages). usage: finish_grid.py BOARD"""
import os, sys, pcbnew
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gen'))
sys.path.insert(0, '/home/rakpozareny/Projects/cm5-handheld/gen')
import route_a as A
out = os.path.abspath(sys.argv[1]); iters = 40
log = lambda m: print(m, flush=True)
b = pcbnew.LoadBoard(out)
left, hot, stuck = A.grid_route(b, out, 2 * iters, skip_nets=(), skip_zone_nets=('GND',), log=log)
# no fine_pass: its windows merge into one over most of the board and take up all router copper there (a near
# re-route); the transactional rip-up below touches only what is in each open connection's way
log(f'left open after the grid passes: {len(left)}')
b, left = A.close_out(b, out, left, iters, log)
A.finish(b, out, log)
