# F3 v2 手（TASK-0538 船首像）：上臂＋前臂＋握拳的手（手掌、四指三節、拇指）⇒ 取代 F2／F3 v1 的圓管末端
# 用法：python -I draft_hands.py <design 資料夾>      （先跑 draft_f3.py、draft_head.py ⇒ f3v2.npz）
#   · f ＝ 前臂方向；a ＝ 握的軸（左手：水平、垂直於 f ⇒ 握提燈的提環；右手：同）；n ＝ 掌心那一側（左手朝下、右手朝身體）。
#   · 手掌從腕沿 f 走 palm_len；指根四個沿 a 排開；每指：沿 f → 轉向 n → 轉回 −f（握成拳、中間留握東西的洞）。
#   ⇒ f3v2h.npz（arms 換掉）、verify_hands.json
import sys, os, json
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from draft_sheet_f1 import Figure, unit   # noqa: E402
from draft_body import seg_capsule   # noqa: E402


def main():
    design = sys.argv[1]
    fig = Figure(design)
    Hp = fig.P['hands']
    d = np.load(os.path.join(design, 'f3v2.npz'))
    V, lant, lo, N = d['body'], d['lantern'], d['lo'], int(d['N'])
    arms = np.zeros_like(V)
    R = fig.P['arms']['radius_H']
    ver = {}
    for side in ('left', 'right'):
        A = fig.arms[side]
        S, E, W = A['S'], A['E'], A['W']
        seg_capsule(arms, lo, N, S, E, R['shoulder'], R['elbow'])
        seg_capsule(arms, lo, N, E, W, R['elbow'], R['wrist'])
        f = unit(W - E)
        a = np.cross(f, [0, 0, 1.0])
        a = unit(a) if np.linalg.norm(a) > 1e-3 else np.array([0, 1.0, 0])
        n = unit(np.cross(a, f))
        want = np.array(Hp[side]['palm_faces'], float)
        if n @ want < 0:
            n = -n
        pl, pw, pt = Hp['palm_len'], Hp['palm_width'], Hp['palm_thick']
        # 手掌：一排平行的膠囊（沿 f），寬 pw、厚 pt
        for s in np.linspace(-0.5, 0.5, 5):
            off = a * s * (pw - pt)
            seg_capsule(arms, lo, N, W + off, W + f * pl + off, pt / 2, pt / 2)
        fr = Hp['finger_r']
        L1, L2, L3 = Hp['finger_seg']
        tips = []
        for i, s in enumerate(np.linspace(-0.5, 0.5, 4)):
            k = W + f * pl + a * s * (pw - fr * 2)
            sc = Hp['finger_scale'][i]
            p1 = k + f * L1 * sc
            p2 = p1 + n * L2 * sc
            p3 = p2 - f * L3 * sc
            for P0, P1 in ((k, p1), (p1, p2), (p2, p3)):
                seg_capsule(arms, lo, N, P0, P1, fr * (0.95 if sc > 0.9 else 0.85), fr * 0.85)
            tips.append(p3.tolist())
        # 拇指：從腕旁（−a 那側）斜過來扣在食指外面
        t0 = W + f * 0.015 - a * pw * 0.45
        t1 = t0 + f * Hp['thumb_len'] * 0.5 + n * Hp['thumb_len'] * 0.45
        t2 = t1 + a * Hp['thumb_len'] * 0.45 + f * Hp['thumb_len'] * 0.15
        seg_capsule(arms, lo, N, t0, t1, fr * 1.1, fr)
        seg_capsule(arms, lo, N, t1, t2, fr, fr * 0.9)
        ver[side] = {'f': np.round(f, 3).tolist(), 'a': np.round(a, 3).tolist(), 'n': np.round(n, 3).tolist(), 'finger_tips': np.round(tips, 4).tolist()}
    lab, ncomp = ndimage.label(V | arms)
    sizes = np.bincount(lab.ravel())[1:]
    ver.update({'arm_cells': int((arms & ~V).sum()), 'components': int(ncomp), 'sizes_top3': sorted(sizes.tolist(), reverse=True)[:3]})
    np.savez_compressed(os.path.join(design, 'f3v2h.npz'), body=V, arms=arms, lantern=lant, lo=lo, N=N)
    json.dump(ver, open(os.path.join(design, 'verify_hands.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(ver)


if __name__ == '__main__':
    main()
