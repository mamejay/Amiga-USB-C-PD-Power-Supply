"""JLCPCB outputs: 2-layer gerbers + drill (zipped), BOM and CPL (all assembled parts on the TOP side).
J2 (cable pads) and the M3 holes are not assembled.
usage: python3 -I make_fab.py <project dir> <out dir>"""
import sys, os, csv, subprocess, zipfile, glob, shutil, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, find, first

D, OUT = map(os.path.abspath, sys.argv[1:3])
N = 'Amiga USB-C PD Power Supply'
PCB, SCH = f'{D}/{N}.kicad_pcb', f'{D}/{N}.kicad_sch'
HAND = {'J2'}
os.makedirs(OUT, exist_ok=True)
G = f'{OUT}/gerbers'; shutil.rmtree(G, ignore_errors=True); os.makedirs(G)
run = lambda *a: subprocess.run(a, check=True, capture_output=True, text=True)

layers = 'F.Cu,B.Cu,F.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'
run('kicad-cli', 'pcb', 'export', 'gerbers', '-o', G + '/', '-l', layers, '--subtract-soldermask', '--no-protel-ext', PCB)
run('kicad-cli', 'pcb', 'export', 'drill', '-o', G + '/', '--format', 'excellon', '--excellon-units', 'mm',
    '--excellon-separate-th', '--generate-map', '--map-format', 'gerberx2', '--drill-origin', 'absolute', PCB)
zp = f'{OUT}/{N} - Gerbers.zip'
with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(glob.glob(G + '/*')):
        z.write(f, os.path.basename(f))

sch = parse(open(SCH).read())[0]
parts = {}
for s in find(sch, 'symbol'):
    p = {q[1]: q[2] for q in find(s, 'property')}
    ref = p['Reference']
    if ref.startswith('#') or first(s, 'in_bom')[1] != 'yes' or ref in HAND:
        continue
    parts[ref] = p
def fpname(p):
    f = p['Footprint'].split(':')[1]
    m = re.search(r'(0603|0805|1206|SOD-123F|SOD-123|TSOT-23-6|SOT-23|SSOP-10|VQFN-HR-10_3x3|VQFN-10-HR_2x2|CMLO0650H|FNR8040|TYPE-C-31-M-12)', f)
    return m.group(1) if m else f
groups = {}
for ref, p in parts.items():
    groups.setdefault((p['Value'], fpname(p), p.get('LCSC', '')), []).append(ref)
nat = lambda r: (re.sub(r'\d', '', r), int(re.sub(r'\D', '', r)))
with open(f'{OUT}/{N} - BOM.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
    for (val, fp, lcsc), refs in sorted(groups.items(), key=lambda g: nat(sorted(g[1], key=nat)[0])):
        assert lcsc, (val, refs)
        w.writerow([val, ','.join(sorted(refs, key=nat)), fp, lcsc])

# JLC rotation corrections (their part models vs KiCad zero orientation), checked in JLC's 3D preview 2026-11-03:
# U1/U4/U5 -90 (set by the user), Q1 +180 (SOT-23 model had its two legs on the wrong side). U2, U3, J1, D1-D8 raw.
JLC_ROT_FIX = {'U1': -90, 'U2': -90, 'U4': -90, 'U5': -90, 'Q1': 180}   # U2 (SY8205 SO-8E, rev 1.2) -90 set by the user 2026-11-03
raw = f'{OUT}/pos_raw.csv'
run('kicad-cli', 'pcb', 'export', 'pos', '-o', raw, '--format', 'csv', '--units', 'mm', '--side', 'both', PCB)
with open(raw) as f, open(f'{OUT}/{N} - CPL.csv', 'w', newline='') as g:
    w = csv.writer(g); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    rows = [r for r in csv.DictReader(f) if r['Ref'] in parts]
    for r in sorted(rows, key=lambda r: nat(r['Ref'])):
        w.writerow([r['Ref'], '%.4fmm' % float(r['PosX']), '%.4fmm' % float(r['PosY']),
                    'Top' if r['Side'] == 'top' else 'Bottom', '%g' % ((float(r['Rot']) + JLC_ROT_FIX.get(r['Ref'], 0)) % 360)])
os.remove(raw)
missing = set(parts) - {r['Ref'] for r in rows}
print('gerbers:', len(glob.glob(G + '/*')), 'files ->', os.path.basename(zp))
print('BOM lines:', len(groups), ' parts:', len(parts), ' CPL rows:', len(rows), ' sides:', {r['Side'] for r in rows}, ' missing:', sorted(missing))
