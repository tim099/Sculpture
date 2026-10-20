# 法式殖民城鎮建築套件（TASK-0741）—— 共用工具：調色盤、Model（分層的格子）、四坡／兩坡屋頂、通用部件的擺放與挖洞、圖紙。
# 座標（建築，見 Sculpture_Building §1）：x ＝ 臨路寬（從街上面向建築看，左 → 右）、y ＝ 進深（y 0 ＝ 臨路那一邊）、z ＝ 往上（z 0 ＝ 整平面）；0.1 m／格。
#   格 k 佔 [k, k+1)、格心 k+0.5；作品框 ＝ 地塊（w×10 × d×10 × 高）。
# 通用部件（parts.py）一律「朝外 ＝ −y」：y 0 ＝ 牆外那一層（百葉、窗台），y 1.. ＝ 牆身裡。擺到哪一面照 face 轉（關聯 turn，公式同引擎 SCP_SculptLinks.Transform）。
# 落子順序：同一格後寫的蓋掉先寫的；put(prio) 低優先的不蓋高優先的（屋頂不蓋牆）。
import math, hashlib

# ── 調色盤（RGB332 的 index）：每個「會換色」的角色只用一個色，替換色（TASK-0584）才換得乾淨 ──
OCHRE, BLUE, CREAM, SALMON = 213, 187, 218, 246          # 灰泥牆（土黃、藍、米白、鮭粉）—— 只用在灰泥
TRIM = 255                                                # 白色線腳、窗框、柱、欄杆
STONE, STONE_L, STONE_D = 146, 182, 110                   # 毛石、淺石（線腳、隅石、灰縫）、深石
STONE_W, SLATE = 177, 73                                  # 偏暖的毛石（倉庫、城牆）、鉛皮與石板（穹頂）
TILE_A, TILE_B, TILE_C, TILE_R = 168, 164, 200, 132       # 紅陶瓦三色＋屋脊、簷口
SH_GREEN, SH_BLUE, SH_RED, SH_GREY = 49, 42, 160, 78      # 百葉與門（漆過的木作）—— 只用在百葉與門
GLASS, IRON, DARK = 41, 37, 36                            # 玻璃、鍛鐵、暗處（煙道、室內）
WOOD, WOOD_D, WOOD_G = 104, 68, 109                       # 木地板、深色木構、風吹雨淋的灰木
BRICK, BRONZE, GOLD = 136, 177, 248
EARTH, GRASS, GRASS_D, LEAF, PURPLE = 141, 76, 44, 80, 98
LOG, LOG_D, LOG_TIP = 104, 68, 177

NAMES = {OCHRE: 'ochre', BLUE: 'blue', CREAM: 'cream', SALMON: 'salmon', TRIM: 'trim', STONE: 'stone', STONE_L: 'stone_l', STONE_D: 'stone_d',
         TILE_A: 'tile_a', TILE_B: 'tile_b', TILE_C: 'tile_c', TILE_R: 'tile_r', SH_GREEN: 'sh_green', SH_BLUE: 'sh_blue', SH_RED: 'sh_red',
         SH_GREY: 'sh_grey', GLASS: 'glass', IRON: 'iron', DARK: 'dark', WOOD: 'wood', WOOD_D: 'wood_d', WOOD_G: 'wood_g', BRICK: 'brick',
         BRONZE: 'bronze', GOLD: 'gold', EARTH: 'earth', GRASS: 'grass', GRASS_D: 'grass_d', LEAF: 'leaf', PURPLE: 'purple'}


def rgb(c):
    return ((c >> 5) & 7) * 255 // 7, ((c >> 2) & 7) * 255 // 7, (c & 3) * 255 // 3


def h01(*a):
    """決定論的雜湊 [0, 1)（⛔ 不用 random）。"""
    s = ','.join(str(v) for v in a).encode()
    return int(hashlib.md5(s).hexdigest()[:8], 16) / 4294967296.0


PRIO = {'body': 3, 'gallery': 2, 'roof': 1}


class Model:
    """一件建築（或牆模組）：分層的格子（body／roof／gallery…）＋擺上去的通用部件（關聯）＋外部模型＋固定點。"""

    def __init__(s, size):
        s.X, s.Y, s.Z = size
        s.cells = {}             # (x, y, z) -> (layer, color)
        s.links = []             # {'name', 'part', 'at', 'turn', 'mirror', 'cells'(組裝件座標)}
        s.models = []            # {'name', 'source', 'at', 'pivot', 'rotate', 'meta'}
        s.anchors = {}           # 名字 -> (x, y, z)（整數格）
        s.oob = 0                # 想落在框外的格數（必須 0）
        s.notes = []
        s.shutter = SH_GREEN     # 這一棟的百葉色：≠ 綠 ⇒ 每個部件的關聯帶替換色 49:<色>

    def inb(s, x, y, z):
        return 0 <= x < s.X and 0 <= y < s.Y and 0 <= z < s.Z

    def put(s, layer, x, y, z, c, force=False):
        if not s.inb(x, y, z):
            s.oob += 1
            return
        k = (x, y, z)
        old = s.cells.get(k)
        if old and not force and PRIO.get(old[0], 3) > PRIO.get(layer, 3):
            return
        s.cells[k] = (layer, c)

    def box(s, layer, x0, y0, z0, x1, y1, z1, c, force=False):
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    s.put(layer, x, y, z, c, force)

    def clear(s, x0, y0, z0, x1, y1, z1, layer=None):
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    k = (x, y, z)
                    if k in s.cells and (layer is None or s.cells[k][0] == layer):
                        del s.cells[k]

    def recolor(s, x0, y0, z0, x1, y1, z1, c, only=None):
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    k = (x, y, z)
                    if k in s.cells and (only is None or s.cells[k][1] in only):
                        s.cells[k] = (s.cells[k][0], c)

    def get(s, x, y, z):
        return s.cells.get((x, y, z))

    def layer(s, name):
        return {k: v[1] for k, v in s.cells.items() if v[0] == name}

    def anchor(s, name, x, y, z):
        x, y, z = int(x), int(y), int(z)
        if not s.inb(x, y, z):
            raise ValueError('固定點 %s (%d,%d,%d) 不在框裡 %s' % (name, x, y, z, (s.X, s.Y, s.Z)))
        s.anchors[name] = (x, y, z)


# ── 關聯的座標（⛔ 跟引擎 SCP_SculptLinks.Transform 同一個公式：先翻、再繞 Z 轉、再加 at）──
def xform(x, y, z, dims, turn=0, mirror='', at=(0, 0, 0)):
    W, H, D = dims
    if 'x' in mirror:
        x = W - 1 - x
    if 'y' in mirror:
        y = H - 1 - y
    if 'z' in mirror:
        z = D - 1 - z
    if turn == 90:
        x, y = H - 1 - y, x
    elif turn == 180:
        x, y = W - 1 - x, H - 1 - y
    elif turn == 270:
        x, y = y, W - 1 - x
    return x + at[0], y + at[1], z + at[2]


# 朝外 −y 的部件擺到哪一面要轉幾度（turn 之後部件的 −y 指向那一面的外側）
FACE_TURN = {'front': 0, 'right': 90, 'back': 180, 'left': 270}


def place(M, part, name, face, rect, u, z, t, carve=True, layer_ok=None):
    """把通用部件擺到牆 rect=(X0, Y0, X1, Y1)（外表面）的 face 面：沿牆從那一面的「左端」量 u 格（部件框的起點）、底 z；
    牆厚 t ⇒ 挖掉部件的 socket（開口）穿過整個牆厚。回傳 at／turn；部件的格落在組裝件座標存在 M.links。
    「左端」：front 從 X0 往 +x；back 從 X1 往 −x；right 從 Y0 往 +y；left 從 Y1 往 −y（都是從外面看那一面的左手邊）。"""
    W, H, D = part['dims']
    X0, Y0, X1, Y1 = rect
    turn = FACE_TURN[face]
    # 先用 at=0 轉一次，再平移：部件 y 0（外面那一層）落在牆外第一格；沿牆起點照 u
    pts = [(xform(x, y, zz, part['dims'], turn), c) for (x, y, zz), c in part['cells'].items()]
    if face == 'front':
        at = (X0 + u, Y0 - 1, z)
    elif face == 'back':
        at = (X1 - u - W, Y1 - H + 1, z)
    elif face == 'right':
        at = (X1 - H + 1, Y0 + u, z)
    elif face == 'left':
        at = (X0 - 1, Y1 - u - W, z)
    else:
        raise ValueError(face)
    # turn 之後框的原點還是 (0,0)（引擎的公式保證外框落在 [0,W')×[0,H')）⇒ 直接加 at
    sock = part['socket']
    if isinstance(sock, tuple):
        sock = [(lx, lz) for lx in range(sock[0], sock[1]) for lz in range(sock[2], sock[3])]
    if carve:
        for (lx, lz) in sock:
                for ly in range(1, 1 + t):
                    wx, wy, wz = xform(lx, ly, lz, part['dims'], turn, '', at)
                    k = (wx, wy, wz)
                    if k in M.cells and M.cells[k][0] in ('body', 'gallery'):
                        del M.cells[k]
    cells = {}
    for (p, c) in pts:
        k = (p[0] + at[0], p[1] + at[1], p[2] + at[2])
        cells[k] = c
    rc = {SH_GREEN: M.shutter} if M.shutter != SH_GREEN else {}
    if rc:
        cells = {k: rc.get(c, c) for k, c in cells.items()}
    M.links.append({'name': name, 'part': part['id'], 'at': list(at), 'turn': turn, 'mirror': '', 'cells': cells, 'dims': part['dims'], 'recolor': rc})
    return at, turn


def place_free(M, part, name, at, turn=0, mirror=''):
    """不挖洞、照 at／turn 直接擺（煙囪、老虎窗這類自己算好位置的）。"""
    rc = {SH_GREEN: M.shutter} if M.shutter != SH_GREEN else {}
    cells = {}
    for (x, y, z), c in part['cells'].items():
        cells[xform(x, y, z, part['dims'], turn, mirror, at)] = rc.get(c, c)
    M.links.append({'name': name, 'part': part['id'], 'at': list(at), 'turn': turn, 'mirror': mirror, 'cells': cells, 'dims': part['dims'], 'recolor': rc})


def carve_cells(M, cells, layers=('roof',)):
    """把部件佔的格從某幾層挖掉（老虎窗、煙囪穿過屋頂）。"""
    n = 0
    for k in cells:
        if k in M.cells and M.cells[k][0] in layers:
            del M.cells[k]
            n += 1
    return n


# ── 屋頂 ──
def roof_field(rects):
    """rects：[{x0,y0,x1,y1, ze, p, over:(左,右,前,後), kick:{front|back|left|right: 緩坡}, gable:'x'|'y'|None}] ⇒ {(x, y): (頂面 z 浮點, 坡面 id)}。
    每一塊照四坡（或兩坡）算，同一欄取最高（兩塊屋頂相接 ⇒ 自然長出天溝）。"""
    F = {}
    for ri, r in enumerate(rects):
        ol, orr, of, ob = r.get('over', (4, 4, 4, 4))
        kick = r.get('kick', {})
        p = r['p']
        for x in range(r['x0'] - ol, r['x1'] + orr):
            for y in range(r['y0'] - of, r['y1'] + ob):
                px, py = x + 0.5, y + 0.5
                pl = {}
                dl, dr, df, db = px - r['x0'], r['x1'] - px, py - r['y0'], r['y1'] - py
                for nm, d in (('left', dl), ('right', dr), ('front', df), ('back', db)):
                    k = kick.get(nm)
                    pl[nm] = r['ze'] + (p * d if (d >= 0 or k is None) else k * d)
                g = r.get('gable')
                if g == 'x':                     # 屋脊沿 x ⇒ 只有前後兩坡
                    pl.pop('left'); pl.pop('right')
                elif g == 'y':
                    pl.pop('front'); pl.pop('back')
                srt = sorted(pl.items(), key=lambda kv: kv[1])
                z = srt[0][1]
                ridge = len(srt) > 1 and srt[1][1] - srt[0][1] < 0.75
                cur = F.get((x, y))
                if cur is None or z > cur[0]:
                    F[(x, y)] = (z, srt[0][0], ridge, ri)
    return F


def tile_color(x, y, facet, ridge, edge, salt=0):
    if ridge or edge:
        return TILE_R
    a = x if facet in ('front', 'back') else y          # 筒瓦順著坡往下 ⇒ 沿簷口方向一條一條
    b = y if facet in ('front', 'back') else x
    if h01('tc', a // 2, b // 3, salt) < 0.12:
        return TILE_C
    return TILE_A if (a // 2) % 2 == 0 else TILE_B


def build_roof(M, F, thick=2, layer='roof', color_fn=None, salt=0, force=True):
    """照高度場鋪屋面（厚 thick；往下補到相鄰欄的頂 ⇒ 陡坡不會從縫裡透光）。回傳 {(x,y): 頂 z}。
    force ⇒ 屋面蓋過牆頂那一層（不然牆頂那一圈被牆佔走，屋頂自己斷成簷口與上半兩塊）。"""
    top = {k: int(math.floor(v[0])) for k, v in F.items()}
    for (x, y), (zf, facet, ridge, ri) in F.items():
        zt = top[(x, y)]
        nb = [top.get((x + 1, y)), top.get((x - 1, y)), top.get((x, y + 1)), top.get((x, y - 1))]
        edge = any(v is None for v in nb)
        lo = zt - thick + 1
        nbv = [v for v in nb if v is not None]
        if nbv:
            lo = min(lo, min(nbv) + 1)
        c = color_fn(x, y, facet, ridge, edge) if color_fn else tile_color(x, y, facet, ridge, edge, salt)
        for z in range(lo, zt + 1):
            M.put(layer, x, y, z, c, force)
    return top


def shed_roof(M, x0, y0, x1, y1, z_hi, p, low='front', thick=2, color_fn=None, layer='roof'):
    """單坡頂：low 那一邊低（front ＝ y 小）。回傳 {(x,y): 頂 z}。"""
    F = {}
    for x in range(x0, x1):
        for y in range(y0, y1):
            px, py = x + 0.5, y + 0.5
            d = {'front': y1 - py, 'back': py - y0, 'left': x1 - px, 'right': px - x0}[low]
            F[(x, y)] = (z_hi - p * d, low if low in ('front', 'back') else 'left', False, 0)
    return build_roof(M, F, thick, layer, color_fn)


def picket_fence(M, pts, z1=14, color=WOOD_G, step=2, layer='body'):
    """木柵圍籬：沿 pts 的折線（軸向段）每 step 格一根、兩道橫檔。"""
    for (a, b) in zip(pts, pts[1:]):
        (xa, ya), (xb, yb) = a, b
        n = max(abs(xb - xa), abs(yb - ya))
        for i in range(n + 1):
            x = xa + (i if xb > xa else -i if xb < xa else 0)
            y = ya + (i if yb > ya else -i if yb < ya else 0)
            for z in (4, z1 - 3):
                M.put(layer, x, y, z, color)
            if i % step == 0:
                for z in range(0, z1):
                    M.put(layer, x, y, z, color)


# ── 牆面 ──
def stucco_walls(M, rect, z0, z1, t, color, layer='body'):
    X0, Y0, X1, Y1 = rect
    M.box(layer, X0, Y0, z0, X1, Y1, z1, color)
    M.clear(X0 + t, Y0 + t, z0, X1 - t, Y1 - t, z1, layer)


def rubble(M, rect, z0, z1, t, layer='body', base=STONE, mortar=STONE_L, course=5, block=8, salt=0, dark=STONE_D):
    """毛石牆：一皮 course 格、灰縫一格、上下皮錯縫；石塊顏色雜一點。"""
    X0, Y0, X1, Y1 = rect
    for z in range(z0, z1):
        rowi = (z - z0) // course
        for x in range(X0, X1):
            for y in range(Y0, Y1):
                if X0 + t <= x < X1 - t and Y0 + t <= y < Y1 - t:
                    continue
                u = x + y + (block // 2 if rowi % 2 else 0)
                if (z - z0) % course == course - 1 or u % block == 0:
                    c = mortar
                else:
                    r = h01('rb', u // block, rowi, salt)
                    c = dark if r < 0.15 else base
                M.put(layer, x, y, z, c)


def quoins(M, rect, z0, z1, color=STONE_L, long=6, short=3, step=5, layer='body'):
    """轉角隅石：每 step 層一塊，長短交錯（長邊在這一面、短邊在另一面，下一層反過來）。只染牆的外面那一層。"""
    X0, Y0, X1, Y1 = rect
    for z in range(z0, z1):
        k = ((z - z0) // step) % 2
        a, b = (long, short) if k == 0 else (short, long)
        if (z - z0) % step == step - 1:
            continue                       # 灰縫留牆色
        for (cx, cy, sx, sy) in ((X0, Y0, 1, 1), (X1 - 1, Y0, -1, 1), (X0, Y1 - 1, 1, -1), (X1 - 1, Y1 - 1, -1, -1)):
            for i in range(a):
                M.recolor(cx + sx * i, cy, z, cx + sx * i + 1, cy + 1, z + 1, color)
            for j in range(b):
                M.recolor(cx, cy + sy * j, z, cx + 1, cy + sy * j + 1, z + 1, color)


def band(M, rect, z0, z1, color, out=1, layer='body'):
    """牆外一圈腰線／簷口線腳（往外凸 out 格）。"""
    X0, Y0, X1, Y1 = rect
    for z in range(z0, z1):
        for x in range(X0 - out, X1 + out):
            for y in range(Y0 - out, Y1 + out):
                if X0 < x < X1 - 1 and Y0 < y < Y1 - 1:
                    continue                   # 只要牆外凸出那一圈＋牆的最外一層
                if X0 <= x < X1 and Y0 <= y < Y1:
                    k = (x, y, z)
                    if k in M.cells:
                        M.cells[k] = (M.cells[k][0], color)
                    continue
                M.put(layer, x, y, z, color)


def floor_slab(M, rect, z0, z1, color=WOOD, layer='body'):
    X0, Y0, X1, Y1 = rect
    M.box(layer, X0, Y0, z0, X1, Y1, z1, color)


# ── 圖紙（新圖紙：俯視＋正立面＋側立面，照組好的格子畫）──
def composite(M):
    comp = {k: v[1] for k, v in M.cells.items()}
    clash = 0
    for L in M.links:
        for k, c in L['cells'].items():
            if k in comp:
                clash += 1
            else:
                comp[k] = c
    return comp, clash


def sheet(comp, size, path, title='', px=2):
    from PIL import Image, ImageDraw
    X, Y, Z = size
    views = []
    # 俯視：每欄最高的格；越低越暗
    top = {}
    for (x, y, z), c in comp.items():
        if (x, y) not in top or z > top[(x, y)][0]:
            top[(x, y)] = (z, c)
    im1 = Image.new('RGB', (X, Y), (232, 228, 214))
    p1 = im1.load()
    for (x, y), (z, c) in top.items():
        f = 0.55 + 0.45 * z / max(1, Z)
        r, g, b = rgb(c)
        p1[x, y] = (int(r * f), int(g * f), int(b * f))
    views.append(('俯視（上 ＝ 臨路）', im1))
    # 正立面：從街上（−y）看，每 (x,z) 最靠前的格
    fr = {}
    for (x, y, z), c in comp.items():
        if (x, z) not in fr or y < fr[(x, z)][0]:
            fr[(x, z)] = (y, c)
    im2 = Image.new('RGB', (X, Z), (232, 228, 214))
    p2 = im2.load()
    for (x, z), (y, c) in fr.items():
        f = 1.0 - 0.45 * y / max(1, Y)
        r, g, b = rgb(c)
        p2[x, Z - 1 - z] = (int(r * f), int(g * f), int(b * f))
    views.append(('正立面（從街上看）', im2))
    # 側立面：從右手邊（+x）看，左 ＝ 臨路
    sd = {}
    for (x, y, z), c in comp.items():
        if (y, z) not in sd or x > sd[(y, z)][0]:
            sd[(y, z)] = (x, c)
    im3 = Image.new('RGB', (Y, Z), (232, 228, 214))
    p3 = im3.load()
    for (y, z), (x, c) in sd.items():
        f = 0.55 + 0.45 * x / max(1, X)
        r, g, b = rgb(c)
        p3[y, Z - 1 - z] = (int(r * f), int(g * f), int(b * f))
    views.append(('側立面（從右手邊看）', im3))
    W = sum(v[1].size[0] for v in views) * px + 40 * (len(views) + 1)
    H = max(v[1].size[1] for v in views) * px + 90
    out = Image.new('RGB', (W, H), (250, 248, 240))
    d = ImageDraw.Draw(out)
    try:
        from PIL import ImageFont
        font = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 16)
    except Exception:
        font = None
    d.text((20, 10), title, fill=(30, 30, 30), font=font)
    xo = 40
    for nm, im in views:
        big = im.resize((im.size[0] * px, im.size[1] * px), Image.NEAREST)
        out.paste(big, (xo, 60))
        d.text((xo, 38), nm, fill=(60, 60, 60), font=font)
        for m in range(0, im.size[0] + 1, 10):          # 每 1 m 一個刻度
            d.line([(xo + m * px, 56), (xo + m * px, 58 if m % 50 else 52)], fill=(120, 120, 120))
        xo += big.size[0] + 40
    out.save(path)
