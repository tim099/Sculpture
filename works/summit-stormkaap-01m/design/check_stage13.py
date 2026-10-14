# 階段十三驗收（彈藥庫＋梯子）：只讀引擎的匯出（組裝件 list／parts／obj），跟設計那一側（verify_magazine.json、verify_ladders.json、masks）比。
# 用法：python -I -X utf8 -B check_stage13.py <design> <匯出資料夾（ship_list.txt、parts.json、ship.obj）> <階段十二的 ship_list.txt> [偏移 dx,dy,dz]
#   偏移 ＝ 反向對照：把引擎給的點（parts）、桶的網格（obj）整批平移，該報的要報出來。
# 量的東西：
#   ① 結果帳：組裝件 ＝ 階段十二 ＋ 彈藥庫（frame_at 位移）＋ 梯子 − 船殼缺口（多 0、缺 0、色差 0）
#   ② 部件：彈藥庫關聯 meta（kind／pos／powder_lb）、梯子關聯 meta kind=ladders；固定點 blast／door、<梯>.foot／lo／hi／head（引擎 vs 我算的，最大差）
#   ③ 火藥桶：obj 三角形重心往裡 0.02 落在實心 0、底面正下方是實心的比例
#   ④ 梯子的點：那一格是空氣、正下方是實心、往上 3 格是空氣（引擎的格）
import sys, os, json, re
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D, EX, PREV = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
off = np.array([float(v) for v in sys.argv[4].split(',')]) if len(sys.argv) > 4 else np.zeros(3)
VM = json.load(open(os.path.join(D, 'verify_magazine.json'), encoding='utf-8'))
VL = json.load(open(os.path.join(D, 'verify_ladders.json'), encoding='utf-8'))
rd = lambda p: np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)
out = {}
a = rd(os.path.join(EX, 'ship_list.txt'))
want = {tuple(r[:3]): int(r[3]) for r in rd(os.path.join(PREV, 'ship_list.txt'))}
fa = np.array(VM['frame_at'])
for r in rd(os.path.join(D, VL['stamp_order']['hull'][0]['file'])):                 # 先刻（扶手柱補在被刻掉的唇的位置上 ⇒ 順序要跟落格一樣）
    assert want.pop(tuple(r[:3])) == r[3]
for r in rd(os.path.join(D, VM['stamp_order']['magazine'][0]['file'])): want[tuple(r[:3] + fa)] = int(r[3])
for r in rd(os.path.join(D, VL['stamp_order']['ladders'][0]['file'])): want[tuple(r[:3])] = int(r[3])
got = {tuple(r[:3]): int(r[3]) for r in a}
out['ledger'] = {'engine': len(got), 'want': len(want), 'missing': sum(1 for k in want if k not in got), 'extra': sum(1 for k in got if k not in want),
                 'color_diff': sum(1 for k, v in want.items() if k in got and got[k] != v)}
occ = np.zeros((736, 261, 576), bool); occ[tuple(a[:, :3].T)] = True
PJ = json.load(open(os.path.join(EX, 'parts.json'), encoding='utf-8'))
links = {l['path']: l for l in PJ['links']}
mg = links.get('彈藥庫'); ld = links.get(VL['path'])
out['magazine_meta'] = mg and mg.get('meta'); out['ladders_meta'] = ld and ld.get('meta')
dmax = 0.0
for an in VM['anchors']:
    dmax = max(dmax, float(np.abs(np.array(mg['points'][an['name']]) + off - (np.array(an['world']) + 0.5)).max()))
pts = {}
for lid, P_ in VL['points'].items():
    for k in ('foot', 'lo', 'hi', 'head'):
        e = np.array(ld['points']['%s.%s' % (lid, k)]) + off
        dmax = max(dmax, float(np.abs(e - (np.array(P_[k]) + 0.5)).max()))
        c = tuple(int(np.floor(v)) for v in e)
        pts['%s.%s' % (lid, k)] = {'air': not occ[c], 'floor': bool(occ[c[0], c[1], c[2] - 1]), 'head3': not any(occ[c[0], c[1], c[2] + h] for h in range(1, 4))}
out['anchor_max_diff'] = round(dmax, 4)
out['ladder_points_bad'] = {k: v for k, v in pts.items() if not all(v.values())}
out['ladder_points'] = len(pts)
# ③ 桶
kegs = {m['path']: m for m in PJ['models'] if m['path'].startswith('彈藥庫/桶-')}
out['kegs_in_parts'] = len(kegs)
S = {}; cur = None; Vv = []; F = []; vbase = nv = 0
for l in open(os.path.join(EX, 'ship.obj'), encoding='utf-8'):
    if l.startswith('o '):
        if cur in kegs: S.setdefault(cur, []).append((np.array(Vv), np.array(F) - 1))
        m = re.match(r'o model_\d+ # (.+)', l.strip()); cur = m.group(1) if m else None; Vv = []; F = []; vbase = nv
    elif l.startswith('v '):
        nv += 1
        if cur in kegs:
            x, z, y = map(float, l.split()[1:4]); Vv.append((x, y, z))
    elif l.startswith('f ') and cur in kegs:
        F.append([int(t.split('/')[0]) - vbase for t in l.split()[1:4]])
if cur in kegs: S.setdefault(cur, []).append((np.array(Vv), np.array(F) - 1))
coll, sup = {}, {}
for p, parts in S.items():
    cs, bc = [], []
    zmin = min((v + off)[:, 2].min() for v, _ in parts)
    for v, f in parts:
        v = v + off; A, B_, C = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
        n = np.cross(B_ - A, C - A); ln = np.linalg.norm(n, axis=1, keepdims=True); n = n / np.where(ln > 0, ln, 1)
        cs.append((A + B_ + C) / 3 + 0.02 * n)              # 讀 OBJ 時 y、z 對調 ⇒ 法線朝內（階段十二量過）
        k = (np.abs(v[f][:, :, 2] - zmin) < 0.01).all(1); bc.append(v[f[k]].mean(1))
    i = np.floor(np.vstack(cs)).astype(int); coll[p] = int(occ[i[:, 0], i[:, 1], i[:, 2]].sum())
    j = np.floor(np.vstack(bc)).astype(int); sup[p] = round(float(occ[j[:, 0], j[:, 1], int(round(zmin)) - 1].mean()), 3)
out['keg_meshes'] = len(S); out['keg_collision_total'] = sum(coll.values()); out['keg_support_min'] = min(sup.values()) if sup else None
print(json.dumps(out, ensure_ascii=False, indent=1))
if not off.any():
    with open(os.path.join(D, 'verify_stage13_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(out, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
