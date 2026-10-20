# 通用部件（TASK-0757；建築規格 §3）：這一套新做的（木板百葉窗、木板門、雙扇木板門、撐開的百葉）＋借法式套件現成的（貨門、氣窗）。
# 座標同 summit-bourg-fr-01m/design/parts.py：朝外 −y；y 0 ＝ 牆外那一層（打開貼牆的百葉、窗台）、y 1 ＝ 跟牆外表面齊的框、y 2 ＝ 往裡一格的門扇；z 0 ＝ 開口底。
# 17 世紀的加勒比海聚落窗上沒有玻璃（史料見作品 references/README.md）⇒ 窗是開口＋實心木板百葉；門是直板＋橫檔＋斜撐。
# 顏色角色：百葉與門 SHUT（配色變化換它）、框 FRAME。
import os, sys, importlib.util
from carib import *

FR_DESIGN = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'summit-bourg-fr-01m', 'design')
FR_ROOT = 'summit-bourg-fr-01m'


def P(pid, title, dims, cells, socket=None, anchors=None, src=None):
    W, H, D = dims
    for (x, y, z) in cells:
        assert 0 <= x < W and 0 <= y < H and 0 <= z < D, (pid, x, y, z)
    return {'id': pid, 'title': title, 'dims': dims, 'cells': cells, 'socket': socket, 'anchors': anchors or {}, 'src': src}


def _box(v, x0, y0, z0, x1, y1, z1, c):
    for x in range(x0, x1):
        for y in range(y0, y1):
            for z in range(z0, z1):
                v[(x, y, z)] = c


def _leaf(v, y, x0, x1, z0, z1, brace=True):
    """一扇木板（直板、每 3 格一道板縫，上下兩道橫檔＋一條斜撐）。"""
    for x in range(x0, x1):
        for z in range(z0, z1):
            v[(x, y, z)] = SHUT
    h = z1 - z0
    for z in (z0 + 1, z1 - 2) if h > 6 else (z0 + h // 2,):
        for x in range(x0, x1):
            v[(x, y, z)] = FRAME
    if brace and h > 8:
        za, zb = z0 + 2, z1 - 2
        for z in range(za, zb):
            u = (z - za) / max(1, (zb - za - 1))
            x = x0 + int(round(u * (x1 - x0 - 1)))
            v[(x, y, z)] = FRAME


def window_board():
    """窗：1.0 × 1.2 m 的開口、深色木框與窗台，兩扇實心木板百葉開著貼在牆上；沒有玻璃。"""
    v = {}
    W, H, D = 20, 3, 14
    _leaf(v, 0, 0, 5, 1, 13, brace=False)
    _leaf(v, 0, 15, 20, 1, 13, brace=False)
    _box(v, 4, 0, 0, 16, 1, 1, FRAME)            # 窗台
    _box(v, 4, 0, 13, 16, 1, 14, FRAME)          # 窗楣
    for z in range(0, 14):                       # y 1 外框
        for x in (4, 15):
            v[(x, 1, z)] = FRAME
    for x in range(4, 16):
        v[(x, 1, 0)] = FRAME
        v[(x, 1, 13)] = FRAME
    return P('window-board', '窗（開口＋兩扇開著的實心木板百葉、深色木框，沒有玻璃；17 世紀加勒比海，通用部件，0.1 m）', (W, H, D), v, (4, 16, 0, 14))


def window_prop():
    """撐開的百葉（上緣鉸鏈、用一根木棍往外撐開）：開口 1.0 × 1.0 m；百葉斜出牆外 0.5 m。"""
    v = {}
    W, H, D = 14, 6, 15
    for z in range(0, 12):                       # y 5 ＝ 牆外那一層（框）；部件往外伸 ⇒ y 0..4 是斜出去的百葉
        for x in (1, 12):
            v[(x, 5, z)] = FRAME
    for x in range(1, 13):
        v[(x, 5, 0)] = FRAME
        v[(x, 5, 11)] = FRAME
    for k in range(10):                          # 百葉：上緣在 (y 5, z 11)，往外往下斜到 (y 0, z 3)
        y = 5 - (k * 5) // 9
        z = 11 - k
        for x in range(1, 13):
            v[(x, y, z)] = FRAME if x in (1, 12) else SHUT
    for k in range(5):                           # 撐棍：從窗台外緣斜上去頂住百葉
        v[(6, 5 - k, 1 + k)] = FRAME
    return P('window-prop', '撐開的百葉窗（上緣鉸鏈、木棍撐開，沒有玻璃；通用部件，0.1 m）', (W, H, D), v, None)


def door_plank():
    """木板門（單扇）：1.0 × 2.1 m 的開口、深色木框、門扇直板＋橫檔＋斜撐，關著。"""
    v = {}
    W, H, D = 14, 3, 23
    _box(v, 0, 0, 21, 14, 1, 23, FRAME)          # 門楣（伸出兩側各 1 格）
    for z in range(0, 22):
        for x in (1, 12):
            v[(x, 1, z)] = FRAME
            v[(x, 0, z)] = FRAME
    for x in range(1, 13):
        v[(x, 1, 21)] = FRAME
    for z in range(0, 22):                       # 門框往裡深一格 ⇒ 門扇的鉸鏈邊壓在框上（不然門扇自己一塊，BUILDING_SPEC §10 第 3 條）
        v[(1, 2, z)] = FRAME
        v[(12, 2, z)] = FRAME
    _leaf(v, 2, 2, 12, 0, 21)
    return P('door-plank', '木板門（單扇、直板＋橫檔＋斜撐、深色木框；通用部件，0.1 m）', (W, H, D), v, (1, 13, 0, 22))


def door_double():
    """雙扇木板門（酒館、教堂、長官的屋子）：1.6 × 2.4 m、兩扇各一條斜撐、門楣上一根橫木。"""
    v = {}
    W, H, D = 20, 3, 27
    _box(v, 0, 0, 24, 20, 1, 27, FRAME)
    for z in range(0, 25):
        for x in (1, 18):
            v[(x, 1, z)] = FRAME
            v[(x, 0, z)] = FRAME
    for x in range(1, 19):
        v[(x, 1, 24)] = FRAME
    for z in range(0, 25):                       # 門框往裡深一格（同木板門）
        v[(1, 2, z)] = FRAME
        v[(18, 2, z)] = FRAME
    _leaf(v, 2, 2, 10, 0, 24)
    _leaf(v, 2, 10, 18, 0, 24)
    for z in range(0, 24):
        v[(9, 2, z)] = FRAME
        v[(10, 2, z)] = FRAME
    return P('door-double', '雙扇木板門（各一條斜撐、門楣橫木；通用部件，0.1 m）', (W, H, D), v, (1, 19, 0, 25))


def borrowed():
    """借法式套件現成的部件（同一件作品 ⇒ 遊戲只存一次）：貨門、氣窗。"""
    spec = importlib.util.spec_from_file_location('fr_parts', os.path.join(FR_DESIGN, 'parts.py'))
    sys.path.insert(0, FR_DESIGN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    sys.path.pop(0)
    out = {}
    for fn in (m.cartdoor, m.vent):
        p = fn()
        out[p['id']] = dict(p, src=FR_ROOT + '-part-' + p['id'])
    return out


def window_baluster():
    """欄杆窗（史料：沒有玻璃、用車製的欄杆 balustres 代替 —— Rochefort 1658、Labat 1722）：1.0 × 1.4 m 的開口、深色木框、九根直條（中段粗一格）。"""
    v = {}
    W, H, D = 20, 3, 16
    _box(v, 4, 0, 0, 16, 1, 1, FRAME)            # 窗台
    _box(v, 4, 0, 15, 16, 1, 16, FRAME)          # 窗楣
    for z in range(0, 16):
        for x in (4, 15):
            v[(x, 1, z)] = FRAME
    for x in range(4, 16):
        v[(x, 1, 0)] = FRAME
        v[(x, 1, 15)] = FRAME
    for x in range(6, 15, 2):                    # 欄杆：每 2 格一根，中段（z 6..9）往外鼓一格 ＝ 車出來的肚子
        for z in range(1, 15):
            v[(x, 1, z)] = FRAME
        for z in range(6, 10):
            v[(x, 2, z)] = FRAME
    return P('window-baluster', '欄杆窗（開口＋車製木欄杆代替玻璃、深色木框；教堂用，17 世紀法屬安地列斯，通用部件，0.1 m）', (W, H, D), v, (4, 16, 0, 16))


ALL = [window_board, window_baluster, door_plank, door_double]          # window_prop：17 世紀有沒有這種窗還沒查到 ⇒ 先不做成作品


def all_parts():
    d = {f()['id']: f() for f in ALL}
    d.update(borrowed())
    return d
