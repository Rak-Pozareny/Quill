#!/bin/sh
# 3D renders of both boards (kicad-cli pcb render) -> <out_dir>/board_{a,b}_{top,bottom,front,left,iso,iso_bottom}.png
# usage: sh tools/renders.sh docs/checkpoint3/img
set -e
D=${1:-docs/checkpoint3/img}
mkdir -p "$D"
for b in "a:hw/board_a/cm5_carrier.kicad_pcb" "b:hw/board_b/q20_keyboard.kicad_pcb"; do
    n=${b%%:*}; f=${b#*:}
    for side in top bottom; do
        kicad-cli pcb render -o "$D/board_${n}_$side.png" --side $side -w 1800 -h 1200 --background opaque \
            --quality high --zoom 1.0 "$f" 2>&1 | grep -v property.h || true
    done
    for side in front left; do
        kicad-cli pcb render -o "$D/board_${n}_$side.png" --side $side -w 2000 -h 700 --background opaque \
            --quality high --zoom 2.6 "$f" 2>&1 | grep -v property.h || true
    done
    kicad-cli pcb render -o "$D/board_${n}_iso.png" --rotate '-45,0,-30' -w 1800 -h 1200 --background opaque \
        --quality high --zoom 0.9 "$f" 2>&1 | grep -v property.h || true
    kicad-cli pcb render -o "$D/board_${n}_iso_bottom.png" --side bottom --rotate '45,0,30' -w 1800 -h 1200 \
        --background opaque --quality high --zoom 0.9 "$f" 2>&1 | grep -v property.h || true
done
