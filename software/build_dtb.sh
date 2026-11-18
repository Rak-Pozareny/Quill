#!/bin/sh
# Compile the board device tree against Orange Pi's 6.1 kernel tree (device-tree folders only), the way the kernel's
# own build does it (C preprocessor, then dtc with symbols for overlays).
# usage: sh software/build_dtb.sh [KERNEL_TREE]
#   KERNEL_TREE defaults to research/dl/linux-orangepi/src (sparse clone of orangepi-xunlong/linux-orangepi,
#   branch orange-pi-6.1-rk35xx: arch/arm64/boot/dts/rockchip, include/dt-bindings, scripts/dtc/include-prefixes)
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
K=${1:-$HERE/../research/dl/linux-orangepi/src}
OUT=$HERE/build
NAME=rk3588s-orangepi-cm5-handheld
mkdir -p "$OUT"
cpp -nostdinc -undef -D__DTS__ -x assembler-with-cpp \
    -I "$HERE/dts" -I "$K/arch/arm64/boot/dts/rockchip" -I "$K/include" -I "$K/scripts/dtc/include-prefixes" \
    "$HERE/dts/$NAME.dts" -o "$OUT/$NAME.dts.pp"
dtc -I dts -O dtb -@ -W no-unit_address_vs_reg -o "$OUT/$NAME.dtb" "$OUT/$NAME.dts.pp" 2> "$OUT/$NAME.dtc.log" || {
    cat "$OUT/$NAME.dtc.log"; exit 1; }
echo "wrote $OUT/$NAME.dtb ($(wc -c < "$OUT/$NAME.dtb") bytes); dtc warnings: $(grep -c Warning "$OUT/$NAME.dtc.log" || true)"
