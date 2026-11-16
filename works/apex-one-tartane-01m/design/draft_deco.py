# 塔爾塔納 步驟 6（TASK-1299）：船首喙＋雕首像（deco=1）、船尾陽台／假艉廊（deco=1）、船名徽（deco=1）、三扇船尾窗玻璃（material=glass）
#   輸出：masks/deco/{stern_glass,beak,gallery,nameplate}.vox.txt、deco_spec.json、sheet05_deco_v1.png
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
from draft_lines import hull_volume, shell_colors, font, palette_rgb
from draft_paint import stern_windows

# 簡易 3x5 像素字型（只用左到右讀出的寬度 3 格字母，船名 "LUCIA" 共 5 字 = 5*3 + 4*1 = 19 格寬，完全塞進 27 格寬尾鏡）
FONT3X5 = {
    'L': ['100', '100', '100', '100', '111'],
    'U': ['101', '101', '101', '101', '111'],
    'C': ['111', '100', '100', '100', '111'],
    'I': ['111', '010', '010', '010', '111'],
    'A': ['010', '101', '111', '101', '101'],
}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    x0, ylo, S, dist = hull_volume(L, plan)
    wall, col = shell_colors(plan, S, dist)
    nx, ny, nz = wall.shape
    yc_i = YC - ylo
    PA = plan['paint']
    RED, GOLD, OAK, WALE, GLASS = PA['red'], PA['gold'], 141, PA['wale'], 155

    # ── 1. stern-glass（獨立關聯，1 格厚填在船尾窗中層 x=89，後方須空；不標 deco）──
    windows = stern_windows(plan, YC)
    glass_cells = []
    for w in windows:
        for y in range(w['y0'], w['y1'] + 1):
            for z in range(w['z0'], w['z1'] + 1):
                # first[y, z] 在步驟 4 已開通 x=88,89,90 ⇒ x=89 恰在正中且前後皆開
                glass_cells.append((89, y, z, GLASS))

    # ── 2. deco-beak（船首喙 becco ＋ 雙舷飾條 ＋ 雕首金捲像，完全低於 z=36 讓上方 bout-dehors 無碰撞通過）──
    beak_dict = {}
    def put_b(x, y, z, c):
        # 不覆蓋船殼現有格子（或退到船殼外一格）
        if 0 <= x - x0 < nx and 0 <= y - ylo < ny and 0 <= z < nz and S[x - x0, y - ylo, z]:
            return
        beak_dict[(int(x), int(y), int(z))] = int(c)

    # 船首前伸木喙 knee / becco：自艏柱前緣凹弧優雅上揚（z=14..33 -> x_stem+1 .. x=287），避免下緣塊狀突兀
    for z in range(14, 34):
        xs_hull = int(math.floor(float(L.x_stem(z + 0.5))))
        t = (z - 14) / 19.0
        tip = int(round(xs_hull + 1 + 19.0 * (t ** 1.35)))
        hw = 1 if z >= 28 else 0
        for x in range(xs_hull + 1, tip + 1):
            for dy in range(-hw, hw + 1):
                c = WALE if (z < 27 or abs(dy) > 0) else OAK
                if z >= 31 and x >= tip - 2:
                    c = GOLD
                put_b(x, YC + dy, z, c)

    # 雕首捲像 figurehead（立於木喙尖前 x=284..290, z=29..35 —— 低於 z=36 讓斜桅通過）
    fig_pts = [
        (285, 0, 33, GOLD), (286, 0, 33, GOLD), (287, 0, 34, GOLD), (288, 0, 34, GOLD),
        (288, 0, 35, GOLD), (287, 0, 35, GOLD), (286, 0, 34, RED),  (285, 0, 32, GOLD),
        (287, 0, 32, GOLD), (288, 0, 33, GOLD), (289, 0, 34, GOLD), (289, 0, 35, GOLD),
    ]
    for fx, fdy, fz, fc in fig_pts:
        for dy in (-1, 0, 1) if fdy == 0 and fz in (33, 34) else (fdy,):
            put_b(fx, YC + dy, fz, fc if dy == 0 else GOLD)

    # 雙舷首飾條 rails/cheeks（貼著船殼外側外伸到木喙）
    for sgn in (-1, 1):
        for i in range(28):
            t = i / 27.0
            x = int(round(256 + 29 * t))
            z = int(round(32 - 4 * math.sin(math.pi * t) + 1 * t))
            # 找船殼在該 (x, z) 最外緣 + 1
            if 0 <= x - x0 < nx:
                ys = np.nonzero(S[x - x0, :, z])[0]
                yo = int((ys.max() + ylo + 1) if sgn > 0 else (ys.min() + ylo - 1)) if len(ys) else (YC + sgn * 2)
            else:
                yo = YC + sgn * 2
            y_target = int(round(yo * (1 - t ** 2) + (YC + sgn * 2) * (t ** 2)))
            put_b(x, y_target, z, GOLD if i % 4 == 0 else WALE)
            put_b(x, y_target, z - 1, OAK)

    # ── 3. deco-gallery（船尾小型雙側陽台與欄杆 z=25..30, x=84..87，高於舵葉 z<=25 + 兩側假艉廊 bouteilles）──
    gal_dict = {}
    def put_g(x, y, z, c):
        if 0 <= x - x0 < nx and 0 <= y - ylo < ny and 0 <= z < nz and S[x - x0, y - ylo, z]:
            return
        gal_dict[(int(x), int(y), int(z))] = int(c)

    # 船尾窗下窄陽台廊（x=85..87, z=25..26, y=82..110 — 兩側完整護欄，中線 y=95..97 僅鋪走板、不立外凸柱以免頂到後舵柄）
    for y in range(83, 110):
        for x in range(85, 88):
            put_g(x, y, 25, WALE if x == 85 else RED)
        if y in (83, 84, 88, 92, 100, 104, 108, 109):
            put_g(85, y, 26, GOLD)
            put_g(85, y, 27, GOLD)
        if y <= 92 or y >= 100:
            put_g(85, y, 28, WALE if y % 2 else GOLD)

    # 雙側假艉廊（fausses bouteilles：貼著船尾兩舷外板 x=88..96, z=27..38）
    for sgn in (-1, 1):
        for x in range(88, 96):
            xi = x - x0
            for z in range(27, 39):
                ys = np.nonzero(S[xi, :, z])[0]
                if not len(ys):
                    continue
                y_out = int((ys.max() + ylo + 1) if sgn > 0 else (ys.min() + ylo - 1))
                c = GOLD if z in (27, 38) or x in (88, 95) else (GLASS if (x in (90, 91, 93, 94) and 30 <= z <= 35) else RED)
                put_g(x, y_out, z, c)
                if z in (28, 37) and 89 <= x <= 94:
                    put_g(x, y_out + sgn, z, GOLD if z == 37 else WALE)

    # ── 4. deco-nameplate（上艉鏡花冠裝飾＋船名 LUCIA：在船尾觀看為左 -y 到右 +y）──
    name_dict = {}
    def put_n(x, y, z, c):
        if 0 <= x - x0 < nx and 0 <= y - ylo < ny and 0 <= z < nz and S[x - x0, y - ylo, z]:
            return
        name_dict[(int(x), int(y), int(z))] = int(c)

    # 船名牌框（x=86 貼在 x=87 上艉牆外，z=33..41，上下各留 1 格深底讓 z=35..39 的金字不粘框邊；y=84..108）
    for y in range(84, 109):
        for z in range(33, 42):
            c = GOLD if (z in (33, 41) or y in (84, 108)) else WALE
            put_n(86, y, z, c)
    # 花冠拱頂（z=42..43 中線裝飾徽）
    for y in range(91, 102):
        h_arc = 43 if abs(y - YC) <= 2 else 42
        for z in range(42, h_arc + 1):
            put_n(86, y, z, GOLD)
    # "LUCIA" 5 個字自 y_start = YC - 8 (=88) 往 +Y 排開（I 只佔 1 寬以免寬度擁擠），在 x=85 浮雕
    FONT_NARROW = dict(FONT3X5)
    FONT_NARROW['I'] = ['1', '1', '1', '1', '1']
    y_cursor = YC - 8
    for ch in 'LUCIA':
        bmp = FONT_NARROW[ch]
        for row_i, row_str in enumerate(bmp):
            zz = 39 - row_i
            for col_i, bit in enumerate(row_str):
                if bit == '1':
                    put_n(85, y_cursor + col_i, zz, GOLD)
        y_cursor += len(bmp[0]) + 1

    # 寫出局部或世界座標（世界座標 0..359,0..191,0..319，子作品照船框建，模型 pivot=bounds 方便轉移與對齊）
    out = os.path.join(design, 'masks', 'deco')
    os.makedirs(out, exist_ok=True)
    parts = {
        'stern_glass': glass_cells,
        'beak': [(x, y, z, c) for (x, y, z), c in sorted(beak_dict.items())],
        'gallery': [(x, y, z, c) for (x, y, z), c in sorted(gal_dict.items())],
        'nameplate': [(x, y, z, c) for (x, y, z), c in sorted(name_dict.items())],
    }

    spec = {'parts': {}}
    for nm, lst in parts.items():
        p = os.path.join(out, nm + '.vox.txt')
        # 轉成局部最小包圍盒，好讓外部模型框緊實、pivot 精準放在 min 角
        xs = [t[0] for t in lst]
        ys = [t[1] for t in lst]
        zs = [t[2] for t in lst]
        mn = (min(xs), min(ys), min(zs))
        mx = (max(xs), max(ys), max(zs))
        with open(p, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('# 塔爾塔納 deco %s（局部框，at=%d,%d,%d）\n' % (nm, mn[0], mn[1], mn[2]))
            for x, y, z, c in lst:
                if nm == 'stern_glass':
                    fh.write('%d,%d,%d,%d\n' % (x, y, z, c))
                else:
                    fh.write('%d,%d,%d,%d\n' % (x - mn[0], y - mn[1], z - mn[2], c))
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        size_xyz = [mx[0] - mn[0] + 1, mx[1] - mn[1] + 1, mx[2] - mn[2] + 1]
        # 對稱檢驗（相對 YC）
        mir_err = 0
        if nm in ('beak', 'gallery', 'stern_glass'):
            s_set = {(x, y, z): c for x, y, z, c in lst}
            for (x, y, z), c in s_set.items():
                if s_set.get((x, 2 * YC - y, z)) != c:
                    mir_err += 1
        spec['parts'][nm] = {
            'cells': len(lst), 'at': list(mn), 'max': list(mx), 'box': size_xyz,
            'deco': (nm != 'stern_glass'), 'mirror_diff': mir_err, 'sha256': h,
        }

    with open(os.path.join(design, 'deco_spec.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=1)

    # 圖紙：船首放大、船尾背面放大（含文字可讀性核對）
    im = Image.new('RGB', (1040, 440), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((24, 14), 'Tartane sheet 05 deco: beak & figurehead (right), stern nameplate LUCIA + gallery + glass (left)', fill=(0, 0, 0), font=font(14))
    sc = 8
    # 左圖：船首（x 250..294, z 12..44）
    all_b = beak_dict
    for x in range(250, 294):
        for z in range(12, 44):
            c = None
            if 0 <= x - x0 < nx and S[x - x0, :, z].any():
                ys = np.nonzero(wall[x - x0, :, z])[0]
                if len(ys):
                    c = int(col[x - x0, ys[-1], z])
            # overlay max-y beak cell
            bcs = [all_b[(x, y, z)] for (bx, y, bz) in all_b if bx == x and bz == z]
            if bcs:
                c = bcs[-1]
            if c:
                X0, Z0 = 30 + (x - 250) * sc, 60 + (44 - z) * sc
                d.rectangle([X0, Z0, X0 + sc, Z0 + sc], fill=palette_rgb(c))
    # 標出 bowsprit 預定線（x 248, z 33 @ 15°）確認無碰撞
    d.line([30 + (248 - 250) * sc, 60 + (44 - 33) * sc, 30 + (294 - 250) * sc, 60 + (44 - (33 + 46 * math.tan(math.radians(15)))) * sc], fill=(0, 140, 220), width=3)

    # 右圖：船尾正面看過去（從 x 小往 +x 看：左邊是 -y、右邊是 +y）
    comb = {}
    for x, y, z, c in glass_cells + list((k[0], k[1], k[2], v) for k, v in gal_dict.items()) + list((k[0], k[1], k[2], v) for k, v in name_dict.items()):
        if (y, z) not in comb or x < comb[(y, z)][0]:
            comb[(y, z)] = (x, c)
    for y in range(72, 121):
        for z in range(15, 45):
            c = None
            yi = y - ylo
            if 0 <= yi < ny:
                xs = np.nonzero(wall[:, yi, z])[0]
                if len(xs):
                    c = int(col[xs[0], yi, z])
            if (y, z) in comb:
                c = comb[(y, z)][1]
            if c:
                X0, Z0 = 480 + (y - 72) * sc, 60 + (44 - z) * sc
                d.rectangle([X0, Z0, X0 + sc, Z0 + sc], fill=palette_rgb(c))

    im.save(os.path.join(design, 'sheet05_deco_v1.png'), optimize=False)
    print(json.dumps(spec, ensure_ascii=False))


if __name__ == '__main__':
    main()
