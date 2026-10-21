# 重量帳：照遊戲的材質比重（Blockside config/game.json materials：一格 0.001 m³）算每個部件幾噸，加上砲（砲種表 mass），跟設計水線排水量比。
# 部件 → 材質照 apply_links.py 的關聯 meta（沒寫 ＝ 全船預設）。照 trailhead 定遠號的 mass.py。
# 用法：python -I -X utf8 -B mass.py <gen 輸出> [<Blockside game.json>] [部件=材質 …]（例 hull=iron*0.2、funnel=iron*0.4 試算；混合寫法同遊戲）
import sys, os, json
import numpy as np
out = sys.argv[1]
gj = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].endswith('.json') else 'D:/Unity/Blocksail/external/Blockside/src/config/game.json'
G = json.load(open(gj, encoding='utf-8'))
MAT = {k: v['density'] for k, v in G['materials']['list'].items()}


class Dens(dict):
    """比重表；混合寫法 `iron*0.15`、`iron*0.5+oak*0.5` 照遊戲 05_material.js matMix：照比例相加，沒寫滿的是空氣。"""
    def __missing__(self, k):
        t = 0.0
        for p in k.split('+'):
            m, _, f = p.partition('*')
            t += (0.0 if m == 'air' else MAT[m]) * (float(f) if f else 1.0)
        return t


MAT = Dens(MAT)
own = np.load(os.path.join(out, 'own.npy'))
names = json.load(open(os.path.join(out, 'own_names.json'), encoding='utf-8'))['names']
default = G['materials']['default']
PART_MAT = {'hull': 'iron*0.15', 'deck-lower': 'iron*0.28', 'mast': 'iron*0.1', 'superstructure': 'iron*0.1', 'vents': 'iron*0.05', 'barbette-posts': 'iron*0.2', 'bulkheads': 'iron*0.1', 'rails': 'iron*0.2', 'ladders': 'iron*0.2', 'conning': 'iron', 'funnel': 'iron', 'boilers': 'boiler', 'engine': 'iron', 'shaft': 'iron', 'barbette': 'iron'}
MIRR = ('boilers', 'engine', 'shaft')
for k in sys.argv[2:]:
    if '=' in k: a, b = k.split('='); PART_MAT[a] = b
cnt = np.bincount(own.ravel(), minlength=len(names) + 1)
rows = []
for i, nm in enumerate(names):
    if nm in ('screw-s', 'screw-p', 'rudder'): continue                    # 模型（遊戲照模型算）
    n = int(cnt[i + 1]) * (2 if nm in MIRR else 1)
    m = PART_MAT.get(nm, default)
    rows.append((nm, n, m, n * 0.001 * MAT[m]))
rows.append(('turret-main-shell', 17035, 'iron', 17035 * 0.001 * MAT['iron']))
g = G['guns']; gt = g['canet320']['mass'] + 12 * g['armstrong120']['mass'] + 6 * g['hotch57']['mass'] + 6 * g['hotch47']['mass'] + 2 * g['hotch37']['mass']
rows.sort(key=lambda r: -r[3])
tot = sum(r[3] for r in rows)
by = {}
for nm, n, m, t in rows:
    by[m] = by.get(m, 0) + t
    if t >= 5: print('  %-20s %9d 格 %-9s %7.0f t' % (nm, n, m, t))
print('材質：' + '、'.join('%s %.0f t' % kv for kv in sorted(by.items(), key=lambda kv: -kv[1])))
print('格子合計 %.0f t＋砲 %.0f t ⇒ %.0f t（設計水線排水 4,330；史料常備排水量 4,278）' % (tot, gt, tot + gt))
