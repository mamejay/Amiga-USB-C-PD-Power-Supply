"""Copper pours after routing: GND on both layers (priority 1) plus F.Cu power zones (priority 2) that fatten the
high-current paths wherever there is room (fills flow around routed tracks; unconnected islands are removed).
usage: pours.py board.kicad_pcb"""
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM
def zone(layer, net, pts, prio, clr=0.2):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(b.FindNet(net))
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(x), mm(y))
    z.SetLocalClearance(mm(clr)); z.SetMinThickness(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS); z.SetAssignedPriority(prio); b.Add(z)
R = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
bb = b.GetBoardEdgesBoundingBox(); E = lambda v: v / 1e6
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    zone(layer, 'GND', R(E(bb.GetLeft()), E(bb.GetTop()), E(bb.GetRight()), E(bb.GetBottom())), 1, 0.25)
F = pcbnew.F_Cu
# rev 1.1 slim layout (76 x 32)
zone(F, 'VBUS', [(117.4, 104.0), (119.95, 104.0), (119.95, 113.4), (111.8, 113.4), (111.8, 118.3), (114.2, 120.7), (114.2, 125.2),
                 (118.2, 125.2), (118.2, 126.5), (112.6, 126.5), (112.6, 121.0), (110.2, 118.6), (110.2, 111.4), (117.4, 111.4)], 2)                                    # bus -> U2 caps/VIN, -> U4 caps
zone(F, '/5V_BUCK', [(x, y - 1.5) for x, y in [(124.5, 103.6), (134.0, 103.6), (134.0, 106.2), (146.4, 106.2), (146.4, 109.5),
                     (124.5, 109.5)]], 2, 0.15)                         # L1 -> caps -> eFuse IN
zone(F, '+12V', [(129.3, 121.9), (132.0, 121.9), (132.0, 124.9), (142.2, 124.9), (142.2, 128.6), (129.3, 128.6)], 2)   # L2 -> caps
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1]); sys.stdout.flush(); os._exit(0)
