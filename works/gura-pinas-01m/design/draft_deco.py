# 出處：calli-cosecha-01m/design/draft_deco.py（收穫號）的框架 —— 部件換成荷蘭 pinas 的（TASK-0967 步驟 6）
# 藍鯊號 步驟 6：船首喙（galjoen＋cutwater＋head rail）、船首像（紅獅子）、船尾走廊＋兩舷側廊、hackebort（藍鯊紋章＋名帶）、船尾燈
#   輸入：plan.json（espolon、figurehead、stern_deco）＋ 組裝件現在的格子（CLI 匯出 ⇒ 船殼＋甲板＋梯子＋玻璃，佔用與貼面都照它算）
#   輸出：masks/deco/<部件>.vox.txt（世界座標、at 0,0,0）、verify_deco.json、sheet05_deco_v1.png
#   用法：python -I -X utf8 draft_deco.py <design> [--probe=shift=<部件>:<dy>]（反向對照：某一件整件往 y 推幾格，⛔ 不寫檔）
#   · galjoen、獅子、船尾走廊、側廊兩舷一起產（照 |dy| 算 ⇒ 對稱）；hackebort 的鯊魚與字不對稱（照實報鏡像差）。
#   · 側廊的窗是畫上去的（87，後面是側廊的實心）—— 只有鏡板的窗是真的玻璃（-stern-glass，material=glass）
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from draft_lines import font, palette_rgb
from wio import export_list

BLACK, GOLD, GLASS, WOOD, TRIM, DECK, BLUE = 36, 248, 87, 141, 136, 209, 6
PARTS = ('galjoen', 'figurehead', 'stern-deco', 'hackebort')

FONT = {  # 3×5，列由上往下
    'B': ['XX.', 'X.X', 'XX.', 'X.X', 'XX.'], 'L': ['X..', 'X..', 'X..', 'X..', 'XXX'], 'A': ['.X.', 'X.X', 'XXX', 'X.X', 'X.X'],
    'U': ['X.X', 'X.X', 'X.X', 'X.X', 'XXX'], 'W': ['X.X', 'X.X', 'XXX', 'XXX', 'X.X'], 'E': ['XXX', 'X..', 'XX.', 'X..', 'XXX'],
    'H': ['X.X', 'X.X', 'XXX', 'X.X', 'X.X'], 'I': ['XXX', '.X.', '.X.', '.X.', 'XXX'], ' ': ['.', '.', '.', '.', '.'],
}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    A = export_list('gura-pinas-01m-assembly', None, links=None)
    # 船 ＝ 組裝件扣掉本步驟自己的件（已經落過一次的話；收穫號 v1 沒扣 ⇒ 重產時把舊裝飾當成船）
    own = set()
    for nm in PARTS:
        if os.path.exists(os.path.join(WORKS, 'gura-pinas-01m-' + nm, 'work.json')):
            own |= set(map(tuple, export_list('gura-pinas-01m-' + nm, None)[:, :3].tolist()))
    if own:
        A = A[np.array([tuple(r) not in own for r in A[:, :3].tolist()], bool)]
    # 側廊 v2 自己改過的格放回去再量（重跑逐位元組相同）：船殼刻掉的窗洞照原色補回、側廊的玻璃拿掉
    gc_path = os.path.join(design, 'masks', 'deco', 'gallery_carve.vox.txt')
    gg_path = os.path.join(design, 'masks', 'glass', 'gallery_glass.vox.txt')
    if os.path.exists(gg_path):
        gg = set(map(tuple, np.loadtxt(gg_path, delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')[:, :3].tolist()))
        A = A[np.array([tuple(r) not in gg for r in A[:, :3].tolist()], bool)]
    Hl = export_list('gura-pinas-01m', None)
    if os.path.exists(gc_path):
        G0 = np.loadtxt(gc_path, delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')
        have = set(map(tuple, A[:, :3].tolist()))
        add = np.array([r for r in G0.tolist() if tuple(r[:3]) not in have], dtype=A.dtype).reshape(-1, A.shape[1])
        A = np.concatenate([A, add[:, :A.shape[1]]]) if len(add) else A
        hs = set(map(tuple, Hl[:, :3].tolist()))
        addh = np.array([r for r in G0.tolist() if tuple(r[:3]) not in hs], dtype=Hl.dtype).reshape(-1, Hl.shape[1])
        Hl = np.concatenate([Hl, addh[:, :Hl.shape[1]]]) if len(addh) else Hl
    hull_col = {tuple(r[:3]): int(r[3]) for r in Hl.tolist()}
    hull_cells = set(hull_col)
    GLASS_REAL = int(open(os.path.join(design, 'masks', 'glass', 'stern_glass.vox.txt'), encoding='utf-8').read().splitlines()[1].split(',')[3])   # 跟鏡板的玻璃同一色
    occ = set(map(tuple, A[:, :3].tolist()))
    aft, outer, fwd = {}, {}, {}
    for x, y, z in A[:, :3].tolist():
        if x < 210:
            if x < aft.get((y, z), 10 ** 6):
                aft[(y, z)] = x
        dy = abs(y - YC)
        if dy > outer.get((x, z), -1):
            outer[(x, z)] = dy
        if x >= 400 and y == YC and x > fwd.get(z, -1):
            fwd[z] = x
    parts = {}

    def put(part, x, y, z, c):
        parts.setdefault(part, {})[(int(x), int(y), int(z))] = c

    def both(part, x, dy, z, c):
        put(part, x, YC + dy, z, c)
        put(part, x, YC - dy, z, c)

    # ── galjoen（船首喙）：甲板＋head rail＋cutwater ──
    E = plan['espolon']
    F = plan['figurehead']
    xs0 = int(math.floor(float(L.x_stem(80)) + 0.5)) - 1           # 艏柱前緣那一格（z 73.6 以上直立）
    tip = xs0 + E['len_beyond_stem']
    zt, th = E['deck_top_z'], E['thick']
    wpar = lambda x: E['half_at_tip'] + (E['half_at_stem'] - E['half_at_tip']) * (1 - (x - xs0) / float(E['len_beyond_stem'])) ** E['taper_pow']
    for x in range(xs0 + 1, tip + 1):
        w = int(math.floor(wpar(x) + 0.5))
        for dy in range(0, w + 1):
            for z in range(zt - th + 1, zt + 1):
                both('galjoen', x, dy, z, DECK if z == zt else TRIM)
        for z in range(zt + 1, zt + 1 + E['rail_h']):
            cap = z == zt + E['rail_h']
            if x > F['x'] - 6:
                continue                                              # head rail 停在獅子後面（收穫號 v1 跟船首像重疊）
            if cap or (x - xs0) % E['stanchion_every'] == 0:
                both('galjoen', x, w, z, GOLD if cap else WOOD)
            if cap:                                                   # 寬度往前收的地方補台階 ⇒ 頂條面相接（收穫號 v1 只在斜角相接）
                w2 = int(math.floor(wpar(x + 1) + 0.5))
                for dy in range(w2, w):
                    both('galjoen', x, dy, z, GOLD)
    z_cw0 = E['cutwater_from_z']
    for z in range(z_cw0, zt - th + 1):
        u = (z - z_cw0) / float(zt - th + 1 - z_cw0)
        xa = fwd.get(z, xs0) + 1
        xf = int(math.floor(xa + (tip - xa) * u ** E['cutwater_pow'] + 0.5))
        for x in range(max(xa, xf - E['cutwater_band']), max(xa, xf) + 1):
            for dy in range(0, E['cutwater_half'] + 1):
                both('galjoen', x, dy, z, GOLD if xf - x == 2 and dy == E['cutwater_half'] else TRIM)
    # ── 船首像：紅獅子（W p.85：長 9 呎、厚 19 duim、前端翹起 2'7"）——趴在喙尖上、往前往上翹 ──
    xr, ln, ht, rs = F['x'], F['len'], F['half_t'], F['raise']
    xf_ = xr + ln
    zc = lambda x: zt + 4 + rs * (x - xr) / float(ln)               # 身體中線的高度
    body, mane, crown, eye = F['body'], F['mane'], F['crown'], F['eye']
    for x in range(xr + 2, xf_ - 4):                                   # 身體（橢圓截面：半厚 ht、半高 3.2）
        for z in range(int(zc(x) - 4), int(zc(x) + 5)):
            for dy in range(0, int(ht) + 1):
                if (dy / ht) ** 2 + ((z + 0.5 - zc(x)) / 3.2) ** 2 <= 1.0:
                    both('figurehead', x, dy, z, body)
    hx, hz = xf_ - 3, zc(xf_) + 3                                       # 頭
    mx, mz = xf_ - 6, zc(xf_) + 2                                       # 鬃
    for x in range(xf_ - 11, xf_ + 1):
        for z in range(int(mz - 5), int(hz + 5)):
            for dy in range(0, 4):
                in_head = ((x + 0.5 - hx) / 3.2) ** 2 + (dy / ht) ** 2 + ((z + 0.5 - hz) / 3.2) ** 2 <= 1.0
                in_mane = ((x + 0.5 - mx) / 3.6) ** 2 + (dy / 3.0) ** 2 + ((z + 0.5 - mz) / 4.6) ** 2 <= 1.0
                if in_head:
                    both('figurehead', x, dy, z, body)
                elif in_mane:
                    both('figurehead', x, dy, z, mane)
    ztop = int(hz + 3.2)                                                # 金冠：頭頂一圈、上面一排尖
    for x in range(int(hx) - 2, int(hx) + 3):
        for dy in range(0, 3):
            both('figurehead', x, dy, ztop, crown)
            if (x + dy) % 2 == 0:
                both('figurehead', x, dy, ztop + 1, crown)
    both('figurehead', int(hx) + 2, 1, int(hz) + 1, eye)               # 眼睛
    for x0_, x1_ in ((xr + 3, xr + 6), (xf_ - 9, xf_ - 6)):           # 後腳、前腳：從喙的甲板面往上接到身體
        for x in range(x0_, x1_ + 1):
            for dy in (1, 2):
                for z in range(zt + 1, int(zc(x)) + 1):
                    both('figurehead', x, dy, z, body)
    for k, z in enumerate(range(int(zc(xr)), int(zc(xr)) + 7)):        # 尾巴：從屁股往後上翹，尾端一撮金
        put('figurehead', xr + 2 - k // 3, YC, z, mane if k >= 5 else body)
        if k and k % 3 == 0:                                            # 往後挪一格的那一階補一格 ⇒ 面相接（v1 只在斜角相接 ⇒ 尾端 1 格浮空）
            put('figurehead', xr + 3 - k // 3, YC, z, mane if k >= 5 else body)
    # ── 船尾走廊（hut 那排窗下面） ──
    S = plan['stern_deco']
    bal = S['balcony']
    zf, dep, hb = bal['floor_z'], bal['depth'], bal['half']
    for dy in range(0, hb + 1):
        fxa = aft.get((YC + dy, zf))
        if fxa is None:
            continue
        for x in range(fxa - dep, fxa):
            both('stern-deco', x, dy, zf, WOOD)
        xo = fxa - dep
        for z in range(zf + 1, zf + bal['rail_h'] + 1):
            cap = z == zf + bal['rail_h']
            if cap or dy % 3 == 0 or dy == hb:
                both('stern-deco', xo, dy, z, GOLD if cap else BLUE)
        if dy == hb:
            for z in range(zf + 1, zf + bal['rail_h'] + 1):
                fz = aft.get((YC + dy, z), fxa)                        # 鏡板往後倒：每一層的船尾位置不同
                for x in range(xo, min(fxa, fz)):
                    if z == zf + bal['rail_h'] or (x - xo) % 2 == 0:
                        both('stern-deco', x, dy, z, GOLD if z == zf + bal['rail_h'] else BLUE)
        if dy % 8 == 0:                                                # 托架：斜撐接回鏡板
            for j, z in enumerate(range(zf - 4, zf)):
                fz = aft.get((YC + dy, z))
                if fz is not None:
                    for x in range(fz - 1 - j, fz):
                        both('stern-deco', x, dy, z, WOOD)
    # ── 兩舷側廊（伸出 out 格；下面一節收成 0、上面一個銅頂） ──
    #   v2（Tim 2026-10-26「側面窗戶是否也能改成玻璃 且打通到艙內」）：
    #   · 每 8 格一個開間、開間的外面是直立的一片（照這一段船殼最外面那一格 ＋ out）⇒ 窗是方的（v1 外面順著船殼斜 ⇒ 每一格深淺不同、窗歪成 L 形）
    #   · 窗的玻璃另外一份清單（masks/glass/gallery_glass.vox.txt ⇒ -stern-glass 子作品，關聯 material=glass）；
    #     玻璃後面一路刻穿到艙裡：側廊這一段不放格、船殼的牆照 masks/deco/gallery_carve.vox.txt 刻（tools/hull_expected.py 的一步）
    Q = S['quarter_gallery']
    wrows = Q['win_rows']
    obody = {}
    for x in range(Q['x0'], Q['x1'] + 1):
        vs = [outer[(x, z)] for z in range(Q['z0'] + 5, Q['z1'] + 1) if (x, z) in outer and (x, YC + outer[(x, z)], z) in occ]
        if vs:
            obody[x] = max(vs)
    bay = lambda x: (x - Q['x0']) // 8
    fy = {}
    for x, o in obody.items():
        fy[bay(x)] = max(fy.get(bay(x), -1), o + Q['out'])
    gal_glass, gal_shaft = {}, set()
    for x in range(Q['x0'], Q['x1'] + 1):
        for z in range(Q['z0'], Q['z1'] + 1):
            if (x - Q['x0']) % 8 in (3, 4, 5) and any(a_ <= z <= b_ for a_, b_ in wrows) and bay(x) in fy:
                gal_glass[(x, YC + fy[bay(x)], z)] = GLASS_REAL
                gal_shaft.add((x, z))
    for x in range(Q['x0'], Q['x1'] + 1):
        if bay(x) not in fy:
            continue
        F = fy[bay(x)]
        for z in range(Q['z0'], Q['z1'] + Q['roof_h'] + 1):
            hz_ = min(z, Q['z1'])
            o = outer.get((x, hz_))
            if o is None or (x, YC + o, hz_) not in occ:
                continue
            ext = F - o
            if z <= Q['z0'] + 4:
                out = max(1, round(ext * (z - Q['z0'] + 1) / 5.0))
            elif z > Q['z1']:
                k = z - Q['z1']
                out = max(0, ext - k)
                inset = 2 * k
                if x < Q['x0'] + inset or x > Q['x1'] - inset or out == 0:
                    continue
            else:
                out = ext
            for d in range(1, out + 1):
                face = d == out
                if (x, z) in gal_shaft and z <= Q['z1']:
                    continue                                           # 窗：外面那一格是玻璃（另一份清單）、裡面一路空到船殼
                c = BLUE
                if z > Q['z1']:
                    c = GOLD if z == Q['z1'] + 1 else Q['roof']
                elif z in (Q['z0'] + 4, Q['z1']):
                    c = GOLD
                elif face and (x - Q['x0']) % 8 in (2, 3, 4, 5, 6) and any(a_ - 1 <= z <= b_ + 1 for a_, b_ in wrows):
                    c = GOLD
                elif face and (x - Q['x0']) % 8 in (0, 7):
                    c = TRIM                                           # 開間之間的壁柱
                both('stern-deco', x, o + d, z, c)
    # 船殼的牆：窗那一欄從外面往裡刻到第一格空氣（只刻船殼的格；碰到別的件 ⇒ 照實報）
    gal_carve, gal_block = {}, []
    for (x, z) in sorted(gal_shaft):
        for sgn in (1, -1):
            o = outer.get((x, z))
            y = YC + sgn * o
            n = 0
            while (x, y, z) in occ and n < 12:
                if (x, y, z) not in hull_cells:
                    gal_block.append((x, y, z))
                    break
                gal_carve[(x, y, z)] = hull_col[(x, y, z)]
                y -= sgn
                n += 1
            if n >= 12:
                gal_block.append((x, y, z))
    for (x, y, z), c in list(gal_glass.items()):
        gal_glass[(x, 2 * YC - y, z)] = c
    # ── hackebort：鏡板頂上那塊板（順著鏡板往後倒、頂上拱形）；奶油底、藍帶金字、藍鯊紋章 ──
    H = S['hackebort']
    z0, z1, half, af, htop = H['z0'], H['z1'], H['half'], H['arch_from'], H['half_top']
    rake = math.tan(math.radians(plan['lines']['sternpost_rake_deg']['v']))
    zb = z0 - 1                                                         # 坐在船殼頂那一層上
    halfz = lambda z: half if z < af else htop + (half - htop) * math.sqrt(max(0.0, 1 - ((z - af + 0.5) / float(z1 - af + 1)) ** 2))
    base = {}
    for dy in range(-half, half + 1):                                   # 每一欄的船尾位置照船殼頂那一層；船殼頂比板窄的那幾欄照最近的一欄
        b = aft.get((YC + dy, zb))
        if b is None:
            for k in range(1, 6):
                b = aft.get((YC + (dy - k if dy > 0 else dy + k), zb))
                if b is not None:
                    break
        base[dy] = b
    face = {}
    for z in range(z0, z1 + 1):
        hw = halfz(z)
        for dy in range(-half, half + 1):
            if abs(dy) > hw + 1e-9 or base[dy] is None:
                continue
            xf0 = base[dy] - int((z - zb) * rake + 0.5)
            edge = abs(dy) + 1 > hw or z in (z0, z1) or abs(dy) + 1 > halfz(z + 1)
            for t in range(H['thick']):
                put('hackebort', xf0 + t, YC + dy, z, H['border'] if edge else H['field'])
            face[(dy, z)] = xf0
    R_ = H['ribbon']
    for (dy, z), xf0 in face.items():                                   # 名帶（只換最外那一層）
        if R_['z0'] < z < R_['z1'] and abs(dy) < half - 1:
            put('hackebort', xf0, YC + dy, z, R_['color'])
    text = R_['text']
    wtxt = sum(len(FONT[ch][0]) for ch in text) + (len(text) - 1)
    ycur = -(wtxt // 2)
    for ch in text:                                                     # 從船尾看左手 ＝ −y ⇒ 第一個字在 y 最小那邊
        g = FONT[ch]
        for c in range(len(g[0])):
            for r in range(5):
                if g[r][c] == 'X':
                    z = R_['z1'] - 1 - r
                    put('hackebort', face[(ycur + c, z)], YC + ycur + c, z, R_['text_color'])
        ycur += len(g[0]) + 1
    SH = H['shark']                                                     # 藍鯊：頭朝左（−y）
    wsh = len(SH['rows'][0])
    for r, row in enumerate(SH['rows']):
        z = SH['z_top'] - r
        for c, ch in enumerate(row):
            if ch in SH:
                dy = c - wsh // 2
                put('hackebort', face[(dy, z)], YC + dy, z, SH[ch])
    # 裝飾不蓋船的格：落在佔用格上的照實數出來、不放
    skipped = {}
    for nm in list(parts):
        bad = [k for k in parts[nm] if k in occ]
        skipped[nm] = len(bad)
        for k in bad:
            del parts[nm][k]
    if probe:
        nm, dv = probe[0].split('=')[1].split(':')
        parts[nm] = {(x, y + int(dv), z): c for (x, y, z), c in parts[nm].items()}

    # ── 讀數 ──
    R = {'parts': {}, 'skipped_on_ship': skipped}
    allk = {}
    for nm, cells in parts.items():
        ks = set(cells)
        ov = len(ks & occ)
        touch = sum(1 for (x, y, z) in ks if any(n in occ for n in ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1), (x, y, z - 1))))
        mir = sum(1 for (x, y, z), c in cells.items() if cells.get((x, 2 * YC - y, z)) != c)
        cross = sum(1 for k in ks if k in allk)
        for k in ks:
            allk[k] = nm
        bb = np.array(list(ks))
        R['parts'][nm] = {'cells': len(ks), 'overlap_ship': ov, 'overlap_other_parts': cross, 'cells_touching_ship': touch, 'mirror_diff': mir,
                          'bbox': [bb.min(axis=0).tolist(), bb.max(axis=0).tolist()],
                          'colors': {int(c): int(n) for c, n in zip(*np.unique(np.array(list(cells.values())), return_counts=True))}}
    B = LY.bowsprit(plan)                                               # 艏斜桅那一條線（半徑 3）有沒有被喙、獅子擋到
    a = math.radians(B['angle'])
    hit = 0
    for (x, y, z) in allk:
        t = (x + 0.5 - B['x0']) * math.cos(a) + (z + 0.5 - B['z0']) * math.sin(a)
        if 0 <= t <= B['len']:
            px, pz = B['x0'] + t * math.cos(a), B['z0'] + t * math.sin(a)
            if (x + 0.5 - px) ** 2 + (y - YC) ** 2 + (z + 0.5 - pz) ** 2 <= 3.0 ** 2:
                hit += 1
    R['bowsprit_clearance_hits'] = hit
    LA = S['lanterns']
    R['lanterns'] = []
    for dy in LA['dy']:
        xl = face[(dy, z1)]
        R['lanterns'].append({'dy': dy, 'at': [xl + 1.0, YC + dy + 0.5, z1 + 1], 'on_solid': (xl, YC + dy, z1) in allk,
                              'air_above': (xl, YC + dy, z1 + 1) not in occ and (xl, YC + dy, z1 + 1) not in allk})
    if probe:
        print(json.dumps({'probe': probe[0], 'parts': {k: {kk: v[kk] for kk in ('overlap_ship', 'mirror_diff', 'cells_touching_ship')} for k, v in R['parts'].items()}}, ensure_ascii=False))
        return
    od = os.path.join(design, 'masks', 'deco')
    os.makedirs(od, exist_ok=True)
    R['lists'] = {}
    for nm, cells in parts.items():
        p = os.path.join(od, nm + '.vox.txt')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 藍鯊號 %s（draft_deco.py；世界座標，at 0,0,0）\n' % nm)
            for (x, y, z) in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (x, y, z, cells[(x, y, z)]))
        R['lists'][nm] = [len(cells), hashlib.sha256(open(p, 'rb').read()).hexdigest()]
    # 側廊 v2：玻璃與船殼要刻的窗洞
    os.makedirs(os.path.dirname(gg_path), exist_ok=True)
    for path, cells, head in ((gg_path, gal_glass, '# 藍鯊號 側廊窗玻璃（draft_deco.py 側廊 v2；1 格厚、後面一路空到艙裡；併進 -stern-glass 子作品）'),
                              (gc_path, gal_carve, '# 藍鯊號 側廊窗洞：船殼的牆要刻的格（carvevox；第 4 欄 ＝ 刻之前的顏色，守門；tools/hull_expected.py 的一步）')):
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head + '\n')
            for k in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (k + (cells[k],)))
        R['lists'][os.path.basename(path)] = [len(cells), hashlib.sha256(open(path, 'rb').read()).hexdigest()]
    allparts = set(allk)
    left = {k for k in occ if k not in gal_carve}
    deep = {}
    for (x, y, z) in gal_carve:
        k = (x, z, 1 if y > YC else -1)
        deep[k] = min(deep.get(k, 10 ** 6), abs(y - YC))
    shafts = {(x, z, 1 if y > YC else -1) for (x, y, z) in gal_glass}
    reach = sum(1 for (x, z, sg) in shafts if (x, z, sg) in deep and (x, YC + sg * (deep[(x, z, sg)] - 1), z) not in left)
    R['gallery_v2'] = {'glass': len(gal_glass), 'hull_carve': len(gal_carve), 'blocked': [list(b) for b in gal_block[:6]], 'blocked_n': len(gal_block),
                       'glass_on_ship': sum(1 for k in gal_glass if k in occ and k not in gal_carve), 'glass_on_parts': sum(1 for k in gal_glass if k in allparts),
                       'shafts': len(shafts), 'shafts_reach_cabin': reach, 'glass_mirror_diff': sum(1 for (x, y, z) in gal_glass if (x, 2 * YC - y, z) not in gal_glass),
                       'carve_mirror_diff': sum(1 for (x, y, z) in gal_carve if (x, 2 * YC - y, z) not in gal_carve)}
    # 圖：船頭側面、船尾正面
    sc = 6
    im = Image.new('RGB', (1560, 900), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((20, 10), '藍鯊號 新圖紙 05：galjoen、紅獅子、船尾走廊、側廊、hackebort（藍鯊紋章）　v1', fill=(0, 0, 0), font=font(18))
    deco = [(k, c) for nm, cells in parts.items() for k, c in cells.items()]
    hullcells = [((x, y, z), c) for x, y, z, c in A.tolist() if x >= 480 or x <= 200]
    best = {}
    for (x, y, z), c in hullcells + deco:
        if x < 480 or y < YC:
            continue
        if y > best.get((x, z), (-1, 0))[0]:
            best[(x, z)] = (y, c)
    for (x, z), (y, c) in best.items():
        if 480 <= x <= 610 and 15 <= z <= 110:
            X, Y = 20 + (x - 480) * sc, 50 + (110 - z) * sc
            d.rectangle([X, Y, X + sc - 1, Y + sc - 1], fill=palette_rgb(int(c)))
    d.text((20, 50 + 96 * sc), '船頭（右舷側面）', fill=(0, 0, 0), font=font(14))
    best = {}
    for (x, y, z), c in hullcells + deco:
        if x > 200:
            continue
        if x < best.get((y, z), (10 ** 6, 0))[0]:
            best[(y, z)] = (x, c)
    ox, oy, s2 = 840, 50, 6
    for (y, z), (x, c) in best.items():
        if 60 <= z <= 132 and 110 <= y <= 210:
            X, Y = ox + (y - 110) * s2, oy + (132 - z) * s2
            d.rectangle([X, Y, X + s2 - 1, Y + s2 - 1], fill=palette_rgb(int(c)))
    d.text((ox, oy + 74 * s2), '船尾正面（從船尾看，左手 ＝ −y）', fill=(0, 0, 0), font=font(14))
    im.save(os.path.join(design, 'sheet05_deco_v1.png'))
    with open(os.path.join(design, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'lists'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
