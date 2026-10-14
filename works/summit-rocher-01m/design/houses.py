# 岩堡港 房屋產生器（TASK-0580）：plan.json 的 houses.<型> ＋ 一個配色 ⇒ 逐格 {(x, y, z): 色} ＋ 固定點。
# 用法：import houses; V, A, meta = houses.build(plan, '<型>', '<配色>')
#   · 座標（房屋自己的作品）：x ＝ 沿街面（左 → 右）、y ＝ 進深（臨街那面在 y 小的一側，往 −y 是街）、z ＝ 往上；0.1 m／格。
#   · 屋身佔 x ∈ [X0, X0+W)、y ∈ [Y0, Y0+D)；X0 ＝ 屋簷外挑（＋招牌、吊貨梁外伸）、Y0 ＝ 迴廊深＋迴廊屋頂外緣 ⇒ 所有格 ≥ 0。
#   · 格 k 佔 [k, k+1)、格心 k+0.5；屋頂斜面照格心算。
#   · 牆的種類：plaster（粉刷）、timber（木構：梁、柱、斜撐）、stone（石砌）、plank（木板：每 4 格一道暗縫）。
#   · 屋頂：gable（兩坡，屋脊沿 x）、hip（四坡）、shed（單坡，臨街那邊低）；先算每一欄的屋頂頂面，牆頂一圈補到屋頂底下（山牆、單坡的高牆）。
#   · 落子順序就是這支程式寫入的順序；後寫的蓋掉先寫的（dict）⇒ 清單本身沒有重複格。
import math


def col(plan, name):
    p = plan['palette']
    return p[name] if isinstance(name, str) else name


class Vox:
    def __init__(s):
        s.v = {}

    def box(s, x0, y0, z0, x1, y1, z1, c):
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    s.v[(x, y, z)] = c

    def clear(s, x0, y0, z0, x1, y1, z1):
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    s.v.pop((x, y, z), None)

    def recolor(s, x0, y0, z0, x1, y1, z1, c):
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    if (x, y, z) in s.v:
                        s.v[(x, y, z)] = c


def face_box(face, X0, Y0, W, D, t, u0, u1, z0, z1, layer=0):
    """牆面上的一塊：face 的 u ∈ [u0, u1)、z ∈ [z0, z1)；layer 0 ＝ 牆身（厚 t），−1 ＝ 牆外貼一層（百葉、窗台）。"""
    if face == 'front':
        ya, yb = (Y0, Y0 + t) if layer == 0 else (Y0 - 1, Y0)
        return X0 + u0, ya, z0, X0 + u1, yb, z1
    if face == 'back':
        ya, yb = (Y0 + D - t, Y0 + D) if layer == 0 else (Y0 + D, Y0 + D + 1)
        return X0 + u0, ya, z0, X0 + u1, yb, z1
    if face == 'left':
        xa, xb = (X0, X0 + t) if layer == 0 else (X0 - 1, X0)
        return xa, Y0 + u0, z0, xb, Y0 + u1, z1
    if face == 'right':
        xa, xb = (X0 + W - t, X0 + W) if layer == 0 else (X0 + W, X0 + W + 1)
        return xa, Y0 + u0, z0, xb, Y0 + u1, z1
    raise ValueError(face)


PIG = ["....pppppp..",                         # 酒館招牌：倒吊的豬（Le Cochon Pendu；12×8，p ＝ 粉、e ＝ 眼）
       "..pppppppppp",
       ".pppppppppep",
       "pppppppppppp",
       ".pppppppppp.",
       "..pp....pp..",
       "..pp....pp..",
       "............"]


def build(plan, typ, variant):
    H = plan['houses'][typ]
    Vt = H['variants'][variant]
    C = lambda n: col(plan, n)
    W, D = H['W'], H['D']
    R = H['roof']
    G = H.get('gallery')
    over = R['over']
    gd = G['depth'] if G else 0
    sign = H.get('sign')
    X0 = over + (sign['reach'] if sign and sign.get('face') == 'left' else 0)
    Y0 = max(over, gd + 2, gd + 6 if sign else 0) + (H['hoist']['reach'] if H.get('hoist') else 0)   # 招牌板伸到迴廊外緣再外 6 格
    V = Vox()
    A = {}
    p = H['plinth']
    ft = H['floor_t']

    # ── 石基（含迴廊下的平台）──
    V.box(X0, Y0, 0, X0 + W, Y0 + D, p, C(H['plinth_color']))
    if G:
        V.box(X0, Y0 - gd, 0, X0 + W, Y0, p, C(H['plinth_color']))

    # ── 各層牆與樓板 ──
    zb = p
    fz = []                                   # 每一層的 [底, 頂)
    for i, F in enumerate(H['floors']):
        if i > 0:                             # 樓板（含牆身那一圈，外面看是一條木帶）
            V.box(X0, Y0, zb, X0 + W, Y0 + D, zb + ft, C('timber_dark') if F['kind'] == 'timber' else C(H['floor_color']))
            V.box(X0 + 1, Y0 + 1, zb, X0 + W - 1, Y0 + D - 1, zb + ft, C(H['floor_color']))
            zb += ft
        t = F['t']
        wallc = C(Vt['wall'] if F['kind'] in ('plaster', 'stone', 'plank') else Vt['infill'])
        V.box(X0, Y0, zb, X0 + W, Y0 + D, zb + F['h'], wallc)
        V.clear(X0 + t, Y0 + t, zb, X0 + W - t, Y0 + D - t, zb + F['h'])
        if F['kind'] == 'timber':             # 木構：上下梁、角柱、每 post_step 一根柱、兩端那一格斜撐
            fr = C(F['frame'])
            for face, L in (('front', W), ('back', W), ('left', D), ('right', D)):
                V.recolor(*face_box(face, X0, Y0, W, D, t, 0, L, zb, zb + 2), fr)
                V.recolor(*face_box(face, X0, Y0, W, D, t, 0, L, zb + F['h'] - 2, zb + F['h']), fr)
                st = F['post_step']             # 離角柱不到半個柱距的那一根拿掉（不然最後一格只剩 4 格寬、斜撐擠成直條）
                posts = [u for u in range(0, L - 1, st) if u < L - 2 - st // 2] + [L - 2]
                for u in posts:
                    V.recolor(*face_box(face, X0, Y0, W, D, t, u, u + 2, zb, zb + F['h']), fr)
                for side, (ua, ub) in enumerate(((posts[0] + 2, posts[1]), (posts[-2] + 2, posts[-1]))):
                    n, hz = ub - ua, F['h'] - 4
                    for kz in range(hz):      # 斜撐：從角柱腳斜上到下一根柱頂、兩格粗；照 z 逐層走（比 45° 陡 ⇒ 照 u 走會斷成一串點）
                        k = int(round(kz * (n - 2) / max(1, hz - 1)))
                        uu = ua + k if side == 0 else ub - 2 - k
                        V.recolor(*face_box(face, X0, Y0, W, D, t, uu, uu + 2, zb + 2 + kz, zb + 3 + kz), fr)
        if F['kind'] == 'plank':              # 木板：每 4 格一道暗縫（只染外面那一層）
            for face, L in (('front', W), ('back', W), ('left', D), ('right', D)):
                for zz in range(zb + 3, zb + F['h'], 4):
                    V.recolor(*face_box(face, X0, Y0, W, D, 1, 0, L, zz, zz + 1), C(F['seam']))
        fz.append((zb, zb + F['h'], F, t))
        zb += F['h']
    z_eave = zb

    # ── 開口：門、窗（窗帶百葉與窗台；二樓的門＝通陽台，也帶百葉）──
    for O in H['openings']:
        z0f, z1f, F, t = fz[O['floor']]
        face = O['face']
        u0, u1 = O['u'], O['u'] + O['w']
        z0 = z0f + (O.get('sill', 0) if O['kind'] in ('window', 'loft') else 0)
        z1 = z0 + O['h']
        if F['kind'] == 'timber':             # 框：開口四周一格染成梁色
            V.recolor(*face_box(face, X0, Y0, W, D, t, u0 - 1, u1 + 1, z0 - 1, z1 + 1), C(F['frame']))
        if O.get('lintel'):                   # 石砌的門窗上一條過梁
            V.recolor(*face_box(face, X0, Y0, W, D, t, u0 - 2, u1 + 2, z1, z1 + 3), C(O['lintel']))
        V.clear(*face_box(face, X0, Y0, W, D, t, u0, u1, z0, z1))
        shut = O.get('shutters', O['kind'] == 'window' or O['floor'] > 0)
        if shut:
            half = O['w'] // 2
            V.box(*face_box(face, X0, Y0, W, D, t, u0 - half, u0, z0, z1, layer=-1), C(Vt['shutter']))
            V.box(*face_box(face, X0, Y0, W, D, t, u1, u1 + half, z0, z1, layer=-1), C(Vt['shutter']))
        if O['kind'] == 'window':
            V.box(*face_box(face, X0, Y0, W, D, t, u0 - 1, u1 + 1, z0 - 1, z0, layer=-1), C('stone_light'))
        if face == 'front' and O['floor'] == 0 and O['kind'] == 'door' and 'door' not in A:
            A['door'] = [X0 + (u0 + u1) / 2.0, Y0 - 1.5, p + 0.5]

    # ── 迴廊：一樓是有頂的廊、二樓是陽台；柱子落地撐住迴廊屋頂 ──
    if G:
        gc, gw = C(G['color']), G['post_w']
        yf = Y0 - gd                          # 迴廊外緣
        z1b = fz[1][0]                        # 二樓樓面（陽台地板頂）
        V.box(X0, yf, z1b - ft, X0 + W, Y0, z1b, C(G['floor']))
        V.box(X0, yf, z1b - ft, X0 + W, yf + 1, z1b, gc)        # 陽台外緣的梁
        zr_wall = z_eave - 2                  # 迴廊屋頂靠牆那一邊
        zr_edge = zr_wall - G['roof_drop']
        for y in range(yf - 2, Y0):           # 迴廊屋頂（單坡，厚 2）
            f = (Y0 - (y + 0.5)) / (gd + 2)
            zt = int(math.floor(zr_wall - f * (zr_wall - zr_edge)))
            V.box(X0 - 1, y, zt - 1, X0 + W + 1, y + 1, zt + 1, C(G['roof']))
        z_post_top = zr_edge - 1
        xs = list(range(X0, X0 + W - gw, G['post_step'])) + [X0 + W - gw]
        for x in xs:                          # 柱：從石台頂到迴廊屋頂下
            V.box(x, yf, p, x + gw, yf + gw, z_post_top + 1, gc)
        rt = z1b + G['rail_h'] - 1
        for x in range(X0, X0 + W):           # 欄杆：前緣＋兩側
            V.box(x, yf, rt, x + 1, yf + 1, rt + 1, gc)
            if (x - X0) % G['baluster_step'] == 0:
                V.box(x, yf, z1b, x + 1, yf + 1, rt, gc)
        for x in (X0, X0 + W - 1):
            for y in range(yf, Y0):
                V.box(x, y, rt, x + 1, y + 1, rt + 1, gc)
                if (y - yf) % G['baluster_step'] == 0:
                    V.box(x, y, z1b, x + 1, y + 1, rt, gc)
        A['lantern-L'] = [xs[0] + gw / 2.0, yf - 0.5, z_post_top - 2.5]
        A['lantern-R'] = [xs[-1] + gw / 2.0, yf - 0.5, z_post_top - 2.5]

    # ── 主屋頂 ──
    k, t = R['rise_per_run'], R['t']
    roofc = C(Vt['roof'])
    ztop = {}
    for x in range(X0 - over, X0 + W + over):
        for y in range(Y0 - over, Y0 + D + over):
            dy = D / 2.0 - abs((y + 0.5) - (Y0 + D / 2.0))            # 離最近的長邊牆多遠（牆外為負）
            dx = W / 2.0 - abs((x + 0.5) - (X0 + W / 2.0))
            if R['type'] == 'gable':
                h = dy
            elif R['type'] == 'hip':
                h = min(dx, dy)
            elif R['type'] == 'shed':                                   # 臨街（y 小）那邊低
                h = (y + 0.5) - Y0
            else:
                raise ValueError(R['type'])
            ztop[(x, y)] = int(math.floor(z_eave + h * k))
    for (x, y), zt in ztop.items():
        V.box(x, y, zt - t + 1, x + 1, y + 1, zt + 1, roofc)
    zr = max(ztop.values())
    for (x, y), zt in ztop.items():           # 屋脊：最高那一排換色
        if zt == zr:
            V.recolor(x, y, zt, x + 1, y + 1, zt + 1, C(Vt.get('ridge', R['ridge_cap'])))
    top = H['floors'][-1]
    gable = C(Vt['infill'] if top['kind'] == 'timber' else Vt['wall'])
    tg = top['t']
    for x in range(X0, X0 + W):               # 牆頂一圈補到屋頂底下（兩坡的山牆、單坡的高牆）
        for y in range(Y0, Y0 + D):
            if not (x < X0 + tg or x >= X0 + W - tg or y < Y0 + tg or y >= Y0 + D - tg):
                continue
            if R['type'] == 'gable' and not (x < X0 + tg or x >= X0 + W - tg):
                continue                      # 兩坡只補山牆（跟改寫前一樣：前後牆的屋簷本來就壓在牆頂）
            zt = ztop[(x, y)] - t
            if zt >= z_eave:
                V.box(x, y, z_eave, x + 1, y + 1, zt + 1, gable)

    # ── 煙囪（石砌，跨在側牆上，高出屋脊）──
    ch = H.get('chimney')
    if ch:
        xa = X0 + W - ch['d'] // 2 if ch['face'] == 'right' else X0 - ch['d'] // 2
        V.box(xa, Y0 + ch['u'], 0, xa + ch['d'], Y0 + ch['u'] + ch['w'], zr + ch['above'], C(ch['color']))
        V.recolor(xa, Y0 + ch['u'], zr + ch['above'] - 2, xa + ch['d'], Y0 + ch['u'] + ch['w'], zr + ch['above'], C('void_dark'))

    # ── 吊招牌（從迴廊左前柱伸出去的托架＋垂下的板；板在 y-z 面上，沿街兩頭都看得到）──
    if sign:
        yf = Y0 - gd
        zs = sign['z']
        V.box(X0 - sign['reach'], yf, zs, X0, yf + 2, zs + 2, C('timber_dark'))          # 托架
        V.box(X0 - sign['reach'] + 1, yf, zs - 2 - len(PIG) - 2, X0 - sign['reach'] + 2, yf + 1, zs, C('timber_dark'))
        bx = X0 - sign['reach'] + 1
        y0s = yf - 2
        for zz in range(len(PIG) + 2):        # 板 14×10、1 格厚，邊框木色、中間豬
            for yy in range(14):
                V.box(bx, y0s + yy - 4, zs - 3 - zz, bx + 1, y0s + yy - 3, zs - 2 - zz, C('wood'))
        for r_, row in enumerate(PIG):
            for c_, ch_ in enumerate(row):
                if ch_ != '.':
                    V.v[(bx, y0s - 4 + 1 + c_, zs - 4 - r_)] = C('plaster_salmon') if ch_ == 'p' else C('void_dark')
        A['sign'] = [bx + 0.5, y0s + 3.0, zs - 8.0]

    # ── 吊貨梁（倉庫：屋簷下伸出去的一根梁，梁頭掛滑車用的固定點）──
    ho = H.get('hoist')
    if ho:
        xm = X0 + ho['u']
        V.box(xm - 1, Y0 - ho['reach'], ho['z'], xm + 1, Y0 + 3, ho['z'] + 2, C('timber_dark'))
        A['hoist'] = [xm, Y0 - ho['reach'] + 0.5, ho['z'] - 0.5]

    meta = {'type': typ, 'variant': variant, 'X0': X0, 'Y0': Y0, 'W': W, 'D': D, 'z_eave': z_eave, 'z_ridge': zr,
            'floors': [[a, b] for a, b, _, _ in fz]}
    return V.v, A, meta
