# 階段十三 b：梯子五座＋扶手柱＋扶手繩 —— 給遊戲 kind=ladders
# 設計 plan.json ladders（出處 provenance ladders）；從夜隼號 draft_ladders.py（階段十九，它照 basecamp 餘燼號）改：
#   · 現況 ＝ 引擎匯出的組裝件格子（exports/stage12/ship_list.txt）＋ 彈藥庫（masks/magazine，還沒落格）＋ obj 的繩／帆／模型（軟障礙，三角形面上取樣）
#   · 甲板面不用手抄表：那一層甲板（sk_world 的標籤）在那一欄**板色**（plan decks.colors.plank）最上面那一格 ＋ 1 —— 圍板、橫樑不算
#   · 開口：梯子那幾條 y 全部沒有板 ⇒ 開口；有板 → 開口 那條線 ＝ 邊；圍板高度 ＝ 邊外那一欄板上面連著的實心格數
#   · 下一層正下方也有艙口（上下甲板的艙口對齊）⇒ 找梯腳時跳過沒有板的欄（夜隼號是碰到就停）
#   · edges／shape／try_one 其餘照抄（試 dir → band → cap_up，第一個「梯子每格是空的、踏板上方 headroom、梯腳外 landing 是空的、扶手柱與扶手繩不穿東西」的就用）
# 輸出：masks/ladders/ladders.vox.txt（世界座標 ＝ 子作品座標，關聯 at 0,0,0）、verify_ladders.json。重跑逐位元組相同。
# 用法：python -I -X utf8 -B draft_ladders.py <design 資料夾> <匯出資料夾（ship_list.txt、ship_ropes.obj）>
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
D, EX = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
sys.path.insert(0, D)
from sk_world import World

plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
P = plan['ladders']; G, C = P['geometry'], P['colors']; PLANK = plan['decks']['colors']['plank']
w = World(D, with_yards=False); YC = w.YC
NX, NY, NZ = w.lab.shape
a = np.loadtxt(os.path.join(EX, 'ship_list.txt'), delimiter=',', dtype=int, comments='#', ndmin=2)
occ = np.zeros((NX, NY, NZ), bool); occ[tuple(a[:, :3].T)] = True
VM = json.load(open(os.path.join(D, 'verify_magazine.json'), encoding='utf-8'))
fa = np.array(VM['frame_at'])
for r in np.loadtxt(os.path.join(D, VM['stamp_order']['magazine'][0]['file']), delimiter=',', dtype=int, comments='#', ndmin=2):
    occ[tuple(r[:3] + fa)] = True

# ───── 軟障礙：obj 裡的繩、帆、模型（只取每座梯子艙口附近那一段）─────
win = []
for L in P['list']:
    win.append((L['hatch'][0] - 30, L['hatch'][1] + 30))
soft = np.zeros((NX, NY, NZ), bool)
vs, faces, cur = [], [], None
for line in open(os.path.join(EX, 'ship_ropes.obj'), encoding='utf-8'):
    if line.startswith('v '):
        vs.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('o '):
        cur = line.split()[1]
    elif line.startswith('f ') and cur and cur.split('_')[0] in ('rope', 'sail', 'model'):
        faces.append([int(t.split('/')[0]) - 1 for t in line.split()[1:4]])
vs = np.array(vs)[:, [0, 2, 1]]                         # obj 是 y 朝上 ⇒ 換回作品座標
T = vs[np.array(faces)]
keep = np.zeros(len(T), bool)
for x0, x1 in win:
    keep |= (T[:, :, 0].max(1) >= x0) & (T[:, :, 0].min(1) <= x1) & (T[:, :, 2].min(1) <= 160)
T = T[keep]
STEP = 0.25
for t in T:
    p0, p1, p2 = t
    n = int(np.ceil(max(np.linalg.norm(p1 - p0), np.linalg.norm(p2 - p0), np.linalg.norm(p2 - p1)) / STEP)) + 1
    i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing='ij')
    m = (i + j) <= n
    u, v = i[m] / n, j[m] / n
    q = p0 + np.outer(u, p1 - p0) + np.outer(v, p2 - p0)
    k = np.floor(q).astype(int)
    ok = (k[:, 0] >= 0) & (k[:, 0] < NX) & (k[:, 1] >= 0) & (k[:, 1] < NY) & (k[:, 2] >= 0) & (k[:, 2] < NZ)
    k = k[ok]
    soft[k[:, 0], k[:, 1], k[:, 2]] = True
soft &= ~occ
cells, kind = {}, {}


def free(k):
    return not occ[k] and not soft[k] and k not in cells


def surf(deck, x, y):
    """那一層甲板在 (x, y) 的甲板面（板色最上面那一格 ＋ 1）；那一欄沒有板 ⇒ None。"""
    c = w.color[deck][x, y, :]
    zs = np.nonzero(c == PLANK)[0]
    return int(zs.max()) + 1 if len(zs) else None


def edges(L, y0, y1):
    out = []
    for x in range(L['hatch'][0] - 4, L['hatch'][1] + 5):
        col = [surf(L['upper'], x, y) is not None for y in range(y0, y1 + 1)]
        nxt = [surf(L['upper'], x + 1, y) is not None for y in range(y0, y1 + 1)]
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


def try_one(L, d, y0, y1, band, cap_up, eds):
    res = []
    yc = (y0 + y1) // 2
    for xe, _ in [e for e in eds if e[1] == d]:
        zu = surf(L['upper'], xe - d, yc)
        coam = 0
        while occ[xe - d, yc, zu + coam]:
            coam += 1
        zcap = zu + coam - 1 + cap_up
        zl = None
        for guess in range(60):
            z_ = surf(L['lower'], xe + d * guess, yc)
            if z_ is None:
                continue                                                  # 下一層這一欄是艙口 ⇒ 往前找
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
        # 夜隼號：最後三欄的甲板面都要 ＝ zl。船尾、船頭舷弧陡、0.1 m 一階每幾格就一階 ⇒ 放寬到 zl−1..zl
        # （比 zl 高 ⇒ 側板會撞進甲板，下面的碰撞會擋；低一格 ⇒ 側板離地 0.1 m；沒有板 ⇒ 艙口，不准）
        sf = [surf(L['lower'], x, yc) for _, x, _ in cols[-3:]]
        if any(s is None or not (zl - 1 <= s <= zl) for s in sf):
            res.append((xe, '梯腳跨過甲板高低差或艙口 %s' % sf))
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
        carve = []
        if head and L.get('carve_head'):
            # 頭頂只撞到船殼的格 ⇒ 刻缺口（整個梯子寬 y0..y1，撞到的那幾個 (x, z) 每條 y 都刻，缺口才是直的）
            hullc = w.code('hull')
            if all(w.lab[k] == hullc and not soft[k] for k in head):
                # 刻整段唇：梯子那幾欄、y0..y1、梯腳到上一層甲板面 ＋4 之間的船殼格（扶手柱也要穿過去；第一版只刻頭頂那幾格 ⇒ 柱撞到唇比較高的那截）
                carve = sorted((x, y, z) for _, x, _ in cols for y in range(y0, y1 + 1) for z in range(zl, zu + 5) if occ[x, y, z] and w.lab[x, y, z] == hullc)
                if not all(w.lab[k] == hullc for k in carve) or len(carve) > L['carve_head']:
                    res.append((xe, '頭頂要刻 %d 格（上限 %d）或不全是船殼' % (len(carve), L['carve_head'])))
                    continue
                for k in carve: occ[k] = False
                head = []
        if head:
            res.append((xe, '頭頂撞到 %d 格（第一格 %s）' % (len(head), head[0])))
            continue

        def undo():
            for k in carve: occ[k] = True
        land = [(xf + d * k, y, z) for k in range(1, G['landing'] + 1) for y in range(y0, y1 + 1) for z in range(zl, zl + G['headroom'])]
        land = [k for k in land if not free(k)]
        if land:
            res.append((xe, '梯腳外撞到 %d 格（第一格 %s%s）' % (len(land), land[0], '，繩／帆／模型' if soft[land[0]] else '')))
            undo()
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
            undo()
            continue
        tb, hh, allc, tops = got_p
        return dict(xe=xe, d=d, y=[y0, y1], zu=zu, coaming=coam, zcap=zcap, zl=zl, band=band, cap_up=cap_up, R=R, xf=xf,
                    treads=len(treads), cells=allc, tops=tops, post_bot=tb, post_h=hh, carve=carve,
                    tread_cells=sorted(k for k, (c, kd) in got.items() if kd == 'tread')), res
    return None, res


rows, anchors, ropes, notes = [], [], [], []
carved = {}
ecol = {tuple(r[:3]): int(r[3]) for r in a}
for L in P['list']:
    y0, y1 = L['y'] if 'y' in L else (YC - L['dy'], YC + L['dy'])
    eds = edges(L, y0, y1)
    got, why = None, []
    for d in L['dir']:
        for band in G['band']:
            for cap_up in G['cap_up']:
                got, r = try_one(L, d, y0, y1, band, cap_up, eds)
                why += [(d, band, cap_up) + tuple(x) for x in r]
                if got:
                    break
            if got:
                break
        if got:
            break
    if not got:
        notes.append('%s 放不下：%s' % (L['id'], '；'.join('dir %d band %d cap %d x %d %s' % x for x in why[:12]) or '找不到邊（edges %s）' % eds))
        rows.append({'id': L['id'], 'placed': False, 'edges': eds})
        print('✗', L['id'], notes[-1][:600])
        continue
    for k, (c, kd) in got['cells'].items():
        cells[k] = c
        kind[k] = kd
    for k in got['carve']:
        carved[k] = ecol[k]
    for side in ('lo', 'hi'):
        sd = 'P' if side == 'lo' else 'S'
        for which in ('top', 'bot'):
            anchors.append({'name': 'manrope-%s-%s-%s' % (L['id'], sd, which), 'at': list(got['tops'][(side, which)]), 'note': '扶手柱頂（階段十三）'})
        M = P['manrope']
        ropes.append({'name': '梯-%s.manrope-%s' % (L['id'], sd), 'from': '%s/manrope-%s-%s-top' % (P['path'], L['id'], sd),
                      'to': '%s/manrope-%s-%s-bot' % (P['path'], L['id'], sd), 'thickness': M['thickness'], 'slack': M['slack'],
                      'color': M['color'], 'group': M['group']})
    row = {k: got[k] for k in ('xe', 'd', 'y', 'zu', 'coaming', 'zcap', 'zl', 'band', 'cap_up', 'R', 'xf', 'treads', 'post_bot', 'post_h')}
    row['tread_cells'] = [list(k) for k in got['tread_cells']]
    row['post_x'] = [got['tops'][('lo', 'top')][0], got['tops'][('lo', 'bot')][0]]
    row.update(id=L['id'], upper=L['upper'], lower=L['lower'], placed=True, cells=len(got['cells']), carve=len(got['carve']), rise=got['zcap'] - got['zl'] + 1, tried_before=len(why))
    rows.append(row)
    print('✓', L['id'], json.dumps({k: row[k] for k in ('xe', 'd', 'zu', 'coaming', 'zcap', 'zl', 'R', 'xf', 'cells', 'tried_before')}))

v = {'note': 'draft_ladders.py（階段十三 b）—— 現況 ＝ 引擎匯出 exports/stage12（%d 格）＋ 彈藥庫 ＋ obj 的繩／帆／模型' % len(a), 'cells': len(cells), 'by_kind': {}}
for k, kd in kind.items():
    v['by_kind'][kd] = v['by_kind'].get(kd, 0) + 1
v['soft_cells'] = int(soft.sum())
v['overlap_world'] = sum(1 for k in cells if occ[k])
v['overlap_soft'] = sum(1 for k in cells if soft[k])
v['mirror_mismatch'] = sum(1 for (x, y, z), c in cells.items() if cells.get((x, NY - 1 - y, z)) != c)
full = occ.copy()
for k in cells:
    full[k] = True
lab, n = ndimage.label(full, ndimage.generate_binary_structure(3, 1))
# 刻缺口之後浮空的小段（艏樓前緣那幾條飛簷只靠兩端接在舷牆上，缺口把中段切下來）：整塊都是船殼、≤ 50 格 ⇒ 一起刻；其他的浮空 ⇒ 不刻，照實報
v['floating_carved'] = []
if n > 1 and carved:
    sizes = ndimage.sum(full, lab, range(1, n + 1)); main = int(np.argmax(sizes)) + 1
    for i in range(1, n + 1):
        if i == main: continue
        pc = [tuple(int(t) for t in c) for c in np.argwhere(lab == i)]
        if len(pc) <= 50 and all(w.lab[c] == w.code('hull') for c in pc):
            for c in pc:
                carved[c] = ecol[c]; full[c] = False; occ[c] = False
            v['floating_carved'].append({'cells': len(pc), 'x': [min(c[0] for c in pc), max(c[0] for c in pc)], 'y': [min(c[1] for c in pc), max(c[1] for c in pc)], 'z': [min(c[2] for c in pc), max(c[2] for c in pc)]})
    lab, n = ndimage.label(full, ndimage.generate_binary_structure(3, 1))
v['components_after'] = int(n)
# ── 給遊戲的 foot／lo／hi／head（造船規格 §9；規則照 basecamp 餘燼號 design/tools/ladder_points.py）──
#   🩸 她那支挑踏板時不分高度 ⇒ 這艘的 aft（下↔上）與 half（上↔後）在同一段 x 上下疊著，兩座的踏板混在一起（aft 的 hi 落到 z 101）⇒ 自己算、只看自己那座的踏板
HEADR, SCAN, FLAT = 3, 25, 3
points = {}
for r in rows:
    if not r.get('placed'): continue
    yc = (r['y'][0] + r['y'][1]) // 2; d = r['d']; up = -d
    xt, xb = r['post_x']                                                    # 扶手柱頂 top／bot 的 x（她那支從固定點讀）
    xm = (xt + xb) / 2.0
    byz = {}
    for x, y, z in r['tread_cells']:
        if y == yc: byz.setdefault(z, set()).add(x)
    zs_ = sorted(byz)
    tr = lambda z: (min(byz[z], key=lambda x: (abs(x - xm), x)), yc, z + 1)
    lo, hi = tr(zs_[0]), tr(zs_[-1])
    steps = zs_

    def walk(x0_, step, zlo, zhi):
        cols_ = []
        for i in range(1, SCAN + FLAT + 1):
            x = x0_ + step * i
            zz = [z for z in range(zlo, zhi + 1) if full[x, yc, z]]
            cols_.append((x, max(zz) if zz else None))
        for i in range(SCAN):
            run = cols_[i:i + FLAT]; t = run[0][1]
            if t is not None and all(c[1] == t for c in run) and all(not any(full[c[0], yc, t + 1 + h] for h in range(HEADR)) for c in run):
                return (run[0][0], yc, t + 1)
        return None
    foot = walk(lo[0], -up, lo[2] - 15, lo[2])
    head = walk(hi[0], up, hi[2] - 10, hi[2] + 2)
    points[r['id']] = {'foot': list(foot) if foot else None, 'lo': list(lo), 'hi': list(hi), 'head': list(head) if head else None, 'steps': len(steps)}
v['points'] = points
pad = np.pad(~full, 1, constant_values=True)
la, na = ndimage.label(pad, ndimage.generate_binary_structure(3, 1))
v['cavities_after'] = int(na - 1)
v['anchors'] = anchors; v['ropes'] = ropes; v['rows'] = rows; v['notes'] = notes
out = os.path.join(D, 'masks', 'ladders'); os.makedirs(out, exist_ok=True)
NL = chr(10)
rws = sorted((k[0], k[1], k[2], c) for k, c in cells.items())
txt = '# 風暴角號梯子（draft_ladders.py）世界座標 ＝ 子作品座標（關聯 at 0,0,0）x,y,z,color（%d 格）' % len(rws) + NL + ''.join('%d,%d,%d,%d' % r + NL for r in rws)
open(os.path.join(out, 'ladders.vox.txt'), 'w', encoding='utf-8', newline=NL).write(txt)
v['file'] = {'path': 'masks/ladders/ladders.vox.txt', 'cells': len(rws), 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()}
v['work'], v['link_in'], v['link'], v['path'], v['title'] = P['work'], P['link_in'], P['link'], P['path'], P['title']
v['stamp_order'] = {'ladders': [{'name': 'ladders', 'op': 'stampvox', 'file': 'masks/ladders/ladders.vox.txt', 'voxels': len(rws)}]}
crw = sorted((k[0], k[1], k[2], c) for k, c in carved.items())
ctxt = '# 風暴角號 艏樓前緣唇的梯子缺口（draft_ladders.py）—— 從船殼刻掉，x,y,z,原色（%d 格）' % len(crw) + NL + ''.join('%d,%d,%d,%d' % r + NL for r in crw)
open(os.path.join(out, 'hull_carve.vox.txt'), 'w', encoding='utf-8', newline=NL).write(ctxt)
v['stamp_order']['hull'] = [{'name': 'ladder_notch', 'op': 'carvevox', 'work': 'summit-stormkaap-01m', 'file': 'masks/ladders/hull_carve.vox.txt', 'voxels': len(crw),
                             'sha256': hashlib.sha256(ctxt.encode('utf-8')).hexdigest()}]
v['carved'] = len(crw)
v['assembly_expect'] = len(a) + len(rws) - len(crw)
with open(os.path.join(D, 'verify_ladders.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(v, f, ensure_ascii=False, indent=1, sort_keys=True); f.write('\n')
print(json.dumps({k: v[k] for k in ('cells', 'carved', 'assembly_expect', 'by_kind', 'soft_cells', 'overlap_world', 'overlap_soft', 'mirror_mismatch', 'components_after', 'cavities_after')}, ensure_ascii=False))
