"""
24 門 32 磅 carronade 擺進 spar deck 砲門（階段二十九）—— 外部模型（子作品 -gun-carronade32，0.05 m ⇒ scale 0.5），掛在 spar deck 子作品上。
S 舷 rotate 0（砲口 +y）、P 舷 rotate 180。pivot ＝ skid 前緣中間、甲板那一層（子作品 (7.5, 42, 0)）。
擺法：x 對準砲門中線（再試 ±0.5、±1），y 從舷牆外面開始往裡退（每步 0.5 格），退到模型每一格的格心＋八個角都不在實心格裡 ⇒ 那就是推得最出去的位置。
讀數：砲口（子作品 (7.5, 52, 19.5)）離舷牆外面幾格（正 ＝ 伸出去）、砲軸高度在開口的哪裡。
用法：python -I place_carronades.py <組裝件清單（draft=1，砲門刻完的樣子）>
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SCALE = 0.5
YC = 160
DECK = [(None, 238, 106), (238, 570, 105), (570, 633, 108)]


def deck(x):
    for a, b, z in DECK:
        if (a is None or x >= a) and (b is None or x < b):
            return z
    raise ValueError(x)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    a = np.loadtxt(sys.argv[1], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    m = a[(a[:, 0] >= 100) & (a[:, 0] < 660) & (a[:, 2] >= 95) & (a[:, 2] < 140)]
    G = np.zeros((560, 320, 45), bool)
    G[m[:, 0] - 100, m[:, 1], m[:, 2] - 95] = True
    cells = []
    for line in open(os.path.join(HERE, 'masks', 'guns2', 'carronade32.vox.txt'), encoding='utf-8'):
        if line.startswith('#') or not line.strip():
            continue
        x, y, z, c = map(int, line.split(','))
        cells.append((x, y, z))
    cells = np.array(cells, float)
    offs = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
    samp = (cells[:, None, :] + offs[None]).reshape(-1, 3)
    pivot = np.array([7.5, 42.0, 0.0])
    muzzle = np.array([7.5, 52.0, 19.5])
    ports = json.load(open(os.path.join(HERE, 'verify_spar_ports.json'), encoding='utf-8'))['ports']

    def place(P, at, rot):
        q = (P - pivot) * SCALE
        c, s = (1.0, 0.0) if rot == 0 else (-1.0, 0.0)
        x = q[:, 0] * c - q[:, 1] * s
        y = q[:, 0] * s + q[:, 1] * c
        return np.stack([x + at[0], y + at[1], q[:, 2] + at[2]], -1)

    def hit(W):
        i = np.floor(W).astype(int)
        i[:, 0] -= 100
        i[:, 2] -= 95
        ok = (i[:, 0] >= 0) & (i[:, 0] < 560) & (i[:, 1] >= 0) & (i[:, 1] < 320) & (i[:, 2] >= 0) & (i[:, 2] < 45)
        h = np.zeros(len(W), bool)
        h[ok] = G[i[ok, 0], i[ok, 1], i[ok, 2]]
        return h

    out = []
    for p in ports:
        xc = (p['x'][0] + p['x'][1] + 1) / 2.0
        for side, nm, rot in ((1, 'S', 0), (-1, 'P', 180)):
            wy = p[nm]['wall_y_mid']                      # [內, 外]（S：小的是內）或 P：[外, 內]
            outer_face = max(wy) + 1 if side > 0 else min(wy)
            best = None
            for dx in (0.0, 0.5, -0.5, 1.0, -1.0):
                z = deck(int(xc))
                for back in [0.5 * k for k in range(0, 40)]:
                    yp = outer_face - side * back
                    at = (xc + dx, yp, float(z))
                    if hit(place(samp, at, rot)).any():
                        continue
                    tip = place(muzzle[None], at, rot)[0]
                    prot = (tip[1] - outer_face) * side
                    cand = {'n': p['n'], 'side': nm, 'at': [round(at[0], 2), round(at[1], 2), at[2]], 'rotate': rot, 'back_from_outer': back,
                            'muzzle_beyond_outer': round(float(prot), 2), 'axis_z': round(float(tip[2]), 2), 'opening_z': p['z']}
                    if best is None or back < best['back_from_outer']:
                        best = cand
                    break
            out.append(best)
            print(json.dumps(best, ensure_ascii=False))
    json.dump({'note': 'place_carronades.py 的結果（S rotate 0、P rotate 180；pivot 子作品 (7.5,42,0)；scale 0.5）', 'rows': out},
              open(os.path.join(HERE, 'carronades_placement.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
