# 利劍號 新圖紙 05（TASK-0022 步驟 7）：三根桅（後桅、主桅、前桅）、三根三角帆桁
#   出處：蠍子號 claude-galiot-01m/design/draft_masts.py（三角帆桁在自己的框裡就做成斜的、模型 rotate 0、固定點 pivot／sling／fore／peak／jackstay；
#         桅頂 calcet、滑輪槽、金帽）。改的地方：
#   * 三根桅、前桅與後桅有傾角（verify_layout.json 的桅腳與桅頂，步驟 3 照 Chapman 甲板下虛線畫的桅身量的）。
#   * 桅孔在步驟 5 就開好了（draft_decks.py 照同一條桅軸、同一個半徑開的圓）⇒ 這裡不刻甲板；桅在甲板那幾層用一樣的圓，剛好填滿。
#   * 不量走路格（中線上只有桅；甲板層的走路照步驟 5，桅把孔補起來只會少掉孔那一圈）。
#   輸入：plan.json（rig、rig_build、decks_build.mast_r、space）、verify_layout.json、verify_decks.json（每層桅孔的軸）、
#         前面每一步的設計清單（船殼＋換色、甲板、梯子、長喙、平台、玻璃、篷架）——不讀作品 ⇒ 落格之後重跑一樣。
#   輸出：masks/masts/<桅>.vox.txt（桅子作品，at 0,0,0、組裝件的框）、masks/yards/lateen-<桅>.vox.txt（帆桁子作品，自己的框）、
#         yards_lateen.json、yards_placement.json、verify_masts.json、sheet05_masts_v1.png
#   用法：python -I -X utf8 draft_masts.py [--probe=pivot_main=-80] [--probe=r_main=4.5]（反向對照，不寫檔）
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
from draft_lines import palette_rgb

sys.stdout.reconfigure(encoding='utf-8')
CELL = 0.1
V = HL.V
ORDER = ['mizzen', 'main', 'fore']


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def main():
    probe = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    YC = int(plan['space']['yc'])
    AX, AY, AZ = [int(v) for v in plan['space']['assembly']]
    RB = {k: V(v) for k, v in plan['rig_build'].items() if k != 'src'}
    C = RB['colors']
    MH = RB['masthead']
    LAY = json.load(open(os.path.join(HERE, 'verify_layout.json'), encoding='utf-8'))['masts']
    VD = json.load(open(os.path.join(HERE, 'verify_decks.json'), encoding='utf-8'))
    MR = V(plan['decks_build']['mast_r'])
    rig = plan['rig']['v']

    hull = load('masks/hull/hull_01.vox.txt')
    hull.update(load('masks/step6/hull_paint.vox.txt'))
    ship = dict(hull)
    for f in ('decks/hold', 'decks/main', 'decks/quarter', 'ladders/main', 'ladders/quarter', 'deco/beak', 'deco/platform', 'deco/glass'):
        ship.update(load('masks/' + f + '.vox.txt'))
    awning = load('masks/deco/awning.vox.txt')
    hcols = {}
    for (x, y, z) in hull:
        hcols.setdefault((x, y), []).append(z)
    hmin = {k: min(v) for k, v in hcols.items()}
    # 甲板層：每層板與樑的 z 範圍（照 decks 清單那一欄）⇒ 那幾層用跟桅孔一樣的圓
    decks = {k: load('masks/decks/%s.vox.txt' % k) for k in ('hold', 'main', 'quarter')}
    masts, R = {}, {'masts': {}, 'yards': {}, 'probe': probe or None}
    TOP = {}
    for m in ORDER:
        L = LAY[m]
        (fx, fz), (tx, tz) = L['foot'], L['top']
        r = float(probe.get('r_' + m, MR[m]))
        axis = lambda z: fx + (tx - fx) * (z + 0.5 - fz) / (tz - fz)
        # 桅頂 ＝ 桅腳（軸那一欄船殼最低格上面一格）＋ 桅長 × cos 傾角（plan.rig：桅長從桅腳量到桅頂）
        #   v1 用 verify_layout 的名義桅腳 z 5 算頂 ⇒ 桅腳實際坐在 z 10／2／11，長度差 −0.48／+0.33／−0.61 m（verifier7）
        def has_cell(z):                                            # 同下面放格的條件：圓內、不在船上、在那一欄船殼底以上
            xa = axis(z)
            return any((x + 0.5 - xa) ** 2 + dy ** 2 <= r * r and (x, YC + dy, z) not in ship and z > hmin.get((x, YC + dy), 10 ** 6)
                       for x in range(int(math.floor(xa)) - 5, int(math.floor(xa)) + 6) for dy in range(-5, 6))
        heel = next(z for z in range(0, 100) if has_cell(z))
        top = heel + int(round(rig[m]['mast_len_m'] * math.cos(math.radians(rig[m]['rake_deg'])) / CELL)) + int(probe.get('top_' + m, 0))
        TOP[m] = top
        holes = VD['masts'][m].get('holes', {})
        # 每層桅孔：孔附近那幾欄甲板的 z（板＋樑）⇒ 那幾層的桅截面用開孔時那條軸（跟孔一模一樣的圓）
        hz = {}
        for k, xh in holes.items():
            ri = int(math.ceil(MR[m])) + 2
            hz[k] = sorted({z for (x, y, z) in decks[k] if abs(x - xh) <= ri + 2 and abs(y - YC) <= ri})
        cells = {}
        for z in range(0, top):
            xa = axis(z)
            for k, xh in holes.items():
                if z in hz[k]:
                    xa = xh
            rr = r
            for dx in range(-5, 6):
                for dy in range(-5, 6):
                    x, y = int(math.floor(xa)) + dx, YC + dy
                    if (x + 0.5 - xa) ** 2 + dy ** 2 > rr * rr:
                        continue
                    if (x, y, z) in ship or z <= hmin.get((x, y), 10 ** 6):
                        continue                                # 船殼與甲板的格不放；只放在那一欄船殼底以上（桅腳坐在船殼上）
                    cells[(x, y, z)] = C['mast']
        # 桅頂 calcet：頂上 h 格，前後各多 1 格；離頂 2–3 格前後端黑滑輪槽；頂 1 格金帽
        xt = axis(top - MH['h'])
        ri = int(math.floor(r))
        for z in range(top - MH['h'], top):
            xa = axis(z)
            for dx in range(-ri - 1, ri + 2):
                for dy in range(-ri, ri + 1):
                    if dy * dy + (max(0, abs(dx) - 1)) ** 2 > r * r + 0.5:
                        continue
                    x, y = int(math.floor(xa)) + dx, YC + dy
                    c = C['mast']
                    if dy == 0 and top - 1 - z in MH['sheave'] and abs(dx) == ri + 1:
                        c = C['sheave']
                    if z >= top - MH['cap_h']:
                        c = C['cap']
                    cells[(x, y, z)] = c
        masts[m] = cells
        # 每層桅孔填滿了沒：孔 ＝ 那幾層裡、圓內、沒有甲板格、在船殼外形裡的格；每一格都要是桅
        unfilled = {}
        for k, xh in holes.items():
            n = 0
            for z in hz[k]:
                for x in range(int(xh) - 6, int(xh) + 7):
                    for y in range(YC - 6, YC + 7):
                        if (x + 0.5 - xh) ** 2 + (y + 0.5 - (YC + 0.5)) ** 2 <= MR[m] ** 2 and (x, y, z) not in ship and (x, y, z) not in cells \
                                and z > hmin.get((x, y), 10 ** 6):
                            n += 1
            unfilled[k] = n
        zs = sorted({k[2] for k in cells})
        G = np.zeros((AX, AY, AZ), bool)
        for k in cells:
            G[k] = True
        R['masts'][m] = {'cells': len(cells), 'components_6': int(ndimage.label(G)[1]), 'z': [zs[0], zs[-1]], 'length_m': round((zs[-1] + 1 - zs[0]) * CELL, 2),
                         'heel_z': heel, 'length_along_axis_m': round((zs[-1] + 1 - zs[0]) * CELL / math.cos(math.radians(rig[m]['rake_deg'])), 2),
                         'plan_mast_len_m': rig[m]['mast_len_m'],
                         'r': r, 'rake_deg': rig[m]['rake_deg'], 'axis_at_heel': round(axis(zs[0]), 2), 'axis_at_top': round(axis(zs[-1]), 2),
                         'mirror_diff': sum(1 for (x, y, z), c in cells.items() if cells.get((x, 2 * YC - y, z)) != c),
                         'overlap_ship': sum(1 for k in cells if k in ship), 'overlap_awning': sum(1 for k in cells if k in awning),
                         'holes_unfilled_cells': unfilled,
                         'colours': {str(c): sum(1 for v in cells.values() if v == c) for c in sorted(set(cells.values()))}}

    # ── 三角帆桁（自己的框）：斜桿，前端低（x 大）、後端高 ──
    yards, place, an_all = {}, [], {}
    Yall = RB['yard']
    for m in ORDER:
        Y = dict(Yall['common'], **Yall[m])
        Lc = rig[m]['yard_len_m'] / CELL
        th = math.radians(plan['rig']['yard_angle_deg']['v'][m])
        pad = 3
        W_ = int(math.ceil(Lc * math.cos(th))) + 2 * pad
        H_ = int(math.ceil(Lc * math.sin(th))) + 2 * pad
        yh = int(math.ceil(Y['r_max'])) + 1
        Wy = 2 * yh + 1
        F = (W_ - pad, pad)
        A = (F[0] - Lc * math.cos(th), F[1] + Lc * math.sin(th))
        hs = Y['hoist_frac'] * Lc
        vx, vz = A[0] - F[0], A[1] - F[1]
        ln = math.hypot(vx, vz)
        radius = lambda s: Y['r_end'] + (Y['r_max'] - Y['r_end']) * max(0.0, 1 - abs(s - hs) / max(hs, Lc - hs))
        yc_ = {}
        for x in range(0, W_):
            for z in range(0, H_):
                px, pz = x + 0.5 - F[0], z + 0.5 - F[1]
                t = (px * vx + pz * vz) / ln
                if t < -0.5 or t > ln + 0.5:
                    continue
                tc = min(max(t, 0.0), ln)
                d2 = (px - tc * vx / ln) ** 2 + (pz - tc * vz / ln) ** 2
                rr = radius(tc)
                lash = abs(tc - hs) <= Y['lash_half'] and abs(tc - hs) > 1.5 and int(round(tc - hs)) % Y['lash_every'] == 0
                for dy in range(-yh, yh + 1):
                    if d2 + dy * dy <= (rr + 0.5) ** 2:              # 格心離桿軸 ≤ r＋0.5 ⇒ r_max 2 的中段 5 格、1.5 的 3 格（v1 用 ≤ r：只有 3 格，verifier7）
                        yc_[(x, yh + dy, z)] = C['lashing'] if lash else C['yard']

        def near(s, top=False):
            px_, pz_ = F[0] + vx / ln * s, F[1] + vz / ln * s
            best = min((k for k in yc_ if k[1] == yh), key=lambda k: ((k[0] + 0.5 - px_) ** 2 + (k[2] + 0.5 - pz_) ** 2, k))
            if top:
                z = best[2]
                while (best[0], yh, z + 1) in yc_:
                    z += 1
                best = (best[0], yh, z)
            return list(best)
        anchors = {'pivot': near(hs), 'sling': near(hs, True), 'fore': near(1.0), 'peak': near(Lc - 1.0)}
        for k_, s in enumerate(np.arange(8.0, Lc - 4, 8.0)):
            anchors['jackstay-%02d' % (k_ + 1)] = near(float(s), True)
        pv = anchors['pivot']
        Lm = LAY[m]
        (fx, fz), (tx, tz) = Lm['foot'], Lm['top']
        zp = TOP[m] - Y['below_top'] + int(probe.get('pivot_' + m, 0))
        xm = fx + (tx - fx) * (zp + 0.5 - fz) / (tz - fz)            # 桅軸在吊點高度
        rmast = MR[m]
        sd_ = Y.get('side', -1)                                      # −1 左舷側（預設）、+1 右舷側
        yhalf = max(abs(k[1] - yh) for k in yc_)                     # 帆桁實際的半寬（格）
        # 跟桅空 1 格：桅（含 calcet）最外 |dy| ＝ floor(r)；v1 照框 ±yh 算 ⇒ 空了 3 格（verifier7）
        yw = YC + sd_ * (int(math.floor(rmast)) + 1 + yhalf + int(probe.get('gap_' + m, 1)))
        xmi = int(math.floor(xm))
        off = (xmi - pv[0], yw - pv[1], zp - pv[2])
        wc = {(x + off[0], y + off[1], z + off[2]): c for (x, y, z), c in yc_.items()}
        an_w = {n: [a[0] + off[0], a[1] + off[1], a[2] + off[2]] for n, a in anchors.items()}
        yards[m] = {'cells': yc_, 'world': wc, 'size': [W_, Wy, H_], 'anchors': anchors, 'anchors_world': an_w}
        place.append({'name': 'yard-%s-lateen' % m, 'mast': m, 'host': 'mast-' + m, 'work': 'claude-xebec-01m-yard-' + m,
                      'at': [xmi + 0.5, yw + 0.5, zp + 0.5], 'pivot': [pv[0] + 0.5, pv[1] + 0.5, pv[2] + 0.5], 'rotate': [0, 0, 0], 'scale': [1, 1, 1],
                      'meta': {'kind': 'yard', 'mast': m, 'yard': 'gaff', 'rig': 'lateen', 'sail': '%s-lateen' % m, 'length_m': rig[m]['yard_len_m'],
                               'length_ft': round(rig[m]['yard_len_m'] / 0.3048, 1), 'diameter_in': round((2 * int(Y['r_max']) + 1) * CELL / 0.0254, 1),
                               'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0}})
    # 帆桁讀數：跟世界（船、三根桅、篷架、別根帆桁）
    allmast = {}
    for m in ORDER:
        allmast.update(masts[m])
    for m in ORDER:
        y = yards[m]
        wc = y['world']
        others = set(ship) | set(allmast) | set(awning)
        for m2 in ORDER:
            if m2 != m:
                others |= set(yards[m2]['world'])
        tree = cKDTree(np.array(sorted(others), float))
        dmin, _ = tree.query(np.array(sorted(wc), float))
        G2 = np.zeros(tuple(y['size']), bool)
        for k in y['cells']:
            G2[k] = True
        piv, fore = y['anchors_world']['pivot'], y['anchors_world']['fore']
        band = [k for k in masts[m] if piv[2] - 40 <= k[2] <= piv[2] - 10 and abs(k[1] - YC) <= 4]
        xh = fore[0] - piv[0]
        R['yards'][m] = {'size': y['size'], 'cells': len(y['cells']), 'components_6': int(ndimage.label(G2)[1]), 'anchors': len(y['anchors']),
                         'overlap_world': sum(1 for k in wc if k in others), 'min_gap_cells': round(float(dmin.min()) - 1, 2),
                         'world_x': [min(k[0] for k in wc), max(k[0] for k in wc)], 'world_y': [min(k[1] for k in wc), max(k[1] for k in wc)],
                         'world_z': [min(k[2] for k in wc), max(k[2] for k in wc)],
                         'pivot_world': piv, 'fore_world': fore, 'peak_world': y['anchors_world']['peak'],
                         'mast_cells_in_shipcheck_band': len(band), 'band_z': [piv[2] - 40, piv[2] - 10],
                         'lateen_swing_deg': round(math.degrees(math.asin(min(1.0, 25.0 / xh))), 1) if xh > 0 else None,
                         'inside_assembly_box': all(0 <= k[0] < AX and 0 <= k[1] < AY and 0 <= k[2] < AZ for k in wc)}
        # 遊戲擺角：帆桁繞 pivot 格心、繞 z 轉 ±上限、±半上限 ⇒ 格心離船＋三根桅＋篷架（不含別根帆桁）最近幾格；< 1 算撞
        sw = R['yards'][m]['lateen_swing_deg'] or 0.0
        pc = np.array(piv, float) + 0.5
        tree_s = cKDTree(np.array(sorted(set(ship) | set(allmast) | set(awning)), float) + 0.5)
        P0 = np.array(sorted(wc), float) + 0.5 - pc
        swing = {}
        for a_ in (-sw, -sw / 2, sw / 2, sw):
            c_, s_ = math.cos(math.radians(a_)), math.sin(math.radians(a_))
            Pr = np.stack([P0[:, 0] * c_ - P0[:, 1] * s_, P0[:, 0] * s_ + P0[:, 1] * c_, P0[:, 2]], 1) + pc
            swing['%+.1f' % a_] = round(float(tree_s.query(Pr)[0].min()), 2)
        R['yards'][m]['swing_min_dist_cells'] = swing
    # 全船（船＋三根桅）結構
    U = np.zeros((AX, AY, AZ), bool)
    for k in ship:
        U[k] = True
    for k in allmast:
        U[k] = True
    R['ship_with_masts'] = {'cells': int(U.sum()), 'components_6': int(ndimage.label(U)[1]), 'cavities': int((ndimage.binary_fill_holes(U) & ~U).sum()),
                            'overlap_masts_ship': sum(1 for k in allmast if k in ship)}
    R['problems'] = (sum(R['masts'][m]['overlap_ship'] + R['masts'][m]['overlap_awning'] + R['masts'][m]['mirror_diff'] + (R['masts'][m]['components_6'] != 1)
                         + sum(R['masts'][m]['holes_unfilled_cells'].values()) for m in ORDER)
                     + (R['ship_with_masts']['components_6'] != 1) + R['ship_with_masts']['cavities']
                     + sum((R['yards'][m]['components_6'] != 1) + R['yards'][m]['overlap_world'] + (R['yards'][m]['mast_cells_in_shipcheck_band'] == 0)
                           + (not R['yards'][m]['inside_assembly_box']) + sum(v < 1.0 for v in R['yards'][m]['swing_min_dist_cells'].values()) for m in ORDER))
    if probe:
        print(json.dumps({'probe': probe, 'problems': R['problems'], 'masts': {m: {k: R['masts'][m][k] for k in ('cells', 'overlap_ship', 'holes_unfilled_cells')} for m in ORDER},
                          'yards': {m: {k: R['yards'][m][k] for k in ('pivot_world', 'band_z', 'mast_cells_in_shipcheck_band', 'min_gap_cells', 'overlap_world')} for m in ORDER},
                          'ship_with_masts': R['ship_with_masts']}, ensure_ascii=False))
        return

    def dump(path, cl, head):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(head)
            for (x, y, z), c in sorted(cl.items()):
                fh.write('%d,%d,%d,%d\n' % (x, y, z, c))
        return hashlib.sha256(open(path, 'rb').read()).hexdigest()
    sha = {}
    for m in ORDER:
        sha['masts/' + m] = dump(os.path.join(HERE, 'masks', 'masts', m + '.vox.txt'), masts[m], '# 利劍號 步驟 7：%s 桅（at 0,0,0、組裝件的框 %d×%d×%d）\n' % (m, AX, AY, AZ))
        s_ = yards[m]['size']
        sha['yards/lateen-' + m] = dump(os.path.join(HERE, 'masks', 'yards', 'lateen-%s.vox.txt' % m), yards[m]['cells'], '# 利劍號 步驟 7：%s 三角帆桁（自己的框 %d×%d×%d）\n' % (m, s_[0], s_[1], s_[2]))
    R['sha256'] = sha
    with open(os.path.join(HERE, 'yards_lateen.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump({m: {'size': yards[m]['size'], 'anchors': yards[m]['anchors'], 'len_m': rig[m]['yard_len_m'],
                       'tilt_deg': plan['rig']['yard_angle_deg']['v'][m], 'sail': '%s-lateen' % m} for m in ORDER}, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'yards_placement.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(place, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)
    # 圖紙 05：右舷外看（船頭朝右）：船＋桅＋帆桁（照 y 排，近的蓋遠的）
    s = 2
    img = Image.new('RGB', (AX * s + 80, AZ * s + 80), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((30, 10), '%s - new sheet 05: masts (mizzen / main / fore) and lateen yards; starboard view, bow to the right; 0.1 m/cell' % plan['title_en'], fill=(20, 20, 40), font=f)
    oy = 40 + AZ * s
    side = {}
    def put(k, c):
        p = (k[0], k[2])
        if p not in side or side[p][0] < k[1]:
            side[p] = (k[1], c)
    for src in (ship, awning, allmast):
        for k, c in src.items():
            put(k, c)
    for m in ORDER:
        for k, c in yards[m]['world'].items():
            put(k, c)
    for (x, z), (_, c) in side.items():
        if 0 <= z < AZ:
            d.rectangle([40 + x * s, oy - (z + 1) * s, 40 + x * s + s - 1, oy - z * s - 1], fill=palette_rgb(c))
    wl = plan['waterline']['z']
    d.line([40, oy - (wl + 1) * s, 40 + AX * s, oy - (wl + 1) * s], fill=(40, 110, 200))
    for m in ORDER:
        for nm, col in (('pivot', (200, 30, 30)), ('fore', (30, 120, 30)), ('peak', (30, 30, 200))):
            p = yards[m]['anchors_world'][nm]
            d.ellipse([40 + p[0] * s - 3, oy - p[2] * s - 3, 40 + p[0] * s + 3, oy - p[2] * s + 3], outline=col, width=2)
        b = R['yards'][m]['band_z']
        xa = R['masts'][m]['axis_at_top']
        d.text((40 + int(xa) * s + 8, oy - b[1] * s), '%s: shipcheck band z %d-%d %d mast cells, swing %s deg' % (m, b[0], b[1], R['yards'][m]['mast_cells_in_shipcheck_band'], R['yards'][m]['lateen_swing_deg']), fill=(200, 30, 200), font=f)
    for x in range(0, AX + 1, 50):
        d.text((40 + x * s - 6, oy + 6), str(x), fill=(80, 80, 80), font=f)
    img.save(os.path.join(HERE, 'sheet05_masts_v1.png'))
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
