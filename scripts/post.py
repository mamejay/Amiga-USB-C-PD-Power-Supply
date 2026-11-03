"""Post-route finishing: extra GND vias around the converters' power-ground pads (both pours must be solid there),
silkscreen labels. Idempotent. usage: post.py board.kicad_pcb"""
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM
gnd = b.FindNet('GND')
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
Z = {L: [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.GetLayer() == L][0].GetFilledPolysList(L)
     for L in (pcbnew.F_Cu, pcbnew.B_Cu)}
HOT = [(120.8, 108.8, 124.2, 115.5), (122.8, 122.5, 125.0, 125.5), (133.4, 103.0, 143.6, 105.0), (135.6, 120.0, 143.5, 122.2),
       (147.0, 118.6, 150.0, 120.2), (135.6, 140.2, 143.5, 142.5), (128.5, 143.0, 134.0, 145.4), (154.0, 121.5, 157.6, 128.5)]
vias = [t.GetPosition() for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
added = 0
for x0, y0, x1, y1 in HOT:
    for ix in range(int(x0 * 10), int(x1 * 10) + 1, 2):
        for iy in range(int(y0 * 10), int(y1 * 10) + 1, 2):
            p = pcbnew.VECTOR2I(ix * 100000, iy * 100000)
            if any((v.x - p.x) ** 2 + (v.y - p.y) ** 2 < mm(1.3) ** 2 for v in vias):
                continue
            if all(Z[L].Contains(pcbnew.VECTOR2I(p.x + dx, p.y + dy)) for L in Z
                   for dx in (-mm(0.55), 0, mm(0.55)) for dy in (-mm(0.55), 0, mm(0.55))):
                v = pcbnew.PCB_VIA(b); v.SetPosition(p); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(gnd)
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v); vias.append(p); added += 1
TXT = [('AMIGA USB-C PSU r1.0', 133.6, 116.2, 0.9), ('+5V', 157.0, 110.2, 0.8), ('FAULT', 150.0, 118.2, 0.8),
       ('+12V', 150.6, 124.8, 0.8), ('-12V', 153.2, 137.2, 0.8)]
for t in [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and any(d.GetText() == s and abs(d.GetPosition().x - mm(x)) < 1000
          and abs(d.GetPosition().y - mm(y)) < 1000 for s, x, y, h in TXT)]:
    b.RemoveNative(t)
for s, x, y, h in TXT:
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetTextSize(pcbnew.VECTOR2I(mm(h), mm(h))); t.SetTextThickness(mm(0.15)); b.Add(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1]); print('power GND vias added:', added); sys.stdout.flush(); os._exit(0)
