# 加拉塔塔 1453（TASK-0748）—— 照 plan.json 產格子：塔身（body）、屋頂與頂飾（roof）兩層。
# 座標（Blocksail docs/BUILDING_SPEC.md §1，0.2 m／格）：x ＝ 臨路寬、y ＝ 進深（y 0 ＝ 正面 ＝ 城外、北）、z ＝ 往上（z 0 ＝ 整平面）。
#   作品框 ＝ 地塊 32 × 32 m ⇒ 160 × 160 × 225；塔中心在框的中心 (80, 80)（格 k 佔 [k, k+1)，格心 k + 0.5）。
#   角度 ang ＝ atan2(y − 80, x − 80)（度）：−90 ＝ 正面（北、城外）、+90 ＝ 背面（南、城裡）。
# 決定論：只用 h01（md5）挑色與位置（⛔ random）。numpy 一次算整個框。
import json, math, os, hashlib, functools
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
MPV = P['mpv']
X, Y, Z = (int(round(v / MPV)) for v in P['frame_m'])
CX = CY = X / 2.0
T, B, C = P['tower'], P['barbican'], P['colors']
K = int(round(0.2 / MPV))                                       # 第一版照 0.2 m／格寫的「格數」都乘 K（0.1 m ⇒ 2；Tim 2026-11-05「可以改成0.1m一格」）⇒ mpv 0.2 時逐格跟以前相同


def h01(*a):
    return int(hashlib.md5(','.join(map(str, a)).encode()).hexdigest()[:8], 16) / 4294967296.0


def zc(m):                                                     # 公尺 ⇒ 第幾層格（取整到格）
    return int(round(m / MPV))


STONES = sorted(((int(k), v) for k, v in C['stone'].items()), key=lambda kv: kv[0])
CUM = np.cumsum([v for _, v in STONES]); CUM = CUM / CUM[-1]


@functools.lru_cache(maxsize=None)
def stone_color(course, block, salt):
    r = h01('st', salt, course, block)
    return STONES[int(np.searchsorted(CUM, r, side='right'))][0] if r < 1 else STONES[-1][0]


def build():
    G = np.zeros((Z, Y, X), np.uint8)                          # 色
    LAY = np.zeros((Z, Y, X), np.uint8)                        # 1 ＝ body、2 ＝ roof、3 ＝ 砲甲板（3 層樓板）、4 ＝ 頂層甲板、5 ＝ 梯子、6 ＝ 火藥間
    yy, xx = np.mgrid[0:Y, 0:X]
    dx, dy = xx + 0.5 - CX, yy + 0.5 - CY
    R = np.hypot(dx, dy) * MPV                                 # 公尺
    A = np.degrees(np.arctan2(dy, dx))                         # −180..180
    zi = np.arange(Z)

    # ── 砌法：一層一層（0.4～0.6 m）不規則的石塊，沿周長 0.6～1.2 m 一塊；照 (層, 塊) 挑色 ──
    course_of = np.zeros(Z, int); z = 0; k = 0
    while z < Z:
        hgt = K * (2 + int(h01('ch', k) * 2))                  # 0.4～0.6 m
        course_of[z:z + hgt] = k; z += hgt; k += 1
    ncourse = k
    blen = [K * (3 + int(h01('bl', c) * 4)) for c in range(ncourse)]  # 一塊 0.6～1.2 m
    boff = [K * int(h01('bo', c) * 6) for c in range(ncourse)]

    def masonry(z, mask, radius, salt):
        c = course_of[z]
        s = (np.radians(A) + math.pi) * radius / MPV          # 沿周長的格數
        blk = ((s + boff[c]) // blen[c]).astype(int)
        cols = np.vectorize(lambda b: stone_color(c, b, salt))(blk[mask]) if mask.any() else []
        return cols

    r_o0, r_i = T['r_out'], T['r_in']
    z_top = zc(T['masonry_top'])
    irr_top = zc(T['genoese_irregular_top'])
    # 平面不規則（4 層以下）：外圈半徑照角度慢慢起伏 ±0.12 m（16 段平滑）
    wob = np.zeros_like(R)
    for j in range(6):
        wob += 0.05 * math.sin(math.radians(h01('wp', j) * 360)) * np.cos(np.radians(A) * (j + 2) + h01('wq', j) * 6.28)
    bricks = set()
    for zz in T['brick_courses']:
        bricks |= set(range(zc(zz), zc(zz) + 2 * K))
    for z in range(0, z_top):
        zm = (z + 0.5) * MPV
        ro = r_o0 + (T['talus_dr'] * (1 - zm / T['talus_h']) if zm < T['talus_h'] else 0)
        if z < irr_top:
            ro = ro + wob
        m = (R >= r_i) & (R < ro)
        if z in bricks:
            G[z][m] = np.where(((xx // K + yy // K + z // K) % 5 == 0)[m], C['mortar'], C['brick'])
        else:
            G[z][m] = masonry(z, m, r_o0, 't')
        LAY[z][m] = 1
    # 樓板（裡面）：地面層＋各層
    for fz in [0.0] + T['floors']:
        z = zc(fz)
        m = R < r_i
        G[z:z + K, m] = C['floor']; LAY[z:z + K, m] = 1

    def carve(mask3):                                          # mask3：(z, y, x) ⇒ 清掉
        G[mask3] = 0; LAY[mask3] = 0

    def perp(a0):                                              # 離「角度 a0 那條半徑線」的垂直距離（公尺）；背面那一半給大數
        ar = math.radians(a0); d = np.abs(dx * math.sin(ar) - dy * math.cos(ar)) * MPV
        return np.where(dx * math.cos(ar) + dy * math.sin(ar) > 0, d, 99.0)

    def arc_s(a0):                                             # 角度差 ⇒ 沿外牆的弧長（公尺）
        d = (A - a0 + 180) % 360 - 180
        return np.radians(d) * r_o0

    # ── 開口 ──
    # 門（地面層、朝城裡）：凹進 0.6 m 的圓拱、木門
    D = T['door']; s = arc_s(D['angle']); hw = D['w'] / 2; spring = D['h'] - hw
    for z in range(0, zc(D['h']) + 1):
        zm = (z + 0.5) * MPV
        inside = (np.abs(s) < hw) & ((zm < spring) | (np.hypot(s, zm - spring) < hw))
        rec = inside & (R >= r_o0 - 0.6) & (R < r_o0 + T['talus_dr'] + 0.3)
        G[z][rec] = 0; LAY[z][rec] = 0
        leaf = inside & (R >= r_o0 - 0.8) & (R < r_o0 - 0.6)
        G[z][leaf] = np.where(((xx // K + z // K) % 7 == 0)[leaf], C['iron'], C['door']); LAY[z][leaf] = 1
        ring = (~inside) & (np.abs(s) < hw + 0.3) & (zm < D['h'] + 0.3) & (R >= r_o0 - 0.6) & (R < r_o0 + 0.05) & (G[z] > 0)
        G[z][ring] = C['brick']
    # 3 層的大射口（砲眼）：穿過整個牆厚
    E = T['embrasures']
    for a in E['angles']:
        s = perp(a)
        for z in range(zc(E['z0']), zc(E['z0'] + E['h'])):
            carve_m = (s < E['w'] / 2 + (R - r_i) * 0.08) & (R >= r_i - 0.01) & (R < r_o0 + 1)
            G[z][carve_m & (LAY[z] == 1) & (R >= r_i)] = 0; LAY[z][carve_m & (R >= r_i)] = 0
    # 不規則的窄射口（4 層以下，每層 4 道，深、窄、底斜）：位置照雜湊、避開門與砲眼
    SI = T['slits_irregular']; levels = [0.0] + [f for f in T['floors'] if f < T['genoese_irregular_top']]
    avoid = [D['angle']] + E['angles']
    for li in range(len(levels) - 1):
        z0, z1 = levels[li], levels[li + 1]
        if z1 - z0 < 2.5: continue
        n = 0; tries = 0
        while n < SI['per_floor'] and tries < 40:
            tries += 1
            a = -180 + 360 * h01('sa', li, tries)
            if any(abs((a - b + 180) % 360 - 180) < 22 for b in avoid): continue
            hh = SI['h'][0] + (SI['h'][1] - SI['h'][0]) * h01('sh', li, tries)
            zb = z0 + 1.0 + (z1 - z0 - 1.0 - hh) * h01('sz', li, tries)
            s = perp(a)
            for z in range(zc(zb), zc(zb + hh)):
                zm = (z + 0.5) * MPV
                sill = (R - r_i) / (r_o0 - r_i)                # 底斜：外面低、裡面高
                cut = (s < 0.11 + (r_o0 - R).clip(0) * 0.03) & (R >= r_i) & (R < r_o0 + 1) & (zm >= zb + (1 - sill) * 0.4)
                G[z][cut] = 0; LAY[z][cut] = 0
            avoid.append(a); n += 1
    # 規則的射口（4 層以上）：8 道等間距
    SR = T['slits_regular']
    for j in range(SR['n']):
        a = -180 + (j + 0.5) * 360 / SR['n']
        s = perp(a)
        for z in range(zc(SR['z0']), zc(SR['z0'] + SR['h'])):
            cut = (s < 0.11 + (r_o0 - R).clip(0) * 0.03) & (R >= r_i) & (R < r_o0 + 1)
            G[z][cut] = 0; LAY[z][cut] = 0
    # 頂層一圈盲拱：凹進 depth、磚拱券
    AR = T['arcade']; ns = AR['n']; hw = AR['w'] / 2; spring = AR['z1'] - hw
    for j in range(ns):
        a = -180 + (j + 0.5) * 360 / ns
        s = arc_s(a)
        for z in range(zc(AR['z0']), zc(AR['z1']) + 3 * K):
            zm = (z + 0.5) * MPV
            inside = (np.abs(s) < hw) & ((zm < spring) | (np.hypot(s, zm - spring) < hw)) & (zm >= AR['z0'])
            rec = inside & (R >= r_o0 - AR['depth']) & (R < r_o0 + 0.05)
            G[z][rec] = 0; LAY[z][rec] = 0
            back = inside & (R >= r_o0 - AR['depth'] - MPV) & (R < r_o0 - AR['depth'])
            G[z][back] = 146
            ring = (~inside) & (zm >= spring) & (np.hypot(s, zm - spring) < hw + 0.3) & (R >= r_o0 - MPV) & (R < r_o0 + 0.05) & (G[z] > 0)
            G[z][ring] = C['brick']
    # 托石一圈（外挑 out）
    CO = T['corbel']; nc = CO['n']
    for z in range(zc(CO['z0']), zc(CO['z1'])):
        zm = (z + 0.5) * MPV
        out = CO['out'] * (zm - CO['z0']) / (CO['z1'] - CO['z0']) + 0.1
        sec = ((A + 180) * nc / 360) % 1
        m = (R >= r_o0 - 0.4) & (R < r_o0 + out) & ((sec < 0.5) | (R < r_o0))
        G[z][m] = 182; LAY[z][m] = 1
    # 雉堞（外挑在托石上）
    PA = T['parapet']; ro, rin = r_o0 + CO['out'], r_o0 + CO['out'] - PA['t']
    gunc = np.zeros_like(R, bool)                              # 頂層架武器的地方：垛口連同兩邊的牆垛開成一個砲口（± gun_open_deg）、挖到 deep_sill（武器角度 ＝ 垛口中心，plan armament.top）
    for w in P['armament']['top']:                             #   只開一個垛口寬 ⇒ 重弩轉 ±30° 時砲口射線撞牆垛（gunclear 量的）
        gunc |= np.abs((A - w['a'] + 180) % 360 - 180) < P['armament']['gun_open_deg']
    for z in range(zc(PA['z0']), zc(PA['z0'] + PA['h'])):
        zm = (z + 0.5) * MPV
        sec = ((A + 180) * PA['n'] / 360) % 1
        crenel = ((sec >= 0.6) & (zm >= PA['z0'] + PA['h'] - PA['crenel_h'])) | (gunc & (zm >= PA['z0'] + P['armament']['deep_sill']))
        m = (R >= rin) & (R < ro) & ~crenel
        cols = masonry(z, m, ro, 'p')
        G[z][m] = cols; LAY[z][m] = 1
        top = m & ((zm + MPV >= PA['z0'] + PA['h']) | ((sec < 0.6) & False))
        G[z][top] = 182
        cap = (R >= rin) & (R < ro) & (sec >= 0.6) & ~gunc & (zc(PA['z0'] + PA['h'] - PA['crenel_h']) - K <= z) & (z < zc(PA['z0'] + PA['h'] - PA['crenel_h']))
        G[z][cap] = 182
    # 屋頂底下的鼓座（撐住屋頂、接到塔頂）：站在內牆線上、開四道門 ⇒ 鼓座與雉堞之間是一圈屋簷蓋著的走道（頂層砲台，TASK-1025）
    DR = T['drum']
    for z in range(z_top, zc(T['roof']['z_eave'])):
        zm = (z + 0.5) * MPV
        m = (R >= DR['r0']) & (R < DR['r0'] + DR['t'])
        if zm < z_top * MPV + DR['door_h']:
            for a in DR['doors']:
                m = m & (np.abs(np.radians((A - a + 180) % 360 - 180)) * DR['r0'] >= DR['door_w'] / 2)
        G[z][m] = masonry(z, m, DR['r0'], 'd'); LAY[z][m] = 1
    # 塔頂的地面 ＝ 頂層甲板（第一版裡面那塊 LAY 沒標 ⇒ 樓板被丟掉、從屋頂底下直落到 25.5 m；TASK-1025 量到）：裡面的樓板＋牆頂那一層
    G[z_top - K:z_top, R < rin] = 182
    LAY[z_top - K:z_top][:, (R < rin)] = np.where(G[z_top - K:z_top][:, (R < rin)] > 0, 4, LAY[z_top - K:z_top][:, (R < rin)])
    # 3 層樓板 ＝ 砲甲板
    AM = P['armament']
    zg = zc(AM['gundeck_floor'])
    for z in range(zg, zg + K):
        LAY[z][(R < r_i) & (G[z] > 0)] = 3
    # 直梯的井：穿過 4、5 層樓板與頂層樓板（3 層 ⇒ 頂層）
    HA = AM['hatch']
    hx0, hx1 = int(round(CX + (HA['x'] - HA['w'] / 2) / MPV)), int(round(CX + (HA['x'] + HA['w'] / 2) / MPV))
    hy0, hy1 = int(round(CY + (HA['y'] - HA['d'] / 2) / MPV)), int(round(CY + (HA['y'] + HA['d'] / 2) / MPV))
    for z0 in [zc(f) for f in T['floors'] if f > AM['gundeck_floor']] + [z_top - K]:
        G[z0:z0 + K, hy0:hy1, hx0:hx1] = 0; LAY[z0:z0 + K, hy0:hy1, hx0:hx1] = 0
    # 梯子（木）：靠井的西緣，兩根立柱、每 2 格一道橫檔，從砲甲板一路到頂層樓板
    lz0, lz1 = zg + K, z_top
    for z in range(lz0, lz1):
        for y in (hy0 + K, hy1 - 2 * K):
            G[z, y:y + K, hx0:hx0 + K] = C['door']; LAY[z, y:y + K, hx0:hx0 + K] = 5
        if ((z - lz0) // K) % 2 == 1:
            G[z, hy0 + 2 * K:hy1 - 2 * K, hx0:hx0 + K] = C['door']; LAY[z, hy0 + 2 * K:hy1 - 2 * K, hx0:hx0 + K] = 5
    yc = (hy0 + hy1) // 2
    ladder = {'L1.foot': (hx0 + K, yc, lz0), 'L1.lo': (hx0 + K, yc, lz0 + K), 'L1.hi': (hx0 + K, yc, lz1 - K), 'L1.head': (hx1, yc, lz1)}
    # 火藥間（砲甲板南邊、背對砲眼）：三面木板圍起來、口朝塔心
    MG = AM['magazine']
    mcx, mcy = CX + MG['r'] * math.cos(math.radians(MG['a'])) / MPV, CY + MG['r'] * math.sin(math.radians(MG['a'])) / MPV
    mx0, mx1 = int(round(mcx - MG['w'] / 2 / MPV)), int(round(mcx + MG['w'] / 2 / MPV))
    my0, my1 = int(round(mcy - MG['d'] / 2 / MPV)), int(round(mcy + MG['d'] / 2 / MPV))
    for z in range(zg + K, zg + K + zc(MG['h'])):
        for ys, xs in ((slice(my1 - K, my1), slice(mx0, mx1)), (slice(my0, my1), slice(mx0, mx0 + K)), (slice(my0, my1), slice(mx1 - K, mx1))):
            G[z, ys, xs] = C['door']; LAY[z, ys, xs] = 6
    magazine = {'anchors': {'blast': (int(mcx), int(mcy), zg + 2 * K), 'door': (int(mcx), my0 - K, zg + K)},
                'barrels': [((mx0 + mx1) / 2.0 + (k - (MG['barrels'] - 1) / 2.0) * 4.0 * K, (my0 + my1) / 2.0 - 0.5 * K, zg + K) for k in range(MG['barrels'])]}
    # 武器：照 plan 的角度擺（元件的砲口朝 +y ⇒ 轉 a − 90°）；砲甲板的砲口退到貼著外牆面，頂層的照走道寬（砲口貼著雉堞內面）
    CP = AM['components']

    def place(w, R_at, z):
        c = CP[w['gun']]; a = w['a']
        meta = {'kind': 'gun', 'gun': w['gun'], 'id': w['id']}
        if w['gun'] == 'springald':
            meta.update({'ammo': 'firebolt', 'weapon': 'springald', 'mount': 'pivot', 'ports': '0,20,-20'})
        return {'name': w['name'], 'source': c['work'], 'pivot': list(c['pivot']), 'scale': c['scale'] * K, 'meta': meta,
                'at': [round((CX + R_at * math.cos(math.radians(a)) / MPV) * 2) / 2.0, round((CY + R_at * math.sin(math.radians(a)) / MPV) * 2) / 2.0, z],
                'rotate': [0, 0, ((a - 90) + 180) % 360 - 180]}
    guns_deck = [place(w, r_o0 - CP['bombardella']['len_m'] - 0.15, zc(T['embrasures']['z0'])) for w in AM['gundeck']]
    guns_top = [place(w, rin - (CP['springald']['front_m'] if w['gun'] == 'springald' else CP['bombardella']['len_m']) - 0.05, z_top) for w in AM['top']]
    powder = [{'name': '火藥桶-%d' % (k + 1), 'source': CP['powder']['work'], 'pivot': [11, 11, 0], 'scale': CP['powder']['scale'] * K, 'rotate': [0, 0, 0],
               'at': [b[0], b[1], b[2]], 'meta': {'kind': 'powder', 'powder_lb': 100}} for k, b in enumerate(magazine['barrels'])]
    armament = {'gundeck': {'floor': '%d:%d,%d:%d' % (int(CX - r_i / MPV), zg + K, int(CX + r_i / MPV), zg + K), 'models': guns_deck},
           'top': {'floor': '%d:%d,%d:%d' % (int(CX - rin / MPV), z_top, int(CX + rin / MPV), z_top), 'models': guns_top},
           'ladder': ladder, 'magazine': {'anchors': magazine['anchors'], 'models': powder, 'powder_lb': 100 * MG['barrels']}}
    # ── 屋頂：實心圓錐（鉛皮、每 15° 一道接縫），簷伸出雉堞外 ──
    RF = T['roof']; ze, re_, rh = RF['z_eave'], RF['r_eave'], RF['h']
    for z in range(zc(ze), zc(ze + rh) + 1):
        zm = (z + 0.5) * MPV
        rc = re_ * (1 - (zm - ze) / rh)
        if rc <= 0: break
        m = R < rc
        seam = (((A + 180) / 15) % 1 < 0.08) | (z == zc(ze))
        G[z][m] = np.where(seam[m], C['roof_seam'], C['roof']); LAY[z][m] = 2
    # 頂飾：旗杆（鐵）、帶十字的金球、熱那亞旗（白底紅十字）
    FI = T['finial']; apex = zc(ze + rh)
    px, py = int(CX) - K, int(CY) - K
    pole_top = apex + zc(FI['pole_h'])
    for z in range(apex - 2 * K, pole_top):
        G[z, py:py + 2 * K, px:px + 2 * K] = C['iron']; LAY[z, py:py + 2 * K, px:px + 2 * K] = 2
    ob = zc(FI['orb_r'])
    for z in range(pole_top, pole_top + 2 * ob + 1):
        for y in range(py - ob, py + ob + 2):
            for x in range(px - ob, px + ob + 2):
                if math.hypot(x + 0.5 - (px + K), y + 0.5 - (py + K), z + 0.5 - (pole_top + ob)) <= ob + 0.5:
                    G[z, y, x] = C['gold']; LAY[z, y, x] = 2
    cz0 = pole_top + 2 * ob; ch = zc(FI['cross_h'])               # 從金球最上面那一層的上面一格開始（差一層 ⇒ 十字架浮空 64 格，第一版量到的）
    G[cz0:cz0 + ch, py:py + 2 * K, px:px + 2 * K] = C['gold']; LAY[cz0:cz0 + ch, py:py + 2 * K, px:px + 2 * K] = 2
    arm = cz0 + int(ch * 0.6)
    G[arm:arm + 2 * K, py:py + 2 * K, px - 3 * K:px + 5 * K] = C['gold']; LAY[arm:arm + 2 * K, py:py + 2 * K, px - 3 * K:px + 5 * K] = 2
    # 熱那亞旗：不雕格子 ⇒ 布（同船的旗：work sub=sail、meta kind=flag；Tim 2026-10-20「旗幟可以改成布?(參考船隻)」）。這裡只給旗杆上的兩個固定點（旗的綁邊）
    fw, fh = zc(FI['flag'][0]), zc(FI['flag'][1])
    fz0 = pole_top - fh - 1
    # ── 1452 年的半圓外堡（faussebraye）：塔前（城外）一道弧牆，兩端接城牆 ──
    a0, a1 = B['a0'], B['a1']
    Aw = np.where(A > 0, A - 360, A)                           # (−360, 0]
    sect = (Aw <= a0) & (Aw >= a1)
    for z in range(0, zc(B['h'])):
        zm = (z + 0.5) * MPV
        m = sect & (R >= B['r'] - B['t'] / 2) & (R < B['r'] + B['t'] / 2)
        if zm >= B['h'] - B['crenel_h']:
            sec = ((Aw * B['r'] * math.pi / 180) / 1.6) % 1
            m = m & (sec < 0.6)
        G[z][m] = masonry(z, m, B['r'], 'b'); LAY[z][m] = 1
        if zm + MPV >= B['h'] or (zm + MPV >= B['h'] - B['crenel_h'] and zm < B['h'] - B['crenel_h']):
            G[z][m] = 182
    anchors = {'lot-0': (0, 0, 0), 'door': (int(CX), int(CY + (r_o0 + T['talus_dr'] + 0.4) / MPV), 0),
               'flag': (px, py, pole_top - 1),
               'flag-top': (px + 2 * K, py, fz0 + fh), 'flag-bottom': (px + 2 * K, py, fz0)}      # 旗的綁邊：旗杆東邊那一格（空氣），上、下
    anchors.update({k: tuple(c * K + K // 2 for c in v) for k, v in T['work_spots_02m'].items()})   # 站崗點（d0eef894／740fbd2e 用 CLI 加在 0.2 m 格上的）⇒ 跟著比例換算
    sail = {'name': 'genoa-flag', 'hoist': ('flag-top', 'flag-bottom'), 'fly': [(px + 2 * K + fw, py, fz0), (px + 2 * K + fw, py, fz0 + fh)]}
    return G, LAY, anchors, sail, armament


if __name__ == '__main__':
    G, L, a, _, arm = build()
    print('格數', int((G > 0).sum()), ' '.join('%s %d' % (k, int((L == i).sum())) for i, k in enumerate(('', 'body', 'roof', 'gundeck', 'top', 'ladder', 'magazine')) if i), a)
    print(json.dumps(arm, ensure_ascii=False))
