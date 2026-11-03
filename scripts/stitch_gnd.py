"""Stitch isolated GND pour islands (either layer) to the other layer's GND pour with a via each.
usage: stitch_gnd.py board.kicad_pcb"""
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
Z = {L: [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.GetLayer() == L][0] for L in (pcbnew.F_Cu, pcbnew.B_Cu)}
VIA_R = 0.45
added = 0
for _ in range(3):
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    new = 0
    for L, O in ((pcbnew.B_Cu, pcbnew.F_Cu), (pcbnew.F_Cu, pcbnew.B_Cu)):
        fl, fo = Z[L].GetFilledPolysList(L), Z[O].GetFilledPolysList(O)
        # the biggest island on each layer is the main pour; stitch every other island that has no via / THT pad
        areas = sorted(range(fl.OutlineCount()), key=lambda k: -abs(fl.Outline(k).Area()))
        for k in areas[1:]:
            isl = pcbnew.SHAPE_POLY_SET(fl.Outline(k))
            if abs(fl.Outline(k).Area()) / 1e12 < 0.4:
                continue
            hit = any(t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == 'GND' and isl.Contains(t.GetPosition()) for t in b.GetTracks()) or \
                  any(p.GetNetname() == 'GND' and p.HasHole() and isl.Contains(p.GetPosition()) for f in b.GetFootprints() for p in f.Pads())
            if hit:
                continue
            bb = fl.Outline(k).BBox(); best = None
            for ix in range(int(bb.GetLeft() / 1e5), int(bb.GetRight() / 1e5) + 1):
                for iy in range(int(bb.GetTop() / 1e5), int(bb.GetBottom() / 1e5) + 1):
                    pt = pcbnew.VECTOR2I(ix * 100000, iy * 100000)
                    if all(isl.Contains(pcbnew.VECTOR2I(pt.x + dx, pt.y + dy)) and fo.Contains(pcbnew.VECTOR2I(pt.x + dx, pt.y + dy))
                           for dx in (-mm(VIA_R), 0, mm(VIA_R)) for dy in (-mm(VIA_R), 0, mm(VIA_R))):
                        if clear_of_others(pt):
                            best = pt; break
                if best: break
            if best is None:
                print('island no via spot', 'F' if L == pcbnew.F_Cu else 'B', round(bb.GetLeft() / 1e6, 2), round(bb.GetTop() / 1e6, 2)); continue
            v = pcbnew.PCB_VIA(b); v.SetPosition(best); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(gnd)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v); added += 1; new += 1
    if not new:
        break
# extra stitching: a GND via grid wherever both pours overlap with room, every 5 mm
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
ff, fb = Z[pcbnew.F_Cu].GetFilledPolysList(pcbnew.F_Cu), Z[pcbnew.B_Cu].GetFilledPolysList(pcbnew.B_Cu)
bb = b.GetBoardEdgesBoundingBox(); grid = 0
vias = [t.GetPosition() for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
for x in range(bb.GetLeft() + mm(2.5), bb.GetRight(), mm(5)):
    for y in range(bb.GetTop() + mm(2.5), bb.GetBottom(), mm(5)):
        pt = pcbnew.VECTOR2I(x, y)
        if any(abs(v.x - x) < mm(1.5) and abs(v.y - y) < mm(1.5) for v in vias):
            continue
        if all(ff.Contains(pcbnew.VECTOR2I(x + dx, y + dy)) and fb.Contains(pcbnew.VECTOR2I(x + dx, y + dy))
               for dx in (-mm(0.6), 0, mm(0.6)) for dy in (-mm(0.6), 0, mm(0.6))) and clear_of_others(pt):
            v = pcbnew.PCB_VIA(b); v.SetPosition(pt); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(gnd)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v); grid += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1]); print('stitching vias added:', added, 'island +', grid, 'grid'); sys.stdout.flush(); os._exit(0)
