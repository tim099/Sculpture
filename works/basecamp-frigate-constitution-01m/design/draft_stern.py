# 新圖紙 12（船尾窗＋船尾裝飾子作品）：plan.json 的 stern 段 ＋ 組裝件的現況（開窗之前）
#   ⇒ masks/stern/deco.vox.txt（子作品，at=0,0,0）、masks/stern/hull_windows_carve.vox.txt（船殼要刻的，帶顏色當守衛）、
#      verify_stern.json、sheet12_stern_v1.png
# 用法：python -I draft_stern.py <design 資料夾>
#   · 船尾面 xf(y,z) ＝ 那一欄最後面（x 最小）的實心格；裝飾貼在它外面 p 格（x ＝ xf − p），窗格縮進 1 格（x ＝ xf ＋ 1）
#   · 橫的白線用每一層 z 的外殼（那一層跟船外空氣相通、離實心 ≤ p 格的空格），所以會繞過船尾角
#   · 窗：每一欄從 xf 往裡刻到第一格空氣（只刻船殼的格）
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP        # noqa: E402
import draft_decks as DD           # noqa: E402
from draft_masts import export_list, ASSEMBLY, HULL   # noqa: E402

YC = 160
XB, ZB = 200, 160                  # 只看船尾這一塊（x < 200、z < 160）


def has_mark(work, name):
    import subprocess
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=marks', '--arg', 'work=' + work],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    base = name.split(':')[0]
    return r.returncode == 0 and base in r.stdout


class Stern:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['stern']
        B = s.P['base']
        oth = export_list(ASSEMBLY, draft=False, hide_links=','.join(B['hide_links']))
        mark = B['hull_mark'] if has_mark(HULL, B['hull_mark']) else None
        hull = export_list(HULL, draft=False, links='none', mark=mark)
        s.hull_read = {'mark': mark, 'voxels': int(len(hull)), 'others': int(len(oth))}
        assert len(hull) + len(oth) == B['assembly_voxels'], ('讀到的現況格數對不上', len(hull), len(oth), B['assembly_voxels'])
        s.H = np.zeros((XB, 320, ZB), np.uint8)
        s.O = np.zeros((XB, 320, ZB), np.uint8)
        for a, G in ((hull, s.H), (oth, s.O)):
            m = a[(a[:, 0] < XB) & (a[:, 2] < ZB)]
            G[m[:, 0], m[:, 1], m[:, 2]] = m[:, 3]
        assert not ((s.H > 0) & (s.O > 0)).any()
        s.S = (s.H > 0) | (s.O > 0)
        s.C = s.H.copy()
        s.C[s.O > 0] = s.O[s.O > 0]
        # 船尾面：每一欄 (y,z) 最小的實心 x
        has = s.S.any(0)
        s.xf = np.where(has, np.argmax(s.S, axis=0), -1)
        s.col = s.P['colors']
        s.deco = {}            # (x,y,z) → color
        s.kind = {}            # (x,y,z) → 哪一個元件
        s.carve = {}           # (x,y,z) → color（刻之前的顏色）
        s.skipped = []

    # ── 放格 ──
    def put(s, x, y, z, c, kind):
        k = (int(x), int(y), int(z))
        if k in s.deco:
            return
        if s.S[k] and k not in s.carve:
            s.skipped.append((kind,) + k)
            return
        s.deco[k] = int(c)
        s.kind[k] = kind

    def on_face(s, dy, z, p, c, kind):
        """貼在船尾面外 p 格（p ≥ 1），或縮進 −p 格（p < 0 ⇒ 窗格）。"""
        y = YC + dy
        xf = s.xf[y, z]
        if xf < 0:
            s.skipped.append((kind, None, y, z))
            return
        if p >= 1:
            for q in range(1, p + 1):
                s.put(xf - q, y, z, c, kind)
        else:
            s.put(xf - p, y, z, c, kind)

    # ── 窗 ──
    def windows(s):
        W = s.P['windows']
        z0, z1 = W['z']
        s.win_cols = []
        for a, b in W['dy']:
            spans = [(a, b)] if a < 0 else [(a, b), (-b, -a)]
            for lo, hi in spans:
                for dy in range(lo, hi + 1):
                    for z in range(z0, z1 + 1):
                        y = YC + dy
                        x = int(s.xf[y, z])
                        n = 0
                        while s.S[x, y, z]:
                            assert s.H[x, y, z] > 0, ('窗裡碰到別的部件', x, y, z)
                            s.carve[(x, y, z)] = int(s.H[x, y, z])
                            x += 1
                            n += 1
                        s.win_cols.append((dy, z, int(s.xf[y, z]), n))
        sh = W['sash']
        bars = set()
        for a, b in W['dy']:
            spans = [(a, b)] if a < 0 else [(a, b), (-b, -a)]
            for lo, hi in spans:
                for dy in range(lo, hi + 1):
                    for z in range(z0, z1 + 1):
                        if z in sh['z'] or abs(dy) in sh['dy']:
                            bars.add((dy, z))
        for dy, z in sorted(bars):
            s.on_face(dy, z, -sh['setback'], s.col['sash'], 'sash')
            # 船尾面是斜的：直的窗格上下兩排 x 差 1 ⇒ 只有邊碰邊（第一版 16 格浮空）。往下一排的位置補 1 格接成面相連
            if abs(dy) in sh['dy'] and z > z0:
                y = YC + dy
                for x in range(int(s.xf[y, z]) + sh['setback'] + 1, int(s.xf[y, z - 1]) + sh['setback'] + 1):
                    s.put(x, y, z, s.col['sash'], 'sash')

    # ── pilasters ──
    def pilasters(s):
        P = s.P['pilasters']
        pr = P['proud']
        for a, b in P['dy']:
            for sg in (1, -1):
                ds = [sg * d for d in range(a, b + 1)]
                for dy in ds:
                    s.on_face(dy, P['base_z'], pr['base'], s.col['trim'], 'pilaster')
                    for z in range(P['shaft_z'][0], P['shaft_z'][1] + 1):
                        s.on_face(dy, z, pr['shaft'], s.col['trim'], 'pilaster')
                w = P['cap_widen']
                for d in range(a - w, b + w + 1):
                    for z in range(P['cap_z'][0], P['cap_z'][1] + 1):
                        s.on_face(sg * d, z, pr['cap'], s.col['trim'], 'pilaster')

    # ── 橫的白線（每一層的外殼，繞過船尾角）──
    def rails(s):
        st = ndimage.generate_binary_structure(2, 1)
        s.rail_wrap = {}
        for name, R in s.P['rails'].items():
            for z, p in zip(range(R['z'][0], R['z'][1] + 1), R['proud']):
                sol = s.S[:, :, z]
                # 船外 ＝ 從船尾（x 0）與兩舷（y 0／319）連得到的空氣；只在 x ≤ x_end ＋ 3 這一段裡判斷 ——
                # 整層的話，船艙經過側面砲門也通到船外（第一版就是這樣讓白線跑進船艙）
                cut = R['x_end'] + 3
                lab, n = ndimage.label(~sol[:cut], structure=st)
                seeds = set(np.unique(np.concatenate([lab[0], lab[:, 0], lab[:, -1]]))) - {0}
                ext = np.zeros(sol.shape, bool)
                ext[:cut] = np.isin(lab, list(seeds))
                d1 = ndimage.binary_dilation(sol, st) & ext
                shell = d1
                if p >= 2:
                    shell = ndimage.binary_dilation(sol, st, iterations=p) & ext
                xs = np.arange(XB)[:, None]
                shell &= (xs <= R['x_end'])
                cells = np.argwhere(shell)
                # 外殼只能在船尾面外面（那一欄的實心在它後面）—— 跑進船艙的話這裡會叫
                inside = [(int(x), int(y)) for x, y in cells if 0 <= s.xf[y, z] < x]
                assert not inside, ('白線跑進船艙', name, z, inside[:5])
                for x, y in cells:
                    s.put(x, y, z, s.col['trim'], 'rail-' + name)
                s.rail_wrap[name + '@' + str(z)] = {'cells': int(len(cells)), 'x_max': int(cells[:, 0].max()), 'dy_max': int(np.abs(cells[:, 1] - YC).max())}

    # ── 拱線（兩道圓角矩形的上半）──
    def arch(s):
        A = s.P['arch']
        for L in A['lines']:
            hw, top, r = L['half_width'], L['top'], L['radius']
            pts = []
            # 只算 dy > 0 那半邊（直線往上 → 圓角 → 頂到中線），細化之後再鏡射 —— 整條一起細化的話，
            # 拿掉哪個 L 角跟路徑方向有關，左右會差 12 格
            for z in np.arange(A['bottom'], top - r, 0.05):
                pts.append((hw, z))
            for t in np.arange(0, math.pi / 2, 0.005):
                pts.append((hw - r + r * math.cos(t), top - r + r * math.sin(t)))
            for d in np.arange(hw - r, -0.01, -0.05):
                pts.append((d, top))
            # 像素畫的細線（8 連通）：每一格都貼著船尾面、不靠彼此相連。密取樣四捨五入出來的是 4 連通的階梯，
            # 45° 那段每一步 2 格厚、內外兩道又只隔 1 格 ⇒ 圓角糊成一團（第一次落草稿）⇒ 拿掉階梯的 L 角
            cells = []
            for d, z in pts:
                c = (int(round(d)), int(round(z)))
                if not cells or cells[-1] != c:
                    cells.append(c)
            thin = [cells[0]]
            for i in range(1, len(cells) - 1):
                p, n = thin[-1], cells[i + 1]
                if abs(p[0] - n[0]) == 1 and abs(p[1] - n[1]) == 1:
                    continue
                thin.append(cells[i])
            thin.append(cells[-1])
            for dy, z in dict.fromkeys(thin + [(-d, z) for d, z in thin]):
                s.on_face(dy, z, A['proud'], s.col['trim'], 'arch')

    # ── 星 ──
    def stars(s):
        S = s.P['stars']
        g = S['glyph']
        h, w = len(g), len(g[0])
        for d0, z0 in S['at']:
            for sg in (1, -1):
                for i, row in enumerate(g):
                    for j, ch in enumerate(row):
                        if ch != '.':
                            s.on_face(sg * d0 + (w // 2 - j), z0 + (h // 2 - i), S['proud'], s.col['trim'], 'star')

    # ── 鷹（從船尾看，觀者的左手邊 ＝ −y：引擎的視圖量到的；第一版照右手系放成 +y，船名在引擎裡是反的）──
    def eagle(s):
        E = s.P['eagle']
        for i, row in enumerate(E['rows']):
            z = E['top_z'] - i
            for j, ch in enumerate(row):
                if ch == '.':
                    continue
                cname, p = E['legend'][ch]
                s.on_face(j - E['center_col'], z, p, s.col[cname], 'eagle')

    # ── 船名與名牌 ──
    def name(s):
        N = s.P['name']
        F = N['font']
        glyphs = [F[ch] for ch in N['text']]
        width = sum(len(g[0]) for g in glyphs) + N['gap'] * (len(glyphs) - 1)
        assert width % 2 == 1, ('字寬要奇數才置中', width)
        col = 0
        left = width // 2               # 第一個字的最左一欄在 dy −left（觀者的左手邊 ＝ −y）
        for g in glyphs:
            for i, row in enumerate(g):
                for j, ch in enumerate(row):
                    if ch == '#':
                        s.on_face((col + j) - left, N['z_top'] - i, N['proud'], s.col['trim'], 'name')
            col += len(g[0]) + N['gap']
        s.name_width = width
        Fr = N['frame']
        za, zb = Fr['z']
        zm = (za + zb) // 2
        for d in range(-Fr['half'], Fr['half'] + 1):
            s.on_face(d, za, N['proud'], s.col['trim'], 'name-frame')
            s.on_face(d, zb, N['proud'], s.col['trim'], 'name-frame')
        for sg in (1, -1):
            for k in range(1, Fr['point'] + 1):
                for z in (za + k, zb - k):
                    if za < z < zb:
                        s.on_face(sg * (Fr['half'] + k), z, N['proud'], s.col['trim'], 'name-frame')
            s.on_face(sg * (Fr['half'] + Fr['point']), zm, N['proud'], s.col['trim'], 'name-frame')

    def build(s):
        s.windows()
        s.rails()
        s.pilasters()
        s.arch()
        s.stars()
        s.eagle()
        s.name()

    def verify(s):
        v = {'read': s.hull_read}
        v['carve'] = {'cells': len(s.carve), 'colors': {str(c): sum(1 for q in s.carve.values() if q == c) for c in sorted(set(s.carve.values()))}}
        cols = [n for (_, _, _, n) in s.win_cols]
        v['window_wall_depth'] = {'min': int(min(cols)), 'max': int(max(cols)), 'columns': len(cols)}
        v['deco'] = {'cells': len(s.deco),
                     'by_kind': {k: sum(1 for q in s.kind.values() if q == k) for k in sorted(set(s.kind.values()))},
                     'colors': {str(c): sum(1 for q in s.deco.values() if q == c) for c in sorted(set(s.deco.values()))}}
        v['skipped'] = {'n': len(s.skipped), 'first': [list(map(lambda t: t if isinstance(t, str) else (None if t is None else int(t)), q)) for q in s.skipped[:10]]}
        v['rail_wrap'] = s.rail_wrap
        # 開窗之後的現況 ＋ 裝飾
        A = s.S.copy()
        for k in s.carve:
            A[k] = False
        D = np.zeros_like(A)
        for k in s.deco:
            D[k] = True
        v['overlap_after_carve'] = int((A & D).sum())
        # 每一格裝飾都接得到（6 連通）現況的實心格
        lab, n = ndimage.label(A | D)
        ok = set(np.unique(lab[A])) - {0}
        v['deco_floating'] = int(sum(1 for k in s.deco if lab[k] not in ok))
        # 鏡像差（y ↔ 320 − y；鷹頭與船名本來就不對稱）
        mm = {}
        for k, c in s.deco.items():
            m = (k[0], 2 * YC - k[1], k[2])
            if s.deco.get(m) != c:
                mm[s.kind[k]] = mm.get(s.kind[k], 0) + 1
        v['mirror_mismatch_by_kind'] = mm
        cm = sum(1 for k, c in s.carve.items() if (k[0], 2 * YC - k[1], k[2]) not in s.carve)
        v['carve_mirror_mismatch'] = cm
        # 透光：每一欄窗（非窗格的那幾欄）從船外往 +x 走，會走到船艙裡的空氣
        thr = 0
        for dy, z, xf, nrun in s.win_cols:
            y = YC + dy
            if (xf + 1, y, z) in s.deco:
                continue
            x = xf - 3
            while x < XB and not (A[x, y, z] or D[x, y, z]):
                x += 1
            if x > xf + nrun:
                thr += 1
        v['window_see_through_columns'] = thr
        # 封閉空腔（只看這一塊；碰到盒子邊的不算）
        def cavities(sol):
            lab, n = ndimage.label(~sol)
            edge = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()]))) - {0}
            return int(n - len(edge))
        v['cavities_box'] = {'before': cavities(s.S), 'after': cavities(A | D)}
        xs = [k[0] for k in s.deco]
        zs = [k[2] for k in s.deco]
        v['deco_bbox'] = {'x': [min(xs), max(xs)], 'y': [min(k[1] for k in s.deco), max(k[1] for k in s.deco)], 'z': [min(zs), max(zs)]}
        v['expect_assembly_after'] = s.P['base']['assembly_voxels'] - len(s.carve) + len(s.deco)
        v['name_width'] = s.name_width
        s.v = v
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'stern')
        os.makedirs(out, exist_ok=True)
        s.files = {}
        for fname, rows, note in (('deco', sorted((k[0], k[1], k[2], c) for k, c in s.deco.items()), '船尾裝飾子作品（窗格、pilasters、白線、拱線、星、鷹、船名）'),
                                  ('hull_windows_carve', sorted((k[0], k[1], k[2], c) for k, c in s.carve.items()), '船殼開船尾窗要刻的格（帶顏色 ＝ 那一格現在要是這個顏色才刻）')):
            p = os.path.join(out, fname + '.vox.txt')
            body = '\n'.join('%d,%d,%d,%d' % r for r in rows)
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— %s（%d 格，at=0,0,0）\n' % (fname, note, len(rows)) + body + '\n')
            s.files[fname] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}


# ── 圖紙 ──
def astern_view(S, C, deco, carve, xf, ya, yb, za, zb):
    """從船尾正後方看（往 +x）：每個 (y,z) 第一格的顏色；透過窗看到的（比船尾面深 4 格以上）調暗。觀者左手邊 ＝ −y（跟引擎的視圖一致）。"""
    img = np.zeros((zb - za, yb - ya, 3), np.uint8)
    img[:] = DD.PAPER
    for iy, y in enumerate(range(ya, yb)):
        for iz, z in enumerate(range(zb - 1, za - 1, -1)):
            best = None
            for x in range(0, XB):
                k = (x, y, z)
                if k in deco:
                    best = (x, deco[k])
                    break
                if S[x, y, z] and k not in carve:
                    best = (x, int(C[x, y, z]))
                    break
            if best is None:
                if xf[y, z] >= 0:
                    img[iz, iy] = (34, 30, 26)        # 視線穿過窗、走出這一塊 ⇒ 船艙裡的暗處
                continue
            rgb = np.array(DP.rgb332(best[1]), float)
            if xf[y, z] >= 0 and best[0] > xf[y, z] + 3:
                rgb *= 0.45
            img[iz, iy] = rgb.astype(np.uint8)
    return img


def side_view(S, C, deco, carve, xa, xb, za, zb):
    """從 y > 160 那一舷看：每個 (x,z) 最外面（y 最大）那一格。"""
    img = np.zeros((zb - za, xb - xa, 3), np.uint8)
    img[:] = DD.PAPER
    for ix, x in enumerate(range(xa, xb)):
        for iz, z in enumerate(range(zb - 1, za - 1, -1)):
            for y in range(319, YC - 1, -1):
                k = (x, y, z)
                if k in deco:
                    img[iz, ix] = DP.rgb332(deco[k]); break
                if S[x, y, z] and k not in carve:
                    img[iz, ix] = DP.rgb332(int(C[x, y, z])); break
    return img


def section(S, C, deco, carve, dy, xa, xb, za, zb):
    y = YC + dy
    img = np.zeros((zb - za, xb - xa, 3), np.uint8)
    img[:] = DD.PAPER
    for ix, x in enumerate(range(xa, xb)):
        for iz, z in enumerate(range(zb - 1, za - 1, -1)):
            k = (x, y, z)
            if k in deco:
                img[iz, ix] = DP.rgb332(deco[k])
            elif S[x, y, z] and k not in carve:
                img[iz, ix] = DP.rgb332(int(C[x, y, z]))
            elif k in carve:
                img[iz, ix] = (255, 200, 200)
    return img


def render_sheet(T, path):
    f12, f14, f18 = DD._font(13), DD._font(15), DD._font(20)
    ya, yb, za, zb = YC - 54, YC + 55, 74, 131
    sc = 6
    before = Image.fromarray(astern_view(T.S, T.C, {}, {}, T.xf, ya, yb, za, zb)).resize(((yb - ya) * sc, (zb - za) * sc), Image.NEAREST)
    after = Image.fromarray(astern_view(T.S, T.C, T.deco, T.carve, T.xf, ya, yb, za, zb)).resize(((yb - ya) * sc, (zb - za) * sc), Image.NEAREST)
    xa, xb = 94, 150
    sv = Image.fromarray(side_view(T.S, T.C, T.deco, T.carve, xa, xb, za, zb)).resize(((xb - xa) * sc, (zb - za) * sc), Image.NEAREST)
    sx0, sx1, sz0, sz1 = 98, 128, 80, 112
    secs = [(dy, Image.fromarray(section(T.S, T.C, T.deco, T.carve, dy, sx0, sx1, sz0, sz1)).resize(((sx1 - sx0) * 8, (sz1 - sz0) * 8), Image.NEAREST)) for dy in (2, 6)]
    PADL = 60
    W = PADL + 2 * (yb - ya) * sc + 60 + 40
    H = 2000
    can = Image.new('RGB', (W, H), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), T.P['title'], font=f18, fill=DD.INK)
    dr.text((PADL, 40), '從正後方看（往船頭；觀者左手邊 ＝ y < 160 那一舷，跟引擎的視圖一致）；z %d–%d、|dy| %d 以內；每格 %d px；透過窗看到的船艙調暗' % (za, zb - 1, YC - ya, sc), font=f12, fill=DD.INK)
    y = 66
    for i, (title, im) in enumerate((('現在（全黑的船尾面，窗被外板封著）', before), ('新圖紙 12 v1', after))):
        x0 = PADL + i * ((yb - ya) * sc + 60)
        dr.text((x0, y), title, font=f14, fill=DD.INK)
        can.paste(im, (x0, y + 22))
        # 刻度：z
        for z in range(za, zb, 5):
            yy = y + 22 + (zb - 1 - z) * sc + sc // 2
            dr.line([(x0 - 6, yy), (x0 - 1, yy)], fill=(130, 130, 130))
            if i == 0:
                dr.text((x0 - 34, yy - 7), str(z), font=f12, fill=(130, 130, 130))
        for d in range(-50, 51, 10):
            xx = x0 + ((YC + d) - ya) * sc + sc // 2
            dr.text((xx - 8, y + 22 + (zb - za) * sc + 2), str(d), font=f12, fill=(130, 130, 130))
    y += 22 + (zb - za) * sc + 26
    dr.text((PADL, y), 'quarter（y > 160 那一舷，x %d–%d）' % (xa, xb - 1), font=f14, fill=DD.INK)
    can.paste(sv, (PADL, y + 22))
    x0 = PADL + (xb - xa) * sc + 50
    for dy, im in secs:
        dr.text((x0, y), '剖面 dy %+d（%s）' % (dy, '窗' if dy == 2 else 'pilaster'), font=f14, fill=DD.INK)
        can.paste(im, (x0, y + 22))
        x0 += (sx1 - sx0) * 8 + 40
    y += 22 + max((zb - za) * sc, (sz1 - sz0) * 8) + 24
    v = T.v
    P = T.P
    lines = [
        '窗：z %d–%d，|dy| %s；刻穿外板＋內板 %d 格（牆厚 %d–%d 格）；窗格 1 格、縮進 1 格（橫的 z %s、直的 |dy| %s）；透光 %d 欄' % (
            P['windows']['z'][0], P['windows']['z'][1], '、'.join('%d–%d' % (max(a, 0), b) for a, b in P['windows']['dy']), v['carve']['cells'],
            v['window_wall_depth']['min'], v['window_wall_depth']['max'], P['windows']['sash']['z'], P['windows']['sash']['dy'], v['window_see_through_columns']),
        'pilasters：|dy| %s（站在 counter timbers 前面）；base z %d、shaft %d–%d、cap %d–%d（寬出 %d）' % (
            '、'.join('%d–%d' % tuple(d) for d in P['pilasters']['dy']), P['pilasters']['base_z'], *P['pilasters']['shaft_z'], *P['pilasters']['cap_z'], P['pilasters']['cap_widen']),
        '白線：窗台 z %s（繞過船尾角到 x %d）、counter 下緣 z %s（到 x %d）；拱線兩道 半寬 %s、頂 %s；星 %s；鷹 27×13（頂 z %d）；船名 %s（%d 格寬，z %d–%d）' % (
            P['rails']['sill']['z'], P['rails']['sill']['x_end'], P['rails']['lower']['z'], P['rails']['lower']['x_end'],
            [l['half_width'] for l in P['arch']['lines']], [l['top'] for l in P['arch']['lines']], P['stars']['at'], P['eagle']['top_z'],
            P['name']['text'], v['name_width'], P['name']['z_top'] - 4, P['name']['z_top']),
        '子作品 %d 格（%s）；重疊 %d、浮空 %d；組裝件預期 %d 格' % (
            v['deco']['cells'], '、'.join('%s %d' % kv for kv in v['deco']['by_kind'].items()), v['overlap_after_carve'], v['deco_floating'], v['expect_assembly_after']),
        '下排：quarter 看窗台白線繞過船尾角、接到側面白帶；剖面 x %d–%d、z %d–%d（粉紅 ＝ 船殼刻掉的格）' % (sx0, sx1 - 1, sz0, sz1 - 1),
        '出處：現代照片（Tim 給的兩張）、1927 MIT PLAN VIII 船尾正視；設計決定見 plan.json stern.decisions',
    ]
    for t in lines:
        dr.text((PADL, y), t, font=f12, fill=DD.INK)
        y += 20
    can = can.crop((0, 0, W, y + 20))
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    T = Stern(design)
    T.build()
    v = T.verify()
    T.write()
    v['files'] = T.files
    json.dump(v, open(os.path.join(design, 'verify_stern.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(T, os.path.join(design, 'sheet12_stern_v1.png'))
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
