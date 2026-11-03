"""Generate the Amiga USB-C PD Power Supply schematic (KiCad 10) and its project symbol library.

Original design (2026-11-03). Spec targets only were taken from public Amiga PSU ratings and the
SnCMuseum/PCBWay "V2" board (5 V 4.5 A cont., +12 V 0.5-1.1 A, -12 V 0.15-0.5 A); no circuitry was copied.
  USB-C -> CH224A (asks for 15 V) -> both bucks enabled only after the PD contract (CH224A PG low, Q1) AND VBUS > ~12 V.
  +5 V : TPS56637 6 A buck (FCCM) -> TPS259470A eFuse (OVLO 5.64 V, ~6 A limit, soft start, fault LED) -> wire pads
  +12 V: LMR51430 3 A buck (12.36 V)
  -12 V: LMR51430 in inverting buck-boost, fed from +12 V (-12.36 V, >1 A capable)
usage: python3 -I gen_sch.py <project dir>
"""
import sys, os, uuid, copy, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, dump, Q, find, first

OUT = sys.argv[1]
NAME = 'Amiga USB-C PD Power Supply'
LIBNICK = 'AMIGA_PD_PSU'
STD = '/usr/share/kicad/symbols'
ROOT = str(uuid.uuid5(uuid.NAMESPACE_URL, 'amiga-pd-psu-root'))
_n = [0]


def uid():
    _n[0] += 1
    return Q(str(uuid.uuid5(uuid.NAMESPACE_URL, 'amiga-pd-psu-%d' % _n[0])))


_libcache = {}


def load_lib(path):
    if path not in _libcache:
        tree = parse(open(path).read())[0]
        _libcache[path] = {s[1]: s for s in find(tree, 'symbol')}
    return _libcache[path]


SOURCES = {
    'CH224K': (f'{STD}/Interface_USB.kicad_sym', 'CH224K'),       # CH224A is pin-compatible (pin 1 = VHV)
    'LMR51430': (f'{STD}/Regulator_Switching.kicad_sym', 'LMR51430'),
    '2N7002': (f'{STD}/Transistor_FET.kicad_sym', '2N7002'),
    'USB_C_Receptacle_USB2.0_16P': (f'{STD}/Connector.kicad_sym', 'USB_C_Receptacle_USB2.0_16P'),
    'Conn_01x06': (f'{STD}/Connector_Generic.kicad_sym', 'Conn_01x06'),
    'TPS56637': (None, None),
    'TPS25947': (None, None),
    'D_Zener': (f'{STD}/Device.kicad_sym', 'D_Zener'),         # unidirectional TVS
    'D_Schottky': (f'{STD}/Device.kicad_sym', 'D_Schottky'),
    'LED': (f'{STD}/Device.kicad_sym', 'LED'),
    'L': (f'{STD}/Device.kicad_sym', 'L'),
    'R': (f'{STD}/Device.kicad_sym', 'R'),
    'C': (f'{STD}/Device.kicad_sym', 'C'),
    'GND': (f'{STD}/power.kicad_sym', 'GND'),
    '+5V': (f'{STD}/power.kicad_sym', '+5V'),
    '+12V': (f'{STD}/power.kicad_sym', '+12V'),
    '-12V': (f'{STD}/power.kicad_sym', '-12V'),
    'VBUS': (f'{STD}/power.kicad_sym', 'VBUS'),
    'PWR_FLAG': (f'{STD}/power.kicad_sym', 'PWR_FLAG'),
}
FPLIB = LIBNICK + ':'

_f = '(effects (font (size 1.27 1.27)))'
def _pin(kind, x, y, a, nm, num, hide=False):
    return (f'(pin {kind} line (at {x} {y} {a}) (length 2.54){" (hide yes)" if hide else ""} '
            f'(name "{nm}" {_f}) (number "{num}" {_f}))')
def _ic(name, desc, pins):
    return (f'(symbol "{name}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
            f'(property "Reference" "U" (at -7.62 10.16 0) {_f}) (property "Value" "{name}" (at 2.54 10.16 0) {_f}) '
            f'(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes))) '
            f'(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes))) '
            f'(property "Description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes))) '
            f'(symbol "{name}_0_1" (rectangle (start -7.62 7.62) (end 7.62 -7.62) (stroke (width 0.254) (type default)) (fill (type background)))) '
            f'(symbol "{name}_1_1" ' + ' '.join(_pin(*p) for p in pins) + '))')
INLINE = {
    'TPS56637': _ic('TPS56637', 'TI TPS56637 4.5-28 V 6 A synchronous buck, D-CAP3, VQFN-HR-10 (RPA)',
                    [('power_in', -10.16, 5.08, 0, 'VIN', '8'), ('input', -10.16, 0, 0, 'EN', '1'),
                     ('input', -10.16, -2.54, 0, 'MODE', '10'), ('passive', -10.16, -5.08, 0, 'NC', '5'),
                     ('passive', 10.16, 5.08, 180, 'BOOT', '7'), ('power_out', 10.16, 2.54, 180, 'SW', '6'),
                     ('input', 10.16, -2.54, 180, 'FB', '2'), ('open_collector', 10.16, -5.08, 180, 'PG', '4'),
                     ('power_in', -2.54, -10.16, 90, 'AGND', '3'), ('power_in', 2.54, -10.16, 90, 'PGND', '9')]),
    'TPS25947': _ic('TPS25947', 'TI TPS25947 eFuse, 2.7-23 V, 0.5-6 A, adjustable OVLO',
                    [('power_in', -10.16, 5.08, 0, 'IN', '5'), ('input', -10.16, 0, 0, 'EN/UVLO', '1'),
                     ('input', -10.16, -2.54, 0, 'OVLO', '2'), ('passive', -10.16, -5.08, 0, 'DVDT', '7'),
                     ('power_out', 10.16, 5.08, 180, 'OUT', '6'), ('open_collector', 10.16, 2.54, 180, 'AUXOFF', '3'),
                     ('open_collector', 10.16, 0, 180, '~{FLT}', '4'), ('passive', 10.16, -2.54, 180, 'ILM', '9'),
                     ('passive', 10.16, -5.08, 180, 'ITIMER', '10'), ('power_in', 0, -10.16, 90, 'GND', '8')]),
}


def lib_symbol(name):
    """Symbol `name` as a bare (library-file) symbol, flattened, sub-units renamed."""
    path, src = SOURCES[name]
    if path is None:                     # project-only symbol, defined inline below
        return parse(INLINE[name])[0]
    syms = load_lib(path)
    s = copy.deepcopy(syms[src])
    ext = first(s, 'extends')
    if ext:
        parent = copy.deepcopy(syms[ext[1]])
        props = {p[1]: p for p in find(s, 'property')}
        new = [parent[0], Q(src)]
        for e in parent[2:]:
            if isinstance(e, list) and e[0] == 'property' and e[1] in props:
                new.append(props.pop(e[1]))
            elif isinstance(e, list) and e[0] == 'symbol':
                e[1] = Q(e[1].replace(ext[1], src, 1)); new.append(e)
            else:
                new.append(e)
        new.extend(props.values())
        s = new
    s[1] = Q(name)
    for sub in find(s, 'symbol'):
        sub[1] = Q(name + sub[1][len(src):])
    return s


def pins_of(sym):
    out = {}
    for sub in find(sym, 'symbol'):
        for p in find(sub, 'pin'):
            at = first(p, 'at')
            out.setdefault(first(p, 'number')[1], []).append((float(at[1]), float(at[2]), float(at[3])))
    return out


# ---------------------------------------------------------------- design
FP = lambda n: FPLIB + n
PWR = {'GND', '+5V', '+12V', '-12V', 'VBUS'}
two = lambda a, b: {'1': a, '2': b}
R0603, C0603, C0805, C1206 = FP('R_0603_1608Metric'), FP('C_0603_1608Metric'), FP('C_0805_2012Metric'), FP('C_1206_3216Metric')
# JLC Basic parts for every passive
LCSC = {'560R': 'C23204', '1k': 'C21190', '4.7k': 'C23162', '5.1k': 'C23186', '10k': 'C25804', '12k': 'C22790',
        '20k': 'C4184', '27k': 'C22967', '47k': 'C25819', '56k': 'C23206', '75k': 'C23242', '100k': 'C25803',
        '100pF': 'C14858', '2.2nF': 'C1604', '100nF/50V': 'C14663', '1uF/50V': 'C15849', '10uF/25V': 'C15850',
        '22uF/25V': 'C45783', '10uF/50V': 'C13585'}
CFP = {'100pF': C0603, '2.2nF': C0603, '100nF/50V': C0603, '1uF/50V': C0603, '10uF/25V': C0805, '22uF/25V': C0805,
       '10uF/50V': C1206}


def R(ref, val, xy, a, b, desc=''):
    return (ref, 'R', val, R0603, xy, two(a, b), {'LCSC': LCSC[val], 'Description': desc})


def C(ref, val, xy, a, b, desc=''):
    return (ref, 'C', val, CFP[val], xy, two(a, b), {'LCSC': LCSC[val], 'Description': desc})


def LED(ref, colour, lcsc, xy, a, k, desc):
    return (ref, 'LED', colour, FP('LED_0805_2012Metric'), xy, {'2': a, '1': k}, {'LCSC': lcsc, 'Description': desc})


TVS = lambda ref, val, lcsc, xy, k, a, desc: (ref, 'D_Zener', val, FP('D_SOD-123F'), xy, {'1': k, '2': a},
                                               {'LCSC': lcsc, 'Description': desc})
usb = {'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'SH': 'GND',
       'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS', 'B9': 'VBUS', 'A5': 'CC1', 'B5': 'CC2'}   # D+/D- open: PD only
PARTS = [
    # ---- input: USB-C + PD sink (15 V request)
    ('J1', 'USB_C_Receptacle_USB2.0_16P', 'USB-C (power in)', FP('USB_C_Receptacle_HRO_TYPE-C-31-M-12'), (38.1, 76.2), usb,
     {'LCSC': 'C165948', 'Description': 'HRO TYPE-C-31-M-12 USB-C receptacle, 5 A contacts. Only VBUS/GND/CC used (PD only)'}),
    ('U1', 'CH224K', 'CH224A', FP('SSOP-10-1EP_3.9x4.9mm_P1mm_EP2.1x3.3mm'), (99.06, 76.2),
     {'1': 'VBUS', '8': 'VBUS', '9': 'CFG1', '7': 'CC1', '6': 'CC2', '10': 'PG', '11': 'GND'},
     {'LCSC': 'C42459160', 'Description': 'WCH CH224A USB PD sink, ESSOP-10 (CH224K pin-out; VHV/PG are 32 V tolerant)'}),
    C('C1', '1uF/50V', (78.74, 101.6), 'VBUS', 'GND', 'U1 VHV decoupling, next to pin 1'),
    R('R1', '56k', (124.46, 101.6), 'CFG1', 'GND', 'CFG1 single-resistor setting: 56k = request 15 V'),
    # ---- run control: converters run only with the 15 V PD contract (PG low) and VBUS above ~11.5 V
    ('Q1', '2N7002', '2N7002', FP('SOT-23'), (73.66, 144.78), {'1': 'PG', '2': 'GND', '3': 'EN'},
     {'LCSC': 'C8545', 'Description': 'holds EN low until the PD contract is made (CH224A PG pulls the gate low)'}),
    R('R2', '100k', (58.42, 132.08), 'VBUS', 'PG', 'Q1 gate pull-up (PG is open drain, 32 V tolerant)'),
    R('R3', '100k', (93.98, 132.08), 'VBUS', 'EN', 'EN/UVLO top: start 11.0 V (TPS56637) / 11.5 V (LMR51430), stop ~10 V'),
    R('R4', '12k', (104.14, 157.48), 'EN', 'GND', 'EN/UVLO bottom'),
    # ---- +5 V: TPS56637, 500 kHz, FCCM (MODE open), Vout = 0.6 x (1 + 75k/10k) = 5.10 V
    ('U2', 'TPS56637', 'TPS56637RPAR', FP('TI_RPA0010A_VQFN-HR-10_3x3mm'), (195.58, 76.2),
     {'8': 'VBUS', '1': 'EN', '7': 'BOOT5', '6': 'SW5', '2': 'FB5', '3': 'GND', '9': 'GND'},   # MODE open = FCCM, PG/NC unused
     {'LCSC': 'C841386', 'Description': 'TI TPS56637 6 A 28 V synchronous buck (D-CAP3), +5 V rail'}),
    C('C2', '10uF/50V', (147.32, 76.2), 'VBUS', 'GND', 'U2 input (1206 50 V keeps ~6 uF at 15 V)'),
    C('C3', '10uF/50V', (157.48, 76.2), 'VBUS', 'GND', 'U2 input'),
    C('C4', '100nF/50V', (167.64, 76.2), 'VBUS', 'GND', 'U2 input HF, right at VIN/PGND'),
    C('C5', '100nF/50V', (220.98, 55.88), 'BOOT5', 'SW5', 'U2 bootstrap'),
    ('L1', 'L', '3.3uH', FP('L_Chilisin_CMLO0650H'), (226.06, 76.2), two('SW5', '5V_BUCK'),
     {'LCSC': 'C439008', 'Description': 'Chilisin CMLO0650H3R3MTT 3.3 uH, 8.5 A rated / 9 A sat, 14 mOhm (TI table: 3.3 uH for 5 V)'}),
    C('C6', '22uF/25V', (246.38, 91.44), '5V_BUCK', 'GND', 'U2 output'),
    C('C7', '22uF/25V', (256.54, 91.44), '5V_BUCK', 'GND', 'U2 output'),
    C('C8', '22uF/25V', (266.7, 91.44), '5V_BUCK', 'GND', 'U2 output'),
    C('C9', '22uF/25V', (276.86, 91.44), '5V_BUCK', 'GND', 'U2 output (4 x 22 uF ~ 40 uF effective at 5 V; TI range 20-100 uF)'),
    R('R5', '75k', (231.14, 104.14), '5V_BUCK', 'FB5', 'FB top: 0.6 x (1 + 75k/10k) = 5.10 V'),
    R('R6', '10k', (231.14, 124.46), 'FB5', 'GND', 'FB bottom'),
    C('C10', '100pF', (213.36, 104.14), '5V_BUCK', 'FF5', 'feed-forward (TI table: 100-220 pF + 20k) for load-step response'),
    R('R7', '20k', (213.36, 124.46), 'FF5', 'FB5', 'feed-forward series resistor'),
    # ---- 5 V eFuse: OVLO 1.2 V x 127/27 = 5.64 V; ILM 560R = 5.95 A typ (5.3 A min); 2.2 nF dVdt ~1 V/ms soft start
    ('U3', 'TPS25947', 'TPS259470ARPWR', FP('TI_RPW0010A_VQFN-10-HR_2x2mm'), (320.04, 76.2),
     {'5': '5V_BUCK', '6': '+5V', '1': 'EF_EN', '2': 'EF_OVLO', '9': 'EF_ILM', '7': 'EF_DVDT', '4': 'FLT', '8': 'GND'},
     {'LCSC': 'C3662799', 'Description': 'TI TPS259470A eFuse: disconnects the Amiga +5 V above 5.64 V, ~6 A current limit, soft start, auto-retry'}),
    R('R8', '100k', (297.18, 104.14), '5V_BUCK', 'EF_EN', 'eFuse EN/UVLO top: on above ~3.75 V'),
    R('R9', '47k', (297.18, 124.46), 'EF_EN', 'GND', 'eFuse EN/UVLO bottom'),
    R('R10', '100k', (307.34, 104.14), '5V_BUCK', 'EF_OVLO', 'eFuse OVLO top: trips at 5.64 V'),
    R('R11', '27k', (307.34, 124.46), 'EF_OVLO', 'GND', 'eFuse OVLO bottom'),
    R('R12', '560R', (342.9, 104.14), 'EF_ILM', 'GND', 'eFuse current limit 560R: ~5.95 A typ, 5.3 A min'),
    C('C11', '2.2nF', (317.5, 109.22), 'EF_DVDT', 'GND', 'eFuse dVdt: ~1 V/ms, limits inrush into the Amiga 5 V bulk caps'),
    C('C12', '22uF/25V', (365.76, 91.44), '+5V', 'GND', '+5 V output'),
    TVS('D1', 'SMF5.0A', 'C19077497', (375.92, 91.44), '+5V', 'GND', 'SMF5.0A TVS (JLC Preferred) on +5 V'),
    R('R13', '1k', (355.6, 124.46), '+5V', 'LED5', '+5 V LED'),
    LED('D2', 'GREEN', 'C2297', (355.6, 139.7), 'LED5', 'GND', '+5 V good, green 0805'),
    R('R14', '1k', (332.74, 124.46), '5V_BUCK', 'LEDF', 'fault LED'),
    LED('D3', 'RED', 'C84256', (332.74, 139.7), 'LEDF', 'FLT', 'eFuse fault (over-voltage / over-current), red 0805'),
    # ---- +12 V: LMR51430 500 kHz, 0.6 x (1 + 100k/5.1k) = 12.36 V
    ('U4', 'LMR51430', 'LMR51430XDDCR', FP('TSOT-23-6'), (195.58, 177.8),
     {'3': 'VBUS', '1': 'GND', '2': 'SW12', '6': 'BOOT12', '4': 'FB12', '5': 'EN'},
     {'LCSC': 'C5185863', 'Description': 'TI LMR51430X 3 A 36 V synchronous buck, 500 kHz, +12 V rail'}),
    C('C13', '10uF/25V', (147.32, 177.8), 'VBUS', 'GND', 'U4 input'),
    C('C14', '10uF/25V', (157.48, 177.8), 'VBUS', 'GND', 'U4 input'),
    C('C15', '100nF/50V', (167.64, 177.8), 'VBUS', 'GND', 'U4 input HF'),
    C('C16', '100nF/50V', (220.98, 160.02), 'BOOT12', 'SW12', 'U4 bootstrap'),
    ('L2', 'L', '12uH', FP('L_FH_FNR8040'), (226.06, 177.8), two('SW12', '+12V'),
     {'LCSC': 'C168128', 'Description': 'Fenghua FNR8040S120MT 12 uH, 3 A rated / 4 A sat, 53 mOhm (TI table: 12 uH for 12 V)'}),
    C('C17', '22uF/25V', (246.38, 193.04), '+12V', 'GND', 'U4 output'),
    C('C18', '22uF/25V', (256.54, 193.04), '+12V', 'GND', 'U4 output'),
    C('C19', '22uF/25V', (266.7, 193.04), '+12V', 'GND', 'U4 output (TI table: 3 x 22 uF)'),
    R('R15', '100k', (231.14, 205.74), '+12V', 'FB12', 'FB top: 12.36 V'),
    R('R16', '5.1k', (231.14, 226.06), 'FB12', 'GND', 'FB bottom'),
    TVS('D4', 'SMF13A', 'C41376087', (276.86, 193.04), '+12V', 'GND', 'SMF13A TVS (JLC Preferred) on +12 V'),
    R('R17', '4.7k', (287.02, 205.74), '+12V', 'LED12', '+12 V LED'),
    LED('D5', 'GREEN', 'C2297', (287.02, 220.98), 'LED12', 'GND', '+12 V good, green 0805'),
    # ---- -12 V: LMR51430 inverting buck-boost from +12 V. IC ground = -12V, inductor to GND.
    #      |Vout| = 0.6 x (1 + 100k/5.1k) = 12.36 V. IC sees +12V - (-12V) = 24.7 V (36 V max).
    ('U5', 'LMR51430', 'LMR51430XDDCR', FP('TSOT-23-6'), (195.58, 241.30),
     {'3': '+12V', '1': '-12V', '2': 'SWN', '6': 'BOOTN', '4': 'FBN', '5': 'ENN'},
     {'LCSC': 'C5185863', 'Description': 'TI LMR51430X as inverting buck-boost: -12 V rail (>1 A capable)'}),
    C('C20', '10uF/50V', (147.32, 241.30), '+12V', '-12V', 'U5 input (VIN to IC ground sees 24.7 V: 50 V part)'),
    C('C21', '10uF/50V', (157.48, 241.30), '+12V', '-12V', 'U5 input'),
    C('C22', '100nF/50V', (167.64, 241.30), '+12V', '-12V', 'U5 input HF'),
    R('R18', '100k', (172.72, 261.62), '+12V', 'ENN', 'U5 EN top (referenced to -12V): on once +12 V is up'),
    R('R19', '20k', (172.72, 276.86), 'ENN', '-12V', 'U5 EN bottom'),
    C('C23', '100nF/50V', (220.98, 223.52), 'BOOTN', 'SWN', 'U5 bootstrap'),
    ('L3', 'L', '12uH', FP('L_FH_FNR8040'), (226.06, 241.30), two('SWN', 'GND'),
     {'LCSC': 'C168128', 'Description': 'Fenghua FNR8040S120MT 12 uH (same part as L2)'}),
    C('C24', '22uF/25V', (246.38, 256.54), 'GND', '-12V', 'U5 output'),
    C('C25', '22uF/25V', (256.54, 256.54), 'GND', '-12V', 'U5 output'),
    C('C26', '22uF/25V', (266.7, 256.54), 'GND', '-12V', 'U5 output'),
    R('R20', '100k', (231.14, 261.62), 'GND', 'FBN', 'FB top (from system GND): -12.36 V'),
    R('R21', '5.1k', (231.14, 276.86), 'FBN', '-12V', 'FB bottom (to IC ground = -12V)'),
    ('D6', 'D_Schottky', 'B5819W', FP('D_SOD-123'), (276.86, 256.54), {'1': 'GND', '2': '-12V'},
     {'LCSC': 'C8598', 'Description': 'keeps the -12 V rail from going positive at start-up / power-down'}),
    TVS('D7', 'SMF13A', 'C41376087', (287.02, 256.54), 'GND', '-12V', 'SMF13A TVS on -12 V'),
    R('R22', '4.7k', (134.62, 261.62), 'LEDN', '-12V', '-12 V LED'),
    LED('D8', 'GREEN', 'C2297', (134.62, 246.38), 'GND', 'LEDN', '-12 V good, green 0805'),
    # ---- Amiga cable: solder pads (ready-made square DIN-5 cable)
    ('J2', 'Conn_01x06', 'AMIGA OUT', FP('WirePads_1x06_P3.81mm_D1.4mm'), (391.16, 177.8),
     {'1': '+5V', '2': '+5V', '3': 'GND', '4': 'GND', '5': '+12V', '6': '-12V'},
     {'Description': 'solder pads for the Amiga DIN cable: 1+2 = +5 V, 3+4 = GND, 5 = +12 V, 6 = -12 V. Hand-soldered, not assembled'}),
]
ROT = {}
items, libsyms = [], {}
netmap = {}


def prop(name, val, x, y, hide=False, just=None):
    p = ['property', Q(name), Q(val), ['at', x, y, 0], ['effects', ['font', ['size', 1.27, 1.27]]]]
    if just:
        p[4].append(['justify', just])
    if hide:
        p[4].append(['hide', 'yes'])
    return p


def symbol_inst(name, ref, value, fp, x, y, rot=0, extra=None, pins=(), inbom=True, refat=None, valat=None, onboard=None):
    extra = dict(extra or {})
    rx, ry, rj = refat or (x + 2.54, y - 5.08, None)
    vx, vy, vj = valat or (x + 2.54, y + 5.08, None)
    s = ['symbol', ['lib_id', Q(LIBNICK + ':' + name)], ['at', x, y, rot], ['unit', 1],
         ['exclude_from_sim', 'no'], ['in_bom', 'yes' if inbom else 'no'],
         ['on_board', 'yes' if (inbom if onboard is None else onboard) else 'no'],
         ['dnp', 'no'], ['uuid', uid()],
         prop('Reference', ref, rx, ry, hide=ref.startswith('#'), just=rj),
         prop('Value', value, vx, vy, just=vj),
         prop('Footprint', fp, x, y, hide=True),
         prop('Datasheet', '', x, y, hide=True),
         prop('Description', extra.pop('Description', ''), x, y, hide=True)]
    for k, v in extra.items():
        s.append(prop(k, v, x, y, hide=True))
    for pn in pins:
        s.append(['pin', Q(pn), ['uuid', uid()]])
    s.append(['instances', ['project', Q(NAME), ['path', Q('/' + ROOT), ['reference', Q(ref)], ['unit', 1]]]])
    return s


def use(name):
    if name not in libsyms:
        libsyms[name] = lib_symbol(name)
    return libsyms[name]


pwr_n = [0]
pwr_ends = []


def power(net, x, y, outdir):
    sym = use(net)
    if net == 'GND':
        rot = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}[outdir]
    else:
        rot = {(0, -1): 0, (-1, 0): 90, (0, 1): 180, (1, 0): 270}[outdir]
    pwr_n[0] += 1
    d = 3.81 if outdir[1] else 5.08
    crowded = any(abs(px - x) < 3.0 and abs(py - y) < 0.1 for px, py in pwr_ends)
    items.append(symbol_inst(net, '#PWR%02d' % pwr_n[0], net, '', x, y, rot, pins=list(pins_of(sym)), inbom=False,
                             valat=(round(x + outdir[0] * d, 2), round(y + outdir[1] * d, 2), None)))
    if crowded:     # neighbouring pin already shows the same rail name
        items[-1][10][4].append(['hide', 'yes'])
    pwr_ends.append((x, y))


def label(net, x, y, outdir):
    rot, just = {(1, 0): (0, 'left'), (-1, 0): (180, 'right'), (0, -1): (90, 'left'), (0, 1): (270, 'right')}[outdir]
    items.append(['label', Q(net), ['at', x, y, rot],
                  ['effects', ['font', ['size', 1.27, 1.27]], ['justify', just, 'bottom']], ['uuid', uid()]])


for ref, name, value, fp, (sx, sy), nets, extra in PARTS:
    sym = use(name)
    pins = pins_of(sym)
    rot = ROT.get(ref, 0)
    def place(px, py):
        a = math.radians(rot)
        return sx + px * math.cos(a) - py * math.sin(a), sy - (px * math.sin(a) + py * math.cos(a))
    P = [place(px, py) for pl in pins.values() for (px, py, _) in pl]
    if all(abs(x - sx) < 0.01 for x, _ in P):       # vertical 2-pin part: text to the right
        refat, valat = (sx + 2.54, sy - 1.27, 'left'), (sx + 2.54, sy + 1.27, 'left')
    else:                                            # text above / below the pin field
        refat = (sx, round(min(y for _, y in P) - 3.81, 2), None)
        valat = (sx, round(max(y for _, y in P) + 3.81, 2), None)
    items.append(symbol_inst(name, ref, value, fp, sx, sy, rot, extra=extra, pins=list(pins), refat=refat, valat=valat,
                             inbom=True, onboard=True))
    for pn, plist in pins.items():
        net = nets.get(pn)
        netmap[(ref, pn)] = net
        seen = set()
        for (px, py, ang) in plist:
            a = math.radians(rot)   # symbol rotation (CCW in lib coords, y up)
            rx, ry = px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a)
            X, Y = round(sx + rx, 4), round(sy - ry, 4)
            if (X, Y) in seen:      # stacked pins (e.g. USB VBUS/GND) share one stub
                continue
            seen.add((X, Y))
            if net is None:
                items.append(['no_connect', ['at', X, Y], ['uuid', uid()]])
                continue
            pa = math.radians(ang + rot)   # pin points inward at `ang`; stub goes outward
            dx, dy = -round(math.cos(pa)), round(math.sin(pa))
            L = 2.54
            if net in PWR and dx:                    # horizontal power stub: clear of labels / neighbours
                L = 7.62
                while any(abs(px - (X + dx * L)) < 0.1 and abs(py - Y) < 3.0 for px, py in pwr_ends):
                    L += 5.08
            ex, ey = round(X + dx * L, 4), round(Y + dy * L, 4)
            items.append(['wire', ['pts', ['xy', X, Y], ['xy', ex, ey]],
                          ['stroke', ['width', 0], ['type', 'default']], ['uuid', uid()]])
            (power if net in PWR else label)(net, ex, ey, (dx, dy))
    for pn in nets:
        assert pn in pins, (ref, pn)

use('PWR_FLAG')
for i, net in enumerate(['VBUS', 'GND', '5V_BUCK', '-12V', '+12V']):   # +5V is driven by U3 OUT
    x, y = 340.36 + i * 10.16, 22.86
    items.append(symbol_inst('PWR_FLAG', '#FLG%02d' % (i + 1), 'PWR_FLAG', '', x, y, 0, pins=['1'], inbom=False,
                             valat=(x, y - 6.35, None)))
    if net in PWR:
        power(net, x, y, (0, 1))
    else:
        items.append(['wire', ['pts', ['xy', x, y], ['xy', x, y + 2.54]],
                      ['stroke', ['width', 0], ['type', 'default']], ['uuid', uid()]])
        label(net, x, y + 2.54, (0, 1))

NOTE = ('Amiga USB-C PD Power Supply v1.0  -  Amiga 500 / 600 / 1200 (and other +5/+12/-12 V machines)\n'
        'Needs a USB-C PD charger that offers 15 V at 3 A (45 W or more). U1 (CH224A) requests 15 V via R1 = 56k.\n'
        'U2/U4 run only while the PD contract holds (PG low -> Q1 off) and VBUS > ~11.5 V (R3/R4).\n'
        '+5 V: U2 TPS56637 -> U3 eFuse (5.64 V OVLO, ~6 A limit): 5 A continuous.  +12 V: U4, 12.36 V.  -12 V: U5 inverting, from +12 V.\n'
        'Budget: 45 W in, about 40 W out, e.g. 5 V 5 A + 12 V 1 A + -12 V 0.2 A.\n'
        'Original design. Spec targets only from Commodore PSU ratings and the SnCMuseum V2 board; no circuitry copied.')
items.append(['text', Q(NOTE), ['exclude_from_sim', 'no'], ['at', 25.4, 22.86, 0],
              ['effects', ['font', ['size', 1.27, 1.27]], ['justify', 'left', 'bottom']], ['uuid', uid()]])

sch = ['kicad_sch', ['version', 20250114], ['generator', Q('eeschema')], ['generator_version', Q('10.0')],
       ['uuid', Q(ROOT)], ['paper', Q('A3')],
       ['title_block', ['title', Q(NAME)], ['date', Q('2026-11-03')], ['rev', Q('1.0')],
        ['comment', 1, Q('USB-C PD 15 V -> Amiga +5 V 5 A (eFuse protected), +12 V, -12 V')]],
       ['lib_symbols'] + [[s[0], Q(LIBNICK + ':' + s[1])] + s[2:] for s in libsyms.values()]] + items + \
      [['sheet_instances', ['path', Q('/'), ['page', Q('1')]]], ['embedded_fonts', 'no']]
open(os.path.join(OUT, NAME + '.kicad_sch'), 'w').write(dump(sch) + '\n')

lib = ['kicad_symbol_lib', ['version', 20241209], ['generator', Q('kicad_symbol_editor')], ['generator_version', Q('10.0')]] + \
      [copy.deepcopy(s) for s in libsyms.values()]
open(os.path.join(OUT, LIBNICK + '.kicad_sym'), 'w').write(dump(lib) + '\n')
json.dump({f'{r}.{p}': n for (r, p), n in netmap.items()}, open(os.path.join(OUT, 'intended_nets.json'), 'w'), indent=0)
print('wrote', len(items), 'items;', len(libsyms), 'symbols')
