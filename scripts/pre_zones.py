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
zone('/SW5', [(120.42, 101.4), (127.3, 101.4), (127.3, 107.8), (124.9, 107.8), (124.9, 104.9), (120.85, 104.9),
              (120.85, 105.6), (120.42, 105.6)], 4)
P = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
def trk(pts, net, w):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        s = pcbnew.PCB_TRACK(b); s.SetStart(P(x0, y0)); s.SetEnd(P(x1, y1)); s.SetWidth(mm(w)); s.SetLayer(pcbnew.F_Cu)
        s.SetNet(b.FindNet(net)); s.SetLocked(True); b.Add(s)
pad = lambda r, n: next(p for f in b.GetFootprints() if f.GetReference() == r for p in f.Pads() if p.GetNumber() == n).GetPosition()
c2, c13 = pad('C2', '1'), pad('C13', '1')
# VBUS bus: both USB-C VBUS pad groups -> 1 mm spine at x = 111.0 -> C2 (U2 input) and C13 (U4 input)
trk([(107.9, 111.55), (111.0, 111.55)], 'VBUS', 0.6)
trk([(107.9, 116.45), (111.0, 116.45)], 'VBUS', 0.6)
trk([(111.0, 111.55), (111.0, c13.y / 1e6), (c13.x / 1e6, c13.y / 1e6)], 'VBUS', 1.0)
trk([(c2.x / 1e6, c2.y / 1e6), (111.0, c2.y / 1e6)], 'VBUS', 1.0)
u18 = pad('U1', '8')
trk([(111.0, c13.y / 1e6), (112.0, c13.y / 1e6 + 1.0), (112.0, u18.y / 1e6), (u18.x / 1e6, u18.y / 1e6)], 'VBUS', 0.4)
# LMR51430 switch nodes: SW pin (U4/U5 rotated 180 deg, SW faces the inductor) straight to the inductor pad
for u, l, net in (('U4', 'L2', '/SW12'), ('U5', 'L3', '/SWN')):
    s, e = pad(u, '2'), pad(l, '1')
    trk([(s.x / 1e6, s.y / 1e6), (e.x / 1e6 - 0.6, s.y / 1e6)], net, 0.6)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1]); print('pre-route zones added'); sys.stdout.flush(); os._exit(0)
