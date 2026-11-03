"""Pre-route copper (F.Cu) for the paths Freerouting handles badly, each with a matching F.Cu keepout so the router
leaves it alone:
  SW5  : U2 SW bar top end -> L1 pin 1 (6 A switch node), plus C5 bootstrap pad.
  VBUS : USB-C VBUS pads (two fingers, leaving a channel for the CC escapes) -> U2/U4 input caps -> U2 VIN.
         The U1 lobe is copper but NOT keepout, so the router can reach U1.8 and tie in C1/R2/R3/U1.1.
usage: pre_zones.py board.kicad_pcb"""
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM
def poly(o, pts):
    o.NewOutline()
    for x, y in pts: o.Append(mm(x), mm(y))
def keepout(pts):
    k = pcbnew.ZONE(b); k.SetIsRuleArea(True); k.SetLayer(pcbnew.F_Cu)
    k.SetDoNotAllowTracks(True); k.SetDoNotAllowVias(True); k.SetDoNotAllowZoneFills(False)
    k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
    poly(k.Outline(), pts); b.Add(k)
def zone(net, pts, prio, ko=True, clr=0.15):
    if ko: keepout(pts)
    z = pcbnew.ZONE(b); z.SetLayer(pcbnew.F_Cu); z.SetNet(b.FindNet(net)); poly(z.Outline(), pts)
    z.SetLocalClearance(mm(clr)); z.SetMinThickness(mm(0.2)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS); z.SetAssignedPriority(prio); b.Add(z)
bbox = lambda r, n: next(q for f in b.GetFootprints() if f.GetReference() == r for q in f.Pads() if q.GetNumber() == n).GetBoundingBox()
E = lambda v: v / 1e6
lx, l1, c5 = bbox('U2', '2'), bbox('L1', '1'), bbox('C5', '2')       # SY8205 LX pin, L1 pin 1, boot cap SW pad
ym = E(lx.GetTop() + lx.GetBottom()) / 2
zone('/SW5', [(E(lx.GetLeft()) + 0.3, ym - 0.42), (E(l1.GetLeft()) - 0.3, ym - 0.42), (E(l1.GetLeft()) - 0.3, E(l1.GetTop()) - 0.25),
              (E(l1.GetRight()) + 0.25, E(l1.GetTop()) - 0.25), (E(l1.GetRight()) + 0.25, E(l1.GetBottom()) + 0.25),
              (E(c5.GetRight()) + 0.2, E(l1.GetBottom()) + 0.25), (E(c5.GetRight()) + 0.2, E(c5.GetBottom()) + 0.2),
              (E(c5.GetLeft()) - 0.2, E(c5.GetBottom()) + 0.2), (E(c5.GetLeft()) - 0.2, ym + 0.42), (E(lx.GetLeft()) + 0.3, ym + 0.42)], 4)
# +5 V: eFuse OUT stub (above U3) -> C12 / D1 -> corridor -> cable pads 1/2 (R13 +5 V pad sits on the corridor edge)
zone('+5V', [(146.4, 100.3), (158.0, 100.3), (158.0, 100.3), (169.8, 100.3), (169.8, 108.6), (174.6, 108.6), (174.6, 113.3),
             (158.0, 113.3), (158.0, 104.5), (150.2, 104.5), (150.2, 102.9), (146.4, 102.9)], 4)
P = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
def trk(pts, net, w):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        s = pcbnew.PCB_TRACK(b); s.SetStart(P(x0, y0)); s.SetEnd(P(x1, y1)); s.SetWidth(mm(w)); s.SetLayer(pcbnew.F_Cu)
        s.SetNet(b.FindNet(net)); s.SetLocked(True); b.Add(s)
pad = lambda r, n: next(p for f in b.GetFootprints() if f.GetReference() == r for p in f.Pads() if p.GetNumber() == n).GetPosition()
c2, c13 = pad('C2', '1'), pad('C13', '1')
# VBUS bus: both USB-C VBUS pad groups -> 1 mm spine at x = 111.0 -> C2 (U2 input) and C13 (U4 input)
vb = sorted({round(pad('J1', n).y / 1e6, 2) for n in ('A4', 'A9')})      # the two USB-C VBUS pad groups
for y in vb:
    trk([(107.9, y), (111.0, y)], 'VBUS', 0.6)
# spine down the left side, then jog right past the run-control parts (Q1/R2-R4) to the U4 input caps
trk([(111.0, min(vb + [c2.y / 1e6])), (111.0, max(vb) + 0.3), (113.4, max(vb) + 2.7), (113.4, c13.y / 1e6), (c13.x / 1e6, c13.y / 1e6)], 'VBUS', 1.0)
trk([(c2.x / 1e6, c2.y / 1e6), (111.0, c2.y / 1e6)], 'VBUS', 1.0)
u18 = pad('U1', '8')
u27 = pad('U2', '7')
trk([(u18.x / 1e6, u18.y / 1e6), (u27.x / 1e6 - 1.7, u18.y / 1e6), (u27.x / 1e6 - 0.9, u27.y / 1e6), (u27.x / 1e6, u27.y / 1e6)], 'VBUS', 0.4)   # CH224A VBUS pin -> SY8205 IN pin
# LMR51430 switch nodes: SW pin (U4/U5 rotated 180 deg, SW faces the inductor) straight to the inductor pad
for u, l, net in (('U4', 'L2', '/SW12'), ('U5', 'L3', '/SWN')):
    s, e = pad(u, '2'), pad(l, '1')
    trk([(s.x / 1e6, s.y / 1e6), (e.x / 1e6 - 0.6, s.y / 1e6)], net, 0.6)
# -12 V boot cap (C23) switch pad straight across to L3 pin 1 (both SWN)
c23, l3 = pad('C23', '2'), bbox('L3', '1')
trk([(c23.x / 1e6, c23.y / 1e6), (E(l3.GetLeft()) + 0.6, c23.y / 1e6)], '/SWN', 0.4)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1]); print('pre-route zones added'); sys.stdout.flush(); os._exit(0)
