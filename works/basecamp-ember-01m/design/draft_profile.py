# 餘燼號 新圖紙 01（TASK-0519 階段一）：憲法號船殼插一層砲甲板
#   輸入：plan.json（band／decks／guns）＋ 憲法號船殼現況（CLI export，links=none）＋ 憲法號 design/source_ports*.json（砲門）
#   ⇒ masks/band/band_layer.vox.txt（插進來那一段的「一層」，z 欄 ＝ 0；落 23 次）、masks/band/entry_fill.vox.txt（entry port 在切口下面那一截補起來）、
#      verify_profile.json、sheet01_profile_v1.png（側面：憲法號／餘燼號上下對照＋甲板線＋砲門＋砲位表）、sheet02_sections_v1.png（橫剖面）
# 用法：python -I draft_profile.py <design 資料夾>
#   · 只讀、不落格：餘燼號的船殼在這裡是「算出來的」（z < 切口不動、z ≥ 切口抬高、中間那段複製來源層）—— 拿來畫圖、量結構；落格是下一階段
import sys, os, json, math, hashlib, subprocess, tempfile
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

CON = 'basecamp-frigate-constitution-01m'
CON_DESIGN = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), CON, 'design')
YC = 160


def export_list(work, links='none'):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work,
                            '--arg', 'out=' + out, '--arg', 'links=' + links], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0 or not os.path.exists(out):
            raise SystemExit('匯出失敗：' + (r.stdout + r.stderr)[-600:])
        return np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def rgb(c):
    c = int(c)
    return (round(((c >> 5) & 7) * 255 / 7), round(((c >> 2) & 7) * 255 / 7), round((c & 3) * 255 / 3))


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


class Ember:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        B = s.plan['band']
        s.cut, s.h, s.src = B['cut_z'], B['height'], B['source_layer']
        a = export_list(CON)
        assert len(a) == s.plan['base']['voxels'], ('憲法號船殼格數跟 plan 記的不一樣', len(a))
        s.con = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
        s.read = {'constitution_voxels': len(s.con)}

    def build(s):
        B = s.plan['band']['entry_slot']
        x0, x1, zf, fx = B['x'][0], B['x'][1], B['z_from'], B['fill_from_x']
        # entry port 的缺口：切口下面那一截（z_from..cut−1）與來源層，都照 fill_from_x 那一欄補（同一個 y、同一個 z 的顏色）
        s.fill = {}
        for z in range(zf, s.cut):
            col = {(y): c for (x, y, zz), c in s.con.items() if x == fx and zz == z}
            for y, c in col.items():
                for x in range(x0, x1 + 1):
                    if (x, y, z) not in s.con:
                        s.fill[(x, y, z)] = c
        layer = {(x, y): c for (x, y, z), c in s.con.items() if z == s.src}
        for (x, y, z), c in s.fill.items():
            if z == s.src:
                layer[(x, y)] = c
        s.layer = layer
        em = {}
        for (x, y, z), c in s.con.items():
            em[(x, y, z if z < s.cut else z + s.h)] = c
        for k, c in s.fill.items():
            em[k] = c
        for dz in range(s.h):
            for (x, y), c in layer.items():
                em[(x, y, s.cut + dz)] = c
        s.em = em
        s.read['entry_fill'] = len(s.fill)
        s.read['band_layer'] = len(layer)
        s.read['band_cells'] = len(layer) * s.h
        s.read['ember_hull_expected'] = len(em)
        assert len(em) == len(s.con) + len(s.fill) + len(layer) * s.h, '有格重疊'

    def structure(s, cells):
        arr = np.array(list(cells), dtype=np.int32)
        lo = arr.min(0)
        A = np.zeros(tuple(arr.max(0) - lo + 3), bool)
        A[tuple((arr - lo + 1).T)] = True
        lab, n = ndimage.label(A)
        air, na = ndimage.label(~A)
        return {'components': int(n), 'cavities': int(na - 1)}

    def ports(s):
        sp = json.load(open(os.path.join(CON_DESIGN, 'source_ports.json'), encoding='utf-8'))
        ss = json.load(open(os.path.join(CON_DESIGN, 'source_ports_spar.json'), encoding='utf-8'))
        low = [(p['X_aft'], p['X_fwd'], p['sill'], p['lintel']) for p in sp['ports_gun_deck']]
        bp = sp['bow_port']
        lowbow = (bp['bottom']['X_aft'], bp['top']['X_fwd'], bp['bottom']['Z'], bp['top']['Z'])
        spar = [(p['X_aft'], p['X_fwd'], p['sill'], p['lintel'], p['group']) for p in ss['ports']]
        s.port_rows = {
            'lower_gun': low + [lowbow],
            'upper_gun': [(a, b, c + s.h, d + s.h) for a, b, c, d in low + [lowbow]],
            'spar': [(a, b, c + s.h, d + s.h) for a, b, c, d, g in spar],
        }
        # 量：上層砲門的框落在插進來那一段裡（整個框在 [cut, cut+h) 裡）
        inside = sum(1 for a, b, c, d in s.port_rows['upper_gun'] if c >= s.cut and d < s.cut + s.h)
        s.read['upper_ports_inside_band'] = '%d/%d' % (inside, len(s.port_rows['upper_gun']))
        # 量：上層砲門框裡現在（餘燼號算出來的船殼）是實心外板 —— 下一階段要開的格數（S 舷，外板那一格）
        return s.port_rows

    def side_image(s, cells, title, z_top, scale=2, x0=80, x1=700):
        W, H = (x1 - x0) * scale, (z_top + 4) * scale
        im = Image.new('RGB', (W, H), (250, 249, 244))
        px = im.load()
        best = {}
        for (x, y, z), c in cells.items():
            if y >= YC and x0 <= x < x1:
                k = (x, z)
                if k not in best or y > best[k][0]:
                    best[k] = (y, c)
        for (x, z), (y, c) in best.items():
            col = rgb(c)
            for i in range(scale):
                for j in range(scale):
                    X, Y = (x - x0) * scale + i, H - 1 - (z * scale + j)
                    if 0 <= Y < H:
                        px[X, Y] = col
        return im

    def sheet_profile(s, path):
        sc, x0, x1 = 2, 80, 700
        con_im = s.side_image(s.con, '憲法號', 160, sc, x0, x1)
        em_im = s.side_image(s.em, '餘燼號', 160, sc, x0, x1)
        W = con_im.width + 40
        Ht = 70 + con_im.height + 50 + em_im.height + 330
        im = Image.new('RGB', (W, Ht), (250, 249, 244))
        d = ImageDraw.Draw(im)
        f20, f14, f12 = font(22), font(15), font(13)
        d.text((20, 14), '餘燼號 新圖紙 01 v1 —— 憲法號在 z %d 切開、插 %d 格（複製 z %d），上面全部抬高' % (s.cut, s.h, s.src), font=f20, fill=(30, 30, 30))
        d.text((20, 44), '上：憲法號船殼現況（%s 格）　下：餘燼號（算出來的，%s 格）　右舷側面、1 格 ＝ %d px、x %d–%d' % (
            format(len(s.con), ','), format(len(s.em), ','), sc, x0, x1), font=f14, fill=(80, 80, 80))
        oy1 = 70
        im.paste(con_im, (20, oy1))
        oy2 = oy1 + con_im.height + 50
        d.text((20, oy2 - 26), '餘燼號：甲板線（虛）、砲門框（紅＝下層、橙＝上層、藍＝上甲板）、插入段（淡黃底）、水線 62.86', font=f14, fill=(80, 80, 80))
        im.paste(em_im, (20, oy2))
        H2 = em_im.height

        def P(x, z, oy, H):
            return (20 + (x - x0) * sc, oy + H - 1 - z * sc)
        # 插入段底色（畫在線底下：用半透明疊）
        ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        a, b = P(x0, s.cut + s.h, oy2, H2), P(x1, s.cut, oy2, H2)
        od.rectangle([a, b], fill=(255, 220, 90, 60))
        im.paste(Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB'))
        d = ImageDraw.Draw(im)
        for oy, H in ((oy1, con_im.height), (oy2, H2)):
            d.line([P(x0, 62.86, oy, H), P(x1, 62.86, oy, H)], fill=(40, 110, 200), width=1)
        # 甲板線（plan.decks 的分段高度 "z｜x｜z｜x…"）
        for nm, D in s.plan['decks'].items():
            seg = [t for t in str(D['z']).split('｜')]
            try:
                vals = [float(t) for t in seg]
            except ValueError:
                vals = [float(seg[0].split('（')[0])]
            zs, xs = vals[0::2], vals[1::2]
            bounds = [x0] + xs + [x1]
            for i, z in enumerate(zs):
                xa, xb = bounds[i], bounds[i + 1]
                for xx in range(int(xa), int(xb), 6):
                    d.line([P(xx, z, oy2, H2), P(min(xx + 3, xb), z, oy2, H2)], fill=(90, 60, 30), width=1)
            d.text((P(x1, zs[-1], oy2, H2)[0] - 120, P(x1, zs[-1], oy2, H2)[1] - 16), {'orlop': 'orlop', 'berth': 'berth', 'lower_gun': '下層砲甲板',
                    'upper_gun': '上層砲甲板', 'spar': '上甲板'}[nm], font=f12, fill=(90, 60, 30))
        colors = {'lower_gun': (200, 40, 40), 'upper_gun': (230, 130, 20), 'spar': (40, 90, 200)}
        for row, L in s.port_rows.items():
            for a_, b_, c_, e_ in L:
                d.rectangle([P(a_, e_, oy2, H2), P(b_, c_, oy2, H2)], outline=colors[row], width=2)
        d.line([P(x0, s.cut, oy2, H2), P(x0 + 25, s.cut, oy2, H2)], fill=(200, 0, 0), width=2)
        d.text((P(x0, s.cut, oy2, H2)[0] + 2, P(x0, s.cut, oy2, H2)[1] + 2), '切口 z %d' % s.cut, font=f12, fill=(200, 0, 0))
        # 砲位表
        ty = oy2 + H2 + 20
        d.text((20, ty), '砲位表（目標：憲法號 54 門 × 1.5，約 81）', font=f20, fill=(30, 30, 30))
        ty += 34
        hdr = ['甲板', '每舷砲門', '舷側', '船頭', '船尾', '砲']
        colx = [20, 150, 390, 455, 515, 575]
        for i, t in enumerate(hdr):
            d.text((colx[i], ty), t, font=f14, fill=(60, 60, 60))
        ty += 24
        nm = {'lower_gun': '下層砲甲板', 'upper_gun': '上層砲甲板', 'spar': '上甲板'}
        tot = 0
        for r in s.plan['guns']['rows']:
            vals = [nm[r['deck']], r['ports_per_side'], str(r['broadside']), str(r['chase_bow']), str(r['chase_stern']), r['gun']]
            tot += r['broadside'] + r['chase_bow'] + r['chase_stern']
            for i, t in enumerate(vals):
                d.text((colx[i], ty), t, font=f12 if i == 5 else f14, fill=(30, 30, 30))
            ty += 26
        d.text((20, ty + 6), '合計 %d 門（憲法號 54 門的 %.2f 倍）；追擊砲 18 磅長砲；船尾砲門開在 transom（下層：船尾窗那一列往下；上層：插入段的船尾）' % (tot, tot / 54), font=f14, fill=(30, 30, 30))
        s.read['guns_total'] = tot
        d.text((20, ty + 34), '甲板高度：orlop 42、berth 60–63、下層砲甲板 82–88（憲法號 gun deck）、上層砲甲板 105–110（憲法號 spar deck 的位置）、上甲板 128–133（＋23）', font=f12, fill=(60, 60, 60))
        d.text((20, ty + 54), '注意：圖上的甲板線與上層／上甲板砲門框是設計（plan.json），格子還沒開；下層砲門是憲法號已開的', font=f12, fill=(160, 60, 60))
        im.save(path)

    def sections(s, path, xs=(160, 250, 350, 449, 520, 600, 640)):
        sc, ztop = 3, 160
        pw = 2 * 70 * sc + 20
        W, H = pw * len(xs) + 20, ztop * sc + 110
        im = Image.new('RGB', (W, H), (250, 249, 244))
        d = ImageDraw.Draw(im)
        f14, f12 = font(15), font(12)
        d.text((10, 8), '餘燼號 新圖紙 01 v1：橫剖面（左半 ＝ 憲法號、右半 ＝ 餘燼號；外緣 ＝ 那一層最外面的格）', font=f14, fill=(30, 30, 30))
        for i, X in enumerate(xs):
            cx = 10 + i * pw + pw // 2
            base = H - 30
            for cells, sgn, col in ((s.con, -1, (90, 90, 160)), (s.em, 1, (180, 70, 40))):
                prof = {}
                for (x, y, z), c in cells.items():
                    if x == X and y >= YC:
                        prof[z] = max(prof.get(z, -1), y - YC)
                pts = [(cx + sgn * (prof[z] + 1) * sc, base - z * sc) for z in sorted(prof)]
                if len(pts) > 1:
                    d.line(pts, fill=col, width=2)
            d.line([(cx, base), (cx, base - ztop * sc)], fill=(200, 200, 200))
            d.line([(cx - 70 * sc, base - 62.86 * sc), (cx + 70 * sc, base - 62.86 * sc)], fill=(40, 110, 200))
            for z in (s.cut, s.cut + s.h):
                d.line([(cx, base - z * sc), (cx + 70 * sc, base - z * sc)], fill=(230, 180, 60))
            d.text((cx - 30, base + 6), 'x %d' % X, font=f12, fill=(30, 30, 30))
        im.save(path)

    def write_masks(s):
        out = os.path.join(s.design, 'masks', 'band')
        os.makedirs(out, exist_ok=True)
        files = {}
        rows = sorted((x, y, 0, c) for (x, y), c in s.layer.items())
        p = os.path.join(out, 'band_layer.vox.txt')
        open(p, 'w', encoding='utf-8', newline='\n').write('# 插入段的一層（憲法號 z %d ＋ entry port 缺口補起來；z 欄 ＝ 0；at ＝ 0,0,%d..%d 各落一次）（%d 格）\n' % (
            s.src, s.cut, s.cut + s.h - 1, len(rows)) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
        files['band_layer'] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        rows = sorted((x, y, z, c) for (x, y, z), c in s.fill.items() if z < s.cut)
        p = os.path.join(out, 'entry_fill.vox.txt')
        open(p, 'w', encoding='utf-8', newline='\n').write('# entry port 在切口下面那一截補起來（世界座標 at 0,0,0）（%d 格）\n' % len(rows) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
        files['entry_fill'] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        return files


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    E = Ember(design)
    E.build()
    E.ports()
    v = {'read': E.read}
    v['structure_constitution'] = E.structure(E.con)
    v['structure_ember'] = E.structure(E.em)
    lay = {}
    for c in E.layer.values():
        lay[c] = lay.get(c, 0) + 1
    v['band_layer_colors'] = dict(sorted(lay.items()))
    zmax = max(z for (x, y, z) in E.em)
    v['ember_z_max'] = zmax
    v['constitution_z_max'] = max(z for (x, y, z) in E.con)
    # 反向對照：不補 entry port 缺口 ⇒ 插入段有一條 9 欄 × 23 層的縫（從外面看得到）；量「插入段每一層外緣不連續的欄」要報得出來
    gaps = 0
    for x in range(100, 680):
        ys = [y for (xx, y) in E.layer if xx == x and y > YC]
        if not ys:
            gaps += 1
    v['band_layer_empty_x_cols_100_680'] = gaps
    raw = {(x, y) for (x, y, z) in E.con if z == E.src}
    v['reverse_check_unfilled_empty_cols'] = sum(1 for x in range(100, 680) if not any((x, y) in raw for y in range(YC + 1, 320)))
    E.sheet_profile(os.path.join(design, 'sheet01_profile_v1.png'))
    E.sections(os.path.join(design, 'sheet02_sections_v1.png'))
    v['files'] = E.write_masks()
    v['ports'] = {k: len(L) for k, L in E.port_rows.items()}
    json.dump(v, open(os.path.join(design, 'verify_profile.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
