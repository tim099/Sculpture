# 砲門蓋板（TASK-0736；Tim 2026-10-19：「另外參考光榮號 把妳的船都加上炮門吧 GO」）—— 照光榮號 kaguya-gloire-01m/design/draft_portlids.py（kaguya，TASK-0719）改，造船規格 §9.12。
#   夜隼號、風暴角號用同一支（兩份檔只差最上面的 CFG）；跟光榮號不一樣的地方：
#   · 砲門清單照各船的 verify_guns.json（砲的擺法讀數裡記著開口），砲照組裝件裡那一層甲板的 models.json（meta.id ⇒ lid_of；⛔ 不照位置猜）。
#   · 外表面照引擎匯出的**船殼作品本身**（export format=list，不帶關聯；砲門已刻穿）—— 光榮號照 masks/build，我的兩艘沒有那一份。
#   · 除了兩舷，也做船尾的砲門（砲口朝 −x）：同一套擬合換一個軸（側向 ＝ y、往外 ＝ −x；rotate z ＝ 90 ＋ rz）。船頭大嘴（風暴角號 chase）不做：那是船首像的嘴，不是砲門。
#   · 一種尺寸＋顏色一件子作品（規格 §9.12「一件子作品掛 N 次」；夜隼號一件、風暴角號下層／上層各一件，船尾跟下層同尺寸同色就共用）。
#   · 顏色照船殼：外層 ＝ 開口那一圈船殼最外那一格最多的顏色、內層 ＝ 那一圈最裡面那一格最多的顏色；鉸鏈板 ＝ 砲的 iron 色（plan.json guns.colors.iron）。
#   擺法（同光榮號）：畫開著（x 沿鉸鏈、y 0 ＝ 鉸鏈那一排、往 +y 往外、z 0 ＝ 關上貼船殼那一層）；pivot ＝ 鉸鏈那條邊的正中間；
#     at ＝（側向：開口中間、往外：鉸鏈那一排外表面外第一格空氣、z：開口上緣 ＋1）；S 舷 rotate rz、P 舷 180 − rz（⛔ mirror=y）、船尾 90 ＋ rz；
#     rz ＝ 外表面沿側向的斜度（平面擬合；|rz| ≤ 2° 取 0 ⇒ 共用網格）、close_deg ＝ 90 ＋ 外表面沿 z 的斜度；house ＝ max(ceil(砲口退到外表面往裡 1 格要拉幾格), 4)。
#   輸出：masks/portlids/<件>.txt（子作品自己的座標，stampvox at 0,0,0）、portlids_placement.json。碰撞讀數另外由 check_portlids.py 量。重跑逐位元組相同。
#   用法：python -I -X utf8 -B draft_portlids.py <design> <船殼匯出清單 hull.txt> <組裝件 links=all 匯出清單 asm.txt>
#     （外表面擬合照船殼；開著碰不碰、關上落進多少照組裝件 —— 遊戲的 hullG 是整艘的格子：夜隼號 4 號擦到的那條黑色不在船殼作品裡，只照船殼量 0、遊戲量 8%）
import sys, os, json, math, hashlib
import numpy as np

CFG = {
    'ship': '夜隼號', 'hull': 'summit-night-falcon-01m', 'frame': (384, 161, 320), 'YC': 80,
    'rows': {'main': {'suffix': 'portlid', 'top': 1, 'thick': 2}},   # 砲的 row ⇒ 子作品後綴、蓋板上緣比開口多蓋幾排（1 ＝ 每邊大一格，照 §9.12）、厚幾格
}

RZ_FLAT = 2.0
SOLID_MAX = 4.0                              # 關上落進船殼（照遊戲的量法）的上限 %：遊戲匯入檢查 > 5% 報 ⚠，我的取樣跟它差 1 個百分點左右（夜隼號 1 號：我 9.1%、遊戲 8%）⇒ 留 1% 餘量
CLOSE_TRY = 8.0                              # 超過 ⇒ close_deg 往小調最多 8°（每 0.5°；蓋板還貼著船殼）；不夠才把鉸鏈往外挪一格
HOUSE_MIN, HOUSE_MAX = 4, 6                  # 最少 4（開火也看得到後座）；⛔ 不超過 6：砲班站位有一個人在砲外框後面 6 格（Blockside 40_crew.js；光榮號同）


def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], 1)


def r1(v, k=1):
    v = round(float(v), k)
    return int(v) if v == int(v) else v


def mode(vals):
    c = {}
    for v in vals:
        c[v] = c.get(v, 0) + 1
    return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def lid_surface(W, H, T, step=0.4, d=0.25):
    """蓋板網格表面的取樣點（同 Blockside 62_ports.js portPts：表面每 0.4 格一點、往實心那邊挪 0.25 格、邊上往裡 0.02）—— 蓋板是實心的長方體，表面 ＝ 六個面。"""
    P = []
    L = (W, H, T)
    for ax in range(3):
        a, b = [i for i in range(3) if i != ax]
        na, nb = max(1, math.ceil(L[a] / step)), max(1, math.ceil(L[b] / step))
        for val, inw in ((0, 1), (L[ax], -1)):
            for i in range(na + 1):
                for j in range(nb + 1):
                    q = [0.0, 0.0, 0.0]
                    q[ax] = val + inw * d
                    q[a] = min(max(i * L[a] / na, 0.02), L[a] - 0.02)
                    q[b] = min(max(j * L[b] / nb, 0.02), L[b] - 0.02)
                    P.append(q)
    return np.array(P, float)


def turn(P, c, k, deg):
    """繞過 c、方向 k 的軸照右手定則轉 deg 度（Rodrigues；同 check_portlids.py、62_ports.js portMat）。"""
    k = k / np.linalg.norm(k)
    t = math.radians(deg)
    v = P - c
    return c + v * math.cos(t) + np.cross(k, v) * math.sin(t) + np.outer(v @ k, k) * (1 - math.cos(t))


def ports(design, works):
    """(model, row, side, 側向軸, [l0, l1], [z0, z1], host_work)；side：S、P、A（船尾，砲口 −x）。"""
    V = json.load(open(os.path.join(design, 'verify_guns.json'), encoding='utf-8'))
    out = []
    for r in V['rows']:
        if 'opening_lat' in r:                                              # 風暴角號
            if r['row'] == 'chase':
                continue
            sd = 'A' if r['row'] == 'stern' else r['meta']['side']
            out.append((r['model'], r['row'], sd, 'y' if sd == 'A' else 'x', r['opening_lat'], r['opening_z'], r['host_work']))
        else:                                                               # 夜隼號
            out.append((r['model'], 'main', r['side'], 'x', r['opening_x'], r['opening_z'], V['host']))
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    works = os.path.dirname(os.path.dirname(design))
    NX, NY, NZ = CFG['frame']
    YC = CFG['YC']
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    iron = plan['guns']['colors']['iron']

    A = np.loadtxt(sys.argv[2], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    A = A[A[:, 2] < NZ]
    hull = np.zeros((NX, NY, NZ), np.int16)
    hull[A[:, 0], A[:, 1], A[:, 2]] = A[:, 3]
    hull_sha = hashlib.sha256(open(sys.argv[2], 'rb').read()).hexdigest()
    B = np.loadtxt(sys.argv[3], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    B = B[B[:, 2] < NZ]
    ship = np.zeros((NX, NY, NZ), bool)
    ship[B[:, 0], B[:, 1], B[:, 2]] = True
    asm_sha = hashlib.sha256(open(sys.argv[3], 'rb').read()).hexdigest()

    def column(sd, l, z):
        """那一欄（側向 l、高 z）在 sd 那一舷的船殼格（沿往外的軸）：回 (往外座標 s 的最外格、最裡格、外層色、內層色) 或 None。
        s ＝ 往外的有號座標：S ＝ y、P ＝ −y、A ＝ −x。"""
        if sd == 'A':
            c = np.nonzero(hull[:NX // 2, l, z])[0]
            if not len(c):
                return None
            lo = int(c.min())
            run = [lo]                                                      # 船尾那一段牆（從最尾那格往船頭連續）
            while run[-1] + 1 < NX and hull[run[-1] + 1, l, z]:
                run.append(run[-1] + 1)
            return -lo, -run[-1], int(hull[lo, l, z]), int(hull[run[-1], l, z])
        c = np.nonzero(hull[l, :, z])[0]
        c = c[c > YC] if sd == 'S' else c[c < YC]
        if not len(c):
            return None
        o = int(c.max()) if sd == 'S' else int(c.min())
        k = 1 if sd == 'S' else -1
        run = [o]
        while 0 <= run[-1] - k < NY and hull[l, run[-1] - k, z]:
            run.append(run[-1] - k)
        sg = 1 if sd == 'S' else -1
        return o * sg, run[-1] * sg, int(hull[l, o, z]), int(hull[l, run[-1], z])

    def cell_of(sd, s):
        """往外座標 s ⇒ 那一格的格號（y 或 x）。"""
        return s if sd == 'S' else -s

    # ── 砲（各層甲板 models.json，照名字配；meta.id 是匯進遊戲時發的物件 id）──
    host_models = {}

    def gun_model(host, name):
        if host not in host_models:
            host_models[host] = {m['name']: m for m in json.load(open(os.path.join(works, host, 'models.json'), encoding='utf-8'))['models']}
        m = host_models[host][name]
        assert (m.get('meta') or {}).get('kind') == 'gun' and m['meta'].get('id'), (host, name, '不是砲或沒有物件 id')
        return m

    anchors = {}

    def gun_point(m, nm):
        if m['work'] not in anchors:
            anchors[m['work']] = {a['name']: a['at'] for a in json.load(open(os.path.join(works, m['work'], 'anchors.json'), encoding='utf-8'))['anchors']}
        assert m['rotate'][0] == 0 and m['rotate'][1] == 0, m['name']
        sc = m['scale'] if isinstance(m['scale'], list) else [m['scale']] * 3
        q = (np.array([anchors[m['work']][nm]], float) + 0.5 - np.array(m['pivot'], float)) * np.array(sc, float)
        if m['mirror'] == 'y':
            q[:, 1] = -q[:, 1]
        return (rotz(q, m['rotate'][2]) + np.array(m['at'], float))[0]

    OUT = {'S': np.array([0, 1, 0.]), 'P': np.array([0, -1, 0.]), 'A': np.array([-1, 0, 0.])}

    def need_pull(m, sd):
        """砲口退到外表面往裡 1 格要沿砲軸拉幾格（同光榮號 need_pull：砲口那一欄往下找船殼、取那一排最外那格的外表面）。"""
        mz, br = gun_point(m, 'muzzle'), gun_point(m, 'breech')
        ax = (mz - br) / np.linalg.norm(mz - br)
        u = OUT[sd]
        li = int(math.floor(mz[1] if sd == 'A' else mz[0]))
        zi = int(math.floor(mz[2]))
        hit = None
        for zz in range(zi, zi - 12, -1):
            for dl in (0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5, -6, 6, -7, 7):
                c = column(sd, li + dl, zz)
                if c and abs(c[0] - float(mz @ u)) <= 12:                   # 只認砲口旁 12 格內的船殼（⛔ 船尾砲口那一欄往下先碰到的是 x 237 的隔艙壁，不是船尾板 ⇒ house 137）
                    hit = c
                    break
            if hit:
                break
        outer_s = hit[0] + (1 if sd == 'S' else 0)                          # 外表面（格角的有號座標）：S 最外那格 o 的外面是 y ＝ o ＋ 1；P、船尾的外面是格號那一面（y ＝ o ⇒ s ＝ −o ＝ hit[0]）
        need = (float(mz @ u) - (outer_s - 1)) / abs(float(ax @ u))
        return mz, ax, outer_s, need

    rows, groups = [], {}
    for name, row, sd, lax, (l0, l1), (z0, z1), host in ports(design, works):
        L0, L1, Z0, Z1 = l0 - 1, l1 + 1, z0 - 1, z1 + 1                     # 開口外那一圈（擬合外表面用；含端點）
        RS = CFG['rows'][row]
        ZT = z1 + RS['top']                                                 # 蓋板最上面那一排（鉸鏈那一排）：照 §9.12 是 z1 ＋ 1；上緣跟開口齊 ⇒ z1
        fc, outc, inc = {}, [], []
        inside = 0
        for l in range(L0, L1 + 1):
            for z in range(Z0, Z1 + 1):
                c = column(sd, l, z)
                if L0 < l < L1 and Z0 < z < Z1:                             # 開口裡（刻穿了）：那一欄還有船殼 ⇒ 記下來（應該是 0）
                    inside += c is not None
                    continue
                if c is None:
                    continue
                fc[(l, z)] = c[0] + 1                                       # 外表面外第一格空氣（有號座標）
                outc.append(c[2])
                inc.append(c[3])
        ring = 2 * (L1 - L0 + 1) + 2 * (Z1 - Z0 - 1)
        assert len(fc) == ring, (name, '蓋板那一圈有一欄沒有船殼', len(fc), ring)
        top = [fc[(l, Z1)] for l in range(L0, L1 + 1)]
        pts = np.array([[l, z, s] for (l, z), s in sorted(fc.items())], float)
        lc, zc = pts[:, 0].mean(), pts[:, 1].mean()
        Am = np.c_[np.ones(len(pts)), pts[:, 0] - lc, pts[:, 1] - zc]
        coef, *_ = np.linalg.lstsq(Am, pts[:, 2], rcond=None)
        rz_fit, rx_fit = math.degrees(math.atan(coef[1])), math.degrees(math.atan(coef[2]))
        rz = 0 if abs(rz_fit) <= RZ_FLAT else r1(rz_fit)
        close = r1(90 + rx_fit)
        size = (L1 - L0 + 1, ZT - Z0 + 1, RS['thick'])
        col = (mode(outc), mode(inc), iron)
        key = (RS['suffix'], size, col)
        groups.setdefault(key, []).append(name)

        g = gun_model(host, name)
        mz, ax, outer_s, need = need_pull(g, sd)
        need_c = max(0.0, round(need, 2))
        house = max(int(math.ceil(need_c - 1e-9)), HOUSE_MIN)
        piv = [size[0] / 2.0, 0, 0]
        lmid = L0 + size[0] / 2.0                                           # 側向：開口中間（格角座標）
        samp = np.array([[x + ox, y + oy, z + oz] for x in range(size[0]) for y in range(size[1]) for z in range(size[2])
                         for ox in (0.3, 0.5, 0.7) for oy in (0.3, 0.5, 0.7) for oz in (0.3, 0.5, 0.7)], float)
        surf = lid_surface(*size)
        ha, hb = np.array([0.5, 0.5, 0.5]), np.array([size[0] - 0.5, 0.5, 0.5])

        def pose(bump, shift):
            hs = int(max(top)) + bump                                       # 鉸鏈那一排：最外那一欄的第一格空氣（有號座標）
            hcell = cell_of(sd, hs)
            lm = lmid + shift                                               # 沿鉸鏈挪幾格（蓋板每邊比開口大 1 格 ⇒ 挪 1 格開口照樣蓋得住）
            if sd == 'S':
                return hs, hcell, [lm, hcell, ZT], rz
            if sd == 'P':
                return hs, hcell, [lm, hcell + 1, ZT], r1(180 - rz)         # 轉 180°：模型 y 0 那一排落在 [at.y − 1, at.y)
            return hs, hcell, [hcell + 1, lm, ZT], r1(90 + rz)              # 船尾：模型 +y ⇒ −x、模型 +x ⇒ +y；y 0 那一排落在 [at.x − 1, at.x)

        def put(Q, at, rot):
            return rotz(Q - np.array(piv), rot) + np.array(at, float)

        def solid(at, rot, cd):
            a, b = put(ha[None], at, rot)[0], put(hb[None], at, rot)[0]
            i = np.floor(turn(put(surf, at, rot), a, b - a, -cd)).astype(int)
            return 100.0 * float(ship[i[:, 0], i[:, 1], i[:, 2]].mean())

        pick = None
        for bump, shift in [(b, s) for b in range(0, 3) for s in (0, -1, 1)]:   # 開著碰到船殼（弧面上 rz 轉過的一角擦進外板）、或關上落進船殼太多 ⇒ 先沿鉸鏈挪一格（夜隼號 4 號：channels 的船尾端在蓋板前緣那一欄）、再把鉸鏈往外挪一格
            hs, hcell, at, rot = pose(bump, shift)
            i = np.floor(put(samp, at, rot)).astype(int)
            open_hull = int(ship[i[:, 0], i[:, 1], i[:, 2]].sum())
            if open_hull:
                continue
            for k in range(int(CLOSE_TRY / 0.5) + 1):                       # close_deg 往小調（每 0.5°）：蓋板下緣往外 ⇒ 不壓進船殼
                cd = r1(close - 0.5 * k)
                sp = solid(at, rot, cd)
                if pick is None or sp < pick[-1]:
                    pick = (bump, shift, hs, hcell, at, rot, cd, sp)
                if sp <= SOLID_MAX:
                    break
            if pick[-1] <= SOLID_MAX:
                break
        assert pick is not None, (name, '鉸鏈往外挪 2 格開著還碰到船殼')
        bump, shift, hs, hcell, at, rot, close_used, solid_pct = pick
        open_hull = 0
        rows.append({'model': '砲門蓋-' + name.split('-', 1)[1], 'gun_model': name, 'host_work': host, 'row': row, 'side': sd,
                     'key': key, 'at': [r1(v, 3) for v in at], 'pivot': [r1(v, 3) for v in piv], 'rotate': [0, 0, rot], 'scale': 1, 'mirror': 'none',
                     'meta': {'kind': 'portlid', 'lid_of': g['meta']['id'], 'close_deg': close_used, 'house': house},
                     'open_lat': [l0, l1], 'open_z': [z0, z1], 'lat_axis': lax, 'hull_in_opening_cols': inside,
                     'face': {'hinge_s': hs, 'hinge_cell': hcell, 'hinge_bump': bump, 'hinge_shift': shift, 'close_fit': close, 'closed_solid_pct': round(solid_pct, 2), 'top_ends': [int(top[0]), int(top[-1])], 'face_s': [int(pts[:, 2].min()), int(pts[:, 2].max())],
                              'rz': round(rz_fit, 1), 'rx': round(rx_fit, 1), 'rz_used': rz, 'resid': round(float(np.abs(Am @ coef - pts[:, 2]).max()), 2)},
                     'gun': {'id': g['meta']['id'], 'muzzle': [round(float(v), 2) for v in mz], 'axis': [round(float(v), 3) for v in ax],
                             'outer_face_s': outer_s, 'need_pull': need_c, 'house': house, 'house_over_max': house > HOUSE_MAX}})

    # ── 子作品：一個 key 一件 ──
    od = os.path.join(design, 'masks', 'portlids')
    os.makedirs(od, exist_ok=True)
    keys = sorted(groups, key=lambda k: (k[0], k[1], k[2]))
    suffix_used = {}
    lids = {}
    for k in keys:
        suf = k[0] if k[0] not in suffix_used else '%s-%d' % (k[0], len(suffix_used[k[0]]) + 1)
        suffix_used.setdefault(k[0], []).append(k)
        (W, H, T), (co, ci, cs) = k[1], k[2]
        straps = (1, W - 2) if W >= 7 else (1,)                             # 兩條鉸鏈板（窄的蓋板一條會擠到邊）
        sy = H - 2                                                          # 從鉸鏈往外伸到離外緣 2 格
        cells = {}
        for x in range(W):
            for y in range(H):
                for z in range(T):                                          # z 0 內層（關上貼船殼）、最上一層外層＋鉸鏈板；厚 1 ⇒ 只有外層
                    top_ = z == T - 1
                    cells[(x, y, z)] = (cs if (x in straps and y < sy) else co) if top_ else ci
        work = CFG['hull'] + '-' + suf
        fn = os.path.join(od, suf + '.txt')
        with open(fn, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# %s 砲門蓋板 %d×%d×%d（draft_portlids.py；TASK-0736）x,y,z,color —— 子作品 %s 自己的座標（畫開著：水平往外伸），stampvox at 0,0,0\n' % (CFG['ship'], W, H, T, work))
            for (x, y, z) in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (x, y, z, cells[(x, y, z)]))
        by_col = {}
        for v in cells.values():
            by_col[str(v)] = by_col.get(str(v), 0) + 1
        lids[work] = {'work': work, 'title': '砲門蓋板（上緣鉸鏈，%d×%d 格、厚 %d，通用部件，0.1 m）' % (W, H, T), 'parent_work': CFG['hull'], 'tags': 'sub', 'meters_per_voxel': 0.1,
                      'size': [W, H, T], 'file': 'masks/portlids/%s.txt' % suf, 'cells': len(cells), 'colors': dict(sorted(by_col.items())),
                      'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest(), 'anchors': {'hinge-a': [0, 0, 0], 'hinge-b': [W - 1, 0, 0]},
                      'straps_x': list(straps), 'strap_y': [0, sy - 1], 'ports': groups[k]}
        for r in rows:
            if r['key'] == k:
                r['source_work'] = work
    for r in rows:
        del r['key']
    rows.sort(key=lambda r: (r['host_work'], r['row'], r['open_lat'][0], r['side']))
    meshes = sorted({(r['source_work'], r['side'], r['rotate'][2]) for r in rows})
    out = {'note': 'draft_portlids.py（TASK-0736）—— %s 砲門蓋板：%d 件子作品掛 %d 次；外表面照船殼匯出（sha256 %s…）；砲照各層甲板 models.json。碰撞讀數在 verify_portlids.json（check_portlids.py）'
                   % (CFG['ship'], len(lids), len(rows), hull_sha[:12]),
           'hull_export_sha256': hull_sha, 'asm_export_sha256': asm_sha, 'lids': lids, 'rows': rows, 'count': len(rows),
           'rules': {'rz_flat_deg': RZ_FLAT, 'house_min': HOUSE_MIN, 'house_max': HOUSE_MAX, 'rows': CFG['rows'],
                     'S': 'rotate 0,0,rz；at ＝ (開口中間, 鉸鏈 y, z1 + 1)', 'P': 'rotate 0,0,180 − rz；at.y ＝ 鉸鏈 y ＋ 1（⛔ mirror=y）', 'A': 'rotate 0,0,90 ＋ rz；at.x ＝ 鉸鏈 x ＋ 1'},
           'meshes': [{'work': w, 'side': s, 'rz': z, 'n': sum(1 for x in rows if x['source_work'] == w and x['side'] == s and x['rotate'][2] == z)} for w, s, z in meshes]}
    with open(os.path.join(design, 'portlids_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    for w, L in lids.items():
        print('子作品 %s %s %d 格 %s ← %d 片' % (w, L['size'], L['cells'], L['colors'], len(L['ports'])))
    print('擺法 %d 片、網格 %d 份' % (len(rows), len(meshes)))
    for r in rows:
        print('  %s %s at %s rot %s close %s house %s（至少縮 %s）resid %s' % (r['model'], r['meta']['lid_of'], r['at'], r['rotate'][2], r['meta']['close_deg'],
                                                                     r['meta']['house'], r['gun']['need_pull'], r['face']['resid']))


if __name__ == '__main__':
    main()
