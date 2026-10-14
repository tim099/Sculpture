# 讀圖：Pl. LI 側面圖 gun deck 的方砲門（階段八，TASK-0538）⇒ readings_LI_ports.json ＋ readings/LI_ports_trace.png
# 用法：python read_ports.py <Pl. LI tif>
#   · 起點：每個砲門左緣與上緣的大概位置（先用「每一欄最長的黑段 140–200 px、相距約 167 px 成對」掃出來的，2026-10-14）。
#   · 四邊各自找線心：左右邊 ＝ 砲門中段那幾列裡、黑的比例 ≥ 0.6 的連續欄的中點；上下邊 ＝ 中段那幾欄裡、黑的比例 ≥ 0.6 的連續列的中點。
#   · 換成底圖 m：x ＝ (px − 1698.6) / 219.4、z ＝ (6756 − py) / 219.4（readings_LI.json 的 datum）。
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, 'readings_LI.json'), encoding='utf-8'))
PXM, X0P, KT = R['px_per_m'], R['datum']['x0_px'], R['datum']['keel_top_py']
APPROX = [(2051, 4726), (2797, 4779), (3596, 4824), (4397, 4857), (5200, 4881), (5932, 4897),
          (6633, 4905), (7334, 4905), (8034, 4897), (8839, 4872), (9551, 4838)]
W0 = 167


def runs(mask):
    out, a = [], None
    for i, v in enumerate(mask):
        if v and a is None:
            a = i
        if not v and a is not None:
            out.append((a, i - 1)); a = None
    if a is not None:
        out.append((a, len(mask) - 1))
    return out


def line_near(prof, want, lo, hi, thr=0.6):
    """prof 是黑的比例；在 [lo, hi] 找黑的比例 ≥ thr 的連續段，取中點最接近 want 的那段 ⇒ (中點, 寬)"""
    best = None
    for a, b in runs(prof >= thr):
        if b < lo or a > hi:
            continue
        c = (a + b) / 2
        if best is None or abs(c - want) < abs(best[0] - want):
            best = (c, b - a + 1)
    return best


def main():
    im = Image.open(sys.argv[1])
    out, ov = [], []
    for n, (xl, yt) in enumerate(APPROX, 1):
        x0, y0 = xl - 40, yt - 40
        a = ~np.array(im.crop((x0, y0, xl + W0 + 40, yt + W0 + 40)))      # True ＝ 黑
        h, w = a.shape
        # 中段：上下各讓 40 px（避開四角與上下邊）
        rows = a[40 + 40:40 + W0 - 40, :]
        colp = rows.mean(0)
        L = line_near(colp, 40, 25, 55)
        Rr = line_near(colp, 40 + W0, 40 + W0 - 20, 40 + W0 + 25)
        cols = a[:, 40 + 40:40 + W0 - 40]
        rowp = cols.mean(1)
        T = line_near(rowp, 40, 25, 55)
        B = line_near(rowp, 40 + W0, 40 + W0 - 20, 40 + W0 + 25)
        rec = {'n': n, 'approx_px': [xl, yt]}
        if None in (L, Rr, T, B):
            rec['missing'] = [k for k, v in zip('LRTB', (L, Rr, T, B)) if v is None]
            out.append(rec)
            continue
        px = {'aft': x0 + L[0], 'fwd': x0 + Rr[0], 'top': y0 + T[0], 'bottom': y0 + B[0]}
        rec.update({'px': {k: round(v, 1) for k, v in px.items()},
                    'line_width_px': {'aft': L[1], 'fwd': Rr[1], 'top': T[1], 'bottom': B[1]},
                    'x_aft': round((px['aft'] - X0P) / PXM, 3), 'x_fwd': round((px['fwd'] - X0P) / PXM, 3),
                    'z_sill': round((KT - px['bottom']) / PXM, 3), 'z_lintel': round((KT - px['top']) / PXM, 3)})
        out.append(rec)
        ov.append((n, x0, y0, px))
    json.dump({'source': 'Chapman 1768 Pl. LI 側面圖 gun deck 方砲門（read_ports.py）',
               'note': '線心（不是內緣）；底圖 m、x 原點 ＝ readings_LI.json datum（船尾柱後面在龍骨頂 px 1698.6）、z ＝ 龍骨頂起',
               'ports': out}, open(os.path.join(HERE, 'readings_LI_ports.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    # 疊圖：每個砲門一格、放大 2 倍、紅線 ＝ 讀到的四條線心
    tiles = []
    for n, x0, y0, px in ov:
        t = im.crop((x0, y0, x0 + W0 + 80, y0 + W0 + 80)).convert('RGB')
        d = ImageDraw.Draw(t)
        for k in ('aft', 'fwd'):
            d.line([(px[k] - x0, 0), (px[k] - x0, t.size[1])], fill=(230, 30, 30))
        for k in ('top', 'bottom'):
            d.line([(0, px[k] - y0), (t.size[0], px[k] - y0)], fill=(230, 30, 30))
        d.text((3, 3), str(n), fill=(0, 0, 255))
        tiles.append(t.resize((t.size[0] * 2, t.size[1] * 2), Image.NEAREST))
    W = sum(t.size[0] for t in tiles[:6]) + 60
    canvas = Image.new('RGB', (W, 2 * tiles[0].size[1] + 30), (255, 255, 255))
    ox = 0
    for i, t in enumerate(tiles):
        if i == 6:
            ox = 0
        canvas.paste(t, (ox, 0 if i < 6 else tiles[0].size[1] + 20))
        ox += t.size[0] + 10
    canvas.save(os.path.join(HERE, 'readings', 'LI_ports_trace.png'))
    for r in out:
        print(r['n'], r.get('missing') or (r['x_aft'], r['x_fwd'], r['z_sill'], r['z_lintel'], r['line_width_px']))


if __name__ == '__main__':
    main()
