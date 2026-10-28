# 通用部件：4 磅長砲（gun 4l；鐵砲管＋兩軸四輪的海用砲架，0.05 m）—— 聖羅曼號（TASK-0970）做的，下一艘要 4 磅砲的船直接引用
#   Tim 2026-10-28：「3 或 4 磅 請另外做炮(炮只有同型號共用模型)」⇒ ⛔ 不拿 6 磅縮
#   結構出處：summit-stormkaap-01m/design/draft_guns.py（Part、tube、wheel、build 的砲架做法）；砲管外形、砲架尺寸是這一件自己的（plan.json gun4l）
#   座標（Ship_Guns §4.1）：x 沿船長（砲軸在 x 中線）、y ＝ 砲口方向、z 0 ＝ 甲板面那一層
#   輸出：masks/gun4l/gun-4l.vox.txt（at 0,0,0）、verify_gun4l.json（框、固定點、pivot、元件、空腔）
#   用法：python -I -X utf8 draft_gun4l.py <design>
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
G = plan['gun4l']
COL = G['colors']


class Part:
    def __init__(s, W, L, H):
        s.cells = {}
        s.W, s.L, s.H = W, L, H

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

    def tube(s, cx, cz, y0, prof, c, bore_r=0.0, bore_depth=0.0):
        """沿 y 的旋轉體：軸在 (cx, cz) 那一格的格心；prof ＝ [(s, r), …] 分段線性；砲口那一段挖空。"""
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
                        s.put(cx + dx, y, cz + dz, c)

    def wheel(s, cx, cy, cz, r, c):
        for y in range(s.L):
            for z in range(s.H):
                if math.hypot(y + 0.5 - cy, z + 0.5 - cz) <= r:
                    s.put(cx, y, z, c, True)


def build():
    B, Cb = G['barrel'], G['carriage']
    prof = [tuple(p) for p in B['profile']]
    blen = prof[-1][0]
    k0, k1 = Cb['cheek_x']
    AX, AZ = k1 + 2, G['AZ']
    cl = 2
    YB = 2 * cl + 1
    rmax = max(r for _, r in prof)
    W, L, H = 2 * AX + 1, YB + int(math.ceil(blen)) + 1, AZ + int(math.ceil(rmax)) + 2
    P = Part(W, L, H)
    assert rmax < k0 + 0.5 or True
    P.tube(AX, AZ, YB, prof, COL['barrel'], B['bore_r'], B['bore_depth'])
    P.tube(AX, AZ, YB - cl, [(0, 1.0), (cl, 1.0)], COL['barrel'])            # cascabel 頸
    P.tube(AX, AZ, YB - 2 * cl, [(0, 1.5), (cl, 1.5)], COL['barrel'])        # cascabel 鈕
    TY = YB + B['trunnion_from_base']
    YF = TY + Cb['front_from_trunnion']
    YR = YF - Cb['len'] + 1
    assert YR >= 0, YR
    cb = Cb['cheek_bottom']
    a0, a1, abot = Cb['arch']
    for k in range(k0, k1 + 1):                                              # cheek（兩片，往後一階一階降）
        for sg in (-1, 1):
            x = AX + sg * k
            for y in range(YR, YF + 1):
                back = YF - y
                top = [h for b0, h in Cb['cheek_steps'] if back >= b0][-1]
                bot = abot if a0 <= back <= a1 else cb
                for z in range(bot, top + 1):
                    P.put(x, y, z, COL['carriage'])
            P.put(x, TY, AZ + 1, COL['iron'], True)                          # cap square
    for k in range(-k1, k1 + 1):                                             # 耳軸：沿 x 穿過兩片 cheek
        P.put(AX + k, TY, AZ, COL['barrel'], True)
    yf = YF - Cb['axle_front_back']
    yr = YR + Cb['axle_rear_fwd']
    for ya, r in ((yf, Cb['wheel_front_r']), (yr, Cb['wheel_rear_r'])):
        P.box(AX - k1 - 1, AX + k1 + 1, ya, ya, 2, cb - 1, COL['carriage'])   # 軸木
        for sg in (-1, 1):
            P.wheel(AX + sg * (k1 + 1), ya + 0.5, r, r, COL['barrel'])        # 實心木輪（truck），漆黑
            P.put(AX + sg * (k1 + 2), ya, 2, COL['iron'], True)              # 輪軸頭
    P.box(AX - k0 + 1, AX + k0 - 1, YR, YR + Cb['bed_len'], cb, cb, COL['carriage'])           # 床板
    zq = AZ - int(math.ceil(rmax)) - 1
    P.box(AX - 1, AX + 1, YR + 1, YR + Cb['quoin_len'], cb + 1, max(cb + 1, zq), COL['quoin'])  # quoin（楔）
    P.box(AX - k0 + 1, AX + k0 - 1, YF - 1, YF, cb, cb + 3, COL['carriage'])                    # 前 transom
    pts = {'muzzle': (AX, YB + int(math.ceil(blen)) - 1, AZ), 'breech': (AX, YB, AZ), 'cascabel': (AX, YB - 2 * cl, AZ),
           'train': (AX, YR, cb), 'trunnion': (AX, TY, AZ),
           'eye-aft': (AX - k1 - 1, YF - Cb['eye_back'], Cb['eye_z']), 'eye-fwd': (AX + k1 + 1, YF - Cb['eye_back'], Cb['eye_z'])}
    assert pts['muzzle'] not in P.cells, '砲口那一格應該是挖空的'
    return P, pts, {'AX': AX, 'AZ': AZ, 'YB': YB, 'YF': YF, 'YR': YR, 'TY': TY, 'size': [W, L, H], 'barrel_len': blen}


def main():
    P, pts, geo = build()
    W, L, H = geo['size']
    occ = np.zeros((W, L, H), bool)
    for (x, y, z) in P.cells:
        occ[x, y, z] = True
    _, ncomp = ndimage.label(occ)
    cav = int((ndimage.binary_fill_holes(occ) & ~occ).sum())
    mir = sum(1 for (x, y, z), c in P.cells.items() if P.cells.get((2 * geo['AX'] - x, y, z)) != c)
    od = os.path.join(D, 'masks', 'gun4l')
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, 'gun-4l.vox.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 4 磅長砲 gun 4l（通用部件，draft_gun4l.py，0.05 m）x,y,z,color —— at 0,0,0\n')
        f.write(''.join('%d,%d,%d,%d\n' % (x, y, z, c) for (x, y, z), c in sorted(P.cells.items())))
    cols = {}
    for c in P.cells.values():
        cols[c] = cols.get(c, 0) + 1
    v = {'cells': len(P.cells), 'size': [W, L, H], 'anchors': {k: list(v) for k, v in pts.items()},
         'pivot': [geo['AX'] + 0.5, geo['YF'] + 1, 0], 'pivot_src': '砲架前緣中間、甲板面那一層（同風暴角號／康塞普西翁號的砲）',
         'barrel_m': round((pts['muzzle'][1] - pts['cascabel'][1] + 1) * G['mpv'], 3), 'trunnion_z_m': round((geo['AZ'] + 0.5) * G['mpv'], 3),
         'components_6': int(ncomp), 'cavity_cells': cav, 'mirror_x_diff': mir, 'colors': {int(k): n for k, n in sorted(cols.items())},
         'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(), 'geo': geo}
    with open(os.path.join(D, 'verify_gun4l.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(v, f, ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False))


if __name__ == '__main__':
    main()
