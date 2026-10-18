# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/draft_magazines.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 階段九（TASK-0614）彈藥庫 —— 抄自三叉戟號 gura-tridente-01m/design/draft_magazines.py（gura；它改自餘燼號 draft_magazine_mid.py，basecamp）。
#   改：共用讀本船的 mio.py、框 1200；船名；其他照原檔（每間的地板、天花板、x 範圍、桶數在 plan.json magazines）。
# 原檔說明：
#   三叉戟號 階段九（TASK-0562）彈藥庫：前、後兩間，在 orlop 底下的貨艙，自己鋪地板與天花板；火藥桶引用憲法號 -powder-barrel
#   改自餘燼號 design/draft_magazine_mid.py（basecamp，階段二十一；它又改自憲法號 draft_magazines.py）。差別：
#   ① 一支產生兩間（plan.json magazines.rooms）；中線 y 200；② 本船貨艙沒有中線支柱、也沒有 orlop 以下的甲板 ⇒ 每個 x 只取中線那一塊空氣；
#   ③ 桶數照砲數換算：憲法號 54 門 138 桶 ⇒ 140 門 ≈ 358 桶，兩間各一半（plan 的 cap）。
#   輸入：現況 ＝ 組裝件 links=all（藏 彈藥庫-* 那幾條關聯 ⇒ 套用之後重跑讀到的還是同一份）
#   輸出：masks/magazines/<鍵>.vox.txt（子作品座標，原點 ＝ 外框最小角）、magazines_placement.json、verify_magazines.json
#   用法：python -I -X utf8 draft_magazines.py <design>
import sys, os, json, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import mio as DB

YC = 200
NZ = 80


def room(occ, R):
    """每個 x：(y,z) 橫切面、z F−1..CEIL 之間，跟中線那一格（F＋1 高）連通的空氣（4 連通）。"""
    F, CEIL = R['floor'], R['ceil']
    interior, log = {}, []
    for x in range(R['x'][0], R['x'][1] + 1):
        band = np.zeros_like(occ[x])
        band[:, F - 1:CEIL + 1] = ~occ[x][:, F - 1:CEIL + 1]
        if not band[YC, F + 1]:
            log.append({'x': x, 'skip': 'centerline solid at floor+1'})
            continue
        lab, _ = ndimage.label(band)
        I = lab == lab[YC, F + 1]
        interior[x] = I
        ys, _ = np.nonzero(I)
        log.append({'x': x, 'cells': int(I.sum()), 'y': [int(ys.min()), int(ys.max())]})
    return interior, log


def build(occ, R, C):
    F, CEIL, ZTOP = R['floor'], R['ceil'], R['ceil'] - 1
    X0, X1 = R['x']
    DW, DH = R['door_w'], R['door_head']
    interior, log = room(occ, R)
    cells = {}
    for x in sorted(interior):
        I = interior[x]
        wall = x in (X0, X1)
        door_x = (R['door'] == 'aft' and x == X0) or (R['door'] == 'fore' and x == X1)
        for y, z in zip(*np.nonzero(I)):
            y, z = int(y), int(z)
            if z == F - 1:
                cells[(x, y, z)] = C['oak'] if (y - YC) % 6 == 0 else C['pine']            # 地板：松木、每 6 格橡木壓條
            elif z == CEIL:
                cells[(x, y, z)] = C['oak'] if (x - X0) % 8 == 0 or wall else C['pine']    # 天花板：松木、每 8 格一道橡木樑
            elif wall:
                if door_x and abs(y - YC) <= DW // 2 and z <= ZTOP - DH:
                    continue
                frame = (y - YC) % 8 == 0 or z == F or z == ZTOP
                if door_x and abs(y - YC) == DW // 2 + 1 and z <= ZTOP - DH + 1:
                    frame = True
                if door_x and abs(y - YC) <= DW // 2 and z == ZTOP - DH + 1:
                    frame = True
                cells[(x, y, z)] = C['oak'] if frame else C['copper']
            else:
                side = any(not (0 <= y + d < I.shape[0]) or (not I[y + d, z] and occ[x, y + d, z]) for d in (-1, 1))
                if side:
                    cells[(x, y, z)] = C['copper']                                          # 船殼那一側包銅皮
    return cells, interior, log


def free_cells(interior, cells, R):
    free = set()
    for x, I in interior.items():
        for y, z in zip(*np.nonzero(I)):
            y, z = int(y), int(z)
            if R['floor'] <= z <= R['ceil'] - 1 and (x, y, z) not in cells:
                free.add((x, y, z))
    return free


def place_barrels(free, R, B, C):
    """同憲法號／餘燼號：直立、每 4.6 格、中線 ±3 留走道；上層放在靠船殼的階梯木架上；排到 cap 就停。"""
    F, X0, X1 = R['floor'], R['x'][0], R['x'][1]
    Rr = B['d_bilge'] * B['mpv'] / 0.1 / 2
    H = B['h'] * B['mpv'] / 0.1
    pitch, TIER = B['pitch'], B['tier']
    out, rack = [], {}
    x_lo, x_hi = X0 + 2, X1 - 1

    def foot(cx, cy):
        return [(x, y) for x in range(int(math.floor(cx - Rr)), int(math.ceil(cx + Rr)))
                for y in range(int(math.floor(cy - Rr)), int(math.ceil(cy + Rr)))]

    def body_free(cx, cy, z0):
        return all((x, y, z) in free and (x, y, z) not in rack
                   for x, y in foot(cx, cy) if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= (Rr + 0.3) ** 2
                   for z in range(int(math.floor(z0)), int(math.ceil(z0 + H))))

    def under_barrel(x, y, z, t_now):
        return any(b['tier'] < t_now and b['at'][2] <= z < b['at'][2] + H and
                   (x + 0.5 - b['at'][0]) ** 2 + (y + 0.5 - b['at'][1]) ** 2 <= Rr ** 2 for b in out)

    capacity = []
    for t in range(0, 4):
        n_t = 0
        cx = x_lo + Rr
        while cx + Rr <= x_hi:
            z0 = F + t * TIER
            for sgn in (1, -1):
                cy = YC + 0.5 + sgn * (3 + 0.5 + Rr)
                while abs(cy - YC) < 90:
                    shelf = [(x, y, int(z0) - 1) for x, y in foot(cx, cy)] if t else []
                    if body_free(cx, cy, z0) and all(p in free and p not in rack and not under_barrel(*p, t) for p in shelf):
                        n_t += 1
                        if len(out) < R['cap']:
                            out.append(dict(at=[round(cx, 3), round(cy, 3), round(z0, 3)], tier=t))
                            for p in shelf:
                                rack[p] = C['oak']
                            if t:
                                fx = [x for x, _ in foot(cx, cy)]
                                py = min(y for _, y in foot(cx, cy)) if sgn > 0 else max(y for _, y in foot(cx, cy))
                                for px in (min(fx), max(fx)):
                                    z = int(z0) - 2
                                    while z >= F and (px, py, z) in free and (px, py, z) not in rack:
                                        rack[(px, py, z)] = C['dark']
                                        z -= 1
                    elif not t:
                        break
                    cy += sgn * pitch
            cx += pitch
        capacity.append(n_t)
        if not n_t and t:
            break
    return out, rack, capacity


def seal(occ, cells, R, C):
    """≤ 50 格的封閉空腔填實（橡木）；新格每一塊都要連到原本的實心。"""
    x0, x1 = R['x'][0] - 2, R['x'][1] + 2
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
            cells[(int(x) + x0, int(y), int(z))] = C['oak']
            new[x, y, z] = True
        filled.append([int(xs.min()) + x0, int(ys.min()), int(zs.min()), int(len(xs))])
    solid = sub | new
    lab, n = ndimage.label(solid)
    anchored = set(np.unique(lab[sub]))
    floating = [int(L) for L in np.unique(lab[new]) if L not in anchored]
    assert not floating, ('浮空', floating[:5])
    return filled


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    plan = HL.load_plan(design)
    MG = plan['magazines']
    links = [l for l in MG['base_links'].split(',')]
    A = DB.export_list(DB.ASM, ','.join(links))
    A = A[A[:, 2] < NZ]
    occ = np.zeros((1300, 400, NZ), bool)   # 蘇士奎哈納號改：框 1300
    occ[A[:, 0], A[:, 1], A[:, 2]] = True
    place, verify = {'barrel_work': MG['barrel']['work'], 'barrel_scale': MG['barrel']['scale'], 'barrel_pivot': MG['barrel']['pivot'], 'rooms': {}}, \
        {'base': '組裝件 %s：%d 格（z < %d）' % (MG['base_links'], len(A), NZ), 'rooms': {}}
    os.makedirs(os.path.join(design, 'masks', 'magazines'), exist_ok=True)
    for key, R in MG['rooms'].items():
        cells, interior, log = build(occ, R, MG['colors'])
        free = free_cells(interior, cells, R)
        barrels, rack, capacity = place_barrels(free, R, MG['barrel'], MG['colors'])
        assert not set(rack) & set(cells)
        cells.update(rack)
        free -= set(rack)
        assert not any(occ[x, y, z] for (x, y, z) in cells), '落在實心上'
        sealed = seal(occ, cells, R, MG['colors'])
        xs, ys, zs = zip(*cells)
        lo, hi = (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
        size = [hi[i] - lo[i] + 1 for i in range(3)]
        title = '蘇士奎哈納號 %s（%d 桶 ＝ %d 磅）' % (R['title'], len(barrels), len(barrels) * 100)
        with open(os.path.join(design, 'masks', 'magazines', key + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# %s：%d 格，子作品座標（原點 ＝ 組裝件 %s）\n' % (title, len(cells), list(lo)))
            for (x, y, z), c in sorted(cells.items()):
                f.write('%d,%d,%d,%d\n' % (x - lo[0], y - lo[1], z - lo[2], c))
        cen = np.array(sorted(free)).mean(axis=0)
        blast = min(sorted(free), key=lambda p: sum((p[i] - cen[i]) ** 2 for i in range(3)))
        door = (R['x'][0] if R['door'] == 'aft' else R['x'][1], YC, R['floor'])
        colors = {}
        for c in cells.values():
            colors[str(c)] = colors.get(str(c), 0) + 1
        place['rooms'][key] = dict(title=title, work=R['work'], link=R['link'], pos=R['pos'], at=list(lo), size=size, cells=len(cells),
                                   anchors={'blast': [blast[i] - lo[i] for i in range(3)], 'door': [door[i] - lo[i] for i in range(3)]},
                                   barrels=[dict(name='桶-%s%03d' % (R['pos'][0].upper(), i + 1),
                                                 at=[round(b['at'][0] - lo[0], 3), round(b['at'][1] - lo[1], 3), round(b['at'][2] - lo[2], 3)],
                                                 tier=b['tier']) for i, b in enumerate(barrels)])
        verify['rooms'][key] = dict(cells=len(cells), colors=dict(sorted(colors.items())), air_inside=len(free), blast_world=list(blast), door_world=list(door),
                                    barrels=len(barrels), capacity_per_tier=capacity, tiers=[sum(1 for b in barrels if b['tier'] == t) for t in range(4)],
                                    rack=len(rack), sealed=sealed, box_world=[list(lo), list(hi)], skipped=[r for r in log if 'skip' in r])
        print(key, 'cells', len(cells), 'air', len(free), 'barrels', len(barrels), 'tiers', verify['rooms'][key]['tiers'], 'capacity', capacity,
              'rack', len(rack), 'sealed', len(sealed), 'box', verify['rooms'][key]['box_world'], 'blast', list(blast), 'door', list(door))
    for nm, obj in (('magazines_placement.json', place), ('verify_magazines.json', verify)):
        with open(os.path.join(design, nm), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write('\n')


if __name__ == '__main__':
    main()
