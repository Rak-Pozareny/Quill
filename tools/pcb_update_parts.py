#!/usr/bin/env python3
"""Replace footprints on a routed board with the current library version of the project's cm5h library, keeping each
part's position, orientation, side, reference, value, schematic link, fields and pad nets. Tracks and vias are not
touched; zones are refilled. Run tools/package.py afterwards: its DRC says whether the new pads still fit the copper.

usage: pcb_update_parts.py BOARD.kicad_pcb REF [REF ...]
"""
import os
import sys

import pcbnew


def main():
    path, refs = sys.argv[1], sys.argv[2:]
    b = pcbnew.LoadBoard(path)
    lib = os.path.join(os.path.dirname(os.path.abspath(path)), 'lib', 'cm5h.pretty')
    for ref in refs:
        old = b.FindFootprintByReference(ref)
        if old is None:
            sys.exit(f'{ref} not on the board')
        name = old.GetFPID().GetUniStringLibItemName()
        new = pcbnew.FootprintLoad(lib, name)
        if new is None:
            sys.exit(f'{ref}: {name} not in {lib}')
        new.SetReference(ref)
        new.SetValue(old.GetValue())
        new.SetFPIDAsString(old.GetFPIDAsString())
        new.SetPath(old.GetPath())
        new.SetSheetname(old.GetSheetname())
        new.SetSheetfile(old.GetSheetfile())
        new.SetAttributes(old.GetAttributes())
        new.SetDNP(old.IsDNP())
        for f in old.GetFields():
            n = f.GetName()
            if n in ('Reference', 'Value', 'Footprint', 'Datasheet', 'Description'):
                continue
            new.SetField(n, f.GetText())
            nf = new.GetField(n)
            if nf is not None:
                nf.SetVisible(False)
        nets = {p.GetNumber(): p.GetNetname() for p in old.Pads() if p.GetNumber()}
        have = {p.GetNumber() for p in new.Pads() if p.GetNumber()}
        if set(nets) != have:
            sys.exit(f'{ref}: pad numbers differ: {sorted(set(nets) ^ have)}')
        for p in new.Pads():
            if p.GetNumber():
                p.SetNet(b.FindNet(nets[p.GetNumber()]))
        pos, ori, flipped = old.GetPosition(), old.GetOrientationDegrees(), old.IsFlipped()
        b.Remove(old)
        b.Add(new)
        if flipped:
            new.Flip(new.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        new.SetPosition(pos)
        new.SetOrientationDegrees(ori)
        print(f'{ref}: {name} updated at ({pcbnew.ToMM(pos.x)}, {pcbnew.ToMM(pos.y)}), {ori} degrees')
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(path, b)
    print(f'saved {path}')


if __name__ == '__main__':
    main()
