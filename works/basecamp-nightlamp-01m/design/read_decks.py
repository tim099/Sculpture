# 讀圖：Pl. LI 側面圖的甲板線（階段九，TASK-0538）⇒ readings_LI_decks.json ＋ readings/LI_decks_trace.png
# 用法：python read_decks.py <Pl. LI tif>
#   · 甲板在側面圖畫成虛線（看不見的線）。每一條從一個「看得清楚的起點」出發，每 0.25 底圖 m 往兩邊走一步：
#     在上一步外插的高度 ±tol 內找「虛線」（那一段 ±40 px 欄裡黑的比例 0.25–0.85、厚 ≤ 9 px 的連續列），找到就接上、找不到記一格空（連 gap 步找不到就停）。
#   · 起點（2026-10-14 先掃各欄的線清單挑的）：上甲板 x 22.0 z 7.36（絞盤下半截的底座就站在這條線上）、下甲板 x 28.0 z 5.46、
#     走道／後甲板／前甲板那一層 x 22.0 z 9.75。
#   · 換算：x ＝ (px − 1698.6) / 219.4、z ＝ (6756 − py) / 219.4（readings_LI.json 的 datum）。
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, 'readings_LI.json'), encoding='utf-8'))
PXM, X0P, KT = R['px_per_m'], R['datum']['x0_px'], R['datum']['keel_top_py']
Y0 = 3300
LINES = {
    'upper_deck': {'x0': 22.0, 'z0': 7.36, 'x_range': [-1.0, 40.0]},
    'lower_deck': {'x0': 28.0, 'z0': 5.46, 'x_range': [-1.0, 40.0]},
    'gangway_level': {'x0': 22.0, 'z0': 9.75, 'x_range': [-1.0, 40.0]},
}
STEP, TOL, GAP = 0.25, 0.05, 6


def main():
    im = Image.open(sys.argv[1])
    A = ~np.array(im.crop((0, Y0, im.size[0], 7000)))

    def dashed_rows(xm, zc, tol):
        px = int(round(X0P + xm * PXM))
        col = A[:, px - 40:px + 40].mean(1)
        lo, hi = int(KT - (zc + tol) * PXM) - Y0, int(KT - (zc - tol) * PXM) - Y0
        out, i = [], lo
        while i <= hi:
            if col[i] > 0.25:
                j = i
                while j < len(col) and col[j] > 0.25:
                    j += 1
                m = float(col[i:j].max())
                if m < 0.85 and j - i <= 9:
                    out.append(((KT - (Y0 + (i + j - 1) / 2)) / PXM, m))
                i = j
            else:
                i += 1
        return out

    res = {}
    for name, L in LINES.items():
        pts = {L['x0']: L['z0']}
        for d in (1, -1):
            xs, zs = [L['x0']], [L['z0']]
            miss, x = 0, L['x0']
            while L['x_range'][0] <= x + d * STEP <= L['x_range'][1] and miss < GAP:
                x = round(x + d * STEP, 3)
                if len(xs) >= 2:
                    k = np.polyfit(xs[-6:], zs[-6:], 1)
                    zp = float(np.polyval(k, x))
                else:
                    zp = zs[-1]
                cand = dashed_rows(x, zp, TOL)
                if not cand:
                    miss += 1
                    continue
                z = min(cand, key=lambda c: abs(c[0] - zp))[0]
                miss = 0
                xs.append(x)
                zs.append(z)
                pts[x] = round(z, 3)
        res[name] = sorted(pts.items())
    json.dump({'source': 'Chapman 1768 Pl. LI 側面圖 甲板虛線（read_decks.py）', 'step_m': STEP, 'tol_m': TOL,
               'note': '虛線的線心；底圖 m；x 原點 ＝ readings_LI.json datum。每條從起點往兩邊追，連 %d 步找不到就停' % GAP,
               'lines': {k: [[x, z] for x, z in v] for k, v in res.items()}},
              open(os.path.join(HERE, 'readings_LI_decks.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    # 疊圖：側面圖（x −1..40、z 4..12.5）縮 1/4，追到的點標紅（上甲板）、藍（下甲板）、綠（走道那一層）
    x0p, x1p = int(X0P - 1 * PXM), int(X0P + 40 * PXM)
    y0p, y1p = int(KT - 12.5 * PXM), int(KT - 4 * PXM)
    t = im.crop((x0p, y0p, x1p, y1p)).convert('RGB')
    t = t.resize((t.size[0] // 4, t.size[1] // 4), Image.LANCZOS)
    dr = ImageDraw.Draw(t)
    col = {'upper_deck': (230, 30, 30), 'lower_deck': (30, 60, 230), 'gangway_level': (20, 160, 40)}
    for k, v in res.items():
        for x, z in v:
            px, py = (X0P + x * PXM - x0p) / 4, (KT - z * PXM - y0p) / 4
            dr.ellipse([px - 2, py - 2, px + 2, py + 2], outline=col[k])
    t.save(os.path.join(HERE, 'readings', 'LI_decks_trace.png'))
    for k, v in res.items():
        print(k, len(v), 'x %.2f..%.2f' % (v[0][0], v[-1][0]), ' '.join('%.1f:%.2f' % (x, z) for x, z in v[::4]))


if __name__ == '__main__':
    main()
