# 量尺：直接從格子（gen_dingyuan 的 own.npy）量主尺寸與幾個部件的位置，跟 plan.json 的設計值比；--shift=dx ⇒ 量之前把整艘往 +x 挪 dx 格（反向對照：尺要報 dx）。
# 用法：python -I -X utf8 -B verify.py <gen 輸出> [--shift=3]
import sys, os, json
import numpy as np

out = sys.argv[1]
shift = int(next((a.split('=')[1] for a in sys.argv[2:] if a.startswith('--shift=')), 0))
HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))['params']
own = np.load(os.path.join(out, 'own.npy'))
names = json.load(open(os.path.join(out, 'own_names.json'), encoding='utf-8'))['names']
if shift: own = np.roll(own, shift, axis=0)
NX, NY, NZ = own.shape; YC = (NY - 1) // 2; ZW = P['z_waterline']


def part(nm): return own == names.index(nm) + 1


hull = part('hull') | part('belt')
rows = []


def row(nm, got, want, unit='格'):
    rows.append((nm, got, want, got - want))


xs = np.nonzero(hull.any((1, 2)))[0]
row('船尾（甲板）x', int(xs.min()), P['x_stern_deck'])
row('衝角尖 x', int(xs.max()), P['ram_tip'][0])
zr = np.nonzero(hull[P['ram_tip'][0]].any(0))[0] if hull[P['ram_tip'][0]].any() else [-1]
row('衝角尖 z', int(np.mean(zr)) if len(zr) else -1, P['ram_tip'][1])
ys = np.nonzero(hull[:, :, ZW].any(0))[0]
row('水線寬（格）', int(ys.max() - ys.min() + 1), int(2 * int(P['half_beam']) + 1))
for b in P['barbettes']:
    ring = part('barbettes')[:, :, P['barbette_z'][0] + 2]
    yy = np.arange(NY)[None, :]; sel = (yy - YC) * np.sign(b['dy']) > 0
    pts = np.argwhere(ring & sel)
    row('露砲台-%s 中心 x' % b['name'], round(float(pts[:, 0].mean()), 2), b['x'] + 0.0)
    row('露砲台-%s 中心 y' % b['name'], round(float(pts[:, 1].mean()), 2), YC + b['dy'] + 0.0)
for f in P['funnels']:
    fm = part('funnel-' + f['name'])
    fx = np.nonzero(fm[:, :, P['z_main_deck'] + 1:].any((1, 2)))[0]          # 甲板以上那一段（甲板下有沿中線的煙箱那一欄）
    row('煙囪-%s 中心 x' % f['name'], round(float((fx.min() + fx.max()) / 2), 1), f['x'] + 0.0)
    row('煙囪-%s 頂 z' % f['name'], int(np.nonzero(fm.any((0, 1)))[0].max()), P['funnel_top'])
for m in P['masts']:
    mm = part('mast-' + m['name'])[:, :, m['top_z'] - 20]
    row('%s桅 x' % m['name'], round(float(np.argwhere(mm)[:, 0].mean()), 2), m['x'] + 0.0)
bm = part('belt'); bx = np.nonzero(bm.any((1, 2)))[0]
row('裝甲帶前後 x0', int(bx.min()), P['citadel'][0]); row('裝甲帶前後 x1', int(bx.max()), P['citadel'][1])
w = max(len(r[0]) for r in rows)
bad = 0
for nm, got, want, d in rows:
    flag = '✓' if abs(d) <= 0.6 else '✗'
    bad += flag == '✗'
    print('%s %-*s 量 %-8s 設計 %-8s 差 %+g' % (flag, w, nm, got, want, round(d, 2)))
print('shift=%d：✗ %d／%d' % (shift, bad, len(rows)))
