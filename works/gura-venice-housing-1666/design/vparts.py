# 威尼斯住宅的部件（gura-venice-housing-1666）—— 每件 ＝ 一件 0.1 m 的子作品 <ROOT>-part-<id>，房子用關聯擺（替換色換得到窗板的色）。
# 格式同 summit-bourg-fr-01m/design/parts.py、kaguya-cpl-housing-1453/design/bzparts.py：朝外 −y；y 0 ＝ 牆外那一層（石框、窗台、開著的窗板凸出一格）、
#   y 1 ＝ 跟牆外表面齊、y 2 ＝ 往裡一格；z 0 ＝ 開口底。socket ＝ 牆上要挖的開口 [(x, z)…]（kit.place() 挖穿牆厚）⇒ y 1、y 2 的格一律落在 socket 裡。
# 樣子：門窗框、窗台、門楣一律伊斯特拉石（白）；哥德式的反曲尖拱（arco inflesso）照 14～15 世紀留到今天的民宅窗；17 世紀的方窗（石框、上面一道小簷）；
#   窗板（scuri）綠漆、開著貼在窗兩側；玻璃是一圈一圈鉛條嵌的小圓片（rui，穆拉諾的）⇒ 玻璃＋鐵格。出處見 ../notes.md。
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


def ogee(x0, w, z0, zs, rise):
    """反曲尖拱（arco inflesso）開口的 (x, z)：x ∈ [x0, x0 + w)、z 從 z0 到 zs 是直的，zs 以上照離中線的距離收：
    兩肩外凸、往中間內凹收成一個尖（rise ＝ 尖比起拱線高幾格）。"""
    out, c = [], x0 + (w - 1) / 2.0
    for x in range(x0, x0 + w):
        t = abs(x - c) / max(0.5, (w - 1) / 2.0)                 # 0 中線 ～ 1 邊
        # 外凸的肩（t 大）＋ 內凹的尖（t 小）：S 形
        top = rise * (1 - t) ** 1.6 if t < 0.55 else rise * (1 - t) ** 0.7 * 0.62
        for z in range(z0, zs + int(round(top)) + 1):
            out.append((x, z))
    return out


def _frame(v, S, W, D, reach=1, color=ISTRIA, z_min=0):
    """開口外 reach 格一圈伊斯特拉石（y 0）。"""
    for x in range(W):
        for z in range(z_min, D):
            if (x, z) in S:
                continue
            if any((x + dx, z + dz) in S for dx in range(-reach, reach + 1) for dz in range(-reach, reach + 1)):
                v[(x, 0, z)] = color


def _glass(v, S, y=2):
    """鉛條嵌的小圓玻璃（rui）：每 2 格一道鐵、其餘玻璃。"""
    for (x, z) in S:
        v[(x, y, z)] = IRON if (x % 2 == 0 and z % 2 == 0) or _edge(set(S), x, z) else GLASS


def _scuri(v, x0, x1, z0, z1):
    """開著的木窗板（貼在牆外 y 0）：一片一片豎的木條、上下兩道橫檔。"""
    for x in range(x0, x1):
        for z in range(z0, z1):
            v[(x, 0, z)] = WOOD_D if (z in (z0 + 2, z1 - 3) or x == x0) else SCURI


def window():
    """哥德式單窗（monofora a arco inflesso）：0.7 m 寬、起拱 1.3 m、尖再高 0.6 m；伊斯特拉石框一圈、凸出的窗台；小圓玻璃；兩片綠窗板開著。"""
    v = {}
    W, H, D = 18, 3, 23
    S = ogee(6, 7, 2, 14, 6)
    SS = set(S)
    _frame(v, SS, W, D, 1, z_min=1)
    for x in range(4, 15):
        v[(x, 0, 1)] = ISTRIA_G                                     # 窗台
    for (x, z) in S:
        if _edge(SS, x, z):
            v[(x, 1, z)] = ISTRIA
    _glass(v, S)
    _scuri(v, 1, 5, 2, 15)
    _scuri(v, 14, 18, 2, 15)
    return P('window', '哥德式單窗（反曲尖拱、伊斯特拉石框與窗台、小圓玻璃、兩片綠窗板開著，部件，0.1 m）', (W, H, D), v, S)


def windowq():
    """17 世紀的方窗：0.8 × 1.5 m、伊斯特拉石框、凸出的窗台、頂上一道小簷（cornicetta）；小圓玻璃；兩片綠窗板開著。"""
    v = {}
    W, H, D = 18, 3, 21
    S = [(x, z) for x in range(5, 13) for z in range(2, 17)]
    SS = set(S)
    _frame(v, SS, W, D, 1, z_min=1)
    for x in range(3, 15):
        v[(x, 0, 1)] = ISTRIA_G                                     # 窗台
        v[(x, 0, 18)] = ISTRIA                                      # 小簷
    for x in range(4, 14):
        v[(x, 0, 19)] = ISTRIA_G
    for (x, z) in S:
        if _edge(SS, x, z):
            v[(x, 1, z)] = ISTRIA
    _glass(v, S)
    _scuri(v, 0, 4, 2, 17)
    _scuri(v, 14, 18, 2, 17)
    return P('windowq', '方窗（17 世紀：伊斯特拉石框、窗台、頂上小簷；小圓玻璃、兩片綠窗板開著，部件，0.1 m）', (W, H, D), v, S)


def _leaves(v, S, x0, x1, z1, y=2):
    """兩扇木門（深褐、豎木條、鐵釘、一個門環）。"""
    xm = (x0 + x1) // 2
    for (x, z) in S:
        if z >= z1:
            continue
        if x in (xm - 1, xm) or z == z1 - 1:
            c = WOOD_D
        elif (x - x0) % 3 == 0:
            c = WOOD_D
        elif x in (x0 + 1, x1 - 2) and z in (4, 10, 16):
            c = IRON
        else:
            c = PORTA
        v[(x, y, z)] = c
    v[(xm - 2, y, 11)] = IRON
    v[(xm + 1, y, 11)] = IRON


def door():
    """門（方的，1.0 × 2.2 m）：伊斯特拉石門框（兩格寬）與門楣、門楣上一個半圓的通氣窗（lunetta）裝鍛鐵格柵；兩扇深褐木門。"""
    v = {}
    W, H, D = 16, 3, 30
    R = [(x, z) for x in range(3, 13) for z in range(0, 22)]
    LUN = [(x, z) for x in range(3, 13) for z in range(24, 29) if math.hypot(x + 0.5 - 8, z + 0.5 - 24) < 5.0]
    S = R + LUN
    for z in range(0, 24):
        for x in (1, 2, 13, 14):
            v[(x, 0, z)] = ISTRIA
    for x in range(0, 16):
        for z in (22, 23):
            v[(x, 0, z)] = ISTRIA_G if z == 23 else ISTRIA          # 門楣
    for x in range(W):
        for z in range(24, D):
            d = math.hypot(x + 0.5 - 8, z + 0.5 - 24)
            if 5.0 <= d < 6.6 and (x, z) not in set(S):
                v[(x, 0, z)] = ISTRIA                               # 通氣窗的石圈
    for (x, z) in LUN:
        v[(x, 1, z)] = IRON if (x % 2 == 0 or (z - 24) % 2 == 0) else DARK
        if (x, 2, z) not in v:
            v[(x, 2, z)] = DARK
    _leaves(v, R, 3, 13, 22)
    return P('door', '門（伊斯特拉石門框與門楣、半圓通氣窗的鍛鐵格柵、兩扇深褐木門，部件，0.1 m）', (W, H, D), v, S)


def doorg():
    """哥德式的門（較好的房子、宅邸的水陸正門那一種）：1.0 m 寬、直的 2.0 m、上面反曲尖拱再高 0.7 m；伊斯特拉石框一圈兩格；兩扇木門＋拱裡的木板。"""
    v = {}
    W, H, D = 16, 3, 32
    S = ogee(3, 10, 0, 20, 7)
    SS = set(S)
    _frame(v, SS, W, D, 2)
    for (x, z) in S:
        if _edge(SS, x, z):
            v[(x, 1, z)] = ISTRIA
    _leaves(v, S, 3, 13, 20)
    for (x, z) in S:
        if z >= 20 and (x, 2, z) not in v:
            v[(x, 2, z)] = WOOD_D if (x + z) % 3 == 0 else PORTA
    return P('doorg', '哥德式的門（反曲尖拱、伊斯特拉石框兩格、兩扇深褐木門，部件，0.1 m）', (W, H, D), v, S)


def shop():
    """店面（bottega）：2.2 m 寬、2.0 m 高的方開口，伊斯特拉石框；下半截一道木櫃台（白天把木板放下來當檯面，balcone），
    櫃台上兩只陶罐，上半截開著（暗處），頂上一片收起來的木窗板。"""
    v = {}
    W, H, D = 26, 3, 24
    S = [(x, z) for x in range(2, 24) for z in range(0, 20)]
    for z in range(0, 22):
        for x in (0, 1, 24, 25):
            v[(x, 0, z)] = ISTRIA
    for x in range(0, 26):
        for z in (20, 21):
            v[(x, 0, z)] = ISTRIA
        v[(x, 0, 22)] = ISTRIA_G
    for (x, z) in S:
        if z < 8:
            v[(x, 2, z)] = WOOD_D if x % 4 == 0 else PORTA          # 櫃台下的木板
        elif z == 8:
            for y in (0, 1, 2):
                v[(x, y, z)] = WOOD                                 # 櫃台面（凸出牆外一格）
        elif z >= 17:
            v[(x, 1, z)] = WOOD_D if x % 3 == 0 else PORTA          # 收起來的上半片窗板
        else:
            v[(x, 2, z)] = DARK
    for cx in (6, 19):                                              # 陶罐
        for x in (cx, cx + 1):
            for z in range(9, 12):
                v[(x, 1, z)] = 136
        v[(cx, 1, 12)] = 136
    return P('shop', '店面（bottega：伊斯特拉石框的方開口、木櫃台、收起來的上半片窗板、櫃台上兩只陶罐，部件，0.1 m）', (W, H, D), v, S)


def trifora():
    """三連窗（trifora）：主樓層中間照亮 portego 的那一組 —— 三個反曲尖拱、中間兩根伊斯特拉石小柱、整組一圈石框；小圓玻璃（窗板在裡面，看不到）。
    前面的石陽台（poggiolo）由房子另外砌（common.poggiolo）。"""
    v = {}
    W, H, D = 30, 3, 27
    S = []
    for k in range(3):
        S += ogee(2 + k * 9, 7, 1, 17, 6)
    COL = [(x, z) for x in (9, 10, 18, 19) for z in range(1, 18)]
    SS = set(S + COL)
    _frame(v, SS, W, D, 1)
    for (x, z) in COL:
        v[(x, 1, z)] = ISTRIA
        if z == 17:
            v[(x, 0, z)] = ISTRIA_G                                 # 柱頭
    SA = set(S)
    for (x, z) in S:
        if _edge(SA, x, z):
            v[(x, 1, z)] = ISTRIA
    _glass(v, S)
    for (x, z) in COL:
        v[(x, 2, z)] = ISTRIA
    return P('trifora', '三連窗（trifora：三個反曲尖拱、伊斯特拉石小柱與框、小圓玻璃，部件，0.1 m）', (W, H, D), v, list(SS))


ALL = [window, windowq, door, doorg, shop, trifora]


def all_parts():
    return {f()['id']: f() for f in ALL}
