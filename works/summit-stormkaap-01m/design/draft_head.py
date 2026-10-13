# 新圖紙 05b 船頭（TASK-0547 階段五）：plan.json 的 head ⇒ 船殼（刻掉艙壁以前、上甲板以上）＋ 艏樓甲板（刻掉艙壁以前、貼 beakhead 艙壁）
#   ＋ galjoen 子作品（knee、格柵平台、上下顎的 head rails、牙、骷髏獅子船首像、追擊砲門的大嘴）的清單、圖紙、verify_head.json。
# 用法：python -I -X utf8 -B draft_head.py <design 資料夾>
#   · 現況照 sk_state 重播到 stage5a（船尾已在）。整件左右對稱（花紋一律以中線取餘）。
#   · beakhead 艙壁：x ＝ bulkhead_x、+1 兩格厚，從上甲板板頂上一格到舷牆頂（艏樓甲板那幾格已在的不動）；兩個追擊砲門、中線一扇門。
#   · 刻：x ≥ bulkhead_x ＋ 2、z 高於上甲板板頂的船殼與艏樓甲板全刻；艏柱留到上甲板＋stem_head 格（艏柱頭）。帶原色守門。
#   · galjoen（新子作品 -head）：
#       knee（cutwater）：中線 |dy| ≤ 2，艏柱前緣往前到 x_k(z) ＝ 艏柱面 ＋ (x_tip − 艏柱面)·((z − z0)/(z1 − z0))^p。
#       格柵平台：上甲板那一層、船殼外面、|dy| ≤ w(x)；x%3、|dy|%3、邊緣是木條，其他是孔。
#       head rails（顎）：每舷上下兩條，從艙壁兩角掃到船首像；上顎的牙往下、下顎的牙往上，每 tooth_every 格一顆；中間每 post_every 格一根立柱。
#       船首像：骷髏化的獅子 —— 顱骨、口鼻、上下顎（張開）、獠牙、眼窩（發綠光）、後面一圈破爛的鬃毛。
#       追擊砲門的大嘴：開口上下沿一排牙（隔一格一顆）、外框一圈、上面兩隻發光的眼。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, font
from sk_state import state_after, read_list

NZ5 = 200


def lst(pts, col):
    if np.isscalar(col): col = np.full(len(pts), col)
    return ''.join(f"{a},{b},{c},{k}\n" for (a, b, c), k in zip(pts, col))


def pal(k):
    return (int(((k >> 5) & 7) * 255 / 7), int(((k >> 2) & 7) * 255 / 7), int((k & 3) * 255 / 3))


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    Hd = plan['head']; C = Hd['colors']
    H = Hull(plan); NX, NY, YC = H.NX, H.NY, H.YC
    W = state_after(d, 'stage5a', nz=NZ5)
    hull, bak = W['hull'], W['bak']
    occ = np.zeros(hull.shape, bool)
    for k, v in W.items(): occ |= v > 0
    xc = np.arange(NX) + 0.5
    Lup = np.floor(H.sheer(xc)).astype(int) - 1                       # 上甲板板那一格
    Lbak = np.floor(H.sheer(xc) + plan['decks']['levels']['bak']['offset']).astype(int) - 1
    xb = Hd['bulkhead_x']
    X = np.arange(NX)[:, None, None]; Y = np.arange(NY)[None, :, None]; Z = np.arange(NZ5)[None, None, :]
    DY = np.abs(Y - YC)
    LUP = Lup[:, None, None]

    # ── 刻：艙壁以前、上甲板以上 ──
    stem = np.zeros(hull.shape, bool)
    a = read_list(os.path.join(d, 'masks', 'frames', 'stem.vox.txt')); stem[tuple(a[:, :3].T)] = True
    fwd = (X >= xb + 2) & (Z > LUP)
    keep_stem = stem & (Z <= LUP + Hd['stem_head'])
    carve_hull = fwd & (hull > 0) & ~keep_stem
    carve_bak = fwd & (bak > 0)
    hull2 = hull.copy(); hull2[carve_hull] = 0
    bak2 = bak.copy(); bak2[carve_bak] = 0
    occ2 = occ & ~carve_hull & ~carve_bak

    # ── beakhead 艙壁（艏樓甲板子作品）──
    zs3 = np.arange(NZ5) + 0.5
    bulk = np.zeros(hull.shape, bool)
    for x in (xb, xb + 1):
        hbz = np.nan_to_num(H.hb(np.full(NZ5, x + 0.5), zs3), nan=-1)
        for z in range(Lup[x] + 1, int(np.floor(H.top(x + 0.5))) + 1):
            if hbz[z] < 0: continue
            bulk[x, :, z] = (np.abs(np.arange(NY) - YC) <= hbz[z])
    bulk &= ~occ2
    P = Hd['chase_ports']; Dr = Hd['door']
    openings = np.zeros(hull.shape, bool)
    port_boxes = []
    for yc in P['y']:
        z0 = int(Lup[xb]) + 1 + P['sill']; z1 = z0 + P['height'] - 1
        openings |= (X >= xb) & (X <= xb + 1) & (Y >= yc - 3) & (Y <= yc + 3) & (Z >= z0) & (Z <= z1)
        port_boxes.append((yc, z0, z1))
    dz0 = Lup[xb] + 1
    openings |= (X >= xb) & (X <= xb + 1) & (DY <= Dr['dy']) & (Z >= dz0) & (Z < dz0 + Dr['h'])
    bulk &= ~openings

    head = np.zeros(hull.shape, np.int16)
    # 追擊砲門的大嘴：開口上下沿的牙（在艙壁那兩格裡）、外框（艙壁外面一格）、上面兩隻眼
    for yc, z0, z1 in port_boxes:
        for y in range(yc - 3, yc + 4):
            if abs(y - yc) % 2 == 0 and abs(y - yc) <= 2:               # 隔一格一顆，以開口中心取餘 ⇒ 對稱
                head[xb:xb + 2, y, z1] = C['tooth']; head[xb:xb + 2, y, z0] = C['tooth']
        for y in range(yc - 4, yc + 5):
            for z in range(z0 - 1, z1 + 2):
                if yc - 3 <= y <= yc + 3 and z0 <= z <= z1: continue
                head[xb + 2, y, z] = C['rim']
        for s in (-1, 1):
            head[xb + 2, yc + s * 2, z1 + 3] = C['glow']
            head[xb + 2, yc + s * 2, z1 + 2] = C['rim']
    bulk &= head == 0

    # ── knee（cutwater）──
    K = Hd['knee']; x_tip = Hd['x_tip']
    for z in range(K['z0'], K['z1'] + 1):
        sf = float(H.stem_face(z + 0.5))
        t = (z - K['z0']) / (K['z1'] - K['z0'])
        xk = sf + (x_tip - sf) * t ** K['power']
        for x in range(int(np.floor(sf)), int(np.floor(xk)) + 1):
            for y in range(YC - 2, YC + 3):
                if not occ2[x, y, z]: head[x, y, z] = C['knee']
    for z in range(K['z1'] + 1, K['z1'] + 1 + K['top_extra']):               # knee 頂往上接船首像的下顎
        for x in range(x_tip - 8, x_tip + 1):
            for y in range(YC - 2, YC + 3):
                if not occ2[x, y, z] and head[x, y, z] == 0: head[x, y, z] = C['knee']

    # ── 格柵平台 ──
    G = Hd['grating']
    zp_of = lambda x: int(Lup[min(x, Hd['deck_x_max'])])
    for x in range(xb + 2, x_tip - G['end_back'] + 1):
        t = (x - (xb + 2)) / (x_tip - G['end_back'] - (xb + 2))
        w = G['w0'] * (1 - t ** G['power']) + G['w_tip'] * t
        zp = zp_of(x)
        hbz = float(np.nan_to_num(H.hb(x + 0.5, zp + 0.5), nan=-1))
        for y in range(YC - int(np.floor(w)), YC + int(np.floor(w)) + 1):
            dy = abs(y - YC)
            if dy <= hbz: continue                                             # 船殼裡面是上甲板
            border = dy >= int(np.floor(w)) - 0
            if x % 3 == 0 or dy % 3 == 0 or border:
                if not occ2[x, y, zp] and head[x, y, zp] == 0: head[x, y, zp] = C['grating']

    # ── head rails（上下顎）＋ 牙 ＋ 立柱 ──
    R_ = Hd['rails']
    def sweep(p0, p1, n, bend):
        out = []
        for i in range(n + 1):
            t = i / n
            x = p0[0] + (p1[0] - p0[0]) * t
            yy = p0[1] * (1 - t) ** R_['y_power'] + p1[1] * t
            z = p0[2] + (p1[2] - p0[2]) * t + bend * np.sin(np.pi * t)
            out.append((x, yy, z, t))
        return out
    x0r = xb + 2
    up_pts = sweep((x0r, R_['y0_up'], R_['z_up0']), (x_tip - R_['end_back'], R_['y_end'], R_['z_up1']), 400, R_['bend_up'])
    lo_pts = sweep((x0r, R_['y0_lo'], R_['z_lo0']), (x_tip - R_['end_back'], R_['y_end'], R_['z_lo1']), 400, R_['bend_lo'])
    rail = np.zeros(hull.shape, bool)
    for pts in (up_pts, lo_pts):
        for x, yy, z, t in pts:
            for s in (-1, 1):
                for dx_ in (0, 1):
                    for dz_ in (0, 1):
                        for dyy in (0, 1):
                            xi, zi = int(np.floor(x)) + dx_, int(np.floor(z)) + dz_
                            yi = YC + s * (int(np.floor(yy)) + dyy)
                            rail[xi, yi, zi] = True
    rail &= ~occ2
    head[rail & (head == 0)] = C['rail']
    # 牙：上顎往下、下顎往上；以 x 取餘（兩舷同一個 x ⇒ 對稱）
    def teeth(pts, direction, length):
        for x, yy, z, t in pts:
            xi = int(np.floor(x))
            if xi % R_['tooth_every'] != 0 or t < 0.06 or t > 0.94: continue
            for s in (-1, 1):
                yi = YC + s * int(np.floor(yy))
                zb_ = int(np.floor(z)) + (0 if direction < 0 else 1)
                for k in range(1, length + 1):
                    zi = zb_ + direction * k
                    ys_ = [yi] + ([yi - s] if k <= length // 2 else [])      # 根部 2 格寬（往船內那一格）、尖端 1 格
                    for yy2 in ys_:
                        if not occ2[xi, yy2, zi] and head[xi, yy2, zi] == 0: head[xi, yy2, zi] = C['tooth']
    seen = set()
    up_t = [(x, yy, z, t) for x, yy, z, t in up_pts if not (int(np.floor(x)) in seen or seen.add(int(np.floor(x))))]
    seen = set()
    lo_t = [(x, yy, z, t) for x, yy, z, t in lo_pts if not (int(np.floor(x)) in seen or seen.add(int(np.floor(x))))]
    teeth(up_t, -1, R_['tooth_up'])
    teeth(lo_t, +1, R_['tooth_lo'])
    # 立柱：上下顎之間，每 post_every 格（以 x 取餘）
    for (xu, yu, zu, tu), (xl, yl, zl, tl) in zip(up_t, lo_t):
        xi = int(np.floor(xu))
        if xi % R_['post_every'] != R_['post_every'] // 2 or tu > 0.9: continue
        for s in (-1, 1):
            yi = YC + s * int(np.floor((yu + yl) / 2))
            for zi in range(int(np.floor(zl)) + 2, int(np.floor(zu))):
                if not occ2[xi, yi, zi] and head[xi, yi, zi] == 0: head[xi, yi, zi] = C['rail']

    # ── 船首像：骷髏化的獅子 ──
    F = Hd['figure']
    fx, fz, sc = x_tip + F['dx'], F['z'], F.get('scale', 1.0)
    E = lambda x, y, z, cx, cy, cz, rx, ry, rz: ((x - cx) / (rx * sc)) ** 2 + ((y - cy) / (ry * sc)) ** 2 + ((z - cz) / (rz * sc)) ** 2 <= 1
    R0 = int(np.ceil(14 * sc))
    for x in range(fx - R0, fx + R0):
        for y in range(YC - R0, YC + R0 + 1):
            for z in range(fz - R0, fz + R0):
                dyy = y - YC
                cran = E(x, dyy, z, fx - 4 * sc, 0, fz + 3 * sc, 6.0, 5.0, 6.0)
                snout = E(x, dyy, z, fx + 3 * sc, 0, fz, 4.5, 3.5, 2.6)
                jaw = E(x, dyy, z, fx + 1 * sc, 0, fz - 5 * sc, 5.0, 3.5, 1.6)
                fy = int(round(2 * sc))
                fang_up = abs(dyy) == fy and fx + 4 * sc <= x <= fx + 5 * sc + 0.5 and fz - 4 * sc <= z <= fz - 2 * sc
                fang_lo = abs(dyy) == fy and fx + 2 * sc <= x <= fx + 3 * sc + 0.5 and fz - 4 * sc <= z <= fz - 3 * sc + 0.5
                eye = E(x, abs(dyy), z, fx + 1 * sc, 3 * sc, fz + 3 * sc, 1.6, 1.6, 1.6)
                nose = abs(dyy) <= 1 and fx + 6 * sc <= x <= fx + 7 * sc + 0.5 and fz + 1 * sc <= z <= fz + 2 * sc + 0.5
                # 鬃毛：從顱骨後半的表面往外長的放射狀鬃束（以垂直軸量角度 ⇒ 左右對稱）
                # 🩸 第一版是 x 9 格外的一圈、斜條紋花紋 ⇒ 沒碰到顱骨、被條紋切碎，291 格浮空被丟
                ex = (x - (fx - 4 * sc)) / (6.0 * sc)
                r_c = 5.5 * sc * np.sqrt(max(0.0, 1 - ex * ex)) if abs(ex) < 1 else 0.0
                r_m = np.hypot(dyy, z - (fz + 3 * sc))
                phi = abs(np.arctan2(dyy, z - (fz + 3 * sc)))
                mane = fx - 10 * sc <= x <= fx - 3 * sc and r_c - 1.0 <= r_m <= r_c + 3.5 * sc - 0.3 * (fx - 3 * sc - x) and int(phi / (np.pi / 9)) % 2 == 0
                col = 0
                if mane: col = C['mane']
                if cran or snout or jaw or fang_up or fang_lo: col = C['bone']
                if eye and (cran or snout): col = C['glow']
                if nose: col = C['dark']
                if col and not occ2[x, y, z]: head[x, y, z] = col
    # 嘴裡（口鼻與下顎之間）留空，獠牙那兩欄除外
    gz0, gz1 = int(np.floor(fz - 3 * sc)), int(np.floor(fz - 2 * sc))
    for x in range(int(fx - 2 * sc), int(fx + 8 * sc)):
        for y in range(YC - int(4 * sc), YC + int(4 * sc) + 1):
            for z in range(gz0, gz1):
                if head[x, y, z] == C['bone'] and abs(y - YC) != int(round(2 * sc)): head[x, y, z] = 0

    # 碎片：沒連到船（或船頭主體）的丟掉，照實記
    st6 = ndimage.generate_binary_structure(3, 1)
    base = occ2 | bulk
    lab_h, n_h = ndimage.label(head > 0)
    touch = ndimage.binary_dilation(base, structure=st6)
    ok_lab = set(np.unique(lab_h[(head > 0) & touch]).tolist()) - {0}
    flo = (head > 0) & ~np.isin(lab_h, list(ok_lab))
    lab_f, n_f = ndimage.label(flo)
    floating = []
    for i in range(1, n_f + 1):
        q = np.argwhere(lab_f == i)
        floating.append({'n': int(len(q)), 'min': [int(v) for v in q.min(0)], 'max': [int(v) for v in q.max(0)], 'colors': sorted(set(int(c) for c in head[tuple(q.T)]))})
    head[flo] = 0

    # ── 清單 ──
    subs = ('hull', 'bak', 'head')
    order = {s: [] for s in subs}
    for s_ in subs:
        od = os.path.join(d, 'masks', 'head', s_); os.makedirs(od, exist_ok=True)
        for f in os.listdir(od): os.remove(os.path.join(od, f))

    def emit(sub_, name, mask, col, op='stampvox', guard=None):
        pts = np.argwhere(mask)
        if len(pts) == 0: return
        text = lst(pts, guard[tuple(pts.T)]) if op == 'carvevox' else lst(pts, col[tuple(pts.T)] if not np.isscalar(col) else col)
        fn = name + '.vox.txt'
        open(os.path.join(d, 'masks', 'head', sub_, fn), 'w', encoding='utf-8', newline='\n').write(text)
        order[sub_].append({'name': name, 'op': op, 'file': 'masks/head/' + sub_ + '/' + fn, 'at': [0, 0, 0], 'expect_pixels': int(len(pts)),
                            'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()})

    emit('hull', 'bow_carve', carve_hull, None, op='carvevox', guard=hull)
    emit('bak', 'bow_carve', carve_bak, None, op='carvevox', guard=bak)
    emit('bak', 'beakhead_bulkhead', bulk, C['bulkhead'])
    emit('head', 'head', head > 0, head)

    # ── 讀數 ──
    parts = {k: v > 0 for k, v in W.items()}
    parts['hull'] = hull2 > 0; parts['bak'] = (bak2 > 0) | bulk; parts['head'] = head > 0
    ks = list(parts); pair = {}
    for i, a_ in enumerate(ks):
        for b_ in ks[i + 1:]:
            n_ = int((parts[a_] & parts[b_]).sum())
            if n_: pair[a_ + '×' + b_] = n_
    allv = np.zeros(hull.shape, bool)
    for v in parts.values(): allv |= v
    lab, ncomp = ndimage.label(allv)
    holes = int((ndimage.binary_fill_holes(allv) & ~allv).sum())
    mir = lambda a: int((a != a[:, ::-1, :]).sum())
    R = {'stamp_order': order, 'bulkhead_x': xb, 'x_tip': x_tip, 'chase_ports': [{'y': [y - 3, y + 3], 'z': [z0, z1]} for y, z0, z1 in port_boxes],
         'counts': {'hull_carve': int(carve_hull.sum()), 'bak_carve': int(carve_bak.sum()), 'bulkhead': int(bulk.sum()), 'head': int((head > 0).sum()),
                    'head_by_color': {str(k): int((head == k).sum()) for k in sorted(set(head[head > 0].tolist()))},
                    'sum_of_parts': int(sum(int(v.sum()) for v in parts.values())), 'assembly_total': int(allv.sum())},
         'floating_dropped': floating,
         'checks': {'pair_overlap_all_parts': pair, 'components_assembly': int(ncomp), 'enclosed_cavity_assembly': holes,
                    'components_head': int(ndimage.label(head > 0)[1]), 'components_bak': int(ndimage.label(parts['bak'])[1]), 'components_hull': int(ndimage.label(hull2 > 0)[1]),
                    'mirror_head': mir(head), 'mirror_bak': mir(np.where(parts['bak'], 1, 0)), 'mirror_hull': mir(hull2)}}
    with open(os.path.join(d, 'verify_head.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    draw(H, W, hull2, bak2, bulk, head, xb, os.path.join(d, 'sheet05_head_v1.png'))
    print(json.dumps({k: R[k] for k in ('bulkhead_x', 'x_tip', 'chase_ports', 'counts', 'floating_dropped', 'checks')}, ensure_ascii=False, indent=1))


def draw(H, W, hull2, bak2, bulk, head, xb, path):
    NX, NY, YC = H.NX, H.NY, H.YC
    allc = np.zeros(hull2.shape, np.int16)
    for k, v in W.items(): allc = np.where(v > 0, v, allc)
    allc = np.where(hull2 > 0, hull2, np.where(W['hull'] > 0, 0, allc))
    allc = np.where(W['bak'] > 0, bak2, allc); allc = np.where(bulk, 109, allc); allc = np.where(head > 0, head, allc)
    S = 5; W_, Hh = 1700, 900
    im = Image.new('RGB', (W_, Hh), (250, 248, 242)); g = ImageDraw.Draw(im); ink = (30, 30, 30)
    g.text((20, 12), "風暴角號 Stormkaap　新圖紙 05b　船頭（從右舷看／從船頭看）　0.1 m／格　summit 2026-10-14　（設計）", fill=ink, font=font(22))
    half = allc[:, YC:, :]
    hasv = (half > 0).any(axis=1)
    last = half.shape[1] - 1 - np.argmax(half[:, ::-1, :] > 0, axis=1)
    ox, base = 40, 860
    for x, z in np.argwhere(hasv):
        if x < 440 or z < 20 or z > 150: continue
        k = int(half[x, last[x, z], z])
        g.rectangle([ox + (x - 440) * S, base - (z - 20 + 1) * S, ox + (x - 440 + 1) * S, base - (z - 20) * S], fill=pal(k))
    g.text((ox, 50), "從右舷看（x 440–620、z 20–150）", fill=ink, font=font(18))
    sub = allc[::-1]
    has = (sub > 0).any(axis=0)
    first = np.argmax(sub > 0, axis=0)
    ox2 = 1100
    for y, z in np.argwhere(has):
        if z < 20 or z > 150 or abs(y - YC) > 55: continue
        k = int(sub[first[y, z], y, z])
        g.rectangle([ox2 + (y - YC + 55) * 5, base - (z - 20 + 1) * 5, ox2 + (y - YC + 56) * 5, base - (z - 20) * 5], fill=pal(k))
    g.text((ox2, 50), "從船頭看（z 20–150）", fill=ink, font=font(18))
    im.save(path, optimize=False)


if __name__ == '__main__':
    main()
