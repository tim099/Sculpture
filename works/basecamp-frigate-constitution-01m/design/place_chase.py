"""
18 磅 chase gun 擺進 gun deck 第 15 個砲門（S 舷船頭；階段二十八）—— 外部模型（子作品 -gun-long18，0.05 m ⇒ 縮 0.5）。

擺法（照實船「推出去、砲架前緣頂到下檻」）：每一個角度 φ（繞 Z，負 ＝ 砲口往船頭偏）、每一個橫向偏移，
沿砲身方向從砲門往裡退，退到「模型的每一格（格心＋八個角往裡縮 0.2）都不落在組裝件的實心格裡」為止 ⇒ 那就是推得最出去的位置。
再要求：砲口那一點在船殼外（不在實心格、而且越過下檻外面那一層）。印出每個角度的結果，挑「最往前、還推得出去」的那個。

用法：python -I place_chase.py <組裝件格子清單.txt>（export format=list 的輸出）
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SCALE = 0.5                       # 0.05 m ÷ 0.1 m
DECK_Z = 88.0                     # gun deck 面（x ≥ 633）
PORT = {'x': (641, 653), 'z': (94, 105), 'sill_y_in': 187, 'sill_y_out': 192}


def load_grid(path):
    a = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    m = a[(a[:, 0] >= 560) & (a[:, 0] < 720) & (a[:, 2] < 140)]
    G = np.zeros((160, 320, 140), bool)
    G[m[:, 0] - 560, m[:, 1], m[:, 2]] = True
    return G


def gun_cells():
    pts = []
    for line in open(os.path.join(HERE, 'masks', 'guns2', 'long18.vox.txt'), encoding='utf-8'):
        if line.startswith('#') or not line.strip():
            continue
        x, y, z, c = map(int, line.split(','))
        pts.append((x, y, z))
    return np.array(pts, float)


def transform(p, pivot, at, phi_deg):
    q = (p - pivot) * SCALE
    c, s = math.cos(math.radians(phi_deg)), math.sin(math.radians(phi_deg))
    x = q[..., 0] * c - q[..., 1] * s
    y = q[..., 0] * s + q[..., 1] * c
    return np.stack([x + at[0], y + at[1], q[..., 2] + at[2]], -1)


def hits(G, P):
    i = np.floor(P).astype(int)
    i[..., 0] -= 560
    ok = (i[..., 0] >= 0) & (i[..., 0] < 160) & (i[..., 1] >= 0) & (i[..., 1] < 320) & (i[..., 2] >= 0) & (i[..., 2] < 140)
    out = np.zeros(i.shape[:-1], bool)
    out[ok] = G[i[ok][:, 0], i[ok][:, 1], i[ok][:, 2]]
    return out


def main():
    G = load_grid(sys.argv[1])
    cells = gun_cells()
    # 每一格取格心＋八個角往裡縮 0.2（模型格 0.5 ship 格 ⇒ 樣本間距 ≤ 0.3）
    offs = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
    samples = (cells[:, None, :] + offs[None, :, :]).reshape(-1, 3)
    pivot = np.array([13.5, 38.5, 0.0])          # 砲架前 transom 的中間、甲板那一層（子作品座標）
    muzzle = np.array([13.5, 62.0, 21.5])        # 砲口那一點（軸上、最前面）
    xc = (PORT['x'][0] + PORT['x'][1] + 1) / 2.0
    rows = []
    for phi in [-5.0 * k for k in range(0, 13)]:
        best = None
        th = math.radians(phi)
        d_out = np.array([-math.sin(th), math.cos(th)])   # 砲口方向（xy）
        d_side = np.array([math.cos(th), math.sin(th)])
        for side in [x * 0.5 for x in range(-8, 9)]:
            for back in [0.5 * k for k in range(0, 60)]:  # 從下檻內面往裡退
                base = np.array([xc, PORT['sill_y_in']]) + d_side * side - d_out * back
                at = (base[0], base[1], DECK_Z)
                P = transform(samples, pivot, at, phi)
                if hits(G, P).any():
                    continue
                tip = transform(muzzle[None, :], pivot, at, phi)[0]
                tip_out = not hits(G, tip[None, :])[0] and tip[1] > PORT['sill_y_out'] - 0.5
                cand = {'phi': phi, 'side': side, 'back': back, 'at': [round(at[0], 3), round(at[1], 3), at[2]], 'tip': [round(float(v), 2) for v in tip], 'tip_out': bool(tip_out)}
                if best is None or (cand['tip_out'] and not best['tip_out']) or (cand['tip_out'] == best['tip_out'] and back < best['back']):
                    best = cand
                break
        rows.append(best)
        print(json.dumps(best, ensure_ascii=False))
    ok = [r for r in rows if r and r['tip_out']]
    with open(os.path.join(HERE, 'chase_placement.json'), 'w', encoding='utf-8') as f:
        json.dump({'note': 'place_chase.py 的搜尋結果（每個角度推得最出去的位置；tip_out ＝ 砲口在船殼外）', 'rows': rows}, f, ensure_ascii=False, indent=1)
    print('砲口推得出去的角度：', [r['phi'] for r in ok])


if __name__ == '__main__':
    main()
