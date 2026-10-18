# 蘇士奎哈納號（crest-001，TASK-0697）階段五：明輪罩（右舷一件；左舷用 mirror=y 關聯）＋兩具明輪（遊戲的 kind=propeller 外部模型，各一件、平移放）
#   crest-001 自己寫的（光榮號沒有明輪）。只讀 plan.json（paddles）與船殼（mio.stage_base ＝ 作品，前幾階段結果帳證過）。
#   輸出：masks/paddles/box_S.vox.txt（明輪罩子作品，整船的框、世界座標）、masks/paddles/wheel_S.vox.txt／wheel_P.vox.txt（明輪子作品，整船的框）、
#         verify_paddles.json、sheet05_paddles_v1.png
#   用法：python -I -X utf8 draft_paddles.py <design> [--probe dx=<n>]（反向對照：輪子往 x 推 n 格，跟箱子／船殼的碰撞要報出來；⛔ 不寫檔）
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import mio
from draft_lines import font, palette_rgb


def wheel_cells(Pd, side, dx=0):
    """一具明輪：右舷 side=+1（y 在 YC＋y_in … YC＋y_out）、左舷 −1（鏡像 y ↔ 2·YC − y）。回 {(x, y, z): 色}。"""
    YC = 200
    cx, cz, R = Pd['x'] + dx, Pd['z'], Pd['R']
    n, fd, ft = Pd['n'], Pd['float_depth'], Pd['float_t']
    C = Pd['colors']
    out = {}
    rr = int(math.ceil(R)) + 1
    for x in range(cx - rr, cx + rr + 1):
        for z in range(cz - rr, cz + rr + 1):
            r = math.hypot(x - cx, z - cz)
            if r > R:
                continue
            a = math.degrees(math.atan2(z - cz, x - cx)) % 360.0
            k = a / (360.0 / n)
            da = abs(k - round(k)) * (360.0 / n)                     # 離最近那一片槳板中心線的角度
            dperp = r * math.sin(math.radians(da))                   # 離那條徑向線的距離（格）
            rim = r >= R - Pd['rim_t']
            spoke = dperp <= Pd['spoke_t'] * 0.5 + 0.35 and r >= Pd['hub_r']
            hub = r <= Pd['hub_r']
            flt = dperp <= ft * 0.5 + 0.05 and r >= R - fd
            for dy in range(Pd['y_in'], Pd['y_out'] + 1):
                face = dy in (Pd['y_in'], Pd['y_in'] + 1, Pd['y_out'] - 1, Pd['y_out'])
                c = 0
                if flt:
                    c = C['float']
                elif face and (rim or spoke):
                    c = C['frame']
                elif hub and (face or r <= Pd['axle_r']):
                    c = C['hub']
                elif r <= Pd['axle_r']:
                    c = C['hub']
                if c:
                    out[(x, YC + side * dy, z)] = c
    # 軸：從船殼邊（|dy| 68 起）接到內輪緣（r ≤ axle_r）—— 掛點 shaft-fwd 在 |dy| 69
    for dy in range(69, Pd['y_in']):
        for x in range(cx - 3, cx + 4):
            for z in range(cz - 3, cz + 4):
                if math.hypot(x - cx, z - cz) <= Pd['axle_r']:
                    out[(x, YC + side * dy, z)] = C['hub']
    return out


def box_cells(Pd, hull, L):
    """右舷的明輪罩＋前後側台（只放船殼沒有的格）。回 {(x, y, z): 色}。"""
    YC = 200
    B, Sp = Pd['box'], Pd['sponson']
    cx, cz, ri, t = Pd['x'], Pd['z'], B['r_in'], B['t']
    ro = ri + t
    out = {}
    def put(x, y, z, c):
        if (x, y, z) not in hull:
            out[(x, y, z)] = c
    y0w, y1w = B['y_wall']
    xs = range(cx - ro - 1, cx + ro + 2)
    # 弧頂（z ≥ 軸心）＋前後直牆（軸心以下到 z_bot）：從舷牆外面（或舷牆頂以上 |dy| ≥ y_inner）到外牆
    for x in xs:
        for z in range(B['z_bot'], cz + ro + 2):
            r = math.hypot(x - cx, z - cz)
            shell = (ri <= r < ro + 0.5) if z >= cz else (ri <= abs(x - cx) < ro + 0.5)
            if not shell:
                continue
            trim = (z >= cz and r >= ro - 0.5) or (z < cz and abs(x - cx) >= ro - 0.5)
            for dy in range(B['y_inner'], y1w + 1):
                put(x, YC + dy, z, B['trim'] if (trim and dy >= y1w - 1) else B['roof'])
    # 外牆：|dy| y0w..y1w、z_bot 到弧頂、x 在箱子裡（r < ri 那一片 ＋ 軸心以下 |x − cx| < ri）
    for x in xs:
        for z in range(B['z_bot'], cz + ri + 1):
            inside = (math.hypot(x - cx, z - cz) < ri) if z >= cz else (abs(x - cx) < ri)
            if not inside:
                continue
            a = math.degrees(math.atan2(z - cz, x - cx))
            r = math.hypot(x - cx, z - cz)
            F = B['fan']
            slot = False
            if z > cz and F['r'][0] <= r <= F['r'][1] and F['deg'][0] <= a <= F['deg'][1]:
                step = (F['deg'][1] - F['deg'][0]) / (F['n'] - 1)
                k = round((a - F['deg'][0]) / step)
                if abs(r * math.sin(math.radians(a - (F['deg'][0] + k * step)))) <= F['w'] * 0.5:
                    slot = True
            Lv = B['louvres']
            if z < cz and abs(x - cx) <= Lv['x_half'] and any(z0 <= z < z0 + Lv['h'] for z0 in Lv['z']):
                slot = True
            boss = B['boss_r'][0] <= r <= B['boss_r'][1]
            for dy in range(y0w, y1w + 1):
                if slot and dy >= y0w:
                    continue                                          # 槽：整片牆厚都開（看得到裡面的輪子）
                c = B['trim'] if boss and dy == y1w else B['color']
                put(x, YC + dy, z, c)
    # 箱子內側在舷牆頂以上的那一面牆（|dy| y_inner .. y_inner+1、z 從舷牆頂到弧頂）
    top = int(round(L.top_z(cx)))
    for x in xs:
        for z in range(top - 1, cz + ri + 1):
            if (math.hypot(x - cx, z - cz) < ri) if z >= cz else (abs(x - cx) < ri):
                for dy in (B['y_inner'], B['y_inner'] + 1):
                    put(x, YC + dy, z, B['roof'])
    # 側台：箱子前後各 taper 格，外緣從 y1w 線性收回船殼；甲板面 z_top、t 格厚；外緣矮欄；底下斜撐
    zt, tt = Sp['z_top'], Sp['t']
    for sgn in (-1, 1):
        x_box = cx + sgn * (ro + 1)
        for k in range(0, Sp['taper'] + 1):
            x = x_box + sgn * k
            hb = float(L.hb(np.array([x + 0.5]), np.array([zt + 0.5]))[0])
            edge = int(round(y1w - (y1w - hb) * (k / float(Sp['taper']))))
            for dy in range(int(hb) - 1, edge + 1):
                for z in range(zt - tt + 1, zt + 1):
                    put(x, YC + dy, z, Sp['edge'] if (dy >= edge - 1 or z < zt) else Sp['deck'])
                if dy >= edge - 1:
                    for z in range(zt + 1, zt + 1 + Sp['rail_h']):
                        put(x, YC + dy, z, Sp['edge'])
            if k % Sp['knee_every'] == 0 and edge - hb > 8:
                # 斜撐：從側台外緣下面斜到船殼（z knee_z）；2 格寬的帶子
                y_a, z_a = edge - 2, zt - tt
                y_b, z_b = hb - 1, Sp['knee_z']
                for s in np.linspace(0, 1, 60):
                    yy, zz = y_a + (y_b - y_a) * s, z_a + (z_b - z_a) * s
                    for ddy in (0, 1):
                        put(x, YC + int(round(yy)) - ddy, int(round(zz)), Sp['edge'])
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    dx = int(probe[0].split('=')[1]) if probe else 0
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    Pd = plan['paddles']
    G, H = mio.stage_base(design, subs=('decks', 'ladders'))
    hull = set(map(tuple, H[:, :3].tolist()))
    decks = set(map(tuple, np.argwhere(G > 0).tolist())) - hull
    box = box_cells(Pd, hull | decks, L)
    wS = wheel_cells(Pd, 1, dx)
    wP = wheel_cells(Pd, -1, dx)
    occ = hull | decks | set(box)
    # 箱子的左舷（鏡像）也要算碰撞：鏡像 y ↔ 400 − y
    boxP = {(x, 400 - y, z) for (x, y, z) in box}
    R = {'box_cells': len(box), 'wheel_cells': [len(wS), len(wP)],
         'wheel_hits_S': len(set(wS) & (hull | decks | set(box))), 'wheel_hits_P': len(set(wP) & (hull | decks | boxP)),
         'box_hits_hull_decks': len(set(box) & (hull | decks)), 'box_mirror_vs_hull': len(boxP & (hull | decks)),
         'wheel_mirror_diff': len({(x, 400 - y, z) for (x, y, z) in wS} ^ set(wP)),
         'colors_box': {int(c): int(n) for c, n in zip(*np.unique(list(box.values()), return_counts=True))},
         'colors_wheel': {int(c): int(n) for c, n in zip(*np.unique(list(wS.values()), return_counts=True))}}
    # 輪子轉一整圈會不會掃到箱子／船殼：每格繞軸轉 0..360（每 2°）看落點
    cx, cz = Pd['x'] + dx, Pd['z']
    sweep = 0
    occS = hull | decks | set(box)
    pts = np.array(list(wS.keys()), float)
    for deg in range(0, 360, 2):
        a = math.radians(deg)
        x = cx + (pts[:, 0] - cx) * math.cos(a) - (pts[:, 2] - cz) * math.sin(a)
        z = cz + (pts[:, 0] - cx) * math.sin(a) + (pts[:, 2] - cz) * math.cos(a)
        keys = set(zip(np.round(x).astype(int).tolist(), pts[:, 1].astype(int).tolist(), np.round(z).astype(int).tolist()))
        sweep = max(sweep, len(keys & occS))
    R['wheel_sweep_hits_max'] = sweep
    wl = plan['waterline']['z']
    R['wheel_bottom_z'] = min(z for (_, _, z) in wS)
    R['wheel_top_z'] = max(z for (_, _, z) in wS)
    R['immersion_cells'] = wl - R['wheel_bottom_z']
    R['box_extent'] = {'x': [min(k[0] for k in box), max(k[0] for k in box)], 'y': [min(k[1] for k in box), max(k[1] for k in box)], 'z': [min(k[2] for k in box), max(k[2] for k in box)]}
    yc_w = 200 + (Pd['y_in'] + Pd['y_out']) // 2
    R['anchors'] = {'S': {'hub': [Pd['x'], yc_w, Pd['z']], 'shaft-fwd': [Pd['x'], 200 + 69, Pd['z']]},
                    'P': {'hub': [Pd['x'], 400 - yc_w, Pd['z']], 'shaft-fwd': [Pd['x'], 400 - 269, Pd['z']]}}
    if probe:
        print(json.dumps({'probe': probe[0], 'wheel_hits_S': R['wheel_hits_S'], 'wheel_sweep_hits_max': sweep}, ensure_ascii=False))
        return
    od = os.path.join(design, 'masks', 'paddles')
    os.makedirs(od, exist_ok=True)
    def dump(name, cells, head):
        p = os.path.join(od, name)
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for k in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], cells[k]))
        return [len(cells), hashlib.sha256(open(p, 'rb').read()).hexdigest()]
    R['lists'] = {'box_S': dump('box_S.vox.txt', box, '# 蘇士奎哈納號 明輪罩（右舷；draft_paddles.py）世界座標、at 0,0,0；左舷 ＝ mirror=y、at 0,1,0\n'),
                  'wheel_S': dump('wheel_S.vox.txt', wS, '# 蘇士奎哈納號 明輪（右舷；draft_paddles.py）世界座標、at 0,0,0\n'),
                  'wheel_P': dump('wheel_P.vox.txt', wP, '# 蘇士奎哈納號 明輪（左舷；draft_paddles.py）世界座標、at 0,0,0\n')}
    # 圖：右舷側面（船殼＋箱子＋輪子，輪子在箱子後面用淡色）與 x = 軸心的橫剖面
    nx0, nx1, nz = Pd['x'] - 130, Pd['x'] + 130, 160
    sc = 3
    im = Image.new('RGB', ((nx1 - nx0) * sc + 120 + 140 * sc, nz * sc + 120), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((20, 10), '蘇士奎哈納號 新圖紙 05：明輪罩與明輪　v1（左：右舷側面；右：軸心橫剖面 x %d）' % Pd['x'], fill=(0, 0, 0), font=font(18))
    oy = 50
    front = {}
    for (x, y, z), c in list(wS.items()):
        front[(x, z)] = (y, tuple(int(v * 0.55 + 110) for v in palette_rgb(c)))
    for src in (H.tolist(), [(k[0], k[1], k[2], c) for k, c in box.items()]):
        for x, y, z, c in src:
            if nx0 <= x < nx1 and z < nz and y > 200 and (front.get((x, z), (-1,))[0] < y):
                front[(x, z)] = (y, palette_rgb(c))
    for (x, z), (_, c) in front.items():
        if nx0 <= x < nx1 and 0 <= z < nz:
            d.rectangle([20 + (x - nx0) * sc, oy + (nz - 1 - z) * sc, 20 + (x - nx0 + 1) * sc - 1, oy + (nz - z) * sc - 1], fill=c)
    yw = 20 + (nx1 - nx0) * sc + 60
    sec = {}
    for src in (H.tolist(), [(k[0], k[1], k[2], c) for k, c in box.items()], [(k[0], k[1], k[2], c) for k, c in wS.items()],
                [(k[0], k[1], k[2], c) for k, c in wP.items()], [(x, 400 - y, z, c) for (x, y, z), c in box.items()]):
        for x, y, z, c in src:
            if x == Pd['x'] and z < nz:
                sec[(y, z)] = palette_rgb(c)
    for (y, z), c in sec.items():
        if 60 <= y < 340:
            d.rectangle([yw + (y - 60) // 2 * sc, oy + (nz - 1 - z) * sc, yw + ((y - 60) // 2 + 1) * sc - 1, oy + (nz - z) * sc - 1], fill=c)
    wly = oy + (nz - 1 - wl) * sc
    d.line([20, wly, im.size[0] - 20, wly], fill=(0, 90, 200))
    d.text((20, oy + nz * sc + 8), '輪 %d／%d 格、箱 %d 格；輪碰船殼／箱 %d、轉一圈掃到 %d；吃水 %d 格（史料 16）；鏡像差 %d' % (
        len(wS), len(wP), len(box), R['wheel_hits_S'], sweep, R['immersion_cells'], R['wheel_mirror_diff']), fill=(0, 0, 0), font=font(14))
    im.save(os.path.join(design, 'sheet05_paddles_v1.png'))
    with open(os.path.join(design, 'verify_paddles.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
