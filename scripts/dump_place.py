"""Dump footprint placement (ref, x, y, rot, bottom) + Edge.Cuts + board texts of a board to JSON.
usage: dump_place.py board.kicad_pcb out.json"""
import sys, os, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
fps = {}
for fp in b.GetFootprints():
    p = fp.GetPosition()
    fps[fp.GetReference()] = (p.x / 1e6, p.y / 1e6, fp.GetOrientationDegrees(), fp.IsFlipped())
texts = []
for d in b.GetDrawings():
    if isinstance(d, pcbnew.PCB_TEXT):
        p = d.GetPosition()
        texts.append((d.GetText(), p.x / 1e6, p.y / 1e6, d.GetLayerName(), d.GetTextSize().x / 1e6))
bb = b.GetBoardEdgesBoundingBox()
json.dump({'fps': fps, 'texts': texts, 'edge': [bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6]},
          open(sys.argv[2], 'w'), indent=1)
print('dumped', len(fps), 'footprints,', len(texts), 'texts, edge', [round(v / 1e6, 2) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())])
sys.stdout.flush(); os._exit(0)
