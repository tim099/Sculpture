# 夜燈號 船首像＋head knee（遊戲用 0.1 m／格，TASK-0538）：跟船頭一起設計 —— 米羅的維納斯只當形象參考
# 用法：python -I draft_head_figure.py <design 資料夾>
#   · 全部在船的格座標（0.1 m、跟船殼同一格）；子作品框原點 plan.sub_origin（關聯照這個 at 放回船上）。
#   · knee：側面多邊形（前緣 ＝ 母作品 stem_outer、接著沿她的背往上、上緣彎回船頭柱、收在艏斜桅下）× 寬 knee_half 格；船殼黑。
#   · 她：腳（衣褶）落在 knee 頂端 F、身體往前傾 lean_deg；身體部件在「她的座標」（x 前、y 她的左手、z 沿身體往上，公尺）。
#     她的左手 ＝ 左舷 ＝ 船 Y < 160。手臂與燈在船的座標定（燈照重力垂直掛）；頭比身體直、臉朝船前。
#   · 衣褶從腰流到 knee 上，再沿 cutwater 往下一段（白布蓋過黑 knee ⇒ 連成一體）。
#   ⇒ masks/head_figure.vox.txt（子作品座標）、masks/head_figure_ship.vox.txt（船座標，預覽落船殼草稿用）、verify_head_figure.json
import sys, os, json, math
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def ell(p, c, r):
    q = (p - np.asarray(c, float)) / np.asarray(r, float)
    k0 = np.linalg.norm(q, axis=-1)
    k1 = np.linalg.norm(q / np.asarray(r, float), axis=-1)
    return k0 * (k0 - 1) / np.maximum(k1, 1e-9)


def cap(p, a, b, ra, rb):
    a, b = np.asarray(a, float), np.asarray(b, float)
    pa, ba = p - a, b - a
    t = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return np.linalg.norm(pa - t[..., None] * ba, axis=-1) - (ra + (rb - ra) * t)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


class Frame:
    """她的座標（公尺）⇄ 船的座標（公尺，原點在船格 (0,0,0) 的角；y_ship ＝ 船 Y × 0.1）"""
    def __init__(s, F_cells, lean_deg, m):
        s.F = np.array(F_cells, float) * m
        s.t = math.radians(lean_deg)
        s.yc = F_cells[1] * m

    def to_ship(s, b):
        b = np.asarray(b, float)
        c, sn = math.cos(s.t), math.sin(s.t)
        x = b[..., 0] * c + b[..., 2] * sn
        z = -b[..., 0] * sn + b[..., 2] * c
        y = -b[..., 1]                                     # 她的左手 ＝ 左舷 ＝ 船 Y 小
        return np.stack([s.F[0] + x, s.F[1] + y, s.F[2] + z], -1)

    def to_body(s, p):
        c, sn = math.cos(s.t), math.sin(s.t)
        dx, dy, dz = p[..., 0] - s.F[0], p[..., 1] - s.F[1], p[..., 2] - s.F[2]
        return np.stack([dx * c - dz * sn, -dy, dx * sn + dz * c], -1)


def main():
    design = sys.argv[1]
    D = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    m = D['meters_per_voxel']
    O = np.array(D['sub_origin'])
    S = np.array(D['sub_size'])
    fr = Frame(D['F_cells'], D['lean_deg'], m)
    # 船格中心（公尺）
    g = [(O[i] + np.arange(S[i]) + 0.5) * m for i in range(3)]
    PX, PY, PZ = np.meshgrid(*g, indexing='ij')
    p = np.stack([PX, PY, PZ], -1)                         # 船座標（公尺）
    b = fr.to_body(p)                                      # 她的座標
    Bd = D['body']
    k = D['k']
    # ── 身體（她的座標）
    skin = ell(b, *Bd['hips'])
    for n in ('waist', 'ribcage'):
        skin = smin(skin, ell(b, *Bd[n]), k)
    for c, r in Bd['breasts']:
        skin = smin(skin, np.linalg.norm(b - np.asarray(c), axis=-1) - r, k * 0.4)
    sh = Bd['shoulders']
    skin = smin(skin, cap(b, sh['R'], sh['L'], sh['r'], sh['r']), k)
    ne = Bd['neck']
    skin = smin(skin, cap(b, ne['a'], ne['b'], ne['r_base'], ne['r']), k * 0.6)
    # ── 頭（船座標：比身體直、臉朝船前）
    Hd = D['head']
    hc = fr.to_ship(np.array(Hd['centre_body']))
    head = ell(p, hc, Hd['r'])
    for n in ('nose', 'chin'):
        f = Hd[n]
        head = smin(head, np.linalg.norm(p - (hc + np.array(f['off_ship'])), axis=-1) - f['r'], 0.04)
    skin = smin(skin, head, k * 0.5)
    # ── 手（船座標）
    arms = {}
    for side, A in D['arms'].items():
        Sh = fr.to_ship(np.array(A['shoulder_body']))
        if 'upper_dir_ship' in A:
            E = Sh + unit(A['upper_dir_ship']) * A['upper_len']
        else:
            E = Sh + (fr.to_ship(np.array(A['upper_dir_body'])) - fr.to_ship(np.zeros(3))) / np.linalg.norm(A['upper_dir_body']) * A['upper_len']
        if 'fore_dir_ship' in A:
            fd = unit(A['fore_dir_ship'])
        else:
            T_ = fr.to_ship(np.array(A['hand_target_body']))
            fd = unit(T_ - E)
        W = E + fd * A['fore_len']
        G = W + fd * A['hand_len']
        a = cap(p, Sh, E, A['r'][0], A['r'][1])
        a = smin(a, cap(p, E, W, A['r'][1], A['r'][2]), 0.05)
        a = smin(a, np.linalg.norm(p - G, axis=-1) - A['fist_r'], 0.05)
        skin = smin(skin, a, k * 0.5)
        arms[side] = {'shoulder': Sh, 'elbow': E, 'wrist': W, 'grip': G}
    # ── 衣褶（她的座標的裙＋腰上的布捲＋往前的左膝；垂直大褶）＋沿 cutwater 往下流的布
    Dr = D['drape']
    z = b[..., 2]
    t = np.clip(z / Dr['top_z'], 0, 1)
    rx = Dr['r_bottom'][0] + (Dr['r_top'][0] - Dr['r_bottom'][0]) * t
    ry = Dr['r_bottom'][1] + (Dr['r_top'][1] - Dr['r_bottom'][1]) * t
    q = np.stack([(b[..., 0] - Dr['centre_x']) / rx, b[..., 1] / ry], -1)
    rad = np.linalg.norm(q, axis=-1)
    az = np.arctan2(q[..., 1], q[..., 0])
    fold = Dr['fold_depth'] * np.sin(az * Dr['folds'] + z * Dr['fold_twist']) * np.clip((Dr['top_z'] - 0.3 - z) / 0.5, 0, 1)
    skirt = (rad - 1) * np.minimum(rx, ry) + fold
    skirt = np.maximum(skirt, z - Dr['top_z'])
    skirt = np.maximum(skirt, -z - Dr['below_feet'])
    skirt = smin(skirt, ell(b, *Dr['knee_L']), 0.15)
    zr = Dr['roll']['z'] + Dr['roll']['tilt'] * b[..., 1]
    ring = np.sqrt(np.maximum((rad - 1) * np.minimum(rx, ry), 0) ** 2 + (z - zr) ** 2) - Dr['roll']['r']
    ring = np.where(rad < 1.3, ring, 9)
    cloth = smin(skirt, ring, 0.06)
    fl = np.array(D['drape_flow_cells'], float) * m
    for (a_, b_), (ra, rb) in zip(zip(fl[:-1], fl[1:]), zip(D['drape_flow_r'][:-1], D['drape_flow_r'][1:])):
        cloth = smin(cloth, cap(p, a_, b_, ra, rb), 0.08)
    # 頭髮（船座標）：頭頂殼＋髮髻
    Hr = D['hair']
    hair = np.maximum(ell(p, hc + np.array(Hr['shell_off_ship']), Hr['shell_r']), (hc[2] + Hr['hairline_dz']) - p[..., 2] + Hr['back_drop'] * np.clip(-(p[..., 0] - hc[0]), 0, None))
    hair = np.minimum(hair, np.linalg.norm(p - (hc + np.array(Hr['bun_off_ship'])), axis=-1) - Hr['bun_r'])
    cloth = np.minimum(cloth, hair)
    # ── knee（側面多邊形 × 寬）
    Kn = D['knee']
    img = Image.new('L', (int(S[0]), int(S[2])), 0)
    ImageDraw.Draw(img).polygon([(x - O[0], z_ - O[2]) for x, z_ in Kn['profile_XZ']], fill=255)
    prof = np.asarray(img).T > 0                             # [X, Z]
    Yi = O[1] + np.arange(S[1])
    knee = prof[:, None, :] & (np.abs(Yi - 160)[None, :, None] <= Kn['half_width'])
    # ── 合起來
    fig = (skin <= 0) | (cloth <= 0)
    solid = fig | knee
    lab, n = ndimage.label(solid)
    sizes = np.bincount(lab.ravel())[1:]
    keep = lab == (sizes.argmax() + 1)
    C = D['colors']
    col = np.where(knee & ~fig, C['knee'], np.where(cloth <= skin, C['cloth'], C['skin']))
    # 不蓋船殼已有的格（船頭柱、gripe）：母作品現況
    hull = set()
    lst = D['hull_list']
    if os.path.exists(lst):
        for ln in open(lst, encoding='utf-8'):
            if ln.strip() and ln[0] != '#':
                x, y, z_ = (int(v) for v in ln.split(',')[:3])
                if O[0] <= x < O[0] + S[0] and O[1] <= y < O[1] + S[1] and O[2] <= z_ < O[2] + S[2]:
                    hull.add((x - O[0], y - O[1], z_ - O[2]))
    cells = [tuple(c) for c in np.argwhere(keep)]
    overlap = sum(1 for c in cells if c in hull)
    cells = [c for c in cells if c not in hull]
    os.makedirs(os.path.join(design, 'masks'), exist_ok=True)
    with open(os.path.join(design, 'masks', 'head_figure.vox.txt'), 'w', encoding='utf-8', newline='\n') as f1, \
            open(os.path.join(design, 'masks', 'head_figure_ship.vox.txt'), 'w', encoding='utf-8', newline='\n') as f2:
        f1.write('# 夜燈號 船首像＋head knee（子作品座標；關聯 at ＝ %s）\n' % ','.join(str(int(v)) for v in O))
        f2.write('# 夜燈號 船首像＋head knee（船座標，預覽用）\n')
        for (i, j, k_) in cells:
            c_ = col[i, j, k_]
            f1.write('%d,%d,%d,%d\n' % (i, j, k_, c_))
            f2.write('%d,%d,%d,%d\n' % (i + O[0], j + O[1], k_ + O[2], c_))
    toc = lambda v: [round(float(x) / m, 2) for x in v]
    ver = {'cells': len(cells), 'overlap_hull_skipped': overlap, 'components_before_keep': int(n), 'dropped': int(solid.sum() - keep.sum()),
           'colors': {int(a): int(c) for a, c in zip(*np.unique([col[c] for c in cells], return_counts=True))},
           'arms_cells': {s_: {k2: toc(v) for k2, v in a.items()} for s_, a in arms.items()},
           'head_centre_cells': toc(hc), 'crown_Z': round(float((hc[2] + Hd['r'][2]) / m), 1)}
    gz = arms['left']['grip']
    bs = D['bowsprit']
    ver['grip_below_bowsprit_cells'] = round(bs['Z0'] + (gz[0] / m - bs['X0']) * math.tan(math.radians(bs['deg'])) - gz[2] / m, 1)
    json.dump(ver, open(os.path.join(design, 'verify_head_figure.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(ver, ensure_ascii=False))


if __name__ == '__main__':
    main()
