# 新圖紙 24（彈藥庫）：組裝件現況（export format=list）＋ 本檔的配置 ⇒
#   masks/magazines/{aft,fore}.vox.txt（子作品自己的座標，原點 ＝ 外框最小角）、masks/magazines/barrel.vox.txt（0.02 m 火藥桶）、
#   magazines_placement.json（外框、關聯 at、固定點、桶的位置）、verify_magazines.json
# 用法：python -I draft_magazines.py <design 資料夾> <組裝件 list 匯出檔（藏掉 彈藥庫-前／後 兩條關聯）>
# 史實（02 號圖 1849 Pook，讀數見 notes 階段三十二）：After Magazine 23'4"（x 199.9–271.1；淨高 4'8" 船尾段、5'3"／5'6" 往前，地板在 x≈233 往下一階）、
#   Fore Magazine 17'2"（x 521.3–573.7；淨高 4'7"）。1812 航海日誌：main magazine（24 磅藥包）＋ forward magazine（carronade）。
# 做法：每個 x 的橫切面（y,z）裡，從中線往外連到的艙內空氣 ＝ 房間；地板一格、地板底下填實（不留封閉空腔）、兩道橫艙壁、
#   貼船殼那一格內襯銅皮；門洞開在通道那一側（後彈藥庫朝船尾、前彈藥庫朝船頭）。淨高從 orlop 橫樑頂（z 41 的下緣）往下量。
import sys, os, json, math
import numpy as np
from scipy import ndimage

COPPER, OAK, DARK, PINE = 168, 136, 104, 177
BEAM_TOP = 41               # orlop 甲板板那一格；淨高從它的下緣量（橫樑頂 ＝ 板底）
ZTOP = 40                   # 房間最高那一格（甲板板底下）
LINE_TOP = 37               # 側壁銅皮鋪到 orlop 橫樑底下（v2 鋪到 40 ⇒ 縱樑 carling 兩側也包了銅、房間上空一條條橫著）
YC = 160                    # 中線那一格（船寬 0..320，鏡面 160↔160）
CELL_FT = 0.3048 / 0.1      # 一英尺幾格

MAGS = {
    'aft': dict(title='憲法號 後彈藥庫（main magazine，1849 圖 23\'4")', x0=200, x1=271, door='aft',
                floors=[(200, 232, BEAM_TOP - round(4 + 8 / 12, 3) * CELL_FT), (233, 271, BEAM_TOP - (5 + 3 / 12) * CELL_FT)]),
    'fore': dict(title='憲法號 前彈藥庫（forward magazine，1849 圖 17\'2")', x0=521, x1=573, door='fore',
                 floors=[(521, 573, BEAM_TOP - (4 + 7 / 12) * CELL_FT)]),
}
DOOR_W, DOOR_HEAD = 5, 3    # 門洞寬 5（y 158–162）、頂上留 3 格
# 火藥桶（1813 英制 whole barrel：bilge 17.36"、高 21.62"）⇒ 0.02 m 一格：bilge 直徑 22、高 27；頭 19
BARREL = dict(mpv=0.02, d_bilge=22, d_head=19, h=27)


def load(path):
    a = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    return a


def floor_of(m, x):
    for xa, xb, f in m['floors']:
        if xa <= x <= xb:
            return int(round(f))
    raise KeyError(x)


def room(occ, m):
    """每個 x：(y,z) 橫切面裡從中線連到的空氣（z 從地板那一格到 ZTOP）。回傳 cells dict。"""
    cells = {}            # (x,y,z) → color
    interior = {}         # x → bool[y, z]（房間內的空氣，含地板那一層）
    log = []
    for x in range(m['x0'], m['x1'] + 1):
        F = floor_of(m, x)
        air = ~occ[x]                                   # [y, z]
        band = np.zeros_like(air)
        band[:, F - 1:ZTOP + 1] = air[:, F - 1:ZTOP + 1]
        lab, _ = ndimage.label(band)                    # 4 連通
        seeds = [y for y in sorted(range(occ.shape[1]), key=lambda y: abs(y - YC)) if band[y, F + 1]]
        if not seeds:
            log.append({'x': x, 'skip': 'no air at floor+1'})
            continue
        I = lab == lab[seeds[0], F + 1]
        interior[x] = I
        ys, zs = np.nonzero(I)
        log.append({'x': x, 'F': F, 'cells': int(I.sum()), 'y': [int(ys.min()), int(ys.max())], 'z': [int(zs.min()), int(zs.max())]})
    return interior, log


def build(occ, m):
    interior, log = room(occ, m)
    cells = {}
    xs = sorted(interior)
    for x in xs:
        I = interior[x]
        F = floor_of(m, x)
        wall = x in (m['x0'], m['x1'])
        for y, z in zip(*np.nonzero(I)):
            y, z = int(y), int(z)
            if z == F - 1:
                cells[(x, y, z)] = OAK if (y - YC) % 6 == 0 else PINE        # 地板：松木板、每 6 格一道橡木壓條
            elif z == ZTOP and not occ[x, y, ZTOP + 1]:
                continue                                                      # 上面是空氣（桅孔、艙口）⇒ 最上一排不鋪，免得把洞口封成空腔（v1：後桅 x 206 封出 2 個）
            elif wall:
                door = (m['door'] == 'aft' and x == m['x0']) or (m['door'] == 'fore' and x == m['x1'])
                if door and abs(y - YC) <= DOOR_W // 2 and z <= ZTOP - DOOR_HEAD:
                    continue
                frame = (y - YC) % 8 == 0 or z == F or z == ZTOP
                if door and abs(y - YC) == DOOR_W // 2 + 1 and z <= ZTOP - DOOR_HEAD + 1:
                    frame = True
                if door and abs(y - YC) <= DOOR_W // 2 and z == ZTOP - DOOR_HEAD + 1:
                    frame = True
                cells[(x, y, z)] = OAK if frame else COPPER
            else:
                # 貼著實心（船殼內板、斜肋、orlop 橫樑以外）的那一格 ⇒ 銅皮；只看 y 方向的鄰居（側壁）
                side = any(not (0 <= y + d < I.shape[0]) or (not I[y + d, z] and occ[x, y + d, z]) for d in (-1, 1))
                if side and z <= LINE_TOP:
                    cells[(x, y, z)] = COPPER
        # 地板底下不填：那層空氣沿船長方向跟艙壁外的船艙相通（橫艙壁只從地板往上），不是封閉空腔 —— 接上組裝件後用 stats 的空腔讀數驗
    return cells, interior, log


def free_cells(interior, cells, m):
    """放桶用：房間內、地板以上、不是銅皮／艙壁的格。"""
    free = set()
    for x, I in interior.items():
        F = floor_of(m, x)
        for y, z in zip(*np.nonzero(I)):
            y, z = int(y), int(z)
            if z >= F and (x, y, z) not in cells:
                free.add((x, y, z))
    return free


TIER = 7                    # 層距：桶高 5.4 ＋ 架板 1 ＋ 空 0.6


def place_barrels(free, m):
    """直立；桶外框 4.4 × 4.4 × 5.4 格（0.1 m）、每 4.6 格一個；中線 ±3 留走道（門口直進去）。
    第 0 層站在地板上；第 t 層（t ≥ 1）站在 z ＝ F＋7t−1 的架板上（船底是 V 形，越上面越寬 ⇒ 階梯式的架子靠著船殼）。
    回傳 (桶, 架子的格)：架板 ＝ 桶底那一格的方框；靠走道那側一根立柱往下接到地板／下一層架板／下一層的桶頂。"""
    R = BARREL['d_bilge'] * BARREL['mpv'] / 0.1 / 2          # 2.2
    H = BARREL['h'] * BARREL['mpv'] / 0.1                     # 5.4
    pitch = 4.6
    out, rack = [], {}
    x_lo, x_hi = m['x0'] + 2, m['x1'] - 1                     # 兩道艙壁內面各留 1 格（v2 曾用「房間最小 x＋1」⇒ 艙壁頂排不鋪之後整排桶往後挪 1 格、貼牆）

    def foot(cx, cy):
        return [(x, y) for x in range(int(math.floor(cx - R)), int(math.ceil(cx + R)))
                for y in range(int(math.floor(cy - R)), int(math.ceil(cy + R)))]

    def body_free(cx, cy, z0):
        return all((x, y, z) in free and (x, y, z) not in rack
                   for x, y in foot(cx, cy) if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= (R + 0.3) ** 2
                   for z in range(int(math.floor(z0)), int(math.ceil(z0 + H))))

    def under_barrel(x, y, z):
        return any(b['tier'] < t_now and b['at'][2] <= z < b['at'][2] + H and
                   (x + 0.5 - b['at'][0]) ** 2 + (y + 0.5 - b['at'][1]) ** 2 <= R ** 2 for b in out)

    for t in range(0, 4):
        t_now = t
        cx = x_lo + R
        placed_any = False
        while cx + R <= x_hi:
            F = floor_of(m, int(cx))
            if floor_of(m, int(cx - R)) != F or floor_of(m, int(min(cx + R, m['x1'] - 1))) != F:
                cx += pitch / 2
                continue
            z0 = F + t * TIER
            for sgn in (1, -1):
                cy = YC + 0.5 + sgn * (3 + 0.5 + R)                 # 走道 y 157..163 留空
                while abs(cy - YC) < 80:
                    shelf = [(x, y, int(z0) - 1) for x, y in foot(cx, cy)] if t else []
                    if body_free(cx, cy, z0) and all(p in free and p not in rack and not under_barrel(*p) for p in shelf):
                        out.append(dict(at=[round(cx, 3), round(cy, 3), round(z0, 3)], tier=t))
                        placed_any = True
                        for p in shelf:
                            rack[p] = OAK
                        if t:                                         # 立柱：架板靠走道那一邊的兩個角往下接到地板／下一層架板
                            # 角在桶的圓外面 ⇒ 下面有下一層的桶也接得下去（v1 放中點，碰到桶就停 ⇒ 19 塊架板以格子來看浮空）
                            fx = [x for x, _ in foot(cx, cy)]
                            py = min(y for _, y in foot(cx, cy)) if sgn > 0 else max(y for _, y in foot(cx, cy))
                            for px in (min(fx), max(fx)):
                                z = int(z0) - 2
                                while z >= F and (px, py, z) in free and (px, py, z) not in rack:
                                    rack[(px, py, z)] = DARK
                                    z -= 1
                    elif not t:
                        break                                         # 地板那層：從走道往外排，碰到船殼就停
                    cy += sgn * pitch
            cx += pitch
        if not placed_any and t:
            break
    return out, rack


def barrel_cells():
    b = BARREL
    rb, rh, h = b['d_bilge'] / 2, b['d_head'] / 2, b['h']
    c = b['d_bilge'] / 2
    hoops = {1, 2, 7, 8, 18, 19, 24, 25}
    cells = []
    for z in range(h):
        t = (z + 0.5 - h / 2) / (h / 2)
        r = rh + (rb - rh) * (1 - t * t)
        top = z in (0, h - 1)
        for x in range(b['d_bilge']):
            for y in range(b['d_bilge']):
                d = math.hypot(x + 0.5 - c, y + 0.5 - c)
                if d > r:
                    continue
                if top:
                    col = DARK if d > r - 1.2 else OAK                     # 桶口：外圈 chime 深色、桶蓋橡木
                elif z in hoops and d > r - 1.5:
                    col = DARK                                             # 木箍（火藥桶不用鐵箍）
                else:
                    ang = math.atan2(y + 0.5 - c, x + 0.5 - c)
                    col = PINE if int((ang + math.pi) / (2 * math.pi) * 18) % 2 else OAK   # 18 片桶板
                cells.append((x, y, z, col))
    return cells


def seal(occ, cells, m):
    """局部掃一次（x0−2..x1+2、全寬、z 0..47）：① 封閉的空氣（碰不到掃描框邊）⇒ 填橡木（≤ 50 格，再大就停下來）；
    ② 新格子每一塊都要連到原本的實心（以格子來看不浮空）。"""
    x0, x1 = m['x0'] - 2, m['x1'] + 2
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
        assert len(xs) <= 50, ('大空腔', len(xs), xs.min() + x0, ys.min(), zs.min())
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
    SXX = 1024
    occ = np.zeros((SXX, 320, 48), bool)
    sel = a[:, 2] < 48
    occ[a[sel, 0], a[sel, 1], a[sel, 2]] = True
    out = os.path.join(design, 'masks', 'magazines')
    os.makedirs(out, exist_ok=True)
    place, verify = {'barrel': dict(BARREL, title='憲法號 火藥桶（whole barrel 100 lb，0.02 m）')}, {}
    for key, m in MAGS.items():
        cells, interior, log = build(occ, m)
        free = free_cells(interior, cells, m)
        barrels, rack = place_barrels(free, m)
        assert not set(rack) & set(cells)
        cells.update(rack)
        free -= set(rack)
        assert not any(occ[x, y, z] for (x, y, z) in cells), '落在實心上'
        sealed = seal(occ, cells, m)
        xs, ys, zs = zip(*cells)
        lo = (min(xs), min(ys), min(zs))
        hi = (max(xs), max(ys), max(zs))
        size = [hi[i] - lo[i] + 1 for i in range(3)]
        with open(os.path.join(out, key + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# %s：%d 格，子作品座標（原點 ＝ 組裝件 %s）\n' % (m['title'], len(cells), lo))
            for (x, y, z), c in sorted(cells.items()):
                f.write('%d,%d,%d,%d\n' % (x - lo[0], y - lo[1], z - lo[2], c))
        # 爆心：房間內空氣（地板以上）的重心，取最近的一格空氣
        fx = np.array(sorted(free))
        cen = fx.mean(axis=0)
        blast = min(free, key=lambda p: sum((p[i] - cen[i]) ** 2 for i in range(3)))
        dz = ZTOP - DOOR_HEAD
        door = (m['x0'] if m['door'] == 'aft' else m['x1'], YC, floor_of(m, m['x0'] if m['door'] == 'aft' else m['x1']))
        place[key] = dict(title=m['title'], x=[m['x0'], m['x1']], floors=m['floors'], at=list(lo), size=size,
                          cells=len(cells), anchors={'blast': [blast[i] - lo[i] for i in range(3)],
                                                     'door': [door[i] - lo[i] for i in range(3)]},
                          barrels=[dict(name='桶-%s%03d' % ('A' if key == 'aft' else 'F', i + 1),
                                        at=[round(b['at'][0] - lo[0], 3), round(b['at'][1] - lo[1], 3), round(b['at'][2] - lo[2], 3)],
                                        tier=b['tier']) for i, b in enumerate(barrels)])
        colors = {}
        for c in cells.values():
            colors[c] = colors.get(c, 0) + 1
        verify[key] = dict(cells=len(cells), colors=colors, air_inside=len(free), blast_world=list(blast),
                           barrels=len(barrels), tiers=[sum(1 for b in barrels if b['tier'] == t) for t in range(4)], rack=len(rack), sealed=sealed,
                           box_world=[list(lo), list(hi)], per_x=log)
    bc = barrel_cells()
    with open(os.path.join(out, 'barrel.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 火藥桶 0.02 m：%d 格\n' % len(bc))
        for c in bc:
            f.write('%d,%d,%d,%d\n' % c)
    place['barrel']['cells'] = len(bc)
    json.dump(place, open(os.path.join(design, 'magazines_placement.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(verify, open(os.path.join(design, 'verify_magazines.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for k in ('aft', 'fore'):
        v = verify[k]
        print(k, 'cells', v['cells'], 'colors', v['colors'], 'air', v['air_inside'], 'barrels', v['barrels'], v['tiers'], 'rack', v['rack'], 'sealed', v['sealed'],
              'box', v['box_world'], 'blast', v['blast_world'])
    print('barrel cells', len(bc))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
