# 通用部件（TASK-1155）：還沒有自己模型的五種砲 —— 36 磅 coursier（36l）、IX 吋／XI 吋 Dahlgren（9d／11d）、6.4 吋／7 吋 Brooke（64b／7b）
#   Tim 2026-11-01：「排查一下目前船有哪些炮是用其他炮暫代的 然後替換成對應的炮」；Ship_Guns §2.2 砲只跟同一種砲共用模型（⛔ 不拿餘燼號 32 磅縮）
#   出處：本船 draft_gun8l.py（照抄 Part／tube／wheel，再加三種砲架：sled 滑橇、marsilly 前輪後滑木、slide 樞軸滑軌）；參數在 guns1155.json
#   座標（Ship_Guns §4.1）：x 沿船長（砲軸在 x 中線）、y ＝ 砲口方向、z 0 ＝ 甲板面那一層
#   輸出：masks/guns1155/<代碼>.vox.txt（at 0,0,0）、verify_guns1155.json（每件的框、固定點、pivot、元件、空腔、鏡像差、色數）
#   用法：python -I -X utf8 draft_guns1155.py <design>
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
SPEC = json.load(open(os.path.join(D, 'guns1155.json'), encoding='utf-8'))
COL = SPEC['colors']


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
        """沿 y 的旋轉體：軸在 (cx, cz) 那一格的格心；prof ＝ [(s, r), …] 分段線性（同一個 s 兩點 ＝ 台階）；砲口那一段挖空。"""
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


def radius_at(prof, t):
    for (a, ra), (b, rb) in zip(prof, prof[1:]):
        if a <= t < b:
            return ra + (rb - ra) * (t - a) / (b - a)
    return prof[-1][1]


def build(G):
    B, C = G['barrel'], G['carriage']
    prof = [tuple(p) for p in B['profile']]
    blen = B['len']
    assert abs(prof[-1][0] - blen) < 1e-9, ('profile 的最後一點要等於 len', prof[-1][0], blen)
    cn_r, cn_l, ck_r, ck_l = B['cascabel']
    k0, k1 = C['k']
    AX, AZ = k1 + 2, G['AZ']
    BC = COL[G['barrel_color']]
    typ = C['type']
    # y 方向先用相對座標排，再整體平移讓最小的 y ＝ 0
    yb = ck_l + cn_l                                        # 砲尾（breech 面）
    ty = yb + B['trunnion_s']
    yf = ty + C['front_from_trunnion']
    yr = yf - C['len'] + 1
    ylo, yhi = min(0, yr), max(yb + int(math.ceil(blen)) - 1, yf)
    if typ == 'slide':
        ylo, yhi = min(ylo, yr - C['slide_back']), max(yhi, yf + C['slide_fwd'])
    off = -ylo
    YB, TY, YF, YR = yb + off, ty + off, yf + off, yr + off
    rmax = max(r for _, r in prof)
    W, L = 2 * AX + 1, yhi - ylo + 1
    H = max(AZ + int(math.ceil(rmax)) + 2, max(h for _, h in C['top_steps']) + 3)
    P = Part(W, L, H)
    P.tube(AX, AZ, YB, prof, BC, B['bore_r'], B['bore_depth'])
    P.tube(AX, AZ, YB - cn_l, [(0, cn_r), (cn_l, cn_r)], BC)                       # cascabel 頸
    P.tube(AX, AZ, YB - cn_l - ck_l, [(0, ck_r), (ck_l, ck_r)], BC)                # cascabel 鈕
    if B.get('dolphins'):                                                          # 青銅砲的一對 dolphins（提把）
        dl = B['dolphins']
        s0, s1 = dl['s']
        for sg in (-1, 1):
            x = AX + sg * dl['dx']
            zt = AZ + int(math.ceil(radius_at(prof, (s0 + s1) / 2)))
            for y in (YB + s0, YB + s1):
                for z in range(zt - 1, zt + dl['h']):
                    P.put(x, y, z, BC, True)
            for y in range(YB + s0, YB + s1 + 1):
                P.put(x, y, zt + dl['h'] - 1, BC, True)
    # 砲架
    base = {'sled': 0, 'marsilly': C.get('bottom', 0), 'slide': C.get('slide_h', 0)}[typ]
    for k in range(k0, k1 + 1):                                                    # cheek：兩片，往後一階一階降
        for sg in (-1, 1):
            x = AX + sg * k
            for y in range(YR, YF + 1):
                back = YF - y
                top = [h for b0, h in C['top_steps'] if back >= b0][-1]
                bot = 0 if (typ == 'marsilly' and back >= C['len'] - C['skid_len']) else base
                for z in range(bot, top + 1):
                    P.put(x, y, z, COL['carriage'])
            for y in (TY - 1, TY, TY + 1):                                         # cap square（蓋在耳軸上面的鐵件）
                P.put(x, y, AZ + int(B['trunnion_r']) + 1, COL['fit'], True)       # 耳軸頂那一格的上面（cheek 頂 ＝ AZ＋1）
    tr = B['trunnion_r']                                                           # 耳軸：沿 x 穿過兩片 cheek
    R = int(math.ceil(tr))
    for x in range(AX - k1, AX + k1 + 1):
        for dy in range(-R, R + 1):
            for dz in range(-R, R + 1):
                if math.hypot(dy, dz) <= tr + 1e-9:
                    P.put(x, TY + dy, AZ + dz, BC, True)
    if typ == 'sled':
        P.box(AX - k0 + 1, AX + k0 - 1, YR, YF, 0, C['bed'] - 1, COL['carriage'])  # 滑橇的底板：整個底面貼著滑軌
    else:
        P.box(AX - k0 + 1, AX + k0 - 1, YR, YR + 12, base, base, COL['carriage'])  # 床板（砲尾底下）
    P.box(AX - k0 + 1, AX + k0 - 1, YF - 1, YF, base, base + 3, COL['carriage'])   # 前 transom
    P.box(AX - k0 + 1, AX + k0 - 1, YR, YR + 1, 0 if typ == 'marsilly' else base, base + 3, COL['carriage'])   # 後 transom（Marsilly：尾端貼甲板）
    zq = AZ - int(math.ceil(radius_at(prof, 3))) - 1                              # quoin（楔）：砲尾底下
    zbed = (C['bed'] if typ == 'sled' else base + 1)
    P.box(AX - 1, AX + 1, YB + 1, YB + 7, zbed, max(zbed, zq), COL['quoin'])
    if typ == 'marsilly':
        ya = YF - C['front_axle_back']
        r = C['truck_r']
        P.box(AX - k1 - 1, AX + k1 + 1, ya, ya, 2, base - 1, COL['carriage'])      # 前軸木
        for sg in (-1, 1):
            P.wheel(AX + sg * (k1 + 1), ya + 0.5, r, r, BC if BC == COL['iron'] else COL['iron'])   # 實心木輪（truck），漆黑
            P.put(AX + sg * (k1 + 2), ya, int(r), COL['fit'], True)                # 輪軸頭
    if typ == 'slide':                                                             # 滑軌：兩根軌木＋前後、中間的橫木（色 slide ⇒ 之後拆成砲座）
        rw, hs = C['rail_w'], C['slide_h']
        y0, y1 = YR - C['slide_back'], YF + C['slide_fwd']
        for sg in (-1, 1):
            xa, xb = sorted((AX + sg * (k1 - rw + 1), AX + sg * k1))
            P.box(xa, xb, y0, y1, 0, hs - 1, COL['slide'], True)
        for ya in (y0, y0 + 1, (y0 + y1) // 2, y1 - 1, y1):
            P.box(AX - k1, AX + k1, ya, ya, 0, hs - 1, COL['slide'], True)
    ymz = YB + int(math.ceil(blen)) - 1
    pts = {'muzzle': (AX, ymz, AZ), 'breech': (AX, YB, AZ), 'cascabel': (AX, YB - cn_l - ck_l, AZ),
           'train': (AX, YR, base), 'trunnion': (AX, TY, AZ),
           'eye-aft': (AX - k1 - 1, YF - 12, base + 4), 'eye-fwd': (AX + k1 + 1, YF - 12, base + 4)}
    assert pts['muzzle'] not in P.cells, '砲口那一格應該是挖空的'
    assert pts['breech'] in P.cells and pts['trunnion'] in P.cells
    return P, pts, {'AX': AX, 'AZ': AZ, 'YB': YB, 'YF': YF, 'YR': YR, 'TY': TY, 'size': [W, L, H], 'base': base, 'type': typ}


def main():
    out = {}
    od = os.path.join(D, 'masks', 'guns1155')
    os.makedirs(od, exist_ok=True)
    for code, G in SPEC['guns'].items():
        P, pts, geo = build(G)
        W, L, H = geo['size']
        occ = np.zeros((W, L, H), bool)
        for (x, y, z) in P.cells:
            occ[x, y, z] = True
        _, ncomp = ndimage.label(occ)
        cav = int((ndimage.binary_fill_holes(occ) & ~occ).sum())
        mir = sum(1 for (x, y, z), c in P.cells.items() if P.cells.get((2 * geo['AX'] - x, y, z)) != c)
        p = os.path.join(od, code + '.vox.txt')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# %s（通用部件，draft_guns1155.py，0.05 m）x,y,z,color —— at 0,0,0\n' % G['title'])
            f.write(''.join('%d,%d,%d,%d\n' % (x, y, z, c) for (x, y, z), c in sorted(P.cells.items())))
        cols = {}
        for c in P.cells.values():
            cols[c] = cols.get(c, 0) + 1
        mz, br = pts['muzzle'], pts['cascabel']
        out[code] = {'work': G['work'], 'cells': len(P.cells), 'size': [W, L, H], 'anchors': {k: list(v) for k, v in pts.items()},
                     'pivot': [geo['AX'] + 0.5, geo['YF'] + 1, 0], 'pivot_src': '砲架前緣中間、甲板面那一層（同其他舷側砲的元件）',
                     'barrel_m': round((mz[1] - br[1] + 1) * 0.05, 3), 'axis_z_m': round((geo['AZ'] + 0.5) * 0.05, 3),
                     'components_6': int(ncomp), 'cavity_cells': cav, 'mirror_x_diff': mir, 'colors': {int(k): n for k, n in sorted(cols.items())},
                     'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(), 'geo': geo}
    with open(os.path.join(D, 'verify_guns1155.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for code, v in out.items():
        print(code, v['size'], v['cells'], '元件', v['components_6'], '空腔', v['cavity_cells'], '鏡像差', v['mirror_x_diff'], '砲管', v['barrel_m'], 'm', '砲軸高', v['axis_z_m'], 'm', v['colors'])


if __name__ == '__main__':
    main()
