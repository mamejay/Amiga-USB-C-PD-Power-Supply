"""JLC-friendly net classes in the .kicad_pro (board.Save resets them). Power 0.5 mm for the converter
input/switch/output nets (solid copper zones are added after routing by pours.py), GND not routed (pours).
usage: set_netclasses.py <project dir>"""
import sys, json, glob
pro = glob.glob(sys.argv[1] + '/*.kicad_pro')[0]
j = json.load(open(pro))
ns = j.setdefault('net_settings', {})
base = next(c for c in ns['classes'] if c['name'] == 'Default')
base.update(track_width=0.25, clearance=0.15, via_diameter=0.6, via_drill=0.3)
pw = dict(base, name='Power', track_width=0.5, clearance=0.2, via_diameter=0.8, via_drill=0.4, priority=0)
gnd = dict(base, name='GND', track_width=0.4, clearance=0.2, via_diameter=0.8, via_drill=0.4, priority=1)
ns['classes'] = [base, pw, gnd]
ns['netclass_patterns'] = [{'netclass': 'Power', 'pattern': p} for p in
                           ('VBUS', '/SW5', '/5V_BUCK', '+5V', '/SW12', '+12V', '/SWN', '-12V')] + [{'netclass': 'GND', 'pattern': 'GND'}]
json.dump(j, open(pro, 'w'), indent=2)
print('net classes:', [c['name'] for c in ns['classes']])
