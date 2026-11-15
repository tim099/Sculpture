# 義大利通用住宅的部件（gura-italy-housing-1666）—— 每件 ＝ 一件 0.1 m 的子作品 <ROOT>-part-<id>，房子用關聯擺（替換色換得到窗板的色）。
# 格式同 gura-venice-housing-1666/design/vparts.py：朝外 −y；y 0 ＝ 牆外那一層（石框、窗台、開著的窗板凸出一格）、y 1 ＝ 跟牆外表面齊、y 2 ＝ 往裡一格；
#   z 0 ＝ 開口底。socket ＝ 牆上要挖的開口 [(x, z)…] ⇒ y 1、y 2 的格一律落在 socket 裡。
# 樣子（史料見 ../notes.md）：
#   finestra：托斯卡納的方窗 —— pietra serena 的石框、凸出的窗台、窗頂一道小簷；小片玻璃＋木窗格；兩片實心木窗板（scuri）開著。
#   finestral：利古里亞的方窗 —— 沒有石框（框是畫在牆上的白框，房子另外畫）、黑石板窗台；窄一點、高一點；scuri。
#   inginocchiata：跪窗（Michelangelo 起、托斯卡納矯飾主義的標準元素，宅邸一樓）—— 窗台架在兩個像跪凳腳的石托上、鐵柵、頂上一道小山牆。
#   portone：托斯卡納的大門 —— serena 的門框兩格寬、門楣上一道簷；兩扇深褐木門、鐵釘。
#   portale：利古里亞的大門 —— 黑石板（ardesia）的門框與刻花的門楣（sopraporta）；兩扇木門。
#   porta：窄樓的小門（serena 框）。
#   volta：拱頂店鋪的開口（熱那亞一樓連成一排的那種）—— 半圓拱、石的拱圈；下半截木板櫃台、上半截暗處、拱裡一片木格扇窗。
from icommon import *


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


def _ring(v, S, W, D, reach, color, z_min=0):
    for x in range(W):
        for z in range(z_min, D):
            if (x, z) in S:
                continue
            if any((x + dx, z + dz) in S for dx in range(-reach, reach + 1) for dz in range(-reach, reach + 1)):
                v[(x, 0, z)] = color


def _glass(v, S, y=2):
    """小片玻璃（或油布 impannata）＋木窗格：每 3 格一道木。"""
    for (x, z) in S:
        v[(x, y, z)] = WOOD_D if (x % 3 == 0 or z % 4 == 0 or _edge(set(S), x, z)) else GLASS


def _scuri(v, x0, x1, z0, z1):
    """開著的實心木窗板（scuri；貼在牆外 y 0）：豎木板、上下兩道橫檔。"""
    for x in range(x0, x1):
        for z in range(z0, z1):
            v[(x, 0, z)] = WOOD_D if (z in (z0 + 2, z1 - 3) or x in (x0, x1 - 1)) else SCURO


def finestra():
    v = {}
    W, H, D = 21, 3, 22
    S = [(x, z) for x in range(6, 15) for z in range(2, 19)]
    SS = set(S)
    _ring(v, SS, W, D, 1, SERENA, z_min=1)
    for x in range(4, 17):
        v[(x, 0, 1)] = SERENA_D                                   # 窗台
    for x in range(4, 17):
        v[(x, 0, 20)] = SERENA                                    # 小簷
    for x in range(5, 16):
        v[(x, 0, 21)] = SERENA_D
    for (x, z) in S:
        if _edge(SS, x, z):
            v[(x, 1, z)] = SERENA
    _glass(v, S)
    _scuri(v, 0, 5, 2, 19)
    _scuri(v, 16, 21, 2, 19)
    return P('finestra', '托斯卡納的方窗（pietra serena 石框、窗台、小簷；小片玻璃木窗格；兩片實心木窗板開著，部件，0.1 m）', (W, H, D), v, S)


def finestral():
    v = {}
    W, H, D = 17, 3, 21
    S = [(x, z) for x in range(5, 12) for z in range(2, 20)]
    SS = set(S)
    for x in range(4, 13):
        v[(x, 0, 1)] = ARDESIA                                    # 黑石板窗台
    for (x, z) in S:
        if _edge(SS, x, z):
            v[(x, 1, z)] = WOOD_D
    _glass(v, S)
    _scuri(v, 0, 4, 2, 20)
    _scuri(v, 13, 17, 2, 20)
    return P('finestral', '利古里亞的窄方窗（黑石板窗台、白框畫在牆上；小片玻璃木窗格；兩片實心木窗板開著，部件，0.1 m）', (W, H, D), v, S)


def inginocchiata():
    v = {}
    W, H, D = 19, 3, 30
    S = [(x, z) for x in range(5, 14) for z in range(8, 24)]
    SS = set(S)
    _ring(v, SS, W, D, 2, SERENA, z_min=6)
    for x in range(2, 17):                                        # 窗台（凸出）
        v[(x, 0, 6)] = SERENA_D
        v[(x, 0, 7)] = SERENA
    for cx in (3, 14):                                            # 跪凳腳的石托（往下收）
        for z in range(0, 6):
            for x in range(cx, cx + 2 + (1 if z > 2 else 0)):
                v[(x, 0, z)] = SERENA if z % 2 else SERENA_D
    for x in range(1, 18):                                        # 小山牆
        v[(x, 0, 26)] = SERENA
    for k, z in enumerate((27, 28, 29)):
        for x in range(3 + 2 * k, 16 - 2 * k):
            v[(x, 0, z)] = SERENA
    for (x, z) in S:
        v[(x, 1, z)] = IRON if (x % 2 == 1 or z % 5 == 3) else DARK  # 鐵柵（凸出牆外表面那一層）
        v[(x, 2, z)] = GLASS if (x + z) % 3 else WOOD_D
    return P('inginocchiata', '跪窗（finestra inginocchiata：窗台架在兩個石托上、鐵柵、頂上小山牆；pietra serena，部件，0.1 m）', (W, H, D), v, S)


def _leaves(v, S, x0, x1, z1, y=2):
    xm = (x0 + x1) // 2
    for (x, z) in S:
        if z >= z1:
            continue
        if x in (xm - 1, xm) or z == z1 - 1:
            c = WOOD_D
        elif (x - x0) % 3 == 0:
            c = WOOD_D
        elif x in (x0 + 1, x1 - 2) and z % 6 == 4:
            c = IRON
        else:
            c = PORTA
        v[(x, y, z)] = c
    v[(xm - 2, y, 12)] = IRON
    v[(xm + 1, y, 12)] = IRON


def portone():
    v = {}
    W, H, D = 20, 3, 34
    S = [(x, z) for x in range(4, 16) for z in range(0, 28)]
    for z in range(0, 30):
        for x in (2, 3, 16, 17):
            v[(x, 0, z)] = SERENA
    for x in range(1, 19):
        v[(x, 0, 28)] = SERENA
        v[(x, 0, 29)] = SERENA
    for x in range(0, 20):
        v[(x, 0, 30)] = SERENA_D                                  # 門楣上的簷
        v[(x, 0, 31)] = SERENA
    for x in range(1, 19):
        v[(x, 0, 32)] = SERENA_D
    _leaves(v, S, 4, 16, 28)
    return P('portone', '托斯卡納的大門（pietra serena 門框兩格、門楣上一道簷；兩扇深褐木門、鐵釘，部件，0.1 m）', (W, H, D), v, S)


def portale():
    v = {}
    W, H, D = 20, 3, 34
    S = [(x, z) for x in range(4, 16) for z in range(0, 26)]
    for z in range(0, 26):
        for x in (2, 3, 16, 17):
            v[(x, 0, z)] = ARDESIA
    for x in range(2, 18):                                        # 刻花的門楣（sopraporta）：黑石板、淺色的刻線
        for z in range(26, 33):
            v[(x, 0, z)] = SERENA if (z in (27, 31) or (z == 29 and x % 3 == 0)) and 3 < x < 16 else ARDESIA
    _leaves(v, S, 4, 16, 26)
    return P('portale', '利古里亞的大門（黑石板 ardesia 門框、刻花的門楣 sopraporta；兩扇木門，部件，0.1 m）', (W, H, D), v, S)


def porta():
    v = {}
    W, H, D = 14, 3, 27
    S = [(x, z) for x in range(3, 11) for z in range(0, 24)]
    for z in range(0, 25):
        for x in (2, 11):
            v[(x, 0, z)] = SERENA
    for x in range(1, 13):
        v[(x, 0, 24)] = SERENA
        v[(x, 0, 25)] = SERENA_D
    _leaves(v, S, 3, 11, 24)
    return P('porta', '小門（窄樓的住家門：serena 框；兩扇木門，部件，0.1 m）', (W, H, D), v, S)


def volta():
    v = {}
    W, H, D = 28, 3, 32
    cx, zs, r = 14.0, 15, 11.0
    S = [(x, z) for x in range(3, 25) for z in range(0, 30) if z < zs or math.hypot(x + 0.5 - cx, z + 0.5 - zs) < r]
    SS = set(S)
    for x in range(W):
        for z in range(0, D):
            if (x, z) in SS:
                continue
            d = math.hypot(x + 0.5 - cx, z + 0.5 - zs)
            if z >= zs and r <= d < r + 2.6:
                v[(x, 0, z)] = SERENA if int(math.degrees(math.atan2(z + 0.5 - zs, x + 0.5 - cx)) // 15) % 2 else SERENA_D   # 拱圈的楔石
            elif z < zs and x in (1, 2, 25, 26):
                v[(x, 0, z)] = SERENA
    for (x, z) in S:
        if z < 9:
            v[(x, 2, z)] = WOOD_D if x % 4 == 0 else PORTA        # 櫃台下的木板
        elif z == 9:
            for y in (0, 1, 2):
                v[(x, y, z)] = WOOD                               # 櫃台面
        elif z >= zs + 3:
            v[(x, 2, z)] = WOOD_D if (x % 3 == 0 or z % 3 == 0) else GLASS   # 拱裡的木格扇窗
        else:
            v[(x, 2, z)] = DARK
    return P('volta', '拱頂店鋪的開口（volta：半圓拱、石拱圈；木櫃台、上半截暗處、拱裡木格扇窗，部件，0.1 m）', (W, H, D), v, S)


ALL = [finestra, finestral, inginocchiata, portone, portale, porta, volta]


def all_parts():
    return {f()['id']: f() for f in ALL}
