#!/bin/bash
# Full board pipeline: schematic -> netlist -> build -> holes -> net classes -> Freerouting (GND not routed)
# -> pours -> GND stitching -> DRC, repeated until DRC reports 0 unconnected pads (Freerouting varies run to run).
set -e
S=$(dirname "$(realpath "$0")"); cd "$S/../hw"; P="Amiga USB-C PD Power Supply"
python3 -I "$S/gen_sch.py" . >/dev/null
kicad-cli sch export netlist -o net.net "$P.kicad_sch" >/dev/null
best=999
for i in $(seq 1 ${1:-6}); do
  python3 -I "$S/build_pcb.py" . 2>&1 | grep -E "^board" || true
  python3 -I "$S/add_holes.py" "$P.kicad_pcb" >/dev/null
  python3 -I "$S/set_netclasses.py" . >/dev/null
  python3 -I "$S/stubs.py" "$P.kicad_pcb" >/dev/null 2>&1
  python3 -I "$S/pre_zones.py" "$P.kicad_pcb" >/dev/null 2>&1
  FR_EXTRA="--router.autorouter.ignore_net_classes=GND" bash "$S/autoroute.sh" "$P.kicad_pcb" ${2:-200} 2>&1 | grep -E "completed|import" | sed 's/.*INFO *\[[^]]*\] //' || true
  cp "$P.kicad_pcb" routed_nopour.kicad_pcb
  python3 -I "$S/pours.py" "$P.kicad_pcb" >/dev/null 2>&1
  python3 -I "$S/stitch_gnd.py" "$P.kicad_pcb" 2>&1 | grep -E "stitch|island" | tr '\n' ' '
  kicad-cli pcb drc --schematic-parity --refill-zones -o drc.rpt "$P.kicad_pcb" >/dev/null
  u=$(grep -oE "Found [0-9]+ unconnected" drc.rpt | grep -oE "[0-9]+")
  echo "run $i: unconnected $u"
  if [ "$u" -lt "$best" ]; then best=$u; cp "$P.kicad_pcb" best.kicad_pcb; cp routed_nopour.kicad_pcb best_nopour.kicad_pcb; fi
  [ "$u" = 0 ] && break
done
cp best.kicad_pcb "$P.kicad_pcb"; cp best_nopour.kicad_pcb routed_nopour.kicad_pcb; echo "kept best: $best unconnected"
python3 -I "$S/post.py" "$P.kicad_pcb" 2>&1 | grep -E "vias" || true
python3 -I "$S/drop_dangling_vias.py" "$P.kicad_pcb" drc.rpt 2>&1 | grep removed || true
kicad-cli pcb drc --schematic-parity --refill-zones -o drc.rpt "$P.kicad_pcb" >/dev/null
grep -E "^\[|Found" drc.rpt | sed 's/:.*//' | sort | uniq -c
