# 重量帳：照遊戲的材質比重（Blockside config/game.json materials：一格 0.001 m³）算每個部件幾噸，加上砲（砲種表 mass）與火藥桶，跟史料排水量比。
# 部件 → 材質照 apply_links.py 的關聯 meta（沒寫 ＝ 全船預設橡木）。用法：python -I -X utf8 -B mass.py <gen 輸出> [<Blockside game.json>]
import sys, os, json
import numpy as np
out = sys.argv[1]
gj = sys.argv[2] if len(sys.argv) > 2 else 'D:/Unity/Blocksail/external/Blockside/src/config/game.json'
G = json.load(open(gj, encoding='utf-8'))
MAT = {k: v['density'] for k, v in G['materials']['list'].items()}
MAT.setdefault('iron_hull', (MAT['iron'] + MAT['oak']) / 2)                # 還沒進材質表時照中間值試算
own = np.load(os.path.join(out, 'own.npy'))
names = json.load(open(os.path.join(out, 'own_names.json'), encoding='utf-8'))['names']
HERE = os.path.dirname(os.path.abspath(__file__))
PART_MAT = {'hull': 'iron_hull', 'belt': 'iron', 'barbettes': 'iron', 'barbette-platforms': 'iron', 'armour-deck': 'iron', 'conning': 'iron',
            'funnel-aft': 'iron', 'funnel-fwd': 'iron', 'boilers-aft': 'boiler', 'boilers-fwd': 'boiler', 'engine': 'iron', 'shaft': 'iron', 'screw-s': None, 'screw-p': None, 'rudder': None}
MIRR = ('boilers-aft', 'boilers-fwd', 'engine', 'shaft')
for k in sys.argv[3:]:                                                     # 例：hull-inner=oak（試算）
    a, b = k.split('='); PART_MAT[a] = b
cnt = np.bincount(own.ravel(), minlength=len(names) + 1)
default = G['materials']['default']
print('材質比重（噸／m³）：', {k: MAT[k] for k in MAT})
rows = []
for i, nm in enumerate(names):
    n = int(cnt[i + 1]) * (2 if nm in MIRR else 1)
    if nm in ('screw-s', 'screw-p', 'rudder'): continue                    # 模型（遊戲照模型算：螺旋槳、舵另計）
    m = PART_MAT.get(nm, default)
    rows.append((nm, n, m, n * 0.001 * MAT[m]))
for nm, n in (('turret-main-shell ×2', 30802 * 2), ('turret15-shell ×2', 10810 * 2)):
    rows.append((nm, n, 'iron', n * 0.001 * MAT['iron']))
guns = G['guns']; gt = 4 * guns['krupp305']['mass'] + 2 * guns['krupp150']['mass'] + 8 * guns['hotch37']['mass']
rows.sort(key=lambda r: -r[3])
tot = sum(r[3] for r in rows)
for nm, n, m, t in rows:
    if t >= 5: print('  %-22s %9d 格 %-7s %7.0f t' % (nm, n, m, t))
print('格子合計 %.0f t＋砲 %.0f t ⇒ %.0f t（史料 7,144–7,340 標準；設計水線排水 7,288）' % (tot, gt, tot + gt))
