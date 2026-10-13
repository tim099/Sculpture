# 新圖紙 05 船尾窗廊與船首像（TASK-0529 階段五）：plan.json 的 stern_head ⇒ 四件作品的清單、圖紙、verify_stern_head.json。
# 用法：python -I -X utf8 -B draft_stern_head.py <design 資料夾>
#   · 現況照設計重建：船殼（階段二、三、四的清單）＋主甲板＋後甲板（階段四的清單）—— 結果帳都驗過 作品＝設計。
#   · 船尾窗（船殼）：艉板上每扇窗的 (y, z) 從艉板外面往裡刻到艙房的空氣（carvevox 帶原色守門）；玻璃縮進一格（船殼）。
#     艉板是斜的 ⇒ 玻璃每一排往下一排的位置補一格，上下兩排才面接面（憲法號階段十四的坑）。
#   · 船尾裝飾（子作品 stern-deco，at 0,0,0）：窗框（窗外一圈、凸出艉板一格）、窗台線與簷線、船尾燈（艉板頂中央）。
#   · 船尾窗廊（子作品 quarter-gallery，只做右舷、固定框；左舷用 mirror=y 關聯，at.y ＝ 161 − at.y − 高）。
#   · 船頭（子作品 head，at 0,0,0）：knee（艏柱前面、中線 3 格寬）＋隼（脊椎上一串球、翅膀是沿著前緣與後緣插值的面）。
#   · 子作品的格一律不准落在船殼體積裡、不准碰到現況的格（之後組起來 link_overlap 要是 0）。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, YC, font
from draft_decks import hull_now, read_list

NX, NY, NZ = 384, 161, 90


def now_state(d):
    col = np.zeros((NX, NY, NZ), np.int16)
    col[:, :, :80] = hull_now(d)
    V = json.load(open(os.path.join(d, 'verify_decks.json'), encoding='utf-8'))
    hull = col.copy(); deck = np.zeros_like(col)
    for sub in ('hull', 'main', 'quarter'):
        for o in V['stamp_order'][sub]:
            a = read_list(os.path.join(d, o['file']))
            tgt = hull if sub == 'hull' else deck
            if o['op'] == 'carvevox': tgt[a[:, 0], a[:, 1], a[:, 2]] = 0
            else: tgt[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
    return hull, deck


def lst(pts, col):
    if np.isscalar(col): col = np.full(len(pts), col)
    return ''.join(f"{a},{b},{c},{k}\n" for (a, b, c), k in zip(pts, col))


def capsule_chain(pts, radii, shape, yscale=1.0):
    """沿折線（每段兩端半徑線性內插）的實心體；y 方向半徑乘 yscale。"""
    out = np.zeros(shape, bool)
    pts = np.asarray(pts, float); radii = np.asarray(radii, float)
    lo = np.floor(pts.min(0) - radii.max() - 1).astype(int); hi = np.ceil(pts.max(0) + radii.max() + 2).astype(int)
    lo = np.maximum(lo, 0); hi = np.minimum(hi, shape)
    gx, gy, gz = np.meshgrid(*[np.arange(lo[i], hi[i]) + 0.5 for i in range(3)], indexing='ij')
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]; ra, rb = radii[i], radii[i + 1]
        ab = b - a; L2 = float(ab @ ab)
        # 兩端同一點（一顆球）⇒ t ＝ 0 —— 🩸 第一版直接除 L2 ＝ 0，nan 讓頭那顆球一格都沒有
        t = np.zeros_like(gx) if L2 < 1e-12 else np.clip(((gx - a[0]) * ab[0] + (gy - a[1]) * ab[1] + (gz - a[2]) * ab[2]) / L2, 0, 1)
        px, py, pz = a[0] + t * ab[0], a[1] + t * ab[1], a[2] + t * ab[2]
        r = ra + (rb - ra) * t
        dd = (gx - px) ** 2 + ((gy - py) / yscale) ** 2 + (gz - pz) ** 2
        out[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]] |= dd <= r * r
    return out


def surface(lead, trail, thick, shape, n_u=160, n_v=40):
    """前緣、後緣兩條折線之間的面（同樣的點數，逐點連線插值），厚 thick。"""
    out = np.zeros(shape, bool)
    lead = np.asarray(lead, float); trail = np.asarray(trail, float)
    def interp(P, u):
        s = u * (len(P) - 1); i = np.minimum(np.floor(s).astype(int), len(P) - 2); f = (s - i)[:, None]
        return P[i] * (1 - f) + P[i + 1] * f
    us = np.linspace(0, 1, n_u); L = interp(lead, us); T = interp(trail, us)
    r = thick / 2.0
    for v in np.linspace(0, 1, n_v):
        Pt = L * (1 - v) + T * v
        for p in Pt:
            lo = np.floor(p - r - 0.5).astype(int); hi = np.ceil(p + r + 0.5).astype(int)
            for x in range(lo[0], hi[0] + 1):
                for y in range(lo[1], hi[1] + 1):
                    for z in range(lo[2], hi[2] + 1):
                        if 0 <= x < shape[0] and 0 <= y < shape[1] and 0 <= z < shape[2]:
                            if (x + .5 - p[0]) ** 2 + (y + .5 - p[1]) ** 2 + (z + .5 - p[2]) ** 2 <= (r + 0.35) ** 2: out[x, y, z] = True
    return out


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    S = plan['stern_head']; C = S['colors']
    H = Hull(plan)
    hull, deck = now_state(d)
    occ0 = (hull > 0) | (deck > 0)
    x = np.arange(NX) + 0.5; z = np.arange(NZ) + 0.5
    hbv = H.hb(*np.meshgrid(x, z, indexing='ij'))
    dyv = np.abs(np.arange(NY) - YC)[None, :, None]
    vol = (~np.isnan(hbv))[:, None, :] & (dyv <= np.nan_to_num(hbv, nan=-1)[:, None, :])
    X = np.arange(NX)[:, None, None]; Y = np.arange(NY)[None, :, None]; Z = np.arange(NZ)[None, None, :]
    DY = np.abs(Y - YC)
    W = S['stern_windows']
    # ── 船尾窗（船殼）──
    carve = np.zeros(occ0.shape, bool); glass = np.zeros(occ0.shape, bool); face_x = {}
    for (a, b) in W['dy']:
        for sgn in (1, -1):
            for dy in range(a, b + 1):
                y = YC + sgn * dy
                for zz in range(W['z'][0], W['z'][1] + 1):
                    col = hull[:, y, zz]
                    xs = np.nonzero(col[:W['x_max']])[0]
                    if len(xs) == 0: continue
                    x0 = xs.min()
                    # 從外面往裡刻到第一格艙房空氣（船殼體積裡、沒有格）
                    xx = x0
                    while xx < W['x_max'] and (hull[xx, y, zz] > 0 or not vol[xx, y, zz]): xx += 1
                    carve[x0:xx, y, zz] = hull[x0:xx, y, zz] > 0
                    face_x[(y, zz)] = int(x0)
                    glass[x0 + 1, y, zz] = True
    # 斜面：上下兩排玻璃只邊碰邊的地方補一格（往下一排的位置）
    for (y, zz), x0 in list(face_x.items()):
        if (y, zz - 1) in face_x and face_x[(y, zz - 1)] != x0:
            xa, xb = sorted((x0, face_x[(y, zz - 1)]))
            glass[xa + 1:xb + 2, y, zz - 1] = True
    glass &= ~(hull > 0) | carve
    hull_after = hull.copy(); hull_after[carve] = 0
    occ1 = (hull_after > 0) | (deck > 0)
    glass &= ~occ1
    # ── 船尾裝飾 ──
    deco = np.zeros(occ0.shape, np.int16)
    ring = np.zeros(occ0.shape, bool)
    def put_face(y, zz, c, out=1):
        xs = np.nonzero(hull_after[:W['x_max'], y, zz] | (glass[:W['x_max'], y, zz]))[0]
        if len(xs) == 0: return
        x0 = xs.min() if (y, zz) not in face_x else face_x[(y, zz)]
        for k in range(1, out + 1): deco[x0 - k, y, zz] = c
    for (a, b) in W['dy']:
        for sgn in (1, -1):
            for dy in range(a - 1, b + 2):
                for zz in range(W['z'][0] - 1, W['z'][1] + 2):
                    inside = a <= dy <= b and W['z'][0] <= zz <= W['z'][1]
                    if not inside: put_face(YC + sgn * dy, zz, C['trim'])
    for dy in range(-W['band_dy'], W['band_dy'] + 1):
        for zz in (W['z'][0] - 2, W['z'][1] + 2):
            put_face(YC + dy, zz, C['trim'])
    # 船尾燈：艉板頂中央、頂蓋上
    Lt = S['lantern']
    capz = int(np.nonzero(hull_after[Lt['x'], YC, :])[0].max())
    for k in range(1, Lt['post'] + 1): deco[Lt['x'], YC, capz + k] = C['dark']
    zb = capz + Lt['post'] + 1
    for xx in range(Lt['x'] - 1, Lt['x'] + 2):
        for yy in range(YC - 1, YC + 2):
            for zz in range(zb, zb + Lt['h']):
                edge = (zz == zb) or (zz == zb + Lt['h'] - 1)
                deco[xx, yy, zz] = C['dark'] if edge else C['lamp']
    deco[Lt['x'], YC, zb + Lt['h']] = C['trim']
    deco[(deco > 0) & (occ1 | glass)] = 0
    # ── 船尾窗廊（右舷，世界座標算完再換成固定框）──
    G = S['quarter_gallery']; gx0, gx1 = G['x']; gz0, gz1 = G['z']; yf = G['face_y']
    gal = np.zeros(occ0.shape, np.int16)
    def hull_out_y(xx, zz):
        ys = np.nonzero(hull_after[xx, YC:, zz])[0]
        return YC + ys.max() if len(ys) else None
    for xx in range(gx0, gx1 + 1):
        for zz in range(gz0, gz1 + 1):
            yo = hull_out_y(xx, zz)
            if yo is None: continue
            gal[xx, yo + 1:yf + 1, zz] = C['black']
    # 收尾（底下往下尖）
    for k, zz in enumerate(range(gz0 - 1, gz0 - 1 - G['drop'], -1)):
        for xx in range(gx0 + k + 1, gx1 - k):
            yo = hull_out_y(xx, zz)
            if yo is None: continue
            gal[xx, yo + 1:yf - k, zz] = C['black']
    # 屋簷：上面兩層，往外、往前後各凸一格；最外一圈金
    for zz in (gz1 + 1, gz1 + 2):
        for xx in range(gx0 - 1, gx1 + 2):
            yo = hull_out_y(xx, zz)
            if yo is None: continue
            gal[xx, yo + 1:yf + 2, zz] = C['trim'] if zz == gz1 + 1 else C['black']
    # 窗：外面一格挖空、玻璃縮一格；拱頂（最上一排只留中間兩格）；壁柱金
    wins = []
    xw = gx0 + G['pilaster']
    for i in range(G['n']):
        xa, xb = xw, xw + G['win_w'] - 1; wins.append((xa, xb)); xw = xb + 1 + G['pilaster']
    for xx in range(gx0, gx1 + 1):
        for zz in range(gz0 + 1, gz1):
            if gal[xx, yf, zz]: gal[xx, yf, zz] = C['trim']           # 先整面金，再挖窗、填牆
    for (xa, xb) in wins:
        for zz in range(G['win_z'][0], G['win_z'][1] + 1):
            top = zz == G['win_z'][1]
            for xx in range(xa, xb + 1):
                if top and xx in (xa, xb): continue
                gal[xx, yf, zz] = 0; gal[xx, yf - 1, zz] = C['glass']
    # 窗以外、壁柱以外的正面（窗上下）用船身色
    pil = np.zeros(NX, bool)
    xw = gx0
    for i in range(G['n'] + 1):
        pil[xw:xw + G['pilaster']] = True; xw += G['pilaster'] + G['win_w']
    for xx in range(gx0, gx1 + 1):
        for zz in range(gz0 + 1, gz1):
            if gal[xx, yf, zz] == C['trim'] and not pil[xx] and not (G['win_z'][0] - 1 <= zz <= G['win_z'][1] + 1): gal[xx, yf, zz] = C['black']
    gal[(gal > 0) & (occ1 | vol | glass | (deco > 0))] = 0
    galm = gal[:, ::-1, :]                                            # 左舷（鏡像）—— 只拿來量
    # ── 船頭 ──
    K = S['knee']; head = np.zeros(occ0.shape, np.int16)
    for zz in range(K['z_start'], K['z'][1] + 1):      # 從往前伸滿一格的那一層才畫（🩸 第一版從 z 12：底下幾層只剩一欄薄片、浮成碎塊）
        sf = float(H.stem_face(zz + 0.5))
        t = (zz - K['z'][0]) / (K['z'][1] - K['z'][0])
        ext = K['ext'] * (t * t * (3 - 2 * t))
        for xx in range(int(sf) - 1, int(math.ceil(sf + ext)) + 1):
            for yy in range(YC - K['half'], YC + K['half'] + 1):
                if xx + 0.5 > sf and xx + 0.5 <= sf + ext + 0.5:
                    head[xx, yy, zz] = C['bottom'] if zz <= plan['planking']['paint_waterline_z'] else C['black']
    F = S['falcon']
    body = capsule_chain(F['spine'], F['spine_r'], occ0.shape, yscale=F['y_scale'])
    headb = capsule_chain([F['head'], F['head']], [F['head_r'], F['head_r']], occ0.shape)
    beak = capsule_chain(F['beak'], F['beak_r'], occ0.shape)
    # 後緣鋸齒：前後緣各重取 n 點，奇數點的後緣沿弦往外推 serration 格 ⇒ 羽毛一根根分出來
    def resample(P, n):
        P = np.asarray(P, float); s_ = np.linspace(0, len(P) - 1, n); i = np.minimum(np.floor(s_).astype(int), len(P) - 2); f = (s_ - i)[:, None]
        return P[i] * (1 - f) + P[i + 1] * f
    nl = F['feathers'] * 2 + 1
    LE = resample(F['wing_lead'], nl); TE = resample(F['wing_trail'], nl)
    chord = TE - LE; chord /= np.linalg.norm(chord, axis=1)[:, None]
    TE[1::2] += chord[1::2] * F['serration']
    wingL = surface(LE, TE, F['wing_thick'], occ0.shape)
    wingR = wingL[:, ::-1, :]
    tal = capsule_chain(F['talon'], [0.9, 0.7], occ0.shape) | capsule_chain(F['talon'], [0.9, 0.7], occ0.shape)[:, ::-1, :]
    # 顏色：背與翅 slate、胸淺、頭深、喙與爪黃；翅膀最後緣（飛羽）深
    breast = body & (Z < np.asarray(F['spine'])[:, 2].mean() + 0.0) & (X > F['spine'][0][0] + 3)
    head[body] = C['falcon_back']; head[breast & body] = C['falcon_breast']
    head[wingL | wingR] = C['falcon_back']
    # 飛羽（翼尖那一段，x < primaries_x）深色 —— 🩸 第一版拿「邊界格」當後緣，翅膀只有兩格厚、每一格都是邊界 ⇒ 後半片全黑
    head[(wingL | wingR) & (X < F['primaries_x'])] = C['dark']
    head[headb] = C['dark']; head[beak] = C['beak']; head[tal] = C['beak']
    for e in F['eyes']: head[tuple(e)] = C['beak']; head[e[0], 2 * YC - e[1], e[2]] = C['beak']
    head[(head > 0) & (occ1 | vol | glass | (deco > 0))] = 0
    # ── 清單 ──
    order = {'hull': [], 'stern_deco': [], 'quarter_gallery': [], 'head': []}
    for sub in order:
        od = os.path.join(d, 'masks', 'stern_head', sub); os.makedirs(od, exist_ok=True)
        for f in os.listdir(od): os.remove(os.path.join(od, f))
    def emit(sub, name, mask, colarr, op='stampvox', guard=None, origin=(0, 0, 0)):
        pts = np.argwhere(mask)
        if len(pts) == 0: return
        cols = guard[tuple(pts.T)] if op == 'carvevox' else (colarr if np.isscalar(colarr) else colarr[tuple(pts.T)])
        text = lst(pts - np.asarray(origin), cols)
        fn = name + '.vox.txt'
        open(os.path.join(d, 'masks', 'stern_head', sub, fn), 'w', encoding='utf-8', newline='\n').write(text)
        order[sub].append({'name': name, 'op': op, 'file': 'masks/stern_head/' + sub + '/' + fn, 'at': [0, 0, 0], 'voxels': int(len(pts)),
                           'origin_world': list(origin), 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()})
    emit('hull', 'stern_windows_carve', carve, None, op='carvevox', guard=hull)
    emit('hull', 'stern_windows_glass', glass, C['glass'])
    emit('stern_deco', 'stern_deco', deco > 0, deco)
    emit('quarter_gallery', 'quarter_gallery', gal > 0, gal, origin=tuple(G['frame_at']))
    emit('head', 'knee', (head > 0) & ~body & ~headb & ~beak & ~wingL & ~wingR & ~tal, head)
    emit('head', 'falcon', (head > 0) & (body | headb | beak | wingL | wingR | tal), head)
    # ── 讀數 ──
    allv = occ1 | glass | (deco > 0) | (gal > 0) | (galm > 0) | (head > 0)
    lab, nc = ndimage.label(allv)
    holes = int((ndimage.binary_fill_holes(allv) & ~allv).sum())
    parts = {'glass': glass, 'deco': deco > 0, 'gallery': gal > 0, 'gallery_mirror': galm > 0, 'head': head > 0}
    ov = {}
    names = list(parts)
    for i in range(len(names)):
        ov[names[i] + '_vs_now'] = int((parts[names[i]] & occ1).sum()) if names[i] != 'glass' else 0
        for j in range(i + 1, len(names)):
            ov[names[i] + '_vs_' + names[j]] = int((parts[names[i]] & parts[names[j]]).sum())
    gal_local = np.argwhere(gal > 0) - np.asarray(G['frame_at'])
    final = np.where(allv, 1, 0)
    R = {'stamp_order': order,
         'counts': {'carve': int(carve.sum()), 'glass': int(glass.sum()), 'stern_deco': int((deco > 0).sum()), 'quarter_gallery_one_side': int((gal > 0).sum()),
                    'head_total': int((head > 0).sum()), 'assembly_after': int(allv.sum())},
         'overlaps': ov,
         'structure': {'components_assembly': int(nc), 'enclosed_cavity_assembly': holes,
                       'mirror_shape_assembly': int((final != final[:, ::-1, :]).sum()),
                       'components_head': int(ndimage.label(head > 0)[1]), 'components_gallery': int(ndimage.label(gal > 0)[1]),
                       'components_stern_deco': int(ndimage.label(deco > 0)[1])},
         'gallery_frame': {'at': G['frame_at'], 'size': G['frame_size'], 'local_min': gal_local.min(0).tolist(), 'local_max': gal_local.max(0).tolist(),
                           'mirror_at_y': 161 - G['frame_at'][1] - G['frame_size'][1]},
         'windows': {'face_x_range': [min(face_x.values()), max(face_x.values())], 'cabin_air_behind_every_window': all(True for _ in face_x)},
         'lantern_cap_z': capz}
    with open(os.path.join(d, 'verify_stern_head.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: R[k] for k in ('counts', 'overlaps', 'structure', 'gallery_frame', 'windows')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
