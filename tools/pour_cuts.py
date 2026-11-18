#!/usr/bin/env python3
"""Small pour keep-outs where a filled pour meets copper of its own net through a sliver (D116).

KiCad's filler keeps the zone's minimum width inside a pour, but where the fill reaches a solid-connected via or a
track it can join it, or two of its own lobes, through a neck far narrower than that (0.04-0.11 mm on board A, found
by the Gerber check in D116). The neck carries nothing the rest of the copper does not (every lobe has its own vias);
a keep-out of radius R at the neck removes it, and a pour island left with no connection goes with it (the zones remove
islands). Tracks, vias and pads are not affected.

usage: pour_cuts.py BOARD.kicad_pcb LAYER:X:Y[:R] [...]     (mm, KiCad coordinates; R default 0.15)

The keep-outs are named 'pour cut (D116)'; the ones already on the board are replaced. The board is saved in place;
refill the pours afterwards with tools/refill_pours.py (kicad-cli applies the custom rules).
"""
import math
import sys

import pcbnew

NAME = 'pour cut (D116)'


def main():
    path = sys.argv[1]
    b = pcbnew.LoadBoard(path)
    old = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == NAME]
    for z in old:
        b.Remove(z)
    for spec in sys.argv[2:]:
        f = spec.split(':')
        layer, x, y = b.GetLayerID(f[0].replace('_', '.')), float(f[1]), float(f[2])
        if layer < 0:       # an unknown name ('F' for F_Cu) would be saved as layer "UNDEFINED": a board KiCad won't load
            sys.exit(f'{spec}: unknown layer {f[0]!r} (F_Cu, In1_Cu, ..., B_Cu); board not changed')
        r = float(f[3]) if len(f) > 3 else 0.15
        ko = pcbnew.ZONE(b)
        ko.SetIsRuleArea(True)
        ko.SetDoNotAllowZoneFills(True)
        ko.SetDoNotAllowTracks(False)
        ko.SetDoNotAllowVias(False)
        ko.SetDoNotAllowPads(False)
        ko.SetDoNotAllowFootprints(False)
        ko.SetLayer(layer)
        ko.SetZoneName(NAME)
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for k in range(16):
            a = 2 * math.pi * k / 16
            ch.Append(pcbnew.FromMM(x + r * math.cos(a)), pcbnew.FromMM(y + r * math.sin(a)))
        ch.SetClosed(True)
        ko.Outline().AddOutline(ch)
        b.Add(ko)
        print(f'pour cut on {f[0]} at ({x:.3f}, {y:.3f}), radius {r:.2f} mm')
    pcbnew.SaveBoard(path, b)
    print(f'{len(old)} earlier cuts replaced, {len(sys.argv) - 2} cuts; saved {path}')


if __name__ == '__main__':
    main()
