# 三叉戟號 階段五（TASK-0558）船尾：三層陽台＋頂簷、quarter gallery（右舷一件，左舷用 mirror=y 關聯）、名牌 TRIDENTE、船尾徽
#   輸入：plan.json（stern_deco、decks、stern）＋「階段五之前」的組裝件（deco_base.base_grid：船殼＋甲板＋梯子）
#   輸出：masks/stern/{walk,gallery,deco}.vox.txt（各子作品自己的座標）、stern_placement.json（框、關聯 at）、verify_stern_deco.json、sheet05_stern_v1.png
#   用法：python -I -X utf8 draft_stern_deco.py <design> [--base=<快取.npy>]（快取只給反覆試畫用；定稿一律不帶，現讀組裝件）
import sys, os, json, math
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import deco_base as DB
from draft_lines import font, palette_rgb

YC = 200
GLYPH = {   # 5×7，第一列在上
    'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
    'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    'I': ['.###.', '..#..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    'D': ['####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'],
    'E': ['#####', '#....', '#....', '####.', '#....', '#....', '#####'],
    'N': ['#...#', '##..#', '#.#.#', '#.#.#', '#..##', '#...#', '#...#'],
}
TRIDENT = [  # 船尾徽的三叉戟（15 寬 × 21 高，第一列在上；中線 ＝ 第 7 欄）
    '.......#.......',
    '......###......',
    '.....#####.....',
    '..#....#....#..',
    '.###...#...###.',
    '#####..#..#####',
    '..#....#....#..',
    '..#....#....#..',
    '..#....#....#..',
    '..#....#....#..',
    '..##...#...##..',
    '...#########...',
    '.......#.......',
    '......###......',
    '.......#.......',
    '.......#.......',
    '.......#.......',
    '.......#.......',
    '.......#.......',
    '......###......',
    '.......#.......',
]


def window_centers(row):
    """船尾窗那一列每扇窗的中心 dy（照 draft_ports 的對稱取整）。"""
    n, w, half = row['n'], row['w'], row['half']
    out = []
    for c in np.linspace(-half + w / 2.0, half - w / 2.0, n):
        out.append(int(math.floor(abs(c) + 0.5)) * (1 if c >= 0 else -1))
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    cache = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--base=')), None)
    plan = HL.load_plan(design)
    SD = plan['stern_deco']
    C = SD['colors']
    WALL, TRIM, DARK, GLASS = C['wall'], C['trim'], C['dark'], C['glass']
    if cache and os.path.exists(cache):
        G = np.load(cache)
    else:
        G = DB.base_grid()
        if cache:
            np.save(cache, G)
    S = G > 0
    NZ = G.shape[2]

    # ── 量現況：船尾面、船尾面半寬、右舷外緣 ──
    sub = S[:170]
    FX = np.where(sub.any(0), sub.argmax(0), -1)                      # [y, z]：從船尾往前第一格實心的 x
    XT, HC = {}, {}
    for z in range(80, NZ):
        c = FX[YC - 40:YC + 41, z]
        c = c[c >= 0]
        if len(c) == 0:
            continue
        XT[z] = int(c.min())                                          # 船尾面（窗凹進去 1 格，取最小 ＝ 面）
        row = FX[YC:YC + 81, z]
        HC[z] = int(np.nonzero((row >= 0) & (row <= XT[z] + 1))[0].max())   # 船尾面平的那一段半寬（取最外那一格：追擊砲門刻穿的那幾欄不算斷）
    Sr = S[:, YC + 1:, :]
    SY = np.where(Sr.any(1), Sr.shape[1] - Sr[:, ::-1, :].argmax(1), 0)   # [x, z]：右舷最外那一格的 dy

    zd = {k: int(LY.deck_z(plan, k, 90)) for k in ('middle', 'upper', 'spar', 'poop')}
    rows = {r['deck']: r for r in plan['stern']['rows']}
    W = SD['walk']
    D = W['depth']
    GA = SD['gallery']
    inset = GA['inset']

    walk, gal, deco = {}, {}, {}
    skipped = {'walk': 0, 'gallery': 0, 'deco': 0}

    def put(part, store, x, y, z, c):
        if S[x, y, z]:
            skipped[part] += 1
            return
        store[(x, y, z)] = c

    # ── 陽台三層＋頂簷 ──
    levels = W['levels'] + [W['roof']]
    walk_info = []
    WDY = {}
    for li, k in enumerate(levels):
        z0 = zd[k]
        xo = XT[z0] - D
        dyw = HC[z0] - inset - 1
        roof = k == W['roof']
        if roof:                                                      # 頂簷跟最上面那層陽台一樣寬、一樣深
            prev = walk_info[-1]
            xo, dyw = prev['xo'], prev['dyw']
        for z in (z0 - 1, z0):
            for dy in range(-dyw, dyw + 1):
                y = YC + dy
                for x in range(xo, FX[y, z]):
                    put('walk', walk, x, y, z, TRIM if x == xo else DARK)
        info = {'level': k, 'z_floor': z0, 'xo': xo, 'dyw': dyw}
        if not roof:
            bh = W['bracket_h']
            for dy in range(-(dyw // W['bracket_dy']) * W['bracket_dy'], dyw + 1, W['bracket_dy']):
                y = YC + dy
                for j in range(1, bh + 1):
                    z = z0 - 1 - j
                    dep = int(round(D * (1 - j / (bh + 1.0))))
                    for x in range(FX[y, z] - dep, FX[y, z]):
                        put('walk', walk, x, y, z, TRIM)
            rh = W['rail_h']
            for dy in range(-dyw, dyw + 1):
                y = YC + dy
                for x in (xo, xo + 1):
                    put('walk', walk, x, y, z0 + 1, DARK)                       # 底檻
                    put('walk', walk, x, y, z0 + rh - 1, DARK)                  # 扶手
                    put('walk', walk, x, y, z0 + rh, DARK)
                if dy % W['baluster_every'] == 0:
                    for z in range(z0 + 2, z0 + rh - 1):
                        put('walk', walk, xo, y, z, TRIM)                       # 欄柱
            # 柱子：窗與窗之間，從陽台地板頂到上一層地板底
            z_up = zd[levels[li + 1]] - 2
            cs = window_centers(rows[k])
            posts = []
            for a, b in W['post_between']:
                p = int(math.floor(abs((cs[a - 1] + cs[b - 1]) / 2.0) + 0.5))
                posts.append(p)
            for p in sorted(set(posts)):
                for dy in (p, p + 1, -p, -p - 1):
                    for x in (xo, xo + 1):
                        for z in range(z0 + 1, z_up + 1):
                            if (x, YC + dy, z) in walk:
                                del walk[(x, YC + dy, z)]
                            put('walk', walk, x, YC + dy, z, TRIM)
            info.update({'posts_dy': sorted(set(posts)), 'z_post_top': z_up})
        walk_info.append(info)
        for z in range(z0 - 1, (info['z_post_top'] if not roof else z0) + 1):
            WDY[z] = dyw                                              # 這個高度陽台佔到 |dy| ≤ dyw ⇒ gallery 在船尾面後面那一段從 dyw ＋ 1 起

    # ── quarter gallery（右舷）──
    zb, zt = zd['middle'] - 1, zd['poop']
    cornice = set()
    for k in ('middle', 'upper', 'spar', 'poop'):
        cornice |= {zd[k] - 1, zd[k]}
    xf, R, dep = GA['x_front'], GA['front_r'], GA['depth']
    foot = {}                                                         # z ⇒ {x: (lo, hi)}（右舷 dy 範圍）

    def span(x, z, extra=0):
        xa = XT[z] - D
        dy_out = SY[100, z] + dep + extra
        lo = max((HC[z] - inset) if x < XT[z] else SY[x, z] + 1, WDY.get(z, -1) + 1)   # 船尾轉角那幾欄陽台地板會填進去 ⇒ 一律讓給陽台
        th = dy_out - lo + 1
        if x > xf - R:
            t = (x - (xf - R)) / float(R)
            th = int(math.floor(th * math.sqrt(max(0.0, 1 - t * t)) + 0.5))
        return lo, lo + th - 1, xa

    for z in range(zb, zt + 1):
        ext = 1 if z in cornice else 0
        xa = XT[z] - D - ext
        foot[z] = {}
        for x in range(xa, xf + 1 + ext):
            lo, hi, _ = span(min(x, xf), z, ext)
            if hi < lo:
                continue
            foot[z][x] = (lo, hi)
            for dy in range(lo, hi + 1):
                put('gallery', gal, x, YC + dy, z, TRIM if ext else WALL)
    # 側窗（每層 3 扇，對齊船尾窗那一列）＋後窗 1 扇
    windows = []
    for k in ('middle', 'upper', 'spar'):
        r = rows[k]
        wz0 = zd[k] + r['sill']
        wz1 = wz0 + r['h'] - 1
        zm = (wz0 + wz1) // 2
        xa = XT[zm] - D
        n, w = GA['win_n'], GA['win_w']
        cx = np.linspace(xa + 2 + w / 2.0, xf - R - 1 - w / 2.0, n)
        for c in cx:
            x0 = int(round(c - w / 2.0))
            windows.append(('side', k, x0, x0 + w - 1, wz0, wz1))
            for x in range(x0 - 1, x0 + w + 1):
                for z in range(wz0 - 1, wz1 + 2):
                    lo, hi = foot[z].get(x, (None, None))
                    if lo is None or (x, YC + hi, z) not in gal:
                        continue
                    if x0 <= x < x0 + w and wz0 <= z <= wz1:
                        del gal[(x, YC + hi, z)]
                        if (x, YC + hi - 1, z) in gal:
                            gal[(x, YC + hi - 1, z)] = GLASS
                    else:
                        gal[(x, YC + hi, z)] = TRIM
        # 後窗：後面那一面（x ＝ xa）
        lo, hi, _ = span(xa, zm)
        aw = GA['aft_win_w']
        yc0 = (lo + hi) // 2 - aw // 2
        windows.append(('aft', k, yc0, yc0 + aw - 1, wz0, wz1))
        for dy in range(yc0 - 1, yc0 + aw + 1):
            for z in range(wz0 - 1, wz1 + 2):
                x = XT[z] - D
                if (x, YC + dy, z) not in gal:
                    continue
                if yc0 <= dy < yc0 + aw and wz0 <= z <= wz1:
                    del gal[(x, YC + dy, z)]
                    if (x + 1, YC + dy, z) in gal:
                        gal[(x + 1, YC + dy, z)] = GLASS
                else:
                    gal[(x, YC + dy, z)] = TRIM
    # 垂飾（cornice 底下往下收成一點）：黑身、每 4 格一道金箍
    xs_body = [x for x in foot[zb] if x >= XT[zb]]
    xc = (min(xs_body) + max(xs_body)) / 2.0
    hx = (max(xs_body) - min(xs_body)) / 2.0
    zdrop = GA['drop_z']
    for z in range(zdrop, zb):
        u = (zb - z) / float(zb - zdrop + 1)
        s = (1 - u) ** 0.8
        for x in range(int(math.floor(xc - hx * s)), int(math.ceil(xc + hx * s)) + 1):
            if x < XT[z] + 1 or x > xf:
                continue
            lo = SY[x, z] + 1
            th = int(round((SY[100, zb] + dep - SY[x, zb]) * s))
            ring = (zb - z) % 4 == 0
            for dy in range(lo, lo + max(th, 1)):
                put('gallery', gal, x, YC + dy, z, TRIM if ring else DARK)
    # 冠（頂簷上面往上收成圓頂）：黑、金肋，頂上金尖
    ztop = GA['crown_top']
    xs_top = sorted(foot[zt])
    xc2 = (xs_top[0] + xs_top[-1]) / 2.0
    hx2 = (xs_top[-1] - xs_top[0]) / 2.0
    peak = None
    for z in range(zt + 1, ztop + 1):
        u = (z - zt) / float(ztop - zt + 1)
        s = math.sqrt(max(0.0, 1 - u * u))
        for x in range(int(math.floor(xc2 - hx2 * s)), int(math.ceil(xc2 + hx2 * s)) + 1):
            lo, hi, _ = span(min(x, xf), zt)
            lo = (HC[z] - inset) if x < XT[z] else SY[x, z] + 1
            th = int(round((hi - lo + 1) * s))
            if th < 1:
                continue
            rib = (int(round(x - xc2)) % 8 == 0)
            for dy in range(lo, lo + th):
                put('gallery', gal, x, YC + dy, z, TRIM if rib else DARK)
            peak = (int(round(xc2)), lo, z)
    if peak:
        x, dy, z = peak
        for k in range(1, GA['finial'] + 1):
            put('gallery', gal, x, YC + dy, z + k, TRIM)

    # ── 名牌 TRIDENTE（counter 紅帶上，凸 1 格）──
    NM = SD['name']
    text = NM['text']
    wtot = len(text) * 6 - 1
    dy0 = -(wtot // 2)
    zt_name = NM['z0'] + 6
    for i, ch in enumerate(text):
        for r, line in enumerate(GLYPH[ch]):
            for c, b in enumerate(line):
                if b == '#':
                    y, z = YC + dy0 + i * 6 + c, zt_name - r
                    put('deco', deco, FX[y, z] - 1, y, z, TRIM)
    for dy in range(dy0 - 3, -dy0 + 4):                               # 上下兩道金線、兩頭收尖
        for z in (NM['z0'] - 2, zt_name + 2):
            y = YC + dy
            put('deco', deco, FX[y, z] - 1, y, z, TRIM)
    for sgn in (-1, 1):
        for k, zz in ((4, (NM['z0'] - 1, zt_name + 1)), (5, (NM['z0'] + 1, zt_name - 1)), (6, (NM['z0'] + 3,))):
            for z in zz:
                y = YC + sgn * (-dy0 + k - 1)
                put('deco', deco, FX[y, z] - 1, y, z, TRIM)
    # ── 船尾徽（taffrail 中線上：扇貝形黑底金邊＋金三叉戟，厚 2）──
    zc = max(z for z in range(150, NZ) if S[40:120, YC, z].any())
    xc0 = int(np.nonzero(S[40:120, YC, zc])[0][0]) + 40
    rr = SD['crest']['r']
    for dy in range(-rr, rr + 1):
        for z in range(zc + 1, zc + rr + 1):
            d = math.hypot(dy, z - zc)
            if d > rr:
                continue
            ang = math.degrees(math.atan2(z - zc, dy))
            rib = d > 6 and abs((ang + 7.5) % 30 - 7.5) < 2.2 and d < rr - 1
            c = TRIM if d > rr - 1.5 or rib else DARK
            for x in (xc0, xc0 + 1):
                put('deco', deco, x, YC + dy, z, c)
    for i, line in enumerate(TRIDENT):                               # 第 0 列在上；最下一列站在 taffrail 上
        z = zc + len(TRIDENT) - i
        for j, b in enumerate(line):
            if b != '#':
                continue
            dy = j - len(line) // 2
            for x in (xc0, xc0 + 1):
                if (x, YC + dy, z) in deco:
                    del deco[(x, YC + dy, z)]
                put('deco', deco, x, YC + dy, z, TRIM)
    # 有些齒尖伸出扇面 ⇒ 要碰得到扇面或彼此（下面連通檢查會量）

    # ── 讀數 ──
    parts = {'walk': walk, 'gallery': gal, 'deco': deco}
    allc = {}
    for nm, p in parts.items():
        for k in p:
            assert k not in allc, ('部件彼此重疊', nm, k)
            allc[k] = p[k]
    galP = {(x, 2 * YC - y, z): c for (x, y, z), c in gal.items()}
    over_P = sum(1 for (x, y, z) in galP if S[x, y, z] or (x, y, z) in allc)
    lo = np.array([40, 100, 80])
    hi = np.array([180, 301, NZ])
    U = S[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]].copy()
    Ub = U.copy()
    for (x, y, z) in list(allc) + list(galP):
        U[x - lo[0], y - lo[1], z - lo[2]] = True
    lab, n = ndimage.label(U)
    base_labels = set(np.unique(lab[Ub]).tolist()) - {0}
    floating = {nm: sum(1 for (x, y, z) in p if lab[x - lo[0], y - lo[1], z - lo[2]] not in base_labels) for nm, p in list(parts.items()) + [('gallery_P', galP)]}
    holes = ndimage.binary_fill_holes(U) & ~U
    sym = set(walk) | set(deco)
    asym_walk = sum(1 for (x, y, z) in walk if (x, 2 * YC - y, z) not in walk or walk[(x, 2 * YC - y, z)] != walk[(x, y, z)])
    asym_deco = sum(1 for (x, y, z) in deco if (x, 2 * YC - y, z) not in deco or deco[(x, 2 * YC - y, z)] != deco[(x, y, z)])
    R = {'cells': {k: len(v) for k, v in parts.items()}, 'skipped_overlap_base': skipped, 'gallery_P_overlap': over_P,
         'floating': floating, 'cavities': int(holes.sum()), 'asym_walk': asym_walk, 'asym_deco_name_only': asym_deco,
         'walk_levels': walk_info, 'decks_z': zd, 'transom_x': {z: XT[z] for z in range(96, 210, 4) if z in XT},
         'transom_half': {z: HC[z] for z in range(96, 210, 4) if z in HC}, 'windows': windows, 'crest_base': [xc0, YC, zc]}
    # ── 清單（各子作品自己的框）──
    out = os.path.join(design, 'masks', 'stern')
    place = {}
    heads = {'walk': '# 三叉戟號 船尾陽台三層＋頂簷（子作品座標）\n', 'gallery': '# 三叉戟號 quarter gallery 右舷（子作品座標；左舷 ＝ mirror=y 關聯）\n',
             'deco': '# 三叉戟號 船尾名牌 TRIDENTE＋船尾徽（子作品座標）\n'}
    lists = {}
    for nm, p in parts.items():
        org, size = DB.bbox(p)
        if nm == 'gallery':
            size[1] += 0                                              # 右舷那一件的框照實
        n, h = DB.write_local(os.path.join(out, nm + '.vox.txt'), p, org, heads[nm])
        place[nm] = {'at': org, 'size': size}
        lists[nm] = [n, h]
    place['gallery']['at_mirror'] = [place['gallery']['at'][0], DB.mirror_at_y(place['gallery']['at'][1], place['gallery']['size'][1]), place['gallery']['at'][2]]
    R['lists'] = lists
    R['placement'] = place
    with open(os.path.join(design, 'stern_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(place, f, ensure_ascii=False, indent=1)
    # ── 圖紙：從船尾看＋右舷側面（船尾那一段）──
    full = dict(allc)
    full.update(galP)
    sc = 4
    X0, X1, Z0, Z1 = 55, 175, 85, 232
    Y0, Y1 = 115, 286
    Wp = (Y1 - Y0) * sc + (X1 - X0) * sc + 120
    Hp = (Z1 - Z0) * sc + 140
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((30, 12), '三叉戟號 新圖紙 05：船尾 —— 三層陽台、quarter gallery、名牌、徽　v1', fill=(0, 0, 0), font=font(22))
    oy = 60
    E = np.zeros((X1 - X0, Y1 - Y0, Z1 - Z0), np.uint8)
    E[:] = G[X0:X1, Y0:Y1, Z0:Z1]
    for (x, y, z), c in full.items():
        if X0 <= x < X1 and Y0 <= y < Y1 and Z0 <= z < Z1:
            E[x - X0, y - Y0, z - Z0] = c
    for yi in range(Y1 - Y0):
        for zi in range(Z1 - Z0):
            xs = np.nonzero(E[:, yi, zi])[0]
            if len(xs):
                c = palette_rgb(int(E[xs[0], yi, zi]))
                X, Y = 30 + yi * sc, oy + (Z1 - Z0 - 1 - zi) * sc
                d.rectangle([X, Y, X + sc - 1, Y + sc - 1], fill=c)
    ox = 30 + (Y1 - Y0) * sc + 60
    for xi in range(X1 - X0):
        for zi in range(Z1 - Z0):
            ys = np.nonzero(E[xi, :, zi])[0]
            if len(ys):
                c = palette_rgb(int(E[xi, ys[-1], zi]))
                X, Y = ox + xi * sc, oy + (Z1 - Z0 - 1 - zi) * sc
                d.rectangle([X, Y, X + sc - 1, Y + sc - 1], fill=c)
    d.text((30, oy + (Z1 - Z0) * sc + 10), '左：從船尾看（觀者左手 = -y = 左舷 P）；右：右舷側面 x %d–%d（船頭在右）' % (X0, X1), fill=(40, 40, 40), font=font(16))
    d.text((30, oy + (Z1 - Z0) * sc + 36), '陽台 %d、gallery 一舷 %d、名牌＋徽 %d；浮空 %s；空腔 %d；左舷鏡過去撞到 %d' % (
        len(walk), len(gal), len(deco), sum(floating.values()), R['cavities'], over_P), fill=(0, 0, 0), font=font(16))
    im.save(os.path.join(design, 'sheet05_stern_v1.png'))
    with open(os.path.join(design, 'verify_stern_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=int)
    print(json.dumps({k: R[k] for k in ('cells', 'skipped_overlap_base', 'gallery_P_overlap', 'floating', 'cavities', 'asym_walk', 'asym_deco_name_only', 'lists', 'placement')}, ensure_ascii=False, default=int))


if __name__ == '__main__':
    main()
