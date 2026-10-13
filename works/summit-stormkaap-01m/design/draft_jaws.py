# 新圖紙 05c 船頭的大嘴（TASK-0547 階段五 c；Tim 2026-10-14：「可以嘗試復刻艦艏那像獠牙一樣的部分嗎」＋兩張電影劇照，只看不收）：
#   plan.json 的 jaws ⇒ 船頭子作品（-head）先整件刻掉階段五 b 的 head rails、格柵、骷髏獅子，再貼上下顎、獠牙、勾角、knee、喉嚨 —— 清單、圖紙、verify_jaws.json。
# 用法：python -I -X utf8 -B draft_jaws.py <design 資料夾>
#   · 現況照 sk_state 重播到 stage5b。整件左右對稱（花紋、牙的長短只看 x ⇒ 兩舷同一顆）。
#   · 上顎：x 從艙壁前一格（bulkhead_x ＋ 2）到 x_tip；平面半寬 w_u(x) ＝ W0·(1 − t^p)^q（圓頭長吻）；上緣 z_top、牙齦 z_gum 從後往前線性降。
#   · 下顎：到 x_tip − lo_short；牙齦 z_gum_l、厚 lo_thick；只放在船殼外面（船頭裡面那一段是船殼）。
#   · knee：中線 5 格寬，從艏柱前緣往前到下顎底（冪次曲線，下段貼著艏柱）。
#   · 嘴角（cheek）：艙壁前 cheek_len 格內，兩舷外側把上下顎接起來 ⇒ 嘴是從前面張開的。
#   · 牙：上顎沿外緣、每 tooth_every 格一顆往下垂；下顎錯開半格往上長；長短照 x 的雜湊（決定論）；根部 2 格寬、尖端 1 格、後半截往嘴裡彎一格。
#   · 牙齦一圈 gum 色、口腔（上顎底面、下顎頂面、外緣以內）與喉嚨（艙壁前那一格）塗暗色；追擊砲門與門的開口留空。
#   · 勾角：上顎尖端往前再往上勾（電影劇照第二張）。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib, math
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


def hsh(x, salt):
    """決定論的 0..1（只看 x ⇒ 兩舷同一顆牙）。"""
    v = math.sin(x * 12.9898 + salt * 78.233) * 43758.5453
    return v - math.floor(v)


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    J = plan['jaws']; C = J['colors']; Hd = plan['head']
    H = Hull(plan); NX, NY, YC = H.NX, H.NY, H.YC
    W = state_after(d, 'stage5b', nz=NZ5)
    old_head = W['head']
    occ = np.zeros(old_head.shape, bool)
    for k, v in W.items():
        if k != 'head': occ |= v > 0
    x0 = Hd['bulkhead_x'] + 2
    xt = J['x_tip']; xl = xt - J['lo_short']
    lerp = lambda a, b, t: a + (b - a) * t
    new = np.zeros(old_head.shape, np.int16)

    def inside_hull(x, y, z):
        h = float(H.hb(x + 0.5, z + 0.5))
        return not math.isnan(h) and abs(y - YC) <= h and z <= H.sheer(x + 0.5)          # 上甲板以下的船殼體積（船艙）

    def put(x, y, z, c, over=False, outside=False):
        if 0 <= x < NX and 0 <= y < NY and 0 <= z < NZ5 and not occ[x, y, z] and (over or new[x, y, z] == 0):
            if outside and inside_hull(x, y, z): return
            new[x, y, z] = c

    def w_of(x, xa, xb, W0):
        t = min(max((x - xa) / (xb - xa), 0.0), 1.0)
        return W0 * (1 - t ** J['plan_p']) ** J['plan_q']

    U, L = J['upper'], J['lower']
    zu_top = lambda x: lerp(U['top0'], U['top1'], (x - x0) / (xt - x0)) + U['hump'] * math.sin(math.pi * min(max((x - x0) / (xt - x0), 0), 1))
    zu_gum = lambda x: lerp(U['gum0'], U['gum1'], (x - x0) / (xt - x0))
    zl_gum = lambda x: lerp(L['gum0'], L['gum1'], (x - x0) / (xl - x0))
    # ── 上顎：空心骨架 —— 口腔頂（底下 2 層）與兩側外緣實心，上面只留橫肋（x%rib）與中脊；內部從肋縫通到外面 ⇒ 不封閉
    # 🩸 第一版整塊實心：船頭多 51,749 格（遊戲每格 0.7 kg ≈ 36 噸掛在船頭），而且劇照的上顎本來就像一具骨骸
    Rb = J['rib_every']
    for x in range(x0, xt + 1):
        w = w_of(x, x0, xt, J['W0'])
        if w < 0.5: continue
        wi = int(w); zg, zt_ = int(round(zu_gum(x))), int(round(zu_top(x)))
        for y in range(YC - wi, YC + wi + 1):
            dy = abs(y - YC); rim = dy >= wi - 1; wall = dy >= wi - J['wall']
            for z in range(zg, zt_ + 1):
                palate = z <= zg + 1
                top = z >= zt_ - 1
                if palate: c = (C['gum'] if rim else C['mouth']) if z == zg else C['skin']
                elif wall: c = C['skin_dark'] if (z - zg) % 3 == 0 else C['skin']
                elif top and (x % Rb == 0 or dy <= 1): c = C['skin_dark'] if dy <= 1 else C['skin']
                elif wi <= J['wall'] + 1: c = C['skin']                       # 尖端太窄 ⇒ 實心
                else: continue
                put(x, y, z, c)
    # ── 下顎：牙齦面（上面 2 層）與兩側外緣實心，底下只留橫肋與中脊 ──
    for x in range(x0, xl + 1):
        w = w_of(x, x0, xl, J['W0'] - 1)
        if w < 0.5: continue
        wi = int(w); zg = int(round(zl_gum(x))); zb_ = zg - L['thick'] + 1
        for y in range(YC - wi, YC + wi + 1):
            dy = abs(y - YC); rim = dy >= wi - 1; wall = dy >= wi - J['wall']
            for z in range(zb_, zg + 1):
                gumz = z >= zg - 1
                bot = z <= zb_ + 1
                if gumz: c = (C['gum'] if rim else C['mouth']) if z == zg else C['skin']
                elif wall: c = C['skin_dark'] if (zg - z) % 3 == 0 else C['skin']
                elif bot and (x % Rb == 0 or dy <= 2): c = C['skin']
                elif wi <= J['wall'] + 1: c = C['skin']
                else: continue
                put(x, y, z, c, outside=True)       # 🩸 第一版鋪進船頭船殼裡肋骨之間的空隙，在上甲板底下封出 70 格空腔
    # ── 嘴角：艙壁前 cheek_len 格內，兩舷外側把上下顎接起來 ──
    for x in range(x0, x0 + J['cheek_len']):
        w = min(w_of(x, x0, xt, J['W0']), w_of(x, x0, xl, J['W0'] - 1))
        for s in (-1, 1):
            for dy in range(int(w) - J['cheek_thick'] + 1, int(w) + 1):
                for z in range(int(round(zl_gum(x))) + 1, int(round(zu_gum(x)))):
                    put(x, YC + s * dy, z, C['skin'])
    # ── 喉嚨：艙壁前那一格塗暗（追擊砲門、門的開口留空）──
    hole = set()
    for yc in Hd['chase_ports']['y']:
        for y in range(yc - 3, yc + 4):
            for z in range(97, 120): hole.add((y, z))
    for y in range(YC - Hd['door']['dy'], YC + Hd['door']['dy'] + 1):
        for z in range(90, 120): hole.add((y, z))
    for y in range(YC - J['W0'], YC + J['W0'] + 1):
        for z in range(int(round(zl_gum(x0))) + 1, int(round(zu_gum(x0)))):
            if (y, z) in hole: continue
            if occ[x0 - 1, y, z]: put(x0, y, z, C['mouth'])
    # ── knee：從艏柱前緣往前到下顎底 ──
    K = J['knee']
    z_top_k = lambda x: int(round(zl_gum(x))) - L['thick']
    for z in range(K['z0'], int(round(zl_gum(xl))) - L['thick'] + 1):
        sf = float(H.stem_face(z + 0.5))
        t = (z - K['z0']) / max(1, (z_top_k(xl) - K['z0']))
        xk = sf + (xl - K['back'] - sf) * min(t, 1.0) ** K['power']
        for x in range(int(math.floor(sf)), int(math.floor(xk)) + 1):
            if z > z_top_k(min(x, xl)): continue
            for y in range(YC - 2, YC + 3): put(x, y, z, C['knee'])
    # ── 牙 ──
    T = J['teeth']; n_up = n_lo = 0
    def tooth(x, y_rim, s, z_root, direction, length):
        for k in range(length):
            z = z_root + direction * k
            inward = 1 if k >= length // 2 else 0                 # 後半截往嘴裡彎一格
            y = y_rim - s * inward
            put(x, y, z, C['tooth'], over=True)
            if k == length // 2:                                  # 彎的那一層補一格接上根部（🩸 第一版只靠邊角相接，牙尖 224 格浮空被丟）
                put(x, y_rim, z, C['tooth'], over=True)
            if k < T['root_len']:
                put(x + 1, y, z, C['tooth'], over=True)           # 根部 2 格寬（沿 x），其他 1 格
        return 1
    for x in range(x0 + 2, xt - 1):
        w = w_of(x, x0, xt, J['W0'])
        if w < 1.5: continue
        if x % T['every'] == 0:
            ln = T['up_min'] + int(hsh(x, 1) * (T['up_max'] - T['up_min'] + 1))
            room = int(round(zu_gum(x))) - int(round(zl_gum(min(x, xl)))) - 2 if x <= xl else ln
            ln = max(2, min(ln, room))
            for s in (-1, 1):
                n_up += tooth(x, YC + s * (int(w) - 1), s, int(round(zu_gum(x))) - 1, -1, ln)
    for x in range(x0 + 3, xl - 1):
        w = w_of(x, x0, xl, J['W0'] - 1)
        if w < 1.5: continue
        if x % T['every'] == (T['every'] + 1) // 2:
            ln = T['lo_min'] + int(hsh(x, 2) * (T['lo_max'] - T['lo_min'] + 1))
            room = int(round(zu_gum(x))) - int(round(zl_gum(x))) - 2
            ln = max(2, min(ln, room))
            for s in (-1, 1):
                n_lo += tooth(x, YC + s * (int(w) - 1), s, int(round(zl_gum(x))) + 1, +1, ln)
    # ── 勾角：上顎尖端往前再往上 ──
    Hk = J['hook']
    zt0 = zu_top(xt)
    for i in range(0, 201):
        s_ = i / 200
        x = xt - 2 + Hk['forward'] * math.sin(s_ * math.pi / 2)
        z = zt0 - 1 + Hk['rise'] * s_ ** 1.6
        r = Hk['r0'] * (1 - s_) + 0.4
        for dy in range(-2, 3):
            for dz in range(-2, 3):
                for dx in range(-2, 3):
                    if dx * dx + dy * dy + dz * dz <= r * r:
                        put(int(round(x)) + dx, YC + dy, int(round(z)) + dz, C['hook'], over=True)

    # 碎片：沒連到船的丟掉，照實記
    st6 = ndimage.generate_binary_structure(3, 1)
    lab, n = ndimage.label(new > 0)
    touch = ndimage.binary_dilation(occ, structure=st6)
    ok_lab = set(np.unique(lab[(new > 0) & touch]).tolist()) - {0}
    flo = (new > 0) & ~np.isin(lab, list(ok_lab))
    floating = int(flo.sum())
    lab_f, n_f = ndimage.label(flo); floating_pieces = []
    for i in range(1, n_f + 1):
        q = np.argwhere(lab_f == i)
        floating_pieces.append({'n': int(len(q)), 'min': [int(v) for v in q.min(0)], 'max': [int(v) for v in q.max(0)], 'colors': sorted(set(int(c) for c in new[tuple(q.T)]))})
    new[flo] = 0

    # 小的封閉口袋（≤ fill_max 格、碰到船頭）補實（下顎外牆、側舷、底肋圍出來的 2 格口袋，兩舷各一）
    allv0 = new > 0
    allv0 = allv0 | occ
    cav0 = ndimage.binary_fill_holes(allv0) & ~allv0
    lab0, n0 = ndimage.label(cav0); filled = 0
    near_head = ndimage.binary_dilation(new > 0, structure=st6)
    for i in range(1, n0 + 1):
        q = lab0 == i
        if q.sum() <= J['fill_max'] and (q & near_head).any():
            new[q] = C['skin']; filled += int(q.sum())
    # ── 清單：先整件刻掉舊的，再貼新的 ──
    od = os.path.join(d, 'masks', 'jaws'); os.makedirs(od, exist_ok=True)
    for f in os.listdir(od): os.remove(os.path.join(od, f))
    order = {'head': []}
    for name, mask, col, op in (('old_head_carve', old_head > 0, old_head, 'carvevox'), ('jaws', new > 0, new, 'stampvox')):
        pts = np.argwhere(mask)
        text = lst(pts, col[tuple(pts.T)])
        fn = name + '.vox.txt'
        open(os.path.join(od, fn), 'w', encoding='utf-8', newline='\n').write(text)
        order['head'].append({'name': name, 'op': op, 'file': 'masks/jaws/' + fn, 'at': [0, 0, 0], 'expect_pixels': int(len(pts)),
                              'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()})
    # ── 讀數 ──
    parts = {k: v > 0 for k, v in W.items() if k != 'head'}; parts['head'] = new > 0
    ks = list(parts); pair = {}
    for i, a_ in enumerate(ks):
        for b_ in ks[i + 1:]:
            n_ = int((parts[a_] & parts[b_]).sum())
            if n_: pair[a_ + '×' + b_] = n_
    allv = np.zeros(old_head.shape, bool)
    for v in parts.values(): allv |= v
    labA, ncomp = ndimage.label(allv)
    cav = ndimage.binary_fill_holes(allv) & ~allv
    holes = int(cav.sum())
    lab_c, n_c = ndimage.label(cav); cav_pieces = []
    for i in range(1, n_c + 1):
        q = np.argwhere(lab_c == i)
        cav_pieces.append({'n': int(len(q)), 'min': [int(v) for v in q.min(0)], 'max': [int(v) for v in q.max(0)]})
    R = {'stamp_order': order, 'cavity_pieces': cav_pieces[:20],
         'geometry': {'x_from': x0, 'x_tip_upper': xt, 'x_tip_lower': xl, 'upper_gum_z': [round(zu_gum(x0), 2), round(zu_gum(xt), 2)],
                      'lower_gum_z': [round(zl_gum(x0), 2), round(zl_gum(xl), 2)], 'gape_at_back': round(zu_gum(x0) - zl_gum(x0), 2),
                      'gape_at_lower_tip': round(zu_gum(xl) - zl_gum(xl), 2)},
         'counts': {'old_head_carved': int((old_head > 0).sum()), 'jaws': int((new > 0).sum()), 'teeth_upper': n_up, 'teeth_lower': n_lo,
                    'by_color': {str(k): int((new == k).sum()) for k in sorted(set(new[new > 0].tolist()))}, 'assembly_total': int(allv.sum())},
         'cavity_filled': filled, 'floating_dropped': floating, 'floating_pieces': floating_pieces[:20],
         'checks': {'pair_overlap_all_parts': pair, 'components_assembly': int(ncomp), 'enclosed_cavity_assembly': holes,
                    'components_head': int(ndimage.label(new > 0)[1]), 'mirror_head': int((new != new[:, ::-1, :]).sum())}}
    with open(os.path.join(d, 'verify_jaws.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    draw(H, W, new, os.path.join(d, 'sheet05_jaws_v1.png'))
    print(json.dumps({k: R[k] for k in ('geometry', 'counts', 'cavity_filled', 'floating_dropped', 'floating_pieces', 'cavity_pieces', 'checks')}, ensure_ascii=False))


def draw(H, W, new, path):
    NX, NY, YC = H.NX, H.NY, H.YC
    allc = np.zeros(new.shape, np.int16)
    for k, v in W.items():
        if k != 'head': allc = np.where(v > 0, v, allc)
    allc = np.where(new > 0, new, allc)
    S = 5; W_, Hh = 1700, 900
    im = Image.new('RGB', (W_, Hh), (250, 248, 242)); g = ImageDraw.Draw(im); ink = (30, 30, 30)
    g.text((20, 12), "風暴角號 Stormkaap　新圖紙 05c　船頭的大嘴（從右舷看／從船頭看）　0.1 m／格　summit 2026-10-14　（設計；Tim 給的劇照只看不收）", fill=ink, font=font(20))
    half = allc[:, YC:, :]
    hasv = (half > 0).any(axis=1)
    last = half.shape[1] - 1 - np.argmax(half[:, ::-1, :] > 0, axis=1)
    ox, base = 40, 860
    for x, z in np.argwhere(hasv):
        if x < 440 or z < 20 or z > 150: continue
        g.rectangle([ox + (x - 440) * S, base - (z - 20 + 1) * S, ox + (x - 440 + 1) * S, base - (z - 20) * S], fill=pal(int(half[x, last[x, z], z])))
    g.text((ox, 50), "從右舷看（x 440–620、z 20–150）", fill=ink, font=font(18))
    sub = allc[::-1]
    has = (sub > 0).any(axis=0)
    first = np.argmax(sub > 0, axis=0)
    ox2 = 1100
    for y, z in np.argwhere(has):
        if z < 20 or z > 150 or abs(y - YC) > 55: continue
        g.rectangle([ox2 + (y - YC + 55) * 5, base - (z - 20 + 1) * 5, ox2 + (y - YC + 56) * 5, base - (z - 20) * 5], fill=pal(int(sub[first[y, z], y, z])))
    g.text((ox2, 50), "從船頭看（z 20–150）", fill=ink, font=font(18))
    im.save(path, optimize=False)


if __name__ == '__main__':
    main()
