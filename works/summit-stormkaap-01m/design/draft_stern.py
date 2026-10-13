# 新圖紙 05a 船尾（TASK-0547 階段五）：plan.json 的 stern ⇒ 船殼（刻窗與船尾砲門、補框）＋ 船尾裝飾子作品 ＋ 側窗廊子作品（右舷一份、左舷走 mirror=y 關聯）
#   的清單、圖紙、verify_stern.json。
# 用法：python -I -X utf8 -B draft_stern.py <design 資料夾>
#   · 船殼現況照 sk_state 重播到 stage4（不讀作品匯出）；裝飾貼在**實際的格**上：艉板外面那一格 ＝ 每個 (y, z) 船殼最小的 x（x < 140 那一段）。
#   · 艉板（荷蘭 spiegel）上由下往上：砲室層兩個船尾砲門 → 大艙層五扇窗（玻璃發綠光、內縮 2 格）＋ 開放陽台（地板、欄杆、托架）→
#     頂上拱頂（往上長出舷牆）＋ Adamastor 的臉（浮雕，往船尾凸 1–4 格）→ 三盞艉燈。
#   · 側窗廊（電影「圓頂小塔」「蜂巢」）：右舷船尾，平面半橢圓（沿船長 a、往外 b），由下往上：吊墜收尖 → 兩層窗 → 圓頂（每 3 層一道環）→ 尖頂。
#   · 鏡像：側窗廊子作品框跟船殼同大，左舷那份走 mirror=y、at 0,0,0（y ↔ 260 − y，跟船殼的鏡像同一條）。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, font
from sk_state import state_after

NZ5 = 200


def lst(pts, col):
    if np.isscalar(col): col = np.full(len(pts), col)
    return ''.join(f"{a},{b},{c},{k}\n" for (a, b, c), k in zip(pts, col))


def pal(k):
    return (int(((k >> 5) & 7) * 255 / 7), int(((k >> 2) & 7) * 255 / 7), int((k & 3) * 255 / 3))


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    S = plan['stern']; C = S['colors']
    H = Hull(plan); NX, NY, YC = H.NX, H.NY, H.YC
    W = state_after(d, 'stage4', nz=NZ5)
    hull = W['hull']
    occ_all = np.zeros(hull.shape, bool)
    for k, v in W.items(): occ_all |= v > 0
    X = np.arange(NX)[:, None, None]; Y = np.arange(NY)[None, :, None]; Z = np.arange(NZ5)[None, None, :]
    DY = np.abs(Y - YC)

    # ── 艉板外面那一格：每個 (y, z)，x < 140 的船殼最小 x ──
    sub = hull[:140] > 0
    has_t = sub.any(axis=0)                                            # (NY, NZ)
    xf = np.where(has_t, np.argmax(sub, axis=0), -1)                   # 艉板外面那一格的 x
    zl = S['transom_z_min']

    def tf(y, z): return int(xf[y, z])

    deco = np.zeros(hull.shape, np.int16)        # 船尾裝飾子作品（色）
    carve = np.zeros(hull.shape, bool)
    lining = np.zeros(hull.shape, bool)

    def cut_box(y0, y1, z0, z1, depth):
        """在艉板上開口：(y, z) 方框裡，從艉板外面那一格往船裡 depth 格的船殼全刻。回傳開口 (y,z) 遮罩。"""
        m2 = np.zeros((NY, NZ5), bool); m2[y0:y1 + 1, z0:z1 + 1] = True
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                x0 = tf(y, z)
                if x0 < 0: raise ValueError('開口落在艉板外：y %d z %d' % (y, z))
                carve[x0:x0 + depth + 1, y, z] |= hull[x0:x0 + depth + 1, y, z] > 0
        return m2

    # 船尾砲門
    ports = []
    for yc in S['ports']['y']:
        z0 = S['ports']['z'][0]; z1 = S['ports']['z'][1]
        m2 = cut_box(yc - 3, yc + 3, z0, z1, S['cut_depth'])
        ports.append({'y': [yc - 3, yc + 3], 'z': [z0, z1]})
        ring = ndimage.binary_dilation(m2, iterations=1) & ~m2
        for y, z in np.argwhere(ring):
            x0 = tf(y, z)
            if x0 < 0: continue
            for x in range(x0, x0 + S['cut_depth'] + 1):
                if not occ_all[x, y, z] and not carve[x, y, z]: lining[x, y, z] = True   # 🩸 第一版只看船殼 ⇒ 窗框上沿 21 格疊在 kampanje 的橫樑上（引擎 link_overlap 抓到）
    # 大艙的窗：開口 ＋ 玻璃（內縮 glass_inset 格，船尾裝飾子作品）
    wins = []
    for yc in S['windows']['y']:
        w = S['windows']['w'] // 2
        z0, z1 = S['windows']['z']
        m2 = cut_box(yc - w, yc + w, z0, z1, S['cut_depth'])
        wins.append({'y': [yc - w, yc + w], 'z': [z0, z1]})
        for y, z in np.argwhere(m2):
            deco[tf(y, z) + S['windows']['glass_inset'], y, z] = C['glass']
        ring = ndimage.binary_dilation(m2, iterations=1) & ~m2
        for y, z in np.argwhere(ring):
            x0 = tf(y, z)
            for x in range(x0, x0 + S['cut_depth'] + 1):
                if not occ_all[x, y, z] and not carve[x, y, z]: lining[x, y, z] = True   # 🩸 第一版只看船殼 ⇒ 窗框上沿 21 格疊在 kampanje 的橫樑上（引擎 link_overlap 抓到）
    hull2 = hull.copy(); hull2[carve] = 0; hull2[lining] = C['frame']

    # ── 陽台（地板、欄杆、托架）──
    B = S['balcony']; zb = B['floor_z']
    yb0, yb1 = B['y']
    xout = {}
    for y in range(yb0, yb1 + 1):
        xa = tf(y, zb)                                  # 地板接在艉板外面那一格之外
        if xa < 0: continue
        e = min(y - yb0, yb1 - y)                       # 兩角收圓：離端點 corner 格內，往船尾伸出的深度照圓弧減
        r = B['depth']
        if e < B['corner']:
            t = (B['corner'] - e) / B['corner']
            r = int(round(B['depth'] - B['corner'] * (1 - np.sqrt(max(0.0, 1 - t * t)))))
        xout[y] = (xa - r, xa)
    rail_top = zb + B['rail_h']
    for y, (x_out, xa) in xout.items():
        deco[x_out:xa, y, zb] = C['floor']
        # 扶手：外緣那一格，沿 x 補到隔壁那排的外緣（🩸 第一版圓角處相鄰兩排差 2 格 ⇒ 兩格扶手只靠邊角相接、被當浮空丟掉）
        nb = [xout[yy][0] for yy in (y - 1, y + 1) if yy in xout]
        x_hi = max([x_out] + nb)                         # 補到隔壁外緣本身 ⇒ 兩排共用一格（補到 −1 會剛好錯開）
        deco[x_out:x_hi + 1, y, rail_top] = C['carve']
        if abs(y - YC) % B['baluster_every'] == 0:
            deco[x_out, y, zb + 1:rail_top] = C['carve']                        # 欄杆柱（外緣；以中線取餘 ⇒ 左右對稱）
        if y in (yb0, yb1):                                                     # 兩側：沿 x 一排
            deco[x_out:xa, y, rail_top] = C['carve']
            for x in range(x_out, xa):
                if (xa - x) % B['baluster_every'] == 0 or x == x_out: deco[x, y, zb + 1:rail_top] = C['carve']
    # 托架：每 bracket_every 格一副，三角（從艉板往下斜到地板外緣）
    for yk in B['brackets_y']:
        for y in (yk - 1, yk, yk + 1):                  # 3 格寬、以 yk 為中心 ⇒ 鏡像對得上
            xa = tf(y, zb)
            for k in range(B['depth']):
                zz = zb - 1 - int(round((B['depth'] - k) * B['bracket_drop'] / B['depth']))
                for z in range(zz, zb):
                    x = xa - 1 - k
                    if hull[x, y, z] == 0 and deco[x, y, z] == 0: deco[x, y, z] = C['frame']

    # ── 拱頂（往上長出舷牆）＋ Adamastor 的臉 ──
    K = S['crown']; F_ = S['face']
    zt = int(np.max(np.where(has_t.any(axis=0))[0]))                   # 艉板最高那一層
    crown_x = {}
    for y in range(YC - K['half_w'], YC + K['half_w'] + 1):
        dy = (y - YC) / K['half_w']
        ztop = zt + int(round(K['height'] * np.sqrt(max(0.0, 1 - dy * dy))))
        for z in range(zt + 1, ztop + 1):
            xc = int(np.floor(H.transom_face(z + 0.5)))                # 艉板面往上延伸
            for x in range(xc, xc + K['thick']):
                deco[x, y, z] = C['crown']
            crown_x[(y, z)] = xc
    # 臉：浮雕高度 h(y, z)（往船尾凸幾格），在艉板／拱頂的外面那一格之外
    yc_, zc_ = YC, F_['center_z']
    rel = {}
    for y in range(YC - F_['half_w'] - 3, YC + F_['half_w'] + 4):
        for z in range(zc_ - F_['half_h'] - 10, zc_ + F_['half_h'] + 1):
            u = (y - yc_) / F_['half_w']; v = (z - zc_) / F_['half_h']
            h, col = 0, None
            if u * u + v * v <= 1.0: h, col = 1, C['face']                                   # 臉的輪廓
            if abs(z - (zc_ + 3)) <= 1 and abs(y - yc_) <= F_['half_w'] - 2: h, col = 3, C['face']   # 眉
            for s in (-1, 1):                                                                 # 眼窩（發綠光）
                if (y - (yc_ + s * 4)) ** 2 + (z - (zc_ + 1)) ** 2 <= 2.3: h, col = 1, C['glow']
            if abs(y - yc_) <= 1 and zc_ - 5 <= z <= zc_ + 2: h, col = 4 if z <= zc_ - 3 else 3, C['face']   # 鼻樑
            for s in (-1, 1):                                                                 # 顴骨
                if ((y - (yc_ + s * 6)) / 2.5) ** 2 + ((z - (zc_ - 3)) / 2.0) ** 2 <= 1: h, col = 2, C['face']
            if ((y - yc_) / 3.6) ** 2 + ((z - (zc_ - 8)) / 1.8) ** 2 <= 1: h, col = 1, C['mouth']   # 張開的嘴
            # 鬍子：嘴以下往下散開的鬚，每 3 格一束
            if zc_ - 10 - F_['beard'] <= z < zc_ - 9 and abs(y - yc_) <= 4 + (zc_ - 9 - z) * 0.5 and (y - yc_) % 3 != 0:
                h, col = 2, C['beard']
            # 頭髮／風暴：眉上往外飄的鬚
            if z > zc_ + 4 and u * u + v * v <= 1.0 and (abs(y - yc_) + z) % 4 in (0, 1):   # 以中線取餘 ⇒ 左右對稱
                h, col = 2, C['beard']
            if h: rel[(y, z)] = (h, col)
    face_cells = 0
    for (y, z), (h, col) in rel.items():
        if (y, z) in crown_x: base = crown_x[(y, z)]
        elif 0 <= z < NZ5 and xf[y, z] >= 0: base = int(xf[y, z])
        else: continue
        for k in range(1, h + 1):
            x = base - k
            if hull2[x, y, z] == 0 and deco[x, y, z] == 0:
                deco[x, y, z] = col; face_cells += 1
            elif deco[x, y, z] != 0: deco[x, y, z] = col

    # ── 艉燈：中間一盞在拱頂上、兩盞在艉板兩角的舷牆上 ──
    Lt = S['lanterns']
    lanterns = []
    for spec in Lt:
        y0 = spec['y']; h = spec['size'] // 2                                 # 燈身 (2h+1)²，以 (xc, y0) 為中心 ⇒ 鏡像對得上
        if spec['on'] == 'crown':
            zbase = max(z for (yy, z) in crown_x if yy == y0) + 1
        else:
            zbase = int(np.max(np.where(occ_all[:140, y0, :].any(axis=0))[0])) + 1
        if spec['on'] == 'crown':
            # 🩸 第一版照艉板面往上延伸算 x（96）⇒ 拱頂的格在 97–99（艉板往後傾），整盞燈 370 格浮空 ⇒ 站在拱頂頂上那幾格的中間
            xc = crown_x[(y0, zbase - 1)] + K['thick'] // 2
        else:
            xc = int(np.floor(H.transom_face(zbase + 0.5))) + spec['x_off']
        for z in range(zbase, zbase + spec['post']): deco[xc, y0, z] = C['iron']           # 柱
        zb2 = zbase + spec['post']
        deco[xc - h:xc + h + 1, y0 - h:y0 + h + 1, zb2] = C['iron']                     # 底盤
        for z in range(zb2 + 1, zb2 + 1 + spec['glass_h']):                              # 玻璃＋四角柱
            deco[xc - h + 1:xc + h, y0 - h + 1:y0 + h, z] = C['glow']
            for cx_ in (xc - h, xc + h):
                for cy_ in (y0 - h, y0 + h): deco[cx_, cy_, z] = C['iron']
        zc2 = zb2 + 1 + spec['glass_h']
        for i in range(h + 1):                                                           # 錐頂
            deco[xc - h + i:xc + h + 1 - i, y0 - h + i:y0 + h + 1 - i, zc2 + i] = C['iron']
        deco[xc, y0, zc2 + h + 1:zc2 + h + 3] = C['carve']                                # 頂飾
        lanterns.append({'y': y0, 'z_base': zbase, 'top_z': zc2 + h + 2})

    # ── 側窗廊（右舷）──
    G = S['gallery']
    gal = np.zeros(hull.shape, np.int16)
    xc_g = G['x_center']
    side = np.where((hull2[:, YC:, :] > 0) | (W['half'][:, YC:, :] > 0) | (W['kamp'][:, YC:, :] > 0), 1, 0)
    ys_out = np.where(side.any(axis=1), YC + side.shape[1] - 1 - np.argmax(side[:, ::-1, :], axis=1), -1)   # (NX, NZ) 右舷最外那格
    z_body0, z_body1 = G['z_body']
    for z in range(G['z_bottom'], G['z_top'] + 1):
        if z < z_body0:
            t = (z - G['z_bottom']) / (z_body0 - G['z_bottom']); s = 0.35 + 0.65 * (t * t * (3 - 2 * t))
        elif z <= z_body1:
            s = 1.0
        else:
            t = (z - z_body1) / (G['z_top'] - z_body1); s = np.sqrt(max(0.0, 1 - t * t))
        a, b = G['a'] * s, G['b'] * s
        if a < 0.6: continue
        for x in range(int(np.floor(xc_g - a)), int(np.ceil(xc_g + a)) + 1):
            u = (x + 0.5 - xc_g) / a
            if abs(u) > 1: continue
            zz = min(z, int(G['attach_z_max']))
            y0 = ys_out[x, zz]
            if y0 < 0: continue
            vmax = b * np.sqrt(1 - u * u)
            for v in range(1, int(np.floor(vmax)) + 1):
                y = y0 + v
                if y >= NY: break
                outer = v > vmax - 1.0
                col = C['gallery']
                if z > z_body1:
                    col = C['dome'] if (z - z_body1) % 3 else C['iron']
                elif any(w0 <= z <= w1 for w0, w1 in G['window_z']) and outer:
                    col = C['glow'] if (x - int(xc_g)) % G['window_every'] not in (0,) else C['iron']
                gal[x, y, z] = col
    # 尖頂
    yo = ys_out[int(xc_g), int(G['attach_z_max'])] + int(round(G['b'] * 0.45))
    for z in range(G['z_top'] + 1, G['z_top'] + 1 + G['finial']):
        gal[int(xc_g), yo, z] = C['carve']
    gal[(hull2 > 0) | (deco > 0)] = 0
    for k, v in W.items():
        if k != 'hull': gal[v > 0] = 0

    # 碎片：每件只留跟主體連著的（照實記）
    def keep_main(a, name):
        m = a > 0
        lab, n = ndimage.label(m)
        if n <= 1: return 0
        sz = ndimage.sum(m, lab, range(1, n + 1)); big_ = int(np.argmax(sz)) + 1
        drop = m & (lab != big_); a[drop] = 0
        return int(drop.sum())
    # 裝飾是好幾塊各自貼在船殼上（陽台、拱頂、燈）⇒ 量「連到船殼的那幾塊」：沒連到船殼＋裝飾主體的才丟
    st6 = ndimage.generate_binary_structure(3, 1)
    base_occ = occ_all & ~carve
    lab_d, n_d = ndimage.label(deco > 0)
    touch = ndimage.binary_dilation(base_occ, structure=st6)
    ok_lab = set(np.unique(lab_d[(deco > 0) & touch]).tolist()) - {0}
    float_deco = (deco > 0) & ~np.isin(lab_d, list(ok_lab))
    deco_dropped = int(float_deco.sum())
    lab_f, n_f = ndimage.label(float_deco)
    dropped_pieces = []
    for i in range(1, n_f + 1):
        q = np.argwhere(lab_f == i)
        dropped_pieces.append({'n': int(len(q)), 'min': [int(v) for v in q.min(0)], 'max': [int(v) for v in q.max(0)],
                               'colors': sorted(set(int(c) for c in deco[tuple(q.T)]))})
    deco[float_deco] = 0
    gal_dropped = keep_main(gal, 'gallery')

    # ── 清單 ──
    subs = ('hull', 'stern_deco', 'gallery')
    order = {s: [] for s in subs}
    for s_ in subs:
        od = os.path.join(d, 'masks', 'stern', s_); os.makedirs(od, exist_ok=True)
        for f in os.listdir(od): os.remove(os.path.join(od, f))

    def emit(sub_, name, mask, col, op='stampvox', guard=None):
        pts = np.argwhere(mask)
        if len(pts) == 0: return
        if op == 'carvevox': text = lst(pts, guard[tuple(pts.T)])
        else: text = lst(pts, col[tuple(pts.T)] if not np.isscalar(col) else col)
        fn = name + '.vox.txt'
        open(os.path.join(d, 'masks', 'stern', sub_, fn), 'w', encoding='utf-8', newline='\n').write(text)
        order[sub_].append({'name': name, 'op': op, 'file': 'masks/stern/' + sub_ + '/' + fn, 'at': [0, 0, 0], 'expect_pixels': int(len(pts)),
                            'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()})

    emit('hull', 'windows_ports_carve', carve, None, op='carvevox', guard=hull)
    emit('hull', 'windows_ports_lining', lining, C['frame'])
    emit('stern_deco', 'stern_deco', deco > 0, deco)
    emit('gallery', 'gallery_S', gal > 0, gal)

    # ── 讀數 ──
    galP = gal[:, ::-1, :]
    allv = (hull2 > 0) | (deco > 0) | (gal > 0) | (galP > 0)
    for k, v in W.items():
        if k != 'hull': allv |= v > 0
    lab, ncomp = ndimage.label(allv)
    holes = int((ndimage.binary_fill_holes(allv) & ~allv).sum())
    others = np.zeros(hull.shape, bool)
    for k, v in W.items():
        if k != 'hull': others |= v > 0
    parts = {'hull': hull2 > 0, 'stern_deco': deco > 0, 'gallery_S': gal > 0, 'gallery_P': galP > 0}
    for k, v in W.items():
        if k != 'hull': parts[k] = v > 0
    ks = list(parts); pair_overlap = {}
    for i, a_ in enumerate(ks):
        for b_ in ks[i + 1:]:
            n_ = int((parts[a_] & parts[b_]).sum())
            if n_: pair_overlap[a_ + '×' + b_] = n_
    R = {'stamp_order': order,
         'transom_top_z': zt, 'ports': ports, 'windows': wins, 'lanterns': lanterns,
         'counts': {'hull_carve': int(carve.sum()), 'hull_lining': int(lining.sum()), 'hull_after': int((hull2 > 0).sum()),
                    'stern_deco': int((deco > 0).sum()), 'face_cells': face_cells, 'gallery_S': int((gal > 0).sum()), 'assembly_total': int(allv.sum())},
         'dropped': {'stern_deco_floating': deco_dropped, 'stern_deco_floating_pieces': dropped_pieces, 'gallery_fragments': gal_dropped},
         'checks': {'pair_overlap_all_parts': pair_overlap, 'sum_of_parts': int(sum(int(v.sum()) for v in parts.values())), 'overlap_deco_hull': int(((deco > 0) & (hull2 > 0)).sum()), 'overlap_deco_others': int(((deco > 0) & others).sum()),
                    'overlap_gallery_any': int(((gal > 0) & ((hull2 > 0) | (deco > 0) | others)).sum()),
                    'overlap_gallery_mirror': int(((gal > 0) & (galP > 0)).sum()),
                    'components_assembly': int(ncomp), 'enclosed_cavity_assembly': holes,
                    'components_stern_deco': int(ndimage.label(deco > 0)[1]), 'components_gallery': int(ndimage.label(gal > 0)[1]),
                    'mirror_stern_deco': int((deco != deco[:, ::-1, :]).sum()), 'mirror_hull': int((hull2 != hull2[:, ::-1, :]).sum())}}
    with open(os.path.join(d, 'verify_stern.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    draw(H, hull2, deco, gal, W, os.path.join(d, 'sheet05_stern_v1.png'))
    print(json.dumps({k: R[k] for k in ('transom_top_z', 'lanterns', 'counts', 'dropped', 'checks')}, ensure_ascii=False, indent=1))


def draw(H, hull2, deco, gal, W, path):
    NX, NY, YC = H.NX, H.NY, H.YC
    allc = hull2.copy()
    for k, v in W.items():
        if k != 'hull': allc = np.where(v > 0, v, allc)
    allc = np.where(gal > 0, gal, allc); allc = np.where(gal[:, ::-1, :] > 0, gal[:, ::-1, :], allc); allc = np.where(deco > 0, deco, allc)
    S = 5; W_, Hh = 1700, 1150
    im = Image.new('RGB', (W_, Hh), (250, 248, 242)); g = ImageDraw.Draw(im); ink = (30, 30, 30)
    g.text((20, 12), "風暴角號 Stormkaap　新圖紙 05a　船尾（從船尾看／從右舷看）　0.1 m／格　summit 2026-10-14　（設計）", fill=ink, font=font(22))
    # 從船尾看（x 由小到大，取第一格）
    sub = allc[:200]
    has = (sub > 0).any(axis=0)
    first = np.argmax(sub > 0, axis=0)
    ox, base = 40, 1100
    for y, z in np.argwhere(has):
        if z < 60: continue
        k = int(sub[first[y, z], y, z])
        g.rectangle([ox + (y - 60) * S, base - (z - 60 + 1) * S, ox + (y - 60 + 1) * S, base - (z - 60) * S], fill=pal(k))
    g.text((ox, 50), "從船尾看（z 60 以上）", fill=ink, font=font(18))
    # 從右舷看（只畫 x < 220）
    half = allc[:220, YC:, :]
    hasv = (half > 0).any(axis=1)
    last = half.shape[1] - 1 - np.argmax(half[:, ::-1, :] > 0, axis=1)
    ox2 = 800
    for x, z in np.argwhere(hasv):
        if z < 60: continue
        k = int(half[x, last[x, z], z])
        g.rectangle([ox2 + (x - 60) * 4, base - (z - 60 + 1) * 4, ox2 + (x - 60 + 1) * 4, base - (z - 60) * 4], fill=pal(k))
    g.text((ox2, 50), "從右舷看（x 60–220、z 60 以上）", fill=ink, font=font(18))
    im.save(path, optimize=False)


if __name__ == '__main__':
    main()
