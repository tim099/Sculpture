# 定遠號的零件產生程式 —— 砲（通用部件）、砲塔殼（牆／轉盤與頂兩件）、信號桁、舵輪、魚雷艇、黃龍旗貼圖。每件一個清單（x,y,z,color）＋固定點 JSON。
# 用法：python -I -X utf8 -B gen_parts.py <輸出資料夾>
# 砲照造船規格 §4.1：x 橫向（砲軸在 x 中線）、y ＝ 砲口方向、z 0 ＝ 站的那一面；比例 0.05 m（模型 scale 0.5）、37 mm 砲 0.02 m（scale 0.2）。
# 數字的出處在 plan.json 的 parts_provenance。
import sys, os, json, math
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
C = PLAN['params']['colors']
GUN_BLACK, GUN_IRON, BRASS = 36, 73, 180


def grid(nx, ny, nz):
    return (np.arange(nx, dtype=np.float32)[:, None, None], np.arange(ny, dtype=np.float32)[None, :, None], np.arange(nz, dtype=np.float32)[None, None, :])


class Part:
    def __init__(self, shape):
        self.col = np.zeros(shape, np.uint8)

    def put(self, mask, color):
        m = mask & (self.col == 0)
        self.col[m] = color if np.isscalar(color) else np.broadcast_to(color, m.shape)[m]

    def write(self, fn, title):
        idx = np.argwhere(self.col > 0); cs = self.col[self.col > 0]
        with open(fn, 'w', newline='\n') as f:
            f.write('# %s —— x,y,z,color（框 %d×%d×%d）\n' % ((title,) + self.col.shape))
            f.write('\n'.join('%d,%d,%d,%d' % (a, b, c, k) for (a, b, c), k in zip(idx.tolist(), cs.tolist())) + '\n')
        return len(idx)


def barrel(X, Y, Z, ax, az, y_b, L, prof, bore, bore_depth):
    """沿 +y 的砲管：剖面半徑照 prof（t 0 ＝ 砲尾面、1 ＝ 砲口）內插；內膛從砲口往裡挖 bore_depth 格。"""
    t = (Y - y_b) / (L - 1)
    rad = np.interp(t, [p[0] for p in prof], [p[1] for p in prof], left=-1, right=-1)
    dr = np.hypot(X - ax, Z - az)
    body = (t >= 0) & (t <= 1) & (dr <= rad)
    hole = (dr <= bore) & (Y >= y_b + L - 1 - bore_depth)
    return body & ~hole


def krupp(spec):
    """克虜伯後膛砲＋滑架（砲耳在兩片側板上、下面兩條滑軌、兩支液壓駐退筒、後面一根橫樑）。"""
    nx, ny, nz = spec['frame']; ax, az = spec['axis']; y_b, L = spec['breech_y'], spec['len']
    X, Y, Z = grid(nx, ny, nz)
    p = Part((nx, ny, nz))
    gun = barrel(X, Y, Z, ax, az, y_b, L, spec['profile'], spec['bore'], 12)
    ty = int(round(y_b + spec['trunnion_t'] * (L - 1)))
    rmax = max(r for _, r in spec['profile'])
    ring = gun & (np.abs(Y - (y_b + 1)) <= 0.5)                                                         # 砲尾一圈黃銅（看得出砲尾）
    wedge = (X >= ax + spec['wedge'][0]) & (X <= ax + spec['wedge'][1]) & (Y >= y_b + 1) & (Y <= y_b + spec['wedge'][2]) & (np.abs(Z - az) <= spec['wedge'][3])   # 橫楔式閂塊（往右滑出）
    handle = (np.hypot(X - (ax + spec['wedge'][1] + 1), Z - az) <= 1.5) & (np.abs(Y - (y_b + spec['wedge'][2] // 2)) <= 1.5)
    trun = (np.abs(Y - ty) <= spec['trunnion_r']) & (np.hypot(Y - ty, Z - az) <= spec['trunnion_r']) & (np.abs(X - ax) <= spec['cheek'][1] + 1)
    cw0, cw1 = spec['cheek']
    hgt = np.clip(az - np.abs(Y - ty) * 0.45, spec['cheek_min'], az)
    cheek = (np.abs(X - ax) >= cw0) & (np.abs(X - ax) <= cw1) & (np.abs(Y - ty) <= spec['cheek_len']) & (Z <= hgt)
    sl0, sl1 = spec['slide']
    slide = (np.abs(X - ax) >= sl0) & (np.abs(X - ax) <= sl1) & (Z <= 2) & (Y >= spec['slide_y'][0]) & (Y <= spec['slide_y'][1])
    tie = (np.abs(X - ax) <= sl1) & (Z <= 2) & (np.isin(Y.astype(int), spec['slide_ties']))
    trans = (np.abs(X - ax) <= cw1) & (np.abs(Y - (ty - spec['cheek_len'] + 2)) <= 2) & (Z >= 3) & (Z <= spec['cheek_min'] + 2)
    rec = np.zeros(gun.shape, bool)
    for sx in (-1, 1):
        rec |= (np.hypot(X - (ax + sx * spec['recoil'][0]), Z - spec['recoil'][1]) <= spec['recoil'][2]) & (Y >= ty - spec['cheek_len']) & (Y <= ty + spec['cheek_len'] - 4)
    p.put(ring, BRASS)
    p.put(gun | wedge, GUN_BLACK)
    p.put(handle, BRASS)
    p.put(trun, GUN_BLACK)
    p.put(cheek | slide | tie | trans | rec, GUN_IRON)
    muz = [ax, y_b + L - 1, az]
    assert p.col[tuple(muz)] == 0, '砲口那一格要空（內膛）'
    anc = {'muzzle': muz, 'breech': [ax, y_b, az], 'trunnion': [ax, ty, az]}
    return p, anc


def hotchkiss(spec):
    """哈乞開斯 37 mm 五管轉膛砲（revolving cannon）＋立柱座：五根管繞中軸、前後兩片圈板、機匣、右側搖把、頂上進彈槽、肩托。"""
    nx, ny, nz = spec['frame']; ax, az = spec['axis']
    X, Y, Z = grid(nx, ny, nz)
    p = Part((nx, ny, nz))
    y0, y1 = spec['barrels_y']; rc, rb = spec['cluster_r'], spec['barrel_r']
    bar = np.zeros(X.shape[:1] + Y.shape[1:2] + Z.shape[2:], bool)
    for k in range(5):
        a = 2 * math.pi * k / 5 + math.pi / 2
        bx, bz = ax + rc * math.cos(a), az + rc * math.sin(a)
        d = np.hypot(X - bx, Z - bz)
        bar |= (d <= rb) & (Y >= y0) & (Y <= y1) & ~((d <= rb - 1.0) & (Y >= y1 - 6))
    rr = np.hypot(X - ax, Z - az)
    plates = (rr <= rc + rb + 1) & (rr > 1.5) & ((np.abs(Y - (y0 + 1)) <= 0.5) | (np.abs(Y - (y1 - 4)) <= 0.5))
    cy0, cy1 = spec['casing_y']; cw = spec['casing_w']
    casing = (np.abs(X - ax) <= cw) & (Y >= cy0) & (Y <= cy1) & (np.abs(Z - az) <= cw)
    crank = (np.abs(X - (ax + cw + 1.5)) <= 0.5) & (np.hypot(Y - (cy0 + cy1) / 2, Z - az) <= cw - 1) & (np.hypot(Y - (cy0 + cy1) / 2, Z - az) > cw - 3)
    crank |= (np.abs(X - (ax + cw + 3)) <= 1) & (np.abs(Y - ((cy0 + cy1) / 2 + cw - 2)) <= 1) & (np.abs(Z - az) <= 1)
    hopper = (np.abs(X - ax) <= 3) & (Y >= cy0 + 6) & (Y <= cy0 + 16) & (Z > az + cw) & (Z <= az + cw + 7)
    stock = (np.abs(X - ax) <= 1) & (Y >= cy0 - 14) & (Y < cy0) & (np.abs(Z - (az - 3 - (cy0 - Y) * 0.25)) <= 1.5)
    py = spec['pivot_y']
    ped = (np.hypot(X - ax, Y - py) <= 5) & (Z <= az - cw - 8)
    ped |= (np.hypot(X - ax, Y - py) <= 9) & (Z <= 2)
    yoke = (np.abs(np.abs(X - ax) - (cw + 1.5)) <= 0.5) & (np.abs(Y - py) <= 6) & (Z > az - cw - 9) & (Z <= az)
    yoke |= (np.abs(X - ax) <= cw + 2) & (np.abs(Y - py) <= 6) & (np.abs(Z - (az - cw - 8)) <= 0.5)
    p.put(plates | crank, BRASS)
    p.put(bar | casing | hopper | stock, GUN_BLACK)
    p.put(ped | yoke, GUN_IRON)
    muz = [ax, y1, az]
    assert p.col[tuple(muz)] == 0
    return p, {'muzzle': muz, 'breech': [ax, cy0, az], 'pivot': [ax, py, 0]}


def turret_main(T):
    """主砲塔殼（0.1 m、框 N×N×NZ、轉軸在 (CX, CX)）：轉盤（中間留洞）＋砲罩（圓筒、平頂、前面兩個砲門）。
    回兩件（同一個框）：牆（2 格厚 ⇒ 平滑＋金屬反光）、轉盤與頂（1 格厚 ⇒ 方塊；平滑會把薄板兩面平均掉，造船規格 §9.5）。"""
    N = 2 * T['r_table'] + 1; CX = T['r_table']; NZ = T['hood_top'] - T['z_table'] + 1 + T['dome']
    X, Y, Z = grid(N, N, NZ)
    r = np.hypot(X - CX, Y - CX)
    p = Part((N, N, NZ)); q = Part((N, N, NZ))
    table = (r > T['r_hole'] + 0.5) & (r <= T['r_table'] + 0.5) & (Z == 0)
    ri, ro = T['r_hood']
    zt = T['hood_top'] - T['z_table']
    wall = (r > ri - 0.5) & (r <= ro + 0.5) & (Z >= 1) & (Z <= zt)
    gz = T['gun_axis'] - T['z_table']
    pw, ph = T['port']
    ports = np.zeros(wall.shape, bool)
    for sx in (-1, 1):
        ports |= (Y > CX) & (np.abs(X - (CX + sx * T['gun_dx'])) <= pw) & (np.abs(Z - gz) <= ph)
    roof = (r <= ro + 0.5) & (Z == zt + 1)
    crown = np.zeros(wall.shape, bool)
    for k in range(1, T['dome']):
        crown |= (r <= ro - 4 * k + 0.5) & (Z == zt + 1 + k)
    hatch = (np.abs(X - CX) <= 3) & (np.abs(Y - (CX - 22)) <= 4)                                         # 頂上一個艙口蓋（後半）
    q.put(table, C['iron'])
    p.put(wall & ~ports, C['white'])
    q.put((roof | crown) & ~(hatch & (Z > zt + 1)), C['grey'])
    q.put(hatch & (Z == zt + 2), C['iron'])
    return p, q, {'pivot': [CX, CX, 0], 'front': [CX, N - 1, 0]}, dict(N=N, CX=CX, NZ=NZ)


def turret_15(T):
    """15 cm 砲塔殼（0.1 m）：圓筒＋平頂、前面一個砲門；罩在甲板上（沒有地板）。回兩件：牆（3 格厚，平滑）、頂（方塊）。"""
    ri, ro = T['r']; N = 2 * ro + 1; CX = ro; NZ = T['h'] + T['dome'] + 1
    X, Y, Z = grid(N, N, NZ)
    r = np.hypot(X - CX, Y - CX)
    p = Part((N, N, NZ)); q = Part((N, N, NZ))
    wall = (r > ri - 0.5) & (r <= ro + 0.5) & (Z <= T['h'] - 1)
    gz = T['gun_axis'] - T['z0']
    pw, ph = T['port']
    port = (Y > CX) & (np.abs(X - CX) <= pw) & (np.abs(Z - gz) <= ph)
    roof = (r <= ro + 0.5) & (Z == T['h'])
    crown = np.zeros(wall.shape, bool)
    for k in range(1, T['dome'] + 1):
        crown |= (r <= ro - 5 * k + 0.5) & (Z == T['h'] + k)
    p.put(wall & ~port, C['white'])
    q.put(roof | crown, C['grey'])
    return p, q, {'pivot': [CX, CX, 0], 'front': [CX, N - 1, 0]}, dict(N=N, CX=CX, NZ=NZ)


def signal_yard(half):
    """信號桁（0.1 m、沿 y、沒轉）：一格粗的桿＋中間 3×7×3 的吊箍（sling）。轉軸 ＝ 中心那一格（造船規格 §5）。"""
    nx, ny, nz = 3, 2 * half + 1, 3
    X, Y, Z = grid(nx, ny, nz)
    p = Part((nx, ny, nz))
    bar = (X == 1) & (Z == 1)
    sling = np.abs(Y - half) <= 3
    p.put(bar | sling, C['buff'])
    return p, {'pivot': [1, half, 1], 'arm-P': [1, 0, 1], 'arm-S': [1, ny - 1, 1], 'sling': [1, half, 2]}


def helm_wheel():
    """海圖室的舵輪（0.02 m，模型 scale 0.2）：單輪、8 根輪輻伸出輪緣當把手、黃銅輪轂、往前一截輪軸插進鐵立柱（立柱是海圖室的格）。
    軸沿 +x（往船頭）：spin-a 輪轂中心 → spin-b 軸前端（26_spin.js：正轉 ＝ 輪頂往左舷）。蒸汽船的舵輪（立柱裡是齒輪、接蒸汽操舵機），不用憲法號的雙輪。"""
    nx, ny, nz = 16, 91, 91; yc = zc = 45
    X, Y, Z = grid(nx, ny, nz)
    p = Part((nx, ny, nz))
    r = np.hypot(Y - yc, Z - zc)
    rim = (r > 32) & (r <= 35.5) & (X >= 1) & (X <= 4)
    spoke = np.zeros((nx, ny, nz), bool); handle = np.zeros((nx, ny, nz), bool)
    for k in range(8):
        t = k * math.pi / 4
        d = np.abs(-(Y - yc) * math.sin(t) + (Z - zc) * math.cos(t))       # 到這根輪輻中線的距離
        along = (Y - yc) * math.cos(t) + (Z - zc) * math.sin(t)
        spoke |= (d <= 1.2) & (along >= 4) & (along <= 35.5) & (X >= 2) & (X <= 3)
        handle |= (d <= 1.6) & (along > 35.5) & (along <= 43) & (X >= 2) & (X <= 3)
    hub = (r <= 6) & (X <= 6)
    axle = (r <= 2.5) & (X > 6)
    p.put(hub | axle, BRASS)
    p.put(rim | spoke | handle, C['teak'])
    return p, {'spin-a': [2, yc, zc], 'spin-b': [nx - 1, yc, zc]}


def torpedo_boat(B):
    """二等魚雷艇（0.1 m）：細長、尖艏、圓艉、艏部龜背甲板、小司令塔、一根煙囪、艏部兩個魚雷管口。實心（外部模型的來源）。"""
    L, hb, D = B['len'], B['half'], B['depth']
    nx, ny, nz = L + 2, 2 * hb + 3, D + 18
    yc = hb + 1
    X, Y, Z = grid(nx, ny, nz)
    t = np.clip((X - 1) / (L - 1), 0, 1)
    w = hb * np.minimum(1, ((1 - t) / 0.35)) ** 0.75 * np.minimum(1, t / 0.10) ** 0.45
    zt = 9.0
    sec = np.where(Z < zt, np.sqrt(np.clip(1 - ((zt - Z) / zt) ** 2, 0, 1)), 1.0)
    turtle = np.where(t > 0.62, 3.0 * (1 - (np.abs(Y - yc) / np.maximum(w, 1)) ** 2), 0)
    top = D + turtle
    hull = (np.abs(Y - yc) <= w * sec) & (Z <= top) & (X >= 1) & (X <= L)
    keel = (np.abs(Y - yc) <= 0.5) & (Z <= 1) & (X >= 8) & (X <= L - 10)
    p = Part((nx, ny, nz))
    tubes = (np.hypot(Y - (yc - 3), Z - (D - 4)) <= 1.5) | (np.hypot(Y - (yc + 3), Z - (D - 4)) <= 1.5)
    tubes = tubes & (X >= L - 12) & hull
    p.put(tubes, C['black'])
    hull_c = np.where(Z < 6, C['red'], np.where(Z >= D, C['grey'], C['black']))
    p.put(hull | keel, hull_c)
    cx_, fx_ = int(L * B['conning_t']), int(L * B['funnel_t'])
    ct = (np.hypot(X - cx_, Y - yc) <= 4.5) & (Z > D) & (Z <= D + 8)
    fn = (np.hypot((X - fx_) / 1.0, (Y - yc) / 0.8) <= 3.5) & (np.hypot((X - fx_) / 1.0, (Y - yc) / 0.8) > 2.2) & (Z > D) & (Z <= D + 15)
    house = (X >= int(L * 0.30)) & (X <= int(L * 0.46)) & (np.abs(Y - yc) <= 6) & (Z > D) & (Z <= D + 5)
    vent = (np.hypot(X - int(L * 0.40), Y - (yc + 7)) <= 1.2) & (Z > D) & (Z <= D + 7)
    p.put(fn & (Z > D + 12), C['black'])
    p.put(fn, C['buff'])
    p.put(ct, C['black'])
    p.put(house | vent, C['white'])
    return p, {}


def dragon_flag(fn, w=60, h=40):
    """黃龍旗（1889 年起的長方形 2:3）：黃底、藍龍、左上角紅珠。像素畫，照 sail 的貼圖規則（左上 ＝ 角 0）。"""
    YEL, BLUE, DARK, RED, WHITE = (250, 214, 40), (36, 72, 200), (16, 36, 110), (210, 30, 30), (255, 255, 255)
    im = Image.new('RGBA', (w, h), YEL + (255,)); px = im.load()

    def dot(x, y, c, r=1.0):
        for yy in range(int(y - r - 1), int(y + r + 2)):
            for xx in range(int(x - r - 1), int(x + r + 2)):
                if 0 <= xx < w and 0 <= yy < h and (xx - x) ** 2 + (yy - y) ** 2 <= r * r: px[xx, yy] = c + (255,)
    # 身體：從右下往左上盤一個 S，頭朝左上的紅珠
    pts = []
    for k in range(240):
        s = k / 239
        x = 50 - 34 * s + 6 * math.sin(s * 2.4 * math.pi)
        y = 31 - 14 * s + 7 * math.sin(s * 3.1 * math.pi + 0.6)
        pts.append((x, y, 3.2 - 1.6 * (1 - s) ** 2 if s > 0.15 else 1.0 + 12 * s))
    for x, y, r in pts: dot(x, y, DARK, r + 0.7)
    for x, y, r in pts: dot(x, y, BLUE, r)
    for i in range(0, 240, 9):                                            # 鱗：深藍點
        x, y, r = pts[i]
        if r > 1.6: px[int(x), int(y)] = DARK + (255,)
    hx, hy, _ = pts[-1]
    dot(hx - 2, hy - 1, BLUE, 3.6); dot(hx - 5, hy, BLUE, 2.2)            # 頭、嘴
    px[int(hx - 2), int(hy - 2)] = WHITE + (255,)                          # 眼
    for k in range(6): px[int(hx + 1 + k), int(hy - 4 - k // 2)] = DARK + (255,)   # 角
    for fx, fy in ((pts[70][0], pts[70][1]), (pts[150][0], pts[150][1]), (pts[200][0], pts[200][1])):   # 爪
        for k in range(4): px[int(fx - 1 + k % 2), int(fy + 3 + k // 2)] = DARK + (255,)
    dot(7, 7, RED, 3.3)                                                    # 紅珠
    dot(6, 6, (255, 140, 120), 0.8)
    im.save(fn)


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    PP = PLAN['parts']
    meta = {}
    for key, fnc in (('gun305', krupp), ('gun150', krupp)):
        p, a = fnc(PP[key]); meta[key] = {'count': p.write(os.path.join(out, key + '.txt'), key), 'anchors': a, 'frame': list(p.col.shape)}
    p, a = hotchkiss(PP['gun37']); meta['gun37'] = {'count': p.write(os.path.join(out, 'gun37.txt'), 'gun37'), 'anchors': a, 'frame': list(p.col.shape)}
    for fnc, T, kw, kt in ((turret_main, PLAN['params']['turret_main'], 'turret-main-shell', 'turret-main-top'), (turret_15, PLAN['params']['turret_15'], 'turret15-shell', 'turret15-roof')):
        p, q, a, d = fnc(T)
        meta[kw] = {'count': p.write(os.path.join(out, kw + '.txt'), kw), 'anchors': a, 'frame': list(p.col.shape), 'geom': d}
        meta[kt] = {'count': q.write(os.path.join(out, kt + '.txt'), kt), 'anchors': {}, 'frame': list(q.col.shape), 'geom': d}
    for m in PLAN['params']['masts']:
        k = 'yard-' + m['name']; p, a = signal_yard(m['yard_half'])
        meta[k] = {'count': p.write(os.path.join(out, k + '.txt'), k), 'anchors': a, 'frame': list(p.col.shape)}
    p, a = helm_wheel(); meta['helm'] = {'count': p.write(os.path.join(out, 'helm.txt'), 'helm'), 'anchors': a, 'frame': list(p.col.shape)}
    p, a = torpedo_boat(PP['torpedo_boat']); meta['torpedo-boat'] = {'count': p.write(os.path.join(out, 'torpedo-boat.txt'), 'torpedo-boat'), 'anchors': a, 'frame': list(p.col.shape)}
    dragon_flag(os.path.join(out, 'flag_dragon.png'))
    json.dump(meta, open(os.path.join(out, 'parts_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: (v['count'], v['frame']) for k, v in meta.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
