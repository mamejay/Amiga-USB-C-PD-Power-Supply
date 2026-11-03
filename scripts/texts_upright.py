"""Set every board and footprint text to angle 0 (readable with the board's final orientation).
usage: texts_upright.py board.kicad_pcb"""
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); n = 0
for d in b.GetDrawings():
    if isinstance(d, pcbnew.PCB_TEXT):
        d.SetTextAngleDegrees(0); n += 1
for fp in b.GetFootprints():
    for t in [fp.Reference(), fp.Value()] + [g for g in fp.GraphicalItems() if isinstance(g, pcbnew.PCB_TEXT)]:
        t.SetTextAngleDegrees(0); n += 1
b.Save(sys.argv[1]); print('upright:', n); sys.stdout.flush(); os._exit(0)
