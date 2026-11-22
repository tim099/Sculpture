# 明鄭一號大鳥船 新圖紙 05（TASK-1316 步驟 6）：艉樓窗玻璃、艉迴廊＋雙層戰棚女牆箭窗、船首繪飾、高尾樓牌匾與 6 具護舷靠墊
#   用法：python -I -X utf8 draft_deco.py <design 資料夾> [--probe=shift_balcony=+3]
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_lines as DL
import draft_decks as DD

sys.stdout.reconfigure(encoding='utf-8')


def load_vox_set(path):
    s = set()
    if not os.path.exists(path):
        return s
    with open(path, encoding='utf-8') as f:
        for l in f:
            l = l.strip()
            if not l or l.startswith('#'):
                continue
            x, y, z, c = map(int, l.split(','))
            s.add((x, y, z, c))
    return s


def main():
    design = HERE
    probe = None
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            probe = a.split('=', 1)[1]
        elif not a.startswith('--'):
            design = a

    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    C = {k: DL.V(v) for k, v in plan['hull_build']['colors'].items()}
    WOOD, INNER, TRIM, RED, GOLD, TEAL = C['hull'], C['inner'], C['trim'], C['red'], C['gold'], C['teal']
    GLASS = int(plan['ports']['stern_windows']['glass_color'])

    zmax = int(math.ceil(L.top_max)) + 16
    x0 = int(math.floor(L.xa_min)) - 12
    x1 = int(math.ceil(L.xf_max)) + 16
    half = int(math.ceil(L.B)) + 10
    ylo = L.YC - half
    yhi = L.YC + half
    shape = (x1 - x0 + 1, yhi - ylo + 1, zmax + 1)

    wall_col, _ = DD.load_carved_shell(design, plan, L, x0, ylo, shape)
    hull_occ = wall_col > 0

    # 載入步驟 5 所有甲板／梯子／艙房佔位，保護零重疊
    deck_occ = np.zeros(shape, bool)
    for folder in ('decks', 'ladders', 'rooms'):
        pdir = os.path.join(design, 'masks', folder)
        if not os.path.isdir(pdir):
            continue
        for fn in os.listdir(pdir):
            if fn.endswith('.vox.txt'):
                arr = np.loadtxt(os.path.join(pdir, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
                if arr.size:
                    xi, yi, zi = arr[:, 0] - x0, arr[:, 1] - ylo, arr[:, 2]
                    m = (xi >= 0) & (xi < shape[0]) & (yi >= 0) & (yi < shape[1]) & (zi >= 0) & (zi < shape[2])
                    deck_occ[xi[m], yi[m], zi[m]] = True
    base_occ = hull_occ | deck_occ

    # ── 1. 艉樓窗玻璃（material=glass；斜牆上下排錯位時在空洞內補 1 格，確保每扇窗 6 連通整片無縫）──
    glass_p = os.path.join(design, 'masks', 'ports', 'glass.vox.txt')
    glass_pts = load_vox_set(glass_p)
    glass_arr = np.zeros(shape, np.uint8)
    for x, y, z, c in glass_pts:
        glass_arr[x - x0, y - ylo, z] = c
    # 若 (xi, yi, z) 有玻璃且 (xi, yi, z-1) 為空，但 (xi±1, yi, z-1) 有玻璃（斜艉牆階差）⇒ 在 (xi, yi, z-1) 或 (nx, yi, z) 補連通格
    xs_g, ys_g, zs_g = np.where(glass_arr > 0)
    for xi, yi, z in zip(xs_g, ys_g, zs_g):
        if z > 0 and glass_arr[xi, yi, z - 1] == 0:
            for dx in (-1, 1):
                if 0 <= xi + dx < shape[0] and glass_arr[xi + dx, yi, z - 1] > 0:
                    if not base_occ[xi, yi, z - 1]:
                        glass_arr[xi, yi, z - 1] = GLASS
                    elif not base_occ[xi + dx, yi, z]:
                        glass_arr[xi + dx, yi, z] = GLASS
    _, n_glass_comp = ndimage.label(glass_arr > 0)
    glass_overlap = int(((glass_arr > 0) & base_occ).sum())

    # ── 2. 艉迴廊＋高尾樓匾額框＋雙層戰棚女牆與箭窗（stern-balcony）──
    balc = np.zeros(shape, np.uint8)
    shift_x = 3 if probe == 'shift_balcony=+3' else 0
    probe_hits = [0]

    def put_b(xw, yw, zw, col):
        xi, yi = xw + shift_x - x0, yw - ylo
        if 0 <= xi < shape[0] and 0 <= yi < shape[1] and 0 <= zw < shape[2]:
            if base_occ[xi, yi, zw]:
                probe_hits[0] += 1
            else:
                balc[xi, yi, zw] = col

    # (2a) 高聳尾樓懸挑迴廊（z=87..97，x=50..56；中央 y=125..131 z=92..95 預留步驟 11 舵柄通道）
    # 托樑腳架 z=87..89
    for yw in (104, 114, 123, 133, 142, 152):
        for step, zw in enumerate((87, 88, 89)):
            for xw in range(54 - step, 58):
                put_b(xw, yw, zw, TRIM)
    # 迴廊踏板 z=90..91（y=102..154, x=51..56）
    for xw in range(51, 57):
        for yw in range(102, 155):
            if 55 <= xw <= 56 and 125 <= yw <= 131:
                continue  # 避開艉柱斜面與舵槽
            col = TRIM if (xw == 51 or yw in (102, 154)) else INNER
            put_b(xw, yw, 90, col)
            if not (125 <= yw <= 131 and xw >= 52):
                put_b(xw, yw, 91, WOOD)
    # 迴廊欄杆 z=92..96（x=51 與側邊 y=102,154；y=125..131 z=92..94 留舵柄槽，欄頂 z=95..96 橫跨不斷裂）
    for xw in range(51, 57):
        for yw in (102, 154):
            for zw in range(92, 97):
                c = GOLD if zw == 96 else (RED if zw in (93, 95) else TRIM)
                if (zw in (92, 94) and (xw % 2 == 1)) or zw in (93, 95, 96):
                    put_b(xw, yw, zw, c)
    for yw in range(102, 155):
        for zw in range(92, 97):
            # 預留步驟 11 舵柄開口：x=51..54, y=125..131, z=92..94
            if 125 <= yw <= 131 and zw <= 94:
                continue
            if zw in (92, 94) and ((yw - 128) % 3 != 0) and zw != 95:
                continue
            c = GOLD if (zw == 96 or (abs(yw - 128) <= 6 and zw == 95)) else (RED if zw in (93, 95) else TRIM)
            put_b(51, yw, zw, c)

    # 高尾樓飛簷牌匾門冠（z=102..109，x=55..58）
    for yw in range(104, 153):
        if abs(yw - 128) <= 24:
            put_b(55, yw, 108, GOLD if abs(yw - 128) % 4 == 0 else RED)
            put_b(55, yw, 109, TRIM)
            put_b(54, yw, 109, GOLD if abs(yw - 128) <= 8 else RED)
    for yw in (104, 114, 142, 152):
        for zw in range(97, 108):
            put_b(55, yw, zw, RED if zw % 3 else GOLD)

    # (2b) 雙層戰棚女牆與箭窗
    # 下層：上戰棚露天腰甲板 x=137..391（避開各上戰棚砲門 x±5、貓頭 x=387..394）
    P = plan['ports']
    skip_waist_x = set()
    for cfg_key in ('upper_fagong', 'upper_hongyi'):
        hw = int(P[cfg_key]['w']) // 2 + 2
        for px in P[cfg_key]['x']:
            for xw in range(px - hw, px + hw + 1):
                skip_waist_x.add(xw)
    for xw in range(386, 396):  # 預留步驟 11 雙舷貓頭錨架
        skip_waist_x.add(xw)

    skip_poop_x = set()
    for sw in plan['guns_build']['swivels']:
        if sw['deck'] == 'poop':
            for xw in range(sw['cut_x0'] - 1, sw['cut_x1'] + 2):
                skip_poop_x.add(xw)

    xs_top = np.array([p[0] for p in plan['lines']['top']], float)
    zs_top = np.array([p[1] for p in plan['lines']['top']], float)

    def place_parapet(x_lo, x_hi, skip_set, tier='waist'):
        for xw in range(x_lo, x_hi + 1):
            if xw in skip_set:
                continue
            xi = xw - x0
            zt = int(np.floor(float(np.interp(xw + 0.5, xs_top, zs_top)) - 0.5))
            # 找該 x 在舷頂 zt 的左右舷最外與次外兩格（對應 wall=2 舷牆正上方）
            row = np.nonzero(hull_occ[xi, :, zt])[0]
            if len(row) < 4:
                continue
            y_list = []
            # 左舷 (low y) 最外兩格 & 右舷 (high y) 最外兩格
            p_outer, s_outer = int(row.min()), int(row.max())
            for yi_col, is_outer in ((p_outer, True), (p_outer + 1, False), (s_outer, True), (s_outer - 1, False)):
                yw = yi_col + ylo
                # 跳過與旁邊不相接或離中線太近處
                if abs(yw - YC) < 12:
                    continue
                is_slit = ((xw % 6) == 0)
                for dz in (1, 2, 3):
                    if is_slit and dz in (1, 2):
                        continue  # 箭窗／銃眼開口
                    if dz == 3:
                        c = GOLD if (tier == 'poop' and xw % 4 == 0) else TRIM
                    else:
                        c = RED if is_outer else INNER
                    put_b(xw, yw, zt + dz, c)

    place_parapet(137, 384, skip_waist_x, tier='waist')
    place_parapet(62, 129, skip_poop_x, tier='poop')

    # ── 3. 船首繪飾模型（deco-bow：0.05 m／格，scale=0.5，鳥喙鳳翼彩繪龍首）──
    # 局部座標框 48 × 56 × 48（0.05 m/voxel -> 2.4 × 2.8 × 2.4 m），pivot=(24.0, 28.0, 8.0)
    # 掛載於 (449.5, 128.5, 92.0)：局部 (x,y,z) 對齊船座標 x = 449.5 + (lx - 24)*0.5, y = 128.5 + (ly - 28)*0.5, z = 92 + (lz - 8)*0.5
    bow_shape = (48, 56, 48)
    bow_piv = (24.0, 28.0, 8.0)
    bow_at = (449.5, 128.5, 92.0)
    bow_g = np.zeros(bow_shape, np.uint8)
    # 中線大鳥喙高昂龍鳳冠與雙翼展開兩側彩板（外張避開船首斜面）
    for lx in range(6, 44):
        for lz in range(4, 38):
            # 高昂頭冠弧線（沿 +x 上翹成鳥首，前伸 x=24..43, z=12..34）
            u = (lx - 6) / 37.0
            z_spine = 10 + 18 * (u ** 1.35)
            # 頭頸脊線 y=26..29
            for ly in range(25, 31):
                dy = abs(ly - 27.5)
                thick = 3.2 if u > 0.72 else 2.2
                if abs(lz - z_spine) <= thick and dy <= (2.6 if u > 0.72 else 1.8):
                    # 頭冠金邊、朱漆鳳首、綠鳥羽眼
                    if u > 0.78 and lz >= z_spine + 1:
                        bow_g[lx, ly, lz] = GOLD
                    elif 0.74 <= u <= 0.86 and abs(lz - z_spine) <= 1 and dy >= 1.5:
                        bow_g[lx, ly, lz] = TEAL
                    elif u > 0.88 and lz < z_spine:
                        bow_g[lx, ly, lz] = GOLD  # 鳥喙金尖
                    else:
                        bow_g[lx, ly, lz] = RED if (lz % 3 != 0) else GOLD
            # 鳳首高羽冠（lx=26..36, z=z_spine+2..z_spine+8）
            if 26 <= lx <= 37 and z_spine + 2 <= lz <= z_spine + 7:
                if (lx + lz) % 2 == 0:
                    bow_g[lx, 27:29, lz] = GOLD if lz > z_spine + 5 else RED
            # 兩舷外張雙翼板（|ly - 27.5| = 12..25, lx=8..30, z=9..26，外張貼在船殼外斜側面）
            if 8 <= lx <= 30:
                v = (lx - 8) / 22.0
                wing_top = 12 + 14 * (1.0 - v * 0.4)
                wing_bot = 6 + 6 * v
                if wing_bot <= lz <= wing_top:
                    wy = int(round(13 + 7 * (1.0 - v)))
                    for side in (-1, 1):
                        ly = 27 + side * wy if side > 0 else 28 + side * wy
                        if 2 <= ly < 54:
                            c = GOLD if (lz >= wing_top - 1.5 or lx <= 10) else (TEAL if ((lx + lz) % 4 == 0) else RED)
                            bow_g[lx, ly, lz] = c
                            if 2 <= ly + side < 54:
                                bow_g[lx, ly + side, lz] = c

    # 檢查 bow_g 轉回船座標有無碰撞 hull_occ + deck_occ
    bow_hits = 0
    for lx, ly, lz in np.argwhere(bow_g > 0):
        sx = int(round(bow_at[0] + (lx - bow_piv[0]) * 0.5))
        sy = int(round(bow_at[1] + (ly - bow_piv[1]) * 0.5))
        sz = int(round(bow_at[2] + (lz - bow_piv[2]) * 0.5))
        xi, yi = sx - x0, sy - ylo
        if 0 <= xi < shape[0] and 0 <= yi < shape[1] and 0 <= sz < shape[2] and base_occ[xi, yi, sz]:
            # 清掉偶爾擦邊的局部格，確保模型外框格零重疊
            bow_g[lx, ly, lz] = 0
            bow_hits += 1

    # 修掉零重疊後的實際碰撞計數應為 0；若還殘留微擦再重測
    bow_post_hits = 0
    for lx, ly, lz in np.argwhere(bow_g > 0):
        sx = int(round(bow_at[0] + (lx - bow_piv[0]) * 0.5))
        sy = int(round(bow_at[1] + (ly - bow_piv[1]) * 0.5))
        sz = int(round(bow_at[2] + (lz - bow_piv[2]) * 0.5))
        xi, yi = sx - x0, sy - ylo
        if 0 <= xi < shape[0] and 0 <= yi < shape[1] and 0 <= sz < shape[2] and base_occ[xi, yi, sz]:
            bow_post_hits += 1

    # ── 4. 船尾牌匾模型（deco-stern：0.05 m／格，scale=0.5，朱金國姓龍鳳花尾牌匾）──
    # 局部 12 × 64 × 24，pivot=(8.0, 32.0, 12.0)，at=(53.5, 128.5, 102.5) -> 世界 x=50..54, y=112.5..144.5, z=96.5..108.5
    st_shape = (12, 64, 24)
    st_piv = (8.0, 32.0, 12.0)
    st_at = (53.5, 128.5, 102.5)
    st_g = np.zeros(st_shape, np.uint8)
    for ly in range(4, 60):
        for lz in range(4, 20):
            # 牌匾框與雲龍紋浮雕
            edge = (ly in (4, 5, 58, 59)) or (lz in (4, 5, 18, 19))
            for lx in range(4, 8):
                if edge:
                    st_g[lx, ly, lz] = GOLD
                elif lx in (5, 6):
                    # 內匾朱紅底＋中央金徽與青綠祥雲
                    dist = math.hypot(ly - 31.5, (lz - 11.5) * 1.4)
                    if dist <= 4.5:
                        st_g[lx, ly, lz] = GOLD
                    elif abs(ly - 31.5) % 8 <= 1 and lz in (9, 10, 13, 14):
                        st_g[lx, ly, lz] = TEAL
                    else:
                        st_g[lx, ly, lz] = RED
                elif lx == 4 and (edge or abs(ly - 31.5) <= 5):
                    st_g[lx, ly, lz] = GOLD

    st_occ_world = balc > 0
    st_hits = 0
    for lx, ly, lz in np.argwhere(st_g > 0):
        sx = int(round(st_at[0] + (lx - st_piv[0]) * 0.5))
        sy = int(round(st_at[1] + (ly - st_piv[1]) * 0.5))
        sz = int(round(st_at[2] + (lz - st_piv[2]) * 0.5))
        xi, yi = sx - x0, sy - ylo
        if 0 <= xi < shape[0] and 0 <= yi < shape[1] and 0 <= sz < shape[2] and (base_occ[xi, yi, sz] or st_occ_world[xi, yi, sz]):
            st_hits += 1

    # ── 5. 6 具複用護舷靠墊（kiara-tunis-sandal-01m-fender，原尺寸 0.1 m/voxel，scale=1.0）──
    # fender 實心在 local x=1..3, y=1, z=1..4 -> pivot=(2.5, 1.0, 2.5) 使 y=1 緊貼船殼最外側＋0.5 格（零重疊）
    fenders = []
    fender_hits = 0
    for idx, xw in enumerate((176, 250, 322), 1):
        zw = 63  # 介於兩條黑漆護木帶之間的壯實舷腰
        xi = xw - x0
        ys = np.nonzero(hull_occ[xi, :, zw])[0]
        y_s_outer = int(ys.max()) + ylo + 1.5
        y_p_outer = int(ys.min()) + ylo - 0.5
        for side_lbl, y_at, rot_z in (('S', y_s_outer, 0.0), ('P', y_p_outer, 180.0)):
            # 檢查 +/-1 x 範圍不撞 hull_occ
            yi_chk = int(round(y_at)) - ylo if side_lbl == 'S' else int(math.floor(y_at)) - ylo
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1, 2):
                    if hull_occ[xi + dx, yi_chk, zw + dz]:
                        fender_hits += 1
            fenders.append({
                'name': f'護舷-{side_lbl}{idx}',
                'source': 'kiara-tunis-sandal-01m-fender',
                'at': [float(xw + 0.5), float(y_at), float(zw)],
                'pivot': [2.5, 1.5 if side_lbl == 'S' else 1.5, 2.5],
                'rotate': [0.0, 0.0, rot_z],
                'scale': 1.0,
                'meta': {'deco': 1},
            })
    # 更精確：fender y=1 佔局部 [1,2)；pivot.y=1.5 ⇒ world y 佔 [y_at - 0.5, y_at + 0.5)
    # 改直接掃 y 外界取 max_outer + 1.5（y_at = y_out + 1.5，落在外板外側 1 格純空氣）
    fenders = []
    fender_hits = 0
    for idx, xw in enumerate((176, 250, 322), 1):
        zw = 63
        xi = xw - x0
        y_s_max = max(int(np.nonzero(hull_occ[xi + dx, :, zw + dz])[0].max()) + ylo
                      for dx in (-1, 0, 1) for dz in (-1, 0, 1, 2))
        y_p_min = min(int(np.nonzero(hull_occ[xi + dx, :, zw + dz])[0].min()) + ylo
                      for dx in (-1, 0, 1) for dz in (-1, 0, 1, 2))
        for side_lbl, y_w, rot_z in (('S', y_s_max + 1, 0.0), ('P', y_p_min - 1, 180.0)):
            yi_c = y_w - ylo
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1, 2):
                    if hull_occ[xi + dx, yi_c, zw + dz]:
                        fender_hits += 1
            fenders.append({
                'name': f'護舷-{side_lbl}{idx}',
                'source': 'kiara-tunis-sandal-01m-fender',
                'at': [float(xw + 0.5), float(y_w + 0.5), float(zw + 0.5)],
                'pivot': [2.5, 1.5, 2.5],
                'rotate': [0.0, 0.0, rot_z],
                'scale': 1.0,
                'meta': {'deco': 1},
            })

    # ── 統計與反證探針 ──
    balc_m = balc > 0
    balc_overlap = int((balc_m & base_occ).sum())
    balc_mirror = int((balc_m != balc_m[:, ::-1, :]).sum())
    bow_mirror = int(((bow_g > 0) != (bow_g[:, ::-1, :] > 0)).sum())
    st_mirror = int(((st_g > 0) != (st_g[:, ::-1, :] > 0)).sum())

    summary = {
        'stern_glass_cells': int((glass_arr > 0).sum()),
        'stern_glass_components': int(n_glass_comp),
        'stern_glass_overlap': glass_overlap,
        'stern_balcony_cells': int(balc_m.sum()),
        'stern_balcony_overlap': balc_overlap,
        'stern_balcony_probe_hits': probe_hits[0],
        'stern_balcony_mirror_diff': balc_mirror,
        'deco_bow_cells': int((bow_g > 0).sum()),
        'deco_bow_trimmed': bow_hits,
        'deco_bow_post_hits': bow_post_hits,
        'deco_stern_cells': int((st_g > 0).sum()),
        'deco_stern_hits': st_hits,
        'fenders_count': len(fenders),
        'fender_hits': fender_hits,
    }
    if probe:
        summary['probe'] = probe
        print(json.dumps(summary, ensure_ascii=False))
        return

    # ── 寫出清單與配置 ──
    od = os.path.join(design, 'masks', 'deco')
    os.makedirs(od, exist_ok=True)
    for fn in os.listdir(od):
        if fn.endswith('.vox.txt'):
            os.remove(os.path.join(od, fn))

    def dump_grid(path, arr, ox, oy, oz, head):
        idx = np.argwhere(arr > 0)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for xi_, yi_, zi_ in idx:
                f.write('%d,%d,%d,%d\n' % (xi_ + ox, yi_ + oy, zi_ + oz, arr[xi_, yi_, zi_]))
        return [int(len(idx)), hashlib.sha256(open(path, 'rb').read()).hexdigest()]

    lists = {
        'stern-glass': dump_grid(os.path.join(od, 'stern-glass.vox.txt'), glass_arr, x0, ylo, 0, '# 艉樓窗玻璃（192 格；material=glass）\n'),
        'stern-balcony': dump_grid(os.path.join(od, 'stern-balcony.vox.txt'), balc, x0, ylo, 0, '# 艉迴廊與雙層戰棚女牆箭窗\n'),
        'deco-bow': dump_grid(os.path.join(od, 'deco-bow.vox.txt'), bow_g, 0, 0, 0, '# 船首大鵬龍鳳飾（0.05 m/格）\n'),
        'deco-stern': dump_grid(os.path.join(od, 'deco-stern.vox.txt'), st_g, 0, 0, 0, '# 高尾樓牌匾飾（0.05 m/格）\n'),
    }

    deco_spec = {
        'links': [
            {'name': '艉樓窗玻璃', 'work': f"{plan['guns_build']['hull']}-stern-glass", 'title': '明鄭一號大鳥船 艉樓窗玻璃', 'mask': 'stern-glass.vox.txt', 'meta': {'material': 'glass'}},
            {'name': '艉迴廊', 'work': f"{plan['guns_build']['hull']}-stern-balcony", 'title': '明鄭一號大鳥船 艉迴廊與雙層戰棚女牆', 'mask': 'stern-balcony.vox.txt', 'meta': None},
        ],
        'custom_models': [
            {
                'name': '船首飾', 'work': f"{plan['guns_build']['hull']}-deco-bow", 'title': '明鄭一號大鳥船 船首彩繪飛鳥飾（0.05 m）',
                'size': list(bow_shape), 'mask': 'deco-bow.vox.txt',
                'at': list(bow_at), 'pivot': list(bow_piv), 'rotate': [0.0, 0.0, 0.0], 'scale': 0.5,
                'meta': {'deco': 1},
            },
            {
                'name': '船尾飾', 'work': f"{plan['guns_build']['hull']}-deco-stern", 'title': '明鄭一號大鳥船 高尾樓朱金匾額飾（0.05 m）',
                'size': list(st_shape), 'mask': 'deco-stern.vox.txt',
                'at': list(st_at), 'pivot': list(st_piv), 'rotate': [0.0, 0.0, 0.0], 'scale': 0.5,
                'meta': {'deco': 1},
            },
        ],
        'fenders': fenders,
    }
    with open(os.path.join(design, 'deco_spec.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(deco_spec, f, ensure_ascii=False, indent=1)

    # 出圖 sheet05_deco_v1.png（側視＋艉視）
    W, H = shape[0] + 180, shape[2] + 60
    im = Image.new('RGB', (W, H), (248, 246, 238))
    d = ImageDraw.Draw(im)
    d.text((20, 12), '明鄭一號大鳥船 新圖紙 05：雙層戰棚女牆箭窗、高尾樓迴廊、窗玻璃與裝飾', fill=(0, 0, 0), font=DL.font(15))
    # 側視投影 (max y)
    for xi_ in range(shape[0]):
        for zi_ in range(shape[2]):
            ys_h = np.nonzero(wall_col[xi_, :, zi_])[0]
            ys_b = np.nonzero(balc[xi_, :, zi_])[0]
            ys_g = np.nonzero(glass_arr[xi_, :, zi_])[0]
            col = 0
            if len(ys_h):
                col = int(wall_col[xi_, ys_h.max(), zi_])
            if len(ys_b):
                col = int(balc[xi_, ys_b.max(), zi_])
            if len(ys_g):
                col = int(glass_arr[xi_, ys_g.max(), zi_])
            if col:
                d.point((30 + xi_, H - 20 - zi_), fill=DL.rgb(col))
    # 疊上 bow_g, st_g
    for lx, ly, lz in np.argwhere(bow_g > 0):
        px = int(round(bow_at[0] + (lx - bow_piv[0]) * 0.5)) - x0 + 30
        pz = H - 20 - int(round(bow_at[2] + (lz - bow_piv[2]) * 0.5))
        if 0 <= px < W and 0 <= pz < H:
            d.point((px, pz), fill=DL.rgb(int(bow_g[lx, ly, lz])))
    for lx, ly, lz in np.argwhere(st_g > 0):
        px = int(round(st_at[0] + (lx - st_piv[0]) * 0.5)) - x0 + 30
        pz = H - 20 - int(round(st_at[2] + (lz - st_piv[2]) * 0.5))
        if 0 <= px < W and 0 <= pz < H:
            d.point((px, pz), fill=DL.rgb(int(st_g[lx, ly, lz])))
    im.save(os.path.join(design, 'sheet05_deco_v1.png'))

    summary['lists'] = lists
    with open(os.path.join(design, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != 'lists'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
