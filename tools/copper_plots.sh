#!/bin/sh
# Copper plots of a routed board, one PNG per copper layer (with the board outline), for review.
# usage: sh tools/copper_plots.sh BOARD.kicad_pcb OUT_DIR PREFIX [LAYERS]
#   LAYERS defaults to F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu (2-layer boards: pass F.Cu,B.Cu)
set -e
BOARD=$1; OUT=$2; P=$3; LAYERS=${4:-F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu}
mkdir -p "$OUT"
T=$(mktemp -d)
for L in $(echo "$LAYERS" | tr ',' ' '); do
    MIRROR=""
    [ "$L" = "B.Cu" ] && MIRROR="--mirror"          # bottom seen from below, as it is assembled
    kicad-cli pcb export svg --mode-single --layers "$L,Edge.Cuts" --page-size-mode 2 --exclude-drawing-sheet \
        --drill-shape-opt 2 $MIRROR -o "$T/$L.svg" "$BOARD" 2>&1 | grep -v -E "property.h|Debug|Plotted|^Done" || true
    rsvg-convert -w 2400 -b white -o "$OUT/${P}_$(echo "$L" | tr -d '.' | tr 'A-Z' 'a-z').png" "$T/$L.svg"
done
rm -rf "$T"
