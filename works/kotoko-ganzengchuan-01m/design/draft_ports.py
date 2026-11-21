# 福建趕繒船 新圖紙 03（TASK-1314 步驟 3/4）：露天舷牆砲門開口、船尾窗開口、白底黑舷護木、艏眼與「花屁股」彩繪艉封板
#   出處：kaguya-shachuan-01m/design/draft_ports.py（改寫為 8 門 4l 露天舷牆砲門、2 扇艉窗、福船黑舷白底＋花屁股彩繪圖騰）
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

    # 1. 露天主甲板 4 對舷牆砲門缺口（w=8, sill=4 ⇒ z=39 起切通舷頂）
    gp = plan['ports']['gun']
    half_w = int(gp['w']) // 2
    z_sill = int(plan['decks']['main']['floor']) + int(gp['sill'])
    for gx in gp['x']:
        if probe == 'skip_port':
            continue
        x_lo, x_hi = gx - half_w, gx + half_w - 1
        for x in range(x_lo, x_hi + 1):
            zt = int(round(float(L.top_z(x + 0.5)))) + 1
            for z in range(z_sill, zt + 1):
                for y in range(YC - 36, YC + 37):
                    if abs(y - YC) >= 22 and (x, y, z) in hull:
                        carve[(x, y, z)] = hull[(x, y, z)]
        # 朱紅砲門檻與側框
        for x in range(x_lo - 1, x_hi + 2):
            for z in range(z_sill - 1, 50):
                for y in range(YC - 36, YC + 37):
                    if abs(y - YC) >= 22 and (x, y, z) in hull and (x, y, z) not in carve:
                        if z == z_sill - 1 or x in (x_lo - 1, x_hi + 1):
                            paint[(x, y, z)] = RED

    # 2. 尾樓下舵艙艉封板 2 扇花格艉窗
    swin = plan['ports']['stern_windows']
    GLASS = int(swin['glass_color'])
    for y0, y1 in swin['ys']:
        for y in range(y0, y1 + 1):
            for z in range(swin['z_lo'], swin['z_hi'] + 1):
                hits = [x for x in range(swin['x_min'], swin['x_max'] + 1) if (x, y, z) in hull]
                for x in hits:
                    carve[(x, y, z)] = hull[(x, y, z)]
                if hits:
                    glass[(min(hits) + 1, y, z)] = GLASS
        for y in range(y0 - 1, y1 + 2):
            for z in range(swin['z_lo'] - 1, swin['z_hi'] + 2):
                for x in range(swin['x_min'], swin['x_max'] + 1):
                    if (x, y, z) in hull and (x, y, z) not in carve and (x, y, z) in surf:
                        if z in (swin['z_lo'] - 1, swin['z_hi'] + 1) or y in (y0 - 1, y1 + 1):
                            paint[(x, y, z)] = GOLD

    # 3. 塗裝：白底黑舷主護木帶 ＋ 高昂艏眼 ＋ 「花屁股」高尾樓彩繪圖騰
    for (x, y, z) in surf:
        if (x, y, z) in carve:
            continue
        dy = abs(y - YC)
        # (a) 主護木黑帶（隨水線上緣與艏翹微升）
        zw = 32 if x <= 250 else int(round(32 + 6 * (x - 250) / 74.0))
        if z in (zw, zw + 1) and (x, y, z) not in paint:
            paint[(x, y, z)] = WALE
        # 舷頂壓條下方一格加朱漆細線（腰部避開尾樓立面）
        zt = int(round(float(L.top_z(x + 0.5)))) - 1
        if z == zt - 1 and (x, y, z) not in paint and x > 113:
            paint[(x, y, z)] = RED
        # (b) 尾樓腰線（z=52..53）朱漆＋金飾帶
        if x <= 112 and z in (52, 53) and (x, y, z) not in paint:
            paint[(x, y, z)] = RED if z == 52 else GOLD

        # (c) 高尾「花屁股」艉封板彩繪（嚴格限於艉背面 x <= x_aft(z) + 1.0, z=36..69）
        xa_z = float(L.x_aft(z))
        if x <= xa_z + 1.0 and 36 <= z <= 69 and (x, y, z) not in paint:
            if z in (36, 37, 68, 69) or dy >= 17:
                paint[(x, y, z)] = RED
            elif 54 <= z <= 67:
                # 中央祥瑞圓徽（z=58..64, dy<=4）＋ 兩翼青綠金黃捲雲框飾
                r2 = (z - 61) ** 2 + (dy * 0.85) ** 2
                if r2 <= 10:
                    paint[(x, y, z)] = RED if r2 <= 3.5 else GOLD
                elif dy in (7, 8, 12, 13) or z in (56, 65):
                    paint[(x, y, z)] = TEAL
                elif (dy + z) % 4 == 0:
                    paint[(x, y, z)] = GOLD
                else:
                    paint[(x, y, z)] = WALE
            elif 38 <= z <= 51:
                if dy <= 4 and z in (42, 43, 44, 45):
                    paint[(x, y, z)] = GOLD
                elif dy >= 14 or z in (39, 49):
                    paint[(x, y, z)] = TEAL
                else:
                    paint[(x, y, z)] = RED if (dy % 3 == 0) else TRIM

        # (d) 高昂福船艏彩繪與龍目（x=305..310, z=43..47）＋ 朱紅艏柱金冠
        if 305 <= x <= 310 and 43 <= z <= 47 and dy >= 4 and (x, y, z) not in paint:
            d2 = (x - 307.5) ** 2 + (z - 45.0) ** 2
            if d2 <= 1.2:
                paint[(x, y, z)] = WALE
            elif d2 <= 4.5:
                paint[(x, y, z)] = WHITE
            elif d2 <= 7.0:
                paint[(x, y, z)] = GOLD
        xf_z = float(L.x_fwd(z))
        if x >= xf_z - 1.2 and z >= 28 and (x, y, z) not in paint:
            paint[(x, y, z)] = GOLD if z >= 54 else RED

    assert not (set(carve) & set(paint)), 'carve 與 paint 重疊'

    if probe:
        print(json.dumps({'probe': probe, 'carve': len(carve), 'paint': len(paint), 'glass': len(glass)}, ensure_ascii=False))
        return

    os.makedirs(os.path.join(design, 'masks', 'ports'), exist_ok=True)
    c_path = os.path.join(design, 'masks', 'ports', 'carve.vox.txt')
    p_path = os.path.join(design, 'masks', 'ports', 'paint.vox.txt')
    g_path = os.path.join(design, 'masks', 'ports', 'glass.vox.txt')
    with open(c_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 福建趕繒船 步驟 4：砲門與船尾窗刻除清單（帶守門色）x,y,z,color\n')
        for k in sorted(carve):
            f.write(f'{k[0]},{k[1]},{k[2]},{carve[k]}\n')
    with open(p_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 福建趕繒船 步驟 4：白底黑舷與花屁股塗裝覆寫清單 x,y,z,color\n')
        for k in sorted(paint):
            f.write(f'{k[0]},{k[1]},{k[2]},{paint[k]}\n')
    with open(g_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 福建趕繒船 步驟 6：船尾窗玻璃清單 x,y,z,color\n')
        for k in sorted(glass):
            f.write(f'{k[0]},{k[1]},{k[2]},{glass[k]}\n')

    # 生成對照圖 sheet03_ports_paint_v1.png（右舷側視＋花屁股正後視）
    final_hull = dict(hull)
    for k in carve:
        final_hull.pop(k, None)
    for k, c in paint.items():
        final_hull[k] = c

    f18, f13 = font(18), font(13)
    im = Image.new('RGB', (1680, 620), (248, 244, 234))
    d = ImageDraw.Draw(im)
    d.text((36, 16), '福建趕繒船 新圖紙 03 — 露天 4 磅砲門、白底黑舷、艏眼與「花屁股」彩繪艉封板', fill=(25, 25, 25), font=f18)
    ox, oy, sc = 50, 440, 4
    side_proj = {}
    for (x, y, z), c in final_hull.items():
        if y >= YC:
            k = (x, z)
            if k not in side_proj or y > side_proj[k][0]:
                side_proj[k] = (y, c)
    for (x, z), (_, c) in side_proj.items():
        px, py = ox + (x - 55) * sc, oy - z * sc
        d.rectangle([px, py, px + sc - 1, py + sc - 1], fill=rgb(c))

    # 艉視（花屁股正面）
    ox_st = 1350
    d.text((ox_st - 110, 60), '花屁股正後視圖', fill=(25, 25, 25), font=f13)
    stern_proj = {}
    for (x, y, z), c in final_hull.items():
        if x <= 112:
            k = (y, z)
            if k not in stern_proj or x < stern_proj[k][0]:
                stern_proj[k] = (x, c)
    for (y, z), (_, c) in stern_proj.items():
        px, py = ox_st + (y - YC) * 5, oy - z * 5
        d.rectangle([px, py, px + 4, py + 4], fill=rgb(c))

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
