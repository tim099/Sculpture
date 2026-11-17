"""威尼斯 galeazza（TASK-1302）步驟 11：舵（含舵柄）、錨（Ship_Helm §9.8.1、Ship_Game §9 anchor）。

- 舵（子作品 -rudder，跟組裝件同框；外部模型 kind=rudder＋spin）：槳帆船的艉柱很斜（本船艉柱後緣 z 12 ⇒ z 36 從 x 77 退到 x 53），
  舵葉前緣貼著艉柱後緣一層一層走（前緣 ＝ 艉柱後緣 −1），弦長 z 2 的 14 格（1.4 m）收到 z 28 的 6 格，厚 3 格；
  z 29–38 是舵桿（弦 3 格），舵頭在艉廊懸出那一層（z 39）底下；舵柄 z 37–38 從舵桿往船頭穿過艉封板的舵柄口、伸進艉樓下艙到 x 72（約 2.2 m）。
  舵柄口：艉封板在舵柄經過那一段開 7 格寬（|dy| ≤ 3）、z 36–39 —— 滿舵時舵柄左右擺得開（masks/upper/hull_cut_02.vox.txt，從船殼刻）。
  鉸鏈照 Ship_Helm 的量法：每一層取前緣最靠船頭那一格的格角（x ＋ 1）⇒ 擬合 x ＝ a ＋ b·z（只丟舵柄那兩層；艉柱是彎的，殘差記在 verify）⇒
  axis ＝ normalize(b, 0, 1)、hinge ＝（a ＋ b·z_low, 160.5, z_low）。舵頭 stock-top ＝ 舵桿最高那層靠艉封板那一格。
- 錨（共用四爪錨 kotoko-fusta-01m-anchor-grapnel，0.05 m）：兩舷各一隻掛在圓形艏樓外牆（艏樓中心算起 64° 方向、牆外 3 格），
  環 ring 在 z 48、錨冠 crown 在水線上；錨爪沿著牆的切線。hawse ＝ 牆面上、艏樓下層甲板那一高度（meta hawse）。
  ⚠ 尺寸是設計：加萊賽的錨重沒查到（scale 0.8 ⇒ 約 1.9 m 高；meadow galea 用 0.65）。
輸出 masks/helm/rudder.vox.txt、masks/upper/hull_cut_02.vox.txt、helm_meta.json、verify_helm.json。
"""
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from lines import load_plan

RUDDER = 68
GRAPNEL = dict(work='kotoko-fusta-01m-anchor-grapnel', size=(20, 20, 24), pivot=(9.5, 9.5, 23.5), ring=(9, 9, 23), crown=(9, 9, 0))


def load(occ, p, val=None):
    a = np.loadtxt(p, delimiter=',', dtype=np.int32, ndmin=2)
    occ[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3] if val is None else val


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    plan = load_plan(D)
    NX, NY, _ = plan['space']['hull']
    NZ = 360
    YC = plan['space']['yc']
    lay = {k: v['v'] for k, v in plan['layout'].items()}
    WL = plan['waterline']['z']
    hull = np.zeros((NX, NY, NZ), np.uint8)
    load(hull, D / 'masks/hull/hull_01.vox.txt')
    load(hull, D / 'masks/upper/upper_01.vox.txt')
    load(hull, D / 'masks/upper/hull_cut_01.vox.txt', 0)
    occ = hull.copy()
    for sub in ('decks', 'deco', 'rig', 'hold'):
        for p in sorted((D / 'masks' / sub).glob('*.vox.txt')):
            if p.name == 'hatch.vox.txt':
                continue                       # 艙蓋是局部座標
            load(occ, p)

    def post_aft(z):
        xs = np.nonzero(hull[:150, YC, z])[0]
        return int(xs[0]) if len(xs) else None

    # ── 舵 ──
    Z0, ZB, ZS = 2, 28, 38                     # 舵底、舵葉頂、舵桿頂
    C0, C1, CS = 14, 6, 3
    TZ = (37, 38)
    TX1 = 72
    rud = {}
    le = {}
    for z in range(Z0, ZS + 1):
        L = post_aft(z) - 1
        le[z] = L
        c = round(C0 + (C1 - C0) * (z - Z0) / (ZB - Z0)) if z <= ZB else CS
        for x in range(L - c + 1, L + 1):
            for y in range(YC - 1, YC + 2):
                rud[(x, y, z)] = RUDDER
    for z in TZ:
        for x in range(le[z] - CS + 1, TX1 + 1):
            for y in range(YC - 1, YC + 2):
                rud[(x, y, z)] = RUDDER
    # 舵柄口：艉封板在舵柄經過那一段（x ≤ 舵柄頭、z 36–39、|dy| ≤ 3）的船殼格刻掉
    cut = {}
    for x in range(le[TZ[0]], 80):
        for y in range(YC - 3, YC + 4):
            for z in range(TZ[0] - 1, TZ[1] + 2):
                if hull[x, y, z]:
                    cut[(x, y, z)] = int(hull[x, y, z])
    occ2 = occ.copy()
    for k in cut:
        occ2[k] = 0
    clash = sorted(k for k in rud if occ2[k])
    # 鉸鏈：每一層前緣最靠船頭那一格的格角
    zs = np.array(sorted({z for (_, _, z) in rud}))
    fx = np.array([max(x for (x, y, zz) in rud if zz == z) + 1 for z in zs], float)
    # Ship_Helm 的「丟掉離線超過 1.5 格的層」是為了丟舵柄那幾層；本船艉柱是彎的，照那條規則反覆丟會丟到只剩 9 層 ⇒
    # 直接丟舵柄那兩層（TZ）、其餘一次擬合，殘差照實記（滿舵時舵葉前緣離艉柱會差這麼多 —— 只是畫面）。
    keep = ~np.isin(zs, TZ)
    b, a = np.polyfit(zs[keep], fx[keep], 1)
    res = np.abs(fx - (a + b * zs))
    z_low = int(zs[keep].min())
    n = math.hypot(b, 1.0)
    axis = [round(b / n, 4), 0.0, round(1.0 / n, 4)]
    hinge = [round(a + b * z_low, 2), YC + 0.5, float(z_low)]
    stock_top = [le[ZS], YC, ZS]
    # 舵柄口一定要讓舵柄過得去：舵柄在船殼裡的格 ⇒ 都在刻掉的格裡
    tiller_in_hull = [k for k in rud if hull[k] and k not in cut]
    near_stern = sum(1 for dx in range(-8, 9) for dy in range(-8, 9) for dz in range(-8, 9)
                     if occ2[stock_top[0] + dx, stock_top[1] + dy, stock_top[2] + dz])

    # ── 錨 ──
    bc = lay['bow_castle']
    cx, R = bc['cx'], bc['r']
    sc = 0.8
    anchors = {}
    for side, sgn in (('S', 1), ('P', -1)):
        ang = math.radians(64)
        rx, ry = math.cos(ang), sgn * math.sin(ang)
        ring = [cx + (R + 3) * rx, YC + 0.5 + (R + 3) * ry, 48.0]
        yaw = -26 if sgn > 0 else 26                       # 錨爪（來源 x 方向）沿牆的切線
        hawse = [int(cx + (R - 1) * rx), int(YC + (R - 1) * ry), 40]
        # 外框（不轉時的框夠用：轉 26° 只會更窄的那一邊進牆 ⇒ 用半徑量最靠牆那一點）
        h = GRAPNEL['size'][2] * sc
        crown_z = ring[2] - (GRAPNEL['pivot'][2] - GRAPNEL['crown'][2]) * sc
        half = GRAPNEL['size'][0] / 2 * sc
        # 錨身上每一格離艏樓中心的水平距離（取錨爪那條切線上的點）最小值要大於外牆半徑
        tx, ty = -ry, rx
        dmin = min(math.hypot(ring[0] + t * tx - cx, ring[1] + t * ty - YC) for t in np.linspace(-half, half, 21))
        body = 0
        for t in np.linspace(-half, half, 9):
            for zz in np.linspace(crown_z, ring[2], 9):
                q = (int(ring[0] + t * tx), int(ring[1] + t * ty), int(zz))
                body += int(occ2[q] > 0)
        hawse_solid = bool(occ2[tuple(hawse)])
        anchors[f'錨-{side}'] = dict(at=[round(v, 2) for v in ring], rotate=[0, 0, yaw], scale=sc, hawse=hawse,
                                     crown_z=round(crown_z, 2), above_waterline=round(crown_z - WL, 2), r_min=round(dmin, 2),
                                     wall_r=R, body_cells_in_ship=body, hawse_on_wall=hawse_solid, height_m=round(h * 0.1, 2))

    out = D / 'masks/helm'
    out.mkdir(parents=True, exist_ok=True)
    body = ''.join(f'{x},{y},{z},{c}\n' for (x, y, z), c in sorted(rud.items())).encode('ascii')
    (out / 'rudder.vox.txt').write_bytes(body)
    cbody = ''.join(f'{x},{y},{z},{c}\n' for (x, y, z), c in sorted(cut.items())).encode('ascii')
    (D / 'masks/upper/hull_cut_02.vox.txt').write_bytes(cbody)
    meta = dict(
        rudder=dict(kind='rudder', hinge_x=hinge[0], hinge_y=hinge[1], hinge_z=hinge[2], axis_x=axis[0], axis_y=0, axis_z=axis[2],
                    max_deg=30, turn_axis='hinge', spin='rudder', spin_k=30, spin_min=-30, spin_max=30, spin_lag=0.3),
        pivot=hinge, stock_top=stock_top,
        anchors={k: dict(at=v['at'], rotate=v['rotate'], scale=v['scale'], hawse=v['hawse']) for k, v in anchors.items()},
        grapnel=GRAPNEL,
    )
    stats = dict(rudder_cells=len(rud), clash=len(clash), clash_sample=clash[:5], hull_cut=len(cut), tiller_in_hull_uncut=len(tiller_in_hull),
                 fit=dict(a=round(a, 3), b=round(b, 4), layers=len(zs), kept=int(keep.sum()), dropped=[int(z) for z in zs[~keep]],
                          max_res_kept=round(float(res[keep].max()), 2), rake_deg=round(math.degrees(math.atan(-b)), 1)),
                 hinge=hinge, axis=axis, stock_top=stock_top, stern_cells_within_8=near_stern,
                 blade=dict(z=[Z0, ZB], chord=[C0, C1], below_waterline_layers=sum(1 for z in zs if z < WL)),
                 anchors=anchors,
                 sha16=dict(rudder=hashlib.sha256(body).hexdigest()[:16], hull_cut_02=hashlib.sha256(cbody).hexdigest()[:16]))
    (D / 'helm_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (D / 'verify_helm.json').write_text(json.dumps(stats, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == '__main__':
    main()
