"""Price the BOM against JLCPCB's parts API: stock, unit price at the order quantity, Basic / Preferred / Extended.
usage: bom_cost.py <BOM.csv> [boards]"""
import sys, csv, json, urllib.request
Q = int(sys.argv[2]) if len(sys.argv) > 2 else 10
def look(code):
    body = json.dumps({"keyword": code, "currentPage": 1, "pageSize": 5}).encode()
    r = urllib.request.Request("https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList",
                               data=body, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    for c in json.load(urllib.request.urlopen(r, timeout=30))["data"]["componentPageInfo"]["list"] or []:
        if c["componentCode"] == code:
            return c
tot, ext, rows = 0.0, [], []
for row in csv.DictReader(open(sys.argv[1])):
    n = len(row['Designator'].split(','))
    c = look(row['LCSC Part #'])
    if not c:
        print('NOT FOUND', row); continue
    need = n * Q
    price = next((p['productPrice'] for p in c['componentPrices'] if p['startNumber'] <= need <= (p['endNumber'] if p['endNumber'] > 0 else 1e12)), c['componentPrices'][-1]['productPrice'])
    kind = 'Basic' if c['componentLibraryType'] == 'base' else ('Preferred' if c.get('preferredComponentFlag') else 'EXTENDED')
    if kind == 'EXTENDED': ext.append(row['LCSC Part #'])
    tot += price * n
    rows.append((row['Comment'], row['Designator'], row['LCSC Part #'], kind, c['stockCount'], price, price * n))
for r in rows:
    print('%-16s %-28s %-10s %-9s stock %8d  $%.4f  x -> $%.3f' % (r[0][:16], r[1][:28], r[2], r[3], r[4], r[5], r[6]))
print(f'\nparts per board ${tot:.2f} at {Q} boards; extended parts {len(ext)}: {ext}  (JLC ~$3 each per order)')
