"""Delete vias that DRC reports as dangling (connected on one layer only), then refill. usage: drop_dangling_vias.py board drc.rpt"""
import sys, os, re, pcbnew
pts = [(float(x), float(y)) for x, y in re.findall(r'@\(([\d.]+) mm, ([\d.]+) mm\): Via', open(sys.argv[2]).read().split('[via_dangling]', 1)[-1] if '[via_dangling]' in open(sys.argv[2]).read() else '')]
rpt = open(sys.argv[2]).read()
pts = [(float(x), float(y)) for blk in rpt.split('[via_dangling]')[1:] for x, y in re.findall(r'@\(([\d.]+) mm, ([\d.]+) mm\): Via', blk.split('\n[')[0])]
b = pcbnew.LoadBoard(sys.argv[1]); n = 0
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T:
        q = t.GetPosition()
        if any(abs(q.x / 1e6 - x) < 0.01 and abs(q.y / 1e6 - y) < 0.01 for x, y in pts):
            b.RemoveNative(t); n += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1]); print('removed dangling vias:', n); sys.stdout.flush(); os._exit(0)
