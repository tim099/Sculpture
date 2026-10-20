# 東羅馬城牆 1453（TASK-0748）—— 共用工具：調色盤、Model（格子＋固定點）、砌法（石灰岩方石夾紅磚帶）、雉堞、拱。
# 0.2 m／格（城牆是巨構：內牆塔 10 × 12 × 20 m，0.1 m 一座就上百萬格）；模型自己帶 mpv，遊戲照它換算（Blockside src/townmodels.py）。
# 城牆模組座標（同 Blocksail docs/BUILDING_SPEC.md §6）：x ＝ 沿牆、y ＝ 橫過牆（−y ＝ 牆外、+y ＝ 城裡）、z ＝ 往上（z 0 ＝ 牆中線那一點的地面，遊戲往下延到地面）。
#   中線 y ＝ Y/2（Y 取偶數）；接口 wall-a 那一格的 −x 面、wall-b 那一格的 +x 面（中線、地面那一層）。
# Model 的寫法照 summit-bourg-fr-01m/design/kit.py（同一套接口），這裡只留城牆用得到的。
import hashlib, math

V = 5                                                     # 一公尺幾格（0.2 m／格）
MPV = 0.2

# ── 調色盤（RGB332 index）──
LIME, LIME_G, LIME_W = 218, 182, 214                      # 石灰岩方石：米白、灰米、暖米（Theodosian 牆面）
BRICK, BRICK_M = 168, 205                                  # 紅磚、磚帶裡粉紅的厚灰漿
MARBLE = 255                                               # 大理石（門框、拱石、海牆牆腳橫嵌的柱身）
PAVE = 182                                                 # 走道、塔頂的鋪石（灰米）
DARK = 36                                                  # 窗洞、射口、門洞深處
WOOD, WOOD_D, IRON = 104, 68, 37
LEAD = 73                                                  # 鉛皮


def h01(*a):
    """決定論的雜湊 [0, 1)（⛔ 不用 random）。"""
    s = ','.join(str(v) for v in a).encode()
    return int(hashlib.md5(s).hexdigest()[:8], 16) / 4294967296.0


class Model:
    def __init__(s, size):
        s.X, s.Y, s.Z = size
        s.cells = {}                                       # (x, y, z) -> color
        s.anchors = {}
        s.oob = 0

    def inb(s, x, y, z):
        return 0 <= x < s.X and 0 <= y < s.Y and 0 <= z < s.Z

    def put(s, x, y, z, c):
        if not s.inb(x, y, z):
            s.oob += 1
            return
        s.cells[(x, y, z)] = c

    def box(s, x0, y0, z0, x1, y1, z1, c):
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    s.put(x, y, z, c)

    def clear(s, x0, y0, z0, x1, y1, z1):
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    s.cells.pop((x, y, z), None)

    def anchor(s, name, x, y, z):
        x, y, z = int(x), int(y), int(z)
        if not s.inb(x, y, z):
            raise ValueError('固定點 %s (%d,%d,%d) 不在框裡 %s' % (name, x, y, z, (s.X, s.Y, s.Z)))
        s.anchors[name] = (x, y, z)


class Masonry:
    """牆面的顏色：石灰岩方石一層 2 格（0.4 m），每 band 格夾一道 3 格的紅磚帶（磚—灰漿—磚）。
    period ＝ 一輪幾格（石＋磚帶）；z_off 讓不同部件的磚帶對得上（同一套用同一個）；irregular ＝ 海牆那種修補過、磚帶間距不齊。"""

    def __init__(s, period=12, z_off=0, irregular=False, salt=''):
        s.period, s.z_off, s.irr, s.salt = period, z_off, irregular, salt

    def band(s, z):
        """z 那一層是不是磚帶：回 0／1／2（磚帶第幾格）或 None。"""
        zz = z + s.z_off
        k, r = divmod(zz, s.period)
        if s.irr:                                          # 海牆：每一輪的磚帶位置挪 0～3 格、偶爾整輪沒有
            if h01('nb', s.salt, k) < 0.2:
                return None
            r = (r + int(h01('sh', s.salt, k) * 4)) % s.period
        return r - (s.period - 3) if r >= s.period - 3 else None

    def color(s, x, z, u_salt=0):
        """沿牆 x（或沿著那一面量的長度）、高 z ⇒ 色。"""
        b = s.band(z)
        if b is not None:
            return BRICK_M if b == 1 else BRICK
        row = (z + s.z_off) // 2                           # 方石一層 2 格
        off = int(h01('ro', s.salt, row) * 4)
        blk = (x + off + u_salt) // 4                      # 一塊方石沿牆 4 格（0.8 m）
        r = h01('bk', s.salt, row, blk)
        if z < 6 and r < 0.5:
            return LIME_G                                  # 牆腳偏髒
        return LIME if r < 0.72 else (LIME_G if r < 0.9 else LIME_W)


def merlons(M, x0, x1, y0, y1, z0, h, crenel_h, period=10, solid=6, cap=None, mason=None, along='x'):
    """雉堞：從 z0 起 h 格高的垛牆（y0..y1 厚），每 period 格一垛（垛寬 solid），垛口從 z0 + h − crenel_h 起切掉。
    along ＝ 'x'（垛沿 x 排）或 'y'。"""
    for a in range(x0, x1) if along == 'x' else range(y0, y1):
        merlon = ((a - (x0 if along == 'x' else y0)) % period) < solid
        for b in range(y0, y1) if along == 'x' else range(x0, x1):
            x, y = (a, b) if along == 'x' else (b, a)
            for z in range(z0, z0 + h):
                if not merlon and z >= z0 + h - crenel_h:
                    continue
                top = (z == z0 + h - 1) or (not merlon and z == z0 + h - crenel_h - 1)
                c = (cap if top and cap is not None else (mason.color(a, z) if mason else LIME))
                M.put(x, y, z, c)


def arch_cut(M, xc, half, spring, y0, y1, ring=0, ring_col=None, alt=None, fill_dark=False):
    """沿 y（y0..y1）挖一個半圓拱的洞：中心 xc（格心座標 xc 是洞的中線）、半寬 half、起拱高 spring。
    ring > 0 ⇒ 拱外一圈 ring 格厚的拱石（y0 那一面），alt ＝ 兩色交替（東羅馬的紅磚白石拱）。fill_dark ⇒ 洞底那一面塗暗（只是窗、不是門洞）。"""
    for x in range(int(xc - half - ring - 1), int(xc + half + ring + 2)):
        dx = x + 0.5 - xc
        for z in range(0, spring + half + ring + 2):
            dz = max(0.0, z + 0.5 - spring)
            d = math.hypot(dx, dz) if z >= spring else abs(dx)
            inside = d < half
            if inside:
                for y in range(y0, y1):
                    M.cells.pop((x, y, z), None)
            elif ring and d < half + ring and z >= spring - 1 and (x, y0, z) in M.cells:
                ang = math.degrees(math.atan2(dz, dx)) if z >= spring else 0
                c = ring_col if alt is None else (alt[0] if int(ang // 18) % 2 == 0 else alt[1])
                M.cells[(x, y0, z)] = c
    if fill_dark:
        for x in range(int(xc - half - 1), int(xc + half + 2)):
            dx = x + 0.5 - xc
            for z in range(0, spring + half + 1):
                dz = max(0.0, z + 0.5 - spring)
                d = math.hypot(dx, dz) if z >= spring else abs(dx)
                if d < half:
                    M.put(x, y1, z, DARK)


def opening(M, axis, plane, inward, a0, a1, z0, z1, depth, arch=True, brick=True, dark=True):
    """在 axis 面（'y' ＝ y＝plane 那一面、沿 x 排；'x' ＝ x＝plane 那一面、沿 y 排）挖一個開口：沿面 a0..a1、高 z0..z1，
    往 inward（+1／−1）挖 depth 格；dark ⇒ 洞底那一格塗暗（窗）；arch ⇒ 頂上半圓；brick ⇒ 開口頂上一圈紅磚拱（只塗在那一面）。"""
    w = a1 - a0
    half = w / 2.0
    spring = z1 - int(round(half)) if arch else z1
    ac = a0 + half

    def xy(a, k):
        p = plane + inward * k
        return (a, p) if axis == 'y' else (p, a)

    for a in range(a0 - 2, a1 + 2):
        da = a + 0.5 - ac
        for z in range(z0, z1 + 3):
            if arch and z >= spring:
                d = math.hypot(da, z + 0.5 - spring)
            else:
                d = abs(da) if z < z1 else 99
            if d < half and z >= z0:
                for k in range(depth):
                    M.cells.pop(xy(a, k) + (z,), None)
                if dark:
                    M.put(*(xy(a, depth) + (z, DARK)))
            elif brick and arch and z >= spring and d < half + 1.6:
                k = xy(a, 0) + (z,)
                if k in M.cells:
                    M.cells[k] = BRICK
