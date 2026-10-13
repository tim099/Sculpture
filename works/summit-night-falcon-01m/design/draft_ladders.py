# 階段十九：梯子三座（後甲板 companion ↔ 艙房、斷口兩舷 主甲板 ↔ 後甲板）＋扶手柱＋扶手繩 —— 給遊戲 kind=ladders
# 設計 plan.json ladders（出處 provenance ladders.*）；現況 nf_state stage18（格）＋組裝件 obj 的繩、帆、模型（軟障礙）。
#   找位置與梯子形狀照 basecamp 餘燼號 design/draft_ladders.py 的 edges／shape／try_one（她照憲法號的）：
#   上端頂在上一層的邊（艙口邊／斷口），往 dir 斜下到下一層；試 dir → band → cap_up，第一個
#   「梯子每格是空的、踏板上方 headroom、梯腳外 landing 是空的、扶手柱與扶手繩不穿東西」的就用。
#   改的地方：① 甲板面、邊從 plan.ladders 讀；② 障礙 ＝ 格 ∪ obj 的繩／帆／模型（三角形面上取樣，⛔ 不只看頂點）；
#             ③ 扶手柱下那根的位置多試 R−2、R−1（斷口只高 1 m，梯子只有 5 欄）；④ 鏡像 y ↔ 160 − y。
# 輸出：masks/ladders/ladders.vox.txt（世界座標 ＝ 子作品座標，關聯 at 0,0,0）、verify_ladders.json、sheet19_ladders_v1.png
# 用法：python -I -X utf8 -B draft_ladders.py <design 資料夾> <組裝件 obj（階段十八之後的現況）>
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from nf_state import state_after, occupancy, NX, NY, NZ

plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
P = plan['ladders']
G, C = P['geometry'], P['colors']
ASM_VOXELS = 96756                     # 階段十八 v2 之後的組裝件（引擎 stats／export 讀數）
W = state_after(D, 'stage18')
occ = occupancy(W)
assert int(occ.sum()) == ASM_VOXELS, ('設計那一側的現況格數對不上組裝件', int(occ.sum()))

# ───── 軟障礙：obj 裡的繩、帆、模型（只取 x 80..175、z 15..70 這一段）─────
XR, ZR = (80, 175), (15, 70)
soft = np.zeros((NX, NY, NZ), bool)
vs, faces, cur = [], [], None
for line in open(sys.argv[2], encoding='utf-8'):
    if line.startswith('v '):
        vs.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('o '):
        cur = line.split()[1]
    elif line.startswith('f ') and cur and cur.split('_')[0] in ('rope', 'sail', 'model'):
        faces.append([int(t.split('/')[0]) - 1 for t in line.split()[1:4]])
vs = np.array(vs)[:, [0, 2, 1]]                         # obj 是 y 朝上 ⇒ (x, 作品 z, 作品 y) 換回作品座標
F = np.array(faces)
T = vs[F]                                               # (n, 3, 3)
keep = ((T[:, :, 0].max(1) >= XR[0]) & (T[:, :, 0].min(1) <= XR[1]) & (T[:, :, 2].max(1) >= ZR[0]) & (T[:, :, 2].min(1) <= ZR[1]))
T = T[keep]
STEP = 0.25
for t in T:
    a, b, c = t
    n = int(np.ceil(max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b)) / STEP)) + 1
    i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing='ij')
    m = (i + j) <= n
    u, v = i[m] / n, j[m] / n
    p = a + np.outer(u, b - a) + np.outer(v, c - a)
    k = np.floor(p).astype(int)
    ok = (k[:, 0] >= 0) & (k[:, 0] < NX) & (k[:, 1] >= 0) & (k[:, 1] < NY) & (k[:, 2] >= 0) & (k[:, 2] < NZ)
    k = k[ok]
    soft[k[:, 0], k[:, 1], k[:, 2]] = True
soft &= ~occ
cells, kind = {}, {}


def free(k):
    return not occ[k] and not soft[k] and k not in cells


def dz(deck, x):
    for a, b, z in P['surfaces'][deck]:
        if (a is None or x >= a) and (b is None or x < b):
            return z
    return None


# 甲板面表對一次現況（梯子那條 y 中線、表裡每一段的每個 x，有板的地方 板頂 ＋ 1 要 ＝ 表）
surf_check = []
for L in P['list']:
    yc = (L['y'][0] + L['y'][1]) // 2
    for deck in (P['edges'][L['edge']]['upper'], L['lower']):
        lo, hi = {'quarter': (36, 45), 'cabin': (18, 28), 'main': (26, 35)}[deck]
        for a, b, z in P['surfaces'][deck]:
            for x in range(a if a is not None else 95, b):
                zs = np.nonzero(occ[x, yc, lo:hi])[0]
                if len(zs) and zs.max() + lo + 1 != z and not (P['edges']['companion']['x'][0] - 1 <= x <= P['edges']['companion']['x'][1] + 1):
                    surf_check.append((L['id'], deck, x, int(zs.max() + lo + 1), z))
assert not surf_check, ('甲板面表跟現況對不上', surf_check[:8])


# ───── 以下三段照餘燼號 draft_ladders.py（她照憲法號）─────
def edges(E, y0, y1):
    x0, x1 = E['x']
    zm = dz(E['upper'], (x0 + x1) // 2)
    zp = (zm if zm is not None else dz(E['upper'], x0 - 1)) - 1     # 斷口：中段在主甲板上方（上一層沒有板）⇒ 取斷口後面那一欄
    out = []
    for x in range(x0 - 1, x1 + 2):
        col = [occ[x, y, zp] for y in range(y0, y1 + 1)]
        nxt = [occ[x + 1, y, zp] for y in range(y0, y1 + 1)]
        if all(col) and not any(nxt):
            out.append((x + 1, 1))
        if not any(col) and all(nxt):
            out.append((x, -1))
    return out


def shape(xe, d, y0, y1, zcap, zl, band):
    slope = G['rise'] / G['run']
    got, t, cols = {}, 0, []
    while True:
        zs = int(np.floor(zcap - slope * t))
        lo = max(zl, zs - band + 1)
        x = xe + d * t
        for y in (y0, y1):
            for z in range(lo, zs + 1):
                got[(x, y, z)] = (C['stringer'], 'stringer')
        cols.append((t, x, zs))
        if zs - band + 1 <= zl:
            break
        t += 1
        if t > 60:
            return None, None, None
    R = t + 1
    j, treads = 0, []
    while True:
        zt = zcap - G['rise'] * j - 3
        if zt < zl + 2:
            break
        for tt in (G['run'] * j + 1, G['run'] * j + 2):
            if tt >= R:
                continue
            for y in range(y0 + 1, y1):
                got[(xe + d * tt, y, zt)] = (C['tread'], 'tread')
        treads.append(zt)
        j += 1
    return got, cols, treads


def try_one(L, E, d, y0, y1, band, cap_up, eds):
    res = []
    for xe, _ in [e for e in eds if e[1] == d]:
        zu = dz(E['upper'], xe if dz(E['upper'], xe) is not None else xe - d)
        zcap = zu + P['coaming'][E['coaming']] - 1 + cap_up
        zl = None
        for guess in range(40):
            z_ = dz(L['lower'], xe + d * guess)
            if z_ is None:
                break
            if zcap - 1.5 * guess - band + 1 <= z_:
                zl = z_
                break
        if zl is None:
            res.append((xe, '下一層在這裡沒有甲板'))
            continue
        got, cols, treads = shape(xe, d, y0, y1, zcap, zl, band)
        if got is None:
            res.append((xe, '太長'))
            continue
        xf = cols[-1][1]
        if any(dz(L['lower'], x) != zl for _, x, _ in cols[-3:]):
            res.append((xe, '梯腳跨過甲板高低差'))
            continue
        bad = [k for k in got if not free(k)]
        if bad:
            res.append((xe, '梯子撞到 %d 格（第一格 %s%s）' % (len(bad), bad[0], '，繩／帆／模型' if soft[bad[0]] else '')))
            continue
        if not all(occ[xf, y, zl - 1] for y in (y0, y1)):
            res.append((xe, '梯腳底下不是甲板'))
            continue
        head = [(x, y, z) for t, x, zs in cols for y in range(y0 + 1, y1) for z in range(zs + 1, min(zs + 1 + G['headroom'], zu))
                if (x, y, z) not in got and not free((x, y, z))]
        if head:
            res.append((xe, '頭頂撞到 %d 格（第一格 %s）' % (len(head), head[0])))
            continue
        land = [(xf + d * k, y, z) for k in range(1, G['landing'] + 1) for y in range(y0, y1 + 1) for z in range(zl, zl + G['headroom'])]
        land = [k for k in land if not free(k)]
        if land:
            res.append((xe, '梯腳外撞到 %d 格（第一格 %s）' % (len(land), land[0])))
            continue
        R = len(cols)
        got_p = None
        for tb in (R - 3, R - 4, R - 5, R - 2, R - 1):
            if tb - 1 < G['post_gap_min']:
                continue
            for hh in (G['stanchion_h'], G['stanchion_h'] - 1, G['stanchion_h'] - 2):
                posts, tops, okp = {}, {}, True
                for side, y in (('lo', y0), ('hi', y1)):
                    for which, t in (('top', 1), ('bot', tb)):
                        _, x, zs = cols[t]
                        for z in range(zs + 1, zs + 1 + hh):
                            if not free((x, y, z)) or (x, y, z) in got:
                                okp = False
                            posts[(x, y, z)] = (C['iron'], 'stanchion')
                        tops[(side, which)] = (x, y, zs + hh)
                if not okp:
                    continue
                allc = dict(got)
                allc.update(posts)
                rope_bad = []
                for side in ('lo', 'hi'):
                    a_, b_ = np.array(tops[(side, 'top')]) + 0.5, np.array(tops[(side, 'bot')]) + 0.5
                    for tt in np.linspace(0, 1, int(np.linalg.norm(b_ - a_) * 3) + 2):
                        q = tuple(int(np.floor(v)) for v in a_ + (b_ - a_) * tt)
                        if q not in allc and not free(q):
                            rope_bad.append(q)
                if not rope_bad:
                    got_p = (tb, hh, allc, tops)
                    break
            if got_p:
                break
        if not got_p:
            res.append((xe, '扶手柱或扶手繩放不下'))
            continue
        tb, hh, allc, tops = got_p
        return dict(xe=xe, d=d, y=[y0, y1], zcap=zcap, zl=zl, band=band, cap_up=cap_up, R=R, xf=xf,
                    treads=len(treads), cells=allc, tops=tops, post_bot=tb, post_h=hh), res
    return None, res
# ───── 照抄到這裡 ─────


rows, anchors, ropes, notes = [], [], [], []
for L in P['list']:
    E = dict(P['edges'][L['edge']])
    y0, y1 = L['y']
    eds = edges(E, y0, y1)
    got, why = None, []
    for d in L['dir']:
        for band in G['band']:
            for cap_up in G['cap_up']:
                got, r = try_one(L, E, d, y0, y1, band, cap_up, eds)
                why += [(d, band, cap_up) + tuple(w) for w in r]
                if got:
                    break
            if got:
                break
        if got:
            break
    if not got:
        notes.append('%s 放不下：%s' % (L['id'], '；'.join('dir %d band %d cap %d x %d %s' % w for w in why) or '找不到邊（edges %s）' % eds))
        rows.append({'id': L['id'], 'placed': False, 'edges': eds})
        continue
    for k, (c, kd) in got['cells'].items():
        cells[k] = c
        kind[k] = kd
    for side in ('lo', 'hi'):
        sd = 'P' if side == 'lo' else 'S'
        for which in ('top', 'bot'):
            anchors.append({'name': 'manrope-%s-%s-%s' % (L['id'], sd, which), 'at': list(got['tops'][(side, which)]), 'note': '扶手柱頂（階段十九）'})
        M = P['manrope']
        ropes.append({'name': '梯-%s.manrope-%s' % (L['id'], sd), 'from': '%s/manrope-%s-%s-top' % (P['path'], L['id'], sd),
                      'to': '%s/manrope-%s-%s-bot' % (P['path'], L['id'], sd), 'thickness': M['thickness'], 'slack': M['slack'],
                      'color': M['color'], 'group': M['group']})
    row = {k: got[k] for k in ('xe', 'd', 'y', 'zcap', 'zl', 'band', 'cap_up', 'R', 'xf', 'treads', 'post_bot', 'post_h')}
    row.update(id=L['id'], placed=True, cells=len(got['cells']), rise=got['zcap'] - got['zl'] + 1, tried_before=len(why))
    rows.append(row)

# ───── 驗（設計那一側）─────
v = {'note': 'draft_ladders.py（階段十九）—— 現況 nf_state stage18 ＋ 組裝件 obj 的繩／帆／模型', 'cells': len(cells), 'by_kind': {}}
for k, kd in kind.items():
    v['by_kind'][kd] = v['by_kind'].get(kd, 0) + 1
v['soft_cells_in_window'] = int(soft.sum())
v['overlap_world'] = sum(1 for k in cells if occ[k])
v['overlap_soft'] = sum(1 for k in cells if soft[k])
v['mirror_mismatch'] = sum(1 for (x, y, z), c in cells.items() if cells.get((x, 160 - y, z)) != c)
full = occ.copy()
for k in cells:
    full[k] = True
lab, n = ndimage.label(full, ndimage.generate_binary_structure(3, 1))
v['components_after'] = int(n)
pad = np.pad(~full, 1, constant_values=True)
la, na = ndimage.label(pad, ndimage.generate_binary_structure(3, 1))
v['cavities_after'] = int(na - 1)
v['assembly_expect'] = ASM_VOXELS + len(cells)
v['anchors'] = anchors
v['ropes'] = ropes
v['rows'] = rows
v['notes'] = notes

out = os.path.join(D, 'masks', 'ladders')
os.makedirs(out, exist_ok=True)
p = os.path.join(out, 'ladders.vox.txt')
rws = sorted((k[0], k[1], k[2], c) for k, c in cells.items())
open(p, 'w', encoding='utf-8', newline='\n').write('# 夜隼號梯子（draft_ladders.py）世界座標 ＝ 子作品座標（關聯 at 0,0,0）x,y,z,color（%d 格）\n' % len(rws)
                                                + '\n'.join('%d,%d,%d,%d' % r for r in rws) + '\n')
v['file'] = {'path': 'masks/ladders/ladders.vox.txt', 'cells': len(rws), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
v['work'], v['link_in'], v['link'], v['path'], v['title'] = P['work'], P['link_in'], P['link'], P['path'], P['title']
v['stamp_order'] = {'ladders': [{'name': 'ladders', 'op': 'stampvox', 'file': 'masks/ladders/ladders.vox.txt', 'voxels': len(rws)}]}

# 圖紙：上 ＝ 側面（companion 那條 y 76..84 疊起來）、下 ＝ 俯視（z 22..52）
x0, x1, z0, z1, sc = 95, 160, 15, 60, 6
im = Image.new('RGB', ((x1 - x0) * sc + 40, (z1 - z0) * sc + 70 + 161 * 3 + 40), (250, 249, 244))
dr = ImageDraw.Draw(im)
dr.text((20, 14), '夜隼號 新圖紙 19 v1：梯子（上：y 56..104 側面；下：俯視 x %d..%d；灰 ＝ 現況、淡藍 ＝ 繩帆模型、彩 ＝ 梯子）' % (x0, x1), fill=(30, 30, 30), font=ImageFont.truetype(r'C:\Windows\Fonts\msjh.ttc', 13))
pal = {C['stringer']: (150, 105, 60), C['tread']: (215, 180, 120), C['iron']: (60, 60, 70)}
side_o = occ[x0:x1, 56:105, z0:z1].any(axis=1)
side_s = soft[x0:x1, 56:105, z0:z1].any(axis=1)
for x in range(x1 - x0):
    for z in range(z1 - z0):
        col = (205, 205, 205) if side_o[x, z] else ((190, 215, 235) if side_s[x, z] else None)
        if col:
            dr.rectangle([20 + x * sc, 50 + (z1 - z0 - 1 - z) * sc, 20 + x * sc + sc - 1, 50 + (z1 - z0 - 1 - z) * sc + sc - 1], fill=col)
for (x, y, z), c in cells.items():
    if x0 <= x < x1 and z0 <= z < z1:
        dr.rectangle([20 + (x - x0) * sc, 50 + (z1 - 1 - z) * sc, 20 + (x - x0) * sc + sc - 1, 50 + (z1 - 1 - z) * sc + sc - 1], fill=pal[c])
oy = 50 + (z1 - z0) * sc + 30
top_o = occ[x0:x1, :, 22:52].any(axis=2)
for x in range(x1 - x0):
    for y in range(161):
        if top_o[x, y]:
            dr.rectangle([20 + x * sc, oy + (160 - y) * 3, 20 + x * sc + sc - 1, oy + (160 - y) * 3 + 2], fill=(205, 205, 205))
for (x, y, z), c in cells.items():
    if x0 <= x < x1:
        dr.rectangle([20 + (x - x0) * sc, oy + (160 - y) * 3, 20 + (x - x0) * sc + sc - 1, oy + (160 - y) * 3 + 2], fill=pal[c])
im.save(os.path.join(D, 'sheet19_ladders_v1.png'))

json.dump(v, open(os.path.join(D, 'verify_ladders.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(json.dumps({k: v[k] for k in v if k not in ('anchors', 'ropes', 'stamp_order')}, ensure_ascii=False, indent=1))
