"""Configure this vessel through Blockside admin.py's load/validate/save functions."""
import json
import sys
from pathlib import Path

ROOT=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(ROOT/"src"))
import admin

cfg=admin.load()
ship=next(s for s in cfg["ships"] if s["id"]=="tungning_trader")
ship.update(
    role="merchant",
    names=["東寧三桅洋船"],
    cargoT=260,
    cfg={"speed":1.25,"agile":1.8,"upwind":1.1,"pump":3},
    crew={"officers":2,"helm":1,"top":1,"marines":6,"marineGap":12,"monkeys":2,"handsK":.65,"navigator":1},
    geo={"spar":[48,72],"marines":[55,60],"center":65,"aim":48,"aimZ":[5,290],"deckAim":[8,73],"rigAim":[90,295]},
    gangway=[[204.5,114.5,48.5],[204.5,46.5,48.5]]
)
design=Path(__file__).resolve().parent
hull={(x,y,z):c for x,y,z,c in (map(int,row.split(",")) for row in (design/"hull.vox.txt").read_text().splitlines())}
rim=[]
for x in (122,154,210,235,258,281):
    ys=[y for px,y,z in hull if px==x and z==51]
    rim.extend([[x+.5,min(ys)+.5,52],[x+.5,max(ys)+.5,52]])
ship["floodRim"]=rim
errors=admin.validate(cfg)
if errors:
    raise SystemExit("\n".join(errors))
admin.save(cfg)
print(json.dumps(ship,ensure_ascii=False,indent=2))
