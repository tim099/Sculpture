# 夜燈號 彈藥庫（Tim 2026-10-15：「補夜燈號的水線 meta 和彈藥庫」；ame shipcheck ⚠「夜燈號沒有彈藥庫」）
#   組裝件現況（export format=list）＋ 本檔配置 ⇒
#   masks/magazine/magazine.vox.txt（子作品座標，原點 ＝ 外框最小角）、magazine_placement.json、verify_magazine.json
# 用法：python -I draft_magazine.py <design 資料夾> <組裝件 list 匯出檔>
# 做法照抄餘燼號 design/draft_magazine_mid.py（階段二十一），差別只在配置：
#   ① 夜燈號是商船型，下甲板（level 0）底下整個是貨艙、沒有 orlop ⇒ 房間自己鋪天花板。
#   ② 位置：船尾貨艙 X 248–272（後艙口 X 278–298 的正後方；放船尾是設計 —— 印象中商船的 powder room 在船尾，⚠ 沒查出處）；門開在船頭那道艙壁、對著後艙口。
#      keelson 頂在這一段 Z 22–25 ⇒ 桶站 Z 26（地板板 Z 25）。
#   ③ 桶數照 22 門砲換算：憲法號 54 門 138 桶 ⇒ ×22/54 ≈ 56 桶（5,600 磅），排到 56 就停。⚠ 換算，不是史料。
# 火藥桶模型沿用憲法號 -powder-barrel（0.02 m，scale 0.2 明寫）。
import sys, os, json, math
import numpy as np
from scipy import ndimage

COPPER, OAK, DARK, PINE = 168, 136, 104, 177
YC = 160
X0, X1 = 248, 272            # 兩道橫艙壁（2.5 m）：船頭那道離後艙口（X 278）留 5 格；X0 試過 236（地板容量 118 ⇒ 只鋪一半）、252（54 ⇒ 要上架）⇒ 248（70，地板放 56）
F = 26                       # 桶站的那一格（地板板在 F−1 ＝ z 25）
ZTOP = 42                    # 房間最高那一格（淨高 1.7 m，同餘燼號）
CEIL = 43                    # 天花板（自己鋪；上面到下甲板底 Z 73 還是貨艙）
DOOR = 'fore'
DOOR_W, DOOR_HEAD = 5, 3
CAP = 56
BARREL = dict(mpv=0.02, d_bilge=22, d_head=19, h=27)
TIER = 7


def load(path):
    return np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def room(occ):
    """每個 x：(y,z) 橫切面裡、z F−1..CEIL 之間，中線兩側最近的空氣各一塊（4 連通）。"""
    interior, log = {}, []
    for x in range(X0, X1 + 1):
        air = ~occ[x]
        band = np.zeros_like(air)
        band[:, F - 1:CEIL + 1] = air[:, F - 1:CEIL + 1]
        lab, _ = ndimage.label(band)
        I = np.zeros_like(band)
        sides = []
        for sgn in (-1, 1):
            ys = [y for y in range(YC, YC + sgn * 80, sgn) if band[y, F + 1]]
            if ys:
                I |= lab == lab[ys[0], F + 1]
                sides.append(ys[0])
        if not I.any():
            log.append({'x': x, 'skip': 'no air at floor+1'})
            continue
        interior[x] = I
        ys, zs = np.nonzero(I)
        log.append({'x': x, 'cells': int(I.sum()), 'y': [int(ys.min()), int(ys.max())], 'pillar': bool(occ[x, YC, F + 1]), 'seeds': sides})
    return interior, log


def build(occ):
    interior, log = room(occ)
    cells = {}
    for x in sorted(interior):
        I = interior[x]
        wall = x in (X0, X1)
        door_x = (DOOR == 'aft' and x == X0) or (DOOR == 'fore' and x == X1)
        for y, z in zip(*np.nonzero(I)):
            y, z = int(y), int(z)
            if z == F - 1:
                cells[(x, y, z)] = OAK if (y - YC) % 6 == 0 else PINE            # 地板：松木、每 6 格橡木壓條
            elif z == CEIL:
                cells[(x, y, z)] = OAK if (x - X0) % 8 == 0 or wall else PINE    # 天花板：松木、每 8 格一道橡木樑
            elif wall:
                if door_x and abs(y - YC) <= DOOR_W // 2 and z <= ZTOP - DOOR_HEAD:
                    continue
                frame = (y - YC) % 8 == 0 or z == F or z == ZTOP
                if door_x and abs(y - YC) == DOOR_W // 2 + 1 and z <= ZTOP - DOOR_HEAD + 1:
                    frame = True
                if door_x and abs(y - YC) <= DOOR_W // 2 and z == ZTOP - DOOR_HEAD + 1:
                    frame = True
                cells[(x, y, z)] = OAK if frame else COPPER
            else:
                side = any(not (0 <= y + d < I.shape[0]) or (not I[y + d, z] and occ[x, y + d, z]) for d in (-1, 1))
                if side and abs(y - YC) > 6:                                   # 只包船殼那一側；中線支柱留原木（v2 連支柱也包 ⇒ 走道在支柱那幾格只剩 1 格）
                    cells[(x, y, z)] = COPPER
    return cells, interior, log


def free_cells(interior, cells):
    free = set()
    for x, I in interior.items():
        for y, z in zip(*np.nonzero(I)):
            y, z = int(y), int(z)
            if F <= z <= ZTOP and (x, y, z) not in cells:
                free.add((x, y, z))
    return free


def place_barrels(free):
    """同憲法號：直立、每 4.6 格、中線 ±3 留走道；上層放在靠船殼的階梯木架上；排到 CAP 就停。"""
    R = BARREL['d_bilge'] * BARREL['mpv'] / 0.1 / 2
    H = BARREL['h'] * BARREL['mpv'] / 0.1
    pitch = 4.6
    out, rack = [], {}
    x_lo, x_hi = X0 + 2, X1 - 1

    def foot(cx, cy):
        return [(x, y) for x in range(int(math.floor(cx - R)), int(math.ceil(cx + R)))
                for y in range(int(math.floor(cy - R)), int(math.ceil(cy + R)))]

    def body_free(cx, cy, z0):
        return all((x, y, z) in free and (x, y, z) not in rack
                   for x, y in foot(cx, cy) if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= (R + 0.3) ** 2
                   for z in range(int(math.floor(z0)), int(math.ceil(z0 + H))))

    def under_barrel(x, y, z, t_now):
        return any(b['tier'] < t_now and b['at'][2] <= z < b['at'][2] + H and
                   (x + 0.5 - b['at'][0]) ** 2 + (y + 0.5 - b['at'][1]) ** 2 <= R ** 2 for b in out)

    capacity = []
    for t in range(0, 4):
        n_t = 0
        cx = x_lo + R
        while cx + R <= x_hi:
            z0 = F + t * TIER
            for sgn in (1, -1):
                cy = YC + 0.5 + sgn * (3 + 0.5 + R)
                while abs(cy - YC) < 80:
                    shelf = [(x, y, int(z0) - 1) for x, y in foot(cx, cy)] if t else []
                    if body_free(cx, cy, z0) and all(p in free and p not in rack and not under_barrel(*p, t) for p in shelf):
                        n_t += 1
                        if len(out) < CAP:
                            out.append(dict(at=[round(cx, 3), round(cy, 3), round(z0, 3)], tier=t))
                            for p in shelf:
                                rack[p] = OAK
                            if t:
                                fx = [x for x, _ in foot(cx, cy)]
                                py = min(y for _, y in foot(cx, cy)) if sgn > 0 else max(y for _, y in foot(cx, cy))
                                for px in (min(fx), max(fx)):
                                    z = int(z0) - 2
                                    while z >= F and (px, py, z) in free and (px, py, z) not in rack:
                                        rack[(px, py, z)] = DARK
                                        z -= 1
                    elif not t:
                        break
                    cy += sgn * pitch
            cx += pitch
        capacity.append(n_t)
        if not n_t and t:
            break
    return out, rack, capacity


def seal(occ, cells):
    x0, x1 = X0 - 2, X1 + 2
    sub = occ[x0:x1 + 1].copy()
    new = np.zeros_like(sub)
    for (x, y, z) in cells:
        new[x - x0, y, z] = True
    solid = sub | new
    lab, n = ndimage.label(~solid)
    edge = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(),
                                         lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])))
    filled = []
    for L in range(1, n + 1):
        if L in edge:
            continue
        xs, ys, zs = np.nonzero(lab == L)
        assert len(xs) <= 50, ('大空腔', len(xs), int(xs.min()) + x0, int(ys.min()), int(zs.min()))
        for x, y, z in zip(xs, ys, zs):
            cells[(int(x) + x0, int(y), int(z))] = OAK
            new[x, y, z] = True
        filled.append([int(xs.min()) + x0, int(ys.min()), int(zs.min()), int(len(xs))])
    solid = sub | new
    lab, n = ndimage.label(solid)
    anchored = set(np.unique(lab[sub]))
    floating = [L for L in np.unique(lab[new]) if L not in anchored]
    assert not floating, ('浮空', [(np.argwhere(lab == L).min(axis=0) + [x0, 0, 0]).tolist() for L in floating][:5])
    return filled


def main(design, listfile):
    a = load(listfile)
    occ = np.zeros((int(a[:, 0].max()) + 1, 320, 64), bool)
    sel = a[:, 2] < 64
    occ[a[sel, 0], a[sel, 1], a[sel, 2]] = True
    cells, interior, log = build(occ)
    free = free_cells(interior, cells)
    barrels, rack, capacity = place_barrels(free)
    assert not set(rack) & set(cells)
    cells.update(rack)
    free -= set(rack)
    assert not any(occ[x, y, z] for (x, y, z) in cells), '落在實心上'
    sealed = seal(occ, cells)
    xs, ys, zs = zip(*cells)
    lo, hi = (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
    size = [hi[i] - lo[i] + 1 for i in range(3)]
    out = os.path.join(design, 'masks', 'magazine')
    os.makedirs(out, exist_ok=True)
    title = '夜燈號 彈藥庫（Tim 2026-10-15；%d 桶 ＝ %d 磅）' % (len(barrels), len(barrels) * 100)
    with open(os.path.join(out, 'magazine.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# %s：%d 格，子作品座標（原點 ＝ 組裝件 %s）\n' % (title, len(cells), lo))
        for (x, y, z), c in sorted(cells.items()):
            f.write('%d,%d,%d,%d\n' % (x - lo[0], y - lo[1], z - lo[2], c))
    cen = np.array(sorted(free)).mean(axis=0)
    blast = min(free, key=lambda p: sum((p[i] - cen[i]) ** 2 for i in range(3)))
    door = (X0 if DOOR == 'aft' else X1, YC, F)
    place = dict(title=title, x=[X0, X1], floor=F, ceil=CEIL, at=list(lo), size=size, cells=len(cells),
                 anchors={'blast': [blast[i] - lo[i] for i in range(3)], 'door': [door[i] - lo[i] for i in range(3)]},
                 barrel_work='basecamp-frigate-constitution-01m-powder-barrel', barrel_scale=0.2, barrel_pivot=[11, 11, 0],
                 barrels=[dict(name='桶-A%03d' % (i + 1), at=[round(b['at'][0] - lo[0], 3), round(b['at'][1] - lo[1], 3), round(b['at'][2] - lo[2], 3)],
                               tier=b['tier']) for i, b in enumerate(barrels)])
    colors = {}
    for c in cells.values():
        colors[c] = colors.get(c, 0) + 1
    verify = dict(cells=len(cells), colors=colors, air_inside=len(free), blast_world=list(blast), door_world=list(door),
                  barrels=len(barrels), capacity_per_tier=capacity, tiers=[sum(1 for b in barrels if b['tier'] == t) for t in range(4)],
                  rack=len(rack), sealed=sealed, box_world=[list(lo), list(hi)], pillars=[r['x'] for r in log if r.get('pillar')], per_x=log)
    json.dump(place, open(os.path.join(design, 'magazine_placement.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(verify, open(os.path.join(design, 'verify_magazine.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('cells', len(cells), 'colors', colors, 'air', len(free), 'barrels', len(barrels), 'tiers', verify['tiers'],
          'capacity', capacity, 'rack', len(rack), 'sealed', sealed, 'box', verify['box_world'], 'blast', list(blast),
          'pillar x', verify['pillars'])


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(sys.argv[1], sys.argv[2])
