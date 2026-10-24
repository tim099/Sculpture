# 君士坦丁堡 1453 的中、高密度住宅（TASK-0893，羅馬 roman 那一套）—— 共用：借 summit-bourg-fr-01m/design 的 kit.py（Model、屋頂、圖紙、部件的擺法）。
#   部件是這一套自己的（bzparts.py：磚拱小窗、雙拱窗、大理石框門、拱券店面）⇒ 建成 <ROOT>-part-<id> 的子作品，房子用關聯擺。
# 座標同 kit.py：x 臨路寬（從街上看左 → 右）、y 進深（y 0 臨路）、z 往上（z 0 整平面）；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 史料（2026-10-24 查的，很薄 ⇒ 樣子大多是〔設計〕）：
#   - 芝諾法（476–479，查士丁尼 531 年推到全帝國）管君士坦丁堡的陽台（maeniana）、採光與視線、大街兩旁店面的排法（revistas.usp.br 的 Private buildings…）。
#   - 上層人家的房子樓上有陽台、主屋分出側翼；大多數人住的房子住人的不超過兩層（博物館模型說明，非學術）。
#   - 遺存多半只剩牆基 ⇒ 窗的樣子不知道、樓上只從留下來的樓梯推得到（Oxford Handbook 的民居一章的摘要）；1455 年鄂圖曼的調查有「單層的房子」「很多房間的房子」。
#   ⇒ 牆照本小姐城牆與港邊倉庫列的石灰岩方石夾紅磚帶（opus mixtum）；樓上一層用木構夾灰泥、挑出街面（同時代地中海城市常見的作法，設計）；
#     紅陶筒瓦緩坡頂；大街的店面是磚拱券的開間；院子有井欄、陶甕。
import os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
WORKS = os.path.dirname(os.path.dirname(HERE))
FR_DESIGN = os.path.join(WORKS, 'summit-bourg-fr-01m', 'design')
if FR_DESIGN not in sys.path:
    sys.path.insert(0, FR_DESIGN)

from kit import *                                     # noqa: E402,F401,F403

# ── 這一套的調色盤（RGB332 index）：會換色的角色各只用一個色 ──
LIME_R, LIME_G, BRICK_R, BRICK_RM = 218, 182, 168, 205   # 石灰岩方石（米白、灰米）、紅磚、磚帶的粉紅厚灰漿（同 kaguya-roman-1453 rkit、kaguya-harbour-01m 的港邊倉庫列）
PLASTER = 255                                            # 木構夾的灰泥、門楣上的半圓（白石灰）—— 配色變化換它
SHUT = 100                                               # 門、店面的木板、窗板（牛血紅漆）—— 配色變化換它
TIMBER = WOOD_D                                          # 木構、托架、陽台
MARBLE = 219                                             # 大理石的門框、小柱、窗格（灰泥鏤空窗 transenna）—— 偏藍灰（普洛孔尼索斯大理石）；⛔ 不用 255，那是灰泥
AMPH = 136                                               # 陶甕（赤陶）
PAVE = 146                                               # 院子、廊下的石板


def mixtum(x, y, z, salt=0):
    """石灰岩方石夾紅磚帶：每 14 層一輪 —— 10 層方石（偶爾一塊灰米）、3 層紅磚、1 道粉紅厚灰漿。"""
    k = z % 14
    if k >= 10:
        return BRICK_RM if k == 12 else BRICK_R
    return LIME_G if h01('mx', (x + y) // 6, z // 2, salt) < 0.22 else LIME_R


def shell(M, R, z0, z1, t, fn, layer='body'):
    """外框 R、厚 t 的四面牆，照 fn(x, y, z) 給色。"""
    X0, Y0, X1, Y1 = R
    for z in range(z0, z1):
        for x in range(X0, X1):
            for y in range(Y0, Y1):
                if X0 + t <= x < X1 - t and Y0 + t <= y < Y1 - t:
                    continue
                M.put(layer, x, y, z, fn(x, y, z))


def masonry(M, R, z0, z1, t, salt=0, layer='body'):
    shell(M, R, z0, z1, t, lambda x, y, z: mixtum(x, y, z, salt), layer)


def timber(M, R, z0, z1, t, panel=16, plaster=PLASTER, layer='body'):
    """木構夾灰泥：每 panel 格一根立柱（2 格寬）、上下兩道橫梁、隔一格一道斜撐；其餘灰泥。
    照牆面算：前後兩面量 x、左右兩面量 y（斜撐在那一格板裡從左下到右上）。"""
    X0, Y0, X1, Y1 = R
    h = z1 - z0

    def fn(x, y, z):
        front = y < Y0 + t or y >= Y1 - t
        u = (x - X0) if front else (y - Y0)
        L = (X1 - X0) if front else (Y1 - Y0)
        v = z - z0
        if v < 2 or v >= h - 2 or u < 2 or u >= L - 2 or u % panel < 2:
            return TIMBER
        pi, pu = u // panel, u % panel
        if pi % 2 == 0 and abs((pu - 1) * (h - 4) / (panel - 2) - (v - 2)) < 1.6:
            return TIMBER
        return plaster
    shell(M, R, z0, z1, t, fn, layer)


def arch_cells(x0, x1, z0, zs):
    """半圓拱開口的 (x, z)：x ∈ [x0, x1)、z 從 z0 到拱頂（從 zs 起拱）。"""
    out = []
    cx, r = (x0 + x1) / 2.0, (x1 - x0) / 2.0
    for x in range(x0, x1):
        dx = x + 0.5 - cx
        zt = zs + int(math.floor(math.sqrt(max(0.0, r * r - dx * dx))))
        for z in range(z0, zt):
            out.append((x, z))
    return out


def ring_color(x, z, cx, zs, n=9):
    """拱券：磚與石一塊一塊相間（照角度分塊，同城牆的拱）。"""
    a = math.atan2(z + 0.5 - zs, x + 0.5 - cx)
    return BRICK_R if int(a / (math.pi / n)) % 2 == 0 else LIME_R


def brackets(M, xs, y_wall, y_out, z_top, layer='body', w=2):
    """挑出的樓板底下的木托架（實心三角）：貼牆那一頭從 z_top 往下伸 (y_wall − y_out) 格、外端只剩一格。"""
    for bx in xs:
        for y in range(y_out, y_wall):
            dz = y - y_out + 1
            M.box(layer, bx, y, z_top - dz, bx + w, y + 1, z_top, TIMBER)


def wood_balcony(M, x0, x1, y0, y1, z, posts=12, layer='gallery'):
    """木陽台（芝諾法管的 maeniana／exostai，樣子設計）：木地板、木欄杆（每 posts 格一根立柱、上下兩道扶手、中間細欄），托架另擺。"""
    M.box(layer, x0, y0, z - 2, x1, y1, z, WOOD)
    M.box(layer, x0, y0, z - 2, x1, y0 + 1, z, TIMBER)
    for x in range(x0, x1):
        for zz in (z + 4, z + 9):
            M.put(layer, x, y0, zz, TIMBER)
        if (x - x0) % posts == 0 or x == x1 - 1:
            M.box(layer, x, y0, z, x + 1, y0 + 1, z + 10, TIMBER)
        elif (x - x0) % 3 == 0:
            M.box(layer, x, y0, z, x + 1, y0 + 1, z + 9, TIMBER)
    for xs in (x0, x1 - 1):
        for y in range(y0, y1):
            for zz in (z + 4, z + 9):
                M.put(layer, xs, y, zz, TIMBER)
            if (y - y0) % 3 == 0:
                M.box(layer, xs, y, z, xs + 1, y + 1, z + 9, TIMBER)


def jar(M, cx, cy, h=9, r=3.2, layer='body'):
    """陶甕（pithos 縮小版）：圓身、細頸。"""
    for x in range(int(cx - r - 1), int(cx + r + 1)):
        for y in range(int(cy - r - 1), int(cy + r + 1)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= r:
                top = h - 2 if d > 1.2 else h
                M.box(layer, x, y, 0, x + 1, y + 1, top, AMPH)


def wellhead(M, cx, cy, layer='body'):
    """院子的井欄（大理石圓欄，底下是蓄水池；拜占庭的院子多半是接雨水的池子）＋ 一根木橫桿、吊桶繩（鐵）。"""
    for x in range(cx - 7, cx + 7):
        for y in range(cy - 7, cy + 7):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if 4.0 < d < 6.8:
                M.box(layer, x, y, 0, x + 1, y + 1, 8, MARBLE)
                if d > 6.0:
                    M.put(layer, x, y, 8, LIME_G)
            elif d <= 4.0:
                M.put(layer, x, y, 0, DARK)
    M.box(layer, cx - 7, cy - 1, 8, cx - 5, cy + 1, 22, TIMBER)
    M.box(layer, cx + 5, cy - 1, 8, cx + 7, cy + 1, 22, TIMBER)
    M.box(layer, cx - 7, cy - 1, 22, cx + 7, cy + 1, 24, TIMBER)
    M.box(layer, cx, cy, 12, cx + 1, cy + 1, 22, IRON)


def yard_wall(M, R, h=22, t=3, salt=0, layer='body'):
    """院牆：方石夾磚帶、頂上一道筒瓦壓頂。R 是牆的外框（只畫有給的那幾段：照 R 的四邊、厚 t）。"""
    X0, Y0, X1, Y1 = R
    M.box(layer, X0, Y0, 0, X1, Y1, h, LIME_R)
    for x in range(X0, X1):
        for y in range(Y0, Y1):
            for z in range(h):
                M.put(layer, x, y, z, mixtum(x, y, z, salt), force=True)
            M.put(layer, x, y, h, TILE_R)


LANTERN = {'source': 'summit-rocher-01m-lantern', 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}


def model(kind, name, at):
    return dict(kind, name=name, at=list(at))
