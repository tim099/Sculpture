# 圖紙 F1 v1（TASK-0538 船首像）：照片描出的外輪廓（正面、右側）＋ 補上的雙手與提燈 ＋ 放在船頭的位置與尺寸
# 用法：python -I draft_sheet_f1.py <design 資料夾>
#   · 先跑 trace_photos.py（readings/mask_front.png、mask_right.png）。
#   · 身體座標：x 往前、y 往她的左手邊、z 往上；長度以身高 H 為 1（plan.json units）。
#   · 手：兩段骨 IK（肩 → 肘 → 腕），pole 決定手肘往哪邊彎；握點 ＝ 腕再往前半個手掌。
#   · 放在船頭：腳底中心在 knee 頂端、整尊往前傾 θ；掃 θ 與 H，取「離艏斜桅 ≥ clearance、背不進船殼」的最大 H。
#   ⇒ sheetF1_v1.png、verify_sheet_f1.json
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.join(HERE, '..', '..', 'basecamp-nightlamp-01m', 'design')
sys.path.insert(0, PARENT)
import draft_lines as DL   # noqa: E402

F = lambda n: DL.font(n)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def ik(S, G, a, b, pole):
    """兩段骨：肩 S、目標腕 G、上臂 a、前臂 b、pole ＝ 手肘偏向 ⇒ 肘 E（G 太遠就拉直、腕停在最遠處）"""
    S, G = np.asarray(S, float), np.asarray(G, float)
    d = G - S
    L = np.linalg.norm(d)
    u = d / L
    reach = min(L, a + b - 1e-6)
    W = S + u * reach
    ca = (a * a + reach * reach - b * b) / (2 * a * reach)
    ang = math.acos(max(-1, min(1, ca)))
    p = np.asarray(pole, float)
    p = p - u * (p @ u)
    p = unit(p)
    E = S + a * (math.cos(ang) * u + math.sin(ang) * p)
    return E, W, L


class Figure:
    def __init__(s, design):
        s.design = design
        s.P = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        ph, lm = s.P['photos'], s.P['landmarks_px']
        fr, ri = ph['front'], ph['right']
        s.Hf = fr['sole_y'] - fr['crown_y']
        s.Hr = ri['sole_y'] - ri['crown_y']
        s.fy = lambda x: (x - fr['mid_x']) / s.Hf                # 正面圖 x → y（圖的右邊 ＝ 她的左邊）
        s.fz = lambda y: (fr['sole_y'] - y) / s.Hf
        s.rx = lambda x: (x - ri['ref_x']) / s.Hr                # 右側圖 x → x（臉朝圖右 ＝ 往前）
        s.rz = lambda y: (ri['sole_y'] - y) / s.Hr
        s.mf = np.asarray(Image.open(os.path.join(design, 'readings', 'mask_front.png'))) > 0
        s.mr = np.asarray(Image.open(os.path.join(design, 'readings', 'mask_right.png'))) > 0
        A = s.P['arms']
        Lh = A['lengths_H']
        f, r = lm['front'], lm['right']
        sL = np.array([s.rx(r['shoulder_R'][0]) - 0.02, s.fy(f['shoulder_L'][0]), s.fz(f['shoulder_L'][1])])
        sR = np.array([s.rx(r['shoulder_R'][0]), s.fy(f['shoulder_R'][0]), (s.fz(f['shoulder_R'][1]) + s.rz(r['shoulder_R'][1])) / 2])
        s.arms = {}
        for side, S in (('left', sL), ('right', sR)):
            g = np.array(A[side]['grip'], float)
            # 握點在腕往目標方向再半個手掌 ⇒ 腕的目標 ＝ 握點往肩那邊退半個手掌
            Wt = g - unit(g - S) * Lh['hand'] * 0.5
            E, W, L = ik(S, Wt, Lh['upper'], Lh['fore'], A[side]['pole'])
            Hd = W + unit(g - W) * (np.linalg.norm(g - W) + 0.015)   # 手掌到握點（手指扣住提環／衣褶，不往外伸）
            s.arms[side] = {'S': S, 'E': E, 'W': W, 'grip': g, 'tip': Hd, 'reach_needed': L,
                            'reach_max': Lh['upper'] + Lh['fore']}
        Lt = s.P['lantern']
        g = s.arms['left']['grip']
        top = g[2] - Lt['bail_H']
        s.lantern = {'cx': g[0], 'cy': g[1], 'roof_top': top, 'body_top': top - Lt['roof_h_H'],
                     'bottom': top - Lt['roof_h_H'] - Lt['body_h_H'], 'w': Lt['body_w_H']}

    # 輪廓（身體座標的點雲：遮罩的邊界像素）
    def outline_pts(s, which):
        m = s.mf if which == 'front' else s.mr
        from scipy import ndimage
        e = m & ~ndimage.binary_erosion(m)
        ys, xs = np.where(e)
        if which == 'front':
            return np.c_[s.fy(xs), s.fz(ys)]
        return np.c_[s.rx(xs), s.rz(ys)]

    def extra_pts_side(s):
        """手與燈在側面（x, z）的點（含粗細）"""
        A = s.P['arms']['radius_H']
        pts = []
        for side in ('left', 'right'):
            a = s.arms[side]
            for P0, P1, r0, r1 in ((a['S'], a['E'], A['shoulder'], A['elbow']), (a['E'], a['W'], A['elbow'], A['wrist']),
                                   (a['W'], a['tip'], A['wrist'], A['wrist'] * 0.8)):
                for t in np.linspace(0, 1, 12):
                    c = P0 + (P1 - P0) * t
                    r = r0 + (r1 - r0) * t
                    for ang in np.linspace(0, 2 * math.pi, 12, endpoint=False):
                        pts.append((c[0] + r * math.cos(ang), c[2] + r * math.sin(ang)))
        L = s.lantern
        w = L['w'] / 2
        for x in (L['cx'] - w, L['cx'] + w):
            for z in (L['bottom'], L['roof_top']):
                pts.append((x, z))
        pts.append((s.arms['left']['grip'][0], s.arms['left']['grip'][2]))
        return np.array(pts)


def placement(fig):
    """船頭：腳底中心在 knee 頂端；掃前傾 θ、身高 H ⇒ 放得下的最大 H（真實公尺；母作品底圖 m × k）"""
    plan, R, B, ship = DL.load(PARENT)
    xs, zs, T, hb_max, _ = DL.hull_table(ship)
    k, cpm, X, Z, Yh = DL.scale_of(plan, ship, hb_max)
    Si, M = plan['silhouette'], plan['masts']
    so = ship.stem_outer_pts
    knee_top = np.array([so[-1, 0], so[-1, 1]]) * k                      # (x, z) 真實 m（從船尾柱基準、龍骨頂）
    x_st = ship.fwd_end_top_x()
    z_st = float(ship.top(x_st)) - 0.6
    ang = math.radians(M['bowsprit']['angle_deg'])
    bs = lambda x: (z_st * k) + (x - x_st * k) * math.tan(ang)          # 艏斜桅中心線 z(x)
    stem_face = lambda z: float(ship.stem_face_x(z / k)) * k
    P = fig.P['placement']
    side = np.vstack([fig.outline_pts('right'), fig.extra_pts_side()])
    # 腳底中心：右側圖遮罩最下面那幾列的中點
    best = None
    rows = []
    for th in range(P['lean_deg_range'][0], P['lean_deg_range'][1] + 1):
        t = math.radians(th)
        c, s_ = math.cos(t), math.sin(t)
        Hok = None
        for H in np.arange(P['H_m_range'][0], P['H_m_range'][1] + 1e-9, 0.05):
            px = side[:, 0] * H
            pz = side[:, 1] * H
            wx = knee_top[0] + px * c + pz * s_                                # 往前傾：z 軸轉向 +x
            wz = knee_top[1] - px * s_ + pz * c
            gap = bs(wx) - wz
            if gap.min() < P['bowsprit_clearance_m']:
                break
            behind = (wx < np.interp(wz, [knee_top[1], knee_top[1] + 10], [stem_face(knee_top[1]), stem_face(knee_top[1] + 10)]))
            if behind.any():
                break
            Hok = round(float(H), 2)
        rows.append((th, Hok))
        if Hok and (best is None or Hok > best[1] + 1e-9):
            best = (th, Hok)
    ctx = {'k': k, 'knee_top': knee_top, 'x_st': x_st, 'z_st': z_st, 'ang': ang, 'bs': bs, 'stem_face': stem_face,
           'ship': ship, 'Si': Si, 'side': side, 'X': X, 'Z': Z}
    return best, rows, ctx


def draw(fig, best, rows, ctx, path):
    W_, H_ = 2400, 1520
    im = Image.new('RGB', (W_, H_), (252, 252, 250))
    d = ImageDraw.Draw(im)
    d.text((20, 12), fig.P['title'] + '　—— 米羅的維納斯＋雙手（左手舉提燈、右手按住衣褶）', fill=(30, 30, 30), font=F(26))
    # (a)(b) 照片＋描線
    from trace_photos import load
    x0 = 20
    for which in ('front', 'right'):
        img, _ = load(which)
        o = Image.open(os.path.join(fig.design, 'readings', f'trace_{which}.jpg')).crop((120, 150, 780, 1560))
        o = o.resize((o.width * 860 // o.height, 860))
        im.paste(o, (x0, 60))
        d.text((x0 + 6, 66), {'front': '(a) 正面照＋外輪廓', 'right': '(b) 右側照＋外輪廓'}[which], fill=(255, 220, 0), font=F(18))
        x0 += o.width + 16
    # (c)(d) 設計：正面、側面（身體座標，H ＝ 1 ⇒ 800 px）
    S = 780
    A = fig.P['arms']['radius_H']

    def panel(ox, oz, proj, title):
        d.rectangle([ox - 300, oz - 860, ox + 340, oz + 40], outline=(200, 200, 200))
        for g in np.arange(0, 1.21, 0.1):
            d.line([(ox - 300, oz - g * S), (ox + 340, oz - g * S)], fill=(232, 232, 236))
        pts = fig.outline_pts('front' if proj == 'yz' else 'right')
        for (a, b) in pts:
            d.point((ox + a * S, oz - b * S), fill=(60, 60, 60))
        for side, col in (('left', (200, 120, 0)), ('right', (40, 110, 200))):
            ar = fig.arms[side]
            seq = ((ar['S'], ar['E'], A['shoulder'], A['elbow']), (ar['E'], ar['W'], A['elbow'], A['wrist']),
                   (ar['W'], ar['tip'], A['wrist'], A['wrist'] * 0.8))
            for P0, P1, r0, r1 in seq:
                for t in np.linspace(0, 1, 40):
                    c = P0 + (P1 - P0) * t
                    r = (r0 + (r1 - r0) * t) * S
                    u = c[1] if proj == 'yz' else c[0]
                    d.ellipse([ox + u * S - r, oz - c[2] * S - r, ox + u * S + r, oz - c[2] * S + r], fill=col)
        L = fig.lantern
        u = L['cy'] if proj == 'yz' else L['cx']
        w = L['w'] / 2 * S
        d.rectangle([ox + u * S - w, oz - L['body_top'] * S, ox + u * S + w, oz - L['bottom'] * S], fill=(255, 210, 90), outline=(150, 100, 0), width=2)
        d.polygon([(ox + u * S - w * 1.15, oz - L['body_top'] * S), (ox + u * S + w * 1.15, oz - L['body_top'] * S), (ox + u * S, oz - L['roof_top'] * S)], fill=(60, 50, 40))
        g = fig.arms['left']['grip']
        gu = g[1] if proj == 'yz' else g[0]
        d.line([(ox + gu * S, oz - g[2] * S), (ox + u * S, oz - L['roof_top'] * S)], fill=(60, 50, 40), width=2)
        d.text((ox - 296, oz - 856), title, fill=(30, 30, 30), font=F(18))
        d.text((ox - 296, oz + 10), '格線每 0.1 H（H ＝ 頭頂到腳底）；灰點 ＝ 照片外輪廓；橘 ＝ 左手（舉燈）、藍 ＝ 右手（按衣褶）', fill=(90, 90, 90), font=F(13))
    panel(x0 + 320, 940, 'yz', '(c) 設計・正面（她面向你；圖右 ＝ 她的左手）')
    panel(x0 + 320 + 680, 940, 'xz', '(d) 設計・右側（往前 ＝ 圖右）')
    # (e) 放在船頭（真實公尺）
    th, Hm = fig.P['placement']['lean_deg'], fig.P['placement']['H_m']
    k = ctx['k']
    ox, oz, sc = 40, 1500, 40          # px／m
    kx = ctx['knee_top'][0]

    def Pm(x, z):
        return (ox + (x - kx + 8) * sc, oz - (z - 2) * sc)
    ship, Si = ctx['ship'], ctx['Si']
    zz = np.linspace(0, 11.5, 60)
    d.line([Pm(float(ship.stem_outer_x(z)) * k, z * k) for z in np.linspace(4.0, 6.85, 30)], fill=(20, 20, 20), width=3)
    d.line([Pm(float(ship.stem_face_x(z)) * k, z * k) for z in zz if z >= 4.0], fill=(20, 20, 20), width=2)
    xb = np.linspace(ctx['x_st'] - 6, ctx['x_st'], 30)
    d.line([Pm(x * k, float(ship.top(x)) * k) for x in xb], fill=(20, 20, 20), width=2)
    lwl = ship.lwl_b * k
    d.line([Pm(kx - 8, lwl), Pm(kx + 8, lwl)], fill=(40, 90, 220), width=1)
    x1 = ctx['x_st'] * k + 9
    d.line([Pm(ctx['x_st'] * k, ctx['z_st'] * k), Pm(x1, ctx['bs'](x1))], fill=(120, 90, 60), width=7)
    t = math.radians(th)
    side = ctx['side']
    wx = ctx['knee_top'][0] + side[:, 0] * Hm * math.cos(t) + side[:, 1] * Hm * math.sin(t)
    wz = ctx['knee_top'][1] - side[:, 0] * Hm * math.sin(t) + side[:, 1] * Hm * math.cos(t)
    for a, b in zip(wx, wz):
        q = Pm(a, b)
        d.ellipse([q[0] - 1, q[1] - 1, q[0] + 1, q[1] + 1], fill=(200, 120, 0))
    hd = Si['head']
    fx, fz = hd['figurehead_box_x'], hd['figurehead_box_z']
    d.rectangle([Pm(fx[0] * k, fz[1] * k), Pm(fx[1] * k, fz[0] * k)], outline=(160, 160, 160))
    gap = float((ctx['bs'](wx) - wz).min())
    over = float(wx.max() - ctx['knee_top'][0])
    top = float(wz.max())
    fig.place = {'lean_deg': th, 'H_m': Hm, 'min_gap_to_bowsprit_centre_m': round(gap, 2),
                 'forward_of_knee_top_m': round(over, 2), 'top_above_keel_top_m': round(top, 2)}
    d.text((ox, oz - 506), f'離艏斜桅中心線最近 {gap:.2f} m；最前端在 knee 頂端前 {over:.2f} m', fill=(90, 90, 90), font=F(13))
    d.text((ox, oz - 552), f'(e) 放在船頭（右舷看、真實公尺）：前傾 {th}°、身高 H ＝ {Hm:.2f} m，{Hm / 0.01:.0f} 格（0.01 m／格）', fill=(30, 30, 30), font=F(18))
    d.text((ox, oz - 529), f'條件：整尊（含手與燈）離艏斜桅中心線至少 {fig.P["placement"]["bowsprit_clearance_m"]} m、背不進船頭柱；灰框 ＝ 線形圖 v1 的船頭像框（{(fx[1]-fx[0])*k:.1f} × {(fz[1]-fz[0])*k:.1f} m）', fill=(90, 90, 90), font=F(13))
    im.save(path)


def main():
    design = sys.argv[1]
    sys.path.insert(0, design)
    fig = Figure(design)
    best, rows, ctx = placement(fig)
    assert best, '沒有任何前傾角放得下'
    draw(fig, best, rows, ctx, os.path.join(design, 'sheetF1_v1.png'))
    v = {'arms': {sd: {k_: (np.round(val, 4).tolist() if isinstance(val, np.ndarray) else round(float(val), 4)) for k_, val in a.items()}
                  for sd, a in fig.arms.items()},
         'lantern_H': {k_: round(float(val), 4) for k_, val in fig.lantern.items()},
         'placement_scan_max': {'lean_deg': best[0], 'H_m': best[1], 'note': '掃描範圍的上限 ⇒ 艏斜桅沒有擋到'},
         'placement_chosen': fig.place,
         'placement_scan': rows, 'knee_top_m': np.round(ctx['knee_top'], 3).tolist(),
         'note': 'H 掃到 0.05 m；手長是人體比例（設計），不是量的'}
    json.dump(v, open(os.path.join(design, 'verify_sheet_f1.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('best', best, 'reach L', round(fig.arms['left']['reach_needed'], 3), 'R', round(fig.arms['right']['reach_needed'], 3), 'max', fig.arms['left']['reach_max'])


if __name__ == '__main__':
    main()
