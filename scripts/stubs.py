"""Pre-route fixed stubs off the eFuse bars (0.3 mm wide, 0.19 mm apart) so the router and the pours can reach them:
5V_BUCK leaves the IN bar at its bottom end, +5V leaves the OUT bar at its top end. usage: stubs.py board.kicad_pcb"""
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM
u3 = next(f for f in b.GetFootprints() if f.GetReference() == 'U3')
bars = {p.GetNumber(): p for p in u3.Pads() if p.GetNumber() in ('5', '6')}
def trk(pts, net, w):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(a); t.SetEnd(c); t.SetWidth(mm(w)); t.SetLayer(pcbnew.F_Cu)
        t.SetNet(b.FindNet(net)); t.SetLocked(True); b.Add(t)
i, o = bars['5'].GetBoundingBox(), bars['6'].GetBoundingBox()
xi, xo = (i.GetLeft() + i.GetRight()) // 2, (o.GetLeft() + o.GetRight()) // 2
assert i.GetLeft() < o.GetLeft(), 'U3 rotated: IN bar must be left of OUT bar'
P = pcbnew.VECTOR2I
trk([P(xi, i.GetBottom() - mm(0.4)), P(xi, i.GetBottom() + mm(0.9)), P(xi - mm(1.2), i.GetBottom() + mm(2.1))], '/5V_BUCK', 0.3)
trk([P(xo, o.GetTop() + mm(0.4)), P(xo, o.GetTop() - mm(0.9)), P(xo + mm(1.2), o.GetTop() - mm(2.1))], '+5V', 0.3)
b.Save(sys.argv[1]); print('stubs added'); sys.stdout.flush(); os._exit(0)
