# ratlines（shrouds 之間的橫繩）：照 design/rig_standing.json 的 shrouds 幾何算 ⇒ design/ratlines.json（給 ropes_apply.py）
# 用法：python -I ratlines.py <design 資料夾>
#   · lower shrouds：每根桅每一舷，從 deadeye 頂上 start 格起、每 step 格一道，到桅頂（hounds）下 stop 格為止；
#     每一道從最前面那根 shroud 拉到最後面那根（shrouds 從一排 deadeye 收到同一個點，大致在一個面上 ⇒ 橫線會貼著中間每一根過）
#   · topmast shrouds：top 邊緣 → topmast head，同樣做法
#   · 端點是**子繩**（TASK-0511）：`rope:<shroud>/比例` —— 掛在兩根 shroud 上，shroud 動 ratline 跟著動（不再是掛在虛空的座標）
#     比例照 shroud **現在真正的**兩端算：lower shrouds 的下端是上 deadeye 頂（design/rig_deadeyes.json），topmast shrouds 照固定點
#   · shrouds 是拉直的（slack 1）⇒ 比例 ＝ (z − 下端 z)／(上端 z − 下端 z)；橫線的高度（z）照舊由 rig_standing.json 的 shrouds 幾何定
import sys, os, json
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
RS = json.load(open(os.path.join(D, 'rig_standing.json'), encoding='utf-8'))
YC = 160
CFG = {'min_span': 5,                               # 一道短於這個就不畫（topmast shrouds 收到同一點，最上面幾道只剩一兩格，像一顆點）
       'lower': {'start': 7, 'stop': 16, 'step': 4, 'thickness': 0.3},
       'topmast': {'start': 4, 'stop': 10, 'step': 4, 'thickness': 0.25},
       'color': '#2b2620', 'slack': 1.0}

W = {}
for a in RS['anchors']:
    c = np.array(a['world'], float) + 0.5
    W[a['link'] + '/' + a['name']] = c
    if a['link'] == 'channels':                     # 鏡像那一舷：格 y ↔ 320 − y ⇒ 連續座標 y ↔ 321 − y
        W['channels-鏡像/' + a['name']] = np.array([c[0], 2 * YC + 1 - c[1], c[2]])
# lower shrouds 現在的下端（rig_deadeyes.py 改成上 deadeye 頂的座標；CLI 帶小數照原值）
ACT = {r['name']: np.array([float(v) for v in r['from'].split(',')]) for r in json.load(open(os.path.join(D, 'rig_deadeyes.json'), encoding='utf-8'))['ropes']
       if r['from'].count(',') == 2 and ('-shroud-' in r['name']) and '.' not in r['name']}


def fmt(p):
    out = []
    for v in p:
        v = round(float(v), 3)
        if v == int(v):
            v += 0.001
        out.append('%.3f' % v)
    return ','.join(out)


def at_z(a, b, z):
    t = (z - a[2]) / (b[2] - a[2])
    return a + (b - a) * t


def on_shroud(sh, z):
    """shroud（拉直）上高度 z 那一點的比例：0 ＝ 繩的 from、1 ＝ to；from 用現在真正的下端（lower shrouds ＝ 上 deadeye 頂）。"""
    F, T = ACT.get(sh[2], sh[0]), sh[1]
    return (z - F[2]) / (T[2] - F[2])


ropes = []
summary = {}
groups = {}
for r in RS['ropes']:
    g = r['group']
    if g not in ('lower shrouds', 'topmast shrouds'):
        continue
    name = r['name']                                  # e.g. main-shroud-S3 / main-tmshroud-P2
    mast, kind, sd = name.split('-')[0], ('lower' if g == 'lower shrouds' else 'topmast'), name.rsplit('-', 1)[1][0]
    groups.setdefault((mast, kind, sd), []).append((W[r['from']], W[r['to']], name))
for (mast, kind, sd), lst in sorted(groups.items()):
    C = CFG[kind]
    lows = [min(ACT.get(n, a)[2], b[2]) for a, b, n in lst]   # 現在真正的下端（上 deadeye 頂）往上 start 格起 —— ⛔ 不從下 deadeye 起算（會跟上 deadeye、lanyard 擠在一起）
    highs = [max(a[2], b[2]) for a, b, _ in lst]
    z0, z1 = max(lows) + C['start'], min(highs) - C['stop']
    # 最前面、最後面那兩根（照下端的 x）
    lst = sorted(lst, key=lambda t: (t[0] if t[0][2] < t[1][2] else t[1])[0])
    fwd, aft = lst[-1], lst[0]
    k = 0
    z = z0
    while z <= z1:
        p = at_z(*fwd[:2], z)
        q = at_z(*aft[:2], z)
        if np.linalg.norm(p - q) < CFG['min_span']:
            break
        k += 1
        tf, ta = on_shroud(fwd, z), on_shroud(aft, z)
        if not (0 <= tf <= 1 and 0 <= ta <= 1):
            raise SystemExit('%s %s %s 第 %d 道：比例超出 0..1（%.4f, %.4f）—— shroud 現在的兩端跟 rig_standing 的差太多，先查' % (mast, kind, sd, k, tf, ta))
        ropes.append({'name': '%s-%sratline-%s%02d' % (mast, 'tm' if kind == 'topmast' else '', sd, k), 'from': 'rope:%s/%.6f' % (fwd[2], tf), 'to': 'rope:%s/%.6f' % (aft[2], ta),
                      'thickness': C['thickness'], 'slack': CFG['slack'], 'color': CFG['color'], 'group': '%s ratlines（子繩，掛在 shrouds 上）' % kind})
        z += C['step']
    summary['%s %s %s' % (mast, kind, sd)] = {'rungs': sum(1 for r in ropes if r['name'].startswith('%s-%sratline-%s' % (mast, 'tm' if kind == 'topmast' else '', sd))), 'z': [float(round(z0, 1)), float(round(z1, 1))], 'shrouds': len(lst), 'span_first': fmt(at_z(*fwd[:2], z0)), 'span_last_aft': fmt(at_z(*aft[:2], z0))}
json.dump({'note': 'ratlines：子繩（TASK-0511）rope:<shroud>/比例，掛在最前與最後那根 shroud 上；shroud 動 ratline 跟著動。shroud 的下端換了（rig_deadeyes）比例會偏 ⇒ 重跑本支', 'config': CFG, 'summary': summary, 'ropes': ropes},
          open(os.path.join(D, 'ratlines.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print('ratlines', len(ropes))
for k, v in summary.items():
    print(k, v['rungs'], v['z'], v['shrouds'])
