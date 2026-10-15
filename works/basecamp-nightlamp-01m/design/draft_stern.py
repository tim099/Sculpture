# 夜燈號 船尾（鬼盜船化，2026-10-15；Tim：「繼續造船 參考鬼盜船 加入更多鬼盜船的元素」「船頭 船尾的建築&弧線可以參考鬼盜船」
#   ＋ Tim 給的船尾模型照「船尾特徵」—— 只看不收）
#   船殼現況（export format=list，船殼作品本身）＋ 組裝件現況（同上，判空氣）＋ 本檔配置 ⇒
#   masks/stern/add.vox.txt（要加的格，船殼座標）、masks/stern/carve.vox.txt（要刻掉的格，帶現在的顏色守門）、verify_stern.json
# 用法：python -I draft_stern.py <design 資料夾> <船殼 list> <組裝件 list>
# v3（照模型照）：
#   · 窗盒：整排船尾窗是一個往外凸的盒子 —— 下面一道托板（ledge）、上面壓一道厚簷口（cornice）、托板底下一排托架小像（corbels）。（讀圖）
#   · 拱窗每排 5 扇、窗裡是直條格（讀圖：模型一排 5 扇）。⚠ 夜燈號船尾有兩層艙（大艙 Z 110–139、船尾樓艙 Z 142–161）⇒ 窗盒裡兩排 —— 這是我的改編。
#   · 簷口上面的船尾頂改成鏤空捲草（openwork scrollwork，看得穿到船尾樓甲板）（讀圖）；正中留營地的山與營火當徽（notes「個人化特色」）。
#   · 船尾頂整體是拱（中間高 1 m）。
#   · 兩舷 quarter gallery（船尾兩角往外凸的圓弧艙）：續集 VFX 船殼有「quarter-galley windows」（CGW 2007）；Tim 給的右舷模型照看得到（讀圖）。
#   · 三盞船尾燈（中間高、兩角各一，插在柱上）是**模型**（-lantern-01m），不在這份遮罩裡 —— 草稿給 Tim 看過才掛。
#     「三盞」有出處（bricknerd 2025、周邊商品；二手）＋ 模型照（讀圖）。
#   ⚠ 尺寸、窗數、捲草的畫法都是設計；鬼盜船的船尾窗數與形狀查不到文字出處（研究 agent 2026-10-15：not found）。
# v1 → v2 → v3：v1 平的兩排六窗＋三道腰線、火像空心的「A」；v2 雙峰的山、火舌；v3 照 Tim 的船尾模型照改成窗盒＋鏤空船尾頂。
import sys, os, json, math
import numpy as np
from scipy import ndimage

BLACK, TRIM, GLASS, FLAME, LOG, SNOW = 36, 73, 5, 240, 100, 182   # RGB332：#242400 黑、#494955 窗框灰、#002455 深藍玻璃、#FF9200 橘、#6D2400 柴、#B6B6AA 雪頂
CORE, TIP = 252, 224                                               # #FFFF00 火芯、#FF0000 火尖
YC = 160                          # 中線；船殼兩舷鏡像 y' ＝ 320 − y
# 窗盒：y 範圍、z 範圍、每個 z 往外凸幾格（從船尾板外表面算；正面在同一個 z 是一個平面）
BOX_Y = (120, 200)
BOX_DEPTH = {**{z: 6 for z in range(110, 113)}, **{z: 4 for z in range(113, 158)},
             158: 5, 159: 6, 160: 7, 161: 7, 162: 6, 163: 5}
# 拱窗：每排 (窗台 z, 直邊頂 z, 拱頂 z)、五扇（寬 11、窗間 5，中間那扇對中線）
TIERS = {'A': (116, 130, 136), 'B': (143, 150, 156)}
WIN_Y = [(123 + 16 * k, 133 + 16 * k) for k in range(5)]
# 托架小像：7 個，托板底下
CORBEL_Y = [YC + 12 * k for k in range(-3, 4)]
CORBEL_Z = (100, 109)
# 鏤空船尾頂：左半塊（右半塊鏡像）、中間的徽
PANEL = dict(y0=121, y1=141, z0=166, z1=194)
MEDAL = dict(y0=142, y1=178)
# quarter gallery（右舷算，左舷鏡像）：平面是半個橢圓，貼在船殼外面
QG = dict(x0=70, x1=98, z0=114, z1=160, out=8, dome=8, drop=14)
QG_WIN_X = [(75, 79), (82, 86), (89, 93)]
QG_BANDS = [(113, 114), (139, 140), (159, 160)]
CREST_H = 10
WALL_MAX = 7                      # 船尾板厚 4–6 格（probe：中線 Z 110–194）


def load(path):
    return np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def grid(a):
    X0, X1, Z1 = 40, 150, 230
    g = np.zeros((X1 - X0, 321, Z1), np.int16)
    s = (a[:, 0] >= X0) & (a[:, 0] < X1) & (a[:, 2] < Z1)
    g[a[s, 0] - X0, a[s, 1], a[s, 2]] = a[s, 3] + 1        # 0 ＝ 空；顏色 ＋1
    return g, X0


def arch_window(ya, yb, zs, zr, zt):
    cy, hw = (ya + yb) / 2, (yb - ya + 1) / 2
    return {(y, z) for z in range(zs, zt + 1) for y in range(ya, yb + 1)
            if z <= zr or ((y - cy) / hw) ** 2 + ((z - zr) / (zt - zr + 0.5)) ** 2 <= 1.0}


def stroke(points, width=1.0):
    """沿一串 (y,z) 點，離線段 ≤ width 的格。"""
    out = set()
    for (y0, z0), (y1, z1) in zip(points, points[1:]):
        n = max(2, int(math.hypot(y1 - y0, z1 - z0) * 4))
        for i in range(n + 1):
            t = i / n
            py, pz = y0 + (y1 - y0) * t, z0 + (z1 - z0) * t
            for y in range(int(py - width - 1), int(py + width + 2)):
                for z in range(int(pz - width - 1), int(pz + width + 2)):
                    if math.hypot(y + 0.5 - py, z + 0.5 - pz) <= width:
                        out.add((y, z))
    return out


def spiral(cy, cz, r0, r1, th0, turns, sign):
    pts = []
    for i in range(121):
        t = i / 120
        th = math.radians(th0 + sign * 360 * turns * t)
        r = r0 + (r1 - r0) * t
        pts.append((cy + r * math.cos(th), cz + r * math.sin(th)))
    return pts


def scroll_left():
    """左半塊的捲草：一個 S（下大捲往裡、上小捲往裡反向）＋一片葉，筆畫寬約 2 格。"""
    a = spiral(128.0, 173.5, 6.0, 1.5, 90, 1.5, -1)
    b = spiral(135.0, 186.5, 5.5, 1.5, 270, 1.5, +1)
    s = stroke(a) | stroke(b) | stroke([a[0], (131.5, 180.5), b[0]])
    s |= stroke([(122.5, 191.5), (126.0, 189.0), (128.5, 185.0)])        # 葉
    return s


def main(design, hull_list, asm_list):
    H, X0 = grid(load(hull_list))
    A, _ = grid(load(asm_list))
    h, aocc = H > 0, A > 0
    add, carve = {}, set()

    def outer_x(y, z):
        xs = np.nonzero(h[:, y, z])[0]
        return int(xs[0]) + X0 if len(xs) else None

    def wall(y, z):
        """(y,z) 那一欄船尾板的格：從外表面往裡直到空氣，最多 WALL_MAX 格。
        ⚠ 不設上限 ⇒ 靠邊那幾欄（y 123）會順著船尾樓的側牆一路刻進去，把側牆上的東西刻斷（v3 第一次跑，浮空斷言擋下）。"""
        x0 = outer_x(y, z)
        out = []
        x = x0
        while h[x - X0, y, z] and x < x0 + WALL_MAX:
            out.append(x)
            x += 1
        return out

    def put(x, y, z, c, over=False):
        if aocc[x - X0, y, z] and (x, y, z) not in carve:
            return False
        if (x, y, z) in add and not over:
            return False
        add[(x, y, z)] = c
        return True

    stats = {}
    # ── 窗盒 ──
    windows = set()
    for t, (zs, zr, zt) in TIERS.items():
        for ya, yb in WIN_Y:
            windows |= arch_window(ya, yb, zs, zr, zt)
    face = {}
    for z, d in BOX_DEPTH.items():
        xs = [outer_x(y, z) for y in range(BOX_Y[0], BOX_Y[1] + 1)]
        assert all(x is not None and x < 100 for x in xs), ('窗盒那一列不是船尾板', z)
        face[z] = min(xs) - d
        for y in range(BOX_Y[0], BOX_Y[1] + 1):
            if (y, z) in windows:
                continue
            for x in range(face[z], outer_x(y, z)):
                put(x, y, z, BLACK)
    stats['box'] = len(add)
    # 窗：刻穿船尾板，玻璃（直條格）放在原本的外表面那一格；窗框凸出窗盒正面 1 格
    glass = 0
    for (y, z) in windows:
        for x in wall(y, z):
            carve.add((x, y, z))
        x0 = outer_x(y, z)
        ya = next(a for a, b in WIN_Y if a <= y <= b)
        add[(x0, y, z)] = TRIM if (y - ya) % 2 == 1 else GLASS
        glass += 1
    frame = 0
    for (y, z) in windows:
        for dy, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            q = (y + dy, z + dz)
            if q not in windows and q[1] in face and put(face[q[1]] - 1, q[0], q[1], TRIM):
                frame += 1
    stats.update(window_cells=glass, frame=frame)
    # 托板與簷口的邊：最外那一格換窗框色（一條細線）
    for z in (110, 160, 161):
        for y in range(BOX_Y[0], BOX_Y[1] + 1):
            if (face[z], y, z) in add:
                add[(face[z], y, z)] = TRIM
    # ── 托架小像（托板底下）──
    corbel = 0
    zc0, zc1 = CORBEL_Z
    for cy in CORBEL_Y:
        for z in range(zc0, zc1 + 1):
            p = 1 + int(round((z - zc0) * 5 / (zc1 - zc0)))
            for y in range(cy - 1, cy + 2):
                x0 = outer_x(y, z)
                for x in range(x0 - p, x0):
                    if put(x, y, z, BLACK):
                        corbel += 1
        for z in range(zc0 + 3, zc0 + 6):                               # 頭：往外多凸 1 格、窗框色
            for y in range(cy - 1, cy + 2):
                x0 = outer_x(y, z)
                p = 1 + int(round((z - zc0) * 5 / (zc1 - zc0)))
                if put(x0 - p - 1, y, z, TRIM):
                    corbel += 1
    stats['corbels'] = corbel
    # ── 鏤空船尾頂 ──
    left = scroll_left()
    keep_l = set()
    P = PANEL
    for y in range(P['y0'], P['y1'] + 1):
        for z in range(P['z0'], P['z1'] + 1):
            border = y <= P['y0'] + 1 or y >= P['y1'] - 1 or z <= P['z0'] + 1 or z >= P['z1'] - 1
            if border or (y, z) in left:
                keep_l.add((y, z))
    pierced = raised = 0
    for side in (1, -1):
        for y0 in range(P['y0'], P['y1'] + 1):
            y = y0 if side == 1 else 2 * YC - y0
            for z in range(P['z0'], P['z1'] + 1):
                if (y0, z) in keep_l:
                    if (y0, z) in left and put(outer_x(y, z) - 1, y, z, TRIM):
                        raised += 1
                    continue
                for x in wall(y, z):
                    carve.add((x, y, z))
                    pierced += 1
    stats.update(pierced=pierced, scroll_raised=raised)
    # 徽：外框凸一格（窗框色），裡面浮雕山與營火
    M = MEDAL
    for y in range(M['y0'], M['y1'] + 1):
        for z in range(P['z0'], P['z1'] + 1):
            if y in (M['y0'], M['y1']) or z in (P['z0'], P['z1']):
                put(outer_x(y, z) - 1, y, z, TRIM)
    relief = 0
    base_z = 168
    peaks = [(YC - 5, 191), (YC + 9, 183)]          # 雙峰（v1 一個正三角形，太像路標）
    for y in range(M['y0'] + 2, M['y1'] - 1):
        top = max(pz - abs(y - py) * 1.45 for py, pz in peaks)
        for z in range(base_z, min(int(top), P['z1'] - 2) + 1):
            snow = z >= top - 2 and top >= 179          # 稜線最上面 3 格、只在兩個峰頂
            if put(outer_x(y, z) - 1, y, z, SNOW if snow else TRIM, over=True):
                relief += 1
    for (y, z, c) in fire_cells(YC, base_z):
        x0 = outer_x(y, z)
        if put(x0 - 2 if c != LOG else x0 - 1, y, z, c, over=True):
            relief += 1
    stats['relief'] = relief
    # ── 船尾頂的拱 ──
    tops = {}
    for y in range(100, 221):
        zs_ = [z for z in range(150, 229) if h[:30, y, z].any()]
        if zs_:
            tops[y] = max(zs_)
    ys = sorted(tops)
    yl, yr = ys[0], ys[-1]
    half = (yr - yl) / 2
    crest = 0
    for y in ys:
        k = 1 - ((y - YC) / (half + 0.5)) ** 2
        hh = int(round(CREST_H * math.sqrt(max(k, 0))))
        zt = tops[y]
        xs = [x + X0 for x in np.nonzero(h[:30, y, zt])[0]]
        for z in range(zt + 1, zt + hh + 1):
            for x in xs:
                edge = (z == zt + hh) or (z >= zt + hh - 1 and x == min(xs))
                if put(x, y, z, TRIM if edge else BLACK):
                    crest += 1
    stats.update(crest=crest, crest_y=[yl, yr])
    # ── quarter gallery（右舷，算完鏡像到左舷）──
    qg = {}
    L = (QG['x1'] - QG['x0']) / 2
    xc = (QG['x0'] + QG['x1']) / 2
    for x in range(QG['x0'], QG['x1'] + 1):
        e_plan = QG['out'] * math.sqrt(max(0.0, 1 - ((x - xc) / (L + 0.5)) ** 2))
        for z in range(QG['z0'] - QG['drop'], QG['z1'] + QG['dome'] + 1):
            if z < QG['z0']:
                e = e_plan * ((z - (QG['z0'] - QG['drop'])) / QG['drop']) ** 0.7
            elif z > QG['z1']:
                e = e_plan * math.sqrt(max(1 - (z - QG['z1']) / QG['dome'], 0))
            else:
                e = e_plan
            n = int(round(e))
            if n <= 0:
                continue
            ys_ = np.nonzero(h[x - X0, YC:, z])[0]
            if not len(ys_):
                continue
            side = YC + int(ys_.max())
            tier = 'A' if 117 <= z <= 133 else ('B' if 146 <= z <= 157 else None)
            inwin = tier and any(a <= x <= b for a, b in QG_WIN_X)
            nearwin = tier and any(a - 1 <= x <= b + 1 for a, b in QG_WIN_X)
            for k in range(1, n + 1):
                outer = k == n
                if outer and inwin:
                    continue                                   # 窗：外層空著，玻璃在下一層
                c = BLACK
                if k == n - 1 and inwin:
                    c = GLASS
                elif outer and (nearwin or any(za <= z <= zb for za, zb in QG_BANDS)):
                    c = TRIM
                qg[(x, side + k, z)] = c
    lowest = min(z for (_, _, z) in qg)
    tip = [(x, y, z) for (x, y, z) in qg if z == lowest]
    tx, ty = int(round(np.mean([p[0] for p in tip]))), int(round(np.mean([p[1] for p in tip])))
    for dz in range(1, 4):
        qg[(tx, ty, lowest - dz)] = TRIM                          # 垂飾尖端
    assert not [p for p in qg if aocc[p[0] - X0, p[1], p[2]]], 'quarter gallery 撞到現有的格'
    for (x, y, z), c in qg.items():
        add[(x, y, z)] = c
        assert not aocc[x - X0, 2 * YC - y, z], ('左舷鏡像撞到現有的格', x, 2 * YC - y, z)
        add[(x, 2 * YC - y, z)] = c
    stats['quarter_gallery_each'] = len(qg)
    # ── 檢查 ──
    stats['asym'] = sum(1 for p, c in add.items() if add.get((p[0], 2 * YC - p[1], p[2])) != c)
    stats['asym_carve'] = sum(1 for p in carve if (p[0], 2 * YC - p[1], p[2]) not in carve)
    pts = list(add) + list(carve)
    lo = np.array([min(p[i] for p in pts) for i in range(3)]) - 3
    hi = np.array([max(p[i] for p in pts) for i in range(3)]) + 4
    sub = h[lo[0] - X0:hi[0] - X0, lo[1]:hi[1], lo[2]:hi[2]].copy()
    for (x, y, z) in carve:
        sub[x - lo[0], y - lo[1], z - lo[2]] = False
    new = np.zeros_like(sub)
    for (x, y, z) in add:
        new[x - lo[0], y - lo[1], z - lo[2]] = True
    both = sub | new
    lab, _ = ndimage.label(both)
    # 錨定：外框邊上（跟外面的船殼相連）的那幾塊
    edge = np.zeros_like(both)
    edge[[0, -1], :, :] = edge[:, [0, -1], :] = edge[:, :, [0, -1]] = True
    anchored = set(np.unique(lab[edge & both])) - {0}
    # 對照：改之前（只有船殼本身）在這個框裡就沒接到框邊的格 ＝ 本來就靠別件作品（甲板…）撐著，不算這次的帳
    sub0 = h[lo[0] - X0:hi[0] - X0, lo[1]:hi[1], lo[2]:hi[2]]
    lab0, _ = ndimage.label(sub0)
    was_anchored = np.isin(lab0, list(set(np.unique(lab0[edge & sub0])) - {0}))
    floating, preexisting = [], []
    for L in sorted(set(np.unique(lab[both])) - anchored - {0}):
        m = lab == L
        info = (int(m.sum()), (np.argwhere(m).min(0) + lo).tolist(), (np.argwhere(m).max(0) + lo).tolist())
        (floating if (m & new).any() or (m & was_anchored).any() else preexisting).append(info)
    stats['floating'] = floating[:10]
    stats['preexisting_unanchored_in_box'] = preexisting[:10]
    assert not floating, ('浮空', floating[:10])
    carve = {p: int(H[p[0] - X0, p[1], p[2]]) - 1 for p in carve}      # 帶現在的顏色 ⇒ carvevox 守門
    stats.update(carve=len(carve), add=len(add), colors={str(c): sum(1 for v in add.values() if v == c) for c in sorted(set(add.values()))})
    write(design, add, carve, stats)


def fire_cells(yc, zb):
    """營火：柴（LOG）＋三條火舌（芯亮黃 CORE、外橘 FLAME、尖紅 TIP），貼在山腳正中。
    v1 是一個實心三角、芯用 GOLD 177（#B69255 偏褐）⇒ 渲染出來像一個空心的「A」，不像火 ⇒ v2 改火舌＋亮色芯。"""
    out = []
    for k in range(-6, 7):
        out.append((yc + k, zb + 1, LOG))
    for k in (-3, -2, 2, 3):
        out.append((yc + k, zb + 2, LOG))
    tongues = [(0, [3, 3, 3, 2, 2, 2, 1, 1, 0, 0]), (-4, [1, 1, 1, 0, 0]), (4, [1, 1, 1, 0, 0])]
    cells = {}
    for cy, prof in tongues:
        for i, w in enumerate(prof):
            z = zb + 2 + i
            for dy in range(-w, w + 1):
                c = TIP if i >= len(prof) - 2 else (CORE if abs(dy) < w and i < len(prof) - 4 else FLAME)
                key = (yc + cy + dy, z)
                if cells.get(key) != CORE:
                    cells[key] = c
    out += [(y, z, c) for (y, z), c in cells.items()]
    return out


def write(design, add, carve, stats):
    out = os.path.join(design, 'masks', 'stern')
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'add.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 夜燈號 船尾（鬼盜船化）要加的格：%d 格，船殼座標\n' % len(add))
        for (x, y, z), c in sorted(add.items()):
            f.write('%d,%d,%d,%d\n' % (x, y, z, c))
    with open(os.path.join(out, 'carve.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 夜燈號 船尾窗與鏤空要刻掉的格：%d 格，船殼座標（帶現在的顏色）\n' % len(carve))
        for (x, y, z), c in sorted(carve.items()):
            f.write('%d,%d,%d,%d\n' % (x, y, z, c))
    json.dump(stats, open(os.path.join(design, 'verify_stern.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(*sys.argv[1:4])
