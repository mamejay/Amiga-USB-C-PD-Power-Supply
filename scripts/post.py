"""Post-route finishing: extra GND vias around the converters' power-ground pads (both pours must be solid there),
silkscreen labels. Idempotent. usage: post.py board.kicad_pcb"""
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM
def clear_of_others(pt, r=0.65):
    # no copper of another net within r mm of the via centre, on either layer (tracks, vias, pads)
    for t in b.GetTracks():
        if t.GetNetname() != 'GND' and t.HitTest(pt, mm(r)):
            return False
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() != 'GND' and p.HitTest(pt, mm(r)):
                return False
    return True
gnd = b.FindNet('GND')
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
Z = {L: [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.GetLayer() == L][0].GetFilledPolysList(L)
     for L in (pcbnew.F_Cu, pcbnew.B_Cu)}
bb = b.GetBoardEdgesBoundingBox()
HOT = [(bb.GetLeft() / 1e6 + 1, bb.GetTop() / 1e6 + 1, bb.GetRight() / 1e6 - 1, bb.GetBottom() / 1e6 - 1)]   # whole board
vias = [t.GetPosition() for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
holes = [p.GetPosition() for f in b.GetFootprints() for p in f.Pads() if p.HasHole()]
added = 0
for x0, y0, x1, y1 in HOT:
    for ix in range(int(x0 * 10), int(x1 * 10) + 1, 2):
        for iy in range(int(y0 * 10), int(y1 * 10) + 1, 2):
            p = pcbnew.VECTOR2I(ix * 100000, iy * 100000)
            if any((v.x - p.x) ** 2 + (v.y - p.y) ** 2 < mm(3.0) ** 2 for v in vias + holes):
                continue
            if all(Z[L].Contains(pcbnew.VECTOR2I(p.x + dx, p.y + dy)) for L in Z
                   for dx in (-mm(0.55), 0, mm(0.55)) for dy in (-mm(0.55), 0, mm(0.55))) and clear_of_others(p):
                v = pcbnew.PCB_VIA(b); v.SetPosition(p); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(gnd)
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v); vias.append(p); added += 1
TXT = []   # rev 1.1: all labels come from place.py SILK (front: cable pads; back: title / notes)
for t in [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and any(d.GetText() == s and abs(d.GetPosition().x - mm(x)) < 1000
          and abs(d.GetPosition().y - mm(y)) < 1000 for s, x, y, h in TXT)]:
    b.RemoveNative(t)
for s, x, y, h in TXT:
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetTextSize(pcbnew.VECTOR2I(mm(h), mm(h))); t.SetTextThickness(mm(0.15)); b.Add(t)
# the F.Cu keepouts from pre_zones.py only steer Freerouting; drop them from the finished board
for z in [z for z in b.Zones() if z.GetIsRuleArea()]:
    b.RemoveNative(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1]); print('power GND vias added:', added); sys.stdout.flush(); os._exit(0)
