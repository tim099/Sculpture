# 杉心號 甲板-main（TASK-1152 步驟 5）：坐板 7 塊＋船頭平台 ⇒ 清單 masks/deck/deck_main.vox.txt、讀數 verify_deck.json、甲板 meta decks_meta.tsv、圖 sheet02_deck_v1.png
#   用法：python -I -X utf8 draft_deck.py [--probe=seat_z=+1]
#   · 露天的獨木舟只有一層：站的地方是船殼自己的艙底（z 1 ＝ 底上第一層空氣），甲板子作品裡只有坐板與船頭平台。
#   · 坐板：每塊從左舷內面鋪到右舷內面（照船殼清單量那一層的艙內空格）⇒ 兩頭都貼著船殼。
#   · 走路格（照遊戲 navBuild 的規則：腳下實心、頭上 1.2 m ＝ 12 格空、四鄰一步高低差 ≤ 3 格）：艙底＋坐板頂要連成一塊 ——
#     坐板高了（一步 > 0.3 m）⇒ 艙底被坐板切成一段一段（--probe=seat_z=+1 反向對照）。
import sys, os, json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 140, 101, 40
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
    hollow = S & (H == 0)                                   # 船殼裡面的空氣
    T = V(plan['layout']['thwarts'])
    seat_z = T['top_z'] - 1 + int(probe.get('seat_z', 0))    # 坐板那一格（站面 ＝ seat_z ＋ 1）
    col = V(plan['deck_build']['colors'])
    D = np.zeros_like(H)
    parts = []
    for i, xc in enumerate(T['x']):
        for x in range(xc - T['width_x'] // 2, xc + T['width_x'] // 2 + 1):
            D[x, :, seat_z][hollow[x, :, seat_z]] = col['thwart']
        parts.append({'name': 'thwart-%d' % (i + 1), 'x': [xc - T['width_x'] // 2, xc + T['width_x'] // 2], 'z': seat_z})
    bp = V(plan['layout']['bow_platform'])
    for x in range(bp['x'][0], bp['x'][1] + 1):
        D[x, :, seat_z][hollow[x, :, seat_z]] = col['platform']
    parts.append({'name': 'bow-platform', 'x': bp['x'], 'z': seat_z})
    return L, H, S, D, parts


def bottom_floor(H, S):
    """每一站中線上艙底的第一層空氣（＝ 甲板 meta 的 floor）；那一站中線沒有艙內空氣 ⇒ 不列。"""
    hollow = S & (H == 0)
    fl = {}
    for x in range(SX):
        zs = np.where(hollow[x, 50])[0]
        if len(zs):
            fl[x] = int(zs.min())
    return fl


def walk_grid(occ, S, fl):
    """遊戲的走路格（簡化同 navBuild）：每一柱 (x, y) 在船殼範圍內、腳下實心、頭上 HEAD 格空、高度在那一站 floor −2～+3 的站點；
    四鄰高低差 ≤ STEP 連一起。⚠ 不限高度的話，人會沿著舷側內面一階一階的牆走上舷頂繞過坐板（v1 反向對照沒叫）。"""
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

    def f(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for (x, y, z), i in idx.items():
        for dx, dy in ((1, 0), (0, 1)):
            for z2 in stand.get((x + dx, y + dy), []):
                if abs(z2 - z) <= STEP:
                    a, b = f(i), f(idx[(x + dx, y + dy, z2)])
                    if a != b:
                        par[a] = b
    groups = {}
    for k, i in idx.items():
        groups.setdefault(f(i), []).append(k)
    return sorted(groups.values(), key=len, reverse=True)


def readings(L, H, S, D, parts):
    R = {'cells': int((D > 0).sum()), 'parts': parts}
    R['overlap_hull'] = int(((D > 0) & (H > 0)).sum())
    both = (D > 0) | (H > 0)
    R['components_with_hull'] = int(ndimage.label(both)[1])
    R['components_deck_alone'] = int(ndimage.label(D > 0)[1])
    R['mirror_diff'] = int(((D > 0) != (D > 0)[:, ::-1, :]).sum())
    # 每塊坐板兩頭都貼著船殼（坐板最外那一格的 y±1 是船殼）
    touch = []
    for p in parts:
        x0 = p['x'][0]
        ys = np.where(D[x0, :, p['z']] > 0)[0]
        touch.append(bool(H[x0, ys.min() - 1, p['z']] > 0 and H[x0, ys.max() + 1, p['z']] > 0) if len(ys) else False)
    R['all_parts_touch_both_walls'] = all(touch)
    fl = bottom_floor(H, S)
    R['_floor_by_x'] = fl
    G = walk_grid(both, S, fl)
    R['walk_groups'] = len(G)
    R['walk_main_cells'] = len(G[0]) if G else 0
    R['walk_main_m2'] = round(len(G[0]) * 0.01, 2) if G else 0
    R['walk_other_cells'] = [len(g) for g in G[1:6]]
    return R


def floor_meta(R, L):
    """甲板 meta floor：每一站中線艙底的第一層空氣 —— 只留轉折點（中間照線性內插）。"""
    fx = R['_floor_by_x']
    xs = sorted(fx)
    pts = [(xs[0], fx[xs[0]])]
    for a, b, c in zip(xs, xs[1:], xs[2:]):
        if fx[b] != fx[a] or fx[c] != fx[b]:
            pts.append((b, fx[b]))
    pts.append((xs[-1], fx[xs[-1]]))
    out = []
    for p in pts:
        if not out or out[-1] != p:
            out.append(p)
    return ','.join('%d:%d' % p for p in out)


def sheet(H, D, R, path):
    sc = 7
    W, Hh = SX * sc + 40, 60 + SY * sc // 2 + 40 + 16 * sc + 60
    im = Image.new('RGB', (W, Hh), (246, 240, 226))
    d = ImageDraw.Draw(im)
    f, fs = font(22), font(15)
    d.text((20, 10), '杉心號 新圖紙 02：坐板 7 塊、船頭平台（俯視、中線縱剖）', fill=(40, 30, 20), font=f)
    oy = 50
    A = np.where(D > 0, D, H)
    for x in range(SX):
        for y in range(0, SY, 2):
            nz = np.nonzero(A[x, y, :])[0]
            if len(nz):
                d.rectangle([20 + x * sc, oy + y // 2 * sc, 20 + x * sc + sc - 1, oy + y // 2 * sc + sc - 1], fill=rgb(int(A[x, y, nz[-1]])))
    oy2 = oy + SY * sc // 2 + 40 + 14 * sc
    for x in range(SX):                                    # 中線 y 50 縱剖
        for z in range(14):
            if A[x, 50, z]:
                d.rectangle([20 + x * sc, oy2 - z * sc, 20 + x * sc + sc - 1, oy2 - z * sc + sc - 1], fill=rgb(int(A[x, 50, z])))
    for x in range(0, SX, 10):
        d.text((20 + x * sc, oy2 + sc + 2), str(x), fill=(90, 80, 70), font=fs)
    d.text((20, Hh - 30), '坐板＋平台 %d 格｜疊船殼 %d｜跟船殼合起來元件 %d｜鏡像差 %d｜走路格 %d 群、主幹 %.2f m²｜兩頭都貼船殼 %s' % (
        R['cells'], R['overlap_hull'], R['components_with_hull'], R['mirror_diff'], R['walk_groups'], R['walk_main_m2'], R['all_parts_touch_both_walls']), fill=(40, 30, 20), font=fs)
    im.save(path)


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)
    plan = HL.load_plan()
    L, H, S, D, parts = build(plan, probe)
    R = readings(L, H, S, D, parts)
    fm = floor_meta(R, L)
    R['floor_meta'] = fm
    del R['_floor_by_x']
    if probe:
        print(json.dumps({'probe': probe, **{k: R[k] for k in ('walk_groups', 'walk_main_cells', 'walk_other_cells', 'overlap_hull', 'components_with_hull')}}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'deck'), exist_ok=True)
    pts = np.argwhere(D > 0)
    with open(os.path.join(HERE, 'masks', 'deck', 'deck_main.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 杉心號 甲板-main（draft_deck.py）x,y,z,color —— at 0,0,0\n')
        f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, D[x, y, z]) for x, y, z in pts) + '\n')
    m = V(plan['deck_build']['meta'])
    with open(os.path.join(HERE, 'decks_meta.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('link\t甲板-main\t%s\n' % json.dumps({'kind': 'deck', 'deck': m['deck'], 'level': m['level'], 'name': m['name'], 'floor': fm, 'thick': m['thick']}, ensure_ascii=False))
    with open(os.path.join(HERE, 'verify_deck.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(H, D, R, os.path.join(HERE, 'sheet02_deck_v1.png'))
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
