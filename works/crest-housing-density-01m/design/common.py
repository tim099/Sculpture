# 住宅三級密度（TASK-0893）—— 共用：借 summit 兩套建築套件的工具與部件（⛔ 這裡不建部件作品；關聯一律指回原作品）。
#   fr：summit-bourg-fr-01m/design 的 kit.py（Model、屋頂、牆、圖紙）、parts.py（窗、落地窗、門、貨門、氣窗、老虎窗、煙囪）、houses.py（院牆、廚房、木板門）
#   carib：summit-carib-01m/design 的 carib.py（調色盤、木板牆、毛石牆、木瓦頂、欄杆）、parts.py（木板百葉窗、木板門、雙扇門；借法式的貨門、氣窗）
#   兩邊的 kit.py 是同一份（carib 那份註明抄自 fr）⇒ 只載 fr 那一份；兩邊都叫 parts.py ⇒ carib 的用 importlib 換名字載。
# 座標同 kit.py：x 臨路寬（從街上看左 → 右）、y 進深（y 0 臨路）、z 往上（z 0 整平面）；0.1 m／格；作品框 ＝ 地塊。
import os, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
WORKS = os.path.dirname(os.path.dirname(HERE))
FR_DESIGN = os.path.join(WORKS, 'summit-bourg-fr-01m', 'design')
CARIB_DESIGN = os.path.join(WORKS, 'summit-carib-01m', 'design')
FR_ROOT, CARIB_ROOT = 'summit-bourg-fr-01m', 'summit-carib-01m'
for p in (CARIB_DESIGN, FR_DESIGN):                  # fr 在最前面：import kit／parts／houses 都是 fr 那一份
    if p not in sys.path:
        sys.path.insert(0, p)

from kit import *                                     # noqa: E402,F401,F403
import parts as FRP                                   # noqa: E402
import houses as FRH                                  # noqa: E402  院牆 yard、廚房 kitchen、木板門 simple_door
import carib as CB                                    # noqa: E402  （它的 from kit import * 拿到的就是上面那一份）


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


CBP = _load('carib_parts', os.path.join(CARIB_DESIGN, 'parts.py'))

# 部件 ⇒ 原作品的 id（關聯的 source）：fr ＝ <FR_ROOT>-part-<id>；carib 自己做的 ＝ <CARIB_ROOT>-part-<id>、借法式的 ＝ 它記的 src
FR_PARTS = {pid: dict(P, work=FR_ROOT + '-part-' + pid) for pid, P in FRP.all_parts().items()}
CB_PARTS = {pid: dict(P, work=P.get('src') or (CARIB_ROOT + '-part-' + pid)) for pid, P in CBP.all_parts().items()}


def put_part(M, parts, pid, name, face, rect, center, z, t, shutter=None):
    """部件的開口中心對準 center（front／back 量 x、left／right 量 y），底在 z（同 summit 兩套 houses.put_part）。
    shutter ＝ 這個部件的百葉色要換成什麼（部件原本是綠 49；None ⇒ 照 M.shutter）。"""
    P = parts[pid]
    W = P['dims'][0]
    X0, Y0, X1, Y1 = rect
    if face == 'front':
        u = center - X0 - W // 2
    elif face == 'back':
        u = X1 - W - center + W // 2
    elif face == 'right':
        u = center - W // 2 - Y0
    else:
        u = Y1 - W - center + W // 2
    keep = M.shutter
    if shutter is not None:
        M.shutter = shutter
    r = place(M, P, name, face, rect, u, z, t)
    M.shutter = keep
    M.links[-1]['part'] = P['work']
    return r


def free_part(M, parts, pid, name, at, turn=0, mirror='', carve=('roof',), shutter=None):
    P = parts[pid]
    keep = M.shutter
    if shutter is not None:
        M.shutter = shutter
    place_free(M, P, name, at, turn, mirror)
    M.shutter = keep
    M.links[-1]['part'] = P['work']
    return carve_cells(M, M.links[-1]['cells'], carve)


def iron_balcony(M, x0, x1, y0, y1, z, layer='gallery', brackets=None):
    """托架鐵陽台（同 fr 住宅 A：木地板、鍛鐵欄杆、木扶手；托架是實心三角，從牆面挑出）：x ∈ [x0, x1)、y ∈ [y0, y1)（y1 ＝ 牆面）、地板頂 z。
    brackets ＝ 托架的 x（每根 2 格寬）：托架貼牆那一頭往下伸到 z − 3 − 進深 ⇒ 要擺在一樓的門、貨門、窗之間（不然撞到部件）。"""
    M.box(layer, x0, y0, z - 2, x1, y1, z, WOOD)
    M.box(layer, x0, y0, z - 2, x1, y0 + 1, z, WOOD_D)
    deep = y1 - y0
    for bx in (brackets or list(range(x0, x1 - 2, 22)) + [x1 - 2]):
        for y in range(y0 + 1, y1):
            for zz in range(z - 3 - (y - y0 - 1), z - 2):
                M.box(layer, bx, y, zz, bx + 2, y + 1, zz + 1, WOOD_D)
    for x in range(x0, x1):
        M.put(layer, x, y0, z, IRON)
        M.put(layer, x, y0, z + 9, WOOD_D)
        if x % 2 == 0:
            for zz in range(z + 1, z + 9):
                M.put(layer, x, y0, zz, IRON)
    for xs in (x0, x1 - 1):
        for y in range(y0, y1):
            M.put(layer, xs, y, z, IRON)
            M.put(layer, xs, y, z + 9, WOOD_D)
            if (y - y0) % 2 == 1:
                for zz in range(z + 1, z + 9):
                    M.put(layer, xs, y, zz, IRON)
    return deep


def well(M, wx, wy, ring=STONE, cap=STONE_L, post=WOOD_D):
    """水井：石圈＋木架（同 fr 住宅 C）。"""
    import math
    for x in range(wx - 6, wx + 6):
        for y in range(wy - 6, wy + 6):
            r = math.hypot(x + 0.5 - wx, y + 0.5 - wy)
            if 3.2 < r < 6.0:
                for z in range(0, 9):
                    M.put('body', x, y, z, cap if z == 8 else ring)
    M.box('body', wx - 6, wy - 1, 9, wx - 4, wy + 1, 30, post)
    M.box('body', wx + 4, wy - 1, 9, wx + 6, wy + 1, 30, post)
    M.box('body', wx - 6, wy - 1, 30, wx + 6, wy + 1, 32, post)


LANTERN = {'source': 'summit-rocher-01m-lantern', 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}
BARREL = {'source': 'summit-rocher-01m-barrel', 'pivot': [6, 6, 0], 'meta': {}}
CRATE = {'source': 'summit-rocher-01m-crate', 'pivot': [6, 6, 0], 'meta': {}}


def model(kind, name, at):
    return dict(kind, name=name, at=list(at))
