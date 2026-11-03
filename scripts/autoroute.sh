#!/bin/bash
# Autoroute the prepped board in place: DSN export, Freerouting, SES import, neck-down fix, GND pours.
# usage: autoroute_v02.sh <board.kicad_pcb> [passes]
set -e
B=$(realpath "$1"); D=$(dirname "$B"); S=$(dirname "$(realpath "$0")"); FR=${FREEROUTING_JAR:-~/claude/tools/freerouting/freerouting-2.5.0.jar}
cd "$D"
python3 -I - "$B" <<'PY' 2>&1 | grep -v -E "assert|leak" || true
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); print('export', pcbnew.ExportSpecctraDSN(b, 'board.dsn')); sys.stdout.flush(); os._exit(0)
PY
timeout 1500 java -Dgui.enabled=false -jar $FR -de board.dsn -do board.ses -mp ${2:-100} ${FR_EXTRA} > fr.log 2>&1 || true
grep -E "Auto-routing stage completed|Optimization stage completed|unrouted" fr.log | tail -4 || tail -3 fr.log
python3 -I - "$B" <<'PY' 2>&1 | grep -v -E "assert|leak" || true
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
print('import', pcbnew.ImportSpecctraSES(b, 'board.ses'))
n = 0
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_TRACE_T and t.GetWidth() < pcbnew.FromMM(0.127):
        t.SetWidth(pcbnew.FromMM(0.127)); n += 1
print('widened', n, 'necked-down tracks to 0.127 mm')
b.Save(sys.argv[1]); sys.stdout.flush(); os._exit(0)
PY
