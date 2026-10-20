# 大競技場 1453 的格子（TASK-0748）：照 plan.json 產生；numpy、決定論（同一份 plan ⇒ 逐格相同）。build.py 呼叫 build()。
#   抄聖索菲亞 kaguya-hagia-sophia-1453/design/sophia.py 的做法（量體先當實心 ⇒ 只留離空氣 shell 格內的、底面當地面不算空氣）；改：格座標直接用格（不經研究座標）、
#   殘破照種子分段、三件子作品（看台／半圓端柱廊／中線與碑柱）。
# 座標：陣列 [z, y, x]；格心 x + 0.5。見 plan.json frame_note。
import os, json, math, random
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
MPV = P['mpv']
NX, NY, NZ = P['frame']['nx'], P['frame']['ny'], P['frame']['nz']
C = P['colors']
STANDS, SPHENDONE, SPINA = 1, 2, 3
SHELL = 2                                    # 留離空氣 2 格內（0.8 m）

X = (np.arange(NX) + 0.5)[None, None, :]
Y = (np.arange(NY) + 0.5)[None, :, None]
Z = (np.arange(NZ) + 0.5)[:, None, None]
XC = P['outer']['half_w']                    # 中線 x ＝ 162.5
YS = P['outer']['straight_to']               # 半圓端圓心 y ＝ 962.5


def put(G, L, sel, color, part, over=True):
    sel = np.broadcast_to(sel, G.shape)
    m = sel if over else (sel & (G == 0))
    G[m] = color
    L[m] = part


def stands(G, L):
    S, O, T = P['stands'], P['outer'], P['track']
    s = np.abs(X - XC) - T['half_w']                     # 離跑道邊往外幾格
    tier = np.floor((s - 2) / S['tier_w'])
    h = np.where(s < 2, S['podium_h'], S['podium_h'] + (np.clip(tier, -1, S['tiers'] - 1) + 1) * S['tier_h'])
    wall = (s >= O['half_w'] - T['half_w'] - S['wall_t']) & (s < O['half_w'] - T['half_w'])
    h = np.where(wall, S['wall_h'], h)
    h = np.where(s < 0, 0, h)                            # (1, 1, NX)
    # 殘破：每一側、每 seg 格一段，照種子挑 完整／上層塌／只剩低的；段內上緣 ±2 格的鋸齒
    R = S['ruin']; nseg = int(math.ceil(NY / R['seg']))
    cap = np.full((NY, NX), 1e9)
    for side in (0, 1):
        rnd = random.Random('%d:%d' % (R['seed'], side))
        for k in range(nseg):
            u = rnd.random()
            keep = 1.0 if u < R['full'] else (rnd.uniform(*R['top_keep']) if u < R['full'] + R['top_cut'] else R['low_keep'])
            jag = [rnd.randint(-2, 2) for _ in range(R['seg'])]
            if keep >= 1.0:
                continue
            for j in range(R['seg']):
                y = k * R['seg'] + j
                if y >= NY:
                    break
                xs = slice(0, int(XC)) if side == 0 else slice(int(XC), NX)
                cap[y, xs] = keep * S['wall_h'] + jag[j]
    hh = np.minimum(np.broadcast_to(h[0], (NY, NX)), cap)
    yin = (Y >= S['y0']) & (Y < YS)
    solid = (Z < hh[None]) & yin
    # 外牆外面的拱（拱室）：沿 y 每 pitch 一個，深 depth、底下是長方、上面半圓
    A = S['arch']; rr = A['w'] / 2.0
    ym = (Y - S['y0']) % A['pitch'] - A['pitch'] / 2.0
    archz = (A['h'] - rr) + np.sqrt(np.clip(rr * rr - ym * ym, 0, None))
    sOut = O['half_w'] - np.abs(X - XC)                  # 離外緣往裡幾格
    arch = (np.abs(ym) < rr) & (Z < archz) & (sOut < A['depth']) & yin
    dark = (np.abs(ym) < rr) & (Z < archz) & (sOut >= A['depth']) & (sOut < A['depth'] + 1) & yin
    solid &= ~arch
    col = np.where(np.broadcast_to(wall, solid.shape), np.where((np.floor(Z) % S['band_every']) == 0, C['band'], C['brick']), 0)
    top = solid & ~np.roll(solid, -1, axis=0)
    col = np.where(col == 0, np.where(top, C['seat'], C['seat_dark']), col)
    put(G, L, solid, 0, STANDS)
    G[solid] = np.broadcast_to(col, solid.shape)[solid]
    put(G, L, dark & solid, C['dark'], STANDS)
    # 起跑門：北端直牆，門洞穿透、上緣殘破
    K = P['carceres']; rnd = random.Random(K['ruin_seed'])
    x0, x1 = XC - T['half_w'], XC + T['half_w']
    capx = np.array([K['h'] * rnd.uniform(*K['ruin_keep']) for _ in range(int(math.ceil(NX / 25.0)))])
    capc = np.repeat(capx, 25)[:NX][None, None, :] + np.array([rnd.randint(-1, 1) for _ in range(NX)])[None, None, :]
    cw = (Y >= K['y0']) & (Y < K['y0'] + K['t']) & (X >= x0) & (X < x1) & (Z < capc)
    pitch = (x1 - x0) / K['gates']
    xm = (X - x0) % pitch - pitch / 2.0; gr = K['gate_w'] / 2.0
    gate = (np.abs(xm) < gr) & (Z < (K['gate_h'] - gr) + np.sqrt(np.clip(gr * gr - xm * xm, 0, None)))
    cw &= ~gate
    put(G, L, cw, C['brick'], STANDS)
    put(G, L, cw & ((np.floor(Z) % S['band_every']) == 0), C['band'], STANDS)
    # 皇帝包廂（東南側、對著狄奧多西方尖碑）：磚塊、頂上敞廊、上緣殘破
    Q = P['kathisma']; rnd = random.Random('kathisma')
    jag = np.array([rnd.randint(0, Q['ruin_top']) for _ in range(NY)])[None, :, None]
    kb = (X >= Q['x0']) & (X < Q['x1']) & (Y >= Q['y0']) & (Y < Q['y1']) & (Z < Q['h'] - jag)
    yc = (Q['y0'] + Q['y1']) / 2.0; lg = Q['loggia']
    log = (np.abs(Y - yc) < lg['w'] / 2.0) & (Z >= lg['z0']) & (Z < lg['z0'] + lg['h']) & (X >= Q['x1'] - 3)
    logd = (np.abs(Y - yc) < lg['w'] / 2.0) & (Z >= lg['z0']) & (Z < lg['z0'] + lg['h']) & (X >= Q['x1'] - 4) & (X < Q['x1'] - 3)
    kb &= ~log
    put(G, L, kb, C['brick'], STANDS)
    put(G, L, kb & ((np.floor(Z) % S['band_every']) == 0), C['band'], STANDS)
    put(G, L, logd & kb, C['dark'], STANDS)


def sphendone(G, L, anchors):
    S = P['sphendone']; r = S['r']; n = S['cols']
    rnd = random.Random(S['seed'])
    gone = set(rnd.sample(range(1, n - 1), n - S['standing']))
    th = [math.pi * i / (n - 1) for i in range(n)]
    pos = [(XC + r * math.cos(t), YS + r * math.sin(t)) for t in th]
    dx, dy = X - XC, Y - YS
    rad = np.sqrt(dx * dx + dy * dy); ang = np.arctan2(dy, dx)
    bw, cw, cd, chh = S['base']['w'] / 2.0, S['capital']['w'] / 2.0, S['col_d'] / 2.0, S['col_h']
    zb, zc = S['base']['h'], S['base']['h'] + chh
    zt = zc + S['capital']['h']
    for i, (px, py) in enumerate(pos):
        if i in gone:
            continue
        ax, ay = np.abs(X - px), np.abs(Y - py)
        put(G, L, (ax < bw) & (ay < bw) & (Z < zb), C['stone'], SPHENDONE)
        put(G, L, ((X - px) ** 2 + (Y - py) ** 2 < (cd + 0.1) ** 2) & (Z >= zb) & (Z < zc), C['marble'], SPHENDONE)
        put(G, L, (ax < cw) & (ay < cw) & (Z >= zc) & (Z < zt), C['marble'], SPHENDONE)
    # 柱頂的迴廊（簷部）與拱：只接兩根都還在的
    B, Pp = S['beam'], S['parapet']
    for i in range(n - 1):
        if i in gone or (i + 1) in gone:
            continue
        a0, a1 = th[i], th[i + 1]
        seg = (ang >= a0) & (ang <= a1) & (Y >= YS - 0.5)
        band = seg & (np.abs(rad - r) < B['t'] / 2.0)
        put(G, L, band & (Z >= zt) & (Z < zt + B['h']), C['marble'], SPHENDONE)
        put(G, L, seg & (rad >= r + B['t'] / 2.0 - Pp['t']) & (rad < r + B['t'] / 2.0) & (Z >= zt + B['h']) & (Z < zt + B['h'] + Pp['h']), C['marble'], SPHENDONE)
        L_ = r * (a1 - a0); t = r * (ang - a0) - L_ / 2.0
        R_ = L_ / 2.0 - cd - 0.5
        crown = zt - 1
        arch_lo = (crown - R_) + np.sqrt(np.clip(R_ * R_ - t * t, 0, None))
        put(G, L, band & (np.abs(t) < L_ / 2.0) & (Z >= arch_lo) & (Z < zt) & (np.abs(rad - r) < cd), C['marble'], SPHENDONE, over=False)
    anchors['colonnade-mid'] = [int(XC), int(YS + r), int(zt + B['h'])]
    return sorted(gone)


def spina(G, L, anchors):
    S, M = P['spina'], P['monuments']
    put(G, L, (np.abs(X - XC) < S['w'] / 2.0) & (Y >= S['y0']) & (Y < S['y1']) & (Z < S['h']), C['stone'], SPINA)
    put(G, L, (np.abs(X - XC) < S['w'] / 2.0) & (Y >= S['y0']) & (Y < S['y1']) & (Z >= S['h'] - 1) & (Z < S['h']), C['seat'], SPINA)
    cx = math.floor(XC) + 0.5

    def sq(cy, hw, z0, z1, color):
        put(G, L, (np.abs(X - cx) <= hw) & (np.abs(Y - cy) <= hw) & (Z >= z0) & (Z < z1), color, SPINA)

    # 狄奧多西方尖碑（寬度用奇數格：hw ＝ (寬 − 1) / 2）
    T = M['theodosius']; cy = T['y'] + 0.5; z = 0
    for w_, h_, c_ in ((T['steps'][0], T['steps'][1], C['marble']), (T['base1'][0], T['base1'][1], C['marble']), (T['base2'][0], T['base2'][1], C['marble'])):
        sq(cy, (w_ - 1) // 2, z, z + h_, c_); z += h_
    s0, s1, sh = T['shaft']
    for o in (-1, 1):
        for o2 in (-1, 1):
            put(G, L, (np.abs(X - (cx + o * (s0 // 2))) <= 0.5) & (np.abs(Y - (cy + o2 * (s0 // 2))) <= 0.5) & (Z >= z) & (Z < z + T['blocks'][1]), C['bronze'], SPINA)
    z += T['blocks'][1]
    for k in range(sh):
        hw = ((s0 - 1) / 2.0) + ((s1 - 1) / 2.0 - (s0 - 1) / 2.0) * k / (sh - 1)
        sq(cy, round(hw), z + k, z + k + 1, C['granite'])
    z += sh
    for k in range(T['pyramid']):
        sq(cy, (T['pyramid'] - 1 - k) * 0.5, z + k, z + k + 1, C['granite'])
    anchors['obelisk-theodosius-top'] = [int(cx), int(cy), z + T['pyramid']]
    # 蛇柱：三條螺旋、頂上三個頭往外伸
    Sp = M['serpent']; cy = Sp['y'] + 0.5
    sq(cy, (Sp['base'][0] - 1) // 2, 0, Sp['base'][1], C['marble'])
    z0 = Sp['base'][1]
    for k in range(Sp['h']):
        for j in range(3):
            a = 2 * math.pi * Sp['turns'] * k / Sp['h'] + 2 * math.pi * j / 3
            px, py = cx + Sp['coil_r'] * math.cos(a), cy + Sp['coil_r'] * math.sin(a)
            put(G, L, ((X - px) ** 2 + (Y - py) ** 2 < 1.0) & (Z >= z0 + k) & (Z < z0 + k + 1), C['bronze'], SPINA)
    zt = z0 + Sp['h']
    for j in range(Sp['heads']):
        a = 2 * math.pi * Sp['turns'] + 2 * math.pi * j / 3
        for t in range(Sp['head_len'] + 1):
            px, py = cx + (Sp['coil_r'] + t) * math.cos(a), cy + (Sp['coil_r'] + t) * math.sin(a)
            put(G, L, ((X - px) ** 2 + (Y - py) ** 2 < 1.0) & (Z >= zt - 1 + (t > 1)) & (Z < zt + 1), C['bronze'], SPINA)
    anchors['serpent-top'] = [int(cx), int(cy), zt]
    # 砌石方尖碑：三級台階、底座、粗石碑身（銅板剝掉留下的釘孔）
    W = M['walled']; cy = W['y'] + 0.5; z = 0
    for w_, h_ in W['steps']:
        sq(cy, (w_ - 1) // 2, z, z + h_, C['stone']); z += h_
    sq(cy, (W['base'][0] - 1) // 2, z, z + W['base'][1], C['stone']); z += W['base'][1]
    s0, s1, sh = W['shaft']
    for k in range(sh):
        hw = ((s0 - 1) / 2.0) + ((s1 - 1) / 2.0 - (s0 - 1) / 2.0) * k / (sh - 1)
        sq(cy, round(hw), z + k, z + k + 1, C['stone_dark'] if (z + k) % 6 == 0 else C['stone'])
    z += sh
    for k in range(W['pyramid']):
        sq(cy, (W['pyramid'] - 1 - k) * 0.5, z + k, z + k + 1, C['stone'])
    anchors['obelisk-walled-top'] = [int(cx), int(cy), z + W['pyramid']]
    # 中線的散柱
    for i, c in enumerate(M['columns']):
        cy = c['y'] + 0.5
        sq(cy, (c['base'] - 1) // 2, 0, 3, C['marble'])
        put(G, L, ((X - cx) ** 2 + (Y - cy) ** 2 < (c['d'] / 2.0 + 0.1) ** 2) & (Z >= 3) & (Z < 3 + c['h']), C['granite'] if i == 0 else C['marble'], SPINA)
        sq(cy, (c['base'] - 1) // 2, 3 + c['h'], 4 + c['h'], C['marble'])


def hollow(G, L):
    """只留離空氣 SHELL 格內的（底面 z −1 當地面、不算空氣）。"""
    solid = G > 0
    pad = np.pad(solid, ((1, 1), (1, 1), (1, 1)), constant_values=False)
    pad[0] = True                                                       # 地面
    d = ndimage.distance_transform_cdt(pad, metric='taxicab')[1:-1, 1:-1, 1:-1]
    inner = solid & (d > SHELL)
    G[inner] = 0
    L[inner] = 0
    return int(inner.sum())


def build():
    G = np.zeros((NZ, NY, NX), np.uint8)
    L = np.zeros((NZ, NY, NX), np.uint8)
    anchors = {'lot-0': [0, 0, 0], 'gate': [int(XC), 0, 0]}
    stands(G, L)
    gone = sphendone(G, L, anchors)
    spina(G, L, anchors)
    removed = hollow(G, L)
    return G, L, anchors, {'columns_gone': gone, 'hollowed': removed}
