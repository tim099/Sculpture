# 來源：改寫自 basecamp-piragua-01m/design/draft_deck.py，依突尼斯湖轉運划艇 Sandal 實尺寸調整
# 步驟 5 甲板設計（kiara-tunis-sandal-01m-deck-main）：
#   - 艙底鋪板（z=1，站面 z=2，x=30..86），於 (80..82,49..51) 設深木桅座
#   - 三對划手坐板（x=35, 43, 81，板 z=4／頂面 z=5，x=81 中央留 3×3 桅孔）、留空舯貨艙 x=46..78
#   - 艉舵手平台（x=21..29，板 z=4／頂 z=5）與艏甲板平台（x=87..105，板 z=4／頂 z=5）
#   用法：python -I -X utf8 draft_deck.py [--probe=seat_z=+1]
import sys, os, json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 136, 101, 30
YC = 50
HEAD, STEP = 12, 3


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def load_hull():
    a = np.loadtxt(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    H = np.zeros((SX, SY, SZ), np.uint8)
    H[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
    return H


def build(plan, probe):
    L = HL.Lines(plan)
    H = load_hull()
    S = L.solid(0, SX - 1, SZ - 1, 0)
    hollow = S & (H == 0)

    fl_cfg = V(plan['layout']['floor'])
    tw_cfg = V(plan['layout']['thwarts'])
    sd_cfg = V(plan['layout']['stern_deck'])
    fd_cfg = V(plan['layout']['fore_deck'])
    col = V(plan['deck_build']['colors'])

    dz_seat = int(probe.get('seat_z', 0))
    zb = int(fl_cfg['z_board'])
    tw_z = int(tw_cfg['board_z']) + dz_seat
    sd_z = int(sd_cfg['board_z']) + dz_seat
    fd_z = int(fd_cfg['board_z']) + dz_seat

    D = np.zeros_like(H)
    parts = []

    # 1. 艙底鋪板（z=1，站面 z=2）：縱向木條紋對稱鋪於兩舷之間，(80..82, 49..51) 設深木桅座底墊
    mx0, mx1 = tw_cfg['mast_hole_x']
    my0, my1 = tw_cfg['mast_hole_y']
    for x in range(int(fl_cfg['x0']), int(fl_cfg['x1']) + 1):
        ys = np.where(hollow[x, :, zb])[0]
        for y in ys:
            if mx0 <= x <= mx1 and my0 <= y <= my1:
                D[x, y, zb] = col['seam']
            elif abs(y - YC) % 4 == 2:
                D[x, y, zb] = col['seam']
            else:
                D[x, y, zb] = col['plank']
    parts.append({'name': 'duckboards', 'x': [int(fl_cfg['x0']), int(fl_cfg['x1'])], 'z': zb})

    # 2. 艉舵手半甲板
    for x in range(int(sd_cfg['x0']), int(sd_cfg['x1']) + 1):
        mask = hollow[x, :, sd_z]
        D[x, mask, sd_z] = col['trim'] if x == int(sd_cfg['x1']) else col['platform']
    parts.append({'name': 'stern-platform', 'x': [int(sd_cfg['x0']), int(sd_cfg['x1'])], 'z': sd_z})

    # 3. 三對槳手坐板（前座 x=81 中央留 3×3 桅孔）
    wx = int(tw_cfg['width_x']) // 2
    for i, xc in enumerate(tw_cfg['x'], 1):
        has_hole = (i == 3)
        for x in range(xc - wx, xc + wx + 1):
            ys = np.where(hollow[x, :, tw_z])[0]
            for y in ys:
                if has_hole and mx0 <= x <= mx1 and my0 <= y <= my1:
                    continue
                D[x, y, tw_z] = col['thwart']
        parts.append({'name': f'thwart-{i}', 'x': [xc - wx, xc + wx], 'z': tw_z, 'mast_hole': has_hole})

    # 4. 艏甲板平台
    for x in range(int(fd_cfg['x0']), int(fd_cfg['x1']) + 1):
        mask = hollow[x, :, fd_z]
        D[x, mask, fd_z] = col['trim'] if x == int(fd_cfg['x0']) else col['platform']
    parts.append({'name': 'bow-platform', 'x': [int(fd_cfg['x0']), int(fd_cfg['x1'])], 'z': fd_z})

    return L, H, S, D, parts, {'duck_x': [int(fl_cfg['x0']), int(fl_cfg['x1'])], 'zb': zb, 'sd_z': sd_z, 'fd_z': fd_z}


def floor_map(H, D, S, cfg, sd_cfg, fd_cfg):
    """計算甲板 meta floor（每一站的第一層走路空氣高度）：
    - 艉平台段 x0..x1 -> sd_z + 1
    - 艙底鋪板段 -> zb + 1
    - 艏平台段 -> fd_z + 1
    """
    fl = {}
    for x in range(int(sd_cfg['x0']), int(sd_cfg['x1']) + 1):
        if (D[x, :, cfg['sd_z']] > 0).any():
            fl[x] = cfg['sd_z'] + 1
    for x in range(cfg['duck_x'][0], cfg['duck_x'][1] + 1):
        if (D[x, :, cfg['zb']] > 0).any():
            fl[x] = cfg['zb'] + 1
    for x in range(int(fd_cfg['x0']), int(fd_cfg['x1']) + 1):
        if (D[x, :, cfg['fd_z']] > 0).any():
            fl[x] = cfg['fd_z'] + 1
    return fl


def walk_grid(occ, S, fl):
    """照遊戲 navBuild 規則量走路格連通性（腳下實心、頭上 1.2 m 空、站高落於 floor −2..+3、四鄰一步高差 ≤ 3）。"""
    stand = {}
    for x in range(SX):
        if x not in fl:
            continue
        for y in range(SY):
            if not S[x, y].any():
                continue
            for z in range(max(1, fl[x] - 2), min(SZ - HEAD, fl[x] + 4)):
                if occ[x, y, z - 1] and not occ[x, y, z:z + HEAD].any():
                    stand.setdefault((x, y), []).append(z)
    idx = {}
    for (x, y), zs in stand.items():
        for z in zs:
            idx[(x, y, z)] = len(idx)
    par = list(range(len(idx)))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    for (x, y, z), i in idx.items():
        for dx, dy in ((1, 0), (0, 1)):
            for z2 in stand.get((x + dx, y + dy), []):
                if abs(z2 - z) <= STEP:
                    a, b = find(i), find(idx[(x + dx, y + dy, z2)])
                    if a != b:
                        par[a] = b

    groups = {}
    for k, i in idx.items():
        groups.setdefault(find(i), []).append(k)
    return sorted(groups.values(), key=len, reverse=True)


def floor_meta_str(fl):
    xs = sorted(fl)
    pts = [(xs[0], fl[xs[0]])]
    for a, b, c in zip(xs, xs[1:], xs[2:]):
        if fl[b] != fl[a] or fl[c] != fl[b] or (b - a) > 1 or (c - b) > 1:
            pts.append((b, fl[b]))
    pts.append((xs[-1], fl[xs[-1]]))
    out = []
    for p in pts:
        if not out or out[-1] != p:
            out.append(p)
    return ','.join(f'{x}:{z}' for x, z in out)


def readings(plan, H, S, D, parts, cfg):
    occ = (D > 0) | (H > 0)
    _, n_comp = ndimage.label(occ)
    _, n_deck = ndimage.label(D > 0)
    la, na = ndimage.label(~occ)
    border = set(np.unique(np.r_[
        la[0].ravel(), la[-1].ravel(),
        la[:, 0].ravel(), la[:, -1].ravel(),
        la[:, :, 0].ravel(), la[:, :, -1].ravel(),
    ]))
    cavities = len([i for i in range(1, na + 1) if i not in border])

    # 兩端貼壁檢查（坐板 3 若有桅孔則分別檢查左／右舷外側貼壁與內側開孔）
    touch = []
    for p in parts:
        x0 = (p['x'][0] + p['x'][1]) // 2
        z = p['z']
        ys = np.where(D[x0, :, z] > 0)[0]
        ok = bool(len(ys) and H[x0, ys.min() - 1, z] > 0 and H[x0, ys.max() + 1, z] > 0)
        touch.append(ok)

    # 貨艙 x=46..78 實際淨寬（z=2 起算、不被坐板或船殼擋住的柱數）
    cb = V(plan['layout']['cargo_bay'])
    cargo_cols = []
    for x in range(int(cb['x0']), int(cb['x1']) + 1):
        clear_y = [int(y) for y in range(SY) if D[x, y, cfg['zb']] > 0 and not occ[x, y, cfg['zb'] + 1:SZ].any()]
        cargo_cols.append(len(clear_y))

    # 檢查 3×3 桅孔 (80..82, 49..51, z=2..12) 淨空
    tw_cfg = V(plan['layout']['thwarts'])
    mx0, mx1 = tw_cfg['mast_hole_x']
    my0, my1 = tw_cfg['mast_hole_y']
    mast_hole_blocked = int(occ[mx0:mx1 + 1, my0:my1 + 1, 2:13].sum())

    fl = floor_map(H, D, S, cfg, V(plan['layout']['stern_deck']), V(plan['layout']['fore_deck']))
    G = walk_grid(occ, S, fl)

    R = {
        'cells': int((D > 0).sum()),
        'parts': parts,
        'overlap_hull': int(((D > 0) & (H > 0)).sum()),
        'mast_hole_blocked': mast_hole_blocked,
        'components_with_hull': int(n_comp),
        'components_deck_alone': int(n_deck),
        'cavities_with_hull': int(cavities),
        'mirror_diff': int(((D > 0) != (D > 0)[:, ::-1, :]).sum()),
        'mirror_color_diff': int((D != D[:, ::-1, :]).sum()),
        'all_parts_touch_both_walls': all(touch),
        'cargo_bay_floor_cols': int(sum(cargo_cols)),
        'cargo_bay_min_width': int(min(cargo_cols)),
        'cargo_bay_max_width': int(max(cargo_cols)),
        'walk_groups': len(G),
        'walk_main_cells': len(G[0]) if G else 0,
        'walk_main_m2': round(len(G[0]) * 0.01, 2) if G else 0.0,
        'walk_other_cells': [len(g) for g in G[1:6]],
        'floor_meta': floor_meta_str(fl),
    }
    return R


def sheet(H, D, R, path):
    sc = 8
    top_h = SY * sc // 2
    side_h = 22 * sc
    W = SX * sc + 40
    Hh = 60 + top_h + 30 + side_h + 60
    im = Image.new('RGB', (W, Hh), (246, 240, 226))
    d = ImageDraw.Draw(im)
    f, fs = font(21), font(14)
    d.text((20, 10), '突尼斯湖轉運艇 Sandal 新圖紙 02：艙底鋪板、坐板、艏艉平台與桅孔（俯視、中線縱剖）', fill=(40, 30, 20), font=f)
    oy = 50
    A = np.where(D > 0, D, H)
    sc_y = max(sc // 2, 4)
    for x in range(SX):
        for y in range(SY):
            nz = np.nonzero(A[x, y, :])[0]
            if len(nz):
                py = oy + y * sc_y
                d.rectangle([20 + x * sc, py, 20 + x * sc + sc - 1, py + sc_y - 1], fill=rgb(int(A[x, y, nz[-1]])))
    oy2 = oy + top_h + 25 + 16 * sc
    for x in range(SX):
        for z in range(15):
            if A[x, YC, z]:
                d.rectangle([20 + x * sc, oy2 - z * sc, 20 + x * sc + sc - 1, oy2 - z * sc + sc - 1], fill=rgb(int(A[x, YC, z])))
    for x in range(0, SX, 10):
        d.text((20 + x * sc, oy2 + sc + 2), str(x), fill=(90, 80, 70), font=fs)
    d.text((20, Hh - 30), '甲板 %d 格｜疊船殼 %d｜桅孔阻擋 %d｜合體元件 %d｜空腔 %d｜鏡像差 %d｜走路格 %d 群 (%.2f m²)｜貨艙地板 %d 格 (寬 %d–%d)' % (
        R['cells'], R['overlap_hull'], R['mast_hole_blocked'], R['components_with_hull'], R['cavities_with_hull'],
        R['mirror_diff'], R['walk_groups'], R['walk_main_m2'], R['cargo_bay_floor_cols'],
        R['cargo_bay_min_width'], R['cargo_bay_max_width']), fill=(40, 30, 20), font=fs)
    im.save(path)


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)
    plan = HL.load_plan()
    L, H, S, D, parts, cfg = build(plan, probe)
    R = readings(plan, H, S, D, parts, cfg)
    if probe:
        print(json.dumps({
            'probe': probe,
            **{k: R[k] for k in ('walk_groups', 'walk_main_cells', 'walk_other_cells', 'overlap_hull', 'components_with_hull', 'cavities_with_hull')}
        }, ensure_ascii=False))
        return

    os.makedirs(os.path.join(HERE, 'masks', 'deck'), exist_ok=True)
    pts = np.argwhere(D > 0)
    with open(os.path.join(HERE, 'masks', 'deck', 'deck_main.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 突尼斯湖轉運艇 Sandal 主甲板／鋪板與坐板（draft_deck.py）x,y,z,color —— at 0,0,0\n')
        for x, y, z in pts:
            f.write(f'{x},{y},{z},{D[x, y, z]}\n')

    meta = dict(V(plan['deck_build']['meta']))
    meta['floor'] = R['floor_meta']
    with open(os.path.join(HERE, 'decks_meta.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(f"link\t甲板-main\t{json.dumps(meta, ensure_ascii=False)}\n")

    with open(os.path.join(HERE, 'verify_deck.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, indent=1, ensure_ascii=False)

    sheet(H, D, R, os.path.join(HERE, 'sheet02_deck_v1.png'))
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
