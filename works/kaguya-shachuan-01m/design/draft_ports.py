# 沙船 新圖紙 03（TASK-1313 步驟 4 後半）：砲門開口、船尾窗開口、主 wale 與艏艉中式塗裝
#   出處：kaguya-guineaman-01m/design/draft_ports.py（改寫為沙船前腰 2 門 4 磅砲缺口、艉艙 2 扇方窗與中式朱紅／深木塗裝）
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
    # 建完整座標系下的船殼字典 (x, y, z) -> color
    hull = {}
    for xi, yi, zi in np.argwhere(G > 0):
        hull[(int(xi + x0), int(yi + ylo), int(zi))] = int(G[xi, yi, zi])

    YC = L.YC
    C = {k: DL.V(v) for k, v in plan['hull_build']['colors'].items()}
    RED = C['red']      # 196 朱紅
    TRIM = C['trim']    # 136 深木
    GOLD = 248          # 248 金黃（龍目／窗框點綴）
    BLACK = 36          # 36 黑（護木下緣與龍目瞳孔）
    GLASS = 155         # 155 窗玻璃（步驟 6 使用）

    # 計算每個 (x, y, z) 是否為外表面格（往外相鄰非 S）
    sx, sy, sz = S.shape
    surf = set()
    for xi, yi, zi in np.argwhere(G > 0):
        is_ext = False
        for dx, dy, dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            nx, ny, nz = xi + dx, yi + dy, zi + dz
            if not (0 <= nx < sx and 0 <= ny < sy and 0 <= nz < sz and S[nx, ny, nz]):
                is_ext = True
                break
        if is_ext:
            surf.add((int(xi + x0), int(yi + ylo), int(zi)))

    carve = {}   # (x,y,z) -> expected_color
    paint = {}   # (x,y,z) -> new_color
    glass = {}   # (x,y,z) -> GLASS

    # 1. 前腰露天 4 磅砲門缺口（x=180 兩舷，w=6: x=177..182, sill=4: z=27..30 切通舷頂）
    gp = plan['ports']['gun']
    for gx in gp['x']:
        if probe == 'skip_port':
            continue
        x_lo, x_hi = gx - 3, gx + 2  # 6 格寬
        z_lo, z_hi = 27, 31          # 從甲板上 4 格起切通舷頂
        for x in range(x_lo, x_hi + 1):
            for z in range(z_lo, z_hi + 1):
                for y in range(YC - 32, YC + 33):
                    if abs(y - YC) >= 18 and (x, y, z) in hull:
                        carve[(x, y, z)] = hull[(x, y, z)]
        # 砲門框（門檻 z=26 與兩側 x=176, 183）塗深紅／深木
        for x in range(x_lo - 1, x_hi + 2):
            for z in range(z_lo - 1, z_hi + 1):
                for y in range(YC - 32, YC + 33):
                    if abs(y - YC) >= 18 and (x, y, z) in hull and (x, y, z) not in carve:
                        if z == z_lo - 1 or x in (x_lo - 1, x_hi + 1):
                            paint[(x, y, z)] = RED

    # 2. 船尾窗（2 扇，在艉艙艉封板 x 38..48，z=28..31，y = YC ± [5..9]）
    #    艉封板斜著往後伸出，在 z=28..31 處 x_aft 約為 43..45
    win_ys = [list(range(YC - 9, YC - 4)), list(range(YC + 5, YC + 10))]
    for wy_list in win_ys:
        for y in wy_list:
            for z in range(28, 32):
                for x in range(38, 49):
                    if (x, y, z) in hull:
                        carve[(x, y, z)] = hull[(x, y, z)]
                        # 最外層那一格留作玻璃清單（步驟 6 貼）
                # 找這條 (y, z) 的最外 x 作為步驟 6 玻璃位置
                xs_hit = [x for x in range(38, 49) if (x, y, z) in carve]
                if xs_hit:
                    glass[(min(xs_hit) + 1, y, z)] = GLASS
        # 窗框周圍塗金邊（上 z=32、下 z=27、左右外緣）
        y_frame = [wy_list[0] - 1] + wy_list + [wy_list[-1] + 1]
        for y in y_frame:
            for z in range(27, 33):
                for x in range(38, 49):
                    if (x, y, z) in hull and (x, y, z) not in carve and (x, y, z) in surf:
                        if z in (27, 32) or y in (wy_list[0] - 1, wy_list[-1] + 1):
                            paint[(x, y, z)] = GOLD

    # 3. 塗裝：
    # (a) 主護木帶（main wale）：深木色 136 / 黑 36 沿主甲板下緣 z=20..21 走全船外表面
    for (x, y, z) in surf:
        if (x, y, z) in carve:
            continue
        # 順艏部微翹的主護木位置
        zw = 21 if x <= 206 else int(round(21 + 5 * (x - 206) / 40.0))
        if z in (zw - 1, zw) and (x, y, z) not in paint:
            paint[(x, y, z)] = TRIM if z == zw else BLACK
        # (b) 艉樓下緣腰帶（z=39）朱紅＋深木
        if x <= 88 and z == 39 and (x, y, z) not in paint:
            paint[(x, y, z)] = RED
        # (c) 艉封板（最外側 x <= L.x_aft(z) + 1.5, z 23..46）塗中式深木底與朱紅邊框
        xa_z = float(L.x_aft(z))
        if x <= xa_z + 1.5 and 23 <= z <= 46 and abs(y - YC) <= 13 and (x, y, z) not in paint:
            if z in (23, 24, 38, 39, 45, 46) or abs(y - YC) >= 12:
                paint[(x, y, z)] = RED
            elif 27 <= z <= 32 and abs(y - YC) <= 10:
                pass  # 窗區留原木或金框
            else:
                paint[(x, y, z)] = TRIM
        # (d) 方艏正面（x >= x_fwd(z) - 1.5, z 22..35）：朱紅牌額＋兩側舷側小龍目（x=234..237, z=32..33）
        xf_z = float(L.x_fwd(z))
        if x >= xf_z - 1.5 and 24 <= z <= 34 and abs(y - YC) <= 10 and (x, y, z) not in paint:
            paint[(x, y, z)] = RED if (z in (24, 34) or abs(y - YC) >= 9) else TRIM
        if 233 <= x <= 236 and 30 <= z <= 32 and abs(y - YC) >= 12 and (x, y, z) not in paint:
            # 龍目：白底 182、黑瞳 36
            paint[(x, y, z)] = BLACK if (x in (234, 235) and z == 31) else 182

    # 驗證 carve 與 paint 不重疊
    assert not (set(carve) & set(paint)), 'carve 與 paint 重疊'

    if probe:
        print(json.dumps({'probe': probe, 'carve': len(carve), 'paint': len(paint), 'glass': len(glass)}, ensure_ascii=False))
        return

    os.makedirs(os.path.join(design, 'masks', 'ports'), exist_ok=True)
    c_path = os.path.join(design, 'masks', 'ports', 'carve.vox.txt')
    p_path = os.path.join(design, 'masks', 'ports', 'paint.vox.txt')
    g_path = os.path.join(design, 'masks', 'ports', 'glass.vox.txt')
    with open(c_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 沙船 步驟 4：砲門與船尾窗刻除清單（帶守門色）x,y,z,color\n')
        for (x, y, z) in sorted(carve):
            f.write(f'{x},{y},{z},{carve[(x, y, z)]}\n')
    with open(p_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 沙船 步驟 4：塗裝覆寫清單 x,y,z,color\n')
        for (x, y, z) in sorted(paint):
            f.write(f'{x},{y},{z},{paint[(x, y, z)]}\n')
    with open(g_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 沙船 步驟 6：船尾窗玻璃清單 x,y,z,color\n')
        for (x, y, z) in sorted(glass):
            f.write(f'{x},{y},{z},{glass[(x, y, z)]}\n')

    # 預期完稿狀態（hull_01 - carve + paint）
    expected = dict(hull)
    for k in carve:
        expected.pop(k, None)
    for k, v in paint.items():
        expected[k] = v

    summary = {
        'hull_cells': len(hull),
        'carve_cells': len(carve),
        'paint_cells': len(paint),
        'glass_cells': len(glass),
        'expected_cells': len(expected),
        'carve_sha256': hashlib.sha256(open(c_path, 'rb').read()).hexdigest(),
        'paint_sha256': hashlib.sha256(open(p_path, 'rb').read()).hexdigest(),
    }
    with open(os.path.join(design, 'verify_ports.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 畫 sheet03_ports_paint_v1.png（側面塗裝＋砲門位置＋方艉正視窗位）
    xs_all = [k[0] for k in expected]
    x_min, x_max = min(xs_all), max(xs_all)
    nz = 54
    sc = 4
    nx = x_max - x_min + 1
    E = np.zeros((nx, 2 * YC + 1, nz), np.uint8)
    for (x, y, z), c in expected.items():
        if z < nz:
            E[x - x_min, y, z] = c
    W, H = nx * sc + 320, nz * sc + 140
    im = Image.new('RGB', (W, H), (248, 244, 234))
    d = ImageDraw.Draw(im)
    f18, f13 = font(18), font(13)
    d.text((30, 14), '沙船 步驟 4：砲門缺口、船尾窗、主 wale 與艏艉塗裝（v1）', fill=(25, 20, 15), font=f18)
    oy = 55
    for xi in range(nx):
        for z in range(nz):
            ys = np.nonzero(E[xi, :, z])[0]
            if len(ys):
                c = rgb(int(E[xi, ys[0], z]))
                d.rectangle([30 + xi * sc, oy + (nz - 1 - z) * sc, 30 + xi * sc + sc - 1, oy + (nz - z) * sc - 1], fill=c)
    # 方艉正視圖（從船尾往船頭看：y = YC-18..YC+18, z = 12..50）
    ox_st = 30 + nx * sc + 40
    d.text((ox_st, oy - 22), '方艉窗位正視', fill=(25, 20, 15), font=f13)
    max_xi_st = min(nx, 55 - x_min)
    for y in range(YC - 18, YC + 19):
        for z in range(12, 50):
            xs_y = np.nonzero(E[:max_xi_st, y, z])[0]
            if len(xs_y):
                c = rgb(int(E[xs_y[0], y, z]))
                d.rectangle([ox_st + (y - (YC - 18)) * 5, oy + (nz - 1 - z) * sc, ox_st + (y - (YC - 18)) * 5 + 4, oy + (nz - z) * sc - 1], fill=c)
    d.text((30, H - 36), f"刻除 {len(carve)} 格 | 塗裝 {len(paint)} 格 | 預期完稿 {len(expected)} 格 | 步驟 6 玻璃 {len(glass)} 格", fill=(40, 30, 20), font=f13)
    im.save(os.path.join(design, 'sheet03_ports_paint_v1.png'))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
