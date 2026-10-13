# 階段十三：砲 —— 4 磅長砲一件子作品（0.05 m／格）＋ 12 門外部模型的擺放（退到零碰撞）
# 設計 plan.json guns（出處在 provenance guns.*）；砲門 plan.json decks.ports（階段四已開）。
# 子作品座標（同憲法號 -gun-24／long18 的慣例）：x ＝ 砲的寬（沿船長，軸在 AX 那一格的格心）、y ＝ 砲身方向（砲口 +y）、z 0 ＝ 甲板面上第一層。
# 擺法（Shipbuilding §4.2）：x 對準砲門中線（再試 ±0.5、±1），y 從舷牆外面往裡退（每步 0.5 格），
#   退到模型每一格的格心＋八個角都不在現況（nf_state stage12，全部子作品）的實心格裡 ⇒ 那就是推得最出去的位置；再要求砲口在船殼外。
#   S 舷照原樣（砲口 +y）、P 舷 mirror=y（繞 pivot 翻 ⇒ 砲口 −y；eye-aft 仍在船尾側）。pivot ＝ 砲架前緣中間、甲板面那一層。
# 輸出：masks/guns/gun4.vox.txt（stampvox 清單，at 0,0,0）、verify_guns.json（子作品、固定點、12 門的 at／meta、讀數）、sheet13_guns_v1.png
# 用法：python -I -X utf8 -B draft_guns.py <design 資料夾>
import sys, os, json, math
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(__file__))
sys.path.insert(0, D)
from nf_state import state_after, occupancy

plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
G = plan['guns']
C = G['carriage']
COL = G['colors']
W_, L_, H_ = G['size']
AX, AZ, YB = G['AX'], G['AZ'], G['yb']


class Part:
    def __init__(s):
        s.cells = {}

    def put(s, x, y, z, c, over=False):
        if not (0 <= x < W_ and 0 <= y < L_ and 0 <= z < H_):
            raise ValueError(('框外', x, y, z))
        if (x, y, z) in s.cells and not over:
            return
        s.cells[(x, y, z)] = c

    def box(s, x0, x1, y0, y1, z0, z1, c, over=False):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    s.put(x, y, z, c, over)

    def tube(s, y0, prof, c, bore_r=0.0, bore_depth=0.0):
        """沿 y 的旋轉體（同 draft_guns2.py）：prof ＝ [(s, r), …] 分段；格心落在半徑內就放；砲口那一段挖空。"""
        smax = prof[-1][0]
        for y in range(L_):
            t = y + 0.5 - y0
            if not (0 <= t < smax):
                continue
            r = None
            for (a, ra), (b, rb) in zip(prof, prof[1:]):
                if a <= t < b:
                    r = ra + (rb - ra) * (t - a) / (b - a) if b > a else rb
                    break
            if r is None:
                continue
            R = int(math.ceil(r)) + 1
            for dx in range(-R, R + 1):
                for dz in range(-R, R + 1):
                    d = math.hypot(dx, dz)
                    if d <= r + 1e-9:
                        if bore_r > 0 and t > smax - bore_depth and d <= bore_r:
                            continue
                        s.put(AX + dx, y, AZ + dz, c)

    def wheel(s, cx, cy, cz, r, c):
        """輪子：輪面在 yz、沿 y 滾，一格厚（x ＝ cx 那一欄）。"""
        for y in range(L_):
            for z in range(H_):
                if math.hypot(y + 0.5 - cy, z + 0.5 - cz) <= r:
                    s.put(cx, y, z, c, True)


def build():
    P = Part()
    prof = [tuple(v) for v in G['profile']]
    assert abs(prof[-1][0] - G['barrel_len']) < 1e-9
    P.tube(YB, prof, COL['barrel'], G['bore_r'], G['bore_depth'])
    P.tube(YB - 2, [(0, 1.0), (2.0, 1.0)], COL['barrel'])                 # cascabel 頸
    P.tube(YB - 4, [(0, 1.5), (2.0, 1.5)], COL['barrel'])                 # cascabel 鈕
    TY = YB + G['trunnion_from_base']
    YF = TY + C['front_from_trunnion']
    YR = YF - C['len'] + 1
    k0, k1 = C['cheek_x']
    steps = [tuple(v) for v in C['cheek_steps']]
    a0, a1, abot = C['arch']
    for k in range(k0, k1 + 1):                                           # cheek（兩片、2 格厚）
        for sg in (-1, 1):
            x = AX + sg * k
            for y in range(YR, YF + 1):
                back = YF - y
                top = [h for b0, h in steps if back >= b0][-1]
                bot = abot if a0 <= back <= a1 else C['cheek_bottom']
                for z in range(bot, top + 1):
                    P.put(x, y, z, COL['carriage'])
            P.put(x, TY, AZ + 1, COL['iron'], True)                       # cap square（壓住耳軸）
    for k in range(-k1, k1 + 1):                                          # 耳軸：沿 x 穿過兩片 cheek
        P.put(AX + k, TY, AZ, COL['barrel'], True)
    yf = YF - C['axle_front_back']
    yr = YR + C['axle_rear_fwd']
    for ya, r in ((yf, C['wheel_front_r']), (yr, C['wheel_rear_r'])):
        P.box(AX - k1 - 1, AX + k1 + 1, ya, ya, 2, C['cheek_bottom'] - 1, COL['carriage'])   # 軸木（接到 cheek 底）
        for sg in (-1, 1):
            P.wheel(AX + sg * (k1 + 1), ya + 0.5, r, r, COL['barrel'])
            P.put(AX + sg * (k1 + 2), ya, 2, COL['iron'], True)           # 輪軸頭
    P.box(AX - k0 + 1, AX + k0 - 1, YR, YR + 9, C['cheek_bottom'], C['cheek_bottom'], COL['carriage'])   # 床板
    P.box(AX - 2, AX + 2, YR + 1, YR + 6, C['cheek_bottom'] + 1, AZ - 3, COL['quoin'])                 # quoin
    P.box(AX - k0 + 1, AX + k0 - 1, YF - 1, YF, C['cheek_bottom'], C['cheek_bottom'] + 3, COL['carriage'])  # 前 transom
    pts = {'muzzle': (AX, YB + G['barrel_len'] - 1, AZ), 'breech': (AX, YB, AZ), 'cascabel': (AX, YB - 4, AZ),
           'train': (AX, YR, C['cheek_bottom']), 'trunnion': (AX, TY, AZ),
           'eye-aft': (AX - k1 - 1, YF - 10, 8), 'eye-fwd': (AX + k1 + 1, YF - 10, 8)}
    return P, pts, YF


def components(cells):
    S = set(cells); seen = set(); n = 0
    for c in S:
        if c in seen:
            continue
        n += 1; st = [c]; seen.add(c)
        while st:
            x, y, z = st.pop()
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                q = (x + d[0], y + d[1], z + d[2])
                if q in S and q not in seen:
                    seen.add(q); st.append(q)
    return n


def main():
    P, pts, YF = build()
    path = os.path.join(D, 'masks', 'guns', 'gun4.vox.txt')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 夜隼號 4 磅長砲＋truck carriage（draft_guns.py，0.05 m）x,y,z,color —— at 0,0,0\n')
        for (x, y, z), c in sorted(P.cells.items()):
            f.write(f'{x},{y},{z},{c}\n')
    asym = sum(1 for (x, y, z), c in P.cells.items() if P.cells.get((2 * AX - x, y, z)) != c)
    ncomp = components(P.cells)
    cnt = {}
    for c in P.cells.values():
        cnt[c] = cnt.get(c, 0) + 1
    assert (pts['muzzle'] not in P.cells), '砲口那一格應該是挖空的'
    print('gun4', len(P.cells), cnt, 'asym', asym, 'components', ncomp)

    # ── 擺放 ──
    W = state_after(D, 'stage12')
    occ = occupancy(W)
    M, H = W['main'], W['hull']
    S = G['scale']
    pivot = np.array([AX + 0.5, YF + 1.0, 0.0])
    cells = np.array(sorted(P.cells), float)
    offs = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
    samp = (cells[:, None, :] + offs[None]).reshape(-1, 3)
    muzzle = np.array(pts['muzzle'], float) + 0.5

    def place(Q, at, side):
        q = (Q - pivot) * S
        if side < 0:
            q[:, 1] = -q[:, 1]
        return q + np.asarray(at)

    def hit(Wp):
        i = np.floor(Wp).astype(int)
        ok = (i[:, 0] >= 0) & (i[:, 0] < occ.shape[0]) & (i[:, 1] >= 0) & (i[:, 1] < occ.shape[1]) & (i[:, 2] >= 0) & (i[:, 2] < occ.shape[2])
        h = np.ones(len(Wp), bool)                         # 框外當撞（不准伸出組裝件的框）
        h[ok] = occ[i[ok, 0], i[ok, 1], i[ok, 2]]
        return h

    bot = cells[cells[:, 2] == 0]
    bsamp = np.array([[x + ox, y + oy, 0.0] for x, y, _ in bot for ox in (0.3, 0.7) for oy in (0.3, 0.7)])

    def support(at, side):
        """輪子底面（子作品 z 0 那一層）每格四個取樣點，正下方那一格（世界）是實心的有幾個。"""
        Wp = place(bsamp, at, side)
        i = np.floor(Wp).astype(int)
        return [int(occ[i[:, 0], i[:, 1], i[:, 2] - 1].sum()), len(Wp)]

    pr = plan['decks']['ports']
    rows = []
    for n, st in enumerate(pr['stations'], 1):
        x0 = st + pr['x_from_station']
        x1 = x0 + pr['width'] - 1
        xc = (x0 + x1 + 1) / 2.0
        for side, nm in ((1, 'S'), (-1, 'P')):
            ys = range(81, 161) if side > 0 else range(79, -1, -1)
            # 甲板面：砲腳下那一段（x0..x1、離中線 10 格到舷牆）甲板子作品的最高格 ＋ 1
            dz = [int(np.nonzero(M[x, y, :])[0].max()) for x in range(x0, x1 + 1) for y in ys if M[x, y, :].any() and abs(y - 80) >= 10]
            deck_top = max(dz)
            z_open = (deck_top + 1 + pr['sill'], deck_top + pr['sill'] + pr['height'])
            # 開口：x0..x1、z_open 範圍裡船殼一格都沒有；舷牆外面 ＝ 開口下緣那一列（sill）船殼最外那一格的外面
            sill_row = [y for y in ys if H[int(xc), y, z_open[0] - 1]]
            outer = (max(sill_row) + 1) if side > 0 else min(sill_row)
            inner = (min(sill_row)) if side > 0 else (max(sill_row) + 1)
            ylo, yhi = min(sill_row), max(sill_row)
            hull_open = int((H[x0:x1 + 1, ylo:yhi + 1, z_open[0]:z_open[1] + 1] > 0).sum())
            tops = sorted({int(np.nonzero(M[x, y, :])[0].max()) for x in range(int(xc) - 6, int(xc) + 7) for y in ys
                           if M[x, y, :].any() and abs(y - 80) >= 10})
            tops = [t for t in tops if deck_top - 2 <= t <= deck_top]
            best = None
            for dx in G['search']['dx']:
                for t in tops:
                    for kb in range(int(G['search']['max_back'] / G['search']['step']) + 1):
                        back = kb * G['search']['step']
                        at = (xc + dx, outer - side * back, float(t + 1))
                        if hit(place(samp, at, side)).any():
                            continue
                        tip = place(muzzle[None], at, side)[0]
                        sup = support(at, side)
                        cand = {'n': n, 'side': nm, 'station': st, 'at': [round(at[0], 3), round(at[1], 3), at[2]], 'dx': dx, 'back_from_outer': back,
                                'muzzle_beyond_outer': round(float((tip[1] - outer) * side), 3), 'axis_z': round(float(tip[2]), 3),
                                'wheel_support': sup, 'opening_x': [x0, x1], 'opening_z': list(z_open), 'hull_in_opening': hull_open,
                                'deck_top': deck_top, 'wall_y': [inner, outer]}
                        # 排序：四輪全著地 ＞ 砲口伸出船殼外 ≥ 1 格 ＞ 置中（|dx| 小）＞ 推得出去（back 小）
                        key = (sup[0] < sup[1], cand['muzzle_beyond_outer'] < G['search']['min_muzzle_out'], abs(dx), back)
                        if best is None or key < best[0]:
                            best = (key, cand)
                        break
            best = best[1] if best else None
            if best is None:
                raise SystemExit(f'砲門 {n}{nm} 退到 {G["search"]["max_back"]} 格還塞不進去')
            name = f'砲-{nm}{n}'
            best.update({'model': name, 'mirror': 'y' if side < 0 else 'none',
                         'meta': {'kind': 'gun', 'gun': G['kind'], 'side': nm, 'port': n, 'deck': 'cabin' if n <= 2 else 'main'}})
            rows.append(best)
            print(name, json.dumps({k: best[k] for k in ('at', 'dx', 'back_from_outer', 'muzzle_beyond_outer', 'axis_z', 'opening_z', 'hull_in_opening', 'deck_top')}))

    out = {'note': 'draft_guns.py（階段十三）—— 子作品 gun4 與 12 門模型的擺放；現況 nf_state stage12（全部子作品）',
           'gun': {'work': G['work'], 'file': 'masks/guns/gun4.vox.txt', 'size': G['size'], 'mpv': G['mpv'], 'cells': len(P.cells),
                   'colors': {str(k): v for k, v in sorted(cnt.items())}, 'asym': asym, 'components': ncomp,
                   'anchors': {k: list(v) for k, v in pts.items()}, 'pivot': pivot.tolist()},
           'host': 'summit-night-falcon-01m-deck-main', 'scale': S, 'rows': rows}
    with open(os.path.join(D, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
