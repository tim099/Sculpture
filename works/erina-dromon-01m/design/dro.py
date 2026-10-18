# 持火號（拜占庭 dromon）設計模組：plan.json 的參數 ⇒ 連續幾何（半寬、舷弧、龍骨線、艏艉柱）＋ 格子工具。
# 座標：X 船長、船頭朝 +X；Y 船寬、中線格 y = YC（格 y ↔ 2·YC − y）；Z 高度、z 0 ＝ 龍骨底面。格 k 佔 [k, k+1)、中心 k+0.5。
# 每個數字的出處寫在 plan.json 的 provenance（參考資料／設計決定）。
import os, json, math
import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
NX, NY, NZ = PLAN['frame']['size']
YC = PLAN['frame']['yc']          # 中線那一格
YM = YC + 0.5                     # 連續座標的中線
H = PLAN['hull']


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


# ── 龍骨線（船殼底的上緣 ＝ 龍骨頂）：船中平、兩頭往上翹進艏柱／艉柱 ──
def keel_top(x):
    k = H['keel']
    if x >= k['flat_fwd']:
        t = (x - k['flat_fwd']) / (H['stem']['x_foot'] - k['flat_fwd'])
        return k['z_top'] + (H['stem']['z_foot'] - k['z_top']) * t ** k['rocker_pow']
    if x <= k['flat_aft']:
        t = (k['flat_aft'] - x) / (k['flat_aft'] - H['stern']['x_foot'])
        return k['z_top'] + (H['stern']['z_foot'] - k['z_top']) * t ** k['rocker_pow']
    return k['z_top']


# ── 船頭、船尾在高度 z 的端點（艏柱前傾成弧、艉柱往後上翹成弧）──
def end_fwd(z):
    s = H['stem']
    t = min(1.0, max(0.0, (z - s['z_foot']) / (s['z_head'] - s['z_foot'])))
    return s['x_foot'] + (s['x_head'] - s['x_foot']) * (1 - (1 - t) ** s['curve'])


def end_aft(z):
    s = H['stern']
    t = min(1.0, max(0.0, (z - s['z_foot']) / (s['z_head'] - s['z_foot'])))
    return s['x_foot'] + (s['x_head'] - s['x_foot']) * (1 - (1 - t) ** s['curve'])


# ── 舷弧：船邊甲板面的高度（z ＝ 甲板面上第一層空氣的那一格的下緣）──
def sheer(x):
    s = H['sheer']
    xm = s['x_low']
    if x >= xm:
        t = (x - xm) / (s['x_fwd'] - xm)
        return s['z_mid'] + s['rise_fwd'] * max(0.0, t) ** s['pow_fwd']
    t = (xm - x) / (xm - s['x_aft'])
    return s['z_mid'] + s['rise_aft'] * max(0.0, t) ** s['pow_aft']


# ── 船中剖面的半寬（格；z 從龍骨頂量的相對高度 h）──
def hb_mid(h):
    """船中剖面的半寬（格）。h ＝ 從龍骨頂量的高度。
    圓舭（keel_half → half_bilge @ bilge_h）→ 直舷（→ half_side @ side_h，下層槳口那一帶）→ 外張（→ half_top @ top_h，Pryor 的 flared upper hull）→ 舷牆直立（掛盾）。"""
    m = H['mid']
    if h <= 0:
        return m['keel_half']
    if h <= m['bilge_h']:
        t = h / m['bilge_h']
        return m['keel_half'] + (m['half_bilge'] - m['keel_half']) * (1 - (1 - t) ** m['bilge_p']) ** (1 / m['bilge_p'])
    if h <= m['side_h']:
        t = (h - m['bilge_h']) / (m['side_h'] - m['bilge_h'])
        return m['half_bilge'] + (m['half_side'] - m['half_bilge']) * t
    if h <= m['top_h']:
        t = (h - m['side_h']) / (m['top_h'] - m['side_h'])
        return m['half_side'] + (m['half_top'] - m['half_side']) * smooth(t)
    return m['half_top']


# ── 半寬 hb(x, z)：船中剖面 × 沿船長的豐滿度；兩端收到 0 ──
def hb(x, z):
    xf, xa = end_fwd(z), end_aft(z)
    if x >= xf or x <= xa:
        return -1.0
    zk = keel_top(x)
    h = z - zk
    if h < 0:
        return -1.0
    xm = H['x_mid']
    F = H['full']
    u = smooth(h / H['mid']['top_h'])                 # 水線下尖瘦、水線上豐滿（上半的豐滿度指數比較大）
    if x >= xm:
        xi = (x - xm) / (xf - xm); a, b = F['a_fwd'] + (F['a_fwd_top'] - F['a_fwd']) * u, F['b_fwd']
    else:
        xi = (xm - x) / (xm - xa); a, b = F['a_aft'] + (F['a_aft_top'] - F['a_aft']) * u, F['b_aft']
    f = (1 - min(1.0, xi) ** a) ** b
    # 兩頭的剖面比較瘦也比較「V」：舭高照龍骨上翹的量縮
    w = hb_mid(h) * f
    return max(w, H['mid']['keel_half'] * min(1.0, 4 * (1 - xi))) if xi < 1 else -1.0


def inside_hull(x, y, z):
    """格 (x, y, z) 的格心在船殼外形裡（含殼本身）。上限 ＝ 舷弧。"""
    cx, cz = x + 0.5, z + 0.5
    if cz > sheer(cx) + H['bulwark']['h'] + 0.0:
        return False
    w = hb(cx, cz)
    return w >= 0 and abs(y + 0.5 - YM) <= w + 0.5


# ── 顏色（RGB332 索引）──
C = PLAN['colors']


def rgb332(i):
    r, g, b = (i >> 5) & 7, (i >> 2) & 7, i & 3
    return (round(r * 255 / 7), round(g * 255 / 7), round(b * 255 / 3))


# ── 清單工具 ──
def write_list(path, cells, header=''):
    """cells：{(x,y,z): color}；照 (x,y,z) 排序寫成 stampvox 清單，回傳格數。"""
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        if header:
            for ln in header.splitlines():
                f.write('# ' + ln + '\n')
        for (x, y, z) in sorted(cells):
            f.write('%d,%d,%d,%d\n' % (x, y, z, cells[(x, y, z)]))
    return len(cells)


def mirror_y(y):
    return 2 * YC - y
