# 重量帳：照遊戲的材質比重（Blockside config/game.json materials：一格 0.001 m³）算每個部件幾噸，加上砲（砲種表 mass），跟設計水線排水量比。
# 部件 → 材質照 apply_links.py 的關聯 meta（沒寫 ＝ 全船預設）。照 trailhead 定遠號的 mass.py。
# 用法：python -I -X utf8 -B mass.py <gen 輸出> [<Blockside game.json>] [部件=材質 …]（例 hull=iron_hull、deck-lower=iron_hull 試算）
import sys, os, json
import numpy as np
out = sys.argv[1]
gj = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].endswith('.json') else 'D:/Unity/Blocksail/external/Blockside/src/config/game.json'
G = json.load(open(gj, encoding='utf-8'))
MAT = {k: v['density'] for k, v in G['materials']['list'].items()}
own = np.load(os.path.join(out, 'own.npy'))
names = json.load(open(os.path.join(out, 'own_names.json'), encoding='utf-8'))['names']
default = G['materials']['default']
PART_MAT = {'deck-lower': 'iron_hull', 'conning': 'iron', 'funnel': 'iron', 'boilers': 'boiler', 'engine': 'iron', 'shaft': 'iron', 'barbette': 'iron'}
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
