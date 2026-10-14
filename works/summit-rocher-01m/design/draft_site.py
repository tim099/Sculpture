# 岩堡港 新圖紙 01 平面圖（TASK-0580）：plan.json 的 site ⇒ 高度圖（每一欄地面上第一層空氣的 z）、平面圖、剖面、verify_site.json。
# 用法：python -I -X utf8 -B draft_site.py <design 資料夾>
#   · 座標：x ＝ 沿岸（西 → 東）、y ＝ 海 → 山（南 → 北，圖上往上）、z ＝ 高；0.1 m／格；海面 z_sea。
#   · 地面：自然坡（沙灘 → 鎮 → 後山）＋ 岩堡山包（高斯、頂上削平成平台）；鎮裡（town.x0..x1、碼頭以北）照平台與街蓋過去。
#   · 高度圖存成 site_height.npy（int16；海 ＝ −1）⇒ 地形階段直接讀，⛔ 不再用算式重算第二遍。
#   · 重跑逐位元組相同（PNG 不帶時間、json 排序鍵、npy 固定 dtype）。
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = r"C:\Windows\Fonts\msjh.ttc"
BG = (250, 248, 242)
INK = (30, 30, 30)


def font(sz):
    return ImageFont.truetype(FONT, sz)


def smooth(a, b, t):
    u = np.clip((t - a) / (b - a), 0.0, 1.0)
    return u * u * (3 - 2 * u)


def heightmap(S):
    NX, NY = S['NX'], S['NY']
    x = np.arange(NX)[:, None] + 0.5
    y = np.arange(NY)[None, :] + 0.5
    sh = S['shore']
    y_shore = sh['y0'] + sh['bay_depth'] * np.exp(-((x - sh['bay_x']) / sh['bay_sigma']) ** 2)
    G = S['ground']
    z = (S['z_sea'] - 6) + (G['z_quay'] - S['z_sea'] + 6) * smooth(0, 40, y - y_shore + 30)       # 沙灘：海裡 6 格深 → 岸上 40 格內升到碼頭高
    z = z + (G['z_town_top'] - G['z_quay']) * smooth(360, G['y_town_top'], y) + (G['z_back'] - G['z_town_top']) * smooth(G['y_town_top'], NY, y)
    F = S['fort_hill']
    bump = F['amp'] * np.exp(-((x - F['cx']) / F['sx']) ** 2 - ((y - F['cy']) / F['sy']) ** 2)
    z = np.minimum(z + bump, F['plateau_z'])
    # 鎮：碼頭以北、town.x0..x1 之間照平台與街
    T = S['town']; Q = S['quay']
    inx = (x >= T['x0']) & (x < T['x1'])
    for t in S['terraces']:
        iny = (y >= t['y0']) & (y < t['y1'])
        if 'z' in t:
            zt = np.full(z.shape, float(t['z']))
        else:
            zt = t['z0'] + (t['z1'] - t['z0']) * (y - t['y0']) / (t['y1'] - t['y0'])
        z = np.where(inx & iny, zt + 0 * x, z)
    qx = (x >= Q['x0']) & (x < Q['x1'])
    z = np.where(qx & (y >= Q['y_face']) & (y < Q['promenade_y1']), float(Q['z_top']), z)
    z = np.where(qx & (y < Q['y_face']), np.minimum(z, S['z_sea'] - 6), z)                         # 碼頭牆外直接是海
    # 大街往上坡接到自然地面
    for st in S['streets']:
        if st['name'] == 'Grande Rue':
            sx_ = (x >= st['x0']) & (x < st['x1']) & (y >= 640) & (y < st['y1'])
            ztop = z[int((st['x0'] + st['x1']) / 2), st['y1']]
            z = np.where(sx_, 46 + (ztop - 46) * (y - 640) / (st['y1'] - 640), z)
    H = np.floor(z).astype(np.int16)
    H[H < S['z_sea']] = -1                                                                           # 海（不做海床）
    return H


def zone(S, x, y):
    for st in S['streets']:
        if st['x0'] <= x < st['x1'] and st['y0'] <= y < st['y1']:
            return st['kind']
    return None


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    S = plan['site']
    NX, NY = S['NX'], S['NY']
    H = heightmap(S)
    R = plan['site']['rock']
    rock = np.zeros((NX, NY), bool)
    xx, yy = np.meshgrid(np.arange(NX) + 0.5, np.arange(NY) + 0.5, indexing='ij')
    rock = ((xx - R['cx']) / R['rx']) ** 2 + ((yy - R['cy']) / R['ry']) ** 2 <= 1.0
    np.save(os.path.join(d, 'site_height.npy'), H)

    # ── 平面圖：1 px ＝ 1 格 ──
    M = 70
    img = np.zeros((NY, NX, 3), np.uint8)
    pal = {k: v for k, v in plan['palette'].items()}
    def c332(k):
        return (round((k >> 5) * 255 / 7), round(((k >> 2) & 7) * 255 / 7), (k & 3) * 85)
    sea = np.array(c332(pal['sea']))
    for xi in range(NX):
        col = H[xi]
        for yi in range(NY):
            h = col[yi]
            if h < 0:
                c = sea * 0.9
            elif h < S['z_sea'] + 6:
                c = np.array(c332(pal['sand']))
            else:
                k = 0.75 + 0.25 * min(1.0, (h - 30) / 140.0)
                c = np.array(c332(pal['grass'])) * k
            img[NY - 1 - yi, xi] = c
    T = S['town']
    for t in S['terraces']:
        img[NY - t['y1']:NY - t['y0'], T['x0']:T['x1']] = np.array(c332(pal['dirt'])) * (0.92 if 'z' in t else 0.85)
    for st in S['streets']:
        cc = c332(pal['stone_light']) if st['kind'] == 'promenade' else c332(pal['dirt'])
        img[NY - st['y1']:NY - st['y0'], st['x0']:st['x1']] = np.array(cc) * (1.0 if st['kind'] == 'promenade' else 0.78)
    for p in S['piers']:
        img[NY - S['quay']['y_face']:NY - p['y_end'], p['x']:p['x'] + p['w']] = c332(pal['wood'])
    img[(rock.T)[::-1]] = c332(pal['rock'])
    im = Image.fromarray(img)
    # 等高線（每 1 m 細、每 5 m 粗）
    g0 = ImageDraw.Draw(im)
    for xi in range(1, NX - 1):
        for yi in range(1, NY - 1):
            h = H[xi, yi]
            if h < 0:
                continue
            for dx, dy in ((1, 0), (0, 1)):
                h2 = H[xi + dx, yi + dy]
                if h2 >= 0 and h // 10 != h2 // 10:
                    big = (max(h, h2) // 10) % 5 == 0
                    im.putpixel((xi, NY - 1 - yi), (60, 80, 40) if big else (120, 140, 90))
    # 地塊
    g = ImageDraw.Draw(im)
    f12, f14, f18, f24 = font(12), font(14), font(18), font(24)
    tcol = {'A': (190, 60, 40), 'B': (150, 30, 120), 'C': (60, 60, 140), 'D': (120, 80, 20)}
    rows = {1: (362, 468), 2: (522, 640)}
    for L in S['lots']:
        y0, y1 = rows[L['row']]
        g.rectangle([L['x0'], NY - y1, L['x1'] - 1, NY - 1 - y0], outline=tcol[L['type']], width=2)
        g.text((L['x0'] + 4, NY - y1 + 4), L['id'] + " " + L['type'], fill=tcol[L['type']], font=f14)
    for st in S['streets']:
        if st['kind'] != 'promenade' and st['x1'] - st['x0'] > st['y1'] - st['y0']:
            g.text((st['x0'] + 10, NY - st['y1'] + 14), st['name'], fill=INK, font=f14)
        elif st['kind'] != 'promenade':
            g.text((st['x0'] + 2, NY - st['y1'] - 18), st['name'], fill=INK, font=f12)
    g.text((S['quay']['x0'] + 10, NY - S['quay']['promenade_y1'] + 14), "Quai（石砌碼頭，頂面高出海 2.2 m）", fill=INK, font=f14)
    pts = [(px_, NY - py_) for px_, py_ in S['fort_path']]
    g.line(pts, fill=(120, 60, 30), width=3)
    g.text((R['cx'] - 60, NY - R['cy'] - R['ry'] - 22), "岩（9 m）＋ 岩頂小堡", fill=INK, font=f14)
    g.text((80, NY - 120), "海（港灣）", fill=(240, 240, 255), font=f24)
    # 北向、比例尺
    g.polygon([(NX - 60, 40), (NX - 70, 70), (NX - 50, 70)], fill=INK)
    g.text((NX - 66, 74), "N", fill=INK, font=f18)
    sheet = Image.new('RGB', (NX + 2 * M, NY + 2 * M + 320), BG)
    sheet.paste(im, (M, M))
    gs = ImageDraw.Draw(sheet)
    gs.text((20, 14), "岩堡港 Port-du-Rocher　新圖紙 01　平面圖（俯視；上 = 北）　0.1 m／格（1 px = 1 格）　summit 2026-10-14　（設計；底本 托圖嘉 Basse-Terre，沒有描圖）", fill=INK, font=f18)
    yb = M + NY + 16
    for i in range(20):
        a = M + i * 50
        gs.rectangle([a, yb, a + 50, yb + 8], outline=INK, fill=INK if i % 2 == 0 else BG)
    for i in range(0, 21, 2):
        gs.text((M + i * 50 - 6, yb + 12), str(i * 5), fill=INK, font=f14)
    gs.text((M + 1010, yb - 2), "m", fill=INK, font=f14)
    gs.text((M + 1060, yb - 2), "等高線：細 = 每 1 m、粗 = 每 5 m", fill=INK, font=f14)
    # 剖面（南北）：大街 x 630 與岩堡 x 920
    ys = M + NY + 70
    gs.text((M, ys), "剖面（南 → 北；1:1）：灰 = 大街 x 630、褐 = 岩堡 x 920（含 9 m 的岩）；藍 = 海面", fill=INK, font=f14)
    base = ys + 300
    gs.line([(M, base - S['z_sea']), (M + NY, base - S['z_sea'])], fill=(30, 90, 200), width=1)
    for xc, cc in ((630, (110, 110, 110)), (920, (130, 80, 30))):
        pts = []
        for yi in range(NY):
            h = H[xc, yi]
            zz = h if h >= 0 else S['z_sea'] - 6
            if xc == R['cx'] and rock[xc, yi]:
                zz = zz + R['h']
            pts.append((M + yi, base - zz))
        gs.line(pts, fill=cc, width=2)
    sheet.save(os.path.join(d, 'sheet01_site_v1.png'), optimize=False)

    # ── 讀數 ──
    lots = {}
    for L in S['lots']:
        y0, y1 = rows[L['row']]
        blk = H[L['x0']:L['x1'], y0:y1]
        lots[L['id']] = {'type': L['type'], 'zmin': int(blk.min()), 'zmax': int(blk.max())}
    out = {'NX': NX, 'NY': NY, 'sea_columns': int((H < 0).sum()), 'land_columns': int((H >= 0).sum()),
           'z_max_ground': int(H.max()), 'rock_columns': int(rock.sum()), 'rock_base_z': int(H[rock].min()), 'rock_top_z': int(H[rock].max()) + R['h'],
           'lots': lots}
    with open(os.path.join(d, 'verify_site.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(out, fo, ensure_ascii=False, indent=1, sort_keys=True); fo.write('\n')
    print(json.dumps({k: v for k, v in out.items() if k != 'lots'}, ensure_ascii=False))
    print('lots', {k: (v['zmin'], v['zmax']) for k, v in lots.items()})


if __name__ == '__main__':
    main()
