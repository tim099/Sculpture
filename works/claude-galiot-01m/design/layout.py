# 蠍子號 甲板以上的配置（TASK-0023）：plan.json 的 layout ⇒ 每一件的格子（numpy 陣列，整船的框，兩舷照 |dy| 產 ⇒ 逐格對稱）
#   出處：apex-one-reale-01m/design/draft_upper.py（皇家號 1694：甲板拱、中央走道兩頭台階、划手座＋柱＋水平腳踏、舷外槳架縱樑＋joug＋bacalat、
#         船頭砲台 rambade＋梯子、撞角斜撐、船尾篷、燈桿）與 kotoko-fusta-01m/design/draft_upper.py（越嶺號：槳栓、小船的尺寸）。
#   改的地方：全部數字讀本船 plan.json 的 layout（皇家號寫死的中線 160、柱的 dy 18／32、腳踏 dy 22、燈桿、翹尾曲線都改成參數）；
#            槳栓改成「每張座 tholes.dx 那幾根」（a scaloccio 一根、alla sensile 兩根）；件的順序與扣重疊照越嶺號。
#   被 draft_layout.py（步驟 3 圖紙與讀數）與之後各步的 draft_*.py（落格清單）import；只讀 plan.json 與船殼清單，不碰作品。
import os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
import lines as HL

PIECES = ['deck', 'apostis', 'rambade', 'ladders', 'spur', 'poop', 'awning']   # 步驟 6 把 stern 拆成 poop（艉台、燈桿）與 awning（篷）


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def load_list(path):
    return np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


class Ctx:
    def __init__(self, plan, probe=None, hull=None):
        self.plan = plan
        self.L = HL.Lines(plan)
        self.YC = self.L.YC
        self.SX, self.SY, self.SZ = [int(v) for v in plan['space']['hull']]
        self.P = {k: V(v) for k, v in plan['layout'].items() if k != 'src'}
        for k, d in (probe or {}).items():                      # 反向對照：layout 的某個數字加減（sec.key 或 key）；drop_bench=i 拿掉第 i 張座
            if k == 'drop_bench':
                self.P['_drop_bench'] = int(d)
            elif '.' in k:
                sec, key = k.split('.')
                self.P[sec] = dict(self.P[sec])
                self.P[sec][key] = self.P[sec][key] + d
            else:
                self.P[k] = self.P[k] + d
        self.C = {k: V(v) for k, v in V(plan['layout']['colors']).items()}
        self.wl = plan['waterline']['z']
        if hull is None:
            h = load_list(os.path.join(HERE, 'masks', 'hull', 'hull_01.vox.txt'))
            hull = np.zeros((self.SX, self.SY, self.SZ), np.uint8)
            hull[h[:, 0], h[:, 1], h[:, 2]] = h[:, 3]
        self.hull = hull
        xs = np.arange(self.SX) + 0.5
        self.sh = np.floor(self.L.sheer(xs)).astype(int)                                  # 舷頂那一格的 z
        self.hbs = np.array([float(self.L.hb(x + 0.5, self.sh[x] - 0.5)) for x in range(self.SX)])   # 舷頂下一格的外緣半寬
        self.wall = int(V(plan['hull_build']['wall']))
        b = self.P['benches']
        self.benches = [int(round(b['first_x'] + b['pitch'] * i)) for i in range(int(b['n']))]

    def hw_deck(self, x):
        """甲板在 x 那一欄的內緣半寬（船殼牆裡面）；沒有 ⇒ -1。"""
        return int(np.floor(self.hbs[x])) - self.wall if self.hbs[x] > 0 else -1

    def deck_top(self, x, dy):
        hw = self.hw_deck(x)
        if hw < 0:
            return None
        dy = min(abs(dy), hw)
        cam = self.P['deck']['camber'] * (hw / self.L.B2) * (1 - (dy / max(hw, 1)) ** 2)
        return int(self.sh[x] - self.P['deck']['side_below_sheer'] + round(cam))

    def seat_top(self, x):
        return int(self.sh[x] + self.P['benches']['above_sheer'])

    def rail_top(self, x):
        return int(self.sh[x] + self.P['apostis']['above_sheer'])


def put(K, a, x, dy, z, c):
    """兩舷一起放（dy ≥ 0；dy 0 只放一次）。"""
    if 0 <= x < K.SX and 0 <= z < K.SZ and 0 <= K.YC + dy < K.SY:
        a[x, K.YC + dy, z] = c
        a[x, K.YC - dy, z] = c


# ───────── 甲板、中央走道（corsia）、划手座 ─────────
def build_deck(K):
    a = np.zeros((K.SX, K.SY, K.SZ), np.uint8)
    C, P = K.C, K.P
    dk = P['deck']
    hatches = dk.get('hatches', [])

    def in_hatch(x, dy):
        return next((h for h in hatches if h['x0'] <= x <= h['x1'] and dy <= h['half']), None)

    for x in range(K.SX):
        hw = K.hw_deck(x)
        if hw < 2:
            continue
        for dy in range(hw + 1):
            h = in_hatch(x, dy)
            if h:
                g = int(h.get('grating', 0))                # 格柵（步驟 5）：只鋪頂層，每 g 格一根條 ⇒ 1 格的孔讓艙裡通氣、人掉不進去
                if g and ((x - h['x0']) % g == 0 or dy % g == 0):
                    put(K, a, x, dy, K.deck_top(x, dy), C['dark'])
                continue
            t = K.deck_top(x, dy)
            put(K, a, x, dy, t, C['deck'])                  # 板兩層（皇家號同）：甲板拱取整後的 1 格階梯靠第二層面相接
            put(K, a, x, dy, t - 1, C['deck'])               # （v0 只有一層 ⇒ 船頭 x 330 中線 3 格只靠斜角相接、斷開）
            if x % int(dk['beam_every']) == 0:
                put(K, a, x, dy, t - 2, C['beam'])
    co = P['corsia']
    cx0, cx1, ch, chalf = co['x0'], co['x1'], int(co['h']), int(co['half'])
    step = max(1, ch // 2)
    for x in range(cx0 - 6, cx1 + 7):
        if K.hw_deck(x) < chalf:
            continue
        if x < cx0 - 3 or x > cx1 + 3:
            top = ch - 2 * step
        elif x < cx0 or x > cx1:
            top = ch - step
        else:
            top = ch
        if top <= 0:
            continue
        zt = K.deck_top(x, 0) + top
        for dy in range(chalf + 1):
            for z in range(K.deck_top(x, dy) + 1, zt + 1):
                put(K, a, x, dy, z, C['deck'] if z == zt else C['wood'])
    be = P['benches']
    b0, b1 = be['dy']
    drop = K.P.get('_drop_bench')
    for i, xc in enumerate(K.benches):
        if drop is not None and i == int(drop):
            continue
        st = K.seat_top(xc)
        for x in range(xc - be['w'] // 2, xc - be['w'] // 2 + be['w']):
            for dy in range(b0, b1 + 1):
                put(K, a, x, dy, st, C['seat'])
        for dy in be['posts_dy']:
            if dy <= K.hw_deck(xc):
                for z in range(K.deck_top(xc, dy) + 1, st):
                    put(K, a, xc, dy, z, C['dark'])
        xf = xc - int(be['footrest_back'])
        zf = K.deck_top(xf, 0) + int(be['footrest_h'])
        for dy in range(b0, min(b1, K.hw_deck(xf)) + 1):
            put(K, a, xf, dy, zf, C['dark'])
        dyp = min(be['footrest_post_dy'], K.hw_deck(xf))      # 船尾窄處：撐柱收到船殼內緣（v2 蠍子號第 1、2 張座的腳踏懸空）
        for z in range(K.deck_top(xf, dyp) + 1, zf):
            put(K, a, xf, dyp, z, C['dark'])
    for h in hatches:                                       # 艙口圍欄（1 格高）
        for x in range(h['x0'] - 1, h['x1'] + 2):
            for dy in range(h['half'] + 2):
                if x in (h['x0'] - 1, h['x1'] + 1) or dy == h['half'] + 1:
                    t = K.deck_top(x, dy)
                    if t is not None:
                        put(K, a, x, dy, t + 1, C['wood'])
    return a


# ───────── 舷外槳架（apostis）：縱樑、兩頭 joug、每張座之間的托架、槳栓 ─────────
def build_apostis(K):
    a = np.zeros((K.SX, K.SY, K.SZ), np.uint8)
    C, P = K.C, K.P
    ap = P['apostis']
    ax0, ax1 = ap['x']
    ah = int(ap['half'])
    rw = int(ap['rail_w'])
    for x in range(ax0 + 2, ax1 - 1):                       # 縱樑：rail_w 寬、rail_h 高、頂一格色帶
        rt = K.rail_top(x)
        for dy in range(ah - rw + 1, ah + 1):
            for z in range(rt - int(ap['rail_h']) + 1, rt + 1):
                put(K, a, x, dy, z, C['rail_top'] if z == rt else C['rail'])
    wk = ap.get('walkway')
    if wk:                                                  # 舷外走道（座的外端那一段，兵站的地方）
        for x in range(ax0 + 2, ax1 - 1):
            wt = K.seat_top(x) - int(wk['below_seat'])
            for dy in range(wk['dy'][0], wk['dy'][1] + 1):
                put(K, a, x, dy, wt, C['deck'])
    for xj in list(range(ax0, ax0 + 2)) + list(range(ax1 - 1, ax1 + 1)):   # 兩頭的橫樑 joug：躺在舷頂上、外端立到縱樑高
        for dy in range(ah + 1):
            put(K, a, xj, dy, K.sh[xj] + 1, C['dark'])
        for dy in range(ah - rw + 1, ah + 1):
            for z in range(K.sh[xj] + 1, K.rail_top(xj) + 1):
                put(K, a, xj, dy, z, C['rail_top'] if z == K.rail_top(xj) else C['rail'])
    for xc in K.benches:                                    # 托架（bacalat）：每張座往船頭 bracket_dx 格一個，船殼舷頂下 → 縱樑底
        xb = xc + int(ap['bracket_dx'])
        if not (ax0 < xb < ax1):
            continue
        d0 = int(np.floor(K.hbs[xb])) + 1
        z0 = K.sh[xb] - 2
        zt = K.rail_top(xb) - int(ap['rail_h'])
        for t in np.linspace(0, math.pi / 2, 60):
            dy = d0 + (ah - rw - d0) * math.sin(t)
            z = z0 + (zt - z0) * (1 - math.cos(t))
            for ddy in (0, 1):
                for dz in (0, 1):
                    put(K, a, xb, int(round(dy)) + ddy - 1, int(round(z)) + dz, C['dark'])
    th = P['tholes']
    for xc in K.benches:                                    # 槳栓：每張座 tholes.dx 那幾根，立在縱樑頂、靠外那一欄
        for dx in th['dx']:
            for z in range(K.rail_top(xc + dx) + 1, K.rail_top(xc + dx) + 1 + int(th['h'])):
                put(K, a, xc + dx, ah - rw + 1 + int(th.get('dy_in_rail', 0)), z, C['beam'])
    return a


# ───────── 船頭砲台（rambade）：中央走道兩旁兩座平台，底下放砲 ─────────
def rambade_geo(K):
    R = K.P['rambade']
    rx0, rx1 = R['x']
    zt = max(K.deck_top(x, 0) for x in range(rx0, rx1 + 1)) + int(R['clear'])
    d_in, w_aft, w_fwd = R['dy']
    wf = lambda x: int(np.floor(w_aft + (w_fwd - w_aft) * (x - rx0) / max(1, rx1 - rx0)))
    return rx0, rx1, zt, d_in, wf


def build_rambade(K):
    a = np.zeros((K.SX, K.SY, K.SZ), np.uint8)
    C, R = K.C, K.P['rambade']
    rx0, rx1, zt, d_in, wf = rambade_geo(K)
    ph = int(R['parapet_h'])
    for x in range(rx0, rx1 + 1):
        w = wf(x)
        wn = wf(x + 1) if x < rx1 else w
        for dy in range(d_in, w + 1):
            put(K, a, x, dy, zt, C['deck'])
            put(K, a, x, dy, zt - 1, C['dark'] if dy >= w - 1 or x >= rx1 - 1 else C['deck'])
        for dy in range(min(w, wn), w + 1):                 # 外緣胸牆頂（斜邊照相鄰兩欄補滿 ⇒ 面相連）
            for z in (zt + ph - 1, zt + ph):
                put(K, a, x, dy, z, C['rail_top'] if z == zt + ph else C['rail'])
        if (x - rx0) % int(R['post_every']) == 0 or x == rx1:
            for z in range(zt + 1, zt + ph - 1):
                put(K, a, x, w, z, C['rail'])
    for dy in range(d_in, wf(rx1) + 1):                    # 船頭那一邊的胸牆
        if dy <= int(R.get('port_half', -1)):
            continue
        for z in (zt + ph - 1, zt + ph):
            put(K, a, rx1, dy, z, C['rail_top'] if z == zt + ph else C['rail'])
        if (dy - d_in) % int(R['post_every']) == 0:
            for z in range(zt + 1, zt + ph - 1):
                put(K, a, rx1, dy, z, C['rail'])
    for x in list(range(rx0, rx1 + 1, int(R['post_every']))) + [rx1]:   # 柱：內緣站在甲板上、外緣站在舷頂上
        if K.hw_deck(x) >= d_in:
            for z in range(K.deck_top(x, d_in) + 1, zt - 1):
                put(K, a, x, d_in, z, C['dark'])
        wo = min(wf(x), int(np.floor(K.hbs[x])))
        if wo > d_in:
            for z in range(K.sh[x] + 1, zt - 1):
                put(K, a, x, wo, z, C['dark'])
    return a


def build_ladders(K):
    """砲台的兩座梯子（甲板 → 砲台），回傳 (格, 固定點)；rambade.ladder 是 null（低平台，從中央走道走上去）⇒ 不做。"""
    a = np.zeros((K.SX, K.SY, K.SZ), np.uint8)
    C, LD = K.C, K.P['rambade'].get('ladder')
    pts = {}
    if not LD:
        return a, pts
    rx0, rx1, zt, d_in, wf = rambade_geo(K)
    d0, d1 = LD['dy']
    dm = (d0 + d1) // 2
    xtop = rx0 - 1
    zb = K.deck_top(xtop - 6, dm)
    n = (zt - zb) // 3
    rungs = []
    for k in range(1, n + 1):
        x = xtop - (n - k)
        z = zb + 3 * k
        if z >= zt - 1:
            break
        rungs.append((x, z))
    for (x, z) in rungs:
        for dy in range(d0, d1 + 1):
            put(K, a, x, dy, z, C['dark'])
    xlo = rungs[0][0]
    for side in (d0 - 1, d1 + 1):                          # 兩條側板：從甲板到砲台底
        for k, (x, z) in enumerate(rungs):
            z_from = K.deck_top(x, side) + 1 if k == 0 else rungs[k - 1][1]
            for zz in range(z_from, z + 3):
                if zz < zt - 1:
                    put(K, a, x, side, zz, C['dark'])
    for s, sgn in (('S', 1), ('P', -1)):
        y = K.YC + sgn * dm
        pts['ram-%s' % s] = {
            'foot': [xlo - 2, y, K.deck_top(xlo - 2, dm) + 1],
            'lo': [rungs[0][0], y, rungs[0][1] + 1],
            'hi': [rungs[-1][0], y, rungs[-1][1] + 1],
            'head': [rx0 + 2, y, zt + 1],
        }
    return a, pts


# ───────── spur（sperone）：從艏柱上段往前上翹，往前收；一根斜撐回艏柱 ─────────
def build_spur(K):
    a = np.zeros((K.SX, K.SY, K.SZ), np.uint8)
    C, E = K.C, K.P['spur']
    x0, x1 = E['x0'], E['x1']
    zc_of = lambda x: E['z0'] + (E['z1'] - E['z0']) * (x - x0) / (x1 - x0)
    for x in range(x0, x1 + 1):
        f = (x - x0) / (x1 - x0)
        zc = zc_of(x)
        h = E['h0'] + (E['h1'] - E['h0']) * f
        w = int(round(E['w0'] + (E['w1'] - E['w0']) * f))
        zlo, zhi = int(round(zc - h / 2)), int(round(zc + h / 2))
        for dy in range(w + 1):
            for z in range(zlo, zhi + 1):
                put(K, a, x, dy, z, C['spur_tip'] if x > x1 - int(E['tip']) else (C['rail_top'] if z == zhi else C['spur']))
    br = E['brace']                                         # 斜撐：艏柱 → spur 下緣
    xa, za = int(K.L.x_fwd(br['z_stem'])) + 1, br['z_stem']
    xb = x0 + int(br['dx'])
    fb = (xb - x0) / (x1 - x0)
    zb = int(round(zc_of(xb) - (E['h0'] + (E['h1'] - E['h0']) * fb) / 2)) - 1
    for t in np.linspace(0, 1, 120):
        x = int(round(xa + (xb - xa) * t))
        z = int(round(za + (zb - za) * t))
        for dz in (0, 1):
            put(K, a, x, 0, z + dz, C['spur'])
    return a


# ───────── 船尾：艉台（站的板）與燈桿（build_poop）、篷架與篷（build_awning）——步驟 6 拆成兩件：篷是外部模型 deco=1 ─────────
def build_stern(K):
    a = build_poop(K)
    b = build_awning(K, a)
    a[b > 0] = b[b > 0]
    return a


def build_awning(K, poop=None):
    a = np.zeros((K.SX, K.SY, K.SZ), np.uint8)
    C, S = K.C, K.P['stern']
    c0, c1 = S['canopy_x']
    for x in range(c0, c1 + 1):                            # 篷：橢圓拱，最外一圈；拱肋每 rib_every 格（木色），其他是布
        hc = int(np.floor(K.hbs[x]))
        if hc < 4:
            continue
        zb = K.sh[x] + int(S['canopy_eave'])
        zr = K.deck_top(x, 0) + int(S['canopy_ridge'])
        roof = lambda d: zb + (zr - zb) * math.sqrt(max(0.0, 1 - (d / hc) ** 2))
        for dy in range(hc + 1):
            zhi = int(math.floor(roof(dy)))
            zlo = int(math.floor(roof(dy + 1))) if dy < hc else zb - 1
            for z in range(min(zlo, zhi), zhi + 1):
                if (x - c0) % int(S['rib_every']) == 0 or x in (c0, c1):
                    c = C['dark']
                elif dy == hc and z == zb - 1:
                    c = C['cloth_edge']
                else:
                    c = C['cloth']
                put(K, a, x, dy, z, c)
    for x in S['canopy_posts']:                            # 篷柱：立在舷頂上
        hc = int(np.floor(K.hbs[x]))
        zb = K.sh[x] + int(S['canopy_eave'])
        for z in range(K.sh[x] + 1, zb - 1):
            put(K, a, x, hc, z, C['dark'])
    if poop is not None:
        a[poop > 0] = 0
    return a


def build_poop(K):
    a = np.zeros((K.SX, K.SY, K.SZ), np.uint8)
    C, S = K.C, K.P['stern']
    px0, px1 = S['poop_x']
    for x in range(px0, px1 + 1):                          # 艉台：甲板上 poop_above_deck 格的一層板（舵手、船長坐的地方）
        hw = K.hw_deck(x)
        if hw < 1:
            continue
        zt = K.deck_top(x, 0) + int(S['poop_above_deck'])
        for dy in range(hw + 1):                             # 實心艉台：板面到甲板之間整塊填同色（v2 板一層 ⇒ x 43–45 只靠邊相碰、斷開；
            for z in range(K.deck_top(x, dy) + 1, zt + 1):   #   板兩層 ⇒ 船尾末端兩舷船殼牆圍住板下那一層，封閉空腔 40 格）
                put(K, a, x, dy, z, C['deck'])
        if (x - px0) % 6 == 0 or x == px1:
            for dy in (0, hw):
                for z in range(K.deck_top(x, dy) + 1, zt):
                    put(K, a, x, dy, z, C['dark'])
    la = S.get('lantern')
    if la:                                                  # 燈桿：船尾中線，立在那一欄最高的實心格上（船殼或艉台），頂上一格是燈的位置（燈是模型）
        x = int(la['x'])
        col = (K.hull[x, K.YC, :] > 0) | (a[x, K.YC, :] > 0)
        zs = np.where(col)[0]
        z0 = int(zs.max()) + 1 if len(zs) else K.SZ
        for z in range(z0, int(la['top_z'])):
            put(K, a, x, 0, z, C['iron'])
    return a


def assemble(K):
    """照 PIECES 的順序：後面的扣掉前面（含船殼）已經有的格；回傳 (pieces, ladder_points, clipped)。"""
    taken = K.hull > 0
    pieces, clipped = {}, {}
    lpts = {}
    builders = {'deck': build_deck, 'apostis': build_apostis, 'rambade': build_rambade, 'spur': build_spur, 'poop': build_poop, 'awning': build_awning}
    for name in PIECES:
        if name == 'ladders':
            a, lpts = build_ladders(K)
        else:
            a = builders[name](K)
        clipped[name] = int(((a > 0) & taken).sum())
        a[taken] = 0
        pieces[name] = a
        taken |= a > 0
    return pieces, lpts, clipped
