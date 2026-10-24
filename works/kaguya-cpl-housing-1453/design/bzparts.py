# 羅馬（拜占庭）住宅的部件（TASK-0893）—— 每件 ＝ 一件 0.1 m 的子作品 <ROOT>-part-<id>，房子用關聯擺（替換色換得到門、窗板、灰泥的色）。
# 格式同 summit-bourg-fr-01m/design/parts.py：朝外 −y；y 0 ＝ 牆外那一層（拱券、門框、窗台凸出一格）、y 1 ＝ 跟牆外表面齊、y 2 ＝ 往裡一格；z 0 ＝ 開口底。
# socket ＝ 牆上要挖的開口 [(x, z)…]（kit.place() 挖穿牆厚）⇒ y 1、y 2 的格一律落在 socket 裡（不然跟牆撞格）。
# 樣子〔設計〕：遺存只剩牆基、窗的樣子沒有史料（common.py 開頭）；磚石相間的拱券照城牆、灰泥鏤空窗（transenna）照教堂的窗。
from common import *


def P(pid, title, dims, cells, socket, anchors=None, meta=None):
    W, H, D = dims
    for (x, y, z) in cells:
        assert 0 <= x < W and 0 <= y < H and 0 <= z < D, (pid, x, y, z)
    S = set(socket)
    for (x, y, z) in cells:
        assert y == 0 or (x, z) in S, (pid, '牆裡的格不在開口裡', x, y, z)
    return {'id': pid, 'title': title, 'dims': dims, 'cells': cells, 'socket': list(socket), 'anchors': anchors or {}, 'meta': meta or {}}


def _edge(S, x, z):
    return (x - 1, z) not in S or (x + 1, z) not in S or (x, z - 1) not in S or (x, z + 1) not in S


def _ring(v, S, W, D, zs, centers, n=9, z_min=1, reach=2):
    """開口外 reach 格一圈：起拱線以上磚石相間的拱券、以下石灰岩的窗框（y 0）。centers ＝ [(x 範圍上限, 圓心 x)]：照 x 挑最近的那個拱。"""
    for x in range(W):
        for z in range(z_min, D):
            if (x, z) in S:
                continue
            if not any((x + dx, z + dz) in S for dx in range(-reach, reach + 1) for dz in range(-reach, reach + 1)):
                continue
            if z >= zs:
                cx = min(centers, key=lambda c: abs(x + 0.5 - c))
                outer = not any((x + dx, z + dz) in S for dx in range(1 - reach, reach) for dz in range(1 - reach, reach))
                v[(x, 0, z)] = BRICK_R if outer else ring_color(x, z, cx, zs, n)   # 最外一圈磚邊 ⇒ 石塊那幾塊也看得出拱
            else:
                v[(x, 0, z)] = LIME_R


def window():
    """磚拱小窗：0.6 m 寬、半圓拱；拱券磚石相間、石灰岩窗台；開口裡是大理石灰泥的鏤空窗格（transenna）嵌小玻璃。"""
    v = {}
    W, H, D = 12, 3, 18
    S = arch_cells(3, 9, 2, 12)
    SS = set(S)
    _ring(v, SS, W, D, 12, [6.0], n=5)
    for x in range(2, 10):
        v[(x, 0, 1)] = LIME_G                                 # 窗台
    for (x, z) in S:
        if _edge(SS, x, z):
            v[(x, 1, z)] = LIME_R                             # 窗洞側面
        v[(x, 2, z)] = MARBLE if (_edge(SS, x, z) or (x - 3) % 3 == 0 or (z - 2) % 3 == 0) else GLASS
    return P('window', '磚拱小窗（半圓拱、磚石相間的拱券、石灰岩窗台；灰泥鏤空窗格嵌小玻璃，部件，0.1 m）', (W, H, D), v, S)


def window2():
    """雙拱窗（bifora）：兩個 0.6 m 的半圓拱中間一根大理石小柱、柱頭一塊墊石；下半截木窗板關著、上半截開著（暗處）。樓上好一點的房間用。"""
    v = {}
    W, H, D = 20, 3, 20
    A = arch_cells(3, 9, 2, 13) + arch_cells(11, 17, 2, 13)
    COL = [(x, z) for x in (9, 10) for z in range(2, 13)]
    S = A + COL
    SA, SS = set(A), set(S)
    _ring(v, SS, W, D, 13, [6.0, 14.0], n=5)
    for x in range(1, 19):
        v[(x, 0, 1)] = LIME_G                                 # 窗台
    for (x, z) in COL:
        v[(x, 1, z)] = MARBLE                                 # 小柱
    for x in range(8, 12):
        v[(x, 0, 12)] = MARBLE                                # 柱頭的墊石（凸出一格）
    for (x, z) in A:                                          # 窗板、暗處鋪滿整個開口（邊上那一圈跟牆接上 ⇒ 不浮空）
        if _edge(SA, x, z):
            v[(x, 1, z)] = LIME_R
        if z < 9:
            v[(x, 2, z)] = TIMBER if x % 3 == 0 else SHUT     # 下半截窗板
        else:
            v[(x, 2, z)] = DARK
    return P('window2', '雙拱窗（bifora：兩個半圓拱、中間大理石小柱與墊石、磚石拱券；下半截木窗板，部件，0.1 m）', (W, H, D), v, S)


def door():
    """門：大理石門框與過梁（方的，1.0 × 2.0 m）、上面一道半圓的磚卸力拱、拱裡一片灰泥；兩扇木門（鐵釘）。"""
    v = {}
    W, H, D = 16, 3, 30
    R = [(x, z) for x in range(3, 13) for z in range(0, 20)]
    LUN = []
    for x in range(3, 13):
        for z in range(22, 27):                               # 過梁（z 20、21，凸出那一層）後面的牆照留
            if math.hypot(x + 0.5 - 8, z + 0.5 - 20) < 5.0:
                LUN.append((x, z))
    S = R + LUN
    SS = set(S)
    for x in range(W):
        for z in range(20, D):
            d = math.hypot(x + 0.5 - 8, z + 0.5 - 20)
            if 5.0 <= d < 7.2 and (x, z) not in SS:
                v[(x, 0, z)] = ring_color(x, z, 8, 20, 7)     # 卸力拱
    for z in range(0, 20):
        for x in (1, 2, 13, 14):
            v[(x, 0, z)] = MARBLE                             # 門框
    for x in range(1, 15):
        for z in (20, 21):
            v[(x, 0, z)] = MARBLE                             # 過梁
    for (x, z) in LUN:
        v[(x, 1, z)] = PLASTER                                # 拱裡的灰泥
    for (x, z) in R:
        if x in (7, 8) or z == 19:
            c = TIMBER
        elif x in (4, 11) and z in (4, 10, 16):
            c = IRON                                          # 門釘
        else:
            c = SHUT
        v[(x, 2, z)] = c                                      # ⛔ 門檻不凸出牆外：門口固定點那一格要是空氣
    return P('door', '門（大理石門框與過梁、上面半圓的磚卸力拱與灰泥、兩扇釘鐵釘的木門，部件，0.1 m）', (W, H, D), v, S)


def shop():
    """店面（ergasterion）：2.2 m 寬的半圓拱開間、磚石拱券；開間下半截木板、一道木櫃台，上半截開著（暗處），櫃台上擺兩只陶甕。大街兩旁一間接一間（芝諾法管的那一排）。"""
    v = {}
    W, H, D = 28, 3, 32
    S = arch_cells(3, 25, 0, 18)
    SS = set(S)
    _ring(v, SS, W, D, 18, [14.0], n=13, z_min=0)
    for (x, z) in S:
        if z < 8:
            v[(x, 2, z)] = TIMBER if x % 4 == 0 else SHUT    # 櫃台下的木板
        elif z == 8:
            for y in (0, 1, 2):
                v[(x, y, z)] = TIMBER                         # 櫃台（凸出牆外一格）
        else:
            v[(x, 2, z)] = DARK
    for cx in (6, 21):                                        # 櫃台上的陶甕
        for x in (cx, cx + 1):
            for z in range(9, 13):
                v[(x, 1, z)] = AMPH
        v[(cx, 1, 13)] = AMPH
    return P('shop', '店面（2.2 m 半圓拱開間、磚石拱券；下半截木板、木櫃台、上半截開著，櫃台上兩只陶甕，部件，0.1 m）', (W, H, D), v, S)


ALL = [window, window2, door, shop]


def all_parts():
    return {f()['id']: f() for f in ALL}
