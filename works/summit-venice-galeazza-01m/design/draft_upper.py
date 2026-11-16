"""威尼斯 galeazza（TASK-1302）船殼 02：舷外槳架外緣與舷牆（拱形槳門）、圓形艏樓（兩層砲門）、艉樓（窗、拱頂艙）、衝角。

只讀 plan.json 與船殼 01 的清單（masks/hull/hull_01.vox.txt），輸出 masks/upper/upper_01.vox.txt（只放船殼 01 沒有的格）。
甲板板、划凳、corsia、艏樓頂板、艉樓平台板是步驟 5 的甲板子作品，⛔ 不在這裡。
座標同 lines.py：X 船長（船頭 +X）、Y 寬（中線 160）、Z 高（龍骨底 0）；格 k 佔 [k, k+1)、格心 k+0.5。
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy import ndimage

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from lines import Lines, load_plan

WOOD, DARK, GOLD, RED, IRON, BOTTOM = 141, 68, 212, 160, 73, 32


def lv(plan, k):
    v = plan['layout'][k]['v']
    return v


def main():
    plan = load_plan(D)
    L = Lines(plan)
    YC = plan['space']['yc']
    NX, NY, NZ = plan['space']['hull']
    hull = np.loadtxt(D / 'masks/hull/hull_01.vox.txt', delimiter=',', dtype=np.int32)
    occ = np.zeros((NX, NY, NZ), np.uint8)
    occ[hull[:, 0], hull[:, 1], hull[:, 2]] = hull[:, 3]

    deck_top = lv(plan, 'deck_top_z')
    post_out = lv(plan, 'postizza_out')
    bw_top = lv(plan, 'bulwark_top_z')
    bw_th = lv(plan, 'bulwark_thick')
    ox0, pitch = lv(plan, 'oar_x0'), lv(plan, 'oar_pitch')
    port = lv(plan, 'oar_port')
    bc = lv(plan, 'bow_castle')
    sc = lv(plan, 'stern_castle')
    sp = lv(plan, 'spur')
    B2 = int(plan['lines']['half_beam']['v'])
    OUT = B2 + post_out                     # 舷牆外緣 |dy|（58）
    oars_x = [int(np.floor(ox0 + i * pitch)) for i in range(plan['oars']['per_side'])]

    X = np.arange(NX)[:, None, None]
    Y = np.arange(NY)[None, :, None]
    Z = np.arange(NZ)[None, None, :]
    dy = np.abs(Y - YC)
    new = np.zeros((NX, NY, NZ), np.uint8)
    groups = {}

    def put(mask, color, name):
        m = mask & (occ == 0) & (new == 0)
        new[m] = color
        groups[name] = groups.get(name, 0) + int(m.sum())

    # ── 1. 舷外槳架外緣（posticcio 縱樑）＋舷牆（拱形槳門）：x 150..466 ──
    xa, xb = sc['x_front'], bc['x_back']
    waist = (X >= xa) & (X <= xb)
    put(waist & (dy >= OUT - 3) & (dy <= OUT) & (Z >= deck_top - 2) & (Z <= deck_top), DARK, 'posticcio')
    wall = waist & (dy > OUT - bw_th) & (dy <= OUT) & (Z > deck_top) & (Z <= bw_top)
    hole = np.zeros_like(wall)
    for xo in oars_x:
        hw = port['half_w']
        h = (np.abs(X - xo) <= hw) & (Z >= port['z0']) & (Z <= port['z1'] - 1)
        h |= (np.abs(X - xo) <= hw - 1) & (Z == port['z1'])           # 拱頂：最上一層窄一格
        hole |= h
    put(wall & ~hole, DARK, 'bulwark')
    # 舷牆頂的鍍金壓條（外層一格、最上兩層）＋槳門一圈的金框不做（顏色少）
    new[waist & (dy == OUT) & (Z >= bw_top - 1) & (Z <= bw_top) & (new == DARK)] = GOLD
    # 槳架托架：每支槳之間一根，從船殼斜撐到縱樑底（z 26..29）
    for i in range(len(oars_x) + 1):
        xm = int(round(ox0 + (i - 0.5) * pitch))
        if not (xa <= xm <= xb):
            continue
        for d in range(B2 - 2, OUT + 1):
            zt = deck_top - 3 - int(round((OUT - d) * 4 / max(1, OUT - B2 + 2)))
            put((X == xm) & (dy == d) & (Z >= zt) & (Z <= deck_top - 3), DARK, 'brackets')
    # 兩頭封板：舷牆從縱樑收回船殼（x 150、x 466 各兩格厚）
    for xe in (xa, xa + 1, xb - 1, xb):
        hbz = np.array([L.hb(xe + 0.5, min(z, L.z_side) + 0.5) for z in range(NZ)])
        inner = np.maximum(hbz - 1, 0)[None, None, :]
        put((X == xe) & (dy >= inner) & (dy <= OUT) & (Z >= deck_top - 2) & (Z <= bw_top), DARK, 'waist_ends')

    # ── 2. 圓形艏樓：x ≥ 466 的直段＋以 (cx, YC) 為心、半徑 r 的半圓；牆 3 格；z 29..62 ──
    cx, r, th = bc['cx'], bc['r'], bc['wall']
    dx = X + 0.5 - (cx + 0.5)
    rr = np.where(X >= cx, np.sqrt(dx * dx + (Y - YC) ** 2), (Y - YC).__abs__() + 0.0 * X)
    ring = (X >= bc['x_back']) & (rr <= r + 0.5) & (rr > r + 0.5 - th)
    inside_disk = (X >= bc['x_back']) & (rr <= r + 0.5)
    z0c, ztop = 29, bc['top_z']
    ang = np.degrees(np.arctan2(Y - YC, np.maximum(dx, 1e-6)))       # 0° ＝ 正前方（x ≥ cx 那半圓）
    ports = np.zeros((NX, NY, NZ), bool)
    for a in (-36, -12, 12, 36):                                        # 下層 4 門：2 × 50 磅 colubrina（中）＋2 × 20 磅 cannone（斜）
        tang = np.abs(np.radians(ang - a)) * r
        ports |= (X >= cx) & (tang <= 3.5) & (Z >= 37) & (Z <= 43)
    for a in (-100, -72, -45, -18, 18, 45, 72, 100):                    # 頂層 8 個砲眼：colubrina 14、falcone 6、petriera 14
        aa = np.clip(np.abs(a), 0, 90) * np.sign(a)
        tang = np.abs(np.radians(ang - aa)) * r
        if abs(a) <= 90:
            ports |= (X >= cx) & (tang <= 3.0) & (Z >= 56) & (Z <= ztop)
        else:                                                           # ±100° ⇒ 直段側牆上、x ＝ cx − 10
            ports |= (np.abs(X - (cx - 10)) <= 3) & (Z >= 56) & (Z <= ztop)
    for xs in (486, 504):                                               # 下層兩舷各 2 門：6 門 30 磅 cannone 的其中 4 門（另 2 門在艉樓艙側窗）
        ports |= (np.abs(X - xs) <= 3) & (X < cx) & (Z >= 37) & (Z <= 43)
    put(ring & ~ports & (Z >= z0c) & (Z <= ztop), DARK, 'castle_ring')
    new[ring & (rr > r - 0.5) & ((Z == 50) | (Z == 51) | (Z == ztop)) & (new == DARK)] = GOLD
    # 下層後牆（x 466..468、z 32..50）＋門（corsia 寬）
    back = (X >= bc['x_back']) & (X <= bc['x_back'] + 2) & (dy < r - th + 1) & (Z > deck_top) & (Z <= bc['deck_z'] - 1)
    door = (dy <= 5) & (Z <= deck_top + 16)
    put(back & ~door, DARK, 'castle_back')
    # 托板 giogo：艏樓圓盤裡、船殼外的地方，z 29–30 兩層（甲板板 z 31 在步驟 5）
    put(inside_disk & (Z >= z0c) & (Z <= deck_top - 1), DARK, 'giogo')

    # ── 3. 艉樓：x 52..150；側牆沿舷頂往上、艉封板、窗；平台板 z 51 在步驟 5 ──
    sx0, sx1 = int(L.x_sh), sc['x_front']
    hbx = np.array([max(L.hb(x + 0.5, L.z_side + 0.5), -1) for x in range(NX)])
    shx = np.array([L.sheer(x + 0.5) for x in range(NX)])
    sx0 = int(next(x for x in range(sx0, NX) if hbx[x] >= 2))         # 艉封板落在第一個有寬度的 x（x_sh 那格半寬 < 0）
    HB = hbx[:, None, None]
    SH = shx[:, None, None]
    stern = (X >= sx0) & (X <= sx1) & (HB >= 2)
    swall = stern & (dy <= HB) & (dy > HB - 2) & (Z > SH) & (Z <= sc['rail_z'])
    win = np.zeros_like(swall)
    for xw in range(sx0 + 14, sx1 - 8, 15):                             # 側窗：艉樓下的艙（dragante）
        win |= (np.abs(X - xw) <= 2) & (Z >= 40) & (Z <= 46)
    put(swall & ~win, DARK, 'stern_walls')
    tran = (X >= sx0) & (X <= sx0 + 1) & (dy <= HB) & (Z > SH) & (Z <= sc['rail_z'])
    twin = ((np.abs(dy - 10) <= 3) | (np.abs(dy - 24) <= 3)) & (Z >= 40) & (Z <= 46)
    put(tran & ~twin, DARK, 'transom')
    # 艉樓前牆（x 150..151，平台下的艙），門在 corsia
    front = (X >= sx1) & (X <= sx1 + 1) & (dy < HB - 1) & (Z > deck_top) & (Z <= sc['deck_z'] - 1)
    put(front & ~((dy <= 5) & (Z <= deck_top + 16)), DARK, 'stern_front')
    new[stern & (dy == HB) & ((Z == 50) | (Z == 51) | (Z == sc['rail_z'])) & (new == DARK)] = GOLD
    new[tran & (X == sx0) & ((Z == 50) | (Z == 51) | (Z == sc['rail_z'])) & (new == DARK)] = GOLD
    # 拱頂艙（tabernacolo）：半圓筒殼，軸沿 x、在平台面上；兩側 z < 62 開敞、留柱
    cab = sc['cabin']
    R = cab['top_z'] - sc['deck_z']
    rz = np.sqrt((Y - YC) ** 2 + (Z - sc['deck_z']) ** 2 + 0.0 * X)
    shell = (X >= cab['x0']) & (X <= cab['x1']) & (rz <= R + 0.5) & (rz > R - 1.5) & (Z > sc['deck_z'])
    posts = (((X - cab['x0']) % 12) <= 1) | (X >= cab['x1'] - 1)
    openside = (Z < sc['deck_z'] + 11) & ~posts
    roof = shell & ~openside
    put(roof, RED, 'cabin_roof')
    rib = roof & ((((X - cab['x0']) % 12) <= 1) | (X >= cab['x1'] - 1)) & (new == RED)
    new[rib] = GOLD
    # 艙的後壁（船尾那端封起來，畫金框）
    put((X >= cab['x0']) & (X <= cab['x0'] + 1) & (rz <= R + 0.5) & (Z > sc['deck_z']), DARK, 'cabin_back')

    # ── 4. 衝角 sperone：艏柱 556 → 632，略往上翹；最後 12 格是鐵 ──
    x0s, x1s = int(L.x_st), sp['x_tip']
    for x in range(x0s, x1s + 1):
        t = (x - x0s) / (x1s - x0s)
        zc = sp['z_root'] + (sp['z_tip'] - sp['z_root']) * t
        hw = 6 * (1 - t) + 0.8
        hh = 3.5 * (1 - t) + 0.8
        m = (X == x) & (((Y - YC) / hw) ** 2 + ((Z + 0.5 - zc - 0.5) / hh) ** 2 <= 1.0)
        put(m, IRON if x > x1s - 12 else DARK, 'spur')

    # 托衝角的膝材（Tim 2026-11-16「撞角是否可以連接龍骨」）：艏柱前緣到衝角下緣之間一片三角形木，
    #   下緣從艏柱腳（龍骨前端附近 z 6）斜上到 x 596 的衝角底；寬 3 格（y ±1）⇒ 衝角經艏柱接到龍骨，衝角本身照史料留在水線上。
    for x in range(x0s - 40, x0s + 41):
        zb = 6 + (x - (x0s - 40)) * (sp['z_root'] - 2 - 6) / 80.0
        ztop_k = z0c - 1 if x <= cx + r else sp['z_root'] + 1             # 艏樓底下一路頂到托板，不留縫
        put((X == x) & (dy <= 1) & (Z >= int(round(zb))) & (Z <= ztop_k), DARK, 'spur_knee')
    new[(new > 0) & (Z <= plan['waterline']['z']) & (X >= x0s - 40) & (occ == 0)] = BOTTOM   # 水線下塗船底色
    cells = np.argwhere(new > 0)
    union = (occ > 0) | (new > 0)
    lab, ncomp = ndimage.label(union)
    voids = ndimage.binary_fill_holes(np.pad(union, 1))[1:-1, 1:-1, 1:-1] & ~union
    stats = {
        'cells': len(cells),
        'groups': groups,
        'union_components': int(ncomp),
        'union_enclosed_air': int(voids.sum()),
        'mirror_differences': int(np.count_nonzero(new != new[:, ::-1, :])),   # NY = 2·YC + 1 ⇒ y ↔ 320 − y
        'bbox_min': [int(v) for v in cells.min(0)],
        'bbox_max': [int(v) for v in cells.max(0)],
        'oars_x': oars_x,
    }
    body = ''.join(f'{x},{y},{z},{new[x, y, z]}\n' for x, y, z in cells).encode('ascii')
    out = D / 'masks/upper/upper_01.vox.txt'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(body)
    stats['sha256'] = hashlib.sha256(body).hexdigest()
    (D / 'verify_upper.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == '__main__':
    main()
