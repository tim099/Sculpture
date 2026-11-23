# 海鷗號 新圖紙 04（TASK-0024 步驟 6）：裝飾 ⇒ masks/step6/hull_paint.vox.txt（船殼換色，overwrite）、
#   masks/deco/stem_head.vox.txt（艏柱頭渦卷，外部模型 deco=1）、verify_deco.json、sheet04_deco_v1.png
#   用法：python -I -X utf8 draft_deco.py [--probe=gull_x=3]
#   · 讀船殼的設計清單（masks/hull/hull_01.vox.txt）＋甲板清單，不讀作品 ⇒ 落格之後重跑一樣。
#   · 換色只動船殼「露在船外」的那一層（那一格往外一格是空的）；不加格、不刻格 ⇒ 重量、命中、走路都不變。
#   · 兩舷對稱：右舷算好、左舷照 y ↔ 2·YC − y 鏡過去。
#   出處：做法照星辰號 claude-baghlah-01m/design/draft_deco.py（船殼換色＋裝飾子作品）與收穫號的 draft_deco；圖案自己畫（Schellinks 1664 正面＋背面註記）。
import sys, os, json, math, hashlib, copy
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
NX, NY, NZ = 170, 161, 50
GULL = ['X...X',
        '.X.X.',
        '..X..']                                      # 白鷗（由上往下），設計決定；v3 縮成 5 格寬 ⇒ 圓牌外圈留得出黑邊


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    G = np.zeros((NX, NY, NZ), np.uint8)
    G[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
    return G


def outer_cell(H, x, z, YC):
    """右舷 (x, z) 那一排最外面的船殼格的 y（往外一格是空的）；中線的柱子（|dy| ≤ 1）不算。"""
    ys = np.where(H[x, YC + 2:, z] > 0)[0]
    if not len(ys):
        return None
    y = YC + 2 + int(ys.max())
    return y if H[x, y + 1, z] == 0 else None


def rail_top(H, x, YC):
    zs = np.where(H[x, YC + 2:, :].any(axis=0))[0]
    return int(zs.max()) if len(zs) else None


def build(plan, H, probe):
    L = HL.Lines(plan)
    YC = L.YC
    dc = {k: V(v) for k, v in plan['deco'].items() if k != 'src'}
    paint = {}                                          # (x, y, z) ⇒ 新色（右舷）
    # ── 蛇帶：黑底 3 排，中間金色正弦 ──
    sp = dc['serpent']
    x0, x1 = sp['x0'], sp['x1']
    zc0, zc1 = float(sp['zc0']), float(sp['zc1'])     # 帶的中線從船中往艏柱斜上（SCH 的亮帶；高度設計決定）
    band = {}
    wale = V(plan['hull_build']['colors']['wale'])
    top_c = V(plan['hull_build']['colors']['topside'])
    xmax = max(k[0] for k in zip(*np.nonzero(H)))
    for x in range(x0, xmax + 1):                      # 蛇帶那一段一直到艏柱，原本的白護舷帶（舷頂下第 3 格）改回木色：帶本身就是這一段的護舷帶（v2 只改到 x1 ⇒ 艏柱旁剩 6 格白，verifier456）
        for y, z in zip(*np.nonzero(H[x, YC + 2:, :] == wale)):   # 白護舷帶的每一格（不只最外一層：艏柱頂那兩格是從上面看得到的，verifier456）
            paint[(x, YC + 2 + int(y), int(z))] = top_c
    for x in range(x0, x1 + 1):
        zc = int(round(zc0 + (zc1 - zc0) * (x - x0) / (x1 - x0)))
        zt = rail_top(H, x, YC)
        zc = min(zc, zt - 2)                           # 帶頂至少在舷頂下一格
        band[x] = zc
        zs = zc + int(round(math.sin(2 * math.pi * (x - x0) / sp['period'])))
        for z in (zc - 1, zc, zc + 1):
            y = outer_cell(H, x, z, YC)
            if y is not None:
                paint[(x, y, z)] = sp['gold'] if z == zs else sp['ground']
    # ── 鑲板：帶頂以上到舷頂下一格；三塊的框黑、中心一朵金花；前端壁柱 ──
    pn = dc['panels']
    edges = [int(round(pn['x0'] + i * (pn['x1'] - pn['x0']) / pn['n'])) for i in range(pn['n'] + 1)]
    for x in range(pn['x0'], pn['x1'] + 1):
        zt = rail_top(H, x, YC)
        lo, hi = band[x] + 2, zt - 1
        if hi - lo < 1:
            continue
        for z in range(lo, hi + 1):
            y = outer_cell(H, x, z, YC)
            if y is None:
                continue
            if x in edges or z in (lo, hi):
                paint[(x, y, z)] = pn['frame']
    for i in range(pn['n']):
        cx = (edges[i] + edges[i + 1]) // 2
        lo, hi = band[cx] + 2, rail_top(H, cx, YC) - 1
        cz = (lo + hi) // 2
        if hi - lo < 2:
            continue                                   # 框裡沒有木色 ⇒ 不放花
        petals = ((1, 0), (-1, 0), (0, 1), (0, -1)) if hi - lo >= 4 else ((1, 0), (-1, 0))   # 框裡 3 排以上 ⇒ 十字花；1–2 排 ⇒ 左右兩瓣
        for dx, dz in ((0, 0),) + petals:
            y = outer_cell(H, cx + dx, cz + dz, YC)
            if y is not None and lo < cz + dz < hi:
                paint[(cx + dx, y, cz + dz)] = pn['rosette'] if (dx, dz) != (0, 0) else pn['frame']
    for x in range(pn['pilaster_x'][0], pn['pilaster_x'][1] + 1):
        zt = rail_top(H, x, YC)
        for z in range(band[x] + 2, zt):
            y = outer_cell(H, x, z, YC)
            if y is not None:
                paint[(x, y, z)] = pn['rosette'] if (z + x) % 2 == 0 and x == pn['pilaster_x'][0] + 1 else pn['frame']
    # ── 船尾兩舷的圓牌：黑底白鷗 ──
    gl = dc['gull']
    gx = gl['x'] + int(probe.get('gull_x', 0))
    gz = gl['z']
    for x in range(gx - 4, gx + 5):
        for z in range(gz - 3, gz + 4):
            if (x - gx) ** 2 + (z - gz) ** 2 <= 3.6 ** 2:
                y = outer_cell(H, x, z, YC)
                if y is not None:
                    paint[(x, y, z)] = gl['ground']
    for r, row in enumerate(GULL):
        for c, ch in enumerate(row):
            if ch == 'X':
                x, z = gx - len(row) // 2 + c, gz + 1 - r     # v3 前寫死 gx − 3（7 格寬那一版的偏移）⇒ 鷗偏 1 格
                y = outer_cell(H, x, z, YC)
                if y is not None:
                    paint[(x, y, z)] = gl['bird']
    # 左舷鏡過去；只留真的換了色的
    out = {}
    for (x, y, z), c in paint.items():
        for yy in (y, 2 * YC - y):
            if H[x, yy, z] and H[x, yy, z] != c:
                out[(x, yy, z)] = c
    # ── 艏柱頭渦卷（子作品，整船的框）──
    sh = dc['stem_head']
    cen = H[:, YC, :]
    zt = int(np.where(cen[100:, :].any(axis=0))[0].max())          # 艏柱頂那一層
    xs = np.where(cen[100:, zt] > 0)[0] + 100
    bx, bz = int(xs.max()), zt + 1                                  # 柱頂最前一格的正上方
    curl = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (-1, 4), (-2, 4), (-3, 4), (-3, 3), (-3, 2), (-2, 2)]   # 往船尾捲的鉤（6 連通；v1 有斜角相接 ⇒ 3 塊）
    S = {}
    for dx, dz in curl:
        for dy in (-1, 0, 1):
            S[(bx + dx, YC + dy, bz + dz)] = sh['color']
    return out, S, band, edges


def readings(plan, H, Dk, paint, S):
    L = HL.Lines(plan)
    YC = L.YC
    Hp = H.copy()
    for (x, y, z), c in paint.items():
        Hp[x, y, z] = c
    exposed_bad = sum(1 for (x, y, z) in paint if H[x, y + (1 if y > YC else -1), z] != 0)       # 不在舷側最外一層（往外一格不是空的）
    hidden = sum(1 for (x, y, z) in paint if all(H[x + dx, y + dy, z + dz] != 0 for dx, dy, dz in
                                                 ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))))   # 六面都被蓋住（從哪裡都看不到）
    new_cells = sum(1 for k in paint if H[k] == 0)
    mdiff = int((Hp != Hp[:, ::-1, :]).sum())
    st = np.zeros_like(H)
    for k, c in S.items():
        st[k] = c
    ov = int(((st > 0) & ((H > 0) | (Dk > 0))).sum())
    U = (H > 0) | (Dk > 0) | (st > 0)
    lab, n = ndimage.label(U)
    touch = int(ndimage.binary_dilation(st > 0) [H > 0].sum())
    return {'paint_cells': len(paint), 'paint_by_color': {str(c): sum(1 for v in paint.values() if v == c) for c in sorted(set(paint.values()))},
            'paint_not_on_outer_face': exposed_bad, 'paint_hidden_all_six_faces': hidden, 'paint_new_cells': new_cells, 'hull_after_paint_mirror_diff': mdiff,
            'stem_head': {'cells': len(S), 'overlap': ov, 'hull_cells_touching': touch, 'bbox': [list(map(int, np.min(list(S), axis=0))), list(map(int, np.max(list(S), axis=0)))],
                          'ship_plus_stem_components': int(n), 'mirror_diff': int((st != st[:, ::-1, :]).sum())}}


def sheet(plan, H, paint, S, R, path):
    L = HL.Lines(plan)
    YC = L.YC
    Hp = H.copy()
    for (x, y, z), c in paint.items():
        Hp[x, y, z] = c
    for k, c in S.items():
        Hp[k] = c
    s = 8
    img = Image.new('RGB', (NX * s + 80, 2 * 32 * s + 140), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((30, 10), 'al-Nawras - new sheet 04: decoration. starboard outside (bow right): serpent band gilded on black (Schellinks verso), panels, gull roundel; stem-head scroll (gold)', fill=(20, 20, 40), font=f)
    for row, (title, side) in enumerate((('starboard (+y) outside', 1), ('port (-y) outside, mirrored', -1))):
        oy = 40 + (row + 1) * 32 * s + row * 20
        d.text((30, oy - 32 * s - 4), title, fill=(20, 20, 40), font=f)
        for x in range(NX):
            for z in range(32):
                ys = np.where(Hp[x, :, z] > 0)[0]
                if len(ys):
                    y = ys.max() if side > 0 else ys.min()
                    xx = x if side > 0 else NX - 1 - x
                    d.rectangle([30 + xx * s, oy - (z + 1) * s, 30 + xx * s + s - 1, oy - z * s - 1], fill=rgb(int(Hp[x, y, z])))
    img.save(path)


def main():
    plan = HL.load_plan(HERE)
    probe = {}
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            k, v = a[len('--probe='):].split('=')
            probe[k] = float(v)
    H = load('masks/hull/hull_01.vox.txt')
    Dk = load('masks/decks/deck_main.vox.txt')
    paint, S, band, edges = build(plan, H, probe)
    R = readings(plan, H, Dk, paint, S)
    if probe:
        print(json.dumps({'probe': probe, 'R': R}, ensure_ascii=False))
        return
    out6 = os.path.join(HERE, 'masks', 'step6')
    outd = os.path.join(HERE, 'masks', 'deco')
    os.makedirs(out6, exist_ok=True)
    os.makedirs(outd, exist_ok=True)
    f1 = os.path.join(out6, 'hull_paint.vox.txt')
    with open(f1, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 海鷗號 船殼換色（draft_deco.py；stampvox overwrite=1）x,y,z,color —— at 0,0,0\n')
        f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, c) for (x, y, z), c in sorted(paint.items())) + '\n')
    f2 = os.path.join(outd, 'stem_head.vox.txt')
    with open(f2, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 海鷗號 艏柱頭渦卷（draft_deco.py）x,y,z,color —— 子作品用整船的框、at 0,0,0\n')
        f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, c) for (x, y, z), c in sorted(S.items())) + '\n')
    R['lists'] = [{'file': os.path.relpath(p, HERE).replace('\\', '/'), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()} for p in (f1, f2)]
    R['serpent_band_centre_z'] = {str(k): v for k, v in band.items() if k % 4 == 2}
    R['panel_edges_x'] = edges
    with open(os.path.join(HERE, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(plan, H, paint, S, R, os.path.join(HERE, 'sheet04_deco_v1.png'))
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
