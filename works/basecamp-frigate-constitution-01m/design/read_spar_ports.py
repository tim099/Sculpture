"""
階段二十九 讀圖：11 號（1927 MIT PLAN VIII）sheer plan 上 spar deck 那排砲門（舷牆上的方框；船尾 quarterdeck 8 個、船頭 forecastle 4 個）。
方法：每一組在 sheer plan 上的範圍裡逐欄數「亮像素」（> 背景＋40）⇒ 豎線是峰（高度 ≈ 砲門高）；相鄰兩條間距 40–95 px 的配成一個砲門的左右緣
（亞像素：峰附近三欄加權）。每條豎線往上往下找連續亮的範圍 ⇒ 上下端點 ＝ 上緣／下緣（取左右兩條的平均）。
換算（同 source_ports.json／source_ends_raw.json readings[1]）：
  u ＝ x − 0.013·(y − 2200)、X ＝ 0.16249533·u ＋ 18.3504
  Z_sheer ＝ (y_keel(x) − y)·0.15859、y_keel ＝ −0.02644·x ＋ 2414.74
  Z ＝ 62.86 ＋ (Z_sheer − Z_LWL(X))／0.15859 × 9.144／(58.38 − 0.000281·x_px)、Z_LWL ＝ −0.0153747·X ＋ 69.613（plan.json ends.provenance.frame_of_heights）
用法：python -I read_spar_ports.py ⇒ source_ports_spar.json
"""
import json, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, '..', '..', '..', 'references', 'uss-constitution-1927', 'RG19_ALPHA_Constitution_1797_11.JPG')
GROUPS = [('quarterdeck', (640, 2130), (1575, 1680)), ('forecastle', (3070, 3660), (1555, 1665))]


def X_of(x, y):
    return 0.16249533 * (x - 0.013 * (y - 2200)) + 18.3504


def Z_of(x, y):
    X = X_of(x, y)
    zs = (-0.02644 * x + 2414.74 - y) * 0.15859
    xpx = (X - 18.3504) / 0.16249533
    return 62.86 + (zs - (-0.0153747 * X + 69.613)) / 0.15859 * 9.144 / (58.38 - 0.000281 * xpx)


def main():
    im = np.asarray(Image.open(IMG).convert('L'), dtype=float)
    out = {'note': __doc__.strip().split('\n')[0], 'source_image': 'references/uss-constitution-1927/RG19_ALPHA_Constitution_1797_11.JPG', 'ports': []}
    n = 0
    for name, (x0, x1), (y0, y1) in GROUPS:
        band = im[y0:y1, x0:x1]
        bg = np.median(band)
        bright = band > bg + 40
        # 豎線：逐欄數亮像素（只算砲門高度那一段的中間，避開上下的長橫線）
        mid = bright[12:-12, :]
        colcount = mid.sum(0).astype(float)
        thr = 0.5 * mid.shape[0]
        peaks = []
        c = 0
        while c < len(colcount):
            if colcount[c] >= thr:
                s = c
                while c < len(colcount) and colcount[c] >= thr:
                    c += 1
                xs = np.arange(s, c)
                w = colcount[s:c]
                peaks.append(float((xs * w).sum() / w.sum()) + x0)
            c += 1
        # 配對：相鄰兩條間距 40–80 px ⇒ 一個砲門（用過的不再用）
        i = 0
        while i + 1 < len(peaks):
            L, R = peaks[i], peaks[i + 1]
            if 40 <= R - L <= 95:   # 船頭最前面那個比較寬（約 88 px）
                ends = []
                for xl in (L, R):
                    col = im[:, int(round(xl)) - 1:int(round(xl)) + 2].max(1)
                    yc = (y0 + y1) // 2
                    if col[yc] <= bg + 40:
                        yc = y0 + 12 + int(np.argmax(bright[12:-12, int(round(xl)) - x0]))
                    a = yc
                    while a > y0 - 30 and col[a - 1] > bg + 40:
                        a -= 1
                    b = yc
                    while b < y1 + 30 and col[b + 1] > bg + 40:
                        b += 1
                    ends.append((a, b))
                T = (ends[0][0] + ends[1][0]) / 2.0
                B = (ends[0][1] + ends[1][1]) / 2.0
                n += 1
                xm = (L + R) / 2
                out['ports'].append({'n': n, 'group': name, 'px': {'L': round(L, 1), 'R': round(R, 1), 'T': T, 'B': B},
                                     'X_aft': round(X_of(L, (T + B) / 2), 2), 'X_fwd': round(X_of(R, (T + B) / 2), 2),
                                     'lintel': round(Z_of(xm, T), 2), 'sill': round(Z_of(xm, B), 2)})
                i += 2
            else:
                i += 1
    with open(os.path.join(HERE, 'source_ports_spar.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for p in out['ports']:
        print(p['n'], p['group'], p['X_aft'], p['X_fwd'], 'w', round(p['X_fwd'] - p['X_aft'], 2), 'sill', p['sill'], 'lintel', p['lintel'], p['px'])


if __name__ == '__main__':
    main()
