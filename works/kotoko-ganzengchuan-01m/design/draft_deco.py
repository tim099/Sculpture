# 福建趕繒船 新圖紙 05（TASK-1314 步驟 6）：裝飾與窗玻璃 —— 船尾窗玻璃（material=glass）、高尾陽台欄杆、船首彩雕／高尾牌飾／兩舷護舷（deco=1）
#   出處：kaguya-shachuan-01m/design/draft_deco.py ＋ calli-cosecha-01m/design/draft_deco.py（依福建趕繒船高尾與龍目獅首改寫）
#   用法：python -I -X utf8 draft_deco.py <design 資料夾> [--probe=shift_bow=-3|shift_fender_in=-1]
import hashlib
import json
import os
import sys
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_lines as DL
from draft_lines import build as hull_build

sys.stdout.reconfigure(encoding='utf-8')


def load_vox_map(path):
    arr = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    return {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in arr}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def check_struct_stats(vox_set, yc):
    """回報 6 連通元件數、內部空腔數、對 y=yc 的對稱差。"""
    if not vox_set:
        return {'count': 0, 'components_6': 0, 'cavities': 0, 'mirror_diff': 0}
    xs = [p[0] for p in vox_set]
    ys = [p[1] for p in vox_set]
    zs = [p[2] for p in vox_set]
    x0, y0, z0 = min(xs) - 1, min(ys) - 1, min(zs) - 1
    sx = max(xs) - x0 + 2
    sy = max(ys) - y0 + 2
    sz = max(zs) - z0 + 2
    arr = np.zeros((sx, sy, sz), dtype=bool)
    for x, y, z in vox_set:
        arr[x - x0, y - y0, z - z0] = True
    _, n_comp = ndimage.label(arr)
    bg = ndimage.label(~arr)[0]
    ext = int(bg[0, 0, 0])
    cav = int(np.sum((~arr) & (bg != ext)))
    mdiff = sum(1 for (x, y, z) in vox_set if (x, 2 * yc - y, z) not in vox_set)
    return {'count': len(vox_set), 'components_6': int(n_comp), 'cavities': cav, 'mirror_diff': int(mdiff)}


def main():
    design = HERE
    probe = None
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            probe = a.split('=', 1)[1]
        elif not a.startswith('--'):
            design = a

    plan = HL.load_plan(design)
    L, _, S, x0, ylo = hull_build(plan, None)
    YC = L.YC
    C = {k: int(DL.V(v)) for k, v in plan['hull_build']['colors'].items()}
    RED = C['red']      # 192 朱漆
    GOLD = C['gold']    # 212 金黃
    TEAL = C['teal']    # 53  青綠
    WALE = C['wale']    # 36  黑漆
    WHITE = C['below']  # 218 白底（⛔ 絕不用 255）
    WOOD = C['hull']    # 177 福杉

    # 讀入步驟 4 + 5 完整已落格結構（船殼 + 甲板 + 梯子），確保任何裝飾 0 重疊、0 擋路
    hull_map = load_vox_map(os.path.join(design, 'masks', 'hull', 'hull_01.vox.txt'))
    carve_map = load_vox_map(os.path.join(design, 'masks', 'ports', 'carve.vox.txt'))
    for k in carve_map:
        hull_map.pop(k, None)
    occ_hull = set(hull_map.keys())
    occ_all = set(occ_hull)
    for folder in ('decks', 'ladders'):
        fd = os.path.join(design, 'masks', folder)
        for fn in sorted(os.listdir(fd)):
            if fn.endswith('.vox.txt'):
                occ_all.update(load_vox_map(os.path.join(fd, fn)).keys())

    # ── 1. 船尾窗玻璃（6 連通、完全鏡像對稱、不與木構重疊；Ship_Materials「窗的玻璃」）──
    raw_glass = load_vox_map(os.path.join(design, 'masks', 'ports', 'glass.vox.txt'))
    swin = plan['ports']['stern_windows']
    GLASS_C = int(swin['glass_color'])  # 155
    glass_map = {}
    # 只由右舷 (y > YC) 基準格生成並鏡射到左舷，再補齊換排斜角接點確保每扇窗 6 連通
    y_p0, y_p1 = swin['ys'][0]
    y_s0, y_s1 = swin['ys'][1]
    assert y_p0 + y_s1 == 2 * YC and y_p1 + y_s0 == 2 * YC, '雙艉窗計畫座標未對稱'
    by_yz_s = {}
    for y in range(y_s0, y_s1 + 1):
        for z in range(swin['z_lo'], swin['z_hi'] + 1):
            # 取船殼艉窗洞最內/中段格（優先讀 raw_glass 對應 x，確保 P/S 鏡像一致）
            x_raw = [x for (x, yy, zz) in raw_glass if yy == y and zz == z]
            assert x_raw, f'缺少玻璃基準格 ({y},{z})'
            x_g = x_raw[0]
            assert (x_g, y, z) not in occ_all and (x_g, 2 * YC - y, z) not in occ_all, f'玻璃重疊木構 ({x_g},{y},{z})'
            by_yz_s[(y, z)] = x_g
            glass_map[(x_g, y, z)] = GLASS_C
            glass_map[(x_g, 2 * YC - y, z)] = GLASS_C
    # 斜艉換行時補 1 格 6 連通橋接（確認不碰兩側木構）
    for (y, z), x1 in sorted(by_yz_s.items()):
        if (y, z + 1) in by_yz_s:
            x2 = by_yz_s[(y, z + 1)]
            if x2 != x1:
                ym = 2 * YC - y
                if (x2, y, z) not in occ_all and (x2, ym, z) not in occ_all:
                    glass_map[(x2, y, z)] = GLASS_C
                    glass_map[(x2, ym, z)] = GLASS_C
                elif (x1, y, z + 1) not in occ_all and (x1, ym, z + 1) not in occ_all:
                    glass_map[(x1, y, z + 1)] = GLASS_C
                    glass_map[(x1, ym, z + 1)] = GLASS_C
                else:
                    raise SystemExit(f'✗ 無法為艉窗玻璃 y={y}, z={z}->{z+1} 找到無衝突 6 連通接點')
    glass_stats = check_struct_stats(set(glass_map.keys()), YC)
    assert glass_stats['components_6'] == 2, f'期望 2 扇完整 6 連通玻璃，實得 {glass_stats}'
    assert glass_stats['cavities'] == 0 and glass_stats['mirror_diff'] == 0

    # ── 2. 高尾懸挑陽台與上層望樓欄杆（尾樓陽台欄杆，結構關聯件）──
    # 構造包含三段連為 1 體的傳統福船高尾雕欄（0 重疊、0 空腔、不遮擋 z=41..46 艉窗與 z=58..64 花屁股主徽）：
    #   (a) z=52..53 懸挑陽台地板（x=57..x_aft(y,z)-1, y=77..115）＋ 5 道支承托架（z=49..51，止於艉窗上方 2 格）
    #   (b) z=54..56 陽台鏤空欄杆（x=57..58 外緣立柱＋細金扶手，z=56 止於花屁股主徽 z=58 下方）
    #   (c) y=77/115 外隅雕花立柱連上 z=69..72 尾樓頂緣朱金望樓欄杆（後圍 x=60..61＋兩舷回轉至 x=70，遠離 x=86 迴旋砲）
    balcony = {}

    def x_aft_hull(y, z):
        xs = [x for x in range(58, 76) if (x, y, z) in occ_hull]
        return min(xs) if xs else 63

    # (a) 懸挑陽台底板 z=52..53 & 托架 z=49..51
    for z in (52, 53):
        for y in range(77, 116):
            dy = abs(y - YC)
            xa = x_aft_hull(y, z)
            x_back = 58 if dy >= 18 else 57
            for x in range(x_back, xa):
                if (x, y, z) not in occ_all:
                    is_edge = (x == x_back or dy >= 18)
                    balcony[(x, y, z)] = GOLD if (z == 53 and is_edge) else (RED if z == 52 and is_edge else WOOD)

    for y in (79, 88, 96, 104, 113):
        for z, x_reach in ((51, 58), (50, 59), (49, 60)):
            xa = x_aft_hull(y, z)
            for x in range(x_reach, xa):
                if (x, y, z) not in occ_all:
                    balcony[(x, y, z)] = GOLD if x == x_reach else RED

    # (b) 陽台鏤空欄杆 z=54..56（立柱間隔 4 格，鏤空不擋花屁股底紋）
    post_ys = {78, 82, 86, 90, 96, 102, 106, 110, 114}
    for y in range(78, 115):
        dy = abs(y - YC)
        x_rail = 58 if dy >= 18 else 57
        # 手扶頂欄 z=56
        balcony[(x_rail, y, 56)] = GOLD
        if y in post_ys:
            for z in (54, 55):
                balcony[(x_rail, y, z)] = RED
    # 陽台左右兩端接回船殼 corner x=59..62（沿 y=78 & 114）
    for y in (78, 114):
        for z in (54, 55, 56):
            xa = x_aft_hull(y, z)
            for x in range(59, xa):
                if (x, y, z) not in occ_all:
                    balcony[(x, y, z)] = GOLD if z == 56 else RED

    # (c) 尾隅外柱連結上下欄杆（y=78 & y=114 外貼面，自 z=56 沿斜艉攀升至 z=69）
    for z in range(56, 70):
        for y in (78, 114):
            xa = x_aft_hull(y, z)
            x_post = xa - 1
            if (x_post, y, z) not in occ_all:
                balcony[(x_post, y, z)] = GOLD if z in (60, 64, 68) else RED
        # 補斜艉升層 6 連通橫接（當 xa(z) != xa(z-1)）
        if z > 56:
            for y in (78, 114):
                xp_cur = x_aft_hull(y, z) - 1
                xp_prev = x_aft_hull(y, z - 1) - 1
                if xp_cur != xp_prev and (xp_cur, y, z - 1) not in occ_all:
                    balcony[(xp_cur, y, z - 1)] = RED
    # 尾隅外柱 z=70 往後內收一格接上 z=70..72 上層望樓欄杆 (59, y, 69) -> (59, y, 70) -> (60, y, 70)
    for y in (78, 114):
        xp_top = x_aft_hull(y, 69) - 1
        if (xp_top, y, 70) not in occ_all:
            balcony[(xp_top, y, 70)] = RED

    # 上層尾樓頂緣望樓欄杆 z=70..72（後封緣 x=60, y=78..114 ＋ 兩舷止於 x=70，確保與 x=86 砲位留足 1.6m 空隙）
    # 先量 x=60..70 在 z=68 最外緣，確保欄杆貼座在船殼頂正上方且兩端 6 連通
    top_rail_pts = [(60, y) for y in range(78, 115)]
    side_edges = {}
    for x in range(61, 71):
        ys_wall = [y for y in range(70, 122) if (x, y, 68) in occ_hull]
        if ys_wall:
            side_edges[x] = (min(ys_wall), max(ys_wall))
            top_rail_pts.append((x, min(ys_wall)))
            top_rail_pts.append((x, max(ys_wall)))
    for x, y in sorted(set(top_rail_pts)):
        is_post = (x == 60 and y in post_ys) or (x > 60 and x in (62, 66, 70))
        if (x, y, 69) not in occ_all:
            balcony[(x, y, 69)] = RED
        balcony[(x, y, 72)] = GOLD
        if is_post:
            balcony[(x, y, 70)] = RED
            balcony[(x, y, 71)] = RED
    # 將 x=60 尾角 (60, 78/114) 與 side_edges[x] 在 z=72（及若為空則 z=69）正交 6 連通接順
    prev_p, prev_s = 78, 114
    for x in range(61, 71):
        if x not in side_edges:
            continue
        cur_p, cur_s = side_edges[x]
        for yy in range(min(prev_p, cur_p), max(prev_p, cur_p) + 1):
            balcony[(x, yy, 72)] = GOLD
        for yy in range(min(prev_s, cur_s), max(prev_s, cur_s) + 1):
            balcony[(x, yy, 72)] = GOLD
        prev_p, prev_s = cur_p, cur_s

    assert not (set(balcony.keys()) & occ_all), '尾樓陽台欄杆重疊船殼或甲板！'
    balcony_stats = check_struct_stats(set(balcony.keys()), YC)
    # 若對稱性要求 0，檢查並確認 1 元件 0 空腔
    assert balcony_stats['components_6'] == 1, f'尾樓陽台欄杆應為 1 連通元件，實得 {balcony_stats}'
    assert balcony_stats['cavities'] == 0, f'尾樓陽台欄杆有封閉空腔：{balcony_stats}'
    assert balcony_stats['mirror_diff'] == 0, f'尾樓陽台欄杆未鏡像對稱：{balcony_stats}'

    # ── 3. 船首龍獅浪紋彩雕（deco-bow，外部模型 deco=1，位於斜艏柱前 x>=324＋側翼頰飾，0 重疊＆不擋 x<=323,z=57 首支索點）──
    # 世界錨定範圍：x_anchor=318, y_center=YC=96（寬 21 格 y=86..106 -> 局部 y=0..20, pivot=(0, 10.5, 0)），z_anchor=47..56
    deco_bow_world = {}
    x_anchor_bow, z_anchor_bow = 318, 47
    y_half_bow = 10  # y = 86..106 (width 21)

    def x_fwd_hull(y, z):
        xs = [x for x in range(310, 326) if (x, y, z) in occ_hull]
        return max(xs) if xs else 318

    # 正前方獅頭主徽（z=48..56，y=91..101，貼在船首柱正前面 x_fwd + 1 .. + 3）
    for z in range(48, 57):
        for y in range(91, 102):
            dy = abs(y - YC)
            xf = x_fwd_hull(y, z)
            dz = abs(z - 52)
            # 獅面微拱厚度 2~3 格
            thick = 3 if (dy <= 2 and dz <= 2) else (2 if dy <= 4 else 1)
            for k in range(1, thick + 1):
                xw = xf + k
                if (xw, y, z) in occ_all:
                    continue
                # 配色：外圈金鬃 (z in 48,56 or dy>=4)、朱紅獅額/鼻 (192)、金睛眉 (212)、黑瞳 (y=94,98 z=53)、白獠牙 (y=94,98 z=49)
                if k == thick and z == 53 and dy == 2:
                    col = WALE
                elif k == thick and z == 49 and dy in (2, 3):
                    col = WHITE
                elif z in (48, 56) or dy >= 4 or (dy <= 1 and z in (51, 52)):
                    col = GOLD
                else:
                    col = RED
                deco_bow_world[(xw, y, z)] = col
    # 兩側捲雲眉翼（沿船艏外側翼 z=50..54, |dy|=6..9 與獅面 dy=5 重疊接順，緊貼船殼外 1~2 格、z<=54 不妨礙支索）
    wing_spans = {
        6: (321, 322, 50, 54),
        7: (320, 321, 51, 53),
        8: (319, 320, 51, 53),
        9: (318, 319, 52, 52),
    }
    for dy, (xa, xb, za, zb) in wing_spans.items():
        for z in range(za, zb + 1):
            for x in range(xa, xb + 1):
                for side in (-1, 1):
                    y = YC + side * dy
                    if (x, y, z) not in occ_all:
                        deco_bow_world[(x, y, z)] = GOLD if z in (50, 54) or dy >= 8 else TEAL

    # ── 4. 高尾翔龍花飾匾（deco-stern，外部模型 deco=1，安放於尾樓頂 z=72 欄杆正上方 z=73..79，x=59..60）──
    deco_stern_world = {}
    x_anchor_stern, z_anchor_stern = 58, 73
    y_half_stern = 15  # y = 81..111 (width 31)
    for y in range(81, 112):
        dy = abs(y - YC)
        for z in range(73, 80):
            # 中央匾額 y=86..106 (dy<=10), z=73..77；中心飛龍山花 z=78 (dy<=5)；兩側翔龍鳳尾 dy=11..15 向上翹起
            in_board = (dy <= 10 and 73 <= z <= 77)
            in_peak = (dy <= 5 and z == 78) or (dy <= 2 and z == 79)
            in_wing = (11 <= dy <= 15 and ((dy == 11 and 73 <= z <= 76) or (dy == 12 and 74 <= z <= 77) or (dy == 13 and 75 <= z <= 77) or (dy == 14 and 76 <= z <= 78) or (dy == 15 and 77 <= z <= 78)))
            if not (in_board or in_peak or in_wing):
                continue
            xs = (59, 60) if (in_board or in_peak) else (60,)
            for x in xs:
                if z in (73, 77, 79) or dy in (10, 14, 15) or in_peak:
                    col = GOLD
                elif in_wing:
                    col = TEAL if z in (75, 77) else GOLD
                elif dy in (0, 3, 6) and z == 75:
                    col = GOLD
                elif dy <= 8 and z == 75:
                    col = RED
                else:
                    col = WALE if (dy in (1, 2, 4, 5) and z in (74, 76)) else RED
                deco_stern_world[(x, y, z)] = col

    # ── 5. 兩舷護舷（複用 kiara-tunis-sandal-01m-fender，size 5×3×5，體素 x=1..3, y=1, z=1..4）──
    # pivot = (2.5, 1.5, 2.5)：S (+y, rot 0) 放 y_hull_max + 1.5；P (-y, rot 180) 放 y_hull_min - 0.5
    # 量測 x=185..187 與 x=251..253 在 z=32..35 區間的船殼外緣（避開所有砲門 138/166/206/234 與 z>=37 外飄）
    fenders = []
    fender_world_cells = set()
    shift_fender = -1 if probe == 'shift_fender_in=-1' else 0
    for fx in (186, 252):
        # 驗證 3×4 接觸區 (x=fx-1..fx+1, z=32..35) 外側無凸出重疊
        ymax_s = max(max(y for (x, y, z) in occ_hull if x == xx and z == zz) for xx in (fx - 1, fx, fx + 1) for zz in range(32, 36))
        ymin_p = min(min(y for (x, y, z) in occ_hull if x == xx and z == zz) for xx in (fx - 1, fx, fx + 1) for zz in range(32, 36))
        ys_w = ymax_s + 1 + shift_fender
        yp_w = ymin_p - 1 - shift_fender
        fenders.append({'name': f'護舷-S-{fx}', 'at': [fx + 0.5, ys_w + 0.5, 33.5], 'pivot': [2.5, 1.5, 2.5], 'rotate': [0, 0, 0], 'world_box': [[fx - 1, fx + 1], [ys_w, ys_w], [32, 35]]})
        fenders.append({'name': f'護舷-P-{fx}', 'at': [fx + 0.5, yp_w + 0.5, 33.5], 'pivot': [2.5, 1.5, 2.5], 'rotate': [0, 0, 180], 'world_box': [[fx - 1, fx + 1], [yp_w, yp_w], [32, 35]]})
        for xx in (fx - 1, fx, fx + 1):
            for zz in range(32, 36):
                if zz == 35 and xx != fx:
                    continue
                fender_world_cells.add((xx, ys_w, zz))
                fender_world_cells.add((xx, yp_w, zz))

    # 探針測試：檢查 deco-bow / fenders / deco-stern 與既有船體＋甲板＋陽台欄杆之碰撞
    dx_probe = -3 if probe == 'shift_bow=-3' else 0
    shifted_bow = {(x + dx_probe, y, z) for (x, y, z) in deco_bow_world}
    bow_overlap = len(shifted_bow & (occ_all | set(balcony)))
    stern_overlap = len(set(deco_stern_world) & (occ_all | set(balcony)))
    fender_overlap = len(fender_world_cells & (occ_all | set(balcony)))
    balcony_overlap = len(set(balcony) & occ_all)
    glass_overlap = len(set(glass_map) & (occ_all | set(balcony)))

    bow_stats = check_struct_stats(set(deco_bow_world), YC)
    stern_stats = check_struct_stats(set(deco_stern_world), YC)

    if probe:
        print(json.dumps({
            'probe': probe,
            'bow_overlap': bow_overlap,
            'stern_overlap': stern_overlap,
            'fender_overlap': fender_overlap,
            'balcony_overlap': balcony_overlap,
            'glass_overlap': glass_overlap,
        }, ensure_ascii=False))
        return

    assert bow_overlap == 0 and stern_overlap == 0 and fender_overlap == 0 and balcony_overlap == 0 and glass_overlap == 0, \
        f'裝飾碰撞：{bow_overlap=} {stern_overlap=} {fender_overlap=} {balcony_overlap=} {glass_overlap=}'
    assert bow_stats['components_6'] == 1 and bow_stats['cavities'] == 0 and bow_stats['mirror_diff'] == 0, f'bow_stats={bow_stats}'
    assert stern_stats['components_6'] == 1 and stern_stats['cavities'] == 0 and stern_stats['mirror_diff'] == 0, f'stern_stats={stern_stats}'

    # 輸出檔案（世界座標掩碼給關聯件，局部座標掩碼給外部模型）
    out_dir = os.path.join(design, 'masks', 'deco')
    os.makedirs(out_dir, exist_ok=True)

    p_glass = os.path.join(out_dir, 'stern_glass.vox.txt')
    with open(p_glass, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 福建趕繒船 步驟 6：船尾窗玻璃（6 連通、完全對稱，material=glass）x,y,z,color\n')
        for (x, y, z), c in sorted(glass_map.items()):
            f.write(f'{x},{y},{z},{c}\n')

    p_bal = os.path.join(out_dir, 'stern_balcony.vox.txt')
    with open(p_bal, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 福建趕繒船 步驟 6：高尾懸挑陽台與上層望樓欄杆（世界座標，0 重疊）x,y,z,color\n')
        for (x, y, z), c in sorted(balcony.items()):
            f.write(f'{x},{y},{z},{c}\n')

    p_bow = os.path.join(out_dir, 'deco_bow.vox.txt')
    bow_local = {(x - x_anchor_bow, y - (YC - y_half_bow), z - z_anchor_bow): c for (x, y, z), c in deco_bow_world.items()}
    assert all(0 <= lx < 12 and 0 <= ly < 21 and 0 <= lz < 12 for lx, ly, lz in bow_local)
    with open(p_bow, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'# 福建趕繒船 步驟 6：船首龍獅彩雕（局部座標，pivot=(0,{y_half_bow + 0.5},0)）x,y,z,color\n')
        for (lx, ly, lz), c in sorted(bow_local.items()):
            f.write(f'{lx},{ly},{lz},{c}\n')

    p_stern = os.path.join(out_dir, 'deco_stern.vox.txt')
    stern_local = {(x - x_anchor_stern, y - (YC - y_half_stern), z - z_anchor_stern): c for (x, y, z), c in deco_stern_world.items()}
    assert all(0 <= lx < 6 and 0 <= ly < 31 and 0 <= lz < 10 for lx, ly, lz in stern_local)
    with open(p_stern, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'# 福建趕繒船 步驟 6：高尾翔龍牌飾（局部座標，pivot=(0,{y_half_stern + 0.5},0)）x,y,z,color\n')
        for (lx, ly, lz), c in sorted(stern_local.items()):
            f.write(f'{lx},{ly},{lz},{c}\n')

    placement = {
        'glass': glass_stats,
        'balcony': balcony_stats,
        'deco_bow': {
            'size': '12,21,12',
            'at': [float(x_anchor_bow), float(YC + 0.5), float(z_anchor_bow)],
            'pivot': [0.0, float(y_half_bow + 0.5), 0.0],
            'stats': bow_stats,
        },
        'deco_stern': {
            'size': '6,31,10',
            'at': [float(x_anchor_stern), float(YC + 0.5), float(z_anchor_stern)],
            'pivot': [0.0, float(y_half_stern + 0.5), 0.0],
            'stats': stern_stats,
        },
        'fenders': fenders,
        'overlaps': {
            'bow': bow_overlap,
            'stern': stern_overlap,
            'fender': fender_overlap,
            'balcony': balcony_overlap,
            'glass': glass_overlap,
        },
        'sha256': {
            'stern_glass': sha256_file(p_glass),
            'stern_balcony': sha256_file(p_bal),
            'deco_bow': sha256_file(p_bow),
            'deco_stern': sha256_file(p_stern),
        },
    }
    with open(os.path.join(design, 'deco_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(placement, f, ensure_ascii=False, indent=2)
    with open(os.path.join(design, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(placement, f, ensure_ascii=False, indent=2)

    print(json.dumps(placement, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
