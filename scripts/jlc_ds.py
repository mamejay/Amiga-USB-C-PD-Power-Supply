"""Download a part's datasheet via the JLCPCB parts API (signed OSS link). usage: jlc_ds.py <LCSC code> <out.pdf>"""
import json, sys, urllib.request
body = json.dumps({"keyword": sys.argv[1], "currentPage": 1, "pageSize": 3}).encode()
r = urllib.request.Request("https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList",
                           data=body, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
c = json.load(urllib.request.urlopen(r))["data"]["componentPageInfo"]["list"][0]
urllib.request.urlretrieve(c["dataManualFileAccessIdUrl"], sys.argv[2])
