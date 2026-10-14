# 三叉戟號 三叉戟砲（TASK-0578）：奇幻三管速射砲，船頭追擊砲用 —— 本船自己的設計（plan.json trident）
#   三根砲管橫排（中間那根最長 ＝ 三叉戟的中尖），兩道金色連結板（yoke）把三根串成一把；砲口一圈金箍；砲尾上方一個金箍彈鼓（速射）；
#   寬砲架（兩片 cheek、床板、quoin）、四個輪子、一根穿過三管與兩片 cheek 的耳軸。
#   旋轉體的畫法參考風暴角號 draft_guns.py 的 Part.tube（summit）。
#   子作品座標（同其他砲）：x ＝ 寬（中管軸在 AX 那一格的格心）、y ＝ 砲身方向（砲口 +y）、z 0 ＝ 甲板面上第一層。0.05 m／格。
#   輸出：masks/guns/trident.vox.txt（at 0,0,0）、verify_trident.json（框、格數、顏色、固定點、左右差、元件）。用法：python -I -X utf8 draft_trident.py <design>
import sys, os, json, math, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL


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

    def tube(s, cx, cz, y0, prof, c, bore_r=0.0, bore_depth=0.0, over=False):
        """沿 y 的旋轉體：軸在 (cx, cz) 那一格的格心；prof ＝ [(t, r)…] 分段線性；砲口那一段挖空。"""
        tmax = prof[-1][0]
        for y in range(s.L):
            t = y + 0.5 - y0
            if not (0 <= t < tmax):
                continue
            r = None
            for (a, ra), (b, rb) in zip(prof, prof[1:]):
                if a <= t < b:
                    r = ra + (rb - ra) * (t - a) / (b - a) if b > a else rb
                    break
            if r is None:
                continue
            R = int(math.ceil(r)) + 1
            for dx in range(-R, R + 1):
                for dz in range(-R, R + 1):
                    d = math.hypot(dx, dz)
                    if d <= r + 1e-9:
                        if bore_r > 0 and t > tmax - bore_depth and d <= bore_r:
                            s.cells.pop((cx + dx, y, cz + dz), None)
                            continue
                        s.put(cx + dx, y, cz + dz, c, over)

    def wheel(s, x, cy, cz, r, c):
        for y in range(s.L):
            for z in range(s.H):
                if math.hypot(y + 0.5 - cy, z + 0.5 - cz) <= r:
                    s.put(x, y, z, c, True)


def components(cells):
    S, seen, n = set(cells), set(), 0
    for c in S:
        if c in seen:
            continue
        n += 1
        st = [c]
        seen.add(c)
        while st:
            x, y, z = st.pop()
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                q = (x + d[0], y + d[1], z + d[2])
                if q in S and q not in seen:
                    seen.add(q)
                    st.append(q)
    return n


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    D = os.path.abspath(sys.argv[1])
    T = HL.load_plan(D)['trident']
    K = T['colors']
    AX, AZ, YB = T['AX'], T['AZ'], T['YB']
    dxs = T['barrel_dx']
    Lc, Ls = T['len_center'], T['len_side']
    W, L, H = 2 * AX + 1, YB + Lc + 1, T['H']
    P = Part(W, L, H)

    def prof(Lb):
        return [(round(a * Lb, 3), r) for a, r in T['profile']]
    # 砲管（三根；中管最長）
    for dx in dxs:
        Lb = Lc if dx == 0 else Ls
        P.tube(AX + dx, AZ, YB, prof(Lb), K['barrel'], T['bore_r'], T['bore_depth'])
        P.tube(AX + dx, AZ, YB - 2, [(0, 1.4), (2, 1.4)], K['barrel'])                       # cascabel 頸
        P.tube(AX + dx, AZ, YB - 4, [(0, 2.0), (2, 2.0)], K['gold'])                         # cascabel 鈕（金）
        for t0 in (Lb - 3, Lb - 2):                                                          # 砲口金箍
            y = YB + t0
            r = [rr for (a, rr), (b, _) in zip(prof(Lb), prof(Lb)[1:]) if a <= t0 + 0.5 < b][0] + 0.6
            for x in range(W):
                for z in range(H):
                    d = math.hypot(x - AX - dx, z - AZ)
                    if T['bore_r'] < d <= r and (x, y, z) not in P.cells:
                        P.put(x, y, z, K['gold'])
    # 金色連結板（yoke）：三根管外面各包 ＋0.9 的那一片
    for a in T['yokes']:
        for dy in range(T['yoke_thick']):
            y = YB + int(round(a * Ls)) + dy
            for x in range(W):
                for z in range(H):
                    if (x, y, z) in P.cells:
                        continue
                    inside = any(math.hypot(x - AX - dx, z - AZ) <= T['profile'][2][1] + 0.9 for dx in dxs)
                    between = abs(z - AZ) <= 1 and min(dxs) + AX <= x <= max(dxs) + AX
                    if inside or between:
                        P.put(x, y, z, K['gold'])
    # 彈鼓（速射）：沿 y 的圓筒，坐在中管上；兩端金箍
    dr = T['drum']
    zc = AZ + dr['z_above_axis']
    P.tube(AX, zc, YB + dr['y0'], [(0, dr['r']), (dr['len'], dr['r'])], K['drum'])
    for t in (0, dr['len'] - 1):
        P.tube(AX, zc, YB + dr['y0'] + t, [(0, dr['r'] + 0.6), (1, dr['r'] + 0.6)], K['gold'], over=True)
    P.box(AX - 1, AX + 1, YB + dr['y0'] + 2, YB + dr['y0'] + dr['len'] - 3, AZ + 2, int(math.ceil(zc - dr['r'])) + 1, K['gold'])   # 鼓座
    # 砲架
    C = T['carriage']
    k0, k1 = C['cheek_x']
    YR, YF = C['y'][0], C['y'][1]
    for sg in (-1, 1):
        for k in range(k0, k1 + 1):
            x = AX + sg * k
            for y in range(YR, YF + 1):
                top = C['cheek_top_front'] if y >= YF - C['front_len'] else C['cheek_top_rear']
                P.box(x, x, y, y, C['cheek_bottom'], top, K['carriage'])
    P.box(AX - k0 + 1, AX + k0 - 1, YR, YF, C['cheek_bottom'], C['cheek_bottom'] + 1, K['carriage'])                 # 床板
    zq = AZ - int(math.ceil(T['profile'][0][1])) - 1
    P.box(AX - 4, AX + 4, YR + 2, YR + 9, C['cheek_bottom'] + 2, zq, K['quoin'])                                   # quoin（墊在砲尾底下）
    TY = YB + C['trunnion_from_breech']
    for x in range(AX - k1 - 1, AX + k1 + 2):                                                                    # 耳軸：穿過三管與兩片 cheek
        P.put(x, TY, AZ, K['gold'], True)
    for ya in (YR + C['axle_from_rear'], YF - C['axle_from_front']):
        P.box(AX - k1 - 1, AX + k1 + 1, ya, ya, 2, C['cheek_bottom'] - 1, K['carriage'])                           # 軸木
        for sg in (-1, 1):
            P.wheel(AX + sg * (k1 + 1), ya + 0.5, C['wheel_r'], C['wheel_r'], K['wheel'])
            P.put(AX + sg * (k1 + 2), ya, int(C['wheel_r']), K['gold'], True)                                        # 輪軸頭
    pts = {'muzzle': (AX, YB + Lc - 1, AZ), 'breech': (AX, YB, AZ), 'cascabel': (AX, YB - 4, AZ), 'train': (AX, YR, C['cheek_bottom']),
           'trunnion': (AX, TY, AZ), 'eye-aft': (AX - k1 - 1, YF - 10, 8), 'eye-fwd': (AX + k1 + 1, YF - 10, 8)}
    for i, dx in enumerate(dxs):
        pts['muzzle-%s' % 'abc'[i]] = (AX + dx, YB + (Lc if dx == 0 else Ls) - 1, AZ)
    for k, v in pts.items():
        if k.startswith('muzzle'):
            assert v not in P.cells, (k, '砲口那一格應該是挖空的')
    os.makedirs(os.path.join(D, 'masks', 'guns'), exist_ok=True)
    text = '# 三叉戟號 三叉戟砲（draft_trident.py，0.05 m）x,y,z,color —— at 0,0,0\n' + ''.join('%d,%d,%d,%d\n' % (x, y, z, c) for (x, y, z), c in sorted(P.cells.items()))
    open(os.path.join(D, 'masks', 'guns', 'trident.vox.txt'), 'w', encoding='utf-8', newline='\n').write(text)
    cnt = {}
    for c in P.cells.values():
        cnt[str(c)] = cnt.get(str(c), 0) + 1
    asym = sum(1 for (x, y, z), c in P.cells.items() if P.cells.get((2 * AX - x, y, z)) != c)
    zmin = min(z for _, _, z in P.cells)
    out = {'size': [W, L, H], 'cells': len(P.cells), 'colors': dict(sorted(cnt.items())), 'asym_x': asym, 'components': components(P.cells), 'z_min': zmin,
           'anchors': {k: list(v) for k, v in sorted(pts.items())}, 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}
    with open(os.path.join(D, 'verify_trident.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    print(json.dumps({k: v for k, v in out.items() if k != 'anchors'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
