# F3 v2 頭（TASK-0538 船首像）：距離場（SDF）部件組 ⇒ 取代 F3 v1 那顆蛋形頭
# 用法：python -I draft_head.py <design 資料夾>     （先跑 draft_f3.py ⇒ f3.npz）
#   · 頭的區域座標（單位 ＝ 頭高 h，頭頂到下巴）：u 往前、v 往她的左手邊、w 往上；原點 ＝ 頭的中心（plan head.origin_body）。
#   · 部件：顱、臉、下顎、下巴、顴骨、眉弓、鼻（楔＋鼻翼）、上下唇、眼球（＋眼窩）、頭髮殼（髮際線＋波浪溝）、髮髻、脖子。
#     平滑聯集 smin(k)；眼窩、嘴縫、頭髮溝用減的。全部參數在 plan.json head。
#   · 落到身體：清掉 F3 身體在「頭的範圍」裡、下巴以上的格，再放上頭（脖子往下接到身體）。
#   ⇒ f3v2.npz（body＝新身體、arms、lantern）、verify_head.json
import sys, os, json, math
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def ell(p, c, r):
    """橢球的近似距離（單位 h）"""
    q = (p - np.asarray(c)) / np.asarray(r)
    k0 = np.linalg.norm(q, axis=-1)
    k1 = np.linalg.norm(q / np.asarray(r), axis=-1)
    return k0 * (k0 - 1) / np.maximum(k1, 1e-6)


def capsule(p, a, b, r):
    a, b = np.asarray(a, float), np.asarray(b, float)
    pa, ba = p - a, b - a
    t = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return np.linalg.norm(pa - t[..., None] * ba, axis=-1) - r


def head_sdf(p, P):
    k = P['smooth_k']
    E = lambda n: ell(p, *P['ell'][n])
    d = smin(E('cranium'), E('face'), k)
    d = smin(d, E('jaw'), k)
    d = smin(d, E('chin'), k * 0.6)
    for n in ('cheek_L', 'cheek_R'):
        d = smin(d, E(n), k * 0.7)
    b = P['brow']
    d = smin(d, capsule(p, b['a'], b['b'], b['r']), k * 0.5)
    # 鼻：沿鼻樑一串變粗的球（楔）＋鼻翼
    n_ = P['nose']
    root, tip = np.array(n_['root']), np.array(n_['tip'])
    for t in np.linspace(0, 1, 12):
        c = root + (tip - root) * t
        r = n_['r_root'] + (n_['r_tip'] - n_['r_root']) * t
        d = smin(d, ell(p, c, (r * 0.8, r, r * 0.9)), k * 0.35)
    for s in (1, -1):
        c = np.array(n_['ala']) * (1, s, 1)
        d = smin(d, ell(p, c, n_['ala_r']), k * 0.3)
    for n in ('lip_upper', 'lip_lower'):
        d = smin(d, E(n), k * 0.25)
    # 嘴縫（減）
    m = P['mouth_slit']
    d = np.maximum(d, -ell(p, m['c'], m['r']))
    # 眼窩（減）＋眼球（加）
    for s in (1, -1):
        so = P['eye']
        c = np.array(so['socket_c']) * (1, s, 1)
        d = np.maximum(d, -ell(p, c, so['socket_r']))
        d = np.minimum(d, ell(p, np.array(so['ball_c']) * (1, s, 1), so['ball_r']))
    # 脖子
    ne = P['neck']                                           # 脖子往下越來越粗（斜方肌的坡）—— 粗細不變的膠囊插在平頂軀幹上會有一圈台階
    a_, b_ = np.array(ne['a']), np.array(ne['b'])
    for t in np.linspace(0, 1, 16):
        c = a_ + (b_ - a_) * t
        r = ne['r'] + (ne['r_base'] - ne['r']) * t ** ne['flare_pow']
        d = smin(d, np.linalg.norm(p - c, axis=-1) - r, k)
    return d


def hair_sdf(p, P):
    H = P['hair']
    shell = ell(p, *H['shell'])
    # 髮際線：前面（臉）那一側、低於髮際的不算頭髮
    u, v, w = p[..., 0], p[..., 1], p[..., 2]
    hl = H['hairline']
    above = w - (hl['w_front'] - hl['slope_back'] * np.clip(hl['u_front'] - u, 0, None) - hl['side_drop'] * (np.abs(v) / 0.4) ** 2)
    d = np.maximum(shell, -above)                            # 髮際線以下（臉、後頸）不是頭髮；往後腦越來越低
    # 波浪溝：往後梳的髮絲（沿 w 的波浪線，隨 v 起伏）
    g = H['grooves']
    th = np.arctan2(w - g['axis_w'], v)                      # 繞前後軸（u）的角：同一個 θ 的線從額頭往後梳到髮髻（經線）
    phase = th / (2 * math.pi) * g['strands'] + g['wave_amp'] * np.sin(u * g['wave_freq'] * 2 * math.pi)
    groove = (np.sin(phase * 2 * math.pi) > g['cut']) & (d < 0) & (d > -g['depth'])
    d = np.where(groove, 0.01, d)
    for c, r in H['bun']:
        d = np.minimum(d, ell(p, c, r))
    return d


def main():
    design = sys.argv[1]
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    P = plan['head']
    d = np.load(os.path.join(design, 'f3.npz'))
    V, arms, lant, lo, N = d['body'].copy(), d['arms'], d['lantern'], d['lo'], int(d['N'])
    h = P['h_H']
    o = np.array(P['origin_body'])
    yaw, tilt = math.radians(P['yaw_deg']), math.radians(P['tilt_deg'])
    # 頭的範圍（身體座標）
    R = 0.75 * h
    Rlo = np.array([R, R, P['box_down_h'] * h])            # 往下延到肩膀（v 只到 0.75 h ⇒ 脖子的喇叭口在框底被硬切一刀）
    i0 = np.maximum(np.floor((o - Rlo - lo) * N).astype(int), 0)
    i1 = np.minimum(np.ceil((o + R - lo) * N).astype(int), np.array(V.shape))
    g = [lo[k] + (np.arange(i0[k], i1[k]) + 0.5) / N for k in range(3)]
    X, Y, Z = np.meshgrid(*g, indexing='ij')
    q = np.stack([X - o[0], Y - o[1], Z - o[2]], -1) / h
    # 身體座標 → 頭的區域座標：先轉回 yaw（繞 w）、再轉回 tilt（繞 v，正 ＝ 低頭）
    cu, su = math.cos(yaw), math.sin(yaw)
    u1 = cu * q[..., 0] + su * q[..., 1]
    v1 = -su * q[..., 0] + cu * q[..., 1]
    ct, st = math.cos(tilt), math.sin(tilt)
    u2 = ct * u1 - st * q[..., 2]
    w2 = st * u1 + ct * q[..., 2]
    p = np.stack([u2, v1, w2], -1)
    dh = head_sdf(p, P)
    dhair = hair_sdf(p, P)
    head = (dh <= 0) | (dhair <= 0)
    sub = (slice(i0[0], i1[0]), slice(i0[1], i1[1]), slice(i0[2], i1[2]))
    # 清掉舊頭：頭的範圍裡、z 在下巴之上（plan head.clear_above_z）
    cr = np.array(P['clear_radii']) * h                     # 只清頭附近那顆橢球裡的（v1 清整個方框 ⇒ 左肩頂與斜方肌被切平）
    clear = (Z > P['clear_above_z']) & ((((X - o[0]) / cr[0]) ** 2 + ((Y - o[1]) / cr[1]) ** 2 + ((Z - o[2]) / cr[2]) ** 2) <= 1)
    clear |= Z > P['clear_all_above_z']                       # 頭搬過位置之後，舊頭在橢球外的那半邊也要清（z 0.88 以上只有頭）
    clear |= (Z > P['clear_above_z']) & (Y < P['clear_side_y_below'])   # 舊頭在 z 0.865–0.88 剩下的那一層會黏在脖子上變成平台（左肩在 y > 0.04，不清）
    old = V[sub] & clear
    V[sub] &= ~clear
    V[sub] |= head
    lab, n = ndimage.label(V | arms)
    sizes = np.bincount(lab.ravel())[1:]
    ver = {'head_cells': int(head.sum()), 'cleared_old_head': int(old.sum()), 'components': int(n),
           'sizes_top5': sorted(sizes.tolist(), reverse=True)[:5], 'h_H': h, 'h_m': h * plan['placement']['H_m'],
           'hair_cells': int(((dhair <= 0) & (dh > 0)).sum())}
    np.savez_compressed(os.path.join(design, 'f3v2.npz'), body=V, arms=arms, lantern=lant, lo=lo, N=N)
    json.dump(ver, open(os.path.join(design, 'verify_head.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(ver)


if __name__ == '__main__':
    main()
