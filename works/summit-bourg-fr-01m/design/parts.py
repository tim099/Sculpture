# 通用部件（TASK-0741；建築規格 §3）：窗、落地窗、門、貨門、氣窗、老虎窗、煙囪、弧拱窗、教堂圓拱窗、圓窗。
# 每件 ＝ 一件 0.1 m 的子作品，用**關聯**擺（不是外部模型）⇒ 建築的替換色（recolor）換得到部件的色（百葉、門、牆色）。
# 座標：朝外 −y；y 0 ＝ 牆外那一層（百葉、窗台、線腳）、y 1 ＝ 跟牆外表面齊的框、y 2 ＝ 往裡一格的窗扇／門扇；z 0 ＝ 開口底（窗台那一層在 z 0）。
# socket ＝ 牆上要挖的開口：(x0, x1, z0, z1) 或 [(x, z)…]；kit.place() 照它挖穿牆厚。
# 顏色角色：百葉與門扇 SH_GREEN（換色換它）、框 TRIM、窗台與拱心石 STONE_L、玻璃 GLASS；老虎窗側面用瓦色、煙囪磚。
from kit import *


def P(pid, title, dims, cells, socket=None, anchors=None, meta=None):
    W, H, D = dims
    for (x, y, z) in cells:
        assert 0 <= x < W and 0 <= y < H and 0 <= z < D, (pid, x, y, z)
    return {'id': pid, 'title': title, 'dims': dims, 'cells': cells, 'socket': socket, 'anchors': anchors or {}, 'meta': meta or {}}


def _box(v, x0, y0, z0, x1, y1, z1, c):
    for x in range(x0, x1):
        for y in range(y0, y1):
            for z in range(z0, z1):
                v[(x, y, z)] = c


def _casement(v, y, x0, x1, z0, z1, frame=TRIM, glass=GLASS, bars=4, mid=True):
    """一層窗扇：外圈框、中間一根中梃（偶數寬 ⇒ 兩格）、每 bars 層一道橫條、其餘玻璃。"""
    w = x1 - x0
    for x in range(x0, x1):
        for z in range(z0, z1):
            edge = x in (x0, x1 - 1) or z in (z0, z1 - 1)
            c = frame if edge else glass
            if mid and (x - x0) in ((w - 1) // 2, w // 2):
                c = frame
            if bars and not edge and (z - z0) % bars == 0:
                c = frame
            v[(x, y, z)] = c


def window():
    v = {}
    W, H, D = 20, 3, 16
    _box(v, 0, 0, 1, 6, 1, 15, SH_GREEN)        # 兩扇百葉開著貼在牆上（鉸鏈那一欄壓到開口邊 1 格）
    _box(v, 14, 0, 1, 20, 1, 15, SH_GREEN)
    _box(v, 4, 0, 0, 16, 1, 1, STONE_L)          # 窗台
    _box(v, 4, 0, 15, 16, 1, 16, TRIM)           # 窗楣
    for y in (1, 2):
        _casement(v, y, 5, 15, 1, 15, bars=0 if y == 1 else 4, mid=(y == 2))
    for x in range(6, 14):                       # y 1 那一層只留外框
        for z in range(2, 14):
            v.pop((x, 1, z), None)
    return P('window', '窗（平開窗＋兩扇開著的百葉，通用部件，0.1 m）', (W, H, D), v, (5, 15, 1, 15))


def frenchdoor():
    v = {}
    W, H, D = 20, 3, 23
    _box(v, 0, 0, 0, 6, 1, 22, SH_GREEN)
    _box(v, 14, 0, 0, 20, 1, 22, SH_GREEN)
    _box(v, 4, 0, 22, 16, 1, 23, TRIM)
    _casement(v, 2, 5, 15, 0, 22, bars=4)
    _box(v, 6, 2, 1, 14, 3, 7, SH_GREEN)         # 下半截木板（跟百葉同色 ⇒ 一起換色）
    for z in range(0, 22):                       # y 1 外框
        for x in range(5, 15):
            if x in (5, 14) or z in (0, 21):
                v[(x, 1, z)] = TRIM
    return P('frenchdoor', '落地窗（porte-fenêtre，通往陽台；開著的百葉，通用部件，0.1 m）', (W, H, D), v, (5, 15, 0, 22))


def door():
    v = {}
    W, H, D = 17, 3, 27
    _box(v, 0, 0, 0, 3, 1, 23, TRIM)             # 兩側壁柱（壓到門框那一欄 ⇒ 跟門框連成一塊）
    _box(v, 14, 0, 0, 17, 1, 23, TRIM)
    _box(v, 0, 0, 23, 17, 1, 26, TRIM)           # 門楣（簷部）
    _box(v, 1, 0, 26, 16, 1, 27, STONE_L)        # 頂上一條石線腳
    for z in range(0, 23):
        for x in range(2, 15):
            if x in (2, 14) or z == 22:
                v[(x, 1, z)] = TRIM
                v[(x, 2, z)] = TRIM
    for z in range(0, 18):                       # 兩扇門（中線 x 8 一條深色木）
        for x in range(3, 14):
            c = SH_GREEN
            if x == 8 or z in (7, 13):
                c = WOOD_D
            v[(x, 2, z)] = c
    for x in range(3, 14):                       # 門楣窗（扇形窗）
        v[(x, 2, 18)] = TRIM
        for z in range(19, 22):
            v[(x, 2, z)] = TRIM if (x == 8 or abs(x - 8) == (z - 18) * 2) else GLASS
    return P('door', '門（雙扇、上有扇形窗、兩側壁柱，通用部件，0.1 m）', (W, H, D), v, (2, 15, 0, 23))


def cartdoor():
    v = {}
    W, H, D = 26, 3, 29
    _box(v, 0, 0, 27, 26, 1, 29, WOOD_D)         # 門外一根木過梁（兩格高，壓到門框頂那一排）
    for z in range(0, 28):
        for x in range(1, 25):
            if x in (1, 24) or z == 27:
                v[(x, 1, z)] = WOOD_D
                v[(x, 2, z)] = WOOD_D
    for z in range(0, 27):                       # 兩扇木門：直板＋Z 形斜撐
        for x in range(2, 24):
            c = SH_GREEN
            if x == 12 or x == 13:
                c = WOOD_D
            elif (x - 2) % 4 == 3:
                c = WOOD_D if z % 9 == 0 else SH_GREEN
            v[(x, 2, z)] = c
        for lx0, lx1 in ((2, 12), (14, 24)):
            if z in (3, 13, 23):
                for x in range(lx0, lx1):
                    v[(x, 2, z)] = WOOD_D
    for lx0 in (2, 14):                          # 斜撐：兩道橫檔之間各一條
        for zb in (3, 13):
            for i in range(10):
                x = lx0 + i
                z = zb + i
                if z < zb + 10:
                    v[(x, 2, z)] = WOOD_D
    return P('cartdoor', '貨門（大的雙扇木門、木過梁，通用部件，0.1 m）', (W, H, D), v, (1, 25, 0, 28))


def vent():
    v = {}
    W, H, D = 14, 3, 12
    _box(v, 2, 0, 0, 10, 1, 1, STONE_L)
    _box(v, 8, 0, 1, 14, 1, 11, SH_GREEN)        # 一扇百葉開在右手邊
    for z in range(1, 11):
        for x in range(3, 9):
            if x in (3, 8) or z in (1, 10):
                v[(x, 1, z)] = STONE_L
            elif x in (5, 6) and 1 < z < 10:
                v[(x, 1, z)] = IRON              # 兩根鐵條
    v[(4, 1, 6)] = IRON
    v[(7, 1, 6)] = IRON
    return P('vent', '氣窗（小的石框鐵條窗、一扇百葉，倉庫用，通用部件，0.1 m）', (W, H, D), v, (3, 9, 1, 11))


def dormer():
    """老虎窗：前面一道小牆＋窗、兩片側牆往後 24 格、兩坡小屋頂（屋脊沿 y）。z 0 ＝ 前牆底；擺的時候讓前牆底落在主屋面上，側牆的下半截埋進閣樓。"""
    v = {}
    W, H, D = 14, 24, 21
    top = {}
    for x in range(0, 14):
        d = min(x + 0.5, 14 - (x + 0.5))
        top[x] = 14 + int(math.floor(d * 0.9))
    for y in range(0, 24):
        for x in range(0, 14):
            zt = top[x]
            for z in range(zt - 1, zt + 1):
                v[(x, y, z)] = TILE_R if (y == 0 or x in (0, 13) or zt == max(top.values())) else (TILE_A if (x // 2) % 2 == 0 else TILE_B)
    for y in range(1, 24):                       # 側牆（瓦色掛面）：從 z 0 補到屋面底下
        for x in (1, 12):
            for z in range(0, top[x] - 1):
                v[(x, y, z)] = TILE_B
    for x in range(1, 13):                       # 前牆＋窗
        for z in range(0, top[x] - 1):
            v[(x, 1, z)] = TRIM
    for x in range(4, 10):                       # 窗扇就在前牆那一層（跟牆連成一塊）
        for z in range(3, 12):
            edge = x in (4, 9) or z in (3, 11)
            v[(x, 1, z)] = TRIM if (edge or x in (6, 7) or z == 7) else GLASS
    _box(v, 1, 0, 3, 4, 1, 12, SH_GREEN)
    _box(v, 10, 0, 3, 13, 1, 12, SH_GREEN)
    return P('dormer', '老虎窗（lucarne：小窗、兩扇百葉、兩坡小屋頂，通用部件，0.1 m）', (W, H, D), v, None)


def chimney():
    v = {}
    W, H, D = 8, 7, 40
    for z in range(0, 36):
        for x in range(1, 7):
            for y in range(1, 6):
                v[(x, y, z)] = STONE_L if z % 6 == 5 else BRICK
    _box(v, 0, 0, 36, 8, 7, 38, STONE_L)         # 帽
    for x in range(2, 6):
        for y in range(2, 5):
            v[(x, y, 38)] = BRICK if x in (2, 5) or y in (2, 4) else DARK
            v[(x, y, 39)] = BRICK if x in (2, 5) or y in (2, 4) else DARK
    for x in range(3, 5):
        for y in range(3, 4):
            for z in range(36, 38):
                v[(x, y, z)] = DARK
    return P('chimney', '煙囪（磚砌、石帽，通用部件，0.1 m；固定點 smoke ＝ 煙囪口）', (W, H, D), v, None, anchors={'smoke': (4, 3, 39)})


def _arch_cells(x0, x1, z0, zs, style):
    """開口的格：x ∈ [x0, x1)、z ∈ [z0, 頂)；segment ＝ 弧拱（頂上兩排各縮一格）、round ＝ 半圓拱（從 zs 起）。"""
    out = []
    w = x1 - x0
    cx = (x0 + x1) / 2.0
    r = w / 2.0
    for x in range(x0, x1):
        px = x + 0.5
        if style == 'segment':
            k = min(px - x0, x1 - px)
            ztop = zs + (2 if k > 2 else (1 if k > 1 else 0))
        else:
            dx = px - cx
            ztop = zs + int(math.floor(math.sqrt(max(0.0, r * r - dx * dx))))
        for z in range(z0, ztop):
            out.append((x, z))
    return out


def window_arch():
    v = {}
    W, H, D = 20, 3, 22
    cells = _arch_cells(5, 15, 1, 18, 'segment')
    S = set(cells)
    _box(v, 0, 0, 1, 6, 1, 18, SH_GREEN)
    _box(v, 14, 0, 1, 20, 1, 18, SH_GREEN)
    _box(v, 4, 0, 0, 16, 1, 1, STONE_L)
    _box(v, 9, 0, 19, 11, 1, 22, STONE_L)        # 拱心石
    for (x, z) in cells:
        edge = (x - 1, z) not in S or (x + 1, z) not in S or (x, z - 1) not in S or (x, z + 1) not in S
        if edge:
            v[(x, 1, z)] = TRIM
        c = TRIM if (edge or x in (9, 10) or (z - 1) % 4 == 0) else GLASS
        v[(x, 2, z)] = c
    return P('window-arch', '弧拱窗（segmental arch、拱心石、兩扇百葉，公共建築用，通用部件，0.1 m）', (W, H, D), v, cells)


def window_round():
    v = {}
    W, H, D = 14, 3, 37
    cells = _arch_cells(2, 12, 1, 30, 'round')
    S = set(cells)
    _box(v, 1, 0, 0, 13, 1, 1, STONE_L)
    for (x, z) in cells:                         # 外面一圈石框（拱券）：開口外兩格、含開口邊那一圈（壓在窗框前 ⇒ 連成一塊）
        edge = any((x + dx, z + dz) not in S for dx in (-1, 0, 1) for dz in (-1, 0, 1) if (dx or dz) and z + dz >= 1)
        if edge:
            v[(x, 0, z)] = STONE_L
        for dx in (-2, -1, 0, 1, 2):
            for dz in (-2, -1, 0, 1, 2):
                nx, nz = x + dx, z + dz
                if (nx, nz) not in S and 0 <= nx < W and 1 <= nz < D:
                    v[(nx, 0, nz)] = STONE_L
    for (x, z) in cells:
        edge = (x - 1, z) not in S or (x + 1, z) not in S or (x, z - 1) not in S or (x, z + 1) not in S
        c = IRON if (edge or x == 7 or (z - 1) % 5 == 0) else GLASS
        v[(x, 1, z)] = c
    return P('window-round', '教堂圓拱窗（高窄、半圓拱、鉛條玻璃、石拱券，通用部件，0.1 m）', (W, H, D), v, cells)


def oculus():
    v = {}
    W, H, D = 16, 3, 16
    cells = []
    for x in range(16):
        for z in range(16):
            r = math.hypot(x + 0.5 - 8, z + 0.5 - 8)
            if r < 5.2:
                cells.append((x, z))
                v[(x, 1, z)] = IRON if (abs(x + 0.5 - 8) < 1 or abs(z + 0.5 - 8) < 1 or r > 4.3) else GLASS
            if 4.3 < r < 7.6:
                v[(x, 0, z)] = STONE_L
    return P('oculus', '圓窗（oeil-de-boeuf：石框、十字鐵條，通用部件，0.1 m）', (W, H, D), v, cells)


ALL = [window, frenchdoor, door, cartdoor, vent, dormer, chimney, window_arch, window_round, oculus]


def all_parts():
    return {f().__getitem__('id'): f() for f in ALL}
