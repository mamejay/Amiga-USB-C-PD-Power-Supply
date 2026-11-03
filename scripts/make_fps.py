"""Write clean KiCad footprints into the project library.
 - TPS56637 RPA (VQFN-HR-10 3x3), CMLO0650H (7.1x6.6) and FNR8040 (8x8) inductors: pad geometry taken from the
   easyeda2kicad imports in e2k/lib.pretty, rewritten with a body outline on F.Fab/F.Silk and a courtyard = pads/body + 0.25 mm.
 - Amiga output wire pads: 6 x THT 1.4 mm holes, 3.81 mm pitch (two +5 V, two GND, +12 V, -12 V).
usage: make_fps.py <e2k lib.pretty> <project lib.pretty>"""
import sys, re, os
SRC, DST = sys.argv[1:3]

def pads_of(f):
    out = []
    for m in re.finditer(r'\(pad (\S+) smd \S+ \(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\) \(size ([\d.]+) ([\d.]+)\)', open(f).read()):
        n, x, y, a, w, h = m[1], float(m[2]), float(m[3]), float(m[4] or 0), float(m[5]), float(m[6])
        if abs(a) % 180 == 90: w, h = h, w
        out.append((n, x, y, w, h))
    return out

def rect(x0, y0, x1, y1, layer, w):
    return ''.join(f'  (fp_line (start {a:.3f} {b:.3f}) (end {c:.3f} {d:.3f}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
                   for a, b, c, d in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)))

def write(name, desc, pads, body, tht=False, extra=''):
    bx, by = body
    xs = [p[1] - p[3] / 2 for p in pads] + [p[1] + p[3] / 2 for p in pads] + [-bx / 2, bx / 2]
    ys = [p[2] - p[4] / 2 for p in pads] + [p[2] + p[4] / 2 for p in pads] + [-by / 2, by / 2]
    cx0, cy0, cx1, cy1 = min(xs) - .25, min(ys) - .25, max(xs) + .25, max(ys) + .25
    s = (f'(footprint "{name}"\n  (version 20241229)\n  (generator "pcbnew")\n  (generator_version "10.0")\n  (layer "F.Cu")\n'
         f'  (descr "{desc}")\n  (property "Reference" "REF**" (at 0 {cy0 - 0.8:.2f} 0) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))\n'
         f'  (property "Value" "{name}" (at 0 {cy1 + 0.8:.2f} 0) (layer "F.Fab") (hide yes) (effects (font (size 0.5 0.5) (thickness 0.08))))\n'
         f'  (attr {"through_hole" if tht else "smd"})\n')
    s += rect(-bx / 2, -by / 2, bx / 2, by / 2, 'F.Fab', 0.1) + rect(cx0, cy0, cx1, cy1, 'F.CrtYd', 0.05) + extra
    for n, x, y, w, h, *k in pads:
        if tht:
            s += (f'  (pad "{n}" thru_hole {"rect" if n == "1" else "circle"} (at {x:.3f} {y:.3f}) (size {w} {h}) (drill {k[0]}) '
                  f'(layers "*.Cu" "*.Mask"))\n')
        else:
            s += f'  (pad "{n}" smd rect (at {x:.3f} {y:.3f}) (size {w:.3f} {h:.3f}) (layers "F.Cu" "F.Paste" "F.Mask"))\n'
    s += '  (embedded_fonts no)\n)\n'
    open(f'{DST}/{name}.kicad_mod', 'w').write(s)
    print(name, len(pads), 'pads, courtyard %.2f x %.2f' % (cx1 - cx0, cy1 - cy0))

pin1 = '  (fp_circle (center -1.9 -1.2) (end -1.8 -1.2) (stroke (width 0.2) (type solid)) (fill yes) (layer "F.SilkS"))\n'
write('TI_RPA0010A_VQFN-HR-10_3x3mm', 'TI RPA0010A VQFN-HR-10 3x3 mm (TPS56637), pads per EasyEDA C841386',
      pads_of(f'{SRC}/VQFN-HR-10_L3.0-W3.0_RPA.kicad_mod'), (3.0, 3.0), extra=pin1)
write('L_Chilisin_CMLO0650H', 'Chilisin CMLO0650H 7.1x6.6 mm molded power inductor, pads per EasyEDA C439008',
      pads_of(f'{SRC}/IND-SMD_L7.1-W6.6.kicad_mod'), (7.1, 6.6))
write('L_FH_FNR8040', 'Fenghua FNR8040S 8x8 mm shielded power inductor, pads per EasyEDA C168128',
      pads_of(f'{SRC}/IND-SMD_L8.0-W8.0_FNR80XXS.kicad_mod'), (8.0, 8.0))
P = 3.81
write('WirePads_1x06_P3.81mm_D1.4mm', 'Amiga output cable wire pads, 1.4 mm holes for up to 18 AWG',
      [(str(i + 1), (i - 2.5) * P, 0.0, 2.6, 2.6, 1.4) for i in range(6)], (6 * P, 3.2), tht=True)
