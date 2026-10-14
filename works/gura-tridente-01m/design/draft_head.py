# 三叉戟號 階段五（TASK-0558）船頭：knee of the head＋格柵平台（中線一件）、cheeks／trailboard 三叉戟／hawse／head rails／cathead（右舷一件，左舷 mirror=y）、船首像（鯊）、錨（關聯憲法號 -anchor）
#   輸入：plan.json（head）＋「階段五之前」的組裝件（deco_base.base_grid）＋ 憲法號 -anchor（匯出量吊環那一格）
#   輸出：masks/head/{knee,side,figurehead}.vox.txt（各子作品自己的座標）、head_placement.json（框、關聯 at、knee 的 bobstay 固定點、錨的 at）、
#         verify_head.json、sheet06_head_v1.png
#   用法：python -I -X utf8 draft_head.py <design> [--base=<快取.npy>]
import sys, os, json, math
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import deco_base as DB
from draft_lines import font, palette_rgb

YC = 200
ANCHOR = 'basecamp-frigate-constitution-01m-anchor'


def trident_bitmap():
    """knee 上半那塊（上 cheek 與格柵之間）的三叉戟：{(s, t)}，s 0..35 往船頭、t −5..5 往上。"""
    c = set()
    for s in range(0, 29):
        c.add((s, 0))                                                 # 柄
    for t in (-1, 0, 1):
        c |= {(0, t), (1, t), (6, t)}                                 # 柄尾、一道箍
    for s in (25, 26):
        for t in range(-4, 5):
            c.add((s, t))                                             # 橫樑
    for sg in (1, -1):
        for s in range(25, 33):
            c.add((s, 4 * sg))                                        # 兩側齒
        for s in (30, 31):
            for t in (3, 4, 5):
                c.add((s, t * sg))                                    # 齒頭
    for s in range(25, 36):
        c.add((s, 0))                                                 # 中齒
    for t in range(-2, 3):
        c.add((31, t))
    for t in (-1, 0, 1):
        c |= {(32, t), (33, t)}
    return c


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    cache = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--base=')), None)
    plan = HL.load_plan(design)
    HD = plan['head']
    C = HD['colors']
    BLACK, COPPER, GOLD, RED = C['black'], C['copper'], C['gold'], C['red']
    G = np.load(cache) if cache and os.path.exists(cache) else DB.base_grid()
    S = G > 0
    NZ = G.shape[2]
    sub = S[600:900]
    BX = np.where(sub.any(0), 600 + sub.shape[0] - 1 - sub[::-1].argmax(0), -1)    # [y, z]：最前面那格實心的 x

    # ── knee of the head（中線，|dy| ≤ 3）──
    KN = HD['knee']
    z0, z1 = KN['z0'], KN['z1']

    def xk(z):
        return BX[YC, z] + KN['length'] * max(0.0, (z - z0) / float(z1 - z0)) ** KN['pow']

    x_stem = int(BX[YC, KN['top_stem']])
    x_front = xk(z1)

    def z_top(x):
        t = min(1.0, max(0.0, (x - x_stem) / (x_front - x_stem)))
        return KN['top_stem'] + (KN['top_front'] - KN['top_stem']) * t ** KN['top_pow']

    def z_cw(x):
        """cutwater 前緣在 x 那裡的高度（xk(z) ≥ x 的最低 z）；x 在艏柱後面 ⇒ −∞。"""
        for z in range(z0, KN['top_front'] + 1):
            if xk(z) >= x:
                return z
        return 10 ** 6

    knee = {}
    for z in range(z0, int(KN['top_front']) + 1):
        xf = int(math.floor(xk(z)))
        for dy in range(-3, 4):
            y = YC + dy
            for x in range(max(BX[y, z], BX[YC, z] - 2) + 1, xf + 1):
                if z > z_top(x) + 1e-9:
                    continue
                d = xk(z) - x
                h = KN['half'][0] if d >= KN['taper_at'][0] else KN['half'][1] if d >= KN['taper_at'][1] else KN['half'][2]
                if abs(dy) > h or S[x, y, z]:
                    continue
                knee[(x, y, z)] = COPPER if z <= KN['copper_to'] else BLACK
    bob = {}
    for zb in HD['bobstay_z']:
        xs = [k[0] for k in knee if k[1] == YC and k[2] == zb]
        bob['bobstay-%d' % (len(bob) + 1)] = [max(xs), YC, zb]

    # ── 平台（格柵）：knee 上緣那兩格、兩道 rail 之間、船殼外面 ──
    RA = HD['rails']

    def dyr(x):
        t = min(1.0, max(0.0, (RA['x_to'] - x) / float(RA['x_to'] - RA['x_from'])))
        return RA['dy_to'] + (RA['dy_from'] - RA['dy_to']) * t ** RA['dy_pow']

    def z_p(x):
        return int(round(z_top(max(x, x_stem))))

    PF = HD['platform']
    plat = {}
    for x in range(PF['x_from'], PF['x_to'] + 1):
        lim = int(math.floor(dyr(x))) - 1
        for dy in range(-lim, lim + 1):
            y = YC + dy
            for z in (z_p(x) - 1, z_p(x)):
                if x <= BX[y, z] or S[x, y, z] or (x, y, z) in knee:
                    continue
                plat[(x, y, z)] = PF['colors'][(x + y) % 2]

    # ── 船首像：躍出的藍鯊 ──
    FH = HD['figurehead']
    ox, oz = FH['origin']
    th = math.radians(FH['lean'])
    ux, uz = math.cos(th), math.sin(th)
    wx, wz = -math.sin(th), math.cos(th)

    def rad(u):
        if u >= 2:
            q = (u - 2) / 12.0
            return 6.0 * math.sqrt(max(0.0, 1 - q * q))
        if u >= -16:
            return 1.5 + 4.5 * ((u + 16) / 18.0) ** 0.8
        return 0.0

    def in_tri(p, a, b, c):
        def cross(o, p1, p2):
            return (p1[0] - o[0]) * (p2[1] - o[1]) - (p1[1] - o[1]) * (p2[0] - o[0])
        d1, d2, d3 = cross(a, b, p), cross(b, c, p), cross(c, a, p)
        neg = d1 < 0 or d2 < 0 or d3 < 0
        pos = d1 > 0 or d2 > 0 or d3 > 0
        return not (neg and pos)

    sc = FH['scale']
    fig = {}
    for x in range(int(ox) - 40, int(ox) + 30):
        for z in range(int(oz) - 25, int(oz) + 30):
            px, pz = x + 0.5 - ox, z + 0.5 - oz
            u = (px * ux + pz * uz) / sc
            w = (px * wx + pz * wz) / sc
            for dy in range(-17, 18):
                v = dy / sc
                r = rad(u)
                col = None
                if r > 0 and (v / (0.85 * r)) ** 2 + (w / r) ** 2 <= 1.0:            # 身體
                    nr = math.sqrt((v / (0.85 * r)) ** 2 + (w / r) ** 2)
                    col = C['shark'] if w > -0.25 * r else C['belly']
                    if 5.5 <= u <= 12.5 and nr > 0.72 and -0.42 * r <= w <= -0.12 * r:   # 嘴：一道黑縫、上緣一排白牙
                        col = BLACK
                    if 5.5 <= u <= 12.5 and nr > 0.72 and -0.12 * r < w <= 0.02 * r and int(math.floor(u)) % 2 == 0:
                        col = C['belly']
                    for sg in (1, -1):                                                # 眼
                        ev = (u - 9.0, v - sg * 0.85 * rad(9.0) * 0.75, w - 0.3 * rad(9.0))
                        if nr > 0.7 and ev[0] ** 2 + ev[1] ** 2 + ev[2] ** 2 <= 1.6:
                            col = BLACK if ev[2] < 0.6 else C['belly']
                elif abs(v) <= 0.5 and in_tri((u, w), (-5.0, rad(-5.0) - 0.5), (4.0, rad(4.0) - 0.5), (-9.0, rad(-5.0) + 8.5)):   # 背鰭
                    col = C['shark']
                elif abs(v) <= 0.5 and (in_tri((u, w), (-14.0, 1.2), (-15.5, -0.8), (-25.0, 9.5)) or in_tri((u, w), (-14.0, 0.8), (-15.5, -1.0), (-22.0, -7.0))):   # 尾鰭
                    col = C['shark']
                else:                                                                 # 胸鰭（兩片，往外下後方）
                    for sg in (1, -1):
                        a = (6.0, sg * 0.8 * rad(6.0), -0.35 * rad(6.0))
                        b = (1.0, sg * 0.8 * rad(1.0), -0.35 * rad(1.0))
                        c = (-3.5, sg * 12.0, -6.0)
                        n = np.cross(np.subtract(b, a), np.subtract(c, a))
                        n = n / np.linalg.norm(n)
                        p = (u, v, w)
                        if abs(np.dot(np.subtract(p, a), n)) <= 0.55:
                            e1, e2 = np.subtract(b, a), np.subtract(c, a)
                            q = np.subtract(p, a)
                            d00, d01, d11 = np.dot(e1, e1), np.dot(e1, e2), np.dot(e2, e2)
                            d20, d21 = np.dot(q, e1), np.dot(q, e2)
                            den = d00 * d11 - d01 * d01
                            bv = (d11 * d20 - d01 * d21) / den
                            bw = (d00 * d21 - d01 * d20) / den
                            if bv >= -0.02 and bw >= -0.02 and bv + bw <= 1.02:
                                col = C['shark']
                if col is None:
                    continue
                y = YC + dy
                if S[x, y, z] or (x, y, z) in knee or (x, y, z) in plat:
                    continue
                fig[(x, y, z)] = col

    # 船首像只靠斜角接上的零碎格（鰭尖）⇒ 拿掉、照實記
    Uf = S[700:840, 160:241, 120:230].copy()
    Ub_ = Uf.copy()
    for (x, y, z) in list(knee) + list(plat) + list(fig):
        Uf[x - 700, y - 160, z - 120] = True
    labf, _ = ndimage.label(Uf)
    keep = set(np.unique(labf[Ub_]).tolist()) - {0}
    fig_pruned = [k for k in fig if labf[k[0] - 700, k[1] - 160, k[2] - 120] not in keep]
    for k in fig_pruned:
        del fig[k]

    # ── 現況＋中線三件 ⇒ 右舷貼表面的殼（空格、同一層 ±x／±y 貼著實心）──
    U0 = S.copy()
    for d in (knee, plat, fig):
        for (x, y, z) in d:
            U0[x, y, z] = True
    bx0, bx1, by0, by1, bz0, bz1 = 680, 830, YC + 1, YC + 70, 80, 215
    Ub = U0[bx0 - 1:bx1 + 1, by0 - 1:by1 + 1, bz0:bz1]
    nb = np.zeros_like(Ub)
    nb[1:, :, :] |= Ub[:-1]; nb[:-1, :, :] |= Ub[1:]
    nb[:, 1:, :] |= Ub[:, :-1]; nb[:, :-1, :] |= Ub[:, 1:]
    shell_arr = nb & ~Ub
    shell = set()
    for (i, j, k) in np.argwhere(shell_arr[1:-1, 1:-1, :]):
        x, y, z = i + bx0, j + by0, k + bz0
        if x > math.floor(xk(z)) and y - YC <= 3 and z <= KN['top_front']:
            continue                                                    # cutwater 正前方那幾格（不往前面包）
        shell.add((x, y, z))

    side = {}
    skipped = {'side': 0}

    def put(x, y, z, c, need_shell=False):
        if y <= YC:
            return False
        if U0[x, y, z] or (need_shell and (x, y, z) not in shell):
            skipped['side'] += 1
            return False
        side[(x, y, z)] = c
        return True

    # cheeks
    CH = HD['cheeks']

    def zc_u(x):
        t = max(0.0, (x - CH['x_from']) / float(CH['x_span']))
        a, b, p = CH['upper']
        return a + b * t ** p

    def zc_l(x):
        t = max(0.0, (x - CH['x_from']) / float(CH['x_span']))
        a, b, p = CH['lower']
        return max(a + b * t ** p, (z_cw(x) + 4) if x > x_stem else -1)

    cheek_end = None
    for x in range(CH['x_from'], int(x_front) + 1):
        zu, zl = int(round(zc_u(x))), int(round(zc_l(x)))
        if zu >= z_top(x) - 2 or zl >= zu - 3:
            cheek_end = x
            break
        for z in (zu, zu + 1, zl - 1, zl):
            for (sx, sy, sz) in [k for k in shell if k[0] == x and k[2] == z]:
                put(sx, sy, sz, GOLD, True)
    # knee 上半（上 cheek 與格柵之間）：三叉戟水平放（不跟著斜的 trailboard 剪切 —— v1 剪切後側面看像一團金線）
    TB = HD['trailboard']
    tri_miss = 0
    for (s_, t) in sorted(trident_bitmap()):
        x, z = TB['trident_x'] + s_, TB['trident_z'] + t
        cand = [k for k in shell if k[0] == x and k[2] == z and k[1] - YC <= 4]
        if not cand:
            tri_miss += 1
            continue
        for k in cand:
            if k not in side:
                put(*k, GOLD, True)
    # trailboard（兩道 cheek 之間）：一道金色波浪
    wave = 0
    prev = None
    for x in range(TB['x_from'], (cheek_end or int(x_front)) - 1):
        zm = (zc_u(x) + zc_l(x)) / 2.0
        z = int(round(zm + TB['wave_amp'] * math.sin(2 * math.pi * (x - TB['x_from']) / TB['wave_len'])))
        zs = range(min(z, prev), max(z, prev) + 1) if prev is not None else [z]
        prev = z
        for zz in zs:
            for k in [k for k in shell if k[0] == x and k[2] == zz and k[1] - YC <= 4]:
                if k not in side:
                    wave += put(*k, GOLD, True)
    # hawse
    HW = HD['hawse']
    hawse = []
    for dyh in HW['dy']:
        y = YC + dyh
        z = HW['z']
        xh = max(k[0] for k in shell if k[1] == y and k[2] == z)
        hawse.append([xh, y, z])
        for k in list(shell):
            d = math.sqrt((k[0] - xh) ** 2 + (k[1] - y) ** 2 + (k[2] - z) ** 2)
            if d <= HW['r'] and k not in side:
                put(*k, BLACK if d <= HW['hole'] else GOLD, True)
    # head rails（main rail＋紅板、upper rail、立柱）
    rails = 0
    for x in range(RA['x_from'], RA['x_to'] + 1):
        d0 = int(round(dyr(x)))
        d1 = int(round(dyr(x - 1))) if x > RA['x_from'] else d0
        dys = range(min(d0, d1), max(d0, d1) + 1)
        zp = z_p(x)
        t = (RA['x_to'] - x) / float(RA['x_to'] - RA['x_from'])
        zm = zp + RA['main_above']
        zu = zp + RA['upper_above'] + int(round(RA['upper_rise'] * t ** RA['upper_pow']))
        for dy in dys:
            y = YC + dy
            for z in range(zp, zm - 1):                                    # 紅板從平台面那一格起（跟平台邊緣同一層相鄰 ⇒ 接得上）
                rails += put(x, y, z, RED)
            for z in (zm - 1, zm, zu - 1, zu):
                rails += put(x, y, z, GOLD)
            if (RA['x_to'] - x) % RA['post_every'] == 0:
                for z in range(zm + 1, zu - 1):
                    rails += put(x, y, z, BLACK)
    # cathead
    CT = HD['cathead']
    az, el = math.radians(CT['angle']), math.radians(CT['rise'])
    u = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    v = np.array([-math.sin(az), math.cos(az), 0.0])
    w = np.cross(u, v)
    ys = np.nonzero(S[CT['x'], YC:, CT['z']])[0]
    p0 = np.array([CT['x'] + 0.5, YC + ys.max() + 0.5, CT['z'] + 0.5])
    L = CT['length']
    hf = CT['half'] + 0.5
    cat = 0
    for x in range(int(p0[0]) - 6, int(p0[0] + L * u[0]) + 6):
        for y in range(int(p0[1]) - 6, int(p0[1] + L * u[1]) + 6):
            for z in range(int(p0[2]) - 6, int(p0[2] + L * u[2]) + 6):
                q = np.array([x + 0.5, y + 0.5, z + 0.5]) - p0
                s = float(q @ u)
                if s < -4 or s > L or abs(float(q @ v)) > hf or abs(float(q @ w)) > hf:
                    continue
                if not U0[x, y, z]:
                    cat += put(x, y, z, GOLD if s > L - 1.2 else BLACK)
    p_end = p0 + L * u

    # ── 檢查：彼此不重疊、左舷鏡過去不撞、連通、空腔、對稱 ──
    parts = {'knee': {**knee, **plat}, 'figurehead': fig, 'side': side}
    allc = {}
    for nm, p in parts.items():
        for k in p:
            assert k not in allc, ('部件彼此重疊', nm, k)
            allc[k] = p[k]
    sideP = {(x, 2 * YC - y, z): c for (x, y, z), c in side.items()}
    over_P = sum(1 for k in sideP if S[k] or k in allc)
    # 錨：吊環頂（憲法號 -anchor 最上面那幾格的中間）放在 cathead 端正下方；兩舷都不撞（現況＋本階段全部）
    A = DB.export_list(ANCHOR, None)
    top = A[A[:, 2] == A[:, 2].max()]
    ring = (int(round(top[:, 0].mean())), int(round(top[:, 1].mean())), int(A[:, 2].max()))
    asize = DB.work_size(ANCHOR)                                     # 錨作品的框（關聯翻面在這個框裡翻）
    occ = set(allc) | set(sideP)

    def anchor_cells(at, mirror):
        ax, ay, az = at
        out = []
        for x, y, z, c in A.tolist():
            yy = (asize[1] - 1 - y) if mirror else y
            out.append((ax + x, ay + yy, az + z))
        return out

    best = None
    ex, ey, ez = int(math.floor(p_end[0])), int(math.floor(p_end[1])), int(math.floor(p_end[2]))
    for ddz in range(0, 8):
        for ddx in (0, -1, 1, -2, 2):
            for ddy in (0, 1, -1, 2):
                at = (ex + ddx - ring[0], ey + ddy - ring[1], ez - CT['half'] - 1 - ddz - ring[2])
                cs = anchor_cells(at, False)
                if any(S[c] or c in occ for c in cs):
                    continue
                atP = (at[0], DB.mirror_at_y(at[1], asize[1]), at[2])
                csP = anchor_cells(atP, True)
                if any(S[c] or c in occ for c in csP):
                    continue
                best = {'S': list(at), 'P': list(atP), 'offset': [ddx, ddy, ddz], 'ring_world': [at[0] + ring[0], at[1] + ring[1], at[2] + ring[2]]}
                break
            if best:
                break
        if best:
            break
    anchor_occ = set()
    if best:
        anchor_occ = set(anchor_cells(best['S'], False)) | set(anchor_cells(best['P'], True))

    lo = np.array([600, 110, 0])
    hi = np.array([840, 291, 230])
    Uc = S[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]].copy()
    Ubase = Uc.copy()
    for (x, y, z) in list(allc) + list(sideP):
        Uc[x - lo[0], y - lo[1], z - lo[2]] = True
    lab, _ = ndimage.label(Uc)
    base_labels = set(np.unique(lab[Ubase]).tolist()) - {0}
    floating = {nm: sum(1 for (x, y, z) in p if lab[x - lo[0], y - lo[1], z - lo[2]] not in base_labels) for nm, p in list(parts.items()) + [('side_P', sideP)]}
    holes = int((ndimage.binary_fill_holes(Uc) & ~Uc).sum())
    asym = {nm: sum(1 for (x, y, z) in p if (x, 2 * YC - y, z) not in p or p[(x, 2 * YC - y, z)] != p[(x, y, z)]) for nm, p in (('knee', parts['knee']), ('figurehead', fig))}
    R = {'cells': {k: len(v) for k, v in parts.items()}, 'figurehead_pruned': len(fig_pruned), 'knee_only': len(knee), 'platform': len(plat), 'rails': rails, 'cathead': cat,
         'skipped_side': skipped['side'], 'trident_miss': tri_miss, 'wave': wave, 'side_P_overlap': over_P, 'floating': floating, 'cavities': holes, 'asym': asym,
         'x_stem': x_stem, 'x_front': round(x_front, 2), 'cheek_end_x': cheek_end, 'hawse': hawse, 'cathead_end': [round(float(v), 2) for v in p_end],
         'anchor': best, 'anchor_ring_local': ring, 'bobstay': bob}
    # ── 清單 ──
    out = os.path.join(design, 'masks', 'head')
    heads = {'knee': '# 三叉戟號 船頭 knee of the head＋格柵平台（子作品座標）\n', 'side': '# 三叉戟號 船頭裝飾 右舷：cheeks、trailboard 三叉戟、hawse、head rails、cathead（子作品座標；左舷 ＝ mirror=y 關聯）\n',
             'figurehead': '# 三叉戟號 船首像：藍鯊（子作品座標）\n'}
    place, lists = {}, {}
    for nm, p in parts.items():
        org, size = DB.bbox(p)
        n, h = DB.write_local(os.path.join(out, nm + '.vox.txt'), p, org, heads[nm])
        place[nm] = {'at': org, 'size': size}
        lists[nm] = [n, h]
    place['side']['at_mirror'] = [place['side']['at'][0], DB.mirror_at_y(place['side']['at'][1], place['side']['size'][1]), place['side']['at'][2]]
    o = place['knee']['at']
    place['knee']['anchors'] = {k: [v[0] - o[0], v[1] - o[1], v[2] - o[2]] for k, v in bob.items()}
    place['anchor'] = {'work': ANCHOR, 'size': list(asize), **(best or {})}
    R['lists'] = lists
    R['placement'] = place
    with open(os.path.join(design, 'head_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(place, f, ensure_ascii=False, indent=1, default=int)
    # ── 圖紙：右舷側面、正面（從船頭看）──
    full = dict(allc)
    full.update(sideP)
    for k in anchor_occ:
        full.setdefault(k, 146)
    X0, X1, Z0, Z1, Y0, Y1 = 640, 830, 0, 222, 130, 271
    sc = 3
    E = np.zeros((X1 - X0, Y1 - Y0, Z1 - Z0), np.uint8)
    E[:] = G[X0:X1, Y0:Y1, Z0:Z1]
    for (x, y, z), c in full.items():
        if X0 <= x < X1 and Y0 <= y < Y1 and Z0 <= z < Z1:
            E[x - X0, y - Y0, z - Z0] = c
    Wp = (X1 - X0) * sc + (Y1 - Y0) * sc + 120
    Hp = (Z1 - Z0) * sc + 140
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((30, 12), '三叉戟號 新圖紙 06：船頭 —— knee、格柵、cheeks、trailboard 三叉戟、hawse、head rails、cathead、船首像（鯊）、錨　v1', fill=(0, 0, 0), font=font(20))
    oy = 60
    for xi in range(X1 - X0):
        for zi in range(Z1 - Z0):
            ysx = np.nonzero(E[xi, :, zi])[0]
            if len(ysx):
                X, Y = 30 + xi * sc, oy + (Z1 - Z0 - 1 - zi) * sc
                d.rectangle([X, Y, X + sc - 1, Y + sc - 1], fill=palette_rgb(int(E[xi, ysx[-1], zi])))
    ox2 = 30 + (X1 - X0) * sc + 60
    for yi in range(Y1 - Y0):
        for zi in range(Z1 - Z0):
            xsx = np.nonzero(E[:, yi, zi])[0]
            if len(xsx):
                X, Y = ox2 + yi * sc, oy + (Z1 - Z0 - 1 - zi) * sc
                d.rectangle([X, Y, X + sc - 1, Y + sc - 1], fill=palette_rgb(int(E[xsx[-1], yi, zi])))
    d.text((30, oy + (Z1 - Z0) * sc + 10), '左：右舷側面 x %d–%d（船頭在右）；右：從船頭看（觀者左手 = +y = 右舷 S）；錨 = 灰' % (X0, X1), fill=(40, 40, 40), font=font(16))
    d.text((30, oy + (Z1 - Z0) * sc + 36), 'knee %d、平台 %d、一舷 %d、船首像 %d；浮空 %d；空腔 %d；左舷鏡過去撞到 %d；錨 %s' % (
        len(knee), len(plat), len(side), len(fig), sum(floating.values()), holes, over_P, '找到' if best else '✗ 找不到不撞的位置'), fill=(0, 0, 0), font=font(16))
    im.save(os.path.join(design, 'sheet06_head_v1.png'))
    with open(os.path.join(design, 'verify_head.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=int)
    print(json.dumps({k: R[k] for k in ('cells', 'figurehead_pruned', 'knee_only', 'platform', 'rails', 'cathead', 'skipped_side', 'trident_miss', 'wave', 'side_P_overlap', 'floating', 'cavities', 'asym', 'cheek_end_x', 'hawse', 'anchor', 'bobstay')}, ensure_ascii=False, default=int))


if __name__ == '__main__':
    main()
