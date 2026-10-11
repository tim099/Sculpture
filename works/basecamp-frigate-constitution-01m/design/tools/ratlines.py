# ratlines（shrouds 之間的橫繩）：照 design/rig_standing.json 的 shrouds 幾何算 ⇒ design/ratlines.json（給 ropes_apply.py）
# 用法：python -I ratlines.py <design 資料夾>
#   · lower shrouds：每根桅每一舷，從 deadeye 頂上 start 格起、每 step 格一道，到桅頂（hounds）下 stop 格為止；
#     每一道從最前面那根 shroud 拉到最後面那根（shrouds 從一排 deadeye 收到同一個點，大致在一個面上 ⇒ 橫線會貼著中間每一根過）
#   · topmast shrouds：top 邊緣 → topmast head，同樣做法
#   · 端點是連續座標（格心 ＝ i + 0.5）；CLI 的端點整數 ＝ 格心、帶小數照原值 ⇒ 一律寫成帶小數（剛好整數的加 0.001）
#   · shrouds 是拉直的（slack 1）⇒ 線上的點直接內插；shrouds 改了就重跑這支
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
    lows = [min(a[2], b[2]) for a, b, _ in lst]
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
        ropes.append({'name': '%s-%sratline-%s%02d' % (mast, 'tm' if kind == 'topmast' else '', sd, k), 'from': fmt(p), 'to': fmt(q),
                      'thickness': C['thickness'], 'slack': CFG['slack'], 'color': CFG['color'], 'group': '%s ratlines' % kind})
        z += C['step']
    summary['%s %s %s' % (mast, kind, sd)] = {'rungs': sum(1 for r in ropes if r['name'].startswith('%s-%sratline-%s' % (mast, 'tm' if kind == 'topmast' else '', sd))), 'z': [float(round(z0, 1)), float(round(z1, 1))], 'shrouds': len(lst), 'span_first': fmt(at_z(*fwd[:2], z0)), 'span_last_aft': fmt(at_z(*aft[:2], z0))}
json.dump({'note': 'ratlines：端點是連續座標（從 rig_standing.json 的 shrouds 內插，CLI 帶小數照原值）；shrouds 改了就重跑 tools/ratlines.py', 'config': CFG, 'summary': summary, 'ropes': ropes},
          open(os.path.join(D, 'ratlines.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print('ratlines', len(ropes))
for k, v in summary.items():
    print(k, v['rungs'], v['z'], v['shrouds'])
