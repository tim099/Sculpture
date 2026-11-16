"""通用部件：威尼斯砲六種（gun ven20／ven30c／ven14／ven30／ven3／ven14p；0.05 m）—— 威尼斯加萊賽戰船（TASK-1302）做的，下一艘要這幾種砲的船直接引用。

- Tim 2026-11-16「Build new gun types」；Ship_Guns §2.2：砲只跟同一種砲共用模型 ⇒ 每種一件，⛔ 不拿別的口徑縮。
- 結構出處：pinnacle-patache-01m/design/draft_gun4l.py（Part、tube、wheel、兩軸四輪海用砲架）—— 砲架尺寸照砲尾半徑 ÷ 4 磅砲尾半徑（0.16 m）放大；
  petriera 是叉架迴旋砲（Furttenbach 1629：舷側小砲在槳之間的鐵叉架上），結構照 apex-one-reale-01m 的 pierrier（立柱、U 叉、砲身、尾把手）自己畫。
- 尺寸與遊戲數值在 plan.json guns.types（〔估〕：彈重照磅，砲管長照倍口徑分類）；顏色：青銅砲管 168、箍 208（同 meadow 的 corsiero）、砲架 132、楔 136、鐵 73。
- 座標（Ship_Guns §4.1）：x 沿船長（砲軸在 x 中線）、y ＝ 砲口方向、z 0 ＝ 甲板面那一層。
輸出 masks/guns/gun-<代碼>.vox.txt、verify_guns_venice.json（框、固定點、pivot、元件、空腔、x 鏡像差）。
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy import ndimage

D = Path(__file__).resolve().parent
MPV = 0.05
BRONZE, BAND, CARR, QUOIN, IRON = 168, 208, 132, 136, 73


class Part:
    def __init__(s, W, L, H):
        s.cells, s.W, s.L, s.H = {}, W, L, H

    def put(s, x, y, z, c, over=False):
        if not (0 <= x < s.W and 0 <= y < s.L and 0 <= z < s.H):
            raise ValueError(('框外', x, y, z))
        if (x, y, z) in s.cells and not over:
            return
        s.cells[(x, y, z)] = c

    def box(s, x0, x1, y0, y1, z0, z1, c, over=False):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    s.put(x, y, z, c, over)

    def tube(s, cx, cz, y0, prof, cols, bore_r=0.0, bore_depth=0.0):
        """沿 y 的旋轉體；prof ＝ [(s, r)] 分段線性；cols(t) ⇒ 顏色；砲口那一段挖空。"""
        smax = prof[-1][0]
        for y in range(s.L):
            t = y + 0.5 - y0
            if not (0 <= t < smax):
                continue
            r = None
            for (a, ra), (b, rb) in zip(prof, prof[1:]):
                if a <= t < b:
                    r = ra + (rb - ra) * (t - a) / (b - a)
                    break
            if r is None:
                continue
            R = int(math.ceil(r)) + 1
            for dx in range(-R, R + 1):
                for dz in range(-R, R + 1):
                    d = math.hypot(dx, dz)
                    if d <= r + 1e-9:
                        if bore_r > 0 and t > smax - bore_depth and d <= bore_r:
                            s.cells.pop((cx + dx, y, cz + dz), None)
                            continue
                        s.put(cx + dx, y, cz + dz, cols(t))

    def wheel(s, cx, cy, cz, r, c):
        for y in range(s.L):
            for z in range(s.H):
                if math.hypot(y + 0.5 - cy, z + 0.5 - cz) <= r:
                    s.put(cx, y, z, c, True)


def profile(T):
    """砲管外形（格）：base ring、第一段、箍、第二段、chase、muzzle swell。cannone 短粗、colubrina 長細、falcone 細長。"""
    L = T['len_m'] / MPV
    rb, rm = T['base_r_m'] / MPV, T['muzzle_r_m'] / MPV
    r1 = rb * 0.88
    r2 = rb * 0.80
    a, b = 0.30 * L, 0.55 * L
    return [(0, rb), (1.5, rb), (1.5, r1), (a, r1 * 0.97), (a, r1 * 1.04), (a + 1, r1 * 1.04), (a + 1, r2), (b, r2 * 0.94),
            (b, r2 * 0.88), (L - 3, rm), (L - 3, rm * 0.9), (L - 2, rm * 0.9), (L - 2, rm * 1.3), (L - 0.5, rm * 1.3),
            (L - 0.5, rm * 1.15), (L, rm * 1.15)], [a, a + 1, L - 2, L - 0.5]


def bands(marks):
    a, a1, m0, m1 = marks
    return lambda t: BAND if (a <= t < a1 or m0 <= t < m1 or t < 1.5) else BRONZE


def carriage_gun(code, T):
    prof, marks = profile(T)
    blen = prof[-1][0]
    rb = T['base_r_m'] / MPV
    k = max(1.0, rb / 3.2)                                   # 照 4 磅砲（砲尾 3.2 格）放大砲架
    bore = 0.5 * (T['lb'] * 0.30122 / 7870 * 6 / math.pi) ** (1 / 3) / MPV   # 鐵彈直徑 ÷ 2
    k0 = int(math.ceil(rb * 0.95)) + 0                       # cheek 內側要讓開砲尾
    k1 = k0 + max(1, int(round(k)))
    AZ = T['AZ']
    AX = k1 + 2
    cl = max(2, int(round(2 * k)))
    YB = 2 * cl + 1
    W, L, H = 2 * AX + 1, YB + int(math.ceil(blen)) + 1, AZ + int(math.ceil(rb * 1.05)) + 3
    P = Part(W, L, H)
    P.tube(AX, AZ, YB, prof, bands(marks), bore, 6)
    P.tube(AX, AZ, YB - cl, [(0, 1.0 * k), (cl, 1.0 * k)], lambda t: BRONZE)              # cascabel 頸
    P.tube(AX, AZ, YB - 2 * cl, [(0, 1.5 * k), (cl, 1.5 * k)], lambda t: BRONZE)          # cascabel 鈕
    TY = YB + int(round(0.42 * blen))
    clen = int(round(20 * k))
    YF = TY + int(round(5 * k))
    YR = max(0, YF - clen + 1)
    cb = max(4, int(round(AZ * 0.36)))                      # cheek 底：砲軸高的 0.36（4 磅砲 AZ 14 ⇒ 5）
    steps = [(0, AZ + 1), (int(6 * k), AZ - 1), (int(10 * k), AZ - 2), (int(14 * k), AZ - 4)]
    for kk in range(k0, k1 + 1):
        for sg in (-1, 1):
            x = AX + sg * kk
            for y in range(YR, YF + 1):
                back = YF - y
                top = [h for b0, h in steps if back >= b0][-1]
                bot = cb + 1 if int(5 * k) <= back <= int(12 * k) else cb
                for z in range(bot, top + 1):
                    P.put(x, y, z, CARR)
            P.put(x, TY, AZ + 1, IRON, True)
    for kk in range(-k1, k1 + 1):
        P.put(AX + kk, TY, AZ, BRONZE, True)                    # 耳軸
    yf, yr = YF - int(round(3 * k)), YR + int(round(3 * k))
    for ya, r in ((yf, min(cb - 0.5, 3.0 * k)), (yr, min(cb - 0.5, 2.7 * k))):
        P.box(AX - k1 - 1, AX + k1 + 1, ya, ya, 2, cb - 1, CARR)
        for sg in (-1, 1):
            P.wheel(AX + sg * (k1 + 1), ya + 0.5, r, r, 36)
            P.put(AX + sg * (k1 + 2), ya, 2, IRON, True)
    P.box(AX - k0 + 1, AX + k0 - 1, YR, YR + int(round(8 * k)), cb, cb, CARR)
    zq = AZ - int(math.ceil(rb)) - 1
    P.box(AX - 1, AX + 1, YR + 1, YR + int(round(5 * k)), cb + 1, max(cb + 1, zq), QUOIN)
    P.box(AX - k0 + 1, AX + k0 - 1, YF - 1, YF, cb, cb + 3, CARR)
    pts = {'muzzle': (AX, YB + int(math.ceil(blen)) - 1, AZ), 'breech': (AX, YB, AZ), 'cascabel': (AX, YB - 2 * cl, AZ),
           'train': (AX, YR, cb), 'trunnion': (AX, TY, AZ),
           'eye-aft': (AX - k1 - 1, YF - int(round(9 * k)), cb + 4), 'eye-fwd': (AX + k1 + 1, YF - int(round(9 * k)), cb + 4)}
    assert pts['muzzle'] not in P.cells, (code, '砲口那一格應該是挖空的')
    pivot = [AX + 0.5, YF + 1, 0]
    return P, pts, pivot


def petriera(code, T):
    """叉架迴旋砲：立柱（z 0 起）＋U 叉＋短砲身（藥室在後、砲口大）＋尾把手。pivot ＝ 立柱軸心、z 0。"""
    prof_len = T['len_m'] / MPV
    rb, rm = T['base_r_m'] / MPV, T['muzzle_r_m'] / MPV
    AZ = T['AZ']
    AX = int(math.ceil(rb)) + 3
    tail = 10
    W, L, H = 2 * AX + 1, tail + int(math.ceil(prof_len)) + 2, AZ + int(math.ceil(rb)) + 3
    P = Part(W, L, H)
    YB = tail
    prof = [(0, rb * 0.75), (prof_len * 0.25, rb * 0.75), (prof_len * 0.25, rb), (prof_len * 0.30, rb), (prof_len * 0.30, rb * 0.92),
            (prof_len - 2, rm), (prof_len - 2, rm * 1.25), (prof_len, rm * 1.25)]
    bore = 0.5 * (T['lb'] * 0.30122 / 2500 * 6 / math.pi) ** (1 / 3) / MPV       # 石彈直徑 ÷ 2
    P.tube(AX, AZ, YB, prof, lambda t: BAND if (prof_len * 0.25 <= t < prof_len * 0.30 or t >= prof_len - 2) else BRONZE, bore, 5)
    TY = YB + int(round(prof_len * 0.40))                       # 耳軸（叉架托的地方）
    for z in range(0, AZ - int(math.ceil(rb)) - 1):              # 立柱
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                P.put(AX + dx, TY + dy, z, IRON if z > 2 else CARR)
    zf = AZ - int(math.ceil(rb)) - 1
    fx = int(math.ceil(rb)) + 1
    for x in range(AX - fx, AX + fx + 1):                       # U 叉的底
        P.put(x, TY, zf, IRON)
    for sg in (-1, 1):
        for z in range(zf, AZ + 1):
            P.put(AX + sg * fx, TY, z, IRON)
        for x in range(AX + sg * int(math.ceil(rb)), AX + sg * fx, sg):
            P.put(x, TY, AZ, IRON, True)                         # 耳軸穿到叉臂
    for y in range(1, YB + 1):                                   # 尾把手（tiller）
        P.put(AX, y, AZ, IRON)
    pts = {'muzzle': (AX, YB + int(math.ceil(prof_len)) - 1, AZ), 'breech': (AX, YB, AZ), 'cascabel': (AX, 1, AZ),
           'trunnion': (AX, TY, AZ), 'pivot': (AX, TY, 0)}
    assert pts['muzzle'] not in P.cells, (code, '砲口那一格應該是挖空的')
    return P, pts, [AX + 0.5, TY + 0.5, 0]


def main():
    plan = json.loads((D / 'plan.json').read_text(encoding='utf-8'))
    out = D / 'masks/guns'
    out.mkdir(parents=True, exist_ok=True)
    res = {}
    for code, T in plan['guns']['types'].items():
        P, pts, pivot = (petriera if T['kind'] == 'petriera' else carriage_gun)(code, T)
        W, L, H = P.W, P.L, P.H
        occ = np.zeros((W, L, H), bool)
        for (x, y, z) in P.cells:
            occ[x, y, z] = True
        _, ncomp = ndimage.label(occ)
        cav = int((ndimage.binary_fill_holes(occ) & ~occ).sum())
        AX = (W - 1) // 2
        mir = sum(1 for (x, y, z), c in P.cells.items() if P.cells.get((2 * AX - x, y, z)) != c)
        body = (f'# {T["name"]}（gun {code}，通用部件，draft_guns_venice.py，0.05 m）x,y,z,color —— at 0,0,0\n' +
                ''.join(f'{x},{y},{z},{c}\n' for (x, y, z), c in sorted(P.cells.items()))).encode('utf-8')
        (out / f'gun-{code}.vox.txt').write_bytes(body)
        res[code] = dict(cells=len(P.cells), size=[W, L, H], anchors={k: list(v) for k, v in pts.items()}, pivot=pivot,
                         barrel_m=round((pts['muzzle'][1] - pts['cascabel'][1] + 1) * MPV, 2), axis_m=round((pts['muzzle'][2] + 0.5) * MPV, 3),
                         components=int(ncomp), cavity=cav, mirror_x_diff=mir, sha16=hashlib.sha256(body).hexdigest()[:16])
        assert ncomp == 1 and cav == 0 and mir == 0, (code, ncomp, cav, mir)
    (D / 'verify_guns_venice.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: {kk: v[kk] for kk in ('cells', 'size', 'barrel_m', 'axis_m')} for k, v in res.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
