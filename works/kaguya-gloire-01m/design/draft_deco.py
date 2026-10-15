# 光榮號 階段五（TASK-0610）：船頭（knee of the head、head rails、trailboard）、船首像（帝國鷹）、圓船尾陽台、船名板、船尾燈位置、煙囪兩根、螺旋槳
#   輸入：plan.json（deco、funnels、propeller、stern）＋ 船現在的樣子 ＝ 階段二～四的清單（船殼 − 砲門刻 ＋ 換色、四層甲板、梯子）——
#         那幾份清單跟作品逐格相同（各階段結果帳證過），所以這裡不另外匯出作品。
#   輸出：masks/deco/<部件>.vox.txt（世界座標、at 0,0,0）、deco_placement.json（船尾燈）、verify_deco.json、sheet05_deco_v1.png
#   用法：python -I -X utf8 draft_deco.py <design> [--probe shift=<部件>:<dx>]（反向對照：某一件往 x 推 dx 格，重疊／對稱讀數要報出來；⛔ 不寫檔）
#   部件：head、figurehead、stern、name、funnels、screw。⛔ 落在船上的格一律不放（照實數 skipped）。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
from draft_lines import font, palette_rgb

FONT = {  # 3×5（上 → 下，每列 3 欄）
    'N': ['101', '111', '111', '111', '101'], 'A': ['010', '101', '111', '101', '101'], 'P': ['110', '101', '110', '100', '100'],
    'O': ['010', '101', '101', '101', '010'], 'L': ['100', '100', '100', '100', '111'], 'E': ['111', '100', '110', '100', '111'],
    'É': ['111', '100', '110', '100', '111'],
    'G': ['011', '100', '101', '101', '011'], 'I': ['111', '010', '010', '010', '111'], 'R': ['110', '101', '110', '101', '101'],   # 光榮號加的
}


def read(p):
    return np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def ship_cells(design):
    d = {}
    for f in sorted(os.listdir(os.path.join(design, 'masks', 'hull'))):
        if f.endswith('.vox.txt'):
            for x, y, z, c in read(os.path.join(design, 'masks', 'hull', f)).tolist():
                d[(x, y, z)] = c
    for x, y, z, c in read(os.path.join(design, 'masks', 'ports', 'carve.vox.txt')).tolist():
        d.pop((x, y, z))
    for x, y, z, c in read(os.path.join(design, 'masks', 'ports', 'paint.vox.txt')).tolist():
        d[(x, y, z)] = c
    for sub in ('decks', 'ladders'):
        for f in sorted(os.listdir(os.path.join(design, 'masks', sub))):
            if f.endswith('.vox.txt'):
                for x, y, z, c in read(os.path.join(design, 'masks', sub, f)).tolist():
                    d[(x, y, z)] = c
    return d


def bez(p0, p1, p2, t):
    return tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c for a, b, c in zip(p0, p1, p2))


def tube(cells, a, b, r, color, step=0.15):
    a, b = np.array(a, float), np.array(b, float)
    n = max(2, int(np.linalg.norm(b - a) / step))
    rr = int(math.ceil(r))
    for t in np.linspace(0, 1, n):
        c = a + (b - a) * t
        for dx in range(-rr - 1, rr + 2):
            for dy in range(-rr - 1, rr + 2):
                for dz in range(-rr - 1, rr + 2):
                    q = (int(math.floor(c[0])) + dx, int(math.floor(c[1])) + dy, int(math.floor(c[2])) + dz)
                    if (q[0] + 0.5 - c[0]) ** 2 + (q[1] + 0.5 - c[1]) ** 2 + (q[2] + 0.5 - c[2]) ** 2 <= r * r:
                        cells.setdefault(q, color)


def build(plan, ship, L):
    """光榮號版（kaguya 改寫）：直艏柱前一條小 cutwater（撐艏斜桅）、沒有 head rails／船首像／船尾陽台（NARA、照片、模型都沒有）；
    船名板、船尾燈位置、煙囪（淺黃黑頂）、六葉螺旋槳照拿破崙號的寫法；多一座開頂的鐵指揮塔（conning）。"""
    YC = L.YC
    D = plan['deco']
    parts = {k: {} for k in ('head', 'figurehead', 'stern', 'name', 'funnels', 'screw', 'conning', 'catheads')}

    def stem_front(z):
        xs = [x for x in range(800, 960) if (x, YC, z) in ship]
        return max(xs) if xs else None
    # ── cutwater（艏柱前緣一條薄的木料，往上加厚撐住艏斜桅根部）──
    K = D['knee']
    pz = np.array(K['profile'], float)
    for z in range(int(pz[0, 0]), int(pz[-1, 0]) + 1):
        sf = stem_front(z)
        if sf is None:
            continue
        b = int(round(float(np.interp(z, pz[:, 0], pz[:, 1]))))
        if b <= 0:
            continue
        w = K['half'] if z >= plan['waterline']['z'] else K['half_low']
        for x in range(sf + 1, sf + b + 1):
            for dy in range(-w, w + 1):
                parts['head'][(x, YC + dy, z)] = 168 if z < plan['hull_build']['bottom_top_z'] else plan['paint']['base']
    # ── 吊錨架 cathead（艏樓舷牆頂伸出舷外的橫木，兩舷；錨環掛在它外端底下 —— 遊戲照錨環旁 8 格內的實心找掛點）──
    CA = D.get('catheads')
    if CA:
        parts.setdefault('catheads', {})
        for x in range(CA['x'] - CA['half'], CA['x'] + CA['half'] + 1):
            for z in range(CA['z'] - CA['half'], CA['z'] + CA['half'] + 1):
                edge = max(y - YC for (x_, y, z_) in ship if x_ == x and z_ == z and y > YC) if any(x_ == x and z_ == z and y > YC for (x_, y, z_) in ship) else 60
                for dy in range(edge - 2, edge + CA['out'] + 1):
                    for sg in (1, -1):
                        parts['catheads'][(x, YC + sg * dy, z)] = CA['color']
    # ── 船名板（貼著船尾曲面、凸出一格）──
    NM = D['name']
    text = NM['text']
    width = len(text) * 4 - 1
    y0 = YC - (width - 1) // 2
    fg = set()
    for i, ch in enumerate(text):
        for rr, row in enumerate(FONT[ch]):
            for cc, bit in enumerate(row):
                if bit == '1':
                    fg.add((y0 + i * 4 + cc, NM['z'][0] + 2 + (4 - rr)))
    z_lo, z_hi = NM['z']
    for dy in range(-NM['half'], NM['half'] + 1):
        y = YC + dy
        for z in range(z_lo, z_hi + 2):
            xs = [x for x in range(100, 260) if (x, y, z) in ship]
            if not xs:
                continue
            x = min(xs) - 1
            border = abs(dy) == NM['half'] or z in (z_lo, z_hi + 1)
            if z == z_hi + 1 and not border:
                continue
            parts['name'][(x, y, z)] = NM['fg'] if (border or (y, z) in fg) else NM['bg']
    # ── 船尾燈的位置（艉樓 taffrail 頂、那一欄最後面的牆中間）──
    LA = D['lanterns']
    lant = []
    for dy in LA['dy']:
        y = YC + dy
        cand = [z for (x_, y_, z) in ship if y_ == y and x_ < 200 and z > LA['min_z']]
        top = max(cand)
        xs = sorted(x for x in range(100, 260) if (x, y, top) in ship)
        xm = xs[0] + 1
        lant.append({'dy': dy, 'at': [xm + 0.5, y + 0.5, top + 1], 'on_solid': (xm, y, top) in ship, 'air_above': (xm, y, top + 1) not in ship})
    # ── 煙囪（淺黃 buff、頂上一段黑；2 格厚的管子，從砲甲板穿上來）──
    FU = D['funnel']
    for f in plan['funnels']['rows']:
        zb = int(LY.deck_z(plan, 'lower', f['x']))
        r = f['r']
        for x in range(f['x'] - r - 2, f['x'] + r + 3):
            for y in range(YC - r - 2, YC + r + 3):
                d2 = (x - f['x']) ** 2 + (y - YC) ** 2
                for z in range(zb, f['top_z'] + 1):
                    top = z > f['top_z'] - FU['rim_h']
                    if d2 <= r * r and d2 > (r - FU['wall']) ** 2:
                        parts['funnels'][(x, y, z)] = FU['rim'] if top else plan['funnels']['color']
                    elif z >= f['top_z'] - 1 and d2 <= (r + FU['lip']) ** 2 and d2 > r * r:
                        parts['funnels'][(x, y, z)] = FU['rim']
    # ── 螺旋槳（plan.propeller；葉片在 y-z 平面）──
    SC = D['screw']
    pr = plan['propeller']
    zc = pr['hub_z']
    for x in range(SC['hub_x'][0], SC['hub_x'][1] + 1):
        rr = SC['hub_r'] if x >= SC['hub_x'][0] + 3 else SC['hub_r'] - (SC['hub_x'][0] + 3 - x)
        for y in range(YC - 6, YC + 7):
            for z in range(zc - 6, zc + 7):
                if (y - YC) ** 2 + (z - zc) ** 2 <= rr * rr:
                    parts['screw'][(x, y, z)] = SC['color']
    for x in range(SC['shaft_x'][0], SC['shaft_x'][1] + 1):
        for y in range(YC - 3, YC + 4):
            for z in range(zc - 3, zc + 4):
                if (y - YC) ** 2 + (z - zc) ** 2 <= SC['shaft_r'] ** 2:
                    parts['screw'][(x, y, z)] = SC['color']
    hw = np.array(SC['hw_deg'], float)
    R = pr['diameter'] / 2.0
    for y in range(YC - int(R) - 1, YC + int(R) + 2):
        for z in range(zc - int(R) - 1, zc + int(R) + 2):
            rho = math.hypot(y - YC, z - zc)
            if rho < SC['hub_r'] - 0.5 or rho > R:
                continue
            ph = math.degrees(math.atan2(z - zc, y - YC))
            lim = float(np.interp(rho, hw[:, 0], hw[:, 1]))
            for k in range(pr['blades']):
                a0 = 90 + k * 360.0 / pr['blades']
                dd = (ph - a0 + 180) % 360 - 180
                if abs(dd) <= lim:
                    xr = SC['blade_x'] if rho < R * 0.6 else SC['blade_x_tip']
                    for x in range(xr[0], xr[1] + 1):
                        parts['screw'][(x, y, z)] = SC['color']
    # ── 指揮塔（開頂的鐵圓筒，上甲板上、後桅前面；船尾那一側開一道門）──
    CT = D['conning']
    zb = int(LY.deck_z(plan, 'spar', CT['x'])) + 1
    for x in range(CT['x'] - CT['r'] - 1, CT['x'] + CT['r'] + 2):
        for y in range(YC - CT['r'] - 1, YC + CT['r'] + 2):
            d2 = (x - CT['x']) ** 2 + (y - YC) ** 2
            if not (d2 <= CT['r'] ** 2 and d2 > (CT['r'] - CT['wall']) ** 2):
                continue
            for z in range(zb, zb + CT['h']):
                if x < CT['x'] and abs(y - YC) <= CT['door_half'] and z < zb + CT['door_h']:
                    continue
                parts['conning'][(x, y, z)] = CT['color']
    return parts, lant


def bowsprit_clear(plan, cells):
    bs = plan['masts']['bowsprit']
    a = math.radians(bs['angle_deg'])
    d = np.array([math.cos(a), 0, math.sin(a)])
    o = np.array([bs['heel_x'] + 0.5, plan['space']['yc'] + 0.5, bs['heel_z'] + 0.5])
    best = 1e9
    for k in cells:
        p = np.array(k, float) + 0.5 - o
        t = float(p @ d)
        if t < 60:                          # 根部 60 格內在船殼裡，不算
            continue
        best = min(best, float(np.linalg.norm(p - t * d)))
    return round(best, 2)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    ship = ship_cells(design)
    parts, lant = build(plan, ship, L)
    if probe:
        k, dx = probe[0].split('=')[1].split(':')
        parts[k] = {(x + int(dx), y, z): c for (x, y, z), c in parts[k].items()}
    R = {'parts': {}, 'problems': []}
    placed = {}
    for k, cells in parts.items():
        keep = {q: c for q, c in cells.items() if q not in ship}
        skipped = len(cells) - len(keep)
        if not probe:                      # 部件之間：先放的優先（船首像讓給 knee）；probe 時照實量重疊
            yielded = sum(1 for q in keep if q in placed)
            keep = {q: c for q, c in keep.items() if q not in placed}
            skipped += yielded
        ov = sum(1 for q in keep if q in placed)
        mir = sum(1 for (x, y, z), c in keep.items() if keep.get((x, 2 * YC - y, z)) != c)
        R['parts'][k] = {'cells': len(keep), 'skipped_on_ship': skipped, 'overlap_other_parts': ov, 'mirror_diff': mir,
                         'colors': {int(a): int(b) for a, b in zip(*np.unique(list(keep.values()), return_counts=True))}}
        for q in keep:
            placed[q] = k
        parts[k] = keep
    R['bowsprit_clearance'] = {k: bowsprit_clear(plan, parts[k]) for k in ('head', 'figurehead')}
    R['lanterns'] = lant
    # 組起來：船＋部件 ⇒ 元件數與封閉空腔（numpy 盒子，只看部件周圍）
    allk = set(ship) | set(placed)
    arr = np.array(list(allk), np.int32)
    lo = arr.min(axis=0)
    hi = arr.max(axis=0)
    G = np.zeros(tuple(hi - lo + 3), bool)
    G[arr[:, 0] - lo[0] + 1, arr[:, 1] - lo[1] + 1, arr[:, 2] - lo[2] + 1] = True
    lab, n = ndimage.label(G)
    sizes = ndimage.sum(G, lab, range(1, n + 1))
    R['components'] = int(n)
    R['small_components'] = sorted(int(s) for s in sizes)[:-1][:20]
    cav = ndimage.binary_fill_holes(G) & ~G
    # 部件夾出來的小空腔（≤ 50 格）⇒ 填進旁邊最多格的那一件、用那一件旁邊的顏色；填完再量一次
    R['cavities_filled'] = []
    labc, nc = ndimage.label(cav)
    for i in range(1, nc + 1):
        idx = np.argwhere(labc == i) + lo - 1
        if len(idx) > 50:
            continue
        votes = {}
        for q in map(tuple, idx.tolist()):
            for dq in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nb = (q[0] + dq[0], q[1] + dq[1], q[2] + dq[2])
                if nb in placed:
                    votes.setdefault(placed[nb], []).append(parts[placed[nb]][nb])
        if not votes:
            continue
        k = max(votes, key=lambda kk: len(votes[kk]))
        c = max(set(votes[k]), key=votes[k].count)
        for q in map(tuple, idx.tolist()):
            parts[k][q] = c
            placed[q] = k
            G[q[0] - lo[0] + 1, q[1] - lo[1] + 1, q[2] - lo[2] + 1] = True
        R['parts'][k]['cells'] = len(parts[k])
        R['cavities_filled'].append({'part': k, 'cells': int(len(idx)), 'at': idx[0].tolist()})
    cav = ndimage.binary_fill_holes(G) & ~G
    R['cavity_cells'] = int(cav.sum())
    if R['components'] != 1:
        R['problems'].append('組起來 %d 個元件' % n)
    if R['cavity_cells']:
        R['problems'].append('封閉空腔 %d 格' % R['cavity_cells'])
    for k, v in R['parts'].items():
        if v['overlap_other_parts']:
            R['problems'].append('%s 跟別的部件重疊 %d' % (k, v['overlap_other_parts']))
    if probe:
        print(json.dumps({'probe': probe[0], 'parts': {k: {kk: vv for kk, vv in v.items() if kk != 'colors'} for k, v in R['parts'].items()},
                          'components': R['components'], 'problems': R['problems']}, ensure_ascii=False))
        return
    od = os.path.join(design, 'masks', 'deco')
    os.makedirs(od, exist_ok=True)
    R['lists'] = {}
    for k, cells in parts.items():
        p = os.path.join(od, k + '.vox.txt')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 光榮號 階段五 %s（draft_deco.py；世界座標，at 0,0,0）\n' % k)
            for q in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (q[0], q[1], q[2], cells[q]))
        R['lists'][k] = [len(cells), hashlib.sha256(open(p, 'rb').read()).hexdigest()]
    with open(os.path.join(design, 'deco_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'lanterns': lant}, f, ensure_ascii=False, indent=1)
    # 圖：船頭側面＋正面、船尾側面＋正面
    sc = 4
    views = [('船頭（右舷看）', 840, 960, 40, 200, 'side'), ('船頭（正面）', YC - 40, YC + 40, 40, 200, 'front'),
             ('船尾（右舷看）', 120, 240, 0, 200, 'side'), ('船尾（從船尾看）', YC - 60, YC + 60, 0, 200, 'back')]
    Wp = sum((v[2] - v[1]) * sc + 40 for v in views) + 40
    Hp = 200 * sc + 120
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((20, 10), '光榮號 新圖紙 05：cutwater、船名板、煙囪、六葉螺旋槳、指揮塔　v1　（部件 ＝ 亮色；船 ＝ 淡）', fill=(0, 0, 0), font=font(18))
    ox = 20
    allc = dict(ship)
    for q, k in placed.items():
        allc[q] = parts[k][q]
    for title, a0, a1, z0, z1, kind in views:
        d.text((ox, 40), title, fill=(0, 0, 0), font=font(14))
        best = {}
        for (x, y, z), c in allc.items():
            if not (z0 <= z < z1):
                continue
            if kind == 'side':
                if not (a0 <= x < a1):
                    continue
                u, depth = x - a0, y
            elif kind == 'front':                # 從船頭往後看：左手 ＝ 右舷 ＋y（引擎：左舷 P ＝ −y）
                if not (a0 <= y < a1) or x < 800:
                    continue
                u, depth = a1 - 1 - y, x
            else:                                # 從船尾往前看：左手 ＝ 左舷 −y
                if not (a0 <= y < a1) or x > 300:
                    continue
                u, depth = y - a0, -x
            kk = (u, z)
            if kk not in best or depth > best[kk][0]:
                best[kk] = (depth, c, (x, y, z) in placed)
        for (u, z), (_, c, mine) in best.items():
            rgb = palette_rgb(int(c))
            if not mine:
                rgb = tuple(int(v * 0.45 + 250 * 0.55) for v in rgb)
            X, Y = ox + u * sc, 70 + (z1 - 1 - z) * sc
            d.rectangle([X, Y, X + sc - 1, Y + sc - 1], fill=rgb)
        ox += (a1 - a0) * sc + 40
    im.save(os.path.join(design, 'sheet05_deco_v1.png'))
    with open(os.path.join(design, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('lists',)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
