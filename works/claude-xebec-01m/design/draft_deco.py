# 利劍號 新圖紙 04（TASK-0022 步驟 6）：裝飾 ⇒ masks/deco/{beak,platform,awning,glass}.vox.txt、masks/step6/hull_paint.vox.txt（船殼換色，overwrite）、
#   verify_deco.json、sheet04_deco_v1.png
#   用法：python -I -X utf8 draft_deco.py [--probe=emblem_x=3]（紋章挪幾格，只印換色清單差幾格；⛔ 不寫檔）
#   出處：做法照蠍子號 claude-galiot-01m/design/draft_deco.py（船殼換色只動最外一層、兩舷鏡過去；裝飾子作品；篷做外部模型 deco=1）。
#   · 長喙（plan.beak）：下緣的 knee、上緣與中間兩條 rail、4 根立柱、尖端金飾；3 格寬、從艏柱外緣起（跟船殼不重疊）；不是撞角（Ship_Steps §2）。
#   · 船尾平台（plan.stern_platform）：照底面線往後上斜的板（0.3 m）、兩舷與後端的欄杆（欄杆柱每 2 格一根＋頂欄）；寬 4.4 m（船尾視圖 D）；
#     船尾在那裡只有 0.4–1 m 寬 ⇒ 每舷 2 根斜撐從船殼後段的舷側撐到平台底。
#   · 篷架（plan.stern_platform.awning_spar）：外部模型 deco=1；兩舷各一根桁＋3 對立柱＋橫桿，立柱腳踩在船殼／平台上。
#   · 窗玻璃：每個方窗洞裡、船殼兩格牆的裡面那一層，1 格厚、色 155（Ship_Materials「窗的玻璃」）；每扇要 6 連通。
#   · 船名：利劍 al-Sayf ⇒ 兩舷後段、兩條 wale 之間畫黑底金色的彎刀（跟著舷弧走）；只換色、不加格。
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
from draft_lines import main_rail, palette_rgb

sys.stdout.reconfigure(encoding='utf-8')
V = HL.V
PLAN = HL.load_plan(HERE)
L = HL.Lines(PLAN)
K, XAP, YC = L.K, L.XAP, L.YC
SX, SY, SZ = PLAN['space']['hull']
AX, AY, AZ = PLAN['space']['assembly']
D = PLAN['deco']
cx = lambda Xp: XAP + Xp * K * 10
cz = lambda Zp: Zp * K * 10


def load(path):
    a = np.loadtxt(path, delimiter=',', comments='#', dtype=int, ndmin=2)
    return {tuple(r[:3]): int(r[3]) for r in a}


def interp(pts, x):
    return float(np.interp(x, [p[0] for p in pts], [p[1] for p in pts]))


def beak(occ):
    """長喙：沿上下輪廓的 rail ＋ 立柱 ＋ 尖端金飾；只放在沒有船殼的格。"""
    b = V(PLAN['beak'])
    up = [(cx(X), cz(Z)) for X, Z in b['upper']]
    lo = [(cx(X), cz(Z)) for X, Z in b['lower']]
    xt = cx(b['tip_X_plate'])
    C = {k: V(v) for k, v in D['beak_colors'].items()}
    hw = D['beak_half']
    cells = {}
    def put(x, z, c, half=hw):
        for y in range(YC - half, YC + half + 1):
            if (x, y, z) not in occ:
                cells[(x, y, z)] = c
    x0 = int(np.floor(min(up[0][0], lo[0][0])))
    for x in range(x0, int(np.floor(xt)) + 1):
        xc = x + 0.5
        if xc >= lo[0][0]:
            zl = interp(lo, xc)
            for z in range(int(np.floor(zl)), int(np.floor(zl)) + D['knee_h']):
                put(x, z, C['rail'])
        if xc >= up[0][0]:
            zu = interp(up, xc)
            for z in range(int(np.floor(zu)) - D['rail_h'] + 1, int(np.floor(zu)) + 1):
                put(x, z, C['rail'])
            if xc >= lo[0][0]:
                zm = (zu + interp(lo, xc)) / 2
                if zu - interp(lo, xc) > 2 * D['rail_h'] + 2:
                    for z in range(int(np.floor(zm)), int(np.floor(zm)) + D['rail_h']):
                        put(x, z, C['rail'])
    for Xs in V(D['beak_posts_X']):
        x = int(np.floor(cx(Xs)))
        zl, zu = interp(lo, x + 0.5), interp(up, x + 0.5)
        for z in range(int(np.floor(zl)), int(np.floor(zu)) + 1):
            put(x, z, C['post'])
    # 尖端金飾：最後 tip_len 格換成金色、高 ±1
    for x in range(int(np.floor(xt)) - D['tip_len'] + 1, int(np.floor(xt)) + 1):
        zu = interp(up, x + 0.5)
        for z in range(int(np.floor(zu)) - 2, int(np.floor(zu)) + 2):
            put(x, z, C['tip'])
    return cells


def platform(occ, hull):
    sp = V(PLAN['stern_platform'])
    C = {k: V(v) for k, v in D['platform_colors'].items()}
    hw = D['platform_half']
    under = [(cx(X), cz(Z)) for X, Z in sp['underside']]
    rail = [(cx(X), cz(Z)) for X, Z in sp['rail_top']]
    xa = int(np.floor(cx(sp['rail_top'][0][0])))       # 後端
    xb = XAP                                           # 前端 ＝ AP（船尾）
    cells = {}
    def put(x, y, z, c):
        if (x, y, z) not in occ:
            cells[(x, y, z)] = c
    top = {}
    for x in range(xa, xb + 1):
        zu = interp(under, x + 0.5)
        z0 = int(np.floor(zu))
        for z in range(z0, z0 + D['platform_thick']):
            for y in range(YC - hw, YC + hw + 1):
                put(x, y, z, C['floor'])
        top[x] = z0 + D['platform_thick']                # 第一層空氣
    # 欄杆：兩舷 dy ±hw、後端 x xa；柱每 2 格一根、頂欄 2 格高（頂 ＝ rail_top）
    for x in range(xa, xb + 1):
        zr = int(np.floor(interp(rail, x + 0.5)))
        for y in (YC - hw, YC + hw):
            for z in range(top[x], zr + 1):
                if z >= zr - 1 or (x - xa) % 2 == 0:
                    put(x, y, z, C['rail'] if z >= zr - 1 else C['baluster'])
    zr = int(np.floor(interp(rail, xa + 0.5)))
    for y in range(YC - hw, YC + hw + 1):
        for z in range(top[xa], zr + 1):
            if z >= zr - 1 or (y - YC) % 2 == 0:
                put(xa, y, z, C['rail'] if z >= zr - 1 else C['baluster'])
    # 斜撐：從船殼舷側（x_from，那一格最外面的船殼往外 1 格）斜到平台底 (x_to, dy ±hw-2)
    for br in V(D['brackets']):
        xf, zf, xt_, dyt = br['x_from'], br['z_from'], br['x_to'], br['dy_to']
        zt = int(np.floor(interp(under, xt_ + 0.5))) - 1
        for sg in (1, -1):
            ys = [y for (x, y, z) in hull if x == xf and z == zf and (y - YC) * sg > 0]
            yf = (max(ys) + 1) if sg > 0 else (min(ys) - 1)
            # 6 連通的折線：每一步只動一軸（剩下比例最大的那一軸）⇒ 一路面貼面接到平台底（v1 用四捨五入的直線，起頭那幾格斷開）
            p = [xf, yf, zf]
            tgt = [xt_, YC + sg * dyt, zt]
            span = [max(1, abs(tgt[i] - p[i])) for i in range(3)]
            while True:
                for dz in (0, 1):
                    put(p[0], p[1], p[2] + dz, C['bracket'])
                if p == tgt:
                    break
                i = max(range(3), key=lambda k: abs(tgt[k] - p[k]) / span[k])
                p[i] += 1 if tgt[i] > p[i] else -1
    return cells, top


def awning(base):
    sp = V(PLAN['stern_platform'])
    C = V(D['awning_color'])
    hw = D['platform_half']
    spar = [(cx(X), cz(Z)) for X, Z in sp['awning_spar']]
    spar.sort()
    cells = {}
    zprev = None
    for x in range(int(np.floor(spar[0][0])), int(np.floor(spar[-1][0])) + 1):
        z = int(np.floor(interp(spar, x + 0.5)))
        for y in (YC - hw, YC + hw):
            cells[(x, y, z)] = C
            if zprev is not None and zprev != z:       # 換高度的地方補一格，桁才面貼面連著（v1 35 塊）
                for zz in range(min(z, zprev), max(z, zprev) + 1):
                    cells[(x, y, zz)] = C
        zprev = z
    for Xs in V(D['awning_posts_X']):
        x = int(np.floor(cx(Xs)))
        z = int(np.floor(interp(spar, x + 0.5)))
        for y in range(YC - hw, YC + hw + 1):
            cells[(x, y, z)] = C                        # 橫桿
        for y in (YC - hw, YC + hw):
            zz = z - 1
            while zz >= 0 and (x, y, zz) not in base:   # 立柱往下到踩到東西
                cells[(x, y, zz)] = C
                zz -= 1
    return cells


def glass(hullset):
    """每個方窗洞：照 draft_decks 的外形（lines.solid）找兩格牆的裡面那一層。"""
    S = L.solid(0, SX - 1, SZ - 1, 0.0)
    Sx = np.pad(L.solid(0, SX - 1, SZ - 1, 3.0), 1)
    dist = ndimage.distance_transform_edt(Sx)[1:-1, 1:-1, 1:-1]
    wl = V(PLAN['hull_build']['wall'])
    lv = json.load(open(os.path.join(HERE, 'verify_lines.json'), encoding='utf-8'))
    cells, per = {}, []
    for p in lv['ports']:
        if p['kind'] != 'window':
            continue
        # v2（verifier6：v1 的 236 格補到牆裡面的艙裡、2–3 格厚）：只用窗洞裡的格（外形實心、在牆那兩格裡、作品上被刻掉）；
        #   每柱 (x, z) 取最裡面那一格（後面就是艙裡的空氣）；相鄰兩柱 y 差 1 的地方，在窗洞裡補一格接起來（Ship_Materials：要 6 連通）
        holes = set()
        for x in range(p['x'][0], p['x'][1] + 1):
            for z in range(p['z'][0], p['z'][1] + 1):
                for y in range(SY):
                    if S[x, y, z] and dist[x, y, z] <= wl and (x, y, z) not in hullset:
                        holes.add((x, y, z))
        win = {}
        pick = {}
        for (x, y, z) in holes:
            sg = 1 if y > YC else -1
            k = (x, z, sg)
            if k not in pick or abs(y - YC) < abs(pick[k] - YC):
                pick[k] = y
        for (x, z, sg), y in pick.items():
            win[(x, y, z)] = V(D['glass_color'])
        for (x, z, sg), y in pick.items():
            for dx, dz in ((1, 0), (0, 1)):
                y2 = pick.get((x + dx, z + dz, sg))
                if y2 is None or y2 == y:
                    continue
                for c in ((x + dx, y, z + dz), (x, y2, z)):
                    if c in holes:
                        win[c] = V(D['glass_color'])
                        break
        # 6 連通：兩舷各一片
        for sg in (1, -1):
            part = {k: v for k, v in win.items() if (k[1] - YC) * sg > 0}
            A = np.zeros((SX, SY, SZ), bool)
            for k in part:
                A[k] = True
            lab, n = ndimage.label(A)
            cols = {}
            for (x, y, z) in part:
                cols[(x, z)] = cols.get((x, z), 0) + 1
            per.append({'X_m': p['X_m'], 'side': 'S' if sg > 0 else 'P', 'cells': len(part), 'components': int(n), 'in_hole': sum(1 for k in part if k in holes),
                        'columns': len(cols), 'thick_hist': {str(t): sum(1 for v in cols.values() if v == t) for t in sorted(set(cols.values()))}})
        cells.update(win)
    return cells, per


def name_paint(hull, shift=0):
    """黑底金彎刀：兩舷後段，上 wale 往下 2 格起往下排；圖案的 x 往船頭、z 往上。"""
    em = D['emblem']
    pat = em['pattern']                                   # 由上往下的字串列，'#' 金、'r' 紅、'.' 黑底
    rows = len(pat)
    x0 = em['x0'] + shift
    xs = np.arange(SX) + 0.5
    mr = main_rail(L, L.x_m(xs))
    off = V(PLAN['hull_build']['wales'])[1]               # 上面那條 wale（主舷牆頂往下 1.09 m）
    out, skipped = {}, []
    outer = {}
    for (x, y, z), c in hull.items():
        if y > YC:
            k = (x, z)
            if y > outer.get(k, -1):
                outer[k] = y
    for i, row in enumerate(pat):
        for j, ch in enumerate(row):
            x = x0 + j
            zw = int(np.floor((mr[x] - off) * 10)) - 1      # 上 wale 的下緣
            z = zw - em['gap'] - i
            col = {'#': 244, 'r': 196, '.': 36}[ch]
            if (x, z) not in outer:
                skipped.append([x, z])
                continue
            y = outer[(x, z)]
            out[(x, y, z)] = col
            out[(x, 2 * YC - y, z)] = col
    return out, skipped


def main():
    probe = dict(a[len('--probe='):].split('=') for a in sys.argv[1:] if a.startswith('--probe='))
    hull = load(os.path.join(HERE, 'masks', 'hull', 'hull_01.vox.txt'))
    occ = dict(hull)
    for f in ('decks/hold', 'decks/main', 'decks/quarter', 'ladders/main', 'ladders/quarter'):
        occ.update(load(os.path.join(HERE, 'masks', f + '.vox.txt')))
    paint, skipped = name_paint(hull, int(probe.get('emblem_x', 0)))
    if probe:
        base, _ = name_paint(hull, 0)
        print(json.dumps({'probe': probe, 'paint_cells': len(paint), 'diff_vs_base': len(set(paint.items()) ^ set(base.items()))}))
        return
    bk = beak(occ)
    occ2 = dict(occ); occ2.update(bk)
    pf, ptop = platform(occ2, hull)
    occ3 = dict(occ2); occ3.update(pf)
    aw = awning(occ3)
    gl, glass_per = glass(set(hull))
    R = {'parts': {}}
    parts = {'beak': bk, 'platform': pf, 'awning': aw, 'glass': gl}
    for k, c in parts.items():
        ks = set(c)
        R['parts'][k] = {'cells': len(c), 'overlap_ship': len(ks & set(occ)), 'mirror_diff': len(ks ^ {(x, 2 * YC - y, z) for x, y, z in ks}),
                         'x': [min(p[0] for p in ks), max(p[0] for p in ks)] if ks else None, 'z': [min(p[2] for p in ks), max(p[2] for p in ks)] if ks else None,
                         'colors': {str(a): int(b) for a, b in zip(*np.unique(list(c.values()), return_counts=True))}}
    R['overlap_between'] = {a + '/' + b: len(set(parts[a]) & set(parts[b])) for i, a in enumerate(parts) for b in list(parts)[i + 1:]}
    # 結構：船殼＋甲板＋梯子＋長喙＋平台＋玻璃（連結的件）；篷是模型 ⇒ 另外量它的腳
    allc = set(occ) | set(bk) | set(pf) | set(gl)
    A = np.array(sorted(allc)); lo = A.min(axis=0)
    G = np.zeros(tuple(A.max(axis=0) - lo + 1), bool); G[tuple((A - lo).T)] = True
    R['structure_linked'] = {'cells': len(allc), 'components_6': int(ndimage.label(G)[1]), 'cavities': int((ndimage.binary_fill_holes(G) & ~G).sum()),
                             'mirror_diff': len(allc ^ {(x, 2 * YC - y, z) for x, y, z in allc})}
    awk = set(aw)
    R['awning_feet_touching'] = int(sum(1 for (x, y, z) in awk if (x, y, z - 1) in allc))
    Aw = np.zeros((AX, AY, AZ), bool)
    for k in awk:
        Aw[k] = True
    R['awning_components'] = int(ndimage.label(Aw)[1])
    R['glass_windows'] = glass_per
    R['paint'] = {'cells': len(paint), 'skipped': skipped, 'was_color': {str(a): int(b) for a, b in zip(*np.unique([hull[k] for k in paint], return_counts=True))},
                  'new_color': {str(a): int(b) for a, b in zip(*np.unique(list(paint.values()), return_counts=True))}}
    newhull = dict(hull); newhull.update(paint)
    R['paint']['hull_mirror_diff_after'] = sum(1 for (x, y, z), c in newhull.items() if newhull.get((x, 2 * YC - y, z)) != c)
    R['platform_top_first_air'] = {str(x): z for x, z in list(ptop.items())[::10]}
    R['beak_tip_x'] = int(max(p[0] for p in bk))
    out = os.path.join(HERE, 'masks', 'deco'); os.makedirs(out, exist_ok=True)
    R['lists'] = {}
    for k, c in parts.items():
        fn = os.path.join(out, k + '.vox.txt')
        with open(fn, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 利劍號 %s（draft_deco.py；世界座標，at 0,0,0）\n' % k)
            for (x, y, z) in sorted(c):
                f.write('%d,%d,%d,%d\n' % (x, y, z, c[(x, y, z)]))
        R['lists'][k] = [len(c), hashlib.sha256(open(fn, 'rb').read()).hexdigest()]
    os.makedirs(os.path.join(HERE, 'masks', 'step6'), exist_ok=True)
    fn = os.path.join(HERE, 'masks', 'step6', 'hull_paint.vox.txt')
    with open(fn, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 利劍號 船殼換色：船名彎刀（draft_deco.py；stampvox overwrite=1）\n')
        for (x, y, z) in sorted(paint):
            f.write('%d,%d,%d,%d\n' % (x, y, z, paint[(x, y, z)]))
    R['lists']['hull_paint'] = [len(paint), hashlib.sha256(open(fn, 'rb').read()).hexdigest()]
    # 圖：右舷外側看（x 右、z 上），只畫最外一層
    s = 2
    im = Image.new('RGB', (AX * s + 40, 140 * s + 60), (246, 242, 230))
    d = ImageDraw.Draw(im)
    d.text((10, 8), 'al-Sayf sheet 04: beak, stern platform, awning (deco model), window glass, name (sword) v1 - starboard outside', fill=(0, 0, 0), font=ImageFont.load_default())
    show = dict(newhull); show.update(bk); show.update(pf); show.update(aw); show.update(gl)
    best = {}
    for (x, y, z), c in show.items():
        if z < 140 and y >= YC and y > best.get((x, z), (-1, 0))[0]:
            best[(x, z)] = (y, c)
    for (x, z), (y, c) in best.items():
        d.rectangle([20 + x * s, 40 + (139 - z) * s, 20 + x * s + s - 1, 40 + (139 - z) * s + s - 1], fill=palette_rgb(int(c)))
    im.save(os.path.join(HERE, 'sheet04_deco_v1.png'))
    with open(os.path.join(HERE, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('platform_top_first_air',)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
