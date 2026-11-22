# 明鄭一號大鳥船 新圖紙 03（TASK-1316 步驟 3/4）：兩重砲位砲門開口、雙層艉窗開口、雙黑護木帶、朱漆戰棚、艏眼與「花屁股」彩繪高尾樓
#   出處：kotoko-ganzengchuan-01m/design/draft_ports.py（改寫為 12 門封閉下層砲門＋12 門露天上戰棚砲門＋雙層 4 扇艉窗）
#   用法：python -I -X utf8 draft_ports.py <design 資料夾> [--probe=skip_port]
import sys, os, json, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_lines as DL

sys.stdout.reconfigure(encoding='utf-8')


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def main():
    design = HERE
    probe = None
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            probe = a.split('=', 1)[1]
        elif not a.startswith('--'):
            design = a

    plan = HL.load_plan(design)
    L, G, S, x0, ylo = DL.build(plan, None)
    hull = {(int(xi + x0), int(yi + ylo), int(zi)): int(G[xi, yi, zi])
            for xi, yi, zi in np.argwhere(G > 0)}

    YC = L.YC
    C = {k: DL.V(v) for k, v in plan['hull_build']['colors'].items()}
    WALE = C['wale']    # 36 黑舷
    TRIM = C['trim']    # 104 深硬木
    RED = C['red']      # 192 朱漆
    GOLD = C['gold']    # 212 金黃
    TEAL = C['teal']    # 53 青綠
    WHITE = C['below']  # 218 白底

    sx, sy, sz = S.shape
    surf = set()
    for xi, yi, zi in np.argwhere(G > 0):
        for dx, dy, dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            nx, ny, nz = xi + dx, yi + dy, zi + dz
            if not (0 <= nx < sx and 0 <= ny < sy and 0 <= nz < sz and S[nx, ny, nz]):
                surf.add((int(xi + x0), int(yi + ylo), int(zi)))
                break

    carve = {}
    paint = {}
    glass = {}

    # 1a. 下層封閉主砲甲板 6 對（12 門）紅夷大銅砲砲門（w=8, h=7, sill=5 -> z=53..59）
    enc = plan['ports']['enclosed']
    half_w = int(enc['w']) // 2
    z_enc_lo = int(plan['decks']['main']['floor']) + int(enc['sill'])
    z_enc_hi = z_enc_lo + int(enc['h']) - 1
    for gx in enc['x']:
        if probe == 'skip_port':
            continue
        x_lo, x_hi = gx - half_w, gx + half_w - 1
        for x in range(x_lo, x_hi + 1):
            for z in range(z_enc_lo, z_enc_hi + 1):
                for y in range(YC - 56, YC + 57):
                    if abs(y - YC) >= 20 and (x, y, z) in hull:
                        carve[(x, y, z)] = hull[(x, y, z)]
        for x in range(x_lo - 1, x_hi + 2):
            for z in range(z_enc_lo - 1, z_enc_hi + 2):
                for y in range(YC - 56, YC + 57):
                    if abs(y - YC) >= 20 and (x, y, z) in hull and (x, y, z) not in carve:
                        if z in (z_enc_lo - 1, z_enc_hi + 1) or x in (x_lo - 1, x_hi + 1):
                            paint[(x, y, z)] = RED

    # 1b. 上戰棚 6 對（2×紅夷船首＋10×發熕兩舷）露天舷牆缺口（w=8, sill=4 -> z=74 起切通舷頂）
    for grp in (plan['ports']['upper_hongyi'], plan['ports']['upper_fagong']):
        hw = int(grp['w']) // 2
        z_sill = int(plan['decks']['upper']['floor']) + int(grp['sill'])
        for gx in grp['x']:
            if probe == 'skip_port':
                continue
            x_lo, x_hi = gx - hw, gx + hw - 1
            for x in range(x_lo, x_hi + 1):
                zt = int(round(float(L.top_z(x + 0.5)))) + 1
                for z in range(z_sill, zt + 1):
                    for y in range(YC - 56, YC + 57):
                        if abs(y - YC) >= 18 and (x, y, z) in hull:
                            carve[(x, y, z)] = hull[(x, y, z)]
            for x in range(x_lo - 1, x_hi + 2):
                for z in range(z_sill - 1, 90):
                    for y in range(YC - 56, YC + 57):
                        if abs(y - YC) >= 18 and (x, y, z) in hull and (x, y, z) not in carve:
                            if z == z_sill - 1 or x in (x_lo - 1, x_hi + 1):
                                paint[(x, y, z)] = RED

    # 2. 雙層尾樓下艉封板 4 扇花格艉窗
    swin = plan['ports']['stern_windows']
    GLASS = int(swin['glass_color'])
    for tier in swin['tiers']:
        for y0, y1 in tier['ys']:
            for y in range(y0, y1 + 1):
                for z in range(tier['z_lo'], tier['z_hi'] + 1):
                    hits = [x for x in range(tier['x_min'], tier['x_max'] + 1) if (x, y, z) in hull]
                    for x in hits:
                        carve[(x, y, z)] = hull[(x, y, z)]
                    if hits:
                        glass[(min(hits) + 1, y, z)] = GLASS
            for y in range(y0 - 1, y1 + 2):
                for z in range(tier['z_lo'] - 1, tier['z_hi'] + 2):
                    for x in range(tier['x_min'], tier['x_max'] + 1):
                        if (x, y, z) in hull and (x, y, z) not in carve and (x, y, z) in surf:
                            if z in (tier['z_lo'] - 1, tier['z_hi'] + 1) or y in (y0 - 1, y1 + 1):
                                paint[(x, y, z)] = GOLD

    # 3. 塗裝：白底雙黑護木帶 ＋ 戰棚朱漆帶 ＋ 高昂龍目艏眼 ＋ 「花屁股」高尾樓彩繪圖騰
    for (x, y, z) in surf:
        if (x, y, z) in carve:
            continue
        dy = abs(y - YC)
        # (a) 雙層黑漆護木帶（隨艏翹微升）
        zw1 = 46 if x <= 350 else int(round(46 + 8 * (x - 350) / 105.0))
        zw2 = 67 if x <= 350 else int(round(67 + 8 * (x - 350) / 105.0))
        if (z in (zw1, zw1 + 1) or z in (zw2, zw2 + 1)) and (x, y, z) not in paint:
            paint[(x, y, z)] = WALE
        # 上戰棚舷頂壓條下方朱漆戰棚帶
        zt = int(round(float(L.top_z(x + 0.5)))) - 1
        if z == zt - 1 and (x, y, z) not in paint and x > 133:
            paint[(x, y, z)] = RED
        # (b) 尾樓腰線（z=90..91）朱漆＋金飾帶
        if x <= 132 and z in (90, 91) and (x, y, z) not in paint:
            paint[(x, y, z)] = RED if z == 90 else GOLD

        # (c) 高尾「花屁股」艉封板彩繪（x <= x_aft(z) + 1.2, z=52..107）
        xa_z = float(L.x_aft(z))
        if x <= xa_z + 1.2 and 52 <= z <= 107 and (x, y, z) not in paint:
            if z in (52, 53, 106, 107) or dy >= 24:
                paint[(x, y, z)] = RED
            elif 92 <= z <= 105:
                r2 = (z - 99) ** 2 + (dy * 0.75) ** 2
                if r2 <= 18:
                    paint[(x, y, z)] = RED if r2 <= 6 else GOLD
                elif dy in (10, 11, 17, 18) or z in (94, 103):
                    paint[(x, y, z)] = TEAL
                elif (dy + z) % 5 == 0:
                    paint[(x, y, z)] = GOLD
                else:
                    paint[(x, y, z)] = WALE
            elif 63 <= z <= 88:
                if dy <= 6 and z in (68, 69, 70, 71, 84, 85):
                    paint[(x, y, z)] = GOLD
                elif dy >= 20 or z in (65, 87):
                    paint[(x, y, z)] = TEAL
                else:
                    paint[(x, y, z)] = RED if (dy % 4 == 0) else TRIM
            elif 54 <= z <= 62:
                paint[(x, y, z)] = TEAL if dy >= 18 else (GOLD if z == 61 else TRIM)

        # (d) 高昂福船龍目艏眼（x=428..435, z=76..81）＋ 朱紅艏柱金冠
        if 428 <= x <= 435 and 76 <= z <= 81 and dy >= 4 and (x, y, z) not in paint:
            d2 = (x - 431.5) ** 2 + (z - 78.5) ** 2
            if d2 <= 1.5:
                paint[(x, y, z)] = WALE
            elif d2 <= 5.5:
                paint[(x, y, z)] = WHITE
            elif d2 <= 9.0:
                paint[(x, y, z)] = GOLD
        xf_z = float(L.x_fwd(z))
        if x >= xf_z - 1.5 and z >= 46 and (x, y, z) not in paint:
            paint[(x, y, z)] = GOLD if z >= 86 else RED

    assert not (set(carve) & set(paint)), 'carve 與 paint 重疊'

    if probe:
        print(json.dumps({'probe': probe, 'carve': len(carve), 'paint': len(paint), 'glass': len(glass)}, ensure_ascii=False))
        return

    os.makedirs(os.path.join(design, 'masks', 'ports'), exist_ok=True)
    c_path = os.path.join(design, 'masks', 'ports', 'carve.vox.txt')
    p_path = os.path.join(design, 'masks', 'ports', 'paint.vox.txt')
    g_path = os.path.join(design, 'masks', 'ports', 'glass.vox.txt')
    with open(c_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 明鄭一號大鳥船 步驟 4：兩重砲門與雙層船尾窗刻除清單（帶守門色）x,y,z,color\n')
        for k in sorted(carve):
            f.write(f'{k[0]},{k[1]},{k[2]},{carve[k]}\n')
    with open(p_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 明鄭一號大鳥船 步驟 4：白底黑舷朱漆戰棚與花屁股塗裝覆寫清單 x,y,z,color\n')
        for k in sorted(paint):
            f.write(f'{k[0]},{k[1]},{k[2]},{paint[k]}\n')
    with open(g_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 明鄭一號大鳥船 步驟 6：船尾窗玻璃清單 x,y,z,color\n')
        for k in sorted(glass):
            f.write(f'{k[0]},{k[1]},{k[2]},{glass[k]}\n')

    final_hull = dict(hull)
    for k in carve:
        final_hull.pop(k, None)
    for k, c in paint.items():
        final_hull[k] = c

    f18, f13 = font(18), font(13)
    im = Image.new('RGB', (1920, 720), (248, 244, 234))
    d = ImageDraw.Draw(im)
    d.text((36, 16), '明鄭一號大鳥船 新圖紙 03 — 兩重砲門、白底雙黑舷、艏眼與「花屁股」高尾樓', fill=(25, 25, 25), font=f18)
    ox, oy, sc = 50, 560, 3
    side_proj = {}
    for (x, y, z), c in final_hull.items():
        if y >= YC:
            k = (x, z)
            if k not in side_proj or y > side_proj[k][0]:
                side_proj[k] = (y, c)
    for (x, z), (_, c) in side_proj.items():
        px, py = ox + (x - 50) * sc, oy - z * sc
        d.rectangle([px, py, px + sc - 1, py + sc - 1], fill=rgb(c))

    ox_st = 1560
    d.text((ox_st - 110, 70), '花屁股正後視圖', fill=(25, 25, 25), font=f13)
    stern_proj = {}
    for (x, y, z), c in final_hull.items():
        if x <= 132:
            k = (y, z)
            if k not in stern_proj or x < stern_proj[k][0]:
                stern_proj[k] = (x, c)
    for (y, z), (_, c) in stern_proj.items():
        px, py = ox_st + (y - YC) * 4, oy - z * 4
        d.rectangle([px, py, px + 3, py + 3], fill=rgb(c))

    png_path = os.path.join(design, 'sheet03_ports_paint_v1.png')
    im.save(png_path)
    ver = {
        'carve_cells': len(carve),
        'paint_cells': len(paint),
        'glass_cells': len(glass),
        'final_hull_cells': len(final_hull),
        'carve_sha256': hashlib.sha256(open(c_path, 'rb').read()).hexdigest(),
        'paint_sha256': hashlib.sha256(open(p_path, 'rb').read()).hexdigest(),
        'sheet03_sha256': hashlib.sha256(open(png_path, 'rb').read()).hexdigest(),
    }
    with open(os.path.join(design, 'verify_ports.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(ver, f, ensure_ascii=False, indent=2)
    print(json.dumps(ver, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
