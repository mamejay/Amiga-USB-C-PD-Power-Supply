"""Add the M3 mounting holes (board-only, not in BOM/CPL) by text edit. usage: add_holes.py board.kicad_pcb"""
import sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, dump, Q, find
from place import HOLES
brd = sys.argv[1]
U = lambda s: Q(str(uuid.uuid5(uuid.NAMESPACE_URL, 'amiga-pd-psu-hole-' + s)))
tree = parse(open(brd).read())[0]
tree[:] = [e for e in tree if not (isinstance(e, list) and e and e[0] == 'footprint' and any(
    p[1] == 'Reference' and p[2] in HOLES for p in find(e, 'property')))]
mh = parse(open('/usr/share/kicad/footprints/MountingHole.pretty/MountingHole_3.2mm_M3.kicad_mod').read())[0]
for ref, (x, y) in HOLES.items():
    f = ['footprint', Q('AMIGA_PD_PSU:MountingHole_3.2mm_M3'), ['layer', Q('F.Cu')], ['uuid', U(ref)], ['at', x, y]]
    for e in mh[2:]:
        if not isinstance(e, list) or e[0] in ('version', 'generator', 'generator_version', 'layer', 'embedded_fonts'):
            continue
        e = list(e)
        if e[0] == 'attr':
            e = ['attr', 'exclude_from_pos_files', 'exclude_from_bom', 'board_only']
        if e[0] == 'property' and e[1] == 'Reference':
            e[2] = Q(ref)
            e = [x_ if not (isinstance(x_, list) and x_[0] == 'layer') else ['layer', Q('F.Fab')] for x_ in e]
        if e[0] == 'property' and e[1] == 'Value':
            e[2] = Q('M3')
        f.append(e)
    tree.append(f)
open(brd, 'w').write(dump(tree) + '\n')
print('holes added', list(HOLES))
