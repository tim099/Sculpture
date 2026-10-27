# 澤漢號 步驟 11（TASK-0966）；出處 calli-cosecha-01m/design/tools/check_stage95.py（中線改讀 plan）。
# 階段九半（TASK-0619）讀數：舵與錨 —— 一律從作品讀（子作品匯出、anchors.json、models.json、CLI `work sub=models`、組裝件匯出）
#   ① 結果帳：舵、錨架子作品 vs 清單
#   ② 舵：組裝件的舵模型 kind=rudder、鉸鏈 meta 齊、舵子作品有 stock-top、stock-top 8 格內有船殼（遊戲 10_ship.js anchorNear 8）；舵的格子跟組裝件零碰撞；
#      轉 ±max_deg（繞鉸鏈軸）時掃進組裝件實心的格數（資訊：遊戲轉舵不做格子碰撞）
#   ③ 錨：kind=anchor、來源有 ring；撞實心 0；腳（外框中心往下 12 格內第一格實心）是錨架；船殼有 hawse-S／P、各在那一舷、落在船殼格上
#   用法：python -I -X utf8 tools/check_stage95.py <design> [--drop=stock-top｜<錨名>｜hawse-S]（反向對照：讀完作品之後當作那一件沒有）
import json, os, re, subprocess, sys, math
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
YCP = json.load(open(os.path.join(sys.argv[1], 'plan.json'), encoding='utf-8'))['space']['yc']      # 拉貝爾號：中線讀 plan（收穫號寫死 160）
design = sys.argv[1]
drop = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--drop=')), None)
sys.path.insert(0, design)
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list, key
from gunsim import Grid, Gun
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
RB = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['rudder_anchor_build']
RU, AN = RB['rudder'], RB['anchor']
HULL, ASM = 'abigail-fluyt-01m', 'abigail-fluyt-01m-assembly'

for w, f in ((RU['work'], 'rudder'), (AN['gear_work'], 'anchor_gear')):
    W = export_list(w, None)
    D = np.loadtxt(os.path.join(design, 'masks', 'rudder', f + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    cw, cd = dict(zip(key(W).tolist(), W[:, 3].tolist())), dict(zip(key(D).tolist(), D[:, 3].tolist()))
    print('① %-30s 作品 %5d、設計 %5d、缺 %d、多 %d、色差 %d' % (w, len(cw), len(cd), len(set(cd) - set(cw)), len(set(cw) - set(cd)), sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])))


def anchors_of(w):
    p = os.path.join(WORKS, w, 'anchors.json')
    return {a['name']: a['at'] for a in json.load(open(p, encoding='utf-8'))['anchors']} if os.path.exists(p) else {}


def models_of(w):
    return {m['name']: m for m in json.load(open(os.path.join(WORKS, w, 'models.json'), encoding='utf-8'))['models']}


def cli_status(w):
    out = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=models', '--arg', 'work=' + w], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
    return {m.group(2).split('/')[-1]: m.group(3) for m in (re.match(r'- (\S) `([^`]+)`［(\w+)］', l) for l in out.splitlines()) if m}


A = export_list(ASM, None, links=None)
G = Grid(A, outside=False)
problems = []
# ② 舵
rud = [m for m in models_of(ASM).values() if (m.get('meta') or {}).get('kind') == 'rudder']
ra = anchors_of(RU['work'])
if drop == 'stock-top':
    ra.pop('stock-top', None)
st = cli_status(ASM)
print('② 舵模型 %d：%s；CLI 狀態 %s' % (len(rud), [m['name'] for m in rud], [st.get(m['name']) for m in rud]))
if not rud:
    problems.append('沒有 kind=rudder 的模型')
for m in rud:
    me = m['meta']
    miss = [k for k in ('hinge_x', 'hinge_y', 'hinge_z', 'axis_x', 'axis_y', 'axis_z', 'max_deg', 'turn_axis') if k not in me]
    if miss:
        problems.append('舵 meta 缺 %s' % miss)
    if 'stock-top' not in ra:
        problems.append('舵子作品沒有固定點 stock-top（遊戲：沒有 hinge 就開局就掉；有 hinge 走退路）')
    else:
        s = ra['stock-top']
        near = min((abs(x - s[0]) + abs(y - s[1]) + abs(z - s[2]), (x, y, z)) for x in range(s[0] - 8, s[0] + 9) for y in range(s[1] - 8, s[1] + 9)
                   for z in range(s[2] - 8, s[2] + 9) if G.solid(x, y, z))
        print('   stock-top %s：8 格內最近的船格 %s（曼哈頓 %d）' % (s, near[1], near[0]))
    cells = export_list(m['work'], None)[:, :3].astype(float)
    same = np.allclose(m['at'], m['pivot']) and np.allclose(m['scale'], 1) and np.allclose(m['rotate'], 0) and not m['mirror']
    hits = int(G.hit(cells + 0.5).sum())
    print('   舵的格 %d 格（at ＝ pivot、scale 1、不轉：%s）；跟組裝件重疊 %d；鉸鏈 (%s,%s,%s) 軸 (%s,%s,%s)、max_deg %s' % (
        len(cells), same, hits, me.get('hinge_x'), me.get('hinge_y'), me.get('hinge_z'), me.get('axis_x'), me.get('axis_y'), me.get('axis_z'), me.get('max_deg')))
    if hits or not same:
        problems.append('舵的格跟組裝件重疊 %d／變換不是原樣' % hits)
    h = np.array([me['hinge_x'], me['hinge_y'], me['hinge_z']], float)
    ax = np.array([me['axis_x'], me['axis_y'], me['axis_z']], float)
    ax /= np.linalg.norm(ax)
    for sgn in (1, -1):
        th = math.radians(sgn * float(me['max_deg']))
        q = cells + 0.5 - h
        rot = q * math.cos(th) + np.cross(ax, q) * math.sin(th) + np.outer(q @ ax, ax) * (1 - math.cos(th))
        print('   轉 %+d°：掃進組裝件實心 %d 格（資訊）' % (sgn * me['max_deg'], int(G.hit(rot + h).sum())))
# ③ 錨
gm = models_of(AN['gear_work'])
if drop in gm:
    gm[drop] = dict(gm[drop], meta={k: v for k, v in gm[drop]['meta'].items() if k != 'kind'})
anc = {n: m for n, m in gm.items() if (m.get('meta') or {}).get('kind') == 'anchor'}
gs = cli_status(AN['gear_work'])
gear = set(map(tuple, export_list(AN['gear_work'], None)[:, :3].tolist()))
print('③ 錨（kind=anchor）%d：%s；CLI 狀態 %s；沒有 kind 的模型 %s' % (len(anc), sorted(anc), [gs.get(n) for n in sorted(anc)], sorted(set(gm) - set(anc))))
for side in ('S', 'P'):
    if not any((m['at'][1] - (YCP + 0.5)) * (1 if side == 'S' else -1) > 0 for m in anc.values()):
        problems.append('%s 舷沒有 kind=anchor 的錨' % side)
cache = {}
for n, m in sorted(anc.items()):
    if m['work'] not in cache:
        cache[m['work']] = export_list(m['work'], None)
    g = Gun(n, {'work': m['work'], 'scale': m['scale'][0], 'pivot': m['pivot'], 'meta': {}}, cache[m['work']], {}, 0.2)
    k = int(G.hit(g.world(g.samples, m['at'], m['rotate'][2], m['mirror'] == 'y')).sum())
    lo, hi = g.bbox(m['at'], m['rotate'][2], m['mirror'] == 'y')
    cx, cy, fz = int(math.floor((lo[0] + hi[0]) / 2)), int(math.floor((lo[1] + hi[1]) / 2)), int(math.floor(lo[2])) - 1
    gap = next((d for d in range(0, 13) if G.solid(cx, cy, fz - d)), None)
    ring = 'ring' in anchors_of(m['work'])
    print('   %s：撞實心 %d、腳 %s（%s）、來源有 ring %s' % (n, k, gap, '錨架' if gap is not None and (cx, cy, fz - gap) in gear else '不是錨架', ring))
    if k or gap is None or not ring:
        problems.append('%s 撞 %d／腳 %s／ring %s' % (n, k, gap, ring))
ha = anchors_of(HULL)
if drop and drop.startswith('hawse'):
    ha.pop(drop, None)
H = Grid(export_list(HULL, None), outside=False)
for nm in ('hawse-S', 'hawse-P'):
    a = ha.get(nm)
    ok = a is not None and H.solid(*a) and (a[1] - YCP) * (1 if nm.endswith('S') else -1) > 0
    print('   %s %s：在船殼格上、在那一舷 %s' % (nm, a, ok))
    if not ok:
        problems.append('%s 沒有／不在船殼上' % nm)
print('問題 %d %s' % (len(problems), problems))
