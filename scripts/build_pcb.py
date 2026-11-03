"""Build the board from the schematic + netlist with the placement in place.py (all parts on the top side).
usage: python3 -I build_pcb.py <project dir>"""
import sys, os
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, find, first
from place import X0, Y0, X1, Y1, PLACE, SILK

D = os.path.abspath(sys.argv[1])
NAME = 'Amiga USB-C PD Power Supply'
LIB = 'AMIGA_PD_PSU'
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))

sch = parse(open(f'{D}/{NAME}.kicad_sch').read())[0]
syms = {}
for s in find(sch, 'symbol'):
    props = {p[1]: p[2] for p in find(s, 'property')}
    if props['Reference'].startswith('#'):
        continue
    syms[props['Reference']] = dict(uuid=first(s, 'uuid')[1], fp=props['Footprint'], value=props['Value'],
                                    lcsc=props.get('LCSC', ''), desc=props.get('Description', ''),
                                    inbom=first(s, 'in_bom')[1] == 'yes')
pinnet = {}
n = parse(open(f'{D}/net.net').read())[0]
for net in find(first(n, 'nets'), 'net'):
    name = first(net, 'name')[1]
    for node in find(net, 'node'):
        pinnet[(first(node, 'ref')[1], first(node, 'pin')[1])] = name

board = pcbnew.BOARD()
board.SetCopperLayerCount(2)
nets = {}
def getnet(name):
    if name not in nets:
        ni = pcbnew.NETINFO_ITEM(board, name); board.Add(ni); nets[name] = ni
    return nets[name]

assert set(syms) == set(PLACE), (set(syms) ^ set(PLACE))
for ref in sorted(syms):
    s = syms[ref]
    lib, fpname = s['fp'].split(':'); assert lib == LIB, s['fp']
    fp = pcbnew.FootprintLoad(f'{D}/{LIB}.pretty', fpname); assert fp, s['fp']
    fp.thisown = False
    fp.SetFPID(pcbnew.LIB_ID(lib, fpname))
    fp.SetReference(ref); fp.SetValue(s['value'])
    if s['lcsc']:
        fp.SetField('LCSC', s['lcsc']); f = fp.GetField('LCSC'); f.SetVisible(False); f.SetLayer(pcbnew.F_Fab)
    fp.SetPath(pcbnew.KIID_PATH('/' + s['uuid']))
    fp.GetField('Description').SetText(s['desc'])
    fp.SetExcludedFromBOM(not s['inbom'])
    fp.SetSheetfile(f'{NAME}.kicad_sch'); fp.SetSheetname('Root')
    board.Add(fp)
    x, y, rot = PLACE[ref]
    for pad in fp.Pads():
        nn = pinnet.get((ref, pad.GetNumber()))
        if nn:
            pad.SetNet(getnet(nn))
        elif ref == 'U1' and pad.GetNumber() == '':     # EP paste-only sub-pads
            pad.SetNet(getnet('GND'))
    fp.SetPosition(V(x, y))
    fp.SetOrientationDegrees(rot)
    r = fp.Reference(); r.SetLayer(pcbnew.F_Fab)
    r.SetTextSize(V(0.5, 0.5)); r.SetTextThickness(mm(0.08)); r.SetPosition(fp.GetPosition())
    fp.Value().SetVisible(False)

R = 2.0   # corner radius
def seg(a, b):
    l = pcbnew.PCB_SHAPE(board); l.SetShape(pcbnew.SHAPE_T_SEGMENT)
    l.SetStart(V(*a)); l.SetEnd(V(*b)); l.SetLayer(pcbnew.Edge_Cuts); l.SetWidth(mm(0.1)); board.Add(l)
seg((X0 + R, Y0), (X1 - R, Y0)); seg((X1, Y0 + R), (X1, Y1 - R)); seg((X1 - R, Y1), (X0 + R, Y1)); seg((X0, Y1 - R), (X0, Y0 + R))
for c, st in (((X0 + R, Y0 + R), (X0, Y0 + R)), ((X1 - R, Y0 + R), (X1 - R, Y0)), ((X1 - R, Y1 - R), (X1, Y1 - R)), ((X0 + R, Y1 - R), (X0 + R, Y1))):
    a = pcbnew.PCB_SHAPE(board); a.SetShape(pcbnew.SHAPE_T_ARC); a.SetLayer(pcbnew.Edge_Cuts); a.SetWidth(mm(0.1))
    a.SetCenter(V(*c)); a.SetStart(V(*st)); a.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T), True); board.Add(a)

for txt, x, y, size, ang in SILK:
    t = pcbnew.PCB_TEXT(board); t.SetText(txt); t.SetLayer(pcbnew.F_SilkS)
    t.SetPosition(V(x, y)); t.SetTextSize(V(size, size)); t.SetTextThickness(mm(0.15)); t.SetTextAngleDegrees(ang)
    board.Add(t)

board.Save(f'{D}/{NAME}.kicad_pcb')
print('board %.1f x %.1f mm, %d footprints' % (X1 - X0, Y1 - Y0, len(syms)))
sys.stdout.flush(); os._exit(0)
