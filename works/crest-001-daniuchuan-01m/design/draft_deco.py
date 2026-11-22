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

    # ── 3. 船首繪飾模型（deco-bow：0.05 m／格，scale=0.5，緊貼船首舷緣與平頭艏封壁的鳥喙鳳翼彩繪龍首）──
    # 局部座標框 48 × 68 × 48（0.05 m/voxel -> 2.4 × 3.4 × 2.4 m），pivot=(24.0, 34.0, 12.0)
    # 掛載於 (449.5, 128.5, 90.0)：orig=(437.5, 111.5, 84.0) -> wx=floor(437.75+0.5*lx), wy=floor(111.75+0.5*ly), wz=floor(84.25+0.5*lz)
    bow_shape = (48, 68, 48)
    bow_piv = (24.0, 34.0, 12.0)
    bow_at = (449.5, 128.5, 90.0)
    bow_ox = bow_at[0] - bow_piv[0] * 0.5
    bow_oy = bow_at[1] - bow_piv[1] * 0.5
    bow_oz = bow_at[2] - bow_piv[2] * 0.5
    bow_g = np.zeros(bow_shape, np.uint8)

    # 先量每個船首 xw (442..454) 實際 hull_occ 最高實心層 zt 與右舷外緣 s_out
    hull_bow_top = {}
    hull_bow_sout = {}
    for xw in range(441, 456):
        xi = xw - x0
        if not (0 <= xi < shape[0]):
            continue
        zs_h = np.nonzero(hull_occ[xi].any(axis=0))[0]
        if not len(zs_h):
            continue
        zt = int(zs_h.max())
        ys_h = np.nonzero(hull_occ[xi, :, zt])[0] + ylo
        hull_bow_top[xw] = zt
        hull_bow_sout[xw] = int(ys_h.max())

    def put_sym(lx_, ly_, lz_, col_):
        if 0 <= lx_ < bow_shape[0] and 0 <= ly_ < bow_shape[1] and 0 <= lz_ < bow_shape[2]:
            bow_g[lx_, ly_, lz_] = col_
            bow_g[lx_, bow_shape[1] - 1 - ly_, lz_] = col_

    # (3a) 雙舷外翼紅綠格紋金邊彩板（lx=9..34 -> xw=442..454；底緣緊貼各 xw 的 zt+1 棕色舷緣，零縫隙）
    for lx in range(9, 35):
        xw = int(math.floor(bow_ox + (lx + 0.5) * 0.5))
        if xw not in hull_bow_top:
            continue
        zt = hull_bow_top[xw]
        s_out = hull_bow_sout[xw]
        lz_bot = int(round((zt + 1 - bow_oz) * 2))  # 正好對應 wz = zt + 1 的下層子格 (12 for zt=89, 14 for zt=90, 16 for zt=91)
        u_w = (lx - 9) / 25.0  # 0 (aft x=442) .. 1 (fwd x=454)
        # 尾端高金柱 (lz=36) 順弧收束至前端接艏胸壁 (lz=25)
        lz_top = int(round(36 - 13 * u_w + 2 * (u_w ** 2)))
        # 找到對應右舷舷緣最外兩格 [s_out-1, s_out]（wy=floor(111.75+0.5*ly)）
        ly_s_list = [ly for ly in range(34, 67)
                     if (s_out - 1) <= int(math.floor(bow_oy + (ly + 0.5) * 0.5)) <= s_out]
        if not ly_s_list:
            continue
        for lz in range(lz_bot, lz_top + 1):
            is_aft_post = (lx in (9, 10, 11))
            is_fwd_post = (lx >= 33)
            is_edge = is_aft_post or is_fwd_post or (lz <= lz_bot + 1) or (lz >= lz_top - 1)
            if is_edge:
                c = GOLD
            elif (lx + lz) % 3 == 0:
                c = TEAL
            else:
                c = RED
            for ly in ly_s_list:
                put_sym(lx, ly, lz, c)

    # (3b) 艏封壁橫向朱金胸甲（lx=29..34 -> xw=452..454；在平頭封壁 wz=91 之上從 wz=92 起鋪滿兩舷間距，接通左右翼與中線龍首座）
    for lx in range(29, 35):
        xw = int(math.floor(bow_ox + (lx + 0.5) * 0.5))
        if xw not in hull_bow_top:
            continue
        zt = hull_bow_top[xw]  # 91 at x=452..454
        s_out = hull_bow_sout[xw]
        lz_bot = int(round((zt + 1 - bow_oz) * 2))  # 16 (wz=92)
        lz_top = lz_bot + 7  # wz=92..95.5
        for ly in range(34, 67):
            wy = int(math.floor(bow_oy + (ly + 0.5) * 0.5))
            if wy > s_out:
                continue
            for lz in range(lz_bot, lz_top + 1):
                if lx >= 33 or lz <= lz_bot + 1 or lz >= lz_top - 1:
                    c = GOLD
                elif abs(ly - 33.5) % 4 < 1.5 and lz % 2 == 0:
                    c = TEAL
                else:
                    c = RED
                put_sym(lx, ly, lz, c)

    # (3c) 中線龍鳳鳥首高昂頭冠與金喙（lx=27..46 -> xw=451..460；根部實座於 x=452..454 wz=92..97 之封壁與胸甲上）
    for lx in range(27, 47):
        u_h = (lx - 27) / 19.0
        # 脊線自 lz=18 (wz=93, x=451) 向前昂揚至 lz=36 (wz=102, x=460)
        z_spine = 18.0 + 18.0 * (u_h ** 1.15)
        for ly in range(34, 41):
            dy = ly - 33.5
            half_y = 4.5 * (1.0 - 0.55 * u_h) + (1.0 if 0.60 <= u_h <= 0.82 else 0.0)
            if dy > half_y:
                continue
            half_z = 3.8 if u_h < 0.35 else (2.8 if u_h < 0.78 else 2.2)
            z_lo_n = max(16, int(math.floor(z_spine - half_z))) if lx >= 29 else int(math.floor(z_spine - half_z))
            z_hi_n = min(46, int(math.ceil(z_spine + half_z)))
            for lz in range(z_lo_n, z_hi_n + 1):
                if abs(lz - z_spine) > half_z and not (lx >= 29 and lz < z_spine):
                    continue
                if u_h > 0.82:
                    c = RED if (abs(lz - z_spine) < 0.7 and dy < 1.2) else GOLD  # 勾金鳥喙
                elif 0.62 <= u_h <= 0.80 and abs(lz - (z_spine + 0.5)) <= 1.0 and dy >= 1.5:
                    c = TEAL  # 翡翠鳳目
                elif lz >= z_spine + half_z - 1.1 or (lx >= 29 and lz <= 17):
                    c = GOLD
                else:
                    c = GOLD if (lz % 3 == 0 and dy <= 1.2) else RED
                put_sym(lx, ly, lz, c)
        # 高昂鏤空鳳冠羽（lx=31..43, lz=z_spine+2..z_spine+7）
        if 31 <= lx <= 43:
            for lz in range(int(round(z_spine + 1)), min(47, int(round(z_spine + 8)))):
                dz_c = lz - z_spine
                if dz_c <= 2.2 or ((lx + lz) % 2 == 0 and dz_c <= 6.5):
                    c = GOLD if dz_c > 4.2 or lx >= 41 else RED
                    put_sym(lx, 34, lz, c)

    # 清掉偶爾擦到 base_occ | (balc > 0) 的局部格，並確保單一 6 連通、0 空腔
    bow_hits = 0
    for lx, ly, lz in np.argwhere(bow_g > 0):
        wx = int(math.floor(bow_ox + (lx + 0.5) * 0.5))
        wy = int(math.floor(bow_oy + (ly + 0.5) * 0.5))
        wz = int(math.floor(bow_oz + (lz + 0.5) * 0.5))
        xi, yi = wx - x0, wy - ylo
        if 0 <= xi < shape[0] and 0 <= yi < shape[1] and 0 <= wz < shape[2] and (base_occ[xi, yi, wz] or balc[xi, yi, wz] > 0):
            bow_g[lx, ly, lz] = 0
            bow_hits += 1

    lbl_b, n_bow_raw = ndimage.label(bow_g > 0)
    if n_bow_raw > 1:
        sizes_b = np.bincount(lbl_b.ravel())
        sizes_b[0] = 0
        keep_b = int(np.argmax(sizes_b))
        bow_g[lbl_b != keep_b] = 0

    # 填補內部空腔（與邊界不相通的空白格）
    pad_b = np.pad(bow_g == 0, 1, constant_values=True)
    ext_b, _ = ndimage.label(pad_b)
    ext_id = ext_b[0, 0, 0]
    cav_mask = (ext_b[1:-1, 1:-1, 1:-1] != ext_id) & (bow_g == 0)
    bow_g[cav_mask] = RED

    lbl_b2, bow_comps = ndimage.label(bow_g > 0)
    pad_b2 = np.pad(bow_g == 0, 1, constant_values=True)
    ext_b2, _ = ndimage.label(pad_b2)
    bow_cavities = int(((ext_b2[1:-1, 1:-1, 1:-1] != ext_b2[0, 0, 0]) & (bow_g == 0)).sum())

    bow_post_hits = 0
    bow_adj_hull = 0
    bow_min_wz_by_x = {}
    for lx, ly, lz in np.argwhere(bow_g > 0):
        wx = int(math.floor(bow_ox + (lx + 0.5) * 0.5))
        wy = int(math.floor(bow_oy + (ly + 0.5) * 0.5))
        wz = int(math.floor(bow_oz + (lz + 0.5) * 0.5))
        if wx not in bow_min_wz_by_x or wz < bow_min_wz_by_x[wx]:
            bow_min_wz_by_x[wx] = wz
        xi, yi = wx - x0, wy - ylo
        if 0 <= xi < shape[0] and 0 <= yi < shape[1] and 0 <= wz < shape[2]:
            if base_occ[xi, yi, wz] or balc[xi, yi, wz] > 0:
                bow_post_hits += 1
            for dx, dy, dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
                nx_, ny_, nz_ = xi + dx, yi + dy, wz + dz
                if 0 <= nx_ < shape[0] and 0 <= ny_ < shape[1] and 0 <= nz_ < shape[2] and base_occ[nx_, ny_, nz_]:
                    bow_adj_hull += 1
                    break

    bow_side_gap_cols = 0
    for xw, zt in hull_bow_top.items():
        if xw in bow_min_wz_by_x and xw <= 454 and bow_min_wz_by_x[xw] > zt + 1:
            bow_side_gap_cols += 1

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
        'deco_bow_components_6': int(bow_comps),
        'deco_bow_cavities': bow_cavities,
        'deco_bow_mirror_diff': bow_mirror,
        'deco_bow_trimmed': bow_hits,
        'deco_bow_post_hits': bow_post_hits,
        'deco_bow_adj_hull_cells': bow_adj_hull,
        'deco_bow_side_gap_cols': bow_side_gap_cols,
        'deco_stern_cells': int((st_g > 0).sum()),
        'deco_stern_mirror_diff': st_mirror,
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
    # 疊上 bow_g, st_g（照實際 voxel floor 座標投影）
    for lx, ly, lz in np.argwhere(bow_g > 0):
        px = int(math.floor(bow_ox + (lx + 0.5) * 0.5)) - x0 + 30
        pz = H - 20 - int(math.floor(bow_oz + (lz + 0.5) * 0.5))
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
