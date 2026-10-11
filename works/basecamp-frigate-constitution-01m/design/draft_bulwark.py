# 新圖紙 10（船殼）：舷牆與舷弧起翹 —— plan.json 的 bulwark 段 ＋ 作品（bulwark.world_mark）
#   ⇒ masks/bulwark/{rise,cap}.vox.txt（stampvox，at=0,0,0）、verify_bulwark.json、sheet10_bulwark_v1.png
# 用法：python -I draft_bulwark.py <design 資料夾>
#   · 白帶上緣（每個 x 外側 255 最高那一格）三次擬合 ＋ offset ＝ 舷頂目標；只往上補、不切
#   · 補的那幾排照肋骨頂那一列（zt）的組成往上疊（外板 36／肋骨 141／內板 177，y 範圍不變）
#   · cap rail：新頂上面一排，比牆內外各多 1 格
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import draft_planking as DP        # noqa: E402
import draft_decks as DD           # noqa: E402
from replay import replay          # noqa: E402

X0, X1, NZ, YC, Y0, SX, SY = DD.X0, DD.X1, DD.NZ, DD.YC, DD.Y0, DD.SX, DD.SY


class Bulwark:
    def __init__(s, design):
        s.design = design
        s.W = os.path.dirname(os.path.abspath(design))
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['bulwark']
        w = {k: v[0] for k, v in replay(s.W, mark=s.P['world_mark']).items()}
        assert len(w) == s.P['world_voxels'], ('讀到的作品格數對不上 world_voxels', len(w), s.P['world_voxels'])
        G = np.zeros((SX, SY, NZ), np.uint8)
        for (x, y, z), c in w.items():
            G[x - X0, y - Y0, z] = c
        s.G = G
        M = DP.Model(design)
        M.lines()
        s.zt = np.asarray(M.zt)

    def design_rail(s):
        P = s.P
        xs, band = [], []
        c = YC - Y0
        for ix in range(SX):
            x = ix + X0
            if not (P['fit_x'][0] <= x <= P['fit_x'][1]):
                continue
            zz = np.where((s.G[ix, c:, :] == P['band_color']).any(0))[0]
            if len(zz):
                xs.append(x)
                band.append(int(zz.max()))
        s.band_x, s.band_z = np.array(xs), np.array(band)
        s.coef = np.polyfit(s.band_x, s.band_z, P['fit_degree'])
        s.fit_resid = float(np.abs(np.polyval(s.coef, s.band_x) - s.band_z).max())
        s.rail = np.full(SX, np.nan)
        s.new_top = s.zt.copy()
        for ix in range(SX):
            x = ix + X0
            if s.zt[ix] < 0:
                continue
            if P['fit_x'][0] <= x <= P['fit_x'][1]:
                s.rail[ix] = np.polyval(s.coef, x) + P['offset_from_band']
                s.new_top[ix] = max(int(s.zt[ix]), int(round(s.rail[ix])))
        mid = int(np.argmin(np.polyval(s.coef, s.band_x)))
        s.mid = {'x': int(s.band_x[mid]), 'band_fit': round(float(np.polyval(s.coef, s.band_x[mid])), 2), 'zt': int(s.zt[s.band_x[mid] - X0])}

    def build(s):
        RISE = np.zeros(s.G.shape, np.uint8)
        CAP = np.zeros(s.G.shape, bool)
        for ix in range(SX):
            zt = int(s.zt[ix])
            if zt < 0:
                continue
            tmpl = s.G[ix, :, zt].copy()
            if not tmpl.any():
                continue
            # 樣板那一列每一舷的牆（最內到最外那一格之間）中間的空格當成肋骨 141 ⇒ 往上疊的牆是實心的，不會長出空管
            c = YC - Y0
            for half in (slice(c + 1, SY), slice(0, c)):
                seg = tmpl[half]
                nz = np.where(seg > 0)[0]
                if len(nz) >= 2:
                    gap = np.zeros(seg.shape, bool)
                    gap[nz.min():nz.max() + 1] = seg[nz.min():nz.max() + 1] == 0
                    seg[gap] = 141
            nt = int(s.new_top[ix])
            for z in range(zt + 1, nt + 1):
                m = (tmpl > 0) & (s.G[ix, :, z] == 0)
                RISE[ix, m, z] = tmpl[m]
            # cap：新頂上面一排，牆的 y 範圍往內外各多 1 格（overhang）
            row = tmpl > 0
            cap = ndimage.binary_dilation(row, iterations=max(s.P['cap']['overhang_out'], s.P['cap']['overhang_in']))
            z = nt + 1
            if z < NZ:
                CAP[ix, cap & (s.G[ix, :, z] == 0) & (RISE[ix, :, z] == 0), z] = True
        s.RISE, s.CAP = RISE, CAP
        # 還封住的小空腔（肋骨頂那一列本來就空著、被新的格蓋住）⇒ 用鄰近 voxel 顏色補實（Tim：用鄰近 voxel 顏色填滿），算進 rise
        SOL = (s.G > 0) | (RISE > 0) | CAP
        lab, n = ndimage.label(~SOL)
        edge = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])))
        col = s.G.copy()
        col[RISE > 0] = RISE[RISE > 0]
        col[CAP] = s.P['cap']['color']
        s.cavity_filled = 0
        for k in range(1, n + 1):
            if k in edge:
                continue
            idx = np.argwhere(lab == k)
            assert len(idx) <= 16, ('封閉空腔太大', len(idx), idx[0])
            for i, j, z in idx:
                nb = [int(col[i + a, j + b, z + c]) for a, b, c in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
                nb = [v for v in nb if v]
                cnt = {v: nb.count(v) for v in nb}
                best = max(cnt.items(), key=lambda kv: (kv[1], kv[0] == 141))[0] if cnt else 141
                RISE[i, j, z] = best
                col[i, j, z] = best
                s.cavity_filled += 1

    def verify(s):
        v = {}
        v['band_fit'] = {'coef': [float(c) for c in s.coef], 'max_resid': round(s.fit_resid, 2), 'points': len(s.band_x)}
        v['midship'] = s.mid
        v['offset'] = s.P['offset_from_band']
        rise = s.new_top - s.zt
        ok = s.zt >= 0
        v['rise_cells_by_x'] = {str(x): int(rise[x - X0]) for x in range(100, 680, 20) if ok[x - X0]}
        v['rise_max'] = int(rise[ok].max())
        v['rise_from_x'] = int(np.where((rise > 0) & ok)[0].min() + X0) if (rise > 0).any() else None
        v['rail_below_zt_kept'] = int(((np.round(s.rail) < s.zt) & ~np.isnan(s.rail)).sum())
        v['rise_cells'] = int((s.RISE > 0).sum())
        v['cap_cells'] = int(s.CAP.sum())
        v['rise_colors'] = {str(c): int((s.RISE == c).sum()) for c in np.unique(s.RISE[s.RISE > 0])}
        SOL = (s.G > 0) | (s.RISE > 0) | s.CAP
        v['overlap_with_world'] = int(((s.RISE > 0) & (s.G > 0)).sum() + (s.CAP & (s.G > 0)).sum())
        v['mirror_mismatch'] = int((SOL != SOL[:, ::-1, :]).sum())
        v['components_after'] = int(ndimage.label(SOL)[1])
        lab, n = ndimage.label(~SOL)
        edge = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])))
        cav = [k for k in range(1, n + 1) if k not in edge]
        v['cavities_after'] = {'n': len(cav), 'cells': int(sum((lab == k).sum() for k in cav))}
        # 跟甲板、房間的距離：新加的格最低在哪
        zz = np.where((s.RISE > 0).any((0, 1)) | s.CAP.any((0, 1)))[0]
        v['new_cells_z_range'] = [int(zz.min()), int(zz.max())] if len(zz) else None
        v['expect_after'] = int(SOL.sum())
        s.v = v
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'bulwark')
        os.makedirs(out, exist_ok=True)
        s.files = {}
        for name, rows, note in (('rise', [(i, j, k, int(s.RISE[i, j, k])) for i, j, k in np.argwhere(s.RISE > 0)], '舷頂往上補（照肋骨頂那一列的組成）'),
                                 ('cap', [(i, j, k, s.P['cap']['color']) for i, j, k in np.argwhere(s.CAP)], 'cap rail（新頂上面一排，內外各多 1 格）')):
            p = os.path.join(out, name + '.vox.txt')
            body = '\n'.join('%d,%d,%d,%d' % (i + X0, j + Y0, k, c) for i, j, k, c in rows)
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— %s（%d 格，at=0,0,0）\n' % (name, note, len(rows)) + body + '\n')
            s.files[name] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}


def side_view(G, xa, xb, za, zb):
    """從 y > 160 那一舷看過去：每個 (x,z) 最外面那一格的顏色。"""
    c = YC - Y0
    sub = G[xa - X0:xb - X0, c:, za:zb]
    has = sub > 0
    idx = np.where(has.any(1), SY - c - 1 - np.argmax(has[:, ::-1, :], axis=1), -1)
    img = np.zeros((zb - za, xb - xa, 3), np.uint8)
    img[:] = DD.PAPER
    for ix in range(xb - xa):
        for iz in range(zb - za):
            j = idx[ix, iz]
            if j >= 0:
                img[zb - za - 1 - iz, ix] = DP.rgb332(int(sub[ix, j, iz]))
    return img


def render_sheet(B, path):
    f12, f14, f18 = DD._font(13), DD._font(15), DD._font(20)
    xa, xb, za, zb = 95, 680, 60, 140
    sc = 2.5
    after = B.G.copy()
    after[B.RISE > 0] = B.RISE[B.RISE > 0]
    after[B.CAP] = B.P['cap']['color']
    imgs = []
    for title, G in (('現在（階段九做完）', B.G), ('補完之後（新圖紙 10 v1）', after)):
        im = Image.fromarray(side_view(G, xa, xb, za, zb)).resize((int((xb - xa) * sc), int((zb - za) * sc)), Image.NEAREST)
        imgs.append((title, im))
    PADL = 70
    W = int((xb - xa) * sc) + PADL + 40
    H = 80 + 2 * (int((zb - za) * sc) + 50) + 300 + 60
    can = Image.new('RGB', (W, H), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), B.P['title'], font=f18, fill=DD.INK)
    dr.text((PADL, 40), '從 y > 160 那一舷看（z %d–%d）；紅線 ＝ 新舷頂、灰線 ＝ 現在的肋骨頂、白虛線 ＝ 白帶上緣擬合、黃 ＝ 白帶 ＋ %d' % (za, zb, B.P['offset_from_band']), font=f12, fill=DD.INK)
    y = 70

    def P(x, z):
        return (PADL + (x - xa) * sc, y + (zb - z) * sc)
    for title, im in imgs:
        dr.text((PADL, y), title, font=f14, fill=DD.INK)
        y += 22
        can.paste(im, (PADL, y))
        for x in range(xa, xb - 1):
            ix = x - X0
            if B.zt[ix] < 0 or B.zt[ix + 1] < 0:
                continue
            dr.line([P(x, B.zt[ix] + 1), P(x + 1, B.zt[ix] + 1)], fill=(150, 150, 150), width=1)
            dr.line([P(x, B.new_top[ix] + 1), P(x + 1, B.new_top[ix] + 1)], fill=(220, 40, 40), width=2)
            if not np.isnan(B.rail[ix]):
                bf = np.polyval(B.coef, x)
                if x % 4 < 2:
                    dr.line([P(x, bf + 1), P(x + 1, bf + 1)], fill=(255, 255, 255), width=1)
        for x in range(100, xb, 50):
            dr.text((PADL + (x - xa) * sc - 8, y + (zb - za) * sc + 2), str(x), font=f12, fill=(130, 130, 130))
        y += int((zb - za) * sc) + 26
    # 兩個剖面：x=440（船中，不升）、x=640（船頭，升最多附近）
    x0 = PADL
    for xs, cap in ((440, 'x = 440 船中（不升，只加 cap rail）'), (640, 'x = 640 船頭（往上補 %d 格 ＋ cap）' % (B.new_top[640 - X0] - B.zt[640 - X0]))):
        ix = xs - X0
        a = np.zeros((SY, NZ, 3), np.uint8)
        a[:] = DD.PAPER
        for G, dim in ((B.G, False), (after, True)):
            pass
        m0 = B.G[ix] > 0
        for j, k in np.argwhere(after[ix] > 0):
            a[j, k] = DP.rgb332(int(after[ix][j, k]))
        new = (B.RISE[ix] > 0) | B.CAP[ix]
        im = Image.fromarray(np.transpose(a, (1, 0, 2))[::-1][NZ - 140:NZ - 95]).resize((SY * 4, 45 * 4), Image.NEAREST)
        d2 = ImageDraw.Draw(im)
        for j, k in np.argwhere(new):
            if 95 <= k < 140:
                yy = (139 - k) * 4
                d2.rectangle([j * 4, yy, j * 4 + 3, yy + 3], outline=(220, 40, 40))
        dr.text((x0, y), cap + '（紅框 ＝ 新加的格）', font=f14, fill=DD.INK)
        can.paste(im, (x0, y + 22))
        x0 += SY * 4 + 40
    y += 22 + 45 * 4 + 20
    v = B.v
    dr.text((PADL, y), '白帶擬合殘差 ≤ %.2f 格；船中 x %d 白帶 %.1f、肋骨頂 %d ⇒ offset %d；往上補 %d 格（%s）、cap %d 格；最多升 %d 格，從 x %s 開始' % (
        v['band_fit']['max_resid'], v['midship']['x'], v['midship']['band_fit'], v['midship']['zt'], v['offset'], v['rise_cells'],
        '、'.join('%s:%d' % kv for kv in v['rise_colors'].items()), v['cap_cells'], v['rise_max'], v['rise_from_x']), font=f12, fill=DD.INK)
    can = can.crop((0, 0, W, y + 30))
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    B = Bulwark(design)
    B.design_rail()
    B.build()
    v = B.verify()
    B.write()
    v['files'] = B.files
    v['cavity_filled'] = B.cavity_filled
    json.dump(v, open(os.path.join(design, 'verify_bulwark.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(B, os.path.join(design, 'sheet10_bulwark_v1.png'))
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
