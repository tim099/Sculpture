# 紀念柱（君士坦丁柱、阿卡狄烏斯柱、查士丁尼騎像柱）：一個參數表 ⇒ 台階、基座、柱礎、柱身（一節一節＋接縫的環）、柱頭、頂上的東西。
#   座標（公尺）：柱軸 (cx, cy)；z 0 ＝ 地塊整平面。
#   參數表：steps: [[寬, 高], …]（由下往上的方台階）、pedestal: {w, h, mat, cornice}、base: {d, h}（圓柱礎）、
#     shaft: {d0, d1（頂徑）, h, drums: 節數, ring_h: 接縫環高（0 ⇒ 沒有）, mat, ring_mat, spiral: {turns, depth, band}（螺旋浮雕帶）}、
#     capital: {w, h, mat}、top: {kind: 'cross'|'rider'|'plinth', …}
import math
import numpy as np
from byz import MARBLE, PORPHYRY, BRONZE, GOLD, STONE, BRICK


def column(M, cx, cy, C, lay=1, top_lay=None):
    top_lay = lay if top_lay is None else top_lay
    z = 0.0
    for w, h in C.get('steps', []):
        M.add(M.box(cx - w / 2, cx + w / 2, cy - w / 2, cy + w / 2, z, z + h), C.get('step_mat', MARBLE), lay); z += h
    Pd = C.get('pedestal')
    if Pd:
        w = Pd['w']
        M.add(M.box(cx - w / 2, cx + w / 2, cy - w / 2, cy + w / 2, z, z + Pd['h']), Pd.get('mat', MARBLE), lay)
        cw = w + 2 * Pd.get('cornice', 0.2)
        M.add(M.box(cx - cw / 2, cx + cw / 2, cy - cw / 2, cy + cw / 2, z + Pd['h'] - 0.4, z + Pd['h']), Pd.get('mat', MARBLE), lay)
        M.add(M.box(cx - cw / 2, cx + cw / 2, cy - cw / 2, cy + cw / 2, z, z + 0.4), Pd.get('mat', MARBLE), lay)
        z += Pd['h']
    B = C.get('base')
    if B:
        M.add(M.cyl(cx, cy, B['d'] / 2, z, z + B['h']), B.get('mat', MARBLE), lay); z += B['h']
    S = C['shaft']
    z0, h = z, S['h']
    t = np.clip((M.Z - z0) / h, 0, 1)
    rad = S['d0'] / 2 + (S.get('d1', S['d0']) - S['d0']) / 2 * t
    r2 = (M.X - cx) ** 2 + (M.Y - cy) ** 2
    shaft = (r2 < rad ** 2) & (M.Z >= z0) & (M.Z < z0 + h)
    Sp = S.get('spiral')
    if Sp:                                                   # 螺旋浮雕帶：沿螺旋線往外凸一圈（band 公尺高、depth 公尺厚）
        ang = np.arctan2(M.Y - cy, M.X - cx)
        ph = ((M.Z - z0) / h * Sp['turns'] - ang / (2 * math.pi)) % 1.0
        ridge = (ph < Sp['band'] / (h / Sp['turns'])) & (r2 < (rad + Sp['depth']) ** 2) & (M.Z >= z0 + 0.5) & (M.Z < z0 + h - 0.5)
        shaft = shaft | ridge
    M.add(shaft, S.get('mat', PORPHYRY), lay)
    if S.get('ring_h') and S.get('drums', 1) > 1:
        dh = h / S['drums']
        for k in range(1, S['drums']):
            zr = z0 + k * dh
            M.add((r2 < (S['d0'] / 2 + 0.12) ** 2) & (M.Z >= zr - S['ring_h'] / 2) & (M.Z < zr + S['ring_h'] / 2), S.get('ring_mat', BRONZE), lay)
    z = z0 + h
    Cp = C.get('capital')
    if Cp:
        w = Cp['w']
        k = np.clip((M.Z - z) / Cp['h'], 0, 1)                # 柱頭：下圓上方，往上外擴
        rr = S.get('d1', S['d0']) / 2 + (w / 2 - S.get('d1', S['d0']) / 2) * k
        M.add((np.maximum(np.abs(M.X - cx), np.abs(M.Y - cy)) < rr) & (M.Z >= z) & (M.Z < z + Cp['h']), Cp.get('mat', MARBLE), lay)
        z += Cp['h']
    T = C.get('top') or {}
    if T.get('kind') == 'cross':
        hh, arm, t_ = T['h'], T['arm'], T.get('t', 0.4)
        if T.get('plinth'):
            pw, ph = T['plinth']
            M.add(M.box(cx - pw / 2, cx + pw / 2, cy - pw / 2, cy + pw / 2, z, z + ph), T.get('plinth_mat', MARBLE), top_lay); z += ph
        M.add(M.box(cx - t_ / 2, cx + t_ / 2, cy - t_ / 2, cy + t_ / 2, z, z + hh), T.get('mat', GOLD), top_lay)
        M.add(M.box(cx - arm / 2, cx + arm / 2, cy - t_ / 2, cy + t_ / 2, z + hh * 0.62, z + hh * 0.62 + t_), T.get('mat', GOLD), top_lay)
        z += hh
    elif T.get('kind') == 'rider':
        z = rider(M, cx, cy, z, T, top_lay)
    return z


def rider(M, cx, cy, z, T, top_lay):
    """騎像：銅馬（身、四腿、頭頸）＋騎者（身、頭、舉起的右手、左手的球十字）；面朝 T['dir']（度，從 +x 往 +y）；回傳像頂的 z。"""
    s = T['scale']; a = math.radians(T.get('dir', 90))
    ux, uy = math.cos(a), math.sin(a)
    u = (M.X - cx) * ux + (M.Y - cy) * uy                # 前後
    v = -(M.X - cx) * uy + (M.Y - cy) * ux               # 左右
    zz = M.Z - z
    if T.get('plinth'):
        pw, ph = T['plinth']
        M.add((np.abs(u) < pw / 2) & (np.abs(v) < pw * 0.35) & (zz >= 0) & (zz < ph), MARBLE, top_lay)
        zz = zz - ph; z += ph
    legs = np.zeros_like(u * v * zz, dtype=bool)
    for lu, lv in ((0.38, 0.13), (0.38, -0.13), (-0.38, 0.13), (-0.38, -0.13)):
        lift = 0.18 if (lu > 0 and lv > 0) else 0.0           # 右前腿抬起（Procopius）
        legs = legs | ((np.abs(u - lu * s) < 0.06 * s) & (np.abs(v - lv * s) < 0.06 * s) & (zz >= lift * s) & (zz < 0.55 * s))
    body = ((u / (0.55 * s)) ** 2 + (v / (0.2 * s)) ** 2 + ((zz - 0.68 * s) / (0.17 * s)) ** 2) <= 1
    neck = (u > 0.3 * s) & (u < 0.62 * s) & (np.abs(v) < 0.08 * s) & (zz > 0.7 * s) & (zz < 0.7 * s + (u - 0.3 * s) * 1.1)
    head = ((u - 0.68 * s) ** 2 / (0.14 * s) ** 2 + v ** 2 / (0.07 * s) ** 2 + (zz - 1.02 * s) ** 2 / (0.09 * s) ** 2) <= 1
    tail = (u < -0.5 * s) & (u > -0.66 * s) & (np.abs(v) < 0.04 * s) & (zz > 0.3 * s) & (zz < 0.75 * s)
    rider = (np.abs(u) < 0.13 * s) & (np.abs(v) < 0.12 * s) & (zz >= 0.8 * s) & (zz < 1.3 * s)
    rhead = (u ** 2 + v ** 2 + (zz - 1.42 * s) ** 2) <= (0.1 * s) ** 2
    crest = (np.abs(u) < 0.03 * s) & (np.abs(v) < 0.1 * s) & (zz >= 1.48 * s) & (zz < 1.62 * s)   # 頭上的羽飾（tufa）
    arm = (u > 0) & (u < 0.45 * s) & (np.abs(v + 0.14 * s) < 0.04 * s) & (np.abs(zz - (1.25 * s + u * 0.35)) < 0.04 * s)
    orb = ((u - 0.08 * s) ** 2 + (v - 0.2 * s) ** 2 + (zz - 1.25 * s) ** 2) <= (0.07 * s) ** 2
    ocross = (np.abs(u - 0.08 * s) < 0.015 * s + 0.1) & (np.abs(v - 0.2 * s) < 0.015 * s + 0.1) & (zz >= 1.3 * s) & (zz < 1.42 * s)
    parts = legs | body | neck | head | tail | rider | rhead | crest | arm
    if T.get('orb', True):                               # 1422–27 年寶球掉了（Majeska）⇒ 1453 年 orb: False
        parts = parts | orb | ocross
    M.add(parts, BRONZE, top_lay)
    z += 1.62 * s
    return z
