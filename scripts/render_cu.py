"""Render one copper layer (zone fills coloured by net, tracks, pads) for layout review.
usage: render_cu.py board.kicad_pcb out.png F|B"""
import sys, pcbnew
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
b = pcbnew.LoadBoard(sys.argv[1]); MM = 1e-6
L = pcbnew.F_Cu if sys.argv[3] == 'F' else pcbnew.B_Cu
COL = {'GND': '#bbbbbb', 'VBUS': '#e07b39', '/5V_BUCK': '#f2c14e', '+5V': '#e8554e', '+12V': '#4caf50', '-12V': '#3f7fd1',
       '/SW5': '#9c27b0', '/SW12': '#9c27b0', '/SWN': '#9c27b0'}
fig, ax = plt.subplots(figsize=(14, 10.5), dpi=100)
def poly(ps, **kw):
    for k in range(ps.OutlineCount()):
        o = ps.Outline(k); ax.add_patch(Polygon([(o.CPoint(i).x*MM, o.CPoint(i).y*MM) for i in range(o.PointCount())], closed=True, **kw))
for z in sorted(b.Zones(), key=lambda z: z.GetAssignedPriority()):
    if z.GetIsRuleArea() or z.GetLayer() != L: continue
    poly(z.GetFilledPolysList(L), fc=COL.get(z.GetNetname(), '#888'), ec='none', alpha=0.85)
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == L:
        ps = pcbnew.SHAPE_POLY_SET(); t.TransformShapeToPolygon(ps, L, 0, 5000, pcbnew.ERROR_INSIDE)
        poly(ps, fc=COL.get(t.GetNetname(), '#444'), ec='k', lw=0.2)
    elif t.Type() == pcbnew.PCB_VIA_T:
        q = t.GetPosition(); ax.add_patch(Circle((q.x*MM, q.y*MM), t.GetWidth(L)*MM/2, fc=COL.get(t.GetNetname(), '#444'), ec='k', lw=0.3))
for f in b.GetFootprints():
    for p in f.Pads():
        if p.IsOnLayer(L):
            ps = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(ps, L, 0, 5000, pcbnew.ERROR_INSIDE)
            poly(ps, fc=COL.get(p.GetNetname(), '#666'), ec='k', lw=0.4)
    q = f.GetPosition(); ax.text(q.x*MM, q.y*MM, f.GetReference(), fontsize=7, ha='center', va='center', color='k')
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts:
        ps = pcbnew.SHAPE_POLY_SET(); d.TransformShapeToPolygon(ps, pcbnew.Edge_Cuts, 0, 5000, pcbnew.ERROR_INSIDE); poly(ps, fc='k', ec='k')
bb = b.GetBoardEdgesBoundingBox()
ax.set_xlim(bb.GetLeft()*MM - 1, bb.GetRight()*MM + 1); ax.set_ylim(bb.GetBottom()*MM + 1, bb.GetTop()*MM - 1)
ax.set_aspect('equal'); ax.set_title(('F' if L == pcbnew.F_Cu else 'B') + '.Cu  orange VBUS, yellow 5V_BUCK, red +5V, green +12V, blue -12V, purple SW, grey GND')
fig.savefig(sys.argv[2], bbox_inches='tight')
