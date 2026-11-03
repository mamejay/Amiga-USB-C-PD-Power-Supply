"""Report JLCPCB 'PCBA Type' (Economic and Standard / Standard only) for every LCSC part in a BOM.
usage: pcba_type.py <BOM.csv>"""
import sys, csv, json, re, urllib.request
def api(code):
    body = json.dumps({"keyword": code, "currentPage": 1, "pageSize": 5}).encode()
    r = urllib.request.Request("https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList",
                               data=body, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    return next(c for c in json.load(urllib.request.urlopen(r, timeout=30))["data"]["componentPageInfo"]["list"] if c["componentCode"] == code)
for row in csv.DictReader(open(sys.argv[1])):
    code = row['LCSC Part #']; c = api(code)
    html = urllib.request.urlopen(urllib.request.Request(f"https://jlcpcb.com/partdetail/{c['urlSuffix']}", headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode('utf-8', 'ignore')
    m = re.search(r'PCBA Type</dt>.*?<span[^>]*>([^<]+)</span>', html, re.S)
    print('%-10s %-22s %-16s %s' % (code, c['componentModelEn'][:22], row['Designator'][:16], m.group(1) if m else '??'))
